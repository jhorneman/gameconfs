from gameconfs import create_app
from gzip_middleware import GzipMiddleware

flask_app, db = create_app("vagrant-test")

app = GzipMiddleware(flask_app, compresslevel=5)
