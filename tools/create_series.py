import re
from gameconfs import create_app
from gameconfs.models import *

if __name__ == "__main__":
    (app, db) = create_app("dev")
    with app.test_request_context():
        db_session = db.create_scoped_session()

        q = Event.query.\
            join(Event.city).\
            join(City.country).\
            order_by(Event.start_date.asc())
        all_events = q.all()

        year_pattern = "\d\d1\d"
        yearless_names = dict()

        for event in all_events:
            yearless_name = re.sub(year_pattern, "", event.name).strip()
            refs = yearless_names.setdefault(yearless_name, [])
            refs.append(event)

        for (name, events) in yearless_names.items():
            if len(events) > 1:
                series = Series(name)
                db.session.add(series)
                for event in events:
                    event.series = series

        db.session.commit()
