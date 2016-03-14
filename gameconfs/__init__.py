# This module encapsulates everything related to creating the Flask app, including selecting and
# loading configurations.
#
# The application's behavior depends on
#   the RUN MODE - the role it's in,
#   KILL SWITCHES - used to turn off certain features, overriding the run mode and the run environment
#
# The following run modes are supported:
#   dev        - for development.
#   test       - for automated testing.
#   production - for live operations.

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


def create_app(_run_mode=None, _production_config_filename=None):
    # Create Flask app.
    # We have to calculate these paths because by default Flask uses the app name to do so, and we're
    # setting that to a value that won't result in a valid path.
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    global app
    app = Flask(PROJECT_NAME, template_folder=template_dir, static_folder=static_dir)

    # Load kill switches.
    load_all_kill_switches(app)

    # Load default, then run mode specific configuration.
    # The 'gameconfs' refers to the name of the directory the app is in, not the project.
    app.config.from_object("gameconfs.config.default")
    try:
        app.config.from_object("gameconfs.config." + _run_mode)
    except ImportError:
        pass

    # Dev run mode.
    if _run_mode == "dev":
        DebugToolbarExtension(app)

    # Test run mode.
    elif _run_mode == "test":
        # Override today so it's always the same value.
        from datetime import date
        from .today import override_today
        override_today(date(2014, 5, 25))

        turn_feature_off(app, "CACHE")

    # Production run mode.
    elif _run_mode == "production":
        if not _production_config_filename:
            logging.error("No production configuration filename provided.")
            return None, None

        config_filename = os.path.join(app.instance_path, _production_config_filename)
        app.config.from_pyfile(config_filename)

        set_up_logging(app)

    # Unrecognized run mode.
    else:
        logging.error("Did not recognize run mode '%s'" % _run_mode)
        return None, None

    # Initialize the connection to the database.
    global db
    import models
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
    import views

    # Register blueprints
    from .widget import widget_blueprint
    from .widget import set_up_blueprint as set_up_widget_blueprint
    app.register_blueprint(widget_blueprint)
    set_up_widget_blueprint(app)

    from .bookmarklet import bookmarklet_blueprint
    app.register_blueprint(bookmarklet_blueprint)

    from .data import data_blueprint
    app.register_blueprint(data_blueprint)

    from admin import set_up_admin_interface
    set_up_admin_interface(app, db.session)

    from .api import api_blueprint
    from .api import set_up_blueprint as set_up_api_blueprint
    app.register_blueprint(api_blueprint)
    set_up_api_blueprint(app)

    from .slack import slack_blueprint
    app.register_blueprint(slack_blueprint)

    # Set up Jinja 2 filters
    set_up_jinja_filters(app)

    # Set up email
    app.mail = Mail(app)

    return app, db
