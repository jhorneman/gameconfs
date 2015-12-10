from gameconfs.today import get_today
from . import SiteTestCase


class BasicSiteTestCase(SiteTestCase):
    def test_index_page(self):
        rv = self.c.get("/")
        assert "Austria" in rv.data
        assert "United Kingdom" in rv.data

    def test_continent_page(self):
        rv = self.c.get("/place/europe")
        assert "Someconf" in rv.data
        assert "London" in rv.data
        assert "United Kingdom" in rv.data
        assert "May" in rv.data

    def test_country_page(self):
        rv = self.c.get("/place/austria")
        assert "Stagconf" in rv.data
        assert "Vienna" in rv.data
        assert "Austria" in rv.data
        assert "August" in rv.data

    def test_year_page(self):
        rv = self.c.get("/year/%s" % (get_today().year - 1))
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data

    def test_place_page(self):
        rv = self.c.get("/place/california")
        assert "GDC" not in rv.data
        assert "San Francisco" not in rv.data

    def test_place_past_page(self):
        rv = self.c.get("/place/california/past")
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data

    def test_event_page(self):
        rv = self.c.get("/event/1")
        assert "Stagconf" in rv.data
        assert "Vienna" in rv.data
        assert "Austria" in rv.data
        assert "August" in rv.data
        assert "Naturhistorisches" in rv.data
        assert "www.stagconf.com" in rv.data

    def test_event_page_with_state(self):
        rv = self.c.get("/event/2")
        assert "GDC" in rv.data
        assert "San Francisco" in rv.data
        assert "California" in rv.data
        assert "March" in rv.data
        assert "Moscone" in rv.data
        assert "www.gdconf.com" in rv.data

    def test_login(self):
        rv = self.c.get("/")
        assert "Sign out" not in rv.data

        rv = self.login("test@gameconfs.com", "test")
        assert "Sign out" in rv.data

        rv = self.logout()
        assert "Sign out" not in rv.data
