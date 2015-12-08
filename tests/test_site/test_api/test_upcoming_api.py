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

    # TO TEST

    # No parameters (3 months + no place) returns the right event(s)

    # 1 month + no place returns the right event(s)
    # 12 months + no place returns the right event(s)

    # No month + place returns the right event(s)

    # A month + place returns the right event(s)

    # A month + "other" returns the right event(s)

    # NEVER an unpublished event

    def test_no_parameters_succeeds(self):
        data = self.call_api({}, 200)
        eq_(data["foundLocationName"], None)
        eq_(data["nrFoundEvents"], 5)

    def test_nr_months_legal_values_succeeds(self):
        data = self.call_api({"nrMonths": 1}, 200)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0

        data = self.call_api({"nrMonths": 12}, 200)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0
