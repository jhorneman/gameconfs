# -*- coding: utf-8 -*-

from functools import wraps
from flask import render_template, current_app
from flask.ext.principal import RoleNeed, Permission
from flask.ext.login import current_user


# Copy of Flask-Security's roles_required decorator so we can call it without the decorator.
# E.g. in a Flask-Admin model view.
# See https://github.com/mattupstate/flask-security/blob/develop/flask_security/decorators.py#L163
def user_has_all_roles(_roles):
    perms = [Permission(RoleNeed(role)) for role in _roles]
    for perm in perms:
        if not perm.can():
            return False
    return True


def editing_kill_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config["GAMECONFS_KILL_EDITING"]:
            return render_template('page_not_found.html'), 404
        return f(*args, **kwargs)
    return decorated_function


def user_is_logged_in():
    return current_user and current_user.is_active and current_user.is_authenticated


def user_can_edit():
    return user_is_logged_in() and not current_app.config["GAMECONFS_KILL_EDITING"]
