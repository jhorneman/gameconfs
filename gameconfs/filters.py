import sys
import inspect
from datetime import date, timedelta
import urllib


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


def index_to_month(_index):
    return (int(_index) % 12) + 1


def index_to_year(_index):
    return int(int(_index) / 12)


def event_venue_and_location(_event):
    if _event.is_online():
        return "Online"
    else:
        return _event.venue + ", " + event_location(_event)


def event_location(_event):
    if _event.is_online():
        return "Online"
    else:
        return _event.city_and_state_or_country()


def definite_country(_country):
    if _country in ["Netherlands", "United Kingdom", "United States"]:
        return "the " + _country
    else:
        return _country


def datetimeformat(_value, _format='%H:%M / %d-%m-%Y'):
    return _value.strftime(_format)


def pretty_url(_url):
    return urllib.splittype(_url)[1][2:]


def split(_value, _sep=None):
    return _value.split(_sep)


def urlencode(_value):
    return urllib.urlencode([("", _value.encode('utf8'))])[1:]


#TODO: Remove this after switch to Flask 0.10
def change_scheme(_url, _scheme):
    assert _url.startswith("http://")
    return _scheme + '://' + _url[len('http://'):]


def build_google_calendar_link(_event):
    return "http://www.google.com/calendar/event?" + urllib.urlencode(dict(
        action='TEMPLATE',
        text=_event.name.encode('utf-8'),
        dates=_event.start_date.strftime('%Y%m%d') + '/' + (_event.end_date + timedelta(days=1)).strftime('%Y%m%d'),
        details="Event website: " + _event.event_url.encode('utf-8'),
        location=event_venue_and_location(_event).encode('utf-8')
    ))
