from gameconfs import create_app

class Middleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

flask_app, db = create_app("production")

app = Middleware(flask_app)
