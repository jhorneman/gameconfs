from flask import render_template, request
from application import app, db
from application.models import *

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event/')
def events():
    events = Event.query.all()
    return render_template('events.html', events=events)

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
