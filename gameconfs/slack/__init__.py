# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify
from gameconfs.query_helpers import search_events_by_string
from gameconfs.jinja_filters import short_range
from slack_utils import escape_text_for_slack


slack_blueprint = Blueprint("slack", __name__, url_prefix="/slack")


@slack_blueprint.route("/")
def slack():
    command = request.args.get("command", "").strip()
    if command != "/confs":
        return "I don't know the command '{0}'.".format(command)

    search_string = request.args.get("text", "").strip()
    if len(search_string) == 0:
        return "Enter search criteria after the command, e.g. '/confs London'."

    found_events = search_events_by_string(search_string)

    if len(found_events) == 0:
        return "I didn't find any upcoming events for '{0}'.".format(search_string)

    message = "I found {0} upcoming events".format(len(found_events)) if len(found_events) > 1 else "I found 1 event"

    message += " for '{0}':\n".format( search_string)

    message += u"\n".join([u"{2}|{0} ({1})".format(event.name, short_range(event), event.event_url) for event in found_events])

    response = jsonify({
        "text": message
    })
    response.status_code = 200
    return response
