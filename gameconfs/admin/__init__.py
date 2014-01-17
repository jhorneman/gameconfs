import re
from datetime import date
from flask import Blueprint, render_template
from sqlalchemy.sql.expression import *
from flask.ext.security.decorators import roles_required
from gameconfs.models import *
from gameconfs.views import editing_kill_check


admin_blueprint = Blueprint('admin', __name__,url_prefix='/admin', template_folder='templates', static_folder='static')


@admin_blueprint.route('/')
@editing_kill_check
@roles_required('admin')
def index():
    return render_template('admin/index.html')


@admin_blueprint.route('/series')
@editing_kill_check
@roles_required('admin')
def view_all_series():
    all_series_data = []
    for series in Series.query.order_by(Series.name):
        all_series_data.append((series, Event.query.filter(Event.series_id == series.id).count()))
    return render_template('admin/all_series.html', all_series_data=all_series_data)


@admin_blueprint.route('/no-series')
@editing_kill_check
@roles_required('admin')
def view_events_without_series():
    events_without_series = Event.query.filter(Event.series_id == None).order_by(Event.name).all()
    return render_template('admin/no_series.html', events_without_series=events_without_series)


@admin_blueprint.route('/problematic-events')
@editing_kill_check
@roles_required('admin')
def view_problematic_events():
    problematic_events = []
    year_regex = re.compile(".*(20\d\d).*")
    for event in Event.query.filter(Event.name.op('~')(".*20\d\d.*")).order_by(Event.name).all():
        year = int(year_regex.match(event.name).group(1))
        if year != event.start_date.year:
            problematic_events.append(event)
    return render_template('admin/problematic_events.html', problematic_events=problematic_events)


@admin_blueprint.route('/events-due-for-update')
@editing_kill_check
@roles_required('admin')
def view_events_due_for_update():
    today = date.today()
    if today.month == 2 and today.day == 29:
        a_year_ago = date(today.year-1, today.month, today.day-1)
    else:
        a_year_ago = date(today.year-1, today.month, today.day)

    events_due_for_update = Event.query.\
        filter(and_(Event.series_id == None,
                    Event.start_date >= a_year_ago,
                    Event.start_date < today)).\
        order_by(Event.start_date.asc()).\
        all()

    for series in Series.query.all():
        event = Event.query.\
            filter(Event.series_id == series.id).\
            order_by(Event.start_date.desc()).\
            first()
        if event:
            if event.start_date >= a_year_ago and event.start_date < today:
                events_due_for_update.append(event)

    events_due_for_update = sorted(events_due_for_update, key=lambda event: event.start_date)

    return render_template('admin/events_due_for_update.html', events_due_for_update=events_due_for_update)
