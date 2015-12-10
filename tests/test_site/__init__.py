# -*- coding: utf-8 -*-

import unittest
from gameconfs import create_app
import tests.mock_data as mock_data


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
        mock_data.load_geo_data(self.db_session)
        mock_data.load_mock_user(self.db_session, self.app.user_datastore)
        mock_data.load_mock_events(self.db_session)

    def login(self, _email, _password):
        return self.c.post('/login', data=dict(
            email=_email,
            password=_password
        ), follow_redirects=True)

    def logout(self):
        return self.c.get('/logout', follow_redirects=True)
