from application import create_app, run_app
from application.models import *

if __name__ == "__main__":
    create_app("dev")
    from application import app, db

    with app.test_request_context():
        db.create_all()
        db_session = db.create_scoped_session()

        countries = {n, Country(n) for n in ["Austria", "United Kingdom", "Sweden"]}

        c = City()
        c.name = "Vienna"
        c.country = countries["Austria"]

        s = Series()
        s.name = "Stagconf"

        e = Event()
        e.name = "Stagconf 2012"
        e.series = s
        # e.event_start_date = Column(Date)
        # e.event_end_date = Column(Date)
        e.main_url = "http://stagconf.com"
        e.is_free = False
        e.twitter_hashtags = "#stagconf #stagconf12"
        e.is_geolocated = False
        e.raw_location_info = "Museum of Natural History, Vienna"
        e.city = c

        admin = User('admin', 'admin@example.com')

        db_session.add(a)
        db_session.add(c)
        db_session.add(s)
        db_session.add(e)
        db_session.add(admin)

        db_session.commit()

        print Country.query.all()
        print City.query.all()
        print Series.query.all()
        print User.query.all()

        print

        qe = Event.query.filter(Event.name.contains('Stagconf')).first()
        print "Event", qe
        print " belongs to the event series", qe.series
        print " and takes place in", qe.city
        print " which is in", qe.city.country
        print " which contains the following cities", qe.city.country.cities
