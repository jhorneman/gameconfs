from datetime import datetime, date, timedelta
import urllib
import codecs
from flask import render_template, request, redirect, url_for
from sqlalchemy.sql.expression import *
from application import app, db
from application.models import *
import geocoder

# http://flask.pocoo.org/snippets/33/
# By Sean Vieira
# Adapted
@app.template_filter()
def friendly_time(dt, past_="ago", 
    future_="from now", 
    default="just now"):
    """
    Returns string representing "time since"
    or "time until" e.g.
    3 days ago, 5 hours from now etc.
    """

    today = date.today()
    if today > dt:
        diff = today - dt
        dt_is_past = True
    else:
        diff = dt - today
        dt_is_past = False

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s %s" % (period, \
                singular if period == 1 else plural, \
                past_ if dt_is_past else future_)

    return default

@app.template_filter()
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

@app.template_filter()
def split(value, sep=None):
    return value.split(sep)

@app.template_filter()
def urlencode(value):
    return urllib.urlencode([("", value.encode('utf8'))])[1:]


@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def index():
    # Get user IP address
    user_host = request.headers["Host"]
    if user_host == "127.0.0.1:5000":
        user_host = "213.47.84.26"
        # user_host = "66.249.73.131"

    # Geocode
    ipg = geocoder.IPGeocodeResults(user_host)

    user_location = "You are apparently based in "

    # Refine (state) and refactor this (move to model?)
    city = City.query.\
        filter(City.name == ipg.results["city"]).\
        join(City.country).\
        filter(Country.name == ipg.results["country_name"]).\
        first()
    if city:
        user_location += "<a href=\"" + url_for('city', city_id=city.id) + "\">" + city.name + "</a>"
    else:
        user_location += ipg.results["city"]

    if ipg.results["country_name"] in geocoder.countries_with_states:
        user_location += ", " + ipg.results["region_name"]
    user_location += ", " + ipg.results["country_name"]
    user_location += "."

    # user_location = repr(ipg.results)

    today = date.today()

    past_events = Event.query.\
        filter(and_(Event.start_date > today - timedelta(days=30), Event.start_date < today)).\
        all()
    add_location_to_events(past_events)

    current_events = Event.query.\
        filter(and_(today >= Event.start_date, today <= Event.end_date)).\
        all()
    add_location_to_events(current_events)

    future_events = Event.query.\
        filter(and_(Event.start_date > today, Event.start_date < today + timedelta(days=180))).\
        filter(Event.start_date >= date.today()).\
        all()
    add_location_to_events(future_events)

    return render_template('events.html', past_events=past_events, current_events=current_events, future_events=future_events, user_location=user_location)

def add_location_to_events(_events):
    for e in _events:
        e.location = nice_location_name(e.city)

def nice_location_name(_city):
    l = _city.name
    if _city.country.name in geocoder.countries_with_states:
        l += ", " + _city.state.name
    elif _city.name not in geocoder.cities_without_countries:
        l += ", " + _city.country.name
    return l

@app.route('/city/<city_id>')
def city(city_id):
    today = date.today()

    future_events = Event.query.\
        filter(Event.city_id == city_id).\
        filter(and_(Event.start_date > today, Event.start_date < today + timedelta(days=180))).\
        filter(Event.start_date >= date.today()).\
        all()
    add_location_to_events(future_events)

    location = nice_location_name(City.query.get(city_id))

    return render_template('city.html', location=location, future_events=future_events)

@app.route('/event/<id>')
def event(id):
    event = Event.query.filter(Event.id == id).one()
    return render_template('event.html', event=event)

@app.route('/search', methods=['POST'])
def search():
    query = request.form['q']
    results = {}

    def update_results(_events):
        for event in _events:
            id = event #[0]
            if results.has_key(id):
                results[id] += 1
            else:
                results.setdefault(id, 1)

    for search_term in query.split():
        search_term = search_term

        # Search continents
        events = db.session.query(Event.id).\
            join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            filter(Continent.name.like(search_term))
        events = [e.id for e in events]
        update_results(events)

        # Search countries
        events = db.session.query(Event.id).\
            join(Event.city).\
            join(City.country).\
            filter(Country.name.like(search_term))
        events = [e.id for e in events]
        update_results(events)

        # Search states
        events = db.session.query(Event.id).\
            join(Event.city).\
            join(City.state).\
            filter(State.name.like(search_term))
        events = [e.id for e in events]
        update_results(events)

        # Search cities
        events = db.session.query(Event.id).\
            join(Event.city).\
            filter(City.name.like(search_term))
        events = [e.id for e in events]
        update_results(events)

        # Search events
        events = db.session.query(Event.id).\
            filter(Event.name.like(search_term))
        events = [e.id for e in events]
        update_results(events)

    # If anything was found, rank results by hits
    if (len(results)):
        # First get all event data we need from the database in one go
        # (This results in fewer SQL queries than using [db.session.query(Event).get(id) for id in event_ids] )
        events_from_db = db.session.query(Event.id, Event.name).\
            filter(Event.id.in_(results.keys())).\
            all()

        # Then build a map of events by id
        events_by_id = {}
        for event in events_from_db:
            events_by_id[event.id] = event

        # Then make a list of events sorted by search ranking
        events = [events_by_id[id] for id in sorted(results, key=results.get, reverse=True)]
    else:
        events = None

    return render_template('search.html', query=query, events=events)
