# This module encapsulates everything related to selecting and loading configurations,
# creating the Flask app, and running it.
#
# The application's behavior depends on:
#   the RUN MODE - how the application behaves, the role it's in
#   the RUN ENVIRONMENT - where it's running and how it connects to external services
#   KILL SWITCHES - used to turn off certain features, overriding the run mode and the run environment
#
# The following run modes are supported:
#   dev        - for development.
#   test       - for automated testing.
#   production - for live operations.
#
# The run environment is only valid in production mode, and is set using the GAMECONFS_RUN_ENV
# environment variable.
#
# The following run environments are supported:
#   local   - a developers' local machine.
#   heroku  - on Heroku or locally using Foreman.
#   vagrant - in a VM managed using Vagrant.
#
# Running the app also depends on the configuration. So we can't just create the app here,
# we also need to provide a function to run it.

import sys
import os
import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask_principal import Principal
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.mail import Mail
from jinja_filters import set_up_jinja_filters
from caching import set_up_cache


# Set to None so code will fail screaming if create_app or run_app haven't been called
app = None
app_run_args = {}

db = SQLAlchemy()


def create_app(_run_mode=None):
    # Create Flask app
    global app
    app = Flask("gameconfs")

    # Load kill switches
    app.config["GAMECONFS_KILL_CACHE"] = os.environ.get("GAMECONFS_KILL_CACHE", False)

    # Load default configuration
    app.config.from_object("gameconfs.default_config")

    # Dev run mode
    if _run_mode == "dev":
        app.config["DEBUG"] = True

        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://gdcal-dev:gdcal@localhost:5432/gdcal-dev"

        app.config["CACHE_TYPE"] = "gameconfs.caching.bmemcached_cache"
        app.config["CACHE_MEMCACHED_SERVERS"] = ["0.0.0.0:11211"]
        app.config["CACHE_MEMCACHED_USERNAME"] = None
        app.config["CACHE_MEMCACHED_PASSWORD"] = None

        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        toolbar = DebugToolbarExtension(app)

    # Test run mode
    elif _run_mode == "test":
        app.config["DEBUG"] = True
        app.config["TESTING"] = True
        app.config["GAMECONFS_KILL_CACHE"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Production run mode
    elif _run_mode == "production":
        # Get additional configuration based on run environment
        run_environment = os.environ.get("GAMECONFS_RUN_ENV", "local")
        if run_environment == "heroku":
            # Get configuration data from Heroku environment variables
            app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

            app.config["CACHE_TYPE"] = "gameconfs.caching.bmemcached_cache"
            app.config["CACHE_MEMCACHED_SERVERS"] = os.environ.get("MEMCACHEDCLOUD_SERVERS").split(",")
            app.config["CACHE_MEMCACHED_USERNAME"] = os.environ.get("MEMCACHEDCLOUD_USERNAME")
            app.config["CACHE_MEMCACHED_PASSWORD"] = os.environ.get("MEMCACHEDCLOUD_PASSWORD")

            app.config["MAIL_SERVER"] = "smtp.mandrillapp.com"
            app.config["MAIL_PORT"] = 587
            app.config["MAIL_USERNAME"] = os.environ.get("MANDRILL_USERNAME")
            app.config["MAIL_PASSWORD"] = os.environ.get("MANDRILL_APIKEY")
            app.config["MAIL_USE_TLS"] = True

            app_run_args["port"] = int(os.environ["PORT"])
            app_run_args["host"] = "0.0.0.0"

        elif run_environment == "vagrant":
            app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://gdcal-dev:gdcal@localhost:5432/gdcal-dev"

        set_up_logging()

    # Unrecognized run mode
    else:
        logging.error("Did not recognize run mode '%s'" % _run_mode)
        return (None, None)

    # Initialize the database
    global db
    import gameconfs.models
    db.init_app(app)

    # Set up Flask-Security
    # (Hang new variables off app to avoid terrible circular import issues.)
    # app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
    # app.config['SECURITY_PASSWORD_SALT'] = '4tjDFbMVTbmVYULHbj2baaGk'
    app.config["SECURITY_EMAIL_SENDER"] = "admin@gameconfs.com"

    app.user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    app.security = Security(app, app.user_datastore)

    # Initialize the cache
    if app.config["GAMECONFS_KILL_CACHE"]:
        app.config["CACHE_TYPE"] = "null"
    set_up_cache(app)

    # Load the Principal extension
    app.principals = Principal(app)

    # Import the views, to apply the decorators which use the global app object.
    import gameconfs.views

    # Register blueprints
    from gameconfs.widget import widget_blueprint
    app.register_blueprint(widget_blueprint)

    from gameconfs.bookmarklet import bookmarklet_blueprint
    app.register_blueprint(bookmarklet_blueprint)

    from gameconfs.data import data_blueprint
    app.register_blueprint(data_blueprint)

    from gameconfs.admin import admin_blueprint
    app.register_blueprint(admin_blueprint)

    # Set up Jinja 2 filters
    set_up_jinja_filters(app)

    # Set up email
    app.mail = Mail(app)

    return app, db


class StdoutHandler(logging.StreamHandler):
    def __init__(self):
        super(StdoutHandler, self).__init__(sys.stdout)

    def emit(self, record):
        super(StdoutHandler, self).emit(record)
        super(StdoutHandler, self).flush()


def set_up_logging(_level=logging.INFO):
    handler = StdoutHandler()
    handler.setLevel(_level)
    handler.setFormatter(logging.Formatter('%(message)s'))
    app.logger.setLevel(_level)
    app.logger.addHandler(handler)


def run_app():
    # Run the application
    # See flask/app.py run() for the implementation of run().
    # See http://werkzeug.pocoo.org/docs/serving/ for the parameters of Werkzeug's run_simple().
    # If the debug parameter is not set, Flask does not change app.debug, which is set from
    # the DEBUG app config variable, which we've set in create_app().
    app.run(**app_run_args)
