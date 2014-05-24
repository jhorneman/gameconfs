from datetime import datetime
import logging
import json
from flask import Blueprint, request, jsonify
from sqlalchemy.sql.expression import *
from sqlalchemy.orm import *
from gameconfs.app_logging import add_logger
from gameconfs.models import *
from gameconfs.query_helpers import *


logger = logging.getLogger(__name__)
add_logger(logger)

api_blueprint = Blueprint('api', __name__,url_prefix='/api')


def get_string(_object, _field_name, _reporter):
    try:
        retrieved_string = _object[_field_name]
    except KeyError:
        return None

    if not isinstance(retrieved_string, basestring):
        _reporter("Date field '%s' is not a string" % _field_name)
        return None

    return retrieved_string.strip()


def get_date(_object, _field_name, _reporter):
    date_string = get_string(_object, _field_name, _reporter)
    if not date_string:
        return None

    try:
        # For dates formatted like this: 2012-04-23
        # See also: http://stackoverflow.com/questions/10286204/the-right-json-date-format
        retrieved_date = datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        _reporter("Couldn't parse date '%s' in date field '%s'" % (date_string, _field_name))
        return None

    return retrieved_date


def query_events(_query_object, _reporter):
    # Base query
    q = Event.query.\
        join(Event.city).\
        join(City.country).\
        join(Country.continent).\
        order_by(Event.start_date.asc()).\
        options(joinedload('city'), joinedload('city.country'), joinedload('city.state'))

    # Date or date range filters
    if "date" in _query_object:
        query_date = get_date(_query_object, "date", _reporter)
        if not query_date:
            return []

        q = q.filter(or_(and_(Event.start_date >= query_date, Event.start_date <= query_date),
                         and_(Event.end_date >= query_date, Event.end_date <= query_date)))

    elif "start-date" in _query_object:
        if "end-date" not in _query_object:
            _reporter("Found start date but not end date.")
            return []

        start_date = get_date(_query_object, "start-date", _reporter)
        end_date = get_date(_query_object, "end-date", _reporter)
        if not (start_date and end_date):
            return []

        q = q.filter(or_(and_(Event.start_date >= start_date, Event.start_date <= end_date),
                         and_(Event.end_date >= start_date, Event.end_date <= end_date)))

    elif "end-date" in _query_object:
        _reporter("Found end date but not start date.")
        return []

    # Place name filters
    place_name = get_string(_query_object, "place-name", _reporter)
    if place_name:
        if place_name == "online":
            place_name = "other"

        if place_name == "other":
            q = q.filter(Event.city == None)
        else:
            q, found_place_name = filter_by_place_name(q, place_name)
            if not found_place_name:
                _reporter("Didn't recognize place '%s'" % place_name)
                return []

    # Event name filter
    event_name = get_string(_query_object, "event-name", _reporter)
    if event_name:
        q = q.filter(Event.name.ilike("%" + event_name + "%"))

    return q.all()


def convert_events_for_json(_events):
    result = []
    for event in _events:
        event_data = {
            "name": event.name,
            "event_url": event.event_url,
            "start-date": date.strftime(event.start_date, "%Y-%m-%d"),
            "end-date": date.strftime(event.end_date, "%Y-%m-%d"),
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


def add_error_message(_error_messages, _index, _message):
    _error_messages.append("Query %d: %s" % (_index, _message))


@api_blueprint.route('/search_events', methods=("POST",))
def search_events():
    response = {"NrFoundEvents": 0, "ErrorMessages": None}

    if request.data:
        try:
            request_parameters = json.loads(request.data)
        except ValueError, e:
            logger.error("Couldn't decode request parameter JSON: " + e.message)
            response["ErrorMessages"] = e.message
        else:
            queries = request_parameters["queries"]
            if not isinstance(queries, list):
                queries = [queries]

            all_found_events = []
            error_messages = []

            for index, query in enumerate(queries):
                def report(_message):
                    add_error_message(error_messages, index, _message)

                if not isinstance(query, dict):
                    report("Query is not an object")
                    continue

                query_results = query_events(query, report)
                all_found_events += query_results

            response["NrFoundEvents"] = len(all_found_events)
            response["Results"] = convert_events_for_json(all_found_events)
            response["ErrorMessages"] = "\n".join(error_messages)
    else:
        response["ErrorMessages"] = "No queries found in request"

    return jsonify(response)
