from flask import render_template
from application import app, db
from application.models import *

@app.teardown_request
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def index():
    return redirect(url_for('events'))

@app.route('/event/')
def events():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/event/<id>')
def event(id):
    event = Event.query.filter(Event.id == id).one()
    return render_template('event.html', event=event)
