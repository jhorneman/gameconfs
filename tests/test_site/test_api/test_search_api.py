# -*- coding: utf-8 -*-

import json
from nose.tools import *
from .. import SiteTestCase
from . import base_url, test_event


class APITestCase(SiteTestCase):
    def call_api(self, _params):
        return self.c.get(base_url + "v1/search_events", query_string=_params)

    # def test_search_post_returns_405(self):
    #     r = self.c.post(base_url + "v1/search_events", params={})
    #     assert r.status_code == 405

    def test_search_no_data_fails(self):
        r = self.call_api({})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Query must contain at least one criterion.")

    def test_search_wrong_data_fails(self):
        r = self.call_api({"blah": 0})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Query must contain at least one criterion.")

    def test_search_right_date(self):
        r = self.call_api({"date": test_event["startDate"]})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]
        result = data["results"][0]
        eq_(result["name"], test_event["name"])
        eq_(result["city"], test_event["city"])
        eq_(result["country"], test_event["country"])

    def test_search_date_wrong_format(self):
        r = self.call_api({"date": "May 5th 2012"})
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["message"].startswith("Couldn't parse date")

    def test_search_date_in_past(self):
        r = self.call_api({"date": "2012-01-01"})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Can't search in the past.")

    def test_search_start_date_but_no_end_date(self):
        r = self.call_api({"startDate": test_event["startDate"]})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Found start date argument but no end date.")

    def test_search_end_date_but_no_start_date(self):
        r = self.call_api({"endDate": test_event["startDate"]})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Found end date argument but no start date.")

    def test_search_start_date_wrong_format(self):
        r = self.call_api({"startDate": "May 5th 2012", "endDate": test_event["endDate"]})
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["message"].startswith("Couldn't parse date")

    def test_search_start_date_in_past(self):
        r = self.call_api({"startDate": "2012-01-01", "endDate": test_event["endDate"]})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Can't search in the past.")

    def test_search_end_date_wrong_format(self):
        r = self.call_api({"startDate": test_event["startDate"], "endDate": "May 5th 2012"})
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["message"].startswith("Couldn't parse date")

    def test_search_end_date_before_start_date(self):
        r = self.call_api({"startDate": test_event["endDate"], "endDate": test_event["startDate"]})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "End date may not be before start date.")

    def test_search_event_name_empty(self):
        r = self.call_api({"eventName": " "})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Event name argument was empty.")

    def test_search_place_empty(self):
        r = self.call_api({"place": " "})
        assert r.status_code == 400
        data = json.loads(r.data)
        eq_(data["message"], "Place argument was empty.")

    def test_search_place_with_results(self):
        r = self.call_api({"place": "Vienna"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], "Vienna")
        assert data["nrFoundEvents"] > 0
        assert len(data["results"]) == data["nrFoundEvents"]
        for result in data["results"]:
            eq_(result["city"], "Vienna")
            eq_(result["country"], "Austria")
            eq_(result["continent"], "Europe")

    def test_search_place_with_no_results(self):
        r = self.call_api({"place": "Vatican City"})
        assert r.status_code == 404
        data = json.loads(r.data)
        assert "message" not in data
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] == 0
        assert len(data["results"]) == data["nrFoundEvents"]
