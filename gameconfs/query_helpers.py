from sqlalchemy.sql.expression import *
from sqlalchemy.orm import *
from flask import current_app
from . import db
from .models import Event, Country, City, State, Continent
from .today import get_today


def search_events_by_string(_search_string, _show_unpublished=False):
    q = build_search_events_by_string_query(_search_string, _show_unpublished)
    if not q:
        return []
    return q.all()


def build_search_events_by_string_query(_search_string, _show_unpublished=False):
    if not _search_string:
        return None
    query_string = "%" + _search_string + "%"
    q = maybe_filter_published_only(Event.query, _show_unpublished).\
        order_by(Event.start_date.desc(), Event.end_date.asc()).\
        filter(or_(Event.name.ilike(query_string),
                   Event.event_url.ilike(query_string),
                   Event.twitter_hashtags.ilike(query_string),
                   Event.twitter_account.ilike(query_string)))
    return q


def order_by_newest_event(_query):
    return _query.order_by(Event.start_date.asc(), Event.end_date.asc())


def filter_published_only(_query):
    return _query.filter(Event.publish_status == "published")


def maybe_filter_published_only(_query, _dont_filter_published_only):
    return _query if _dont_filter_published_only else _query.filter(Event.publish_status == "published")


def filter_by_place(_query, _continent, _country, _state, _city):
    q = _query.filter(Country.continent_id == _continent.id)
    if _country:
        q = q.filter(City.country_id == _country.id)
        if _state:
            q = q.filter(City.state_id == _state.id)
        if _city:
            q = q.filter(Event.city_id == _city.id)
    return q


def filter_by_period_start_end(_query, _period_start, _period_end):
    return _query.filter(or_(and_(Event.start_date >= _period_start, Event.start_date <= _period_end),
                             and_(Event.end_date >= _period_start, Event.end_date <= _period_end)))


def filter_by_year(_query, _year):
    return _query.filter(extract("year", Event.start_date) == _year)


def filter_by_newer_than(_query, _threshold):
    return _query.filter(Event.last_modified_at > _threshold)


def get_year_range():
    if current_app.cache:
        cached_value = current_app.cache.get("min-max-year")
        if cached_value:
            min_year, max_year = map(int, cached_value.split("-"))
            return min_year, max_year

    min_year = db.session.query(func.min(Event.start_date)).one()[0]
    if min_year:
        min_year = min_year.year
        max_year = db.session.query(func.max(Event.end_date)).one()[0].year
    else:
        min_year = get_today().year
        max_year = min_year

    if current_app.cache:
        current_app.cache.set("min-max-year", "%s-%s" % (min_year, max_year), 60*60*24)

    return min_year, max_year


def filter_by_place_name(_query, _place_name):
    if _place_name == "online":
        _place_name = "other"

    if _place_name == "other":
        return _query.filter(Event.city == None), _place_name

    country = Country.query. \
        filter(Country.name.ilike(_place_name)). \
        first()
    if country:
        return _query.filter(Country.id == country.id), country.name

    continent = Continent.query. \
        filter(Continent.name.ilike(_place_name)). \
        first()
    if continent:
        return _query.filter(Continent.id == continent.id), continent.name

    state = State.query. \
        filter(State.name.ilike(_place_name)). \
        first()
    if state:
        return _query.filter(City.state == state), state.name

    city = City.query. \
        filter(City.name.ilike(_place_name)). \
        first()
    if city:
        return _query.filter(City.id == city.id), city.name

    return _query, None
