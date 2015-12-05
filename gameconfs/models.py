import re
import logging
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship, backref, joinedload
import sqlalchemy.orm
from flask.ext.security import UserMixin, RoleMixin
from gameconfs import db
from gameconfs import geocoder


logger = logging.getLogger(__name__)


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    #TODO: Check password field, check connection with relevant Flask plugins
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
        backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User %r (%r)>' % (self.user_name, self.email)


class City(db.Model):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    country = relationship('Country', backref=backref('cities', lazy='select'))
    state_id = Column(Integer, ForeignKey('states.id'))
    state = relationship('State', backref=backref('cities', lazy='select'))

    def __init__(self, _name):
        self.name = _name

    def __repr__(self):
        return '<City %r>' % (self.name)


class State(db.Model):
    __tablename__ = 'states'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    short_name = Column(String(50), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    country = relationship('Country', backref=backref('states', lazy='select'))

    def __init__(self, _name, _short_name = ""):
        self.name = _name
        self.short_name = _short_name

    def __repr__(self):
        return '<State %r>' % (self.name)


class Country(db.Model):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)
    continent_id = Column(Integer, ForeignKey('continents.id'), nullable=False)
    continent = relationship('Continent', backref=backref('countries', lazy='select'))
    has_states = Column(Boolean)

    def __init__(self, _name):
        self.name = _name
        self.has_states = _name in geocoder.countries_with_states

    def __repr__(self):
        return '<Country %r>' % (self.name)


class Continent(db.Model):
    __tablename__ = 'continents'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)

    def __init__(self, _name):
        self.name = _name

    def __repr__(self):
        return '<Continent %r>' % (self.name)


class Series(db.Model):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)

    def __init__(self, _name):
        self.name = _name

    def __repr__(self):
        return self.name


publish_states = Enum('draft', 'published', name='publish_states')


class Event(db.Model):
    __tablename__ = 'events'

    # Primary key. Global event ID.
    id = Column(Integer, primary_key=True)

    # Creation and last modification date/times.
    created_at = Column(DateTime)
    last_modified_at = Column(DateTime)

    # Name of the event. Need not be unique. Repeating events may have the same name.
    name = Column(String(250))

    # Start and end dates of the event.
    start_date = Column(Date)
    end_date = Column(Date)

    # URL for the website for this event.
    event_url = Column(String(250))

    # Twitter hash tags for this event, with hash signs, separated by spaces.
    twitter_hashtags = Column(String(250))

    # Twitter account associated with this event, no @ sign.
    twitter_account = Column(String(250))

    # Location info
    venue = Column(String(250), nullable=True)
    address_for_geocoding = Column(String(250), nullable=True)

    # An event may take place worldwide or online. If it has no city, the venue describes the location.
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)
    city = relationship('City')

    series_id = Column(Integer, ForeignKey('series.id'), nullable=True)
    series = relationship('Series', backref=backref('events', lazy='select'))

    publish_status = Column(publish_states, default='draft')

    @staticmethod
    def base_query(_only_published=True, _with_location=True, _sorted_by_date=True):
        query = Event.query\

        if _only_published:
            query = query.filter(Event.publish_status == 'published')

        if _with_location:
            # query = query.options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))
            query = query.join(Event.city).\
                join(City.country).\
                join(Country.continent).\
                options(joinedload("city"), joinedload("city.country"), joinedload("city.state"))

        if _sorted_by_date:
            query = query.order_by(Event.start_date.asc(), Event.end_date.asc())

        return query

    def get_is_published(self):
        return self.publish_status == 'published'
    def set_is_published(self, value):
        self.publish_status = 'published' if value else 'draft'
    is_published = property(get_is_published, set_is_published)

    def get_last_checked_at(self):
        return self.last_modified_at
    def set_last_checked_at(self, value):
        pass
    last_checked_at = property(get_last_checked_at, set_last_checked_at)

    def __setattr__(self, name, value):
        if name == "event_url":
            if not re.match("^https?://", value):
                value = "http://" + value
        elif name == "twitter_account":
            if value.startswith("@"):
                value = value[1:]
        super(Event, self).__setattr__(name, value)

    def is_not_in_a_city(self):
        return self.city_id is None

    def is_in_a_city(self):
        return not self.is_not_in_a_city()

    # Needed for proper grouping of months across year boundaries
    def get_year_month_index(self):
        return self.start_date.year * 12 + self.start_date.month - 1
    year_month_index = property(get_year_month_index)

    def city_and_state_or_country(self):
        address = self.city.name
        if self.city.country.has_states:
            if self.city.name not in geocoder.cities_without_states_or_countries:
                address += ", " + self.city.state.name
        elif self.city.name not in geocoder.cities_without_states_or_countries:
            address += ", " + self.city.country.name
        return address

    def set_location(self, _db_session, _venue, _address_for_geocoding):
        """
        Set location data based on geocoding of location info.
        Caller is responsible for committing database transaction.
        """

        if _venue is None:
            _venue = ""
        self.venue = _venue.strip()

        if _address_for_geocoding is None:
            _address_for_geocoding = ""
        self.address_for_geocoding = _address_for_geocoding.strip()

        # Address given?
        if self.address_for_geocoding:
            # Yes -> Try to geocode, then set location data if successful.
            g = geocoder.GeocodeResults(self.address_for_geocoding)
            if g.is_valid:
                (self.city, state, country, continent) = set_up_location_data(_db_session, g)
            return g.is_valid
        else:
            # No -> Online event, valid.
            self.city = None
            return True

    def __repr__(self):
        return '<Event %r>' % (self.name)


def set_up_location_data(_db_session, _geocoded):
    """
    Find or create city, state, country and continent data based on geocoder results.
    Caller is responsible for committing database transaction.
    """

    state = None

    # Try to find the city
    try:
        city_query = _db_session.query(City).\
            filter(City.name == _geocoded.city).\
            join(City.country).\
            filter(Country.name == _geocoded.country).\
            join(Country.continent).\
            filter(Continent.name == _geocoded.continent)

        if _geocoded.is_in_a_state:
            city_query = city_query.\
                join(City.state).\
                filter(State.name == _geocoded.state)

        city = city_query. one()
        logger.debug("Found city " + _geocoded.city)

        country = city.country
        state = city.state
        continent = country.continent

    except sqlalchemy.orm.exc.NoResultFound:
        logger.debug("Didn't find city " + _geocoded.city)

        # Try to find the country
        try:
            country = _db_session.query(Country).\
                filter(Country.name == _geocoded.country).\
                join(Country.continent).\
                filter(Continent.name == _geocoded.continent).\
                one()

            logger.debug("Found country " + _geocoded.country)

            city = City(_geocoded.city)
            city.country = country
            _db_session.add(city)
            logger.debug("Created city " + _geocoded.city)

            if _geocoded.state:
                try:
                    state = _db_session.query(State).\
                        filter(State.name == _geocoded.state).\
                        join(State.country).\
                        filter(Country.name == _geocoded.country).\
                        join(Country.continent).\
                        filter(Continent.name == _geocoded.continent).\
                        one()

                except sqlalchemy.orm.exc.NoResultFound:
                    logger.debug("Didn't find state " + _geocoded.state)

                    state = State(_geocoded.state, _geocoded.state_abbr)
                    state.country = country
                    _db_session.add(state)
                    logger.debug("Created state " + _geocoded.state)

                city.state = state

            continent = country.continent

        except sqlalchemy.orm.exc.NoResultFound:
            logger.debug("Didn't find country " + _geocoded.country)

            # Try to find the continent
            try:
                continent = _db_session.query(Continent).\
                    filter(Continent.name == _geocoded.continent).\
                    one()

                logger.debug("Found continent " + _geocoded.continent)

                country = Country(_geocoded.country)
                country.continent = continent
                _db_session.add(country)
                logger.debug("Created country " + _geocoded.country)

                city = City(_geocoded.city)
                city.country = country
                _db_session.add(city)
                logger.debug("Created city " + _geocoded.city)

                if _geocoded.state:
                    state = State(_geocoded.state, _geocoded.state_abbr)
                    state.country = country
                    _db_session.add(state)
                    logger.debug("Created state " + _geocoded.state)
                    city.state = state

            except sqlalchemy.orm.exc.NoResultFound:
                logger.error("Didn't find continent " + _geocoded.continent)
                return (None, None, None, None)

    return (city, state, country, continent)


def initialize_continents(_db):
    db_session = _db.create_scoped_session()
    for continent_name in geocoder.all_continents:
        continent = Continent(continent_name)
        db_session.add(continent)
    db_session.commit()
