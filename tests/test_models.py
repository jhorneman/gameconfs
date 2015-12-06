import unittest
import sqlalchemy.orm
from nose.tools import *
from gameconfs import create_app
from gameconfs.models import *


class TestCaseUsingDatabase(unittest.TestCase):
    def setUp(self):
        create_app("test")
        from gameconfs import app, db
        self.app = app
        self.db = db

        with self.app.test_request_context():
            self.db.create_all()
            initialize_continents(self.db)
            self.db_session = self.db.create_scoped_session()
            # IMPORTANT: Always use self.db_session.query(Klass) NOT Klass.query
            # as the latter will create a new session

    def tearDown(self):
        with self.app.test_request_context():
            self.db_session.remove()
            self.db.drop_all()

    def count_in_db(self, _klass):
        return _klass.query.count()

    def exists_in_db(self, _klass, _name, _msg=None):
        ok_(_klass.query.filter(_klass.name == _name).count() == 1, _msg)

    def does_not_exist_in_db(self, _klass, _name, _msg=None):
        ok_(_klass.query.filter(_klass.name == _name).count() == 0, _msg)


class UserModelTestCase(TestCaseUsingDatabase):
    def test_user_can_be_added(self):
        with self.app.test_request_context():
            user = User()
            user.user_name = 'Jurie Horneman'
            user.email = 'admin@example.com'
            self.db_session.add(user)
            self.db_session.commit()

            found_user = User.query.one()
            ok_(found_user.user_name == 'Jurie Horneman')
            ok_(found_user.email == 'admin@example.com')


class ContinentModelTestCase(TestCaseUsingDatabase):
    def test_all_continents_exist(self):
        with self.app.test_request_context():
            for continent_name in ["Europe", "Africa", "North America", "South America", "Australia", "Asia"]:
                Continent.query.filter(Continent.name == continent_name).one()


class LocationSetUpTestCase(TestCaseUsingDatabase):
    def test_setting_up_locations(self):
        with self.app.test_request_context():
            self.does_not_exist_in_db(City, 'San Francisco')
            self.does_not_exist_in_db(State, 'California')
            self.does_not_exist_in_db(Country, 'United States')
            self.exists_in_db(Continent, 'North America')

            g = geocoder.GeocodeResults("Moscone, 747 Howard Street, San Francisco")
            ok_(g.is_valid)
            (city, state, country, continent) = set_up_location_data(self.db_session, g)
            ok_(city)
            ok_(state)
            ok_(country)
            ok_(continent)
            self.db_session.commit()

            self.exists_in_db(City, 'San Francisco')
            self.exists_in_db(State, 'California')
            self.exists_in_db(Country, 'United States')
            self.exists_in_db(Continent, 'North America')

            g = geocoder.GeocodeResults("101 Harborside Drive, Boston")
            ok_(g.is_valid)
            (city, state, country, continent) = set_up_location_data(self.db_session, g)
            ok_(city)
            ok_(state)
            ok_(country)
            ok_(continent)
            self.db_session.commit()

            self.exists_in_db(City, 'Boston')
            self.exists_in_db(State, 'Massachusetts')

            g = geocoder.GeocodeResults("1675 Owens Street San Francisco")
            ok_(g.is_valid)
            (city, state, country, continent) = set_up_location_data(self.db_session, g)
            ok_(city)
            ok_(state)
            ok_(country)
            ok_(continent)
            self.db_session.commit()

            eq_(Country.query.filter(Country.name == 'United States').one().states[0].name, 'California')
            eq_(State.query.filter(State.name == 'California').one().cities[0].name, 'San Francisco')
            eq_(State.query.filter(State.name == 'California').one().country.name, 'United States')
            eq_(City.query.filter(City.name == 'San Francisco').one().state.short_name, 'CA')

    def test_setting_up_location_with_empty_string(self):
        with self.app.test_request_context():
            g = geocoder.GeocodeResults("")
            ok_(not g.is_valid)

    def test_setting_up_location_with_bad_continent(self):
        with self.app.test_request_context():
            g = geocoder.GeocodeResults("Valeria, Mu")
            ok_(not g.is_valid)


class CountryModelTestCase(TestCaseUsingDatabase):
    def test_country_can_be_added(self):
        with self.app.test_request_context():
            continent = self.db_session.query(Continent).filter(Continent.name == 'Asia').one()

            country = Country('Japan')
            country.continent = continent
            self.db_session.add(country)
            self.db_session.commit()

            found_country = Country.query.one()
            ok_(found_country.name == 'Japan')
            ok_(found_country.continent.name == 'Asia')

    @raises(sqlalchemy.exc.IntegrityError)
    def test_country_without_continent_raises_exception(self):
        with self.app.test_request_context():
            country = Country('Belgium')
            self.db_session.add(country)
            self.db_session.commit()

    @raises(sqlalchemy.exc.IntegrityError)
    def test_duplicate_country_raises_exception(self):
        with self.app.test_request_context():
            continent = self.db_session.query(Continent).filter(Continent.name == 'Europe').one()

            country1 = Country('Belgium')
            country1.continent = continent
            self.db_session.add(country1)
            self.db_session.commit()

            country2 = Country('Belgium')
            country1.continent = continent
            self.db_session.add(country2)
            self.db_session.commit()


class StateModelTestCase(TestCaseUsingDatabase):
    def test_state_can_be_added(self):
        with self.app.test_request_context():
            continent = self.db_session.query(Continent).filter(Continent.name == 'North America').one()

            country = Country('United States')
            country.continent = continent
            self.db_session.add(country)
            self.db_session.commit()

            state = State('Iowa')
            state.country = country
            self.db_session.add(state)
            self.db_session.commit()

            found_state = State.query.one()
            ok_(found_state.name == 'Iowa')
            ok_(found_state.country.name == 'United States')
            ok_(found_state.country.continent.name == 'North America')

    @raises(sqlalchemy.exc.IntegrityError)
    def test_state_without_country_raises_exception(self):
        with self.app.test_request_context():
            state = State('Iowa')
            self.db_session.add(state)
            self.db_session.commit()


class CityModelTestCase(TestCaseUsingDatabase):
    def test_city_can_be_added(self):
        with self.app.test_request_context():
            continent = self.db_session.query(Continent).filter(Continent.name == 'Asia').one()

            country = Country('Japan')
            country.continent = continent
            self.db_session.add(country)
            self.db_session.commit()

            city = City('Tokyo')
            city.country = country
            self.db_session.add(city)
            self.db_session.commit()

            found_city = City.query.one()
            ok_(found_city.name == 'Tokyo')
            ok_(found_city.country.name == 'Japan')
            ok_(found_city.country.continent.name == 'Asia')

    def test_city_can_be_added_with_state(self):
        with self.app.test_request_context():
            continent = self.db_session.query(Continent).filter(Continent.name == 'North America').one()

            country = Country('United States')
            country.continent = continent
            self.db_session.add(country)
            self.db_session.commit()

            state = State('California', 'CA')
            state.country = country
            self.db_session.add(state)
            self.db_session.commit()

            city = City('San Francisco')
            city.state = state
            city.country = country
            self.db_session.add(city)
            self.db_session.commit()

            found_city = City.query.one()
            ok_(found_city.name == 'San Francisco')
            ok_(found_city.state.name == 'California')
            ok_(found_city.state.short_name == 'CA')
            ok_(found_city.country.name == 'United States')
            ok_(found_city.country.continent.name == 'North America')

    @raises(sqlalchemy.exc.IntegrityError)
    def test_city_without_country_raises_exception(self):
        with self.app.test_request_context():
            city = City('Tokyo')
            self.db_session.add(city)
            self.db_session.commit()


class EventModelTestCase(TestCaseUsingDatabase):
    def test_event_can_be_added(self):
        with self.app.test_request_context():
            event = Event()
            event.name = 'Stagconf 2012'
            event.set_location(self.db_session, 'Naturhistorisches Museum', 'Vienna, Austria')
            self.db_session.add(event)
            self.db_session.commit()

            found_event = Event.query.one()
            ok_(found_event.name == 'Stagconf 2012')

            found_city = City.query.one()
            ok_(found_city.name == 'Vienna')
