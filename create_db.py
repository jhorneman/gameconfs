import codecs
import logging
import yaml
from application import create_app, run_app
from application.models import *
from datetime import date

if __name__ == "__main__":
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger('').addHandler(console)

    create_app("dev")
    from application import app, db

    with app.test_request_context():
        db.drop_all()
        db.create_all()
        initialize_continents(db)

        db_session = db.create_scoped_session()

        # Load event series
        with codecs.open('data/series.yaml', 'r', 'utf-8') as f:
            for data in yaml.load_all(f):
                new_series = Series(data["name"])
                db_session.add(new_series)
        db_session.commit()

        # Load events
        with codecs.open('data/events.yaml', 'r', 'utf-8') as f:
            for data in yaml.load_all(f):
                new_event = Event(data["name"])
                new_event.series = db_session.query(Series).filter(Series.name == data["series"]).one()
                new_event.start_date = date(*data["start_date"])
                new_event.end_date = date(*data["end_date"])
                new_event.main_url = data["main_url"]
                new_event.is_free = False
                new_event.twitter_hashtags = data["twitter_hashtags"]
                new_event.twitter_account = data["twitter_account"]
                new_event.set_location(db_session, data["location"])

                # Only add if setting location worked (geocoding can fail)
                if new_event.formatted_location_info:
                    db_session.add(new_event)

                    # Must commit inside loop because set_location() will add cities, countries, etc.
                    db_session.commit()
                else:
                    # Otherwise get rid of whatever was done to the session or it will cause trouble later
                    db_session.expunge_all()

        # Load users
        with codecs.open('data/users.yaml', 'r', 'utf-8') as f:
            for data in yaml.load_all(f):
                new_user = User(data["first_name"], data["last_name"], data["email"])
                db_session.add(new_user)
        db_session.commit()

        # Report
        print db_session.query(Country).count(), "countries"
        print db_session.query(City).count(), "cities"
        print db_session.query(Series).count(), "event series"
        print db_session.query(Event).count(), "events"
        print db_session.query(User).count(), "users"
