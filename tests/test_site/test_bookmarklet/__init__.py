# -*- coding: utf-8 -*-

import re
import json
from nose.tools import *
from .. import SiteTestCase
from bs4 import BeautifulSoup, Tag


base_url = "/bookmarklet/"


class BookmarkletTestCase(SiteTestCase):
    def call_api(self, _params, _expected_status):
        r = self.c.get(base_url + "search", query_string=_params)

        assert r.status_code == _expected_status, "Expected status code to be {0}, got {1}.".format(_expected_status, r.status_code)

        if _expected_status == 200:
            ok_(r.content_type.startswith('text/html'))
            soup = BeautifulSoup(r.data, 'html.parser')
            return soup
        else:
            return None

    @staticmethod
    def gather_events_from_bookmarklet_html(_html):
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

    def test_bookmarklet_js_succeeds(self):
        r = self.c.get(base_url + "js/search.js")
        eq_(r.status_code, 200)
        ok_(r.content_type.startswith('text/javascript'))

    def test_data_no_params_succeeds(self):
        data = self.call_api({}, 200)
        events = data.find_all("div", "event-entry")
        eq_(len(events), 0)

    def test_data_real_url_succeeds(self):
        data = self.call_api({"u": "http://www.computationalcreativity.net/iccc2016/"}, 200)
        events = data.find_all("div", "event-entry")
        eq_(len(events), 3)
