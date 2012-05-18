from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
from application import db

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.name)


class Series(db.Model):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Series %r>' % (self.name)


class City(db.Model):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship('Country', backref=backref('cities', lazy='lazy'))

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<City %r>' % (self.name)


class Country(db.Model):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Country %r>' % (self.name)


class Event(db.Model):
    __tablename__ = 'events'

    #TODO: Handle compound / child events (GDC tutorials and summits, e.g.)
    #TODO: Add event prototype model and link to it

    # Primary key. Global event ID.
    id = Column(Integer, primary_key=True)

    # Name of the event. Need not be unique. Repeating events may have the same name.
    name = Column(String(250))

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

    def __init__(self, name=None):
        self.name = name
        self.is_free = False
        self.is_geolocated = False

    def __repr__(self):
        return '<Event %r>' % (self.name)
