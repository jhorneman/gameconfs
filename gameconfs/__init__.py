# This module encapsulates everything related to creating the Flask app, including selecting and
# loading configurations.
#
# The application's behavior depends on:
#   the RUN MODE - the role it's in,
#   the RUN ENVIRONMENT - where it's running (how it connects to external services), and
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

import os
import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.mail import Mail
from werkzeug.routing import BaseConverter
from jinja_filters import set_up_jinja_filters
from .project import PROJECT_NAME, ADMIN_EMAIL
from .caching import set_up_cache
from .app_logging import set_up_logging
from .kill_switches import load_all_kill_switches, is_feature_on, turn_feature_off


app = None  # Set to None so code will fail screaming if create_app hasn't been called
db = SQLAlchemy()


class RegexIconURLConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexIconURLConverter, self).__init__(url_map)
        self.regex = items[0]


def create_app(_run_mode=None):
    # Create Flask app
    global app
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app = Flask("gameconfs", template_folder=template_dir)

    # Load kill switches
    load_all_kill_switches(app)

    # Load default configuration
    app.config.from_object("gameconfs.default_config")

    # Dev run mode
    if _run_mode == "dev":
        app.config["DEBUG"] = True

        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://gameconfs@localhost:5432/gameconfs"

        # app.config["CACHE_TYPE"] = "gameconfs.caching.bmemcached_cache"
        # app.config["CACHE_MEMCACHED_SERVERS"] = ["0.0.0.0:11211"]
        # app.config["CACHE_MEMCACHED_USERNAME"] = None
        # app.config["CACHE_MEMCACHED_PASSWORD"] = None

        app.config["MAIL_PORT"] = 1025

        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False  # Otherwise this gets annoying real fast
        DebugToolbarExtension(app)

    # Test run mode
    elif _run_mode == "test":
        # Override today so it's always the same value.
        from datetime import date
        from gameconfs.today import override_today
        override_today(date(2014, 5, 25))

        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # Or CSRF checks will fail
        turn_feature_off(app, "CACHE")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Production run mode
    elif _run_mode == "production":
        # Get additional configuration based on run environment
        run_environment = os.environ.get(PROJECT_NAME.upper() + "_RUN_ENV", "local")
        if run_environment == "heroku":
            # Get configuration data from Heroku environment variables
            app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

            app.config["CACHE_TYPE"] = "gameconfs.caching.bmemcached_cache"
            app.config["CACHE_MEMCACHED_SERVERS"] = os.environ.get("MEMCACHEDCLOUD_SERVERS").split(",")
            app.config["CACHE_MEMCACHED_USERNAME"] = os.environ.get("MEMCACHEDCLOUD_USERNAME")
            app.config["CACHE_MEMCACHED_PASSWORD"] = os.environ.get("MEMCACHEDCLOUD_PASSWORD")

            app.config["MAIL_SERVER"] = os.environ.get("POSTMARK_SMTP_SERVER")
            app.config["MAIL_USERNAME"] = os.environ.get("POSTMARK_API_TOKEN")
            app.config["MAIL_PASSWORD"] = os.environ.get("POSTMARK_API_TOKEN")
            app.config["MAIL_DEFAULT_SENDER"] = ADMIN_EMAIL
            app.config["MAIL_USE_TLS"] = True

        else:
            logging.error("Did not recognize run environment '%s'" % run_environment)
            return None, None

        set_up_logging(app)

    # Unrecognized run mode
    else:
        logging.error("Did not recognize run mode '%s'" % _run_mode)
        return None, None

    # Initialize the database
    global db
    import gameconfs.models
    db.init_app(app)

    # Set up Flask-Security
    app.config["SECURITY_EMAIL_SENDER"] = ADMIN_EMAIL

    app.user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    app.security = Security(app, app.user_datastore)

    # Initialize the cache
    if not is_feature_on(app, "CACHE"):
        app.config["CACHE_TYPE"] = "null"
    set_up_cache(app)

    # Import the views, to apply the decorators which use the global app object.
    app.url_map.converters['regex'] = RegexIconURLConverter
    import gameconfs.views

    # Register blueprints
    from gameconfs.widget import widget_blueprint
    from gameconfs.widget import set_up_blueprint as set_up_widget_blueprint
    app.register_blueprint(widget_blueprint)
    set_up_widget_blueprint(app)

    from gameconfs.bookmarklet import bookmarklet_blueprint
    app.register_blueprint(bookmarklet_blueprint)

    from gameconfs.data import data_blueprint
    app.register_blueprint(data_blueprint)

    from admin import set_up_admin_interface
    set_up_admin_interface(app, db.session)

    from gameconfs.api import api_blueprint
    from gameconfs.api import set_up_blueprint as set_up_api_blueprint
    app.register_blueprint(api_blueprint)
    set_up_api_blueprint(app)

    from gameconfs.slack import slack_blueprint
    app.register_blueprint(slack_blueprint)

    # Set up Jinja 2 filters
    set_up_jinja_filters(app)

    # Set up email
    app.mail = Mail(app)

    return app, db
