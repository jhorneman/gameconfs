import os
import json
from dateutil import relativedelta
from flask import Blueprint, render_template, send_from_directory, request, abort
from gameconfs.query_helpers import *
from gameconfs.today import get_today


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

    today = get_today()

    start_date = today
    end_date = start_date + relativedelta(months=nr_months)

    q = filter_published_only(Event.query)
    q = order_by_newest_event(q)
    q = filter_by_period_start_end(q, start_date, end_date)

    if place_name:
        if place_name == "other":
            q = q.filter(Event.city == None)
            found_location_name = "other"
        else:
            q = q.join(Event.city).\
                join(City.country).\
                join(Country.continent).\
                options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
            q, found_location_name = filter_by_place_name(q, place_name)
        if found_location_name:
            events = q.all()
        else:
            events = []
    else:
        events = q.all()

    html = render_template('widget/contents.html', events=events, today=today,
                           nr_months=nr_months, place_name=place_name)
    return "%s({'html':%s})" % (callback, json.dumps(html))
