from datetime import datetime, date, timedelta
import operator
from flask import render_template, request, redirect, url_for, abort
from sqlalchemy.sql.expression import *
from sqlalchemy import func 
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.forms import EventForm
from gameconfs.geocoder import all_continents


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

def get_year_range():
    min_year = db.session.query(func.min(Event.start_date)).one()[0].year
    max_year = db.session.query(func.max(Event.end_date)).one()[0].year
    return min_year, max_year

@app.route('/', defaults={'year': None, 'continent_name': None, 'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>', defaults={'continent_name': None, 'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>', defaults={'country_name': None, 'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>', defaults={'city_or_state_name': None, 'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>/<city_or_state_name>', defaults={'city_name': None})
@app.route('/<int:year>/<continent_name>/<country_name>/<city_or_state_name>/<city_name>')
def index(year, continent_name, country_name, city_or_state_name, city_name):
    # Per default, the year is the current year
    today = date.today()
    if year is None:
        year = today.year

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

    if continent_name is None:
        selection_level = "all"
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
                    else:
                        selection_level = "city"
                        city = City.query.\
                            join(City.state).\
                            join(City.country).\
                            filter(and_(City.name.like(city_name), State.id == City.state_id, Country.id == City.country_id)).\
                            first()
                        if city is None:
                            abort(404)
            else:
                cities = db.session.query(City.name).\
                    join(City.country).\
                    filter(Country.id == country.id).\
                    order_by(City.name).\
                    all()
                cities = [c[0] for c in cities]

                if city_or_state_name is None:
                    selection_level = "country"
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

    # Get the number of events for each month
    # We need this to set the status of the month buttons
    nr_events_by_month = [ 0 for i in range(0, 12) ]
    for month in range(1, 12+1):
        period_start = date(year, month, 1)
        if month < 12:
            period_end = date(year, month+1, 1)
        else:
            period_end = date(year+1, 1, 1)
        #TODO: Add place filter
        nr_events_by_month[month-1] = Event.query.\
            filter(and_(Event.start_date >= period_start, Event.start_date < period_end)).\
            count()

    # Get the events
    if continent is None:
        q = Event.query
        q = filter_by_period(q, year, 1, 12)
        events = q.all()
    else:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent)
        q = filter_by_place(q, continent, country, state, city)
        q = filter_by_period(q, year, 1, 12)
        events = q.all()

    return render_template('index.html', events=events, year=year, today=today, selection_level=selection_level,
        min_year=min_year, max_year=max_year, nr_events_by_month=nr_events_by_month,
        selected_continent=continent_name, selected_country=country_name, selected_state=state_name, selected_city=city_name,
        continents=all_continents, countries=countries, states=states, cities=cities,
        show_states=show_states, show_cities=show_cities)

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

@app.route('/other')
def other():
    return render_template('other.html')

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
    for id, name in db.session.query(City.id, City.name):
        city_stats.append((name, Event.query.filter(Event.city_id == id).count()))
    city_stats = sorted(city_stats, key=operator.itemgetter(1), reverse=True)[:10]

    # Get country stats
    country_stats = []
    for id, name in db.session.query(Country.id, Country.name):
        count = db.session.query(Event).\
             join(Event.city).\
             join(City.country).\
             filter(City.country_id == id).\
             count()
        country_stats.append((name, count))
    country_stats = sorted(country_stats, key=operator.itemgetter(1), reverse=True)[:10]

    # Get total number of events
    total_nr_events = Event.query.count()

    return render_template('stats.html', time_stats=time_stats, country_stats=country_stats,
        city_stats=city_stats, total_nr_events=total_nr_events)

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

