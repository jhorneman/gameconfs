from flask import Blueprint, render_template, request
from gameconfs.models import Event
from gameconfs.query_helpers import search_events_by_string


bookmarklet_blueprint = Blueprint('bookmarklet', __name__, url_prefix='/bookmarklet', template_folder='templates', static_folder='static')


@bookmarklet_blueprint.route('/')
def index():
    return render_template('bookmarklet/index.html')


@bookmarklet_blueprint.route('/js/search.js')
def search_js():
    return render_template('bookmarklet/search.js')


@bookmarklet_blueprint.route('/search')
def search():
    search_string = request.args.get('q', '').strip()
    # document_title = request.args.get('t', '').strip()
    referring_url = request.args.get('u', '').strip()

    found_events_by_string = search_events_by_string(search_string)

    search_url = referring_url
    if search_url.endswith('/'):
        search_url = search_url[:-1]
    found_events_by_url = Event.query. \
        filter(Event.event_url.ilike('%' + search_url + '%')). \
        order_by(Event.start_date.desc()). \
        all()

    return render_template('bookmarklet/search.html', search_string=search_string,
                           referring_url=referring_url, found_events_by_string=found_events_by_string,
                           found_events_by_url=found_events_by_url)
