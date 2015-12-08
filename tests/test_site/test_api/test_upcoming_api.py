# -*- coding: utf-8 -*-

from nose.tools import *
from . import APITestCase


class UpcomingEventsAPITestCase(APITestCase):
    def get_base_url(self):
        return super(UpcomingEventsAPITestCase, self).get_base_url() + "v1/upcoming"

    def test_post_returns_405(self):
        r = self.c.post(self.get_base_url() + "v1/upcoming", query_string={})
        assert r.status_code == 405

    def test_wrong_parameters_fails(self):
        data = self.call_api({"blah": 0}, 400)
        assert data["message"].startswith("Did not recognize parameter")

    def test_nr_months_wrong_format_fails(self):
        data = self.call_api({"nrMonths": "FIVE"}, 400)
        assert data["message"].startswith("Could not parse nrMonths value")

    def test_nr_months_illegal_values_fails(self):
        data = self.call_api({"nrMonths": -1}, 400)
        eq_(data["message"], "nrMonths must be at least 1.")

        data = self.call_api({"nrMonths": 0}, 400)
        eq_(data["message"], "nrMonths must be at least 1.")

        data = self.call_api({"nrMonths": 13}, 400)
        eq_(data["message"], "nrMonths may not be higher than 12.")

    def test_place_empty_fails(self):
        data = self.call_api({"place": " "}, 400)
        eq_(data["message"], "Place argument was empty.")

    def test_place_not_found_fails(self):
        data = self.call_api({"place": "Vatican City"}, 404)
        ok_("message" not in data)

    def test_no_parameters_succeeds(self):
        data = self.call_api({}, 200)
        eq_(data["nrFoundEvents"], 6)
        APITestCase.check_events(data["results"])

    def test_no_place_and_1_month_succeeds(self):
        data = self.call_api({"nrMonths": 1}, 200)
        eq_(data["nrFoundEvents"], 3)
        APITestCase.check_events(data["results"])

    def test_no_place_and_12_months_succeeds(self):
        data = self.call_api({"nrMonths": 12}, 200)
        eq_(data["nrFoundEvents"], 9)
        APITestCase.check_events(data["results"])

    def test_place_and_no_months_succeeds(self):
        data = self.call_api({"place": "Paris"}, 200)
        eq_(data["nrFoundEvents"], 3)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_place_and_1_month_succeeds(self):
        data = self.call_api({"place": "Paris", "nrMonths": 1}, 200)
        eq_(data["nrFoundEvents"], 2)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_place_and_12_months_succeeds(self):
        data = self.call_api({"place": "Paris", "nrMonths": 12}, 200)
        eq_(data["nrFoundEvents"], 5)
        APITestCase.check_events(data["results"], lambda e: e["city"] == "Paris")

    def test_other_place_and_no_months_succeeds(self):
        data = self.call_api({"place": "other"}, 200)
        eq_(data["nrFoundEvents"], 1)
        APITestCase.check_events(data["results"], lambda e: "city" not in e)

    def test_other_place_and_1_month_fails(self):
        data = self.call_api({"place": "other", "nrMonths": 1}, 404)
        ok_("message" not in data)

    def test_other_place_and_2_months_succeeds(self):
        data = self.call_api({"place": "other", "nrMonths": 2}, 200)
        eq_(data["nrFoundEvents"], 1)
        APITestCase.check_events(data["results"], lambda e: "city" not in e)

    def test_other_place_and_12_months_succeeds(self):
        data = self.call_api({"place": "other", "nrMonths": 12}, 200)
        eq_(data["nrFoundEvents"], 1)
        APITestCase.check_events(data["results"], lambda e: "city" not in e)
