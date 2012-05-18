import os
import unittest
import tempfile
import application

# application.create_app("dev")

# class SkeletonTestCase(unittest.TestCase):
# 	def setUp(self):
# 		#self.db_file, app.config['DATABASE'] = tempfile.mkstemp()
# 		application.app.config['TESTING'] = True
# 		self.app = application.app.test_client()

# 	def tearDown(self):
# 		pass

# 	def test_data(self):
# 		rv = self.app.get('/')
# 		assert 'admin' in rv.data

# 	def test_data2(self):
# 		rv = self.app.get('/')
# 		assert 'user' in rv.data
