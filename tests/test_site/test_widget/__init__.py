# -*- coding: utf-8 -*-

import re
import json
from nose.tools import *
from gameconfs.today import get_today
from .. import SiteTestCase


base_url = "/widget/"


class WidgetTestCase(SiteTestCase):
    def call_api(self, _params, _expected_status):
        r = self.c.get(base_url + "v1/data.json", query_string=_params)

        assert r.status_code == _expected_status, "Expected status code to be {0}, got {1}.".format(_expected_status, r.status_code)

        if _expected_status == 405:
            eq_(r.content_type, 'application/json')
            return None

        if _expected_status == 200:
            ok_(r.content_type.startswith('text/html'))
            m = re.match(_params["callback"] + r"\(\{'html':\"(.*)\"\}\)$", r.data)
            ok_(m, "Expected to parse returned HTML.")
            return m.group(1)
        else:
            eq_(r.content_type, 'application/json')
            data = json.loads(r.data)
            return data

    def test_index_returns_HTML(self):
        r = self.c.get(base_url)
        assert r.status_code == 200
        assert r.content_type.startswith('text/html')

    def test_wrong_path_returns_404(self):
        r = self.c.get(base_url + "completely_wrong")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid path.")

    def test_wrong_API_version_returns_404(self):
        r = self.c.get(base_url + "v0/data.json")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid version number.")

    def test_wrong_API_endpoint_returns_404(self):
        r = self.c.get(base_url + "v1/completely_wrong")
        eq_(r.status_code, 404)
        eq_(r.content_type, 'application/json')
        data = json.loads(r.data)
        assert data["message"].endswith("not a valid endpoint.")

    def test_cleanslate_css_succeeds(self):
        r = self.c.get(base_url + "v1/cleanslate.css")
        eq_(r.status_code, 200)
        ok_(r.content_type.startswith('text/css'))

    def test_widget_css_succeeds(self):
        r = self.c.get(base_url + "v1/widget.css")
        eq_(r.status_code, 200)
        ok_(r.content_type.startswith('text/css'))

    def test_script_js_succeeds(self):
        r = self.c.get(base_url + "v1/script.js")
        eq_(r.status_code, 200)
        ok_(r.content_type.startswith('text/javascript'))

    def test_data_no_params_fails(self):
        data = self.call_api({}, 400)
        eq_(data["message"], "No JSONP callback parameter found.")

    def test_wrong_parameters_fails(self):
        data = self.call_api({"blah": 0}, 400)
        assert data["message"].startswith("Did not recognize parameter")

    def test_nr_months_wrong_format_fails(self):
        data = self.call_api({"callback": "JSONP", "nr-months": "FIVE"}, 400)
        assert data["message"].startswith("Could not parse nr-months value")

    def test_nr_months_illegal_values_fails(self):
        data = self.call_api({"callback": "JSONP", "nr-months": -1}, 400)
        eq_(data["message"], "nr-months must be at least 1.")

        data = self.call_api({"callback": "JSONP", "nr-months": 0}, 400)
        eq_(data["message"], "nr-months must be at least 1.")

        data = self.call_api({"callback": "JSONP", "nr-months": 13}, 400)
        eq_(data["message"], "nr-months may not be higher than 12.")

    def test_place_empty_fails(self):
        data = self.call_api({"callback": "JSONP", "place": " "}, 400)
        eq_(data["message"], "Place argument was empty.")

    def test_place_not_found_returns_empty_html(self):
        html = self.call_api({"callback": "JSONP", "place": "Vatican City"}, 200)
        assert "The Gameconfs database contains no events satisfying these criteria." in html
