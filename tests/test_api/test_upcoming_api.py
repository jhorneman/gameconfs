# -*- coding: utf-8 -*-

from nose.tools import *
import requests
from . import base_url, test_event


def call_api(_params):
    return requests.get(base_url + "v1/upcoming", params=_params)


def test_upcoming_post_returns_405():
    r = requests.post(base_url + "v1/upcoming", params={})
    assert r.status_code == 405


def test_upcoming_no_data_fails():
    r = call_api({})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_wrong_data_fails():
    r = call_api({"blah": 0})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_nr_months_wrong_format():
    r = call_api({"nrMonths": "FIVE"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Could not parse nrMonths value")


def test_upcoming_nr_months_illegal_values():
    r = call_api({"nrMonths": -1})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths must be at least 1.")

    r = call_api({"nrMonths": 0})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths must be at least 1.")

    r = call_api({"nrMonths": 13})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "nrMonths may not be higher than 12.")


def test_upcoming_nr_months_legal_values():
    r = call_api({"nrMonths": 1})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]

    r = call_api({"nrMonths": 12})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]


def test_upcoming_place_empty():
    r = call_api({"place": " "})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Place argument was empty.")
