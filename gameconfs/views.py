import os
import operator
from functools import wraps
from datetime import date, datetime, timedelta, time
from calendar import monthrange
import icalendar
import pytz
from flask import render_template, request, send_from_directory, flash, redirect, url_for, Response
from flask.ext.security.decorators import roles_required
from flask.ext.login import current_user
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy.orm import *
from sqlalchemy.sql.expression import *
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.jinja_filters import event_venue_and_location, event_location
from gameconfs.forms import EventForm, SearchForm
from gameconfs.query_helpers import *


@app.context_processor
def inject_common_values():
    return dict(logged_in=current_user and current_user.is_authenticated() and not current_app.config["GAMECONFS_KILL_EDITING"])


def editing_kill_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config["GAMECONFS_KILL_EDITING"]:
            return render_template('page_not_found.html'), 404
        return f(*args, **kwargs)
    return decorated_function


# From http://flask.pocoo.org/docs/patterns/viewdecorators/
def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator


@app.route('/')
@templated()
def index():
    today = date.today()
    q = Event.query.\
        order_by(Event.start_date.asc()).\
        filter(and_(Event.start_date <= today, Event.end_date >= today)).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
    ongoing_events = q.all()

    min_year, max_year = get_year_range()

    countries = Country.query.\
        order_by(Country.name).\
        all()

    continents = Continent.query.\
        order_by(Continent.name).\
        all()
    continents.append({"name": "Other"})

    return {"body_id": "index",
            "ongoing_events": ongoing_events,
            "min_year": min_year,
            "max_year": max_year,
            "countries": countries,
            "continents": continents,
            "form": SearchForm()
    }


@app.route('/search', methods=("GET", "POST"))
def search():
    if request.method == "POST":   # Form has no validation
        form = SearchForm()
        search_string = form.search_string.data
        if search_string:
            q = Event.query.\
                filter(Event.name.ilike("%" + search_string + "%")).\
                order_by(Event.start_date.desc())
            found_events = q.all()
        else:
            found_events = []
    else:
        search_string = ""
        found_events = []
    return render_template('search.html', body_id="search", search_string=search_string, found_events=found_events)


@app.route('/event/<int:id>')
def view_event(id):
    try:
        event = Event.query.\
            filter(Event.id == id).\
            options(joinedload('city'), joinedload('city.country'), joinedload('city.state')).\
            one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404
    return render_template('event.html', body_id="view-event", event=event, today=date.today())


@app.route('/upcoming')
def view_upcoming_events():
    today = date.today()
    end_of_upcoming_period = today + timedelta(days=90)
    end_of_upcoming_period = date(end_of_upcoming_period.year, end_of_upcoming_period.month,
                                  monthrange(end_of_upcoming_period.year, end_of_upcoming_period.month)[1])

    q = Event.query.\
        order_by(Event.start_date.asc()).\
        filter(and_(Event.start_date > today, Event.start_date < end_of_upcoming_period)).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
    events = q.all()

    return render_template('upcoming.html', body_id='upcoming', events=events, until_date=end_of_upcoming_period)


@app.route('/year/<int:year>')
@app.cache.cached(timeout=60)
def view_year(year):
    # Make sure the year is valid (compared to our data)
    min_year, max_year = get_year_range()
    if year < min_year or year > max_year:
        return render_template('page_not_found.html'), 404

    q = filter_by_year(Event.query, year).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
    events = q.all()

    return render_template('year.html', body_id='year', events=events, year=year)


@app.route('/place/<place_name>')
def view_place(place_name):
    if place_name == "other":
        q = Event.query.\
            filter(Event.city == None).\
            order_by(Event.start_date.asc())
        location = "other"
    else:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            order_by(Event.start_date.asc()).\
            options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))

        (q, location) = filter_by_place_name(q, place_name)
        if not location:
            return render_template('page_not_found.html'), 404

    today = date.today()
    q = filter_by_period(q, today.year, 1, 12)
    events = q.all()

    return render_template('place.html', body_id='place', events=events, location=location,
                           year=today.year)


@app.route('/place/<place_name>/past')
def view_place_past(place_name):
    if place_name == "other":
        q = Event.query.\
            filter(Event.city == None).\
            order_by(Event.start_date.asc())
        location = "other"
    else:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            order_by(Event.start_date.asc()).\
            options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))

        (q, location) = filter_by_place_name(q, place_name)
        if not location:
            return render_template('page_not_found.html'), 404

    q = q.filter(Event.start_date < date(date.today().year, 1, 1))
    events = q.all()

    return render_template('place_past.html', body_id='place', events=events, location=location)


@app.route('/series/<int:series_id>')
def view_series(series_id):
    try:
        series = Series.query.filter(Series.id == series_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    q = Event.query.\
        order_by(Event.start_date.desc()).\
        filter(Event.series_id == series_id).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
    events = q.all()

    return render_template('series.html', body_id='series', events=events, series=series)


class EventSaveException(Exception):
    def __init__(self, _flash_message=None):
        self.flash_message = _flash_message


@app.route('/new', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def create_new_event():
    form = EventForm()
    if form.validate_on_submit():
        new_event = Event()
        now = datetime.now()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = form.name.data
        new_event.start_date = form.start_date.data
        new_event.end_date = form.end_date.data
        new_event.event_url = form.event_url.data
        new_event.twitter_hashtags = form.twitter_hashtags.data
        new_event.twitter_account = form.twitter_account.data

        if form.series.data:
            try:
                series = Series.query.filter(Series.name == form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(form.series.data)
                db.session.add(series)
            new_event.series = series

        try:
            if not new_event.set_location(db.session, form.venue.data, form.address.data):
                raise EventSaveException("Location setting failed.")
        except EventSaveException as e:
            # Get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()
            if e.flash_message:
                flash(e.flash_message, "error")
        else:
            db.session.add(new_event)
            db.session.commit()
            return redirect(url_for('view_event', id=new_event.id))
    return render_template('edit_event.html', body_id="edit-event", form=form, event_id=None,
                           view_name='create_new_event')


@app.route('/event/<int:id>/duplicate', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def duplicate_event(id):
    if request.method == "GET":
        try:
            original_event = Event.query.filter(Event.id == id).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return render_template('page_not_found.html'), 404

        new_event = Event()
        new_event.name = original_event.name
        new_event.start_date = original_event.start_date
        new_event.end_date = original_event.end_date
        new_event.event_url = original_event.event_url
        new_event.twitter_hashtags = original_event.twitter_hashtags
        new_event.twitter_account = original_event.twitter_account
        new_event.city = original_event.city
        new_event.venue = original_event.venue
        new_event.address_for_geocoding = original_event.address_for_geocoding
        new_event.series = original_event.series

        address = ""
        if original_event.is_in_a_city():
            address = original_event.city_and_state_or_country()

        form = EventForm(obj=new_event, address=address)
    else:
        new_event = Event()
        form = EventForm()

    if form.validate_on_submit():
        now = datetime.now()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = form.name.data
        new_event.start_date = form.start_date.data
        new_event.end_date = form.end_date.data
        new_event.event_url = form.event_url.data
        new_event.twitter_hashtags = form.twitter_hashtags.data
        new_event.twitter_account = form.twitter_account.data

        if form.series.data:
            try:
                series = Series.query.filter(Series.name == form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(form.series.data)
                db.session.add(series)
            new_event.series = series

        try:
            if not new_event.set_location(db.session, form.venue.data, form.address.data):
                raise EventSaveException("Location setting failed.")
            if is_duplicate_event(new_event):
                raise EventSaveException("Another event with the same name already exists for this year.")

        except EventSaveException as e:
            # Get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()
            if e.flash_message:
                flash(e.flash_message, "error")
        else:
            db.session.add(new_event)
            db.session.commit()
            return redirect(url_for('view_event', id=new_event.id))

    return render_template('edit_event.html', body_id="edit-event", form=form, event_id=id, view_name='duplicate_event')


@app.route('/event/<int:id>/edit', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def edit_event(id):
    try:
        event = Event.query.filter(Event.id == id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    address = ""
    if event.is_in_a_city():
        address = event.city_and_state_or_country()

    form = EventForm(obj=event, address=address)
    if form.validate_on_submit():
        event.last_modified_at = datetime.now()
        event.name = form.name.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.event_url = form.event_url.data
        event.twitter_hashtags = form.twitter_hashtags.data
        event.twitter_account = form.twitter_account.data

        if form.series.data:
            try:
                series = Series.query.filter(Series.name == form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(form.series.data)
                db.session.add(series)
            event.series = series

        try:
            if not event.set_location(db.session, form.venue.data, form.address.data):
                raise EventSaveException("Location setting failed.")
        except EventSaveException as e:
            # Get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()
            if e.flash_message:
                flash(e.flash_message, "error")
        else:
            db.session.commit()
            return redirect(url_for('view_event', id=event.id))

    return render_template('edit_event.html', body_id="edit-event", form=form, event_id=event.id, view_name='edit_event')


def is_duplicate_event(_event):
    events = Event.query.\
        filter(Event.name == _event.name).\
        filter(extract("year", Event.start_date) == extract("year", _event.start_date)).\
        all()
    return len(events) > 0


@app.route('/event/<int:id>/delete', methods=("GET", "POST"))
# @editing_kill_check
# @roles_required('admin')
def delete_event(id):
    if 'X-Forwarded-For' in request.headers:
        forwarded_ip = " (%s)" % request.headers['X-Forwarded-For']
    else:
        forwarded_ip = ""
    app.logger.warning("An attempt to delete event %d was made from IP %s" % (id, request.remote_addr) + forwarded_ip)
    return render_template('page_not_found.html'), 404

    # try:
    #     event = Event.query.filter(Event.id == id).one()
    # except sqlalchemy.orm.exc.NoResultFound:
    #     pass
    # else:
    #     db.session.delete(event)
    #     db.session.commit()
    # return redirect(url_for('index'))


@app.route('/event/<int:id>/ics')
def event_ics(id):
    try:
        event = Event.query.filter(Event.id == id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    cal = icalendar.Calendar()
    cal.add('prodid', '-//Game event//gameconfs.com//')
    cal.add('version', '2.0')

    calendar_entry = icalendar.Event()
    calendar_entry.add('summary', event.name)
    calendar_entry.add('location', event_venue_and_location(event))
    calendar_entry.add('url', event.event_url)
    calendar_entry.add('dtstart', event.start_date)
    calendar_entry.add('dtend', event.end_date + timedelta(days=1))
    calendar_entry.add('dtstamp', datetime.now(pytz.utc))
    calendar_entry['uid'] = u'{event_id}-{date}@gameconfs.com'.format(date=event.start_date, event_id=event.id)
    calendar_entry.add('priority', 5)
    cal.add_component(calendar_entry)

    return Response(cal.to_ical(), status=200, mimetype='text/calendar')


@app.route('/recent.atom')
def recent_feed():
    if current_app.cache:
        cached_value = current_app.cache.get("recent-feed")
        if cached_value:
            return cached_value

    feed = AtomFeed('Gameconfs - New events',
                    title_type='text',
                    url=request.url_root,
                    updated=datetime.now(),
                    feed_url=request.url,
                    author='Gameconfs',
                    subtitle='New events on Gameconfs',
                    subtitle_type='text')

    #TODO: This will miss events if more than 15 are added at once, which occasionally happens.
    events = Event.query.\
        order_by(Event.created_at.desc()).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state')).\
        limit(15).\
        all()
    for event in events:
        feed.add(event.name + " - " + event_location(event),
                 title_type='text',
                 content=render_template('recent_feed_entry.html', event=event),
                 content_type='text/html',
                 url=url_for('view_event', id=event.id, _external=True),
                 updated=event.created_at,
                 author='Gameconfs',
                 published=event.created_at)

    response = feed.get_response()

    if current_app.cache:
        current_app.cache.set("recent-feed", response, 60*60*24)
        current_app.logger.info("Stored recent feed in cache")

    return response


@app.route('/today.atom')
def today_feed():
    feed = AtomFeed("Gameconfs - Today's events",
                    title_type='text',
                    url=request.url_root,
                    updated=datetime.now(),
                    feed_url=request.url,
                    author='Gameconfs',
                    subtitle='Events on Gameconfs starting today',
                    subtitle_type='text')

    events = Event.query.\
        filter(Event.start_date == date.today()).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state')).\
        all()
    for event in events:
        start_datetime = datetime.combine(event.start_date, time.min)
        feed.add(event.name + " - " + event_location(event),
                 title_type='text',
                 content=render_template('today_feed_entry.txt', event=event),
                 content_type='text/plain',
                 url=url_for('view_event', id=event.id, _external=True),
                 updated=start_datetime,
                 author='Gameconfs',
                 published=start_datetime)

    return feed.get_response()


# from flask.ext.mail import Message
# @app.route('/email')
# def send():
#     msg = Message("Hello", recipients=["jhorneman@pobox.com"])
#     msg.body = "Hello\nThis is a mail from your server\n\nBye\n"
#     app.mail.send(msg)
#     return "OK"


@app.route('/about')
@templated()
def about():
    return


@app.route('/other')
@templated()
def other():
    return


@app.route('/notifications')
@templated()
def notifications():
    return


@app.route('/sponsoring')
def sponsoring():
    class Sponsor(object):
        def __init__(self):
            self.target_url = "http://www.intelligent-artifice.com/"
            self.image_filename = "placeholder_sponsor.jpg"

    return render_template('sponsoring.html', sponsor=Sponsor())


@app.route('/stats')
def stats():
    # Get time stats
    time_stats = {}

    for d in db.session.query(Event.start_date).order_by(Event.start_date):
        start_date = d.start_date
        if time_stats.has_key(start_date.year):
            time_stats[start_date.year][start_date.month-1] += 1
        else:
            time_stats[start_date.year] = [ 0 for i in range(0, 13) ]
            time_stats[start_date.year][start_date.month-1] = 1

    for year in time_stats.keys():
        time_stats[year][12] = sum(time_stats[year][0:11])

    # Get city stats
    city_stats = []
    for city_id, name in db.session.query(City.id, City.name):
        city_stats.append((name, Event.query.filter(Event.city_id == city_id).count()))
    city_stats = sorted(city_stats, key=operator.itemgetter(1), reverse=True)[:10]
    total_nr_cities = City.query.count()

    # Get country stats
    country_stats = []
    for country_id, name in db.session.query(Country.id, Country.name):
        count = db.session.query(Event).\
            join(Event.city).\
            join(City.country).\
            filter(City.country_id == country_id).\
            count()
        country_stats.append((name, count))
    country_stats = sorted(country_stats, key=operator.itemgetter(1), reverse=True)[:10]
    total_nr_countries = Country.query.count()

    # Get total number of events
    total_nr_events = Event.query.count()

    return render_template('stats.html', time_stats=time_stats, country_stats=country_stats,
        city_stats=city_stats, total_nr_events=total_nr_events, total_nr_cities=total_nr_cities,
        total_nr_countries=total_nr_countries)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    url_root = request.url_root[:-1]
    event_ids = [e[0] for e in db.session.query(Event.id).all()]
    return render_template('sitemap.xml', url_root=url_root, event_ids=event_ids, mimetype='text/xml')
