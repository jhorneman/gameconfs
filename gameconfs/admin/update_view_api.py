# -*- coding: utf-8 -*-

from flask import jsonify, abort, redirect, url_for, request
from flask.ext.login import current_user
from .. import app
from ..models import *
from ..today import get_today
from ..security import user_has_all_roles


def is_accessible():
    if not current_user or not current_user.is_active or not current_user.is_authenticated:
        return False
    if user_has_all_roles(["admin"]):
        return True
    return False


@app.route('/event/<int:event_id>/set_last_checked', methods=("POST",))
def event_set_last_checked(event_id):
    if not is_accessible():
        if current_user.is_authenticated:
            # permission denied
            abort(403)
        else:
            # login
            return redirect(url_for('security.login', next=request.url))

    try:
        event = Event.query.filter(Event.id == event_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        raise InvalidUsage("Could not find event.", 404)
    else:
        event.last_checked_at = get_today()
        db.session.commit()
        return jsonify({})


@app.route('/event/<int:event_id>/toggle_checking', methods=("POST",))
def event_toggle_checking(event_id):
    if not is_accessible():
        if current_user.is_authenticated:
            # permission denied
            abort(403)
        else:
            # login
            return redirect(url_for('security.login', next=request.url))

    try:
        event = Event.query.filter(Event.id == event_id).one()
    except sqlalchemy.orm.exc.NoResultFound:
        raise InvalidUsage("Could not find event.", 404)
    else:
        event.is_being_checked = not event.is_being_checked
        db.session.commit()
        return jsonify({
            "newState": event.is_being_checked
        })


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


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
