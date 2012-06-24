import re
import os.path
from datetime import datetime, date, timedelta
import json
import operator
from flask import render_template, request, redirect, url_for, abort, send_from_directory
from flask_principal import Permission, RoleNeed
from sqlalchemy.sql.expression import *
from sqlalchemy import func 
from gameconfs import app, db
from gameconfs.models import *
from gameconfs.geocoder import all_continents
from gameconfs.filters import definite_country
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
    return filter_by_period_start_end(_query, period_start, period_end)


def filter_by_period_start_end(_query, _period_start, _period_end):
    return _query.filter(or_(and_(Event.start_date >= _period_start, Event.start_date < _period_end),
        and_(Event.end_date >= _period_start, Event.end_date < _period_end)))


def get_year_range():
    #TODO: Cache this
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

    #TODO: Cache this
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
        show_states=show_states, show_cities=show_cities, title=title )


#    if not admin_permission.can():
#        abort(403)

admin_permission = Permission(RoleNeed('admin'))

@app.route('/new', methods=("GET", "POST"))
@admin_permission.require(403)
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        logging.info("NEW EVENT")
    return render_template('edit_event.html', form=form)


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
    total_nr_cities = City.query.count()

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
    total_nr_countries = Country.query.count()

    # Get total number of events
    total_nr_events = Event.query.count()

    return render_template('stats.html', time_stats=time_stats, country_stats=country_stats,
        city_stats=city_stats, total_nr_events=total_nr_events, total_nr_cities=total_nr_cities,
        total_nr_countries=total_nr_countries)


@app.route('/widget/v<int:version>/script.js')
def widget_script(version):
    return send_from_directory(os.path.join(app.root_path, 'widget'), 'script.js', mimetype='text/javascript')


@app.route('/widget/v<int:version>/<filename>.css')
def widget_css(version, filename):
    return send_from_directory(os.path.join(app.root_path, 'widget'), filename + '.css', mimetype='text/css')


def filter_by_place_name(_query, _place_name):
    continent = Continent.query.\
        filter(Continent.name.like(_place_name)).\
        first()
    if continent:
        return _query.filter(Continent.id == continent.id)

    country = Country.query.\
        filter(Country.name.like(_place_name)).\
        first()
    if country:
        return _query.filter(Country.id == country.id)

    state = State.query.\
    filter(State.name.like(_place_name)).\
    first()
    if state:
        return _query.filter(City.state_id == state.id)

    city = City.query.\
    filter(City.name.like(_place_name)).\
    first()
    if city:
        return _query.filter(City.id == city.id)

    return _query


@app.route('/widget/v<int:version>/data.json')
def widget_data(version):
    #TODO: Move this to a database or text file or something
    widget_users = {
        '2467750341': 'www.gameconfs.com'
    }

    # Get widget user ID
    user_id = request.args.get('user-id', None)

    # Fail if no user ID was given
    if user_id is None:
        abort(400)

    # Fail if user ID is unknown
    if user_id not in widget_users:
        abort(403)

    # Extract domain from request URL
    regex = re.match("https?://([\w\.:]*)/?", request.url_root)
    if regex:
        domain = regex.group(1)
    else:
        domain = ""

    # Fail if domain doesn't match UNLESS we're in debug mode and requesting from local machine
    if not app.debug or domain != '127.0.0.1:5000':
        if domain != widget_users[user_id]:
          abort(403)

    # Fail is no JSONP callback name was given
    callback = request.args.get('callback', None)
    if callback is None:
        abort(400)

    # Get number of months, make sure it's a reasonable value
    nr_months = int(request.args.get('nr-months', 3))
    if nr_months < 1:
        nr_months = 1
    elif nr_months > 12:
        nr_months = 12

    place_name = request.args.get('place', None)

    today = date.today()
    year = today.year

    period_start, period_end = get_month_period(year, today.month, nr_months)

    if place_name:
        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            join(Country.continent)
        q = filter_by_place_name(q, place_name)
    else:
        q = Event.query
    q = filter_by_period_start_end(q, period_start, period_end)
    events = q.all()

    html = render_template('widget_contents.html', events=events, year=year, today=today,
        period_start=period_start, period_end=period_end,
        nr_months=nr_months, place_name=place_name)
    return "%s ( {'html': %s } )" % (callback, json.dumps(html))


@app.route('/widget_test')
def widget_test():
    return render_template('widget_test.html')


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

