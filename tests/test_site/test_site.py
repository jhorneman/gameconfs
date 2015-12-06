import os
import unittest
import datetime
from gameconfs import create_app
from tests.mock_data import load_geo_data, load_mock_events, load_mock_user


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep
mock_data_dir = os.path.join(SCRIPT_DIR, 'mock_data')

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
        load_geo_data(self.db_session)
        load_mock_events(self.db_session)
        load_mock_user(self.db_session, self.app.user_datastore)

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
