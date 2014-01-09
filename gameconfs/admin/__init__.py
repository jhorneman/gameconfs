import os
import json
from flask import Blueprint, render_template, send_from_directory, request, abort
from gameconfs.helpers import *


admin_blueprint = Blueprint('admin', __name__,url_prefix='/admin', template_folder='templates', static_folder='static')


@admin_blueprint.route('/')
def index():
    return render_template('admin/index.html')
