import json
from flask import Blueprint
from sqlalchemy.orm import joinedload
from gameconfs.models import Series, City, Event


data_blueprint = Blueprint('data', __name__,url_prefix='/data', template_folder='templates', static_folder='static')


@data_blueprint.route('/events.json')
def events():
    data = Event.query.order_by(Event.name).all()
    return json.dumps([d.name for d in data])


@data_blueprint.route('/series.json')
def series():
    data = Series.query.order_by(Series.name).all()
    return json.dumps([d.name for d in data])


@data_blueprint.route('/cities.json')
def cities():
    data = City.query.\
        join(City.country).\
        options(joinedload('country')).\
        order_by(City.name).\
        all()
    data = [{'value': d.name, 'country': d.country.name} for d in data]
    return json.dumps(data)
