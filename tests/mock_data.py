# -*- coding: utf-8 -*-

import os
import codecs
import json
from datetime import datetime
import sqlalchemy.orm
from gameconfs.models import Event, City, State, Country, Continent
from gameconfs.today import get_now


__all__ = ["load_geo_data", "load_mock_user", "load_old_mock_events"]


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__)) + os.sep
mock_data_dir = os.path.join(SCRIPT_DIR, "mock_data")


def load_geo_data(_db_session):
    continents_by_id = {}
    with codecs.open(os.path.join(mock_data_dir, "continents.json"), "r", "utf-8") as f:
        for continent_data in json.load(f):
            continents_by_id[continent_data["id"]] = continent_data["name"]
            new_continent = Continent(continent_data["name"])
            _db_session.add(new_continent)
    _db_session.commit()

    countries_by_id = {}
    with codecs.open(os.path.join(mock_data_dir, "countries.json"), "r", "utf-8") as f:
        for country_data in json.load(f):
            countries_by_id[country_data["id"]] = country_data["name"]
            new_country = Country(country_data["name"])
            continent_name = continents_by_id[country_data["continent_id"]]
            new_country.continent = _db_session.query(Continent).filter(Continent.name == continent_name).one()
            _db_session.add(new_country)
    _db_session.commit()

    states_by_id = {}
    with codecs.open(os.path.join(mock_data_dir, "states.json"), "r", "utf-8") as f:
        for state_data in json.load(f):
            states_by_id[state_data["id"]] = state_data["name"]
            new_state = State(state_data["name"], state_data["short_name"])
            country_name = countries_by_id[state_data["country_id"]]
            new_state.country = _db_session.query(Country).filter(Country.name == country_name).one()
            _db_session.add(new_state)
    _db_session.commit()

    cities_by_id = {}
    with codecs.open(os.path.join(mock_data_dir, "cities.json"), "r", "utf-8") as f:
        for city_data in json.load(f):
            cities_by_id[city_data["id"]] = city_data["name"]
            new_city = City(city_data["name"])
            country_name = countries_by_id[city_data["country_id"]]
            new_city.country = _db_session.query(Country).filter(Country.name == country_name).one()
            if city_data["state_id"]:
                state_name = states_by_id[city_data["state_id"]]
                new_city.state = _db_session.query(State).filter(State.name == state_name).one()
            _db_session.add(new_city)
    _db_session.commit()


def parse_date(_date_as_string):
    return datetime.strptime(_date_as_string, "%Y-%m-%d")


def load_mock_events(_db_session):
    now = get_now()

    with codecs.open(os.path.join(mock_data_dir, "events.json"), "r", "utf-8") as f:
        for event_data in json.load(f):
            new_event = Event()
            new_event.created_at = now
            new_event.last_modified_at = now
            new_event.publish_status = event_data.get("publish_status", "published")
            new_event.name = event_data["name"]
            new_event.start_date = parse_date(event_data["start_date"])
            new_event.end_date = parse_date(event_data.get("end_date", event_data["start_date"]))
            new_event.event_url = event_data.get("url", "http://www.gameconfs.com/")
            new_event.twitter_hashtags = ""
            new_event.twitter_account = ""
            new_event.venue = "Venue for " + event_data["name"]
            if "city" in event_data:
                try:
                    new_event.city = _db_session.query(City).filter(City.name == event_data["city"]).first()
                except sqlalchemy.orm.exc.NoResultFound:
                    raise Exception("Couldn't find city '{0}' - did you add it to the mock data?".format(event_data["city"]))
            _db_session.add(new_event)

    _db_session.commit()


def load_mock_user(_db_session, _user_datastore):
    admin_role = _user_datastore.create_role(name="admin")
    user = _user_datastore.create_user(user_name="Test", email="test@gameconfs.com", password="test")
    _user_datastore.add_role_to_user(user, admin_role)
    _db_session.commit()
