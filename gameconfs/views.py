from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for
from sqlalchemy.sql.expression import *
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.forms import EventForm


@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

def get_x_months_ago(_start_year, _start_month, _nr_months):
    final_month = _start_month - _nr_months
    if final_month >= 1:
        return _start_year, final_month
    else:
        return _start_year - 1, final_month + 12

def get_x_months_away(_start_year, _start_month, _nr_months):
    final_month = _start_month + _nr_months
    if final_month <= 12:
        return _start_year, final_month
    else:
        return _start_year + 1, final_month - 12

def get_month_period(_start_year, _start_month, _nr_months = 1):
    period_start = date(_start_year, _start_month, 1)
    end_year, end_month = get_x_months_away(_start_year, _start_month, _nr_months)
    period_end = date(end_year, end_month, 1)
    return period_start, period_end

def find_place(_place):
    city = City.query.\
        filter(City.name.like(_place)).\
        first()
    if city is not None:
        return city.country.continent, city.country, city.state, city

    state = State.query.\
        filter(State.name.like(_place)).\
        first()
    if state is not None:
        return state.country.continent, state.country, state, None

    country = Country.query.\
        filter(Country.name.like(_place)).\
        first()
    if country is not None:
        return country.continent, country, None, None

    continent = Continent.query.\
        filter(Continent.name.like(_place)).\
        first()
    if continent is not None:
        return continent, None, None, None

    return None, None, None, None

def filter_by_place(_query, _continent, _country, _state, _city):
    q = _query.filter(Country.continent_id == _continent.id)
    if _country:
        q = q.filter(City.country_id == _country.id)
        if _state:
            q = q.filter(City.state_id == _state.id)
        if _city:
            q = q.filter(Event.city_id == _city.id)
    return q

def filter_by_period(_query, _start_year, _start_month, _nr_months = 1):
    period_start, period_end = get_month_period(_start_year, _start_month, _nr_months)
    return _query.filter(or_(and_(Event.start_date >= period_start, Event.start_date < period_end),
                  and_(Event.end_date >= period_start, Event.end_date < period_end)))

def place_name(_continent, _country, _state, _city):
    if _city:
        loc = _city.name + ", "
    else:
        loc = ""
    if _state:
        if _country.name in geocoder.countries_with_states:
            if _city:
                if _city.name not in geocoder.cities_without_states_or_countries:
                    loc += _state.name + ", "
            else:
                loc += _state.name + ", "
    if _country:
        if _city:
            if _city.name not in geocoder.cities_without_states_or_countries:
                loc += _country.name + ", "
        else:
            loc += _country.name + ", "
    loc += _continent.name
    return loc

@app.route('/<place>')
def place(place):
    continent, country, state, city = find_place(place)
    if continent:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent)
        q = filter_by_place(q, continent, country, state, city)
        today = date.today()
        q = filter_by_period(q, today.year, today.month, 3)
        return render_template('place.html', events=q.all(), place_name=place_name(continent, country, state, city), today=today)
    else:
        #TODO: Show error message
        return "Place not found"

@app.route('/<int:year>/<int:month>')
def month(year, month):
    #TODO: Check year and month are valid
    q = Event.query
    q = filter_by_period(q, year, month, 1)
    return render_template('month.html', events=q.all(), month=month, year=year, today=date.today())

@app.route('/')
def index():
    today = date.today()
    q = Event.query
    q = filter_by_period(q, today.year, today.month, 3)
    return render_template('index.html', events=q.all(), today=today)

# @app.route('/new', methods=("GET", "POST"))
# def new_event():
#     form = EventForm()
#     if form.validate_on_submit():
#         # user = User()
#         # user.username = form.username.data
#         # user.email = form.email.data
#         # user.save()
#         # redirect('register')
#         logging.info("NEW EVENT")
#     return render_template('edit_event.html', form=form)

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
