# -*- coding: utf-8 -*-

import datetime
import json
from nose.tools import *
from .. import SiteTestCase


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
        return data


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
