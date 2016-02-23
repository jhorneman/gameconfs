# -*- coding: utf-8 -*-

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView as SQLAModelview
from gameconfs import models
from secure_view import secure_view


class InsecureAdminHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render(self._template)


AdminHomeView = secure_view(InsecureAdminHomeView)
ModelView = secure_view(SQLAModelview)


class EventView(ModelView):
    pass


class CityView(ModelView):
    column_list = ('name', 'state', 'country')
    column_searchable_list = ('name',)


class CountryView(ModelView):
    pass


class UserView(ModelView):
    pass


def set_up_views(_app, _db_session):
    admin = Admin(
        _app,
        name="Gameconfs",
        index_view=AdminHomeView(),
        base_template="admin_master.html",
        template_mode="bootstrap3"
    )
    admin.add_view(EventView(models.Event, _db_session))
    admin.add_view(CityView(models.City, _db_session))
    admin.add_view(CountryView(models.Country, _db_session))
    admin.add_view(UserView(models.User, _db_session))
    _app.admin = admin
