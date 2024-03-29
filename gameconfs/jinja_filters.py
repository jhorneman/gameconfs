import sys
import inspect
from datetime import date, datetime, timedelta
import urllib
from today import get_today


def set_up_jinja_filters(_app):
    this_module = sys.modules[__name__]

    def is_mod_function(_func):
        return inspect.isfunction(_func) and inspect.getmodule(_func) == this_module
    for func in [func for func in this_module.__dict__.itervalues() if is_mod_function(func)]:
        if func.__name__ != 'set_up_jinja_filters':
            _app.jinja_env.filters[func.__name__] = func

__all__ = [set_up_jinja_filters]


# Adapted http://flask.pocoo.org/snippets/33/ by Sean Vieira.
def friendly_time(_date, past_="ago", future_ = "from now", default = "just now"):
    """
    Returns string representing "time since"
    or "time until" e.g.
    3 days ago, 5 hours from now etc.
    """

    if isinstance(_date, datetime):
        _date = date(_date.year, _date.month, _date.day)

    today = get_today()
    if today > _date:
        diff = today - _date
        dt_is_past = True
    else:
        diff = _date - today
        dt_is_past = False

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s %s" % (period,
                                 singular if period == 1 else plural,
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


def nr_months(_nr_months):
    return "{0} months".format(_nr_months) if _nr_months > 1 else "month"


def short_range(_event):
    if _event.start_date == _event.end_date:
        return "{0} {1}".format(short_date(_event.start_date), _event.start_date.year)
    else:
        if _event.start_date.month == _event.end_date.month:
            return "{0}-{1} {2}".format(short_date(_event.start_date), _event.end_date.day, _event.start_date.year)
        else:
            return "{0}-{1} {2}".format(short_date(_event.start_date), short_date(_event.end_date), _event.start_date.year)


def index_to_month(_index):
    return (int(_index) % 12) + 1


def index_to_year(_index):
    return int(int(_index) / 12)


def date_or_range(_event):
    if _event.start_date == _event.end_date:
        return "{0} {1}".format(nice_date(_event.start_date), _event.start_date.year)
    else:
        return "{0} until {1} {2}".format(nice_date(_event.start_date), nice_date(_event.end_date), _event.start_date.year)


def event_venue_and_location(_event):
    if _event.is_not_in_a_city():
        return _event.venue
    else:
        return _event.venue + ", " + _event.city_and_state_or_country()


def event_location(_event):
    if _event.is_not_in_a_city():
        return _event.venue
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


def build_google_calendar_link(_event):
    return "http://www.google.com/calendar/event?" + urllib.urlencode(dict(
        action='TEMPLATE',
        text=_event.name.encode('utf-8'),
        dates=_event.start_date.strftime('%Y%m%d') + '/' + (_event.end_date + timedelta(days=1)).strftime('%Y%m%d'),
        details="Event website: " + _event.event_url.encode('utf-8'),
        location=event_venue_and_location(_event).encode('utf-8')
    ))
