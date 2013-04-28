# coding=utf-8

import logging
import unittest
from nose.tools import *
from testfixtures import LogCapture
from gameconfs.geocoder import GeocodeResults


class GeocoderTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def test_vienna(self):
        g = GeocodeResults("Naturhistorisches Museum in Vienna, Austria")
        ok_(g.is_valid)
        ok_(g.city == "Vienna")
        ok_(g.country == "Austria")
        ok_(g.continent == "Europe")

    def test_query_fail_outputs_error(self):
        with LogCapture(level=logging.ERROR) as l:
            g = GeocodeResults("")
            ok_(not g.is_valid)
            l.check(("gameconfs.geocoder", "ERROR", "Geocoding query '': Status was 'ZERO_RESULTS' instead of 'OK'"))

    def test_utf8_query_works(self):
        g = GeocodeResults("Koelnmesse, Köln, Germany")
        ok_(g.is_valid)
        ok_(g.city == "Cologne")
        ok_(g.country == "Germany")
        ok_(g.continent == "Europe")

    def test_unicode_query_works(self):
        g = GeocodeResults(u"Koelnmesse, K\xf6ln, Germany")
        ok_(g.is_valid)
        ok_(g.city == "Cologne")
        ok_(g.country == "Germany")
        ok_(g.continent == "Europe")
