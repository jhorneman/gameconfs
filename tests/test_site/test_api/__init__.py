# -*- coding: utf-8 -*-

import json
from datetime import datetime
from nose.tools import *
from gameconfs.today import get_today
from .. import SiteTestCase


api_base_url = "/api/"


class APITestCase(SiteTestCase):
    def get_base_url(self):
        return api_base_url

    def call_api(self, _params, _expected_status):
        r = self.c.get(self.get_base_url(), query_string=_params)
        assert r.status_code == _expected_status, "Expected status code to be {0}, got {1}.".format(_expected_status, r.status_code)
        eq_(r.content_type, 'application/json')
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
            start_date = datetime.date(datetime.strptime(result["startDate"], "%Y-%m-%d"))
            end_date = datetime.date(datetime.strptime(result["endDate"], "%Y-%m-%d"))
            ok_(start_date <= end_date)
            ok_(end_date >= get_today())
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
        assert data["message"].endswith("not a valid path.")

    def test_wrong_API_version_returns_404(self):
        r = self.c.get(api_base_url + "v0/upcoming")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid version number.")

    def test_wrong_API_endpoint_returns_404(self):
        r = self.c.get(api_base_url + "v1/completely_wrong")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid endpoint.")
