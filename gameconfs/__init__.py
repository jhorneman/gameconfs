# This module encapsulates everything related to selecting and loading configurations,
# creating the Flask app, and running it.
#
# We need the following run modes:
#   dev        - local, personal development server.
#   test       - used for automated testing.
#   team       - still local server, for development by team (specifically non-coder team members).
#   production - deployed on Heroku.
#
# Don't use environment variables for local configurations.
# Environment variables are annoying to set locally (global machine changes for a single project).
# Also we need to be able to run multiple servers on one machine (for dev/team).
#
# For production configuration, use whichever environment variables Heroku provides.
# But isolate this so it can be easily changed if we need to deploy somewhere else.
#
# Make production the default configuration so we never run in debug mode on the server by
# accident. 
#
# Isolate secrets and make it so they're only deployed if necessary
# (Can't really think of anything - there are secrets but they're needed in production. But
#  keep it mind.)
#
# Bundle default and per-configuration settings in clear places.
#
# Running the app also depends on the configuration. So we can't just create the app here,
# we also need to run it.
#
# If this code grows we could move it into its own module instead of __init__.

import os
import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask_principal import Principal
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from filters import init_template_filters


# Set to None so code will fail screaming if create_app or run_app haven't been called
app = None
app_run_args = {}

db = SQLAlchemy()


def create_app(_run_mode):
    # Set up logging
    # if _run_mode != 'dev':
    #     # This messes up Werkzeug's console output - no idea why
    #     console = logging.StreamHandler()
    #     console.setLevel(logging.INFO)
    #     console.setFormatter(logging.Formatter('%(message)s'))
    #     logging.getLogger('').addHandler(console)

    # Create Flask app
    global app
    app = Flask("gameconfs")

    # Load default configuration
    app.config.from_object('gameconfs.default_config')

    # app.debug and app.config["DEBUG"] do the same thing. app.debug defaults to False.
    # To be extra sure default_config doesn't change this behavior, we set it to False again,
    # because we want to make sure we don't run debug in production by accident.
    app.config["DEBUG"] = False

    # (In the latest version of Flask we could set port and host to None so the Flask defaults will
    # be used if we don't change these variables.)
    global app_run_args
    app_run_args = {'port': 5000, 'host': '127.0.0.1'}

    # Dev run mode
    if _run_mode == "dev":
        app.config["DEBUG"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://gdcal-dev:gdcal@localhost:5432/gdcal-dev"
#        toolbar = DebugToolbarExtension(app)

    # Test run mode
    elif _run_mode == "test":
        app.config["DEBUG"] = True
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Production run mode
    elif _run_mode == "production":
        # Get configuration data from Heroku environment variables
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL'))
        app_run_args['port'] = int(os.environ['PORT'])
        app_run_args['host'] = '0.0.0.0'
        app_run_args['SECURITY_PASSWORD_HASH'] = 'bcrypt'
        app_run_args['SECURITY_PASSWORD_SALT'] = '4tjDFbMVTbmVYULHbj2baaGk'
        app_run_args['SECURITY_EMAIL_SENDER'] = 'admin@gameconfs.com'

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
    app.user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    app.security = Security(app, app.user_datastore)

    # Load the Principal extension
    app.principals = Principal(app)

    # Import the views, to apply the decorators which use the global app object.
    import gameconfs.views
    
    # Set up Jinja2 filters
    init_template_filters(app)

    return (app, db)


def run_app():
    # Run the application
    # See flask/app.py run() for the implementation of run().
    # See http://werkzeug.pocoo.org/docs/serving/ for the parameters of Werkzeug's run_simple().
    # If the debug parameter is not set, Flask does not change app.debug, which is set from
    # the DEBUG app config variable, which we've set in create_app().
    app.run(**app_run_args)
