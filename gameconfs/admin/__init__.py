# -*- coding: utf-8 -*-

from views import set_up_views
from update_view import set_up_update_view


def set_up_admin_interface(_app, _db_session):
    set_up_views(_app, _db_session)
    set_up_update_view(_app)
