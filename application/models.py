import logging
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
import sqlalchemy.orm
from application import db
from application import geocoder

logger = logging.getLogger(__name__)

#TODO: Right now, these models cannot handle multiple cities with the same name in the same country.
# So we need to add states for some countries...


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)

    def __init__(self, _name=None, _email=None):
        self.name = _name
        self.email = _email

    def __repr__(self):
        return '<User %r>' % (self.name)


class Series(db.Model):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    def __init__(self, _name=None):
        self.name = _name

    def __repr__(self):
        return '<Series %r>' % (self.name)


class City(db.Model):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    country = relationship('Country', backref=backref('cities', lazy='lazy'))

    def __init__(self, _db_session, _name, _country_name, _continent_name):
        self.name = _name
        try:
            print "Looking for country", _country_name
            country = _db_session.query(Country).\
                filter(Country.name == _country_name).\
                join(Country.continent).\
                filter(Continent.name == _continent_name).\
                one()
        except sqlalchemy.orm.exc.NoResultFound:
            country = Country(_db_session, _country_name, _continent_name)
        self.country = country

    def __repr__(self):
        return '<City %r>' % (self.name)


class Country(db.Model):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)
    continent_id = Column(Integer, ForeignKey("continents.id"), nullable=False)
    continent = relationship('Continent', backref=backref('countries', lazy='lazy'))

    def __init__(self, _db_session, _name, _continent_name):
        self.name = _name
        continent = _db_session.query(Continent).filter(Continent.name == _continent_name).one()

        # The following causes horrible problems:
        #   continent = Continent.query.filter(Continent.name == _continent_name).one()
        # It will magically invoke a _SignallingSession session instead of a ScopingSession
        # and then sometime later the following exception will be raised:
        #   InvalidRequestError: Object '<Country at 0x10cb29e10>' is already attached to session '6' (this is '7')
        # It probably kinda makes sense.

        self.continent = continent

    def __repr__(self):
        return '<Country %r>' % (self.name)


class Continent(db.Model):
    __tablename__ = 'continents'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)

    def __init__(self, _name=None):
        self.name = _name

    def __repr__(self):
        return '<Continent %r>' % (self.name)


class Event(db.Model):
    __tablename__ = 'events'

    #TODO: Handle compound / child events (GDC tutorials and summits, e.g.)
    #TODO: Add event prototype model and link to it
    #TODO: Creation / modification dates
    #TODO: Slug support
    #TODO: Slug history in other table
    #TODO: Deadline support in other table

    # Primary key. Global event ID.
    id = Column(Integer, primary_key=True)

    # Name of the event. Need not be unique. Repeating events may have the same name.
    name = Column(String(250))

    # slug = Column(String(250))

    # Series this event is a part of.
    series_id = Column(Integer, ForeignKey("series.id"))
    series = relationship('Series')

    # Start and end dates of the event.
    #TODO: Decide if we need a start time for very short events
    event_start_date = Column(Date)
    event_end_date = Column(Date)

    # Start and end dates of the speaker submission period.
    # submission_start_date = Column(Date)
    # submission_end_date = Column(Date)

    # Start date of event registration. The end date is assumed to be the event itself.
    # registration_start_date = Column(Date)

    # End date of the early bird discount period. Some events may have.
    # early_bird_end_date = Column(Date)

    # Main URL for the site for this event.
    main_url = Column(String(250))

    # Is this event free or not?
    is_free = Column(Boolean)

    # Twitter hash tags for this event, with hash signs, separated by spaces.
    twitter_hashtags = Column(String(250))

    # Location info
    is_geolocated = Column(Boolean)
    raw_location_info = Column(String(250))
    formatted_location_info = Column(String(250))

    city_id = Column(Integer, ForeignKey("cities.id"))
    city = relationship('City')

    def __init__(self, _name=None):
        self.name = _name
        self.is_free = False
        self.is_geolocated = False

    def set_location(self, _location_info):
        self.raw_location_info = _location_info

        g = geocoder.GeocodeResults(self.raw_location_info)
        self.is_geolocated = g.is_valid

        if g.is_valid:
            self.formatted_location_info = g.formatted_location_info
            city = City.query.filter((City.name == g.city) & (City.country.name == g.country) & (City.country.continent.name == g.continent)).one()
            if city:
                self.city = city
            else:
                self.city = City(g.city, g.country, g.continent)

    def __repr__(self):
        return '<Event %r>' % (self.name)


def initialize_continents(_db):
    db_session = _db.create_scoped_session()
    for continent_name in geocoder.all_continents:
        continent = Continent(continent_name)
        db_session.add(continent)
    db_session.commit()

