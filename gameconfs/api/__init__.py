import re
from datetime import datetime, date
from flask import Blueprint, jsonify, render_template
from gameconfs.app_logging import add_logger
from gameconfs.models import *
from json_api_helpers import set_up_JSON_api_error_handlers


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
    return date(retrieved_date.year, retrieved_date.month, retrieved_date.day)


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


@api_blueprint.route('/', defaults={'path': ''})
@api_blueprint.route('/<path:path>')
def not_found(path):
    m = re.match(r"v(\d+)/(\S*)\??", path)
    if not m:
        message = "'{0}' is not a valid API path.".format(path)
    else:
        requested_API_version = int(m.group(1))
        if requested_API_version != 1:
            message = "{0} is not a valid API version number.".format(requested_API_version)
        else:
            message = "'{0}' is not a valid API endpoint.".format(m.group(2))

    response = jsonify({
        "message": message
    })
    response.status_code = 404
    return response


@api_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


import upcoming_api
upcoming_api.routes.apply_routes(api_blueprint)

import search_api
search_api.routes.apply_routes(api_blueprint)
