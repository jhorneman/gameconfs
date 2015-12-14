# -*- coding: utf-8 -*-

import re
import json
from nose.tools import *
from gameconfs.today import get_today
from .. import SiteTestCase
from bs4 import BeautifulSoup, Tag


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
            soup = BeautifulSoup(m.group(1), 'html.parser')
            return soup
        else:
            eq_(r.content_type, 'application/json')
            data = json.loads(r.data)
            return data

    @staticmethod
    def gather_events_from_widget_html(_html):
        events = []
        for table in _html.find_all("table"):
            for row in table.find_all("tr"):
                link = row.find_all("a")[0]
                events.append(link.text)
        return events

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
        paragraph = html.find_all("p")[0]
        eq_(paragraph.text, "The Gameconfs database contains no events satisfying these criteria.")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 0)

    def test_no_month_or_place_succeeds(self):
        html = self.call_api({"callback": "JSONP"}, 200)
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 6)

    def test_no_place_and_1_month_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 1}, 200)
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 3)

    def test_no_place_and_12_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 12}, 200)
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 9)

    def test_place_and_no_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "place": "Paris"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next 3 months in Paris")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 3)

    def test_place_and_1_month_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 1, "place": "Paris"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next month in Paris")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 2)

    def test_place_and_12_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 12, "place": "Paris"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next 12 months in Paris")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 5)

    def test_other_place_and_no_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "place": "other"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next 3 months in other")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 1)

    def test_other_place_and_1_month_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 1, "place": "other"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next month in other")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 0)

    def test_other_place_and_2_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 2, "place": "other"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next 2 months in other")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 1)

    def test_other_place_and_12_months_succeeds(self):
        html = self.call_api({"callback": "JSONP", "nr-months": 12, "place": "other"}, 200)
        h2 = html.find_all("h2")[0]
        eq_(h2.text, "Game events in the next 12 months in other")
        events = WidgetTestCase.gather_events_from_widget_html(html)
        eq_(len(events), 1)
