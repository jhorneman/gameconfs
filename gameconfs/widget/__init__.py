import os
import re
import json
from dateutil.relativedelta import *
from flask import Blueprint, render_template, send_from_directory, request, abort, jsonify
from gameconfs.query_helpers import *
from gameconfs.today import get_today
from gameconfs.json_api_helpers import set_up_JSON_api_error_handlers


widget_blueprint = Blueprint('widget', __name__,url_prefix='/widget', template_folder='templates', static_folder='static')


def set_up_blueprint(_app):
    set_up_JSON_api_error_handlers(_app, widget_blueprint)


@widget_blueprint.route('/')
def index():
    return render_template('widget/index.html')


@widget_blueprint.route('/v1/script.js')
def script():
    return send_from_directory(os.path.join(widget_blueprint.root_path, 'static/js'), 'script.js', mimetype='text/javascript')


def send_css_file(_filename):
    return send_from_directory(os.path.join(widget_blueprint.root_path, 'static/css'), _filename + '.css', mimetype='text/css')


@widget_blueprint.route('/v1/cleanslate.css')
def cleanslate_css():
    return send_css_file('cleanslate')


@widget_blueprint.route('/v1/widget.css')
def widget_css():
    return send_css_file('widget')


@widget_blueprint.route('/v1/data.json')
def data():
    # For GET requests, which is what we have, we can only get the parameters from the URL arguments.
    request_parameters = request.args

    # Make sure we only received parameters we know.
    for param in request_parameters.keys():
        if param not in ["callback", "nr-months", "place"]:
            raise InvalidUsage("Did not recognize parameter {0}.".format(param))

    # Fail if no JSONP callback name was given.
    callback = request_parameters.get('callback', None)
    if callback is None:
        raise InvalidUsage("No JSONP callback parameter found.")

    # Get parameters.
    nr_months = 3
    if "nr-months" in request_parameters:
        nr_months = request_parameters["nr-months"]
        try:
            nr_months = int(nr_months)
        except ValueError:
            raise InvalidUsage("Could not parse nr-months value '{0}'.".format(nr_months))

    if nr_months < 1:
        raise InvalidUsage("nr-months must be at least 1.")
    elif nr_months > 12:
        raise InvalidUsage("nr-months may not be higher than 12.")

    place_name = None
    if "place" in request_parameters:
        place_name = request_parameters["place"].strip()
        if len(place_name) == 0:
            raise InvalidUsage("Place argument was empty.")

    # Get time period.
    today = get_today()
    start_date = today
    end_date = start_date + relativedelta(days=1, months=nr_months)

    # Find events.
    q = filter_published_only(Event.query)
    q = order_by_newest_event(q)
    q = filter_by_period_start_end(q, start_date, end_date)

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

    html = render_template('widget/contents.html', events=found_events, today=today,
                           nr_months=nr_months, place_name=found_location_name)
    return "%s({'html':%s})" % (callback, json.dumps(html))


@widget_blueprint.route('/', defaults={'path': ''})
@widget_blueprint.route('/<path:path>')
def not_found(path):
    m = re.match(r"v(\d+)/(\S*)\??", path)
    if not m:
        message = "'{0}' is not a valid path.".format(path)
    else:
        requested_API_version = int(m.group(1))
        if requested_API_version != 1:
            message = "{0} is not a valid version number.".format(requested_API_version)
        else:
            message = "'{0}' is not a valid endpoint.".format(m.group(2))

    response = jsonify({
        "message": message
    })
    response.status_code = 404
    return response


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


@widget_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
