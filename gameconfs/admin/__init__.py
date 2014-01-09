from flask import Blueprint, render_template
from gameconfs.models import *


admin_blueprint = Blueprint('admin', __name__,url_prefix='/admin', template_folder='templates', static_folder='static')


@admin_blueprint.route('/')
def index():
    return render_template('admin/index.html')


@admin_blueprint.route('/series')
def view_all_series():
    all_series_data = []
    for series in Series.query.order_by(Series.name):
        all_series_data.append((series, Event.query.filter(Event.series_id == series.id).count()))
    return render_template('admin/all_series.html', all_series_data=all_series_data)


@admin_blueprint.route('/no-series')
def view_events_without_series():
    events_without_series = Event.query.filter(Event.series_id == None).order_by(Event.name).all()
    return render_template('admin/no_series.html', events_without_series=events_without_series)
