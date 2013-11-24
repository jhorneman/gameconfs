from datetime import date
from sqlalchemy.sql.expression import *
from sqlalchemy import func
from gameconfs import db
from gameconfs.models import Event, Country, City, State, Continent


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


def filter_by_newer_than(_query, _threshold):
    return _query.filter(Event.last_modified_at > _threshold)


def get_year_range():
    #TODO: Cache this
    min_year = db.session.query(func.min(Event.start_date)).one()[0].year
    max_year = db.session.query(func.max(Event.end_date)).one()[0].year
    return min_year, max_year


def filter_by_place_name(_query, _place_name):
    continent = Continent.query. \
        filter(Continent.name.ilike(_place_name)). \
        first()
    if continent:
        return _query.filter(Continent.id == continent.id)

    country = Country.query. \
        filter(Country.name.ilike(_place_name)). \
        first()
    if country:
        return _query.filter(Country.id == country.id)

    state = State.query. \
        filter(State.name.ilike(_place_name)). \
        first()
    if state:
        return _query.filter(City.state == state)

    city = City.query. \
        filter(City.name.ilike(_place_name)). \
        first()
    if city:
        return _query.filter(City.id == city.id)

    return None
