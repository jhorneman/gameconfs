# -*- coding: utf-8 -*-

from flask import request, redirect, url_for, abort
from flask_admin.form import SecureForm
from flask.ext.login import current_user
from gameconfs.security import user_is_logged_in, user_has_all_roles


# Take a Flask-Admin view class and return a derived class that uses Flask-Security.
# See https://github.com/flask-admin/flask-admin/blob/master/examples/auth/app.py.
def secure_view(view_class):
    class SecuredView(view_class):
        form_base_class = SecureForm

        def is_accessible(self):
            if not user_is_logged_in():
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

    return SecuredView
