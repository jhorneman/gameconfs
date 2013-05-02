import sys
import inspect
from datetime import datetime, date, timedelta
import urllib
import codecs
from gameconfs import geocoder


def init_template_filters(_app):
    this_module = sys.modules[__name__]
    def is_mod_function(_func):
        return inspect.isfunction(_func) and inspect.getmodule(_func) == this_module
    for func in [func for func in this_module.__dict__.itervalues() if is_mod_function(func)]:
        if func.__name__ != 'init_template_filters':
            _app.jinja_env.filters[func.__name__] = func

__all__ = [ init_template_filters ]


# http://flask.pocoo.org/snippets/33/
# By Sean Vieira
# Adapted
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

def nice_date(_date):
    return "{0} {1}".format(_date.strftime("%B"), _date.day)

def short_date(_date):
    return "{0} {1}".format(_date.strftime("%b"), _date.day)

def microdata_date(_date):
    return _date.isoformat()

def nice_month(_month):
    month = date(2012, _month, 1)   # Year is irrelevant
    return "{0}".format(month.strftime("%B"))

def short_month(_month):
    month = date(2012, _month, 1)   # Year is irrelevant
    return "{0}".format(month.strftime("%b"))

def event_location(_event):
    if _event.is_online():
        return "Online"
    else:
        return _event.venue + ", " + event_city_and_state_or_country(_event)

def event_city_and_state_or_country(_event):
    if _event.is_online():
        return "Online"
    else:
        loc = _event.city.name
        if _event.city.country.has_states:
            if _event.city.name not in geocoder.cities_without_states_or_countries:
                loc += ", " + _event.city.state.name
        elif _event.city.name not in geocoder.cities_without_states_or_countries:
            loc += ", " + _event.city.country.name
        return loc

def definite_country(_country):
    if _country in ["Netherlands", "United Kingdom", "United States"]:
        return "the " + _country
    else:
        return _country

def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

def split(value, sep=None):
    return value.split(sep)

def urlencode(value):
    return urllib.urlencode([("", value.encode('utf8'))])[1:]
