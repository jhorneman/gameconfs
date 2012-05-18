import logging
import unittest
from nose.tools import *
from application.geocoder import GeocodeResults

class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""
    # Origin: http://stackoverflow.com/questions/899067/how-should-i-verify-a-log-message-when-testing-python-code-under-nose

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }

class GeocoderTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_handler = MockLoggingHandler()
        self.mock_handler.setLevel(logging.WARNING)
        self.mock_handler.setFormatter(logging.Formatter('%(message)s'))

        self.geocoder_logger = logging.getLogger("application.geocoder")
        self.geocoder_logger.setLevel(logging.WARNING)
        self.geocoder_logger.addHandler(self.mock_handler)

        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.mock_handler.reset()

    def tearDown(self):
        pass

    def test_vienna(self):
        g = GeocodeResults("Naturhistorisches Museum in Vienna, Austria")
        ok_(g.is_valid)
        ok_(g.city == "Vienna")
        ok_(g.country == "Austria")
        ok_(g.continent == "Europe")

    def test_query_fail(self):
        g = GeocodeResults("")
        ok_(not g.is_valid)
        ok_(len(self.mock_handler.messages["error"]) > 0)

    def test_query_multiple_results(self):
        g = GeocodeResults("Springfield")
        ok_(g.is_valid)
        ok_(len(self.mock_handler.messages["warning"]) > 0)
