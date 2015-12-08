# -*- coding: utf-8 -*-

from flask import request, jsonify
from gameconfs.query_helpers import *
from gameconfs.today import get_today
from gameconfs.view_module_helper import DeferredRoutes
from . import InvalidUsage, convert_events_for_JSON, parse_date


__all__ = ["routes"]


routes = DeferredRoutes()
route = routes.get_decorator()


@route("/v1/search_events")
def search_events():
    # For GET requests, which is what we have, we can only get the parameters from the URL arguments.
    request_parameters = request.args

    # Make sure we only received parameters we know.
    for param in request_parameters.keys():
        if param not in ["date", "startDate", "endDate", "eventName", "place"]:
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
