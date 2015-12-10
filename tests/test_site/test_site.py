from datetime import datetime
from bs4 import BeautifulSoup, Tag
from nose.tools import *
from . import SiteTestCase


class BasicSiteTestCase(SiteTestCase):
    def get_page(self, _path):
        r = self.c.get(_path)
        assert r.status_code == 200, "Expected status code to be 200, got {0}.".format(r.status_code)
        soup = BeautifulSoup(r.data, 'html.parser')
        return soup

    @staticmethod
    def check_event(_event, **kwargs):
        name_el = _event.find_all(["span", "div", "h2"], "event-name")[0]
        name = name_el.contents[0]
        if isinstance(name, Tag):
            eq_(name.name, "a")
            name = name.contents[0]

        ok_("unpublished"not in name.string.lower(), "Expected event to be published (according to name).")

        if "name" in kwargs:
            eq_(name.string, kwargs["name"])

        if "location" in kwargs:
            location_el = _event.find_all(["span", "div"], "event-location")[0]
            eq_(location_el.contents[0], kwargs["location"])

        if "year" in kwargs:
            start_date, end_date = BasicSiteTestCase.get_event_dates(_event)
            eq_(start_date.year, kwargs["year"])

    @staticmethod
    def get_event_dates(_event):
        date_el = _event.find_all(["span", "div"], "event-date")[0]
        start_date_el = date_el.find_all(["span", "div"], itemprop="startDate")[0]
        end_date_el = date_el.find_all(["span", "div"], itemprop="endDate")[0]
        start_date = datetime.strptime(start_date_el["content"], "%Y-%m-%d")
        end_date = datetime.strptime(end_date_el["content"], "%Y-%m-%d")
        return start_date, end_date

    def test_index_page(self):
        page = self.get_page("/")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 1)
        BasicSiteTestCase.check_event(events[0], name="Europe overlapping past today", location="Paris, France")

    def test_continent_page(self):
        page = self.get_page("/place/europe")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 4)
        for event in events:
            BasicSiteTestCase.check_event(event, location="Paris, France", year=2014)

    def test_country_page(self):
        page = self.get_page("/place/france")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 4)
        for event in events:
            BasicSiteTestCase.check_event(event, location="Paris, France", year=2014)

    def test_city_page(self):
        page = self.get_page("/place/paris")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 4)
        for event in events:
            BasicSiteTestCase.check_event(event, location="Paris, France", year=2014)

    def test_city_past_page(self):
        page = self.get_page("/place/paris/past")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 1)
        for event in events:
            BasicSiteTestCase.check_event(event, location="Paris, France", year=2013)

    def test_year_page(self):
        page = self.get_page("/year/2014")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 9)
        for event in events:
            BasicSiteTestCase.check_event(event, year=2014)

    def test_event_page(self):
        page = self.get_page("/event/1")
        events = page.find_all("div", "event-entry")
        eq_(len(events), 1)
        BasicSiteTestCase.check_event(events[0],
                                      name="Europe last year",
                                      location="Venue for Europe last year, Paris, France",
                                      year=2013)

    # def test_event_page_with_state(self):
    #     r = self.c.get("/event/2")
    #     assert "GDC" in r.data
    #     assert "San Francisco" in r.data
    #     assert "California" in r.data
    #     assert "March" in r.data
    #     assert "Moscone" in r.data
    #     assert "www.gdconf.com" in r.data

    def test_login(self):
        r = self.c.get("/")
        assert "Sign out" not in r.data

        r = self.login("test@gameconfs.com", "test")
        assert "Sign out" in r.data

        r = self.logout()
        assert "Sign out" not in r.data
