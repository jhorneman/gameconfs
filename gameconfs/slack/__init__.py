# -*- coding: utf-8 -*-

from flask import Blueprint, request
from gameconfs.query_helpers import search_events_by_string
from gameconfs.jinja_filters import short_range


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

    message += " for '{0}':<br/>".format( search_string)

    message += u"<br/>".join([u"{0} ({1})".format(event.name, short_range(event)) for event in found_events])

    return message
