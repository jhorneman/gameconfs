# -*- coding: utf-8 -*-

from nose.tools import *
from .. import SiteTestCase
from bs4 import BeautifulSoup


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
        ok_(r.content_type.startswith('text/html'))  # Note the html type. See bookmarklet code for details.

    def test_data_no_params_succeeds(self):
        data = self.call_api({}, 200)
        events = data.find_all("div", "event-entry")
        eq_(len(events), 0)

    def test_data_real_url_succeeds(self):
        data = self.call_api({"u": "http://www.computationalcreativity.net/iccc2016/"}, 200)
        events = data.find_all("div", "event-entry")
        eq_(len(events), 3)
