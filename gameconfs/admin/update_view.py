# -*- coding: utf-8 -*-

from datetime import date
import calendar
from dateutil.relativedelta import *
from flask_admin import BaseView, expose
from gameconfs.today import get_today
from secure_view import secure_view
import update_view_api      # Importing it so it gets run
from sqlalchemy.sql.expression import *
from sqlalchemy.orm import joinedload
from gameconfs.models import *


class InsecureSpecialView(BaseView):
    @expose('/')
    def index(self):
        today = get_today()

        # We need to find a time that is a year plus the time since the last time we checked this ago.
        # We assume this list will be checked at least every 6 months.
        new_year = today.year - 1

        new_month = today.month - 6
        if new_month < 1:
            new_year -= 1
            new_month += 6

        new_day = today.day
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        if new_day > last_day_of_month:
            new_day = last_day_of_month

        a_while_ago = date(new_year, new_month, new_day)

        events_due_for_update = Event.query.\
            filter(and_(Event.series_id == None,
                        Event.is_being_checked == True,
                        Event.start_date >= a_while_ago,
                        Event.start_date < today)).\
            order_by(Event.start_date.asc()).\
            options(joinedload('city'), joinedload('city.country'), joinedload('city.state')).\
            all()

        for series in Series.query.all():
            event = Event.query.\
                filter(Event.series_id == series.id).\
                order_by(Event.start_date.desc()).\
                options(joinedload('city'), joinedload('city.country'), joinedload('city.state')).\
                first()
            if event:
                if event.start_date >= a_while_ago and event.start_date < today and event.is_being_checked:
                    events_due_for_update.append(event)

        events_due_for_update = sorted(events_due_for_update, cmp=compare_events_due_for_update)

        return self.render(
            'events_due_for_update.html',
            events_due_for_update=events_due_for_update,
            body_id='events_update',
            full_width=True
        )

SpecialView = secure_view(InsecureSpecialView)


def compare_events_due_for_update(_a, _b):
    c = cmp(_a.last_checked_at, _b.last_checked_at)
    if c != 0:
        return c
    return cmp(_a.start_date, _b.start_date)


def select_due_color_class(_date):
    diff = relativedelta(_date, get_today())
    if diff.years < 0 or diff.months < -6:
        return "overdue"
    if diff.years == 0 and diff.months < -3:
        return "due"
    if diff.years >= 0 and diff.months >= -1:
        return "recently-checked"
    return ""


def set_up_update_view(_admin, _app):
    _app.add_template_filter(select_due_color_class, name="due_color")
    _admin.add_view(SpecialView(name='Event Updates', endpoint='special'))
