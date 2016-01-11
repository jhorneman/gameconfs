# -*- coding: utf-8 -*-

from flask import request, redirect, url_for, abort
from flask.ext.principal import RoleNeed, Permission
from flask_admin.form import SecureForm
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView as SQLAModelview
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


# Create a customized model view class to let Flask-Admin work with Flask-Security.
# See https://github.com/flask-admin/flask-admin/blob/master/examples/auth/app.py.
class AdminModelView(SQLAModelview):
    form_base_class = SecureForm

    def is_accessible(self):
        if not current_user or not current_user.is_active or not current_user.is_authenticated:
            return False
        if user_has_all_roles(["admin"]):
            return True
        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


class AdminHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render(self._template)

    def is_accessible(self):
        if not current_user or not current_user.is_active or not current_user.is_authenticated:
            return False
        if user_has_all_roles(["admin"]):
            return True
        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))
