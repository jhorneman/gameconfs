from . import create_app
from gzip_middleware import GzipMiddleware

# This module is executed by Gunicorn via Heroku's Procfile.
# Return a WSGI application.

flask_app, db = create_app("production")

app = GzipMiddleware(flask_app)
