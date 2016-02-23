# -*- coding: utf-8 -*-

from flask.ext.principal import RoleNeed, Permission


# Copy of Flask-Security's roles_required decorator so we can call it without the decorator.
# E.g. in a Flask-Admin model view.
# See https://github.com/mattupstate/flask-security/blob/develop/flask_security/decorators.py#L163
def user_has_all_roles(_roles):
    perms = [Permission(RoleNeed(role)) for role in _roles]
    for perm in perms:
        if not perm.can():
            return False
    return True
