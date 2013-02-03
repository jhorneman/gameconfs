import os.path
import codecs
import logging
import yaml
from sqlalchemy import MetaData
from gameconfs import create_app
from gameconfs.models import *
from gameconfs.geocoder import GeocodeResults
from datetime import date

if __name__ == "__main__":
    logging.basicConfig()
    
    (app, db) = create_app("dev")

    with app.test_request_context():
        # Drop all tables with cascade
        meta = MetaData(db.engine)
        meta.reflect()
        meta.drop_all()

#        db.drop_all()
        db.create_all()
        initialize_continents(db)

        db_session = db.create_scoped_session()

        # Load geocoder cache
        if os.path.exists("geocoder_cache.json"):
            GeocodeResults.load_cache("geocoder_cache.json")

        # Load events
        with codecs.open('data/events.yaml', 'r', 'utf-8') as f:
            for data in yaml.load_all(f):
                if "name" not in data:
                    continue
                name = data["name"]
                if not name:
                    continue
                    
                new_event = Event(data["name"])
                d = [int(i) for i in data["start_date"]]
                new_event.start_date = date(d[0], d[1], d[2])
                d = [int(i) for i in data["end_date"]]
                new_event.end_date = date(d[0], d[1], d[2])

                if "main_url" in data:
                    new_event.main_url = data["main_url"]
                if "twitter_hashtags" in data:
                    new_event.twitter_hashtags = data["twitter_hashtags"]
                if "twitter_account" in data:
                    new_event.twitter_account = data["twitter_account"]

                if "address" in data:
                    address = data["address"]
                else:
                    address = data["location"]
                result = new_event.set_location(db_session, data["location"], address)

                # Only add if setting location worked (geocoding can fail)
                if result:
                    db_session.add(new_event)

                    # Must commit inside loop because set_location() will add cities, countries, etc.
                    db_session.commit()
                else:
                    # Otherwise get rid of whatever was done to the session or it will cause trouble later
                    db_session.expunge_all()

        # Save geocoder cache
        GeocodeResults.save_cache("geocoder_cache.json")

        # Create users
        admin_role = app.user_datastore.create_role(name='admin')
        user = app.user_datastore.create_user(name='Jurie', email='admin@gameconfs.com', password='password')
        app.user_datastore.add_role_to_user(user, admin_role)
        db.session.commit()

#        with codecs.open('data/users.yaml', 'r', 'utf-8') as f:
#            for data in yaml.load_all(f):
#                new_user = User(data["first_name"], data["last_name"], data["email"])
#                db_session.add(new_user)
#        db_session.commit()

        # Report
        print db_session.query(Country).count(), "countries"
        print db_session.query(City).count(), "cities"
        print db_session.query(Event).count(), "events"
        print db_session.query(User).count(), "users"
