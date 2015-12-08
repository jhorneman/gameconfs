# -*- coding: utf-8 -*-

import datetime
import json
from nose.tools import *
from .. import SiteTestCase
from tests.mock_data import load_api_mock_events


api_base_url = "/api/"

test_event = {
    "startDate": datetime.date(2016, 7, 18),
    "endDate": datetime.date(2016, 7, 20),
    "place": "Vienna",
    "city": "Vienna",
    "country": "Austria",
    "name": "nucl.ai 2016"
}


class APITestCase(SiteTestCase):
    def load_data(self):
        super(APITestCase, self).load_data()
        load_api_mock_events(self.db_session)

    def get_base_url(self):
        return api_base_url

    def call_api(self, _params, _expected_status):
        r = self.c.get(self.get_base_url(), query_string=_params)
        assert r.status_code == _expected_status, "Expected status code to be {0}, got {1}.".format(_expected_status, r.status_code)
        assert r.content_type == 'application/json'
        if _expected_status == 405:
            return None
        data = json.loads(r.data)
        if _expected_status == 200:
            assert "message" not in data
            assert len(data["results"]) == data["nrFoundEvents"]
            if "place" not in _params:
                eq_(data["foundLocationName"], None)
        return data

    @staticmethod
    def check_events(_results, _test_func=None):
        for result in _results:
            ok_("name" in result)
            ok_("eventUrl" in result)
            ok_("startDate" in result)
            ok_("endDate" in result)
            ok_("venue" in result)
            if "city" in result:
                ok_("country" in result)
                ok_("continent" in result)
            event_name = result["name"].lower()
            ok_("unpublished" not in event_name)
            if _test_func:
                ok_(_test_func(result))


class BasicAPITestCase(SiteTestCase):
    def test_index_returns_HTML(self):
        r = self.c.get(api_base_url)
        assert r.status_code == 200
        assert r.content_type.startswith('text/html')

    def test_wrong_path_returns_404(self):
        r = self.c.get(api_base_url + "completely_wrong")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid API path.")

    def test_wrong_API_version_returns_404(self):
        r = self.c.get(api_base_url + "v0/upcoming")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid API version number.")

    def test_wrong_API_endpoint_returns_404(self):
        r = self.c.get(api_base_url + "v1/completely_wrong")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid API endpoint.")
