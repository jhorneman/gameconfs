import os
import operator
from functools import wraps
from datetime import date, timedelta, time
from calendar import monthrange
import icalendar
import pytz
import urllib
from flask import render_template, request, send_from_directory, flash, redirect, url_for, Response, make_response
from flask.ext.security.decorators import roles_required
from werkzeug.contrib.atom import AtomFeed
from . import app
from .models import *
from .jinja_filters import event_venue_and_location, event_location
from .forms import EventForm, SearchForm
from .query_helpers import *
from .security import editing_kill_check, user_can_edit
from today import get_today, get_now
from kill_switches import is_feature_on
from project import *


def get_request_parameters():
    if request.data:
        return request.data
    else:
        try:
            return request.form.keys()[0]
        except IndexError:
            return None


class DemoSponsor(object):
    def __init__(self):
        self.target_url = "http://www.intelligent-artifice.com/"
        self.text = "Here are a few tasteful words about our lovely sponsor for this month."
        self.image_path = None
        self.alt_text = ""


def sponsoring_turned_on():
    if not is_feature_on(app, "SPONSORING"):
        return False
    return False
    # return request.cookies.get("sponsoring") == "true"


def mailto(_address, _subject=None, _body=None):
    result = "mailto:" + _address

    params = {}
    if _subject:
        params["subject"] = _subject
    if _body:
        params["body"] = _body

    if len(params):
        result += "?" + "&".join(["%s=%s" % (k, urllib.quote(v)) for k,v in params.items()])

    return result


@app.context_processor
def inject_common_values():
    common_values = {
        "project_name": PROJECT_NAME,
        "project_twitter_account": PROJECT_TWITTER_ACCOUNT,
        "tag_line": PROJECT_TAG_LINE,
        "meta_description": PROJECT_META_DESCRIPTION,
        "admin_email": ADMIN_EMAIL,
        "project_root_url": PROJECT_ROOT_URL,
        "project_domain": PROJECT_DOMAIN,

        "logged_in": user_can_edit(),
        "sponsor": None,
        "ce_retarget": is_feature_on(app, "CE_RETARGET"),
        "mailto": mailto,
        "url_of_this": request.url,
        "today_iso_8601": get_today().isoformat()
    }
    if not sponsoring_turned_on():
        common_values["sponsor"] = None

    return common_values


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


def make_cache_key():
    cache_key = 'view%s' % request.path
    if user_can_edit():
        cache_key += "-edit"
    if sponsoring_turned_on():
        cache_key += "-sponsor"
    app.logger.debug("Cache key: " + cache_key)
    return cache_key.encode('utf-8')     # IMPORTANT! memcached will complain if passed Unicode


def make_date_cache_key(*args, **kwargs):
    cache_key = 'view%s-%s' % (request.path, get_today().strftime("%Y%m%d"))
    return cache_key.encode('utf-8')     # IMPORTANT! memcached will complain if passed Unicode


@app.route('/')
@templated()
def index():
    today = get_today()
    q = maybe_filter_published_only(Event.query, user_can_edit()).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state")).\
        filter(and_(Event.start_date <= today, Event.end_date >= today))
    q = order_by_newest_event(q)
    ongoing_events = q.all()

    min_year, max_year = get_year_range()

    countries = Country.query.\
        order_by(Country.name).\
        all()

    continents = Continent.query.\
        order_by(Continent.name).\
        all()
    continents.append({"name": "Other"})

    return {
        "body_id": "index",
        "ongoing_events": ongoing_events,
        "min_year": min_year,
        "max_year": max_year,
        "countries": countries,
        "continents": continents,
        "search_form": SearchForm()
    }


@app.route('/index.html')
def index_html():
    return redirect(url_for('index'), code=301)


@app.route('/search', methods=("GET", "POST"))
def search():
    if request.method == "POST":   # Form has no validation
        search_form = SearchForm()
        search_string = search_form.search_string.data
        found_events = search_events_by_string(search_string, user_can_edit())
    else:
        search_string = ""
        found_events = []
    return render_template(
        'search.html',
        body_id="search",
        search_string=search_string,
        found_events=found_events,
        search_form=SearchForm()
    )


@app.route('/event/<int:event_id>')
@app.cache.cached(timeout=60*60*24, unless=user_can_edit, key_prefix=make_cache_key)
def view_event(event_id):
    try:
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            filter(Event.id == event_id).\
            options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
        event = q.one()
    except sqlalchemy.orm.exc.NoResultFound:
        max_event_id = db.session.query(func.max(Event.id)).one()[0]
        if 0 < event_id <= max_event_id:
            return render_template('event_deleted.html'), 410
        else:
            return render_template('page_not_found.html'), 404
    return render_template('event.html', body_id="view-event", event=event, today=get_today(), search_form=SearchForm())


@app.route('/upcoming')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
def view_upcoming_events():
    today = get_today()
    end_of_upcoming_period = today + timedelta(days=90)
    end_of_upcoming_period = date(end_of_upcoming_period.year, end_of_upcoming_period.month,
                                  monthrange(end_of_upcoming_period.year, end_of_upcoming_period.month)[1])

    q = maybe_filter_published_only(Event.query, user_can_edit()).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state")).\
        filter(and_(Event.start_date > today, Event.start_date < end_of_upcoming_period))
    q = order_by_newest_event(q)
    events = q.all()

    return render_template('upcoming.html', body_id='upcoming', events=events, until_date=end_of_upcoming_period)


@app.route('/year/<int:year>')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
def view_year(year):
    # Make sure the year is valid (compared to our data)
    min_year, max_year = get_year_range()
    if year < min_year or year > max_year:
        return render_template('page_not_found.html'), 404

    q = maybe_filter_published_only(Event.query, user_can_edit()).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
    q = order_by_newest_event(q)
    q = filter_by_year(q, year)

    events = q.all()

    return render_template('year.html', body_id='year', events=events, year=year)


# To deal with old URL scheme
@app.route('/<int:year>/')
@app.route('/<int:year>/<path:path>')
def old_year(year, path=None):
    return redirect(url_for('view_year', year=year), code=301)


@app.route('/place/<place_name>')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
def view_place(place_name):
    # To deal with old URL scheme
    if place_name == "online":
        return redirect(url_for('view_place', place_name="other"), code=301)

    if place_name == "other":
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            filter(Event.city == None)
        location = "other"
    else:
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
        (q, location) = filter_by_place_name(q, place_name)
        if not location:
            return render_template('page_not_found.html'), 404

    today = get_today()
    q = filter_by_year(q, today.year)
    q = order_by_newest_event(q)
    events = q.all()

    # TODO: Generalize this
    is_in_uk = place_name.lower() == "united kingdom"
    if len(events) > 0:
        if events[0].city and events[0].city.country_id == 5:
            is_in_uk = True
    is_in_london = place_name.lower() == "london" and is_in_uk

    return render_template('place.html', body_id='place', events=events, location=location,
                           year=today.year, is_in_uk=is_in_uk, is_in_london=is_in_london)


@app.route('/place/<place_name>/past')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
def view_place_past(place_name):
    if place_name == "other":
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            filter(Event.city == None)
        location = "other"
    else:
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
        (q, location) = filter_by_place_name(q, place_name)
        if not location:
            return render_template('page_not_found.html'), 404

    q = q.filter(Event.start_date < date(get_today().year, 1, 1))
    q = order_by_newest_event(q)
    events = q.all()

    return render_template('place_past.html', body_id='place', events=events, location=location)


@app.route('/series/<int:series_id>')
def view_series(series_id):
    try:
        series = Series.query.filter(Series.id == series_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    q = maybe_filter_published_only(Event.query, user_can_edit()).\
        filter(Event.series_id == series_id).\
        order_by(Event.start_date.desc(), Event.end_date.asc())
    events = q.all()

    return render_template('series.html', body_id='series', events=events, series=series)


@app.route('/submit')
@templated()
def submit_event():
    return {
        "body_id": "submit",
        "search_form": SearchForm()
    }


class EventSaveException(Exception):
    def __init__(self, _flash_message=None):
        self.flash_message = _flash_message


@app.route('/new', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def create_new_event():
    event_form = EventForm()
    if event_form.validate_on_submit():
        new_event = Event()
        now = get_now()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = event_form.name.data
        new_event.start_date = event_form.start_date.data
        new_event.end_date = event_form.end_date.data
        new_event.event_url = event_form.event_url.data
        new_event.twitter_hashtags = event_form.twitter_hashtags.data
        new_event.twitter_account = event_form.twitter_account.data
        new_event.is_published = event_form.is_published.data

        if event_form.series.data:
            try:
                series = Series.query.filter(Series.name == event_form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(event_form.series.data)
                db.session.add(series)
            new_event.series = series

        # Try to extract a city ID from the hidden field set by the auto-completion system.
        # This helps us avoid using geolocation if it's not necessary.
        try:
            city_id = event_form.city_id.data
            if city_id is not None:
                city_id = int(city_id)
        except ValueError:
            city_id = None

        try:
            if city_id:
                new_event.city_id = city_id

                # TODO: Refactor this, it's copied from Event.set_location()
                venue = event_form.venue.data
                if venue is None:
                    venue = ""
                new_event.venue = venue.strip()

                address_for_geocoding = event_form.address.data
                if address_for_geocoding is None:
                    address_for_geocoding = ""
                new_event.address_for_geocoding = address_for_geocoding.strip()

            elif not new_event.set_location(db.session, event_form.venue.data, event_form.address.data):
                raise EventSaveException("Location setting failed.")

            if is_duplicate_event(new_event):
                raise EventSaveException("Another event with the same name already exists for this year.")

        except Exception as e:
            # Get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()
            if hasattr(e, "flash_message"):
                flash(e.flash_message, "error")
        else:
            db.session.add(new_event)
            db.session.commit()
            app.cache.clear()
            return redirect(url_for('view_event', event_id=new_event.id))

    return render_template('edit_event.html', body_id="edit-event", event_form=event_form, event_id=None,
                           view_name='create_new_event')


@app.route('/event/<int:event_id>/duplicate', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def duplicate_event(event_id):
    if request.method == "GET":
        try:
            original_event = Event.query.filter(Event.id == event_id).one()
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
        new_event.is_published = original_event.is_published

        address = ""
        if original_event.is_in_a_city():
            address = original_event.city_and_state_or_country()

        event_form = EventForm(obj=new_event, address=address)
    else:
        new_event = Event()
        event_form = EventForm()

    if event_form.validate_on_submit():
        now = get_now()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = event_form.name.data
        new_event.start_date = event_form.start_date.data
        new_event.end_date = event_form.end_date.data
        new_event.event_url = event_form.event_url.data
        new_event.twitter_hashtags = event_form.twitter_hashtags.data
        new_event.twitter_account = event_form.twitter_account.data
        new_event.is_published = event_form.is_published.data

        if event_form.series.data:
            try:
                series = Series.query.filter(Series.name == event_form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(event_form.series.data)
                db.session.add(series)
            new_event.series = series

        # Try to extract a city ID from the hidden field set by the auto-completion system.
        # This helps us avoid using geolocation if it's not necessary.
        try:
            city_id = event_form.city_id.data
            if city_id is not None:
                city_id = int(city_id)
        except ValueError:
            city_id = None

        try:
            if city_id:
                new_event.city_id = city_id

                # TODO: Refactor this, it's copied from Event.set_location()
                venue = event_form.venue.data
                if venue is None:
                    venue = ""
                new_event.venue = venue.strip()

                address_for_geocoding = event_form.address.data
                if address_for_geocoding is None:
                    address_for_geocoding = ""
                new_event.address_for_geocoding = address_for_geocoding.strip()

            elif not new_event.set_location(db.session, event_form.venue.data, event_form.address.data):
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
            app.cache.clear()
            return redirect(url_for('view_event', event_id=new_event.id))

    return render_template('edit_event.html', body_id="edit-event", event_form=event_form, event_id=event_id, view_name='duplicate_event')


@app.route('/event/<int:event_id>/edit', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def edit_event(event_id):
    try:
        event = Event.query.filter(Event.id == event_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    address = ""
    if event.is_in_a_city():
        address = event.city_and_state_or_country()

    event_form = EventForm(obj=event, address=address)
    if event_form.validate_on_submit():
        event.last_modified_at = get_now()
        event.name = event_form.name.data
        event.start_date = event_form.start_date.data
        event.end_date = event_form.end_date.data
        event.event_url = event_form.event_url.data
        event.twitter_hashtags = event_form.twitter_hashtags.data
        event.twitter_account = event_form.twitter_account.data
        event.is_published = event_form.is_published.data

        if event_form.series.data:
            try:
                series = Series.query.filter(Series.name == event_form.series.data).one()
            except sqlalchemy.orm.exc.NoResultFound:
                series = Series(event_form.series.data)
                db.session.add(series)
            event.series = series

        # Try to extract a city ID from the hidden field set by the auto-completion system.
        # This helps us avoid using geolocation if it's not necessary.
        try:
            city_id = event_form.city_id.data
            if city_id is not None:
                city_id = int(city_id)
        except ValueError:
            city_id = None

        try:
            if city_id:
                event.city_id = city_id

                # TODO: Refactor this, it's copied from Event.set_location()
                venue = event_form.venue.data
                if venue is None:
                    venue = ""
                event.venue = venue.strip()

                address_for_geocoding = event_form.address.data
                if address_for_geocoding is None:
                    address_for_geocoding = ""
                event.address_for_geocoding = address_for_geocoding.strip()
            elif not event.set_location(db.session, event_form.venue.data, event_form.address.data):
                raise EventSaveException("Location setting failed.")

        except EventSaveException as e:
            # Get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()
            if e.flash_message:
                flash(e.flash_message, "error")
        else:
            db.session.commit()
            app.cache.clear()
            return redirect(url_for('view_event', event_id=event.id))

    return render_template('edit_event.html', body_id="edit-event", event_form=event_form, event_id=event.id, view_name='edit_event')


def is_duplicate_event(_event):
    events = Event.query.\
        filter(Event.name == _event.name).\
        filter(extract("year", Event.start_date) == extract("year", _event.start_date)).\
        all()
    # TODO: Find out why we need this check (SQLAlchemy upgrade?)
    return len([event for event in events if event.id != _event.id]) > 0


@app.route('/event/<int:event_id>/delete', methods=("GET", "POST"))
@editing_kill_check
@roles_required('admin')
def delete_event(event_id):
    try:
        event = Event.query.filter(Event.id == event_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        pass
    else:
        db.session.delete(event)
        db.session.commit()
        app.cache.clear()
    return redirect(url_for('index'))


@app.route('/event/<int:event_id>/ics')
def event_ics(event_id):
    try:
        q = maybe_filter_published_only(Event.query, user_can_edit()).\
            filter(Event.id == event_id)
        event = q.one()
    except sqlalchemy.orm.exc.NoResultFound:
        return render_template('page_not_found.html'), 404

    cal = icalendar.Calendar()
    cal.add('prodid', '-//Event//' + PROJECT_DOMAIN + '//')
    cal.add('version', '2.0')

    calendar_entry = icalendar.Event()
    calendar_entry.add('summary', event.name)
    calendar_entry.add('location', event_venue_and_location(event))
    calendar_entry.add('url', event.event_url)
    calendar_entry.add('dtstart', event.start_date)
    calendar_entry.add('dtend', event.end_date + timedelta(days=1))
    calendar_entry.add('dtstamp', datetime.now(pytz.utc))
    calendar_entry['uid'] = u'{event_id}-{date}@{domain}'.format(
        date=event.start_date,
        event_id=event_id,
        domain=PROJECT_DOMAIN)
    calendar_entry.add('priority', 5)
    cal.add_component(calendar_entry)

    return Response(cal.to_ical(), status=200, mimetype='text/calendar')


@app.route('/upcoming.ics')
@app.cache.cached(timeout=60*60*24)
def upcoming_ics():
    today = get_today()
    end_of_upcoming_period = today + timedelta(days=90)
    end_of_upcoming_period = date(end_of_upcoming_period.year, end_of_upcoming_period.month,
                                  monthrange(end_of_upcoming_period.year, end_of_upcoming_period.month)[1])

    q = filter_published_only(Event.query).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state")).\
        filter(and_(Event.start_date > today, Event.start_date < end_of_upcoming_period))
    q = order_by_newest_event(q)
    events = q.all()

    cal = icalendar.Calendar()
    cal.add('prodid', '-//Event//' + PROJECT_DOMAIN + '//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', PROJECT_NAME)
    cal.add('X-WR-CALDESC', PROJECT_CALENDAR_DESCRIPTION)

    for event in events:
        calendar_entry = icalendar.Event()
        calendar_entry.add('summary', event.name)
        calendar_entry.add('location', event_venue_and_location(event))
        calendar_entry.add('url', url_for('view_event', event_id=event.id, _external=True))
        calendar_entry.add('dtstart', event.start_date)
        calendar_entry.add('dtend', event.end_date + timedelta(days=1))
        calendar_entry.add('dtstamp', datetime.now(pytz.utc))
        calendar_entry['uid'] = u'{event_id}-{date}@{domain}'.format(
            date=event.start_date,
            event_id=event.id,
            domain=PROJECT_DOMAIN)
        calendar_entry.add('priority', 5)
        cal.add_component(calendar_entry)

    return Response(cal.to_ical(), status=200, mimetype='text/calendar')
upcoming_ics.make_cache_key = make_date_cache_key


@app.route('/recent.atom')
@app.cache.cached(timeout=60*60*24)
def recent_feed():
    today = get_today()

    feed = AtomFeed(PROJECT_NAME + ' - New events',
                    title_type='text',
                    url=PROJECT_ROOT_URL,
                    updated=get_now(),
                    feed_url=request.url,
                    author=PROJECT_NAME,
                    subtitle='New events on ' + PROJECT_NAME,
                    subtitle_type='text')

    #TODO: This will miss events if more than 15 are added at once, which occasionally happens.
    events = filter_published_only(Event.query).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state")).\
        filter(Event.end_date >= today).\
        order_by(Event.created_at.desc()).\
        limit(15).\
        all()
    for event in events:
        feed.add(event.name + " - " + event_location(event),
                 title_type='text',
                 content=render_template('recent_feed_entry.html', event=event),
                 content_type='text/html',
                 url=url_for('view_event', event_id=event.id, _external=True),
                 updated=event.created_at,
                 author=PROJECT_NAME,
                 published=event.created_at)

    return feed.get_response()
recent_feed.make_cache_key = make_date_cache_key


@app.route('/today.atom')
@app.cache.cached(timeout=60*60*24)
def today_feed():
    feed = AtomFeed(PROJECT_NAME + " - Today's events",
                    title_type='text',
                    url=PROJECT_ROOT_URL,
                    updated=get_now(),
                    feed_url=request.url,
                    author=PROJECT_NAME,
                    subtitle='Events on {0} starting today'.format(PROJECT_NAME),
                    subtitle_type='text')

    events = filter_published_only(Event.query).\
        order_by(Event.end_date.asc()).\
        filter(Event.start_date == get_today()).\
        all()
    for event in events:
        start_datetime = datetime.combine(event.start_date, time.min)
        feed.add(event.name + " - " + event_location(event),
                 title_type='text',
                 content=render_template('today_feed_entry.txt', event=event),
                 content_type='text/plain',
                 url=url_for('view_event', event_id=event.id, _external=True),
                 updated=start_datetime,
                 author=PROJECT_NAME,
                 published=start_datetime)

    return feed.get_response()
today_feed.make_cache_key = make_date_cache_key


@app.route('/<any(about, other, tools):page_name>')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
def static_page(page_name):
    template_name = page_name + '.html'
    return render_template(template_name)


# @app.route('/sponsoring', methods=("GET", "POST"))
# def sponsoring():
#     if request.method == "POST":
#         if "on_button" in request.form:
#             resp = make_response(render_template('sponsoring.html', sponsoring_state=True, sponsor=GamingInsidersSponsor()))
#             resp.set_cookie("sponsoring", "true")
#         else:
#             resp = make_response(render_template('sponsoring.html', sponsoring_state=False, sponsor=None))
#             resp.set_cookie("sponsoring", "")
#         return resp
#     else:
#         return render_template('sponsoring.html', sponsoring_state=sponsoring_turned_on())


@app.route('/stats')
@app.cache.cached(timeout=60*60*24, key_prefix=make_cache_key)
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
        q = filter_published_only(Event.query).\
            options(joinedload("city")).\
            join(Event.city).\
            filter(Event.city_id == city_id)
        city_stats.append((name, q.count()))
    city_stats = sorted(city_stats, key=operator.itemgetter(1), reverse=True)[:10]
    total_nr_cities = City.query.count()

    # Get country stats
    country_stats = []
    for country_id, name in db.session.query(Country.id, Country.name):
        count = filter_published_only(Event.query).\
            options(joinedload("city"), joinedload("city.country")).\
            join(Event.city).\
            join(City.country).\
            filter(City.country_id == country_id).\
            count()
        country_stats.append((name, count))
    country_stats = sorted(country_stats, key=operator.itemgetter(1), reverse=True)[:10]
    total_nr_countries = Country.query.count()

    # Get total number of events
    total_nr_events = filter_published_only(Event.query).count()

    return render_template('stats.html', time_stats=time_stats, country_stats=country_stats,
        city_stats=city_stats, total_nr_events=total_nr_events, total_nr_cities=total_nr_cities,
        total_nr_countries=total_nr_countries)


@app.errorhandler(404)
@app.cache.cached(timeout=60*60*24*365, key_prefix=make_cache_key)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/icons/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/<regex("apple-touch-icon(-\d+x\d+)?.png"):filename>')
def apple_touch_icon(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/icons/' + filename, mimetype='image/png')


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt', mimetype='text/plain')


@app.route('/sitemap.xml')
@app.cache.cached(timeout=60*60*24)
def sitemap():
    event_ids = [e[0] for e in db.session.query(Event.id).all()]
    return render_template('sitemap.xml', event_ids=event_ids, mimetype='text/xml')
