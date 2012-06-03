from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for
from sqlalchemy.sql.expression import *
from application import app, db
from application.models import *

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

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def index():
    return redirect(url_for('events'))
    # return render_template('index.html')

@app.route('/event/')
def events():
    today = date.today()

    past_events = Event.query.\
        filter(and_(Event.start_date > today - timedelta(days=30), Event.start_date < today)).\
        all()

    current_events = Event.query.\
        filter(and_(today >= Event.start_date, today <= Event.end_date)).\
        all()

    future_events = Event.query.\
        filter(and_(Event.end_date > today, Event.start_date < today + timedelta(days=180))).\
        filter(Event.start_date >= date.today()).\
        all()

    return render_template('events.html', past_events=past_events, current_events=current_events, future_events=future_events)

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
