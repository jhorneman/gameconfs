import logging
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
import sqlalchemy.orm
from gameconfs import db
from gameconfs import geocoder

logger = logging.getLogger(__name__)


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(250), nullable=False)
    last_name = Column(String(250), nullable=False)
    email = Column(String(250), unique=True, nullable=False)

    def __init__(self, _first_name, _last_name, _email):
        self.first_name = _first_name
        self.last_name = _last_name
        self.email = _email

    @property
    def display_name(self):
        return self.first_name + " " + self.last_name

    def __repr__(self):
        return '<User %r (%r %r)>' % (self.user_name, self.first_name, self.last_name)


class City(db.Model):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    country = relationship('Country', backref=backref('cities', lazy='lazy'))
    state_id = Column(Integer, ForeignKey('states.id'))
    state = relationship('State', backref=backref('cities', lazy='lazy'))

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
    country = relationship('Country', backref=backref('states', lazy='lazy'))

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
    continent = relationship('Continent', backref=backref('countries', lazy='lazy'))

    def __init__(self, _name):
        self.name = _name

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


class Event(db.Model):
    __tablename__ = 'events'

    #TODO: Handle compound / child events (GDC tutorials and summits, e.g.)
    #TODO: Add event prototype model and link to it
    #TODO: Creation / modification dates
    #TODO: Non-database index ID?
    #TODO: Slug support
    #TODO: Slug history in other table
    #TODO: Deadline support in other table
    #TODO: See if strings that are null (nullable) are treated as empty strings

    # Primary key. Global event ID.
    id = Column(Integer, primary_key=True)

    # Name of the event. Need not be unique. Repeating events may have the same name.
    name = Column(String(250))

    # slug = Column(String(250))

    # Start and end dates of the event.
    start_date = Column(Date)
    end_date = Column(Date)

    #TODO: Replace these with deadline table rows
    # Start and end dates of the speaker submission period.
    # submission_start_date = Column(Date)
    # submission_end_date = Column(Date)
    # Start date of event registration. The end date is assumed to be the event itself.
    # registration_start_date = Column(Date)
    # End date of the early bird discount period. Some events may have.
    # early_bird_end_date = Column(Date)

    # Main URL for the site for this event.
    main_url = Column(String(250))

    # Twitter hash tags for this event, with hash signs, separated by spaces.
    twitter_hashtags = Column(String(250))
    twitter_account = Column(String(250))

    # Location info
    location_name = Column(String(250), nullable=False)
    address_for_geocoding = Column(String(250), nullable=False)

    location_lat = Column(String(32))
    location_long = Column(String(32))

    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    city = relationship('City')

    def __init__(self, _name):
        self.name = _name
        self.is_free = False

    def set_location(self, _db_session, _location_name, _address_for_geocoding):
        """
        Set location data based on geocoding of location info.
        Caller is responsible for committing database transaction.
        """
        self.location_name = _location_name
        self.address_for_geocoding = _address_for_geocoding
        g = geocoder.GeocodeResults(self.address_for_geocoding)
        if g.is_valid:
            self.location_lat = g.latitude
            self.location_long = g.longitude
            (self.city, state, country, continent) = set_up_location_data(_db_session, g)
        return g.is_valid

    @property
    def full_location(self):
        return self.location_name + ", " + self.city_and_state_or_country

    @property
    def city_and_state_or_country(self):
        loc = self.city.name
        if self.city.country.name in geocoder.countries_with_states:
            loc += ", " + self.city.state.name
        elif self.city.name not in geocoder.cities_without_countries:
            loc += ", " + self.city.country.name
        return loc

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
        city = _db_session.query(City).\
            filter(City.name == _geocoded.city).\
            join(City.country).\
            filter(Country.name == _geocoded.country).\
            join(Country.continent).\
            filter(Continent.name == _geocoded.continent).\
            one()
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
