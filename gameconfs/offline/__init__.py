from flask import Blueprint


offline_blueprint = Blueprint('offline', __name__,url_prefix='/offline', static_folder='static')
