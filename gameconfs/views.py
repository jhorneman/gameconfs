from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for
from sqlalchemy.sql.expression import *
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.forms import EventForm
import geocoder


@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

def get_month_period(_start_year, _start_month, _nr_months = 1):
    period_start = date(_start_year, _start_month, 1)
    final_month = _start_month + _nr_months
    if final_month < 12:
        period_end = date(_start_year, final_month, 1)
    else:
        period_end = date(_start_year + 1, final_month - 12, 1)
    return period_start, period_end

@app.route('/')
def index():
    today = date.today()

    period_start, period_end = get_month_period(today.year, today.month, 3)

    events = Event.query.\
        filter(or_(and_(Event.start_date >= period_start, Event.start_date < period_end),
                   and_(Event.end_date >= period_start, Event.end_date < period_end))).\
        all()
    return render_template('index.html', events=events, is_index=True, today=today)

@app.route('/<int:year>/<int:month>')
def month(year, month):
    #TODO: Check year and month are valid
    period_start, period_end = get_month_period(year, month)
    events = Event.query.\
        filter(or_(and_(Event.start_date >= period_start, Event.start_date < period_end),
                   and_(Event.end_date >= period_start, Event.end_date < period_end))).\
        all()
    return render_template('month.html', events=events, month=month, year=year, today=date.today())

@app.route('/new', methods=("GET", "POST"))
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        # user = User()
        # user.username = form.username.data
        # user.email = form.email.data
        # user.save()
        # redirect('register')
        logging.info("NEW EVENT")
    return render_template('edit_event.html', form=form)

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
    return render_template('event.html', event=event, today=date.today())

@app.route('/about')
def about():
    return render_template('about.html')

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

# @app.route('/search', methods=['POST'])
# def search():
#     query = request.form['q']
#     results = {}

#     def update_results(_events):
#         for event in _events:
#             id = event #[0]
#             if results.has_key(id):
#                 results[id] += 1
#             else:
#                 results.setdefault(id, 1)

#     for search_term in query.split():
#         search_term = search_term

#         # Search continents
#         events = db.session.query(Event.id).\
#             join(Event.city).\
#             join(City.country).\
#             join(Country.continent).\
#             filter(Continent.name.like(search_term))
#         events = [e.id for e in events]
#         update_results(events)

#         # Search countries
#         events = db.session.query(Event.id).\
#             join(Event.city).\
#             join(City.country).\
#             filter(Country.name.like(search_term))
#         events = [e.id for e in events]
#         update_results(events)

#         # Search states
#         events = db.session.query(Event.id).\
#             join(Event.city).\
#             join(City.state).\
#             filter(State.name.like(search_term))
#         events = [e.id for e in events]
#         update_results(events)

#         # Search cities
#         events = db.session.query(Event.id).\
#             join(Event.city).\
#             filter(City.name.like(search_term))
#         events = [e.id for e in events]
#         update_results(events)

#         # Search events
#         events = db.session.query(Event.id).\
#             filter(Event.name.like(search_term))
#         events = [e.id for e in events]
#         update_results(events)

#     # If anything was found, rank results by hits
#     if (len(results)):
#         # First get all event data we need from the database in one go
#         # (This results in fewer SQL queries than using [db.session.query(Event).get(id) for id in event_ids] )
#         events_from_db = db.session.query(Event.id, Event.name).\
#             filter(Event.id.in_(results.keys())).\
#             all()

#         # Then build a map of events by id
#         events_by_id = {}
#         for event in events_from_db:
#             events_by_id[event.id] = event

#         # Then make a list of events sorted by search ranking
#         events = [events_by_id[id] for id in sorted(results, key=results.get, reverse=True)]
#     else:
#         events = None

#     return render_template('search.html', query=query, events=events)
