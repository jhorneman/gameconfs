# coding=iso-8859-1

import logging
import unittest
from nose.tools import *
from gameconfs.geocoder import GeocodeResults
from utils import *


class GeocoderTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.mock_handler = MockLoggingHandler()
        self.mock_handler.setLevel(logging.WARNING)
        self.mock_handler.setFormatter(logging.Formatter('%(message)s'))

        self.geocoder_logger = logging.getLogger("gameconfs.geocoder")
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

    def test_query_fail_outputs_error(self):
        g = GeocodeResults("")
        ok_(not g.is_valid)
        ok_(len(self.mock_handler.messages["error"]) > 0)

    def test_query_multiple_results_outputs_warning(self):
        g = GeocodeResults("Springfield")
        ok_(g.is_valid)
        ok_(len(self.mock_handler.messages["warning"]) > 0)

    def test_utf8_query_works(self):
        g = GeocodeResults("Koelnmesse, Köln, Germany")
        ok_(g.is_valid)
        ok_(g.city == "Cologne")
        ok_(g.country == "Germany")
        ok_(g.continent == "Europe")

    def test_unicode_query_works(self):
        g = GeocodeResults(u"Koelnmesse, Köln, Germany")
        ok_(g.is_valid)
        ok_(g.city == "Cologne")
        ok_(g.country == "Germany")
        ok_(g.continent == "Europe")
