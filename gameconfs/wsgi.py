from . import create_app
from gzip_middleware import GzipMiddleware

flask_app, db = create_app("production")

app = GzipMiddleware(flask_app)
