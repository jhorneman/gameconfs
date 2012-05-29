from flaskext.script import Manager, Shell
from application import create_app, run_app
from application.models import *

app = None
db = None


def create_app_for_Flask_script(_run_mode = None):
    global app
    global db
    (app, db) = create_app(_run_mode)
    return app


manager = Manager(create_app_for_Flask_script, with_default_commands=False)


@manager.command
def run_server():
    run_app()


@manager.command
def reset_db():
    with app.test_request_context():
        db.drop_all()
        db.create_all()
        initialize_continents(db)


@manager.command
def check_db():
    with app.test_request_context():
        db_session = db.create_scoped_session()
        print db_session.query(Country).count(), "countries"
        print db_session.query(City).count(), "cities"
        print db_session.query(Series).count(), "event series"
        print db_session.query(Event).count(), "events"
        print db_session.query(User).count(), "users"


if __name__ == "__main__":
    manager.add_option('-r', '--runmode', dest='_run_mode', required=False, default="dev")
    manager.add_command("shell", Shell())
    manager.run()
