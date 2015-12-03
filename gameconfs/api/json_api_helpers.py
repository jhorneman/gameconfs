# -*- coding: utf-8 -*-

from werkzeug.exceptions import HTTPException, default_exceptions
from flask import jsonify


integer_types = (int, long)     # From https://github.com/mitsuhiko/flask/blob/master/flask/_compat.py#L40


def set_up_JSON_api_error_handlers(_app, _blueprint):
    for code in default_exceptions.iterkeys():
        register_blueprint_error_handler(_app, _blueprint, code, make_json_error)
    register_blueprint_error_handler(_app, _blueprint, Exception, make_json_error)


# Function hacked together because Blueprint.register_error_handler, which is not yet in 0.10.1.
# See https://github.com/mitsuhiko/flask/blob/master/flask/blueprints.py#L404
# and https://github.com/mitsuhiko/flask/blob/master/flask/app.py#L1168.
def register_blueprint_error_handler(_app, _blueprint, _code_or_exception, _error_handler):
    exc_class, code = _get_exc_class_and_code(_code_or_exception)
    handlers = _app.error_handler_spec.setdefault(_blueprint.name, {}).setdefault(code, {})
    if code is None:
        handlers.append((exc_class, _error_handler))
    else:
        handlers[exc_class] = _error_handler


# Based on snippet by Pavel Repin, see http://flask.pocoo.org/snippets/83/
def make_json_error(e):
    response = jsonify(message=str(e))
    response.status_code = (e.code if isinstance(e, HTTPException) else 500)
    return response


# Copied from https://github.com/mitsuhiko/flask/blob/master/flask/app.py#L1097
def _get_exc_class_and_code(exc_class_or_code):
    """Ensure that we register only exceptions as handler keys"""
    if isinstance(exc_class_or_code, integer_types):
        exc_class = default_exceptions[exc_class_or_code]
    else:
        exc_class = exc_class_or_code

    assert issubclass(exc_class, Exception)

    if issubclass(exc_class, HTTPException):
        return exc_class, exc_class.code
    else:
        return exc_class, None
