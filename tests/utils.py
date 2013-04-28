import unittest
from nose.tools import *
from gameconfs import create_app
from gameconfs.models import initialize_continents


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
