# -*- coding: utf-8 -*-

from dateutil.relativedelta import *
from flask import request, jsonify
from gameconfs.query_helpers import *
from gameconfs.today import get_today
from gameconfs.view_module_helper import DeferredRoutes
from . import InvalidUsage, convert_events_for_JSON


__all__ = ["routes"]


routes = DeferredRoutes()
route = routes.get_decorator()


@route("/v1/upcoming")
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
    start_date = get_today()
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
