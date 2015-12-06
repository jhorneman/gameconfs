# -*- coding: utf-8 -*-

import json
from nose.tools import *
from .. import SiteTestCase
from . import base_url, test_event


class UpcomingEventsAPITestCase(SiteTestCase):
    def call_api(self, _params, _expected_status):
        r = self.c.get(base_url + "v1/upcoming", query_string=_params)
        assert r.status_code == _expected_status, "Expected status code to be {0}, got {1}.".format(_expected_status, r.status_code)
        if _expected_status == 405:
            return None
        data = json.loads(r.data)
        if _expected_status == 200:
            assert "message" not in data
            assert len(data["results"]) == data["nrFoundEvents"]
        return data

    def test_post_returns_405(self):
        r = self.c.post(base_url + "v1/upcoming", query_string={})
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

    # A unpublished event in Europe at 1 month out
    # B unpublished event in Asia at 1 month out
    # C unpublished event in Other at 1 month out

    # D published event in Europe at 1 month out
    # E published event in Asia at 1 month out
    # F published event in Other at 1 month out

    # G published event in Europe at 3 months out
    # H published event in Asia at 3 months out

    # I published event in Europe at 12 months out
    # J published event in Asia at 12 months out

    # K published event in Europe at 13 months out
    # L published event in Asia at 13 months out

    def test_nr_months_legal_values_succeeds(self):
        data = self.call_api({"nrMonths": 1}, 200)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0

        data = self.call_api({"nrMonths": 12}, 200)
        eq_(data["foundLocationName"], None)
        assert data["nrFoundEvents"] > 0

    # def test_wrong_data_fails(self):
    #     data = self.call_api({"blah": 0}, 200)
    #     eq_(data["foundLocationName"], None)
    #     assert data["nrFoundEvents"] > 0
    #     assert len(data["results"]) == data["nrFoundEvents"]
