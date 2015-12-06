from datetime import date
import calendar
from flask import Blueprint, render_template
from sqlalchemy.sql.expression import *
from sqlalchemy.orm import joinedload
from flask.ext.security.decorators import roles_required
from gameconfs.models import *
from gameconfs.views import editing_kill_check
from gameconfs.today import get_today


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

    q = Event.query.filter(not_(Event.event_url.startswith("http")))
    problematic_events += q.all()

    return render_template('admin/problematic_events.html', problematic_events=problematic_events)


@admin_blueprint.route('/events-due-for-update')
@editing_kill_check
@roles_required('admin')
def view_events_due_for_update():
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
            if event.start_date >= a_while_ago and event.start_date < today:
                events_due_for_update.append(event)

    events_due_for_update = sorted(events_due_for_update, key=lambda event: event.start_date)

    return render_template(
        'admin/events_due_for_update.html',
        events_due_for_update=events_due_for_update,
        body_id='events_update',
        full_width=True
    )
