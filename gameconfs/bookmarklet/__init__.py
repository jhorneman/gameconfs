import os
import re
from flask import Blueprint, render_template, request, send_from_directory
from gameconfs.models import Event
from gameconfs.query_helpers import search_events_by_string


bookmarklet_blueprint = Blueprint('bookmarklet', __name__, url_prefix='/bookmarklet', template_folder='templates', static_folder='static')


@bookmarklet_blueprint.route('/')
def index():
    return render_template('bookmarklet/index.html')


@bookmarklet_blueprint.route('/js/search.js')
def search_js():
    # We're returning this as text/html because we're running it through render_template.
    return render_template('bookmarklet/search.js')


@bookmarklet_blueprint.route('/search')
def search():
    search_string = request.args.get('q', '').strip()
    # document_title = request.args.get('t', '').strip()
    referring_url = request.args.get('u', '').strip()

    found_events_by_string = search_events_by_string(search_string)

    # Strip http or https, www., trailing slash.
    # It's better to search for less data and get a few false positives than to have lots of false negatives.
    match = re.match(r"^(http|https)?://(www.)?(?P<url>.*?)/?$", referring_url, re.IGNORECASE)
    if match:
        found_events_by_url = Event.query. \
            filter(Event.event_url.ilike('%' + match.group('url') + '%')). \
            order_by(Event.start_date.desc()). \
            all()
    else:
        found_events_by_url = []

    return render_template('bookmarklet/search.html', search_string=search_string,
                           referring_url=referring_url, found_events_by_string=found_events_by_string,
                           found_events_by_url=found_events_by_url)
