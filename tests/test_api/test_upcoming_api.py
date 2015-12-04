# -*- coding: utf-8 -*-

from nose.tools import *
import requests
from . import base_url, test_event


def test_upcoming_post_returns_405():
    r = requests.post(base_url + "v1/upcoming", params={})
    assert r.status_code == 405


def test_upcoming_no_data_fails():
    r = requests.get(base_url + "v1/upcoming", params={})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_wrong_data_fails():
    r = requests.get(base_url + "v1/upcoming", params={"blah": 0})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_nr_months_wrong_format():
    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": "FIVE"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Could not parse nrMonths value")


def test_upcoming_nr_months_illegal_values():
    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": -1})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths must be at least 1.")

    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": 0})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths must be at least 1.")

    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": 13})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths may not be higher than 12.")


def test_upcoming_nr_months_legal_values():
    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": 1})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]

    r = requests.get(base_url + "v1/upcoming", params={"nrMonths": 12})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_place_empty():
    r = requests.get(base_url + "v1/upcoming", params={"place": " "})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Place argument was empty.")
