# -*- coding: utf-8 -*-

import json
from nose.tools import *
from .. import SiteTestCase
from . import base_url, test_event


class APITestCase(SiteTestCase):
    def call_api(self, _params):
        return self.c.get(base_url + "v1/upcoming", query_string=_params)
    
    def test_upcoming_post_returns_405(self):
        r = self.c.post(base_url + "v1/upcoming", query_string={})
        assert r.status_code == 405
    
    def test_upcoming_no_data_fails(self):
        r = self.call_api({})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]

    def test_upcoming_wrong_data_fails(self):
        r = self.call_api({"blah": 0})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]

    def test_upcoming_nr_months_wrong_format(self):
        r = self.call_api({"nrMonths": "FIVE"})
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["message"].startswith("Could not parse nrMonths value")

    def test_upcoming_nr_months_illegal_values(self):
        r = self.call_api({"nrMonths": -1})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "nrMonths must be at least 1.")
    
        r = self.call_api({"nrMonths": 0})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "nrMonths must be at least 1.")
    
        r = self.call_api({"nrMonths": 13})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "nrMonths may not be higher than 12.")

    def test_upcoming_nr_months_legal_values(self):
        r = self.call_api({"nrMonths": 1})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]
    
        r = self.call_api({"nrMonths": 12})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]

    def test_upcoming_place_empty(self):
        r = self.call_api({"place": " "})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Place argument was empty.")
