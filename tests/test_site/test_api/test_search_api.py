# -*- coding: utf-8 -*-

from nose.tools import *
from . import APITestCase


class SearchAPITestCase(APITestCase):
    def get_base_url(self):
        return super(SearchAPITestCase, self).get_base_url() + "v1/search_events"

    def test_post_returns_405(self):
        r = self.c.post(self.get_base_url() + "v1/search_events", query_string={})
        assert r.status_code == 405

    def test_no_data_fails(self):
        data = self.call_api({}, 400)
        eq_(data["message"], "Query must contain at least one criterion.")

    def test_wrong_parameters_fails(self):
        data = self.call_api({"blah": 0}, 400)
        assert data["message"].startswith("Did not recognize parameter")

    def test_right_date(self):
        data = self.call_api({"date": "2014-06-01"}, 200)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
        result = data["results"][0]
        eq_(result["name"], "Europe 1 month out")
        eq_(result["city"], "Paris")
        eq_(result["country"], "France")
        eq_(result["continent"], "Europe")

    def test_date_wrong_format(self):
        data = self.call_api({"date": "May 5th 2012"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_date_in_past(self):
        data = self.call_api({"date": "2012-01-01"}, 400)
        eq_(data["message"], "Can't search in the past.")

    def test_start_date_but_no_end_date(self):
        data = self.call_api({"startDate": "2014-06-01"}, 400)
        eq_(data["message"], "Found start date argument but no end date.")

    def test_end_date_but_no_start_date(self):
        data = self.call_api({"endDate": "2014-06-01"}, 400)
        eq_(data["message"], "Found end date argument but no start date.")

    def test_start_date_wrong_format(self):
        data = self.call_api({"startDate": "May 5th 2012", "endDate": "2014-06-01"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_start_date_in_past(self):
        data = self.call_api({"startDate": "2012-01-01", "endDate": "2014-06-01"}, 400)
        eq_(data["message"], "Can't search in the past.")

    def test_end_date_wrong_format(self):
        data = self.call_api({"startDate": "2014-06-01", "endDate": "May 5th 2012"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_end_date_before_start_date(self):
        data = self.call_api({"startDate": "2014-06-01", "endDate": "2014-05-23"}, 400)
        eq_(data["message"], "End date may not be before start date.")

    def test_event_name_empty(self):
        data = self.call_api({"eventName": " "}, 400)
        eq_(data["message"], "Event name argument was empty.")

    def test_place_empty(self):
        data = self.call_api({"place": " "}, 400)
        eq_(data["message"], "Place argument was empty.")

    def test_place_with_results(self):
        data = self.call_api({"place": "Paris"}, 200)
        eq_(data["foundLocationName"], "Paris")
        eq_(data["nrFoundEvents"], 4)
        for result in data["results"]:
            eq_(result["city"], "Paris")
            eq_(result["country"], "France")
            eq_(result["continent"], "Europe")

    def test_place_with_no_results(self):
        data = self.call_api({"place": "Vatican City"}, 404)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] == 0
