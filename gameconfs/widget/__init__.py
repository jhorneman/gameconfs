import os
import json
from flask import Blueprint, render_template, send_from_directory, request, abort
from gameconfs.query_helpers import *


widget_blueprint = Blueprint('widget', __name__,url_prefix='/widget', template_folder='templates', static_folder='static')


@widget_blueprint.route('/')
def index():
    return render_template('widget/index.html')


@widget_blueprint.route('/v<int:version>/script.js')
def script(version):
    return send_from_directory(os.path.join(widget_blueprint.root_path, 'static/js'), 'script.js', mimetype='text/javascript')


@widget_blueprint.route('/v<int:version>/<filename>.css')
def css(version, filename):
    return send_from_directory(os.path.join(widget_blueprint.root_path, 'static/css'), filename + '.css', mimetype='text/css')


@widget_blueprint.route('/v<int:version>/data.json')
def data(version):
    # Fail if no JSONP callback name was given
    callback = request.args.get('callback', None)
    if callback is None:
        abort(400)

    # Get number of months, make sure it's a reasonable value
    nr_months = 3
    try:
        nr_months = int(request.args.get('nr-months', 3))
    except ValueError:
        pass
    if nr_months < 1:
        nr_months = 1
    elif nr_months > 12:
        nr_months = 12

    place_name = request.args.get('place', None)

    today = date.today()
    year = today.year

    period_start, period_end = get_month_period(year, today.month, nr_months)

    q = Event.base_query()
    q = filter_by_period_start_end(q, period_start, period_end)

    if place_name:
        q, found_location_name = filter_by_place_name(q, place_name)
        if found_location_name:
            events = q.all()
        else:
            events = []
    else:
        events = q.all()

    html = render_template('widget/contents.html', events=events, year=year, today=today,
                           period_start=period_start, period_end=period_end,
                           nr_months=nr_months, place_name=place_name)
    return "%s({'html':%s})" % (callback, json.dumps(html))
