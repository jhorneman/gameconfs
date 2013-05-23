import os
from datetime import date, datetime, timedelta, time
import operator
import icalendar
import pytz
from flask import render_template, request, abort, send_from_directory, flash, redirect, url_for, Response
from flask.ext.security.decorators import roles_required
from flask.ext.login import current_user
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy.orm import *
from sqlalchemy.sql.expression import *
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.geocoder import all_continents
from gameconfs.filters import definite_country, event_location, event_city_and_state_or_country
from gameconfs.forms import EventForm
from gameconfs.helpers import *


# For convenience
@app.context_processor
def inject_logged_in_status():
    return dict(logged_in=current_user and current_user.is_authenticated())


@app.route('/', defaults={'year': None, 'continent_name': None, 'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>', defaults={'continent_name': None, 'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>', defaults={'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>', defaults={'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>/<city_or_state_name>', defaults={'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>/<city_or_state_name>/<city_name>')
def index(year, continent_name, country_name, city_or_state_name, city_name):
    today = date.today()

    # Per default, the year is the current year
    title = None
    if year is None:
        year = today.year
        # If no year is set, set a different title
        title = "Game events all over the world"

    # Make sure the year is valid (compared to our data)
    min_year, max_year = get_year_range()
    if year < min_year or year > max_year:
        abort(404)

    state_name = None
    continent = None
    country = None
    state = None
    city = None
    countries = []
    states = []
    cities = []
    show_states = False
    show_cities = True

    location_title = None
    if continent_name is None:
        selection_level = "all"
        location_title = u"all over the world"
    else:
        continent = Continent.query.\
            filter(Continent.name.like(continent_name)).\
            first()
        if continent is None:
            abort(404)

        countries = db.session.query(Country.name).\
            join(Country.continent).\
            filter(Continent.id == continent.id).\
            order_by(Country.name).\
            all()
        countries = [c[0] for c in countries]

        if country_name is None:
            selection_level = "continent"
            location_title = u"in " + continent_name
        else:
            country = Country.query.\
                filter(Country.name.like(country_name)).\
                first()
            if country is None:
                abort(404)

            if country_name in geocoder.countries_with_states:
                states = db.session.query(State.name).\
                    join(State.country).\
                    filter(Country.id == country.id).\
                    order_by(State.name).\
                    all()
                states = [c[0] for c in states]
                show_states = True

                if city_or_state_name is None:
                    selection_level = "country"
                    location_title = u"in " + definite_country(country_name)
                    show_cities = False
                else:
                    state_name = city_or_state_name
                    state = State.query.\
                        join(State.country).\
                        filter(and_(State.name.like(state_name), Country.id == State.country_id)).\
                        first()
                    if state is None:
                        abort(404)

                    cities = db.session.query(City.name).\
                        join(City.state).\
                        filter(State.id == state.id).\
                        order_by(City.name).\
                        all()
                    cities = [c[0] for c in cities]

                    if city_name is None:
                        selection_level = "state"
                        location_title = u"in " + state_name
                    else:
                        selection_level = "city"
                        city = City.query.\
                            join(City.state).\
                            join(City.country).\
                            filter(and_(City.name.like(city_name), State.id == City.state_id, Country.id == City.country_id)).\
                            first()
                        if city is None:
                            abort(404)
                        location_title = u"in " + city_name
            else:
                cities = db.session.query(City.name).\
                    join(City.country).\
                    filter(Country.id == country.id).\
                    order_by(City.name).\
                    all()
                cities = [c[0] for c in cities]

                if city_or_state_name is None:
                    selection_level = "country"
                    location_title = u"in " + definite_country(country_name)
                    show_cities = country_name not in geocoder.countries_without_cities
                else:
                    if city_name is None:
                        city_name = city_or_state_name

                    selection_level = "city"
                    city = City.query.\
                        join(City.country).\
                        filter(and_(City.name.like(city_name), Country.id == City.country_id)).\
                        first()
                    if city is None:
                        abort(404)
                    location_title = u"in " + city_name

    # Get the events
    if continent is None:
        q = Event.query
        q = filter_by_period(q, year, 1, 12).\
            options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
        events = q.all()
    else:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent)
        q = filter_by_place(q, continent, country, state, city)
        q = filter_by_period(q, year, 1, 12)
        events = q.all()

    # Get the number of events for each month
    # We need this to set the status of the month buttons
    nr_events_by_month = [0 for i in range(0, 12)]
    for event in events:
        if event.start_date.year == year:
            nr_events_by_month[event.start_date.month-1] += 1
            if event.end_date.year == year and event.end_date.month != event.start_date.month:
                nr_events_by_month[event.end_date.month-1] += 1

    # Get stats for header
    # total_nr_countries = Country.query.count()
    # total_nr_events = Event.query.count()

    if not title:
        title = u"Game events {0} in {1}".format(location_title, unicode(year))

    #TODO: Find a nicer way to pass all of these parameters
    return render_template('index.html', events=events, year=year, today=today, selection_level=selection_level,
        min_year=min_year, max_year=max_year, nr_events_by_month=nr_events_by_month,
        selected_continent=continent_name, selected_country=country_name, selected_state=state_name, selected_city=city_name,
        continents=all_continents, countries=countries, states=states, cities=cities,
        show_states=show_states, show_cities=show_cities, title=title)


@app.route('/new', methods=("GET", "POST"))
@roles_required('admin')
def new_event():
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

        result = new_event.set_location(db.session, form.venue.data, form.address.data)

        # Only add if setting location worked (geocoding can fail)
        if result:
            db.session.add(new_event)
            db.session.commit()
            return redirect(url_for('event', id=new_event.id))
        else:
            # Otherwise get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()

            flash("Location setting failed", "error")
            return render_template('edit_event.html', body_id="edit-event", form=form)
    else:
        return render_template('edit_event.html', body_id="edit-event", form=form, event_id=None)


@app.route('/event/<id>/edit', methods=("GET", "POST"))
@roles_required('admin')
def edit_event(id):
    event = Event.query.filter(Event.id == id).one()

    address = ""
    if not event.is_online():
        # Copied from filters
        address = event.city.name
        if event.city.country.has_states:
            if event.city.name not in geocoder.cities_without_states_or_countries:
                address += ", " + event.city.state.name
        elif event.city.name not in geocoder.cities_without_states_or_countries:
            address += ", " + event.city.country.name

    form = EventForm(obj=event, address=address)

    if form.is_submitted():
        event.last_modified_at = datetime.now()
        event.name = form.name.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.event_url = form.event_url.data
        event.twitter_hashtags = form.twitter_hashtags.data
        event.twitter_account = form.twitter_account.data

        result = event.set_location(db.session, form.venue.data, form.address.data)

        # Only add if setting location worked (geocoding can fail)
        if result:
            db.session.commit()
            return redirect(url_for('event', id=event.id))
        else:
            # Otherwise get rid of whatever was done to the session or it will cause trouble later
            db.session.expunge_all()

            flash("Location setting failed", "error")

    return render_template('edit_event.html', body_id="edit-event", form=form, event_id=event.id)


@app.route('/event/<id>/delete', methods=("GET", "POST"))
@roles_required('admin')
def delete_event(id):
    event = Event.query.filter(Event.id == id).one()
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/new_events')
@roles_required('admin')
def new_events():
    new_threshold = datetime(2013, 5, 2, 12, 35)
    q = Event.query
    q = filter_by_newer_than(q, new_threshold).\
        order_by(Event.last_modified_at.desc()).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))
    events = q.all()
    return render_template('new_events.html', events=events)


@app.route('/event/<id>')
def event(id):
    try:
        event = Event.query.filter(Event.id == id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        abort(404)
    return render_template('event.html', body_id="view-event", event=event, today=date.today())


@app.route('/event/<id>/ics')
def event_ics(id):
    event = Event.query.filter(Event.id == id).one()

    cal = icalendar.Calendar()
    cal.add('prodid', '-//Game event//gameconfs.com//')
    cal.add('version', '2.0')

    calendar_entry = icalendar.Event()
    calendar_entry.add('summary', event.name)
    calendar_entry.add('location', event_location(event))
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
    feed = AtomFeed('Gameconfs - New events',
                    title_type='text',
                    url=request.url_root,
                    updated=datetime.now(),
                    feed_url=request.url,
                    author='Gameconfs',
                    subtitle='New events on Gameconfs',
                    subtitle_type='text')

    events = Event.query.order_by(Event.created_at.desc()).limit(15).all()
    for event in events:
        feed.add(event.name + " - " + event_city_and_state_or_country(event),
                 title_type='text',
                 content=render_template('recent_feed_entry.html', event=event),
                 content_type='text/html',
                 url=url_for('event', id=event.id, _external=True),
                 updated=event.created_at,
                 author='Gameconfs',
                 published=event.created_at)

    return feed.get_response()


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

    events = Event.query.filter(Event.start_date == date.today()).all()
    for event in events:
        start_datetime = datetime.combine(event.start_date, time.min)
        feed.add(event.name + " - " + event_city_and_state_or_country(event),
                 title_type='text',
                 content=render_template('today_feed_entry.txt', event=event),
                 content_type='text/plain',
                 url=url_for('event', id=event.id, _external=True),
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
def about():
    return render_template('about.html')


@app.route('/other')
def other():
    return render_template('other.html')


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

# @app.route('/favicon.ico')
# def favicon():
#     return send_from_directory(os.path.join(app.root_path, 'static'),
#                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    url_root = request.url_root[:-1]
    event_ids = [e[0] for e in db.session.query(Event.id).all()]
    return render_template('sitemap.xml', url_root=url_root, event_ids=event_ids, mimetype='text/xml')
