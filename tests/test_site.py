import os
import unittest
import datetime
import codecs
import json
from gameconfs import create_app
from gameconfs.models import Event, City, State, Country, Continent


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep


app, db = create_app("test")


class SiteTestCase(unittest.TestCase):
    def setUp(self):
        global app, db
        self.app = app
        self.db = db
        self.c = self.app.test_client()

        with self.app.test_request_context():
            self.db.create_all()
            self.db_session = self.db.session
            self.load_data()

    def tearDown(self):
        with self.app.test_request_context():
            self.db_session.remove()
            self.db.drop_all()

    def load_data(self):
        continents_by_id = {}
        with codecs.open(SCRIPT_DIR + 'continents.json', 'r', 'utf-8') as f:
            for continent_data in json.load(f):
                continents_by_id[continent_data['id']] = continent_data['name']
                new_continent = Continent(continent_data['name'])
                self.db_session.add(new_continent)
        self.db_session.commit()

        countries_by_id = {}
        with codecs.open(SCRIPT_DIR + 'countries.json', 'r', 'utf-8') as f:
            for country_data in json.load(f):
                countries_by_id[country_data['id']] = country_data['name']
                new_country = Country(country_data['name'])
                continent_name = continents_by_id[country_data['continent_id']]
                new_country.continent = self.db_session.query(Continent).filter(Continent.name == continent_name).one()
                self.db_session.add(new_country)
        self.db_session.commit()

        states_by_id = {}
        with codecs.open(SCRIPT_DIR + 'states.json', 'r', 'utf-8') as f:
            for state_data in json.load(f):
                states_by_id[state_data['id']] = state_data['name']
                new_state = State(state_data['name'], state_data['short_name'])
                country_name = countries_by_id[state_data['country_id']]
                new_state.country = self.db_session.query(Country).filter(Country.name == country_name).one()
                self.db_session.add(new_state)
        self.db_session.commit()

        cities_by_id = {}
        with codecs.open(SCRIPT_DIR + 'cities.json', 'r', 'utf-8') as f:
            for city_data in json.load(f):
                cities_by_id[city_data['id']] = city_data['name']
                new_city = City(city_data['name'])
                country_name = countries_by_id[city_data['country_id']]
                new_city.country = self.db_session.query(Country).filter(Country.name == country_name).one()
                if city_data['state_id']:
                    state_name = states_by_id[city_data['state_id']]
                    new_city.state = self.db_session.query(State).filter(State.name == state_name).one()
                self.db_session.add(new_city)
        self.db_session.commit()

        now = datetime.datetime.now()
        this_year = now.date().year

        new_event = Event()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = "Stagconf"
        new_event.start_date = datetime.date(this_year, 8, 14)
        new_event.end_date = datetime.date(this_year, 8, 14)
        new_event.event_url = "http://www.stagconf.com/"
        new_event.twitter_hashtags = ""
        new_event.twitter_account = ""
        new_event.venue = "Naturhistorisches Museum"
        new_event.city = self.db_session.query(City).filter(City.name == "Vienna").first()
        self.db_session.add(new_event)

        new_event = Event()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = "GDC"
        new_event.start_date = datetime.date(this_year-1, 3, 31)
        new_event.end_date = datetime.date(this_year-1, 4, 1)
        new_event.event_url = "http://www.gdconf.com/"
        new_event.twitter_hashtags = ""
        new_event.twitter_account = ""
        new_event.venue = "Moscone"
        new_event.city = self.db_session.query(City).filter(City.name == "San Francisco").one()
        self.db_session.add(new_event)

        new_event = Event()
        new_event.created_at = now
        new_event.last_modified_at = now
        new_event.name = "Someconf"
        new_event.start_date = datetime.date(this_year, 5, 25)
        new_event.end_date = datetime.date(this_year, 5, 27)
        new_event.event_url = "http://www.someconf.com/"
        new_event.twitter_hashtags = ""
        new_event.twitter_account = ""
        new_event.venue = "St. Paul's Cathedral"
        new_event.city = self.db_session.query(City).filter(City.name == "London").first()
        self.db_session.add(new_event)

        self.db_session.commit()

        # Create user data
        admin_role = self.app.user_datastore.create_role(name='admin')
        user = self.app.user_datastore.create_user(user_name='Test', email='test@gameconfs.com', password='test')
        self.app.user_datastore.add_role_to_user(user, admin_role)
        db.session.commit()

        self.db_session.commit()

    def login(self, _email, _password):
        return self.c.post('/login', data=dict(
            email=_email,
            password=_password
        ), follow_redirects=True)

    def logout(self):
        return self.c.get('/logout', follow_redirects=True)

    def test_index_page(self):
        rv = self.c.get('/')
        assert "Austria" in rv.data
        assert "United Kingdom" in rv.data

    def test_continent_page(self):
        rv = self.c.get('/place/europe')
        assert "Someconf" in rv.data
        assert "London" in rv.data
        assert "United Kingdom" in rv.data
        assert "May" in rv.data

    def test_country_page(self):
        rv = self.c.get('/place/austria')
        assert "Stagconf" in rv.data
        assert "Vienna" in rv.data
        assert "Austria" in rv.data
        assert "August" in rv.data

    def test_year_page(self):
        rv = self.c.get('/year/%s' % (datetime.date.today().year - 1))
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data

    def test_place_page(self):
        rv = self.c.get('/place/california')
        assert "GDC" not in rv.data
        assert "San Francisco" not in rv.data

    def test_place_past_page(self):
        rv = self.c.get('/place/california/past')
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data

    def test_event_page(self):
        rv = self.c.get('/event/1')
        assert "Stagconf" in rv.data
        assert "Vienna" in rv.data
        assert "Austria" in rv.data
        assert "August" in rv.data
        assert "Naturhistorisches" in rv.data
        assert "www.stagconf.com" in rv.data

    def test_event_page_with_state(self):
        rv = self.c.get('/event/2')
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data
        assert "Moscone" in rv.data
        assert "www.gdconf.com" in rv.data

    def test_login(self):
        rv = self.c.get('/')
        assert "Sign out" not in rv.data

        rv = self.login('test@gameconfs.com', 'test')
        assert "Sign out" in rv.data

        rv = self.logout()
        assert "Sign out" not in rv.data
