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
    def __init__(self, *args, **kwargs):
        super(APITestCase, self).__init__(*args, **kwargs)
        self.base_url = api_base_url

    def call_api(self, _params, _expected_status):
        r = self.c.get(self.base_url, query_string=_params)
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
    def test_index_works(self):
        r = self.c.get(api_base_url)
        assert r.status_code == 200
        assert r.content_type.startswith('text/html')

    def test_wrong_slug_returns_404(self):
        r = self.c.get(api_base_url + "v1/screw_up")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')

    def test_wrong_version_returns_404(self):
        r = self.c.get(api_base_url + "v0/upcoming")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
