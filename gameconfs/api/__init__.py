from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from gameconfs.app_logging import add_logger
from gameconfs.models import *
from gameconfs.query_helpers import *
from json_api_helpers import set_up_JSON_api_error_handlers
from gameconfs.today import get_today


logger = logging.getLogger(__name__)
add_logger(logger)

api_blueprint = Blueprint("api", __name__, url_prefix="/api", template_folder="templates")


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


def parse_date(_date_as_string):
    _date_as_string = _date_as_string.strip()
    try:
        # For dates formatted like this: 2012-04-23
        # See also: http://stackoverflow.com/questions/10286204/the-right-json-date-format
        retrieved_date = datetime.strptime(_date_as_string, "%Y-%m-%d")
    except ValueError:
        raise InvalidUsage("Couldn't parse date '{0}'.".format(_date_as_string))
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


@api_blueprint.route('/')
def index():
    return render_template('api/index.html')


@api_blueprint.route("/v1/search_events")
def search_events():
     # For GET requests, which is what we have, we can only get the parameters from the URL arguments.
    request_parameters = request.args

    # Make sure we only received parameters we know.
    for param in request_parameters.keys():
        if param not in ["data", "startDate", "endDate", "eventName", "place"]:
            raise InvalidUsage("Did not recognize parameter {0}.".format(param))

    # Start with base query.
    q = filter_published_only(Event.query)
    q = order_by_newest_event(q)

    found_query_criterion = False

    # Check for and apply date or date range filters.
    today = get_today()
    if "date" in request_parameters:
        found_query_criterion = True
        query_date = parse_date(request_parameters["date"])
        if query_date < today:
            raise InvalidUsage("Can't search in the past.")
        q = q.filter(and_(Event.start_date <= query_date, query_date <= Event.end_date))

    elif "startDate" in request_parameters:
        if "endDate" not in request_parameters:
            raise InvalidUsage("Found start date argument but no end date.")
        found_query_criterion = True

        start_date = parse_date(request_parameters["startDate"])
        end_date = parse_date(request_parameters["endDate"])

        if end_date < start_date:
            raise InvalidUsage("End date may not be before start date.")
        if start_date < today or end_date < today:
            raise InvalidUsage("Can't search in the past.")

        q = q.filter(or_(and_(Event.start_date >= start_date, Event.start_date <= end_date),
                         and_(Event.end_date >= start_date, Event.end_date <= end_date)))

    elif "endDate" in request_parameters:
        raise InvalidUsage("Found end date argument but no start date.")

    else:
        q = q.filter(Event.end_date >= today)

    # Check for and apply event name filter.
    if "eventName" in request_parameters:
        event_name = request_parameters["eventName"].strip()
        if len(event_name) > 0:
            found_query_criterion = True
            event_name = request_parameters["eventName"].strip()
            q = q.filter(Event.name.ilike("%" + event_name + "%"))
        else:
            raise InvalidUsage("Event name argument was empty.")

    # Check for and apply place name filter.
    # Do this last because we will either query or skip.
    found_location_name = None
    if "place" in request_parameters:
        place_name = request_parameters["place"].strip()
        if len(place_name) == 0:
            raise InvalidUsage("Place argument was empty.")
        else:
            if place_name == "other":
                q = q.filter(Event.city == None)
                found_location_name = "other"
            else:
                q = q.join(Event.city).\
                    join(City.country).\
                    join(Country.continent).\
                    options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
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
     # For GET requests, which is what we have, we can only get the parameters from the URL arguments.
    request_parameters = request.args

    # Make sure we only received parameters we know.
    for param in request_parameters.keys():
        if param not in ["nrMonths", "place"]:
            raise InvalidUsage("Did not recognize parameter {0}.".format(param))

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
        place_name = request_parameters["place"].strip()
        if len(place_name) == 0:
            raise InvalidUsage("Place argument was empty.")

    # Get time period.
    today = get_today()
    period_start, period_end = get_month_period(today.year, today.month, nr_months)

    # Find events.
    q = filter_published_only(Event.query)
    q = order_by_newest_event(q)
    q = filter_by_period_start_end(q, period_start, period_end)

    found_location_name = None
    if place_name:
        if place_name == "other":
            q = q.filter(Event.city == None)
            found_location_name = "other"
        else:
            q = q.join(Event.city).\
                join(City.country).\
                join(Country.continent).\
                options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
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
