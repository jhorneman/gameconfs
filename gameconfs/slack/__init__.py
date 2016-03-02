# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify
from gameconfs.query_helpers import *
from gameconfs.jinja_filters import short_range
from gameconfs.today import get_today
from gameconfs.models import Event
from slack_utils import escape_text_for_slack


slack_blueprint = Blueprint("slack", __name__, url_prefix="/slack")


def found_message(_found_events):
    return "I found {0} upcoming events".format(len(_found_events)) if len(_found_events) > 1 else "I found 1 event"


@slack_blueprint.route("/")
def slack():
    command = request.args.get("command", "").strip()
    if command != "/confs":
        return "Sorry, I don't know the command '{0}'.".format(command)

    search_string = request.args.get("text", "").strip()
    if len(search_string) == 0:
        return "Please enter search criteria after the command, like '/confs London' or '/confs GDC'."

    today = get_today()

    query = build_search_events_by_string_query(search_string)
    query = query.filter(Event.end_date >= today)

    found_events_by_name = query.all()

    query = filter_published_only(Event.query)
    query = order_by_newest_event(query)
    query = query.filter(Event.end_date >= today)

    if search_string == "other":
        query = query.filter(Event.city == None)
        found_location_name = "other"
    else:
        query = query.join(Event.city).\
            join(City.country).\
            join(Country.continent).\
            options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
        query, found_location_name = filter_by_place_name(query, search_string)

    found_events_by_place = query.all() if found_location_name else []

    if len(found_events_by_name) == 0 and found_location_name is None:
        return "Sorry, I couldn't find any upcoming events for '{0}'.".format(search_string)

    message = ""

    if len(found_events_by_name) > 0:
        message += found_message(found_events_by_name) + " with '{0}':\n".format( search_string)
        message += u"\n".join([u"<{2}|{0}> ({1}, {3})".\
                              format(escape_text_for_slack(event.name), short_range(event), event.event_url, event.city_and_state_or_country())
                              for event in found_events_by_name])

    if len(found_events_by_place) > 0:
        if len(found_events_by_name) > 0:
            message += "\n\n"

        message += found_message(found_events_by_place) + " in {0}:\n".format(found_location_name)
        message += u"\n".join([u"<{2}|{0}> ({1})".format(escape_text_for_slack(event.name), short_range(event), event.event_url) for event in found_events_by_name])

    response = jsonify({
        "text": message,
        "unfurl_media": False
    })
    response.status_code = 200
    return response
