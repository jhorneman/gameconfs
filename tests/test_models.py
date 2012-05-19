import unittest
import sqlalchemy.orm
from nose.tools import *
from application import create_app
from application.models import *


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        create_app("dev")
        from application import app, db
        self.app = app

        with app.test_request_context():
            db.create_all()
            initialize_continents(db)
            self.db_session = db.create_scoped_session()

    def tearDown(self):
        pass


class UserModelTestCase(ModelTestCase):
    def test_user_can_be_added(self):
        with self.app.test_request_context():
            new_user = User('admin', 'admin@example.com')
            self.db_session.add(new_user)
            self.db_session.commit()

            found_user = User.query.one()
            ok_(found_user.name == 'admin')
            ok_(found_user.email == 'admin@example.com')


class ContinentModelTestCase(ModelTestCase):
    def test_all_continents_exist(self):
        with self.app.test_request_context():
            for continent_name in ["Europe", "Africa", "North America", "South America", "Australia", "Asia"]:
                c = Continent.query.filter(Continent.name == continent_name).all()
                ok_(len(c) == 1, "There must be exactly one query result per continent")
                ok_(c[0].name == continent_name)

    @raises(sqlalchemy.orm.exc.NoResultFound)
    def test_nonexistent_continent_raises_exception(self):
        with self.app.test_request_context():
            Continent.query.filter(Continent.name == "Mu").one()


class CountryModelTestCase(ModelTestCase):
    def test_country_can_be_added(self):
        with self.app.test_request_context():
            new_country = Country(self.db_session, 'Japan', 'Asia')
            self.db_session.add(new_country)
            self.db_session.commit()

            found_country = Country.query.one()
            ok_(found_country.name == 'Japan')
            ok_(found_country.continent.name == 'Asia')

    @raises(sqlalchemy.orm.exc.NoResultFound)
    def test_country_with_bad_continent_raises_exception(self):
        with self.app.test_request_context():
            country = Country(self.db_session, 'Hy-Brasil', 'Mu')
            self.db_session.add(country)
            self.db_session.commit()

    @raises(sqlalchemy.exc.IntegrityError)
    def test_duplicate_country_raises_exception(self):
         with self.app.test_request_context():
             country1 = Country(self.db_session, 'Belgium', 'Europe')
             self.db_session.add(country1)
             self.db_session.commit()

             country2 = Country(self.db_session, 'Belgium', 'Europe')
             self.db_session.add(country2)
             self.db_session.commit()


class CityModelTestCase(ModelTestCase):
    def test_city_can_be_added(self):
        with self.app.test_request_context():
            new_city = City(self.db_session, 'Tokyo', 'Japan', 'Asia')
            self.db_session.add(new_city)
            self.db_session.commit()

            found_city = City.query.one()
            ok_(found_city.name == 'Tokyo')
            ok_(found_city.country.name == 'Japan')
            ok_(found_city.country.continent.name == 'Asia')

    def test_adding_city_adds_country(self):
        with self.app.test_request_context():
            new_city = City(self.db_session, 'Tokyo', 'Japan', 'Asia')
            self.db_session.add(new_city)
            self.db_session.commit()

            c = Country.query.all()
            ok_(len(c) == 1)
            ok_(c[0].name == 'Japan')

    def test_adding_city_finds_country(self):
        with self.app.test_request_context():
            new_city1 = City(self.db_session, 'London', 'United Kingdom', 'Europe')
            self.db_session.add(new_city1)
            self.db_session.commit()

            new_city2 = City(self.db_session, 'Brighton', 'United Kingdom', 'Europe')
            self.db_session.add(new_city2)
            self.db_session.commit()

            c = Country.query.all()
            ok_(len(c) == 1)
            ok_(c[0].name == 'United Kingdom')

    @raises(sqlalchemy.exc.IntegrityError)
    def test_adding_two_cities_with_same_country_in_one_transaction_raises_exception(self):
        with self.app.test_request_context():
            new_city1 = City(self.db_session, 'London', 'United Kingdom', 'Europe')
            new_city2 = City(self.db_session, 'Brighton', 'United Kingdom', 'Europe')
            self.db_session.add(new_city1)
            self.db_session.add(new_city2)
            self.db_session.commit()

    def test_city_is_distinguished_by_country(self):
        with self.app.test_request_context():
            new_city1 = City(self.db_session, 'London', 'United Kingdom', 'Europe')
            new_city2 = City(self.db_session, 'London', 'Canada', 'North America')
            self.db_session.add(new_city1)
            self.db_session.add(new_city2)
            self.db_session.commit()

            found_city = City.query.\
                filter(City.name == 'London').\
                join(City.country).\
                filter(Country.name == 'Canada').\
                one()
            ok_(found_city.name == 'London')
            ok_(found_city.country.name == 'Canada')
            ok_(found_city.country.continent.name == 'North America')
