import re
from flask import Blueprint, render_template, request
from gameconfs.helpers import *


bookmarklet_blueprint = Blueprint('bookmarklet', __name__,url_prefix='/bookmarklet', template_folder='templates', static_folder='static')


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

    if not search_string:
        found_events_by_string = []
    else:
        found_events_by_string = Event.query. \
            filter(or_(Event.name.ilike('%' + search_string + '%'), Event.twitter_hashtags.ilike('%' + search_string + '%'),
                       Event.twitter_account.ilike('%' + search_string + '%'), Event.event_url.ilike('%' + search_string + '%'))). \
            order_by(Event.start_date). \
            all()

    search_url = referring_url
    if search_url.endswith('/'):
        search_url = search_url[:-1]
    found_events_by_url = Event.query. \
        filter(Event.event_url.ilike('%' + search_url + '%')). \
        order_by(Event.start_date). \
        all()

    return render_template('bookmarklet/search.html', search_string=search_string,
                           referring_url=referring_url, found_events_by_string=found_events_by_string,
                           found_events_by_url=found_events_by_url)
