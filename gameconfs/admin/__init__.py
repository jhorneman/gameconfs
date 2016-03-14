# -*- coding: utf-8 -*-

from flask_admin import Admin
from views import AdminHomeView, set_up_views
from update_view import set_up_update_view
from gameconfs.project import PROJECT_NAME


def set_up_admin_interface(_app, _db_session):
    admin = Admin(
        _app,
        name=PROJECT_NAME,
        index_view=AdminHomeView(),
        base_template="admin_master.html",
        template_mode="bootstrap3"
    )
    _app.admin = admin
    set_up_views(admin, _db_session)
    set_up_update_view(admin, _app)
