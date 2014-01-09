from gameconfs import create_app
from gameconfs.models import *

if __name__ == "__main__":
    (app, db) = create_app("dev")
    with app.test_request_context():
        db_session = db.create_scoped_session()

        q = Event.query
        all_events = q.all()

        for event in all_events:
            if event.is_not_in_a_city():
                if event.venue:
                    print "Event %s is 'online' but has a non-empty venue." % event.name
                else:
                    event.venue = "Online"

        db.session.commit()
