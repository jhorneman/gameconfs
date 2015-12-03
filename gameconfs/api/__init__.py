from datetime import datetime
import logging
import types
import json
from flask import Blueprint, request, jsonify
from gameconfs.app_logging import add_logger
from gameconfs.models import *
from gameconfs.query_helpers import *
from json_api_helpers import set_up_JSON_api_error_handlers


logger = logging.getLogger(__name__)
add_logger(logger)

api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def set_up_api_blueprint(_app):
    set_up_JSON_api_error_handlers(_app, api_blueprint)


# See http://flask.pocoo.org/docs/0.10/patterns/apierrors/
class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_request_parameters():
    if request.data:
        try:
            return json.loads(request.data)
        except ValueError, e:
            raise InvalidUsage("Couldn't decode request parameter JSON: " + e.message)
    else:
        return request.form


def get_string_from_JSON_object(_JSON_object, _field_name):
    try:
        retrieved_string = _JSON_object[_field_name]
    except KeyError:
        raise InvalidUsage("Couldn't find field '{0}' in query.".format(_field_name))

    if not isinstance(retrieved_string, basestring):
        raise InvalidUsage("Query field '{0}' is not a string.".format(_field_name))

    return retrieved_string.strip()


def get_date_from_JSON_object(_object, _field_name):
    date_string = get_string_from_JSON_object(_object, _field_name)
    try:
        # For dates formatted like this: 2012-04-23
        # See also: http://stackoverflow.com/questions/10286204/the-right-json-date-format
        retrieved_date = datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise InvalidUsage("Couldn't parse date '{0}' in query field '{1}'.".format(date_string,_field_name))

    return retrieved_date


def convert_events_for_JSON(_events):
    """Convert events returned from database into something that can be passed to jsonify
    and turned into the API return value."""
    result = []
    for event in _events:
        event_data = {
            "name": event.name,
            "eventUrl": event.event_url,
            "startDate": date.strftime(event.start_date, "%Y-%m-%d"),
            "endDate": date.strftime(event.end_date, "%Y-%m-%d"),
            "venue": event.venue
        }
        if event.city:
            event_data.update({
                "city": event.city.name,
                "state": event.city.state.name if event.city.country.has_states else None,
                "country": event.city.country.name,
                "continent": event.city.country.continent.name
            })
        result.append(event_data)
    return result


@api_blueprint.route("/v1/search_events", methods=("POST",))
def search_events():
    # Get and decode request parameters, raise exception if this is not possible.
    request_parameters = get_request_parameters()
    if not request_parameters:
        raise InvalidUsage("No query parameters found in request.")

    # Start with base query.
    q = Event.query.\
        join(Event.city).\
        join(City.country).\
        join(Country.continent).\
        order_by(Event.start_date.asc()).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))

    found_query_criterion = False

    # Check for and apply date or date range filters.
    today = datetime.today()
    if "date" in request_parameters:
        found_query_criterion = True
        query_date = get_date_from_JSON_object(request_parameters, "date")
        if query_date < today:
            raise InvalidUsage("Can't search in the past.")
        q = q.filter(and_(Event.start_date <= query_date, query_date <= Event.end_date))

    elif "startDate" in request_parameters:
        if "endDate" not in request_parameters:
            raise InvalidUsage("Found start date query field but no end date.")
        found_query_criterion = True

        start_date = get_date_from_JSON_object(request_parameters, "startDate")
        end_date = get_date_from_JSON_object(request_parameters, "endDate")

        if end_date < start_date:
            raise InvalidUsage("End date may not be before start date.")
        if start_date < today or end_date < today:
            raise InvalidUsage("Can't search in the past.")

        q = q.filter(or_(and_(Event.start_date >= start_date, Event.start_date <= end_date),
                         and_(Event.end_date >= start_date, Event.end_date <= end_date)))

    elif "endDate" in request_parameters:
        raise InvalidUsage("Found end date query field but no start date.")

    else:
        q = q.filter(Event.end_date >= today)

    # Check for and apply event name filter.
    if "eventName" in request_parameters:
        found_query_criterion = True
        event_name = get_string_from_JSON_object(request_parameters, "eventName")
        q = q.filter(Event.name.ilike("%" + event_name + "%"))

    # Check for and apply place name filter.
    # Do this last because we will either query or skip.
    found_location_name = None
    if "place" in request_parameters:
        place_name = get_string_from_JSON_object(request_parameters, "place")
        q, found_location_name = filter_by_place_name(q, place_name)
        if found_location_name:
            found_events = q.all()
        else:
            found_events = []
    else:
        if not found_query_criterion:
            raise InvalidUsage("Query must contain at least one criterion.")
        place_name = None
        found_events = q.all()

    response = jsonify({
        "searchedLocationName": place_name,
        "foundLocationName": found_location_name,
        "nrFoundEvents": len(found_events),
        "results": convert_events_for_JSON(found_events)
    })
    if len(found_events) == 0:
        response.status_code = 404
    return response


@api_blueprint.route("/v1/upcoming")
def upcoming_events():
    request_parameters = get_request_parameters()
    if not request_parameters:
        raise InvalidUsage("No query parameters found in request.")

    # Get parameters.
    nr_months = 3
    if "nrMonths" in request_parameters:
        nr_months = request_parameters["nrMonths"]
        try:
            nr_months = int(nr_months)
        except ValueError:
            raise InvalidUsage("Could not parse nrMonths value '{0}'.".format(nr_months))

    if nr_months < 1:
        raise InvalidUsage("nrMonths must be at least 1.")
    elif nr_months > 12:
        raise InvalidUsage("nrMonths may not be higher than 12.")

    place_name = None
    if "place" in request_parameters:
        place_name = request_parameters["place"]
        if not isinstance(place_name, types.StringTypes):
            raise InvalidUsage("Could not parse place value '{0}'.".format(place_name))

    # Get time period.
    today = datetime.today()
    period_start, period_end = get_month_period(today.year, today.month, nr_months)

    # Find events.
    q = Event.query.\
        join(Event.city).\
        join(City.country).\
        join(Country.continent).\
        order_by(Event.start_date.asc()).\
        options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
    q = filter_by_period_start_end(q, period_start, period_end)

    found_location_name = None
    if place_name:
        q, found_location_name = filter_by_place_name(q, place_name)
        if found_location_name:
            found_events = q.all()
        else:
            found_events = []
    else:
        found_events = q.all()

    response = jsonify({
        "nrMonths": nr_months,
        "searchedLocationName": place_name,
        "foundLocationName": found_location_name,
        "nrFoundEvents": len(found_events),
        "results": convert_events_for_JSON(found_events)
    })
    if len(found_events) == 0:
        response.status_code = 404
    return response


@api_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
