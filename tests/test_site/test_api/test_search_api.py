# -*- coding: utf-8 -*-

from nose.tools import *
from . import APITestCase


class SearchAPITestCase(APITestCase):
    def get_base_url(self):
        return super(SearchAPITestCase, self).get_base_url() + "v1/search_events"

    def test_post_returns_405(self):
        r = self.c.post(self.get_base_url() + "v1/search_events", query_string={})
        assert r.status_code == 405

    def test_no_parameters_fails(self):
        data = self.call_api({}, 400)
        eq_(data["message"], "Query must contain at least one criterion.")

    def test_wrong_parameters_fails(self):
        data = self.call_api({"blah": 0}, 400)
        assert data["message"].startswith("Did not recognize parameter")

    def test_date_wrong_format_fails(self):
        data = self.call_api({"date": "May 5th 2012"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_date_in_past_fails(self):
        data = self.call_api({"date": "2012-01-01"}, 400)
        eq_(data["message"], "Can't search in the past.")

    def test_start_date_but_no_end_date_fails(self):
        data = self.call_api({"startDate": "2014-06-01"}, 400)
        eq_(data["message"], "Found start date argument but no end date.")

    def test_end_date_but_no_start_date_fails(self):
        data = self.call_api({"endDate": "2014-06-01"}, 400)
        eq_(data["message"], "Found end date argument but no start date.")

    def test_start_date_wrong_format_fails(self):
        data = self.call_api({"startDate": "May 5th 2012", "endDate": "2014-06-01"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_start_date_in_past_fails(self):
        data = self.call_api({"startDate": "2012-01-01", "endDate": "2014-06-01"}, 400)
        eq_(data["message"], "Can't search in the past.")

    def test_end_date_wrong_format_fails(self):
        data = self.call_api({"startDate": "2014-06-01", "endDate": "May 5th 2012"}, 400)
        assert data["message"].startswith("Couldn't parse date")

    def test_end_date_before_start_date_fails(self):
        data = self.call_api({"startDate": "2014-06-01", "endDate": "2014-05-23"}, 400)
        eq_(data["message"], "End date may not be before start date.")

    def test_event_name_empty_fails(self):
        data = self.call_api({"eventName": " "}, 400)
        eq_(data["message"], "Event name argument was empty.")

    def test_place_empty_fails(self):
        data = self.call_api({"place": " "}, 400)
        eq_(data["message"], "Place argument was empty.")

    def test_exact_event_name_succeeds(self):
        data = self.call_api({"eventName": "Europe 1 month out"}, 200)
        eq_(data["nrFoundEvents"], 1)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_partial_event_name_succeeds(self):
        data = self.call_api({"eventName": "Europe"}, 200)
        eq_(data["nrFoundEvents"], 6)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_right_date_succeeds(self):
        data = self.call_api({"date": "2014-06-01"}, 200)
        eq_(data["foundLocationName"], None)
        eq_(data["nrFoundEvents"], 1)
        APITestCase.check_events(data["results"], lambda e: e["name"] == "Europe 1 month out")

    def test_right_start_and_end_date_succeeds(self):
        data = self.call_api({"startDate": "2014-05-25", "endDate": "2014-08-31"}, 200)
        eq_(data["foundLocationName"], None)
        eq_(data["nrFoundEvents"], 6)
        APITestCase.check_events(data["results"])

    def test_right_place_succeeds(self):
        data = self.call_api({"place": "Paris"}, 200)
        eq_(data["foundLocationName"], "Paris")
        eq_(data["nrFoundEvents"], 6)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_other_place_succeeds(self):
        data = self.call_api({"place": "other"}, 200)
        eq_(data["foundLocationName"], "other")
        eq_(data["nrFoundEvents"], 2)
        APITestCase.check_events(data["results"], lambda e: "city" not in e)

    def test_wrong_place_fails(self):
        data = self.call_api({"place": "Vatican City"}, 404)
        eq_(data["foundLocationName"], None)
        eq_(data["nrFoundEvents"], 0)
