# -*- coding: utf-8 -*-

from nose.tools import *
import requests
from . import base_url, test_event


def test_search_post_returns_405():
    r = requests.post(base_url + "v1/search_events", params={})
    assert r.status_code == 405


def test_search_no_data_fails():
    r = requests.get(base_url + "v1/search_events", params={})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Query must contain at least one criterion.")


def test_search_wrong_data_fails():
    r = requests.get(base_url + "v1/search_events", params={"blah": 0})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Query must contain at least one criterion.")


def test_search_right_date():
    r = requests.get(base_url + "v1/search_events", params={"date": test_event["startDate"]})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]
    result = json["results"][0]
    eq_(result["name"], test_event["name"])
    eq_(result["city"], test_event["city"])
    eq_(result["country"], test_event["country"])


def test_search_date_wrong_format():
    r = requests.get(base_url + "v1/search_events", params={"date": "May 5th 2012"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")


def test_search_date_in_past():
    r = requests.get(base_url + "v1/search_events", params={"date": "2012-01-01"})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Can't search in the past.")


def test_search_start_date_but_no_end_date():
    r = requests.get(base_url + "v1/search_events", params={"startDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Found start date argument but no end date.")


def test_search_end_date_but_no_start_date():
    r = requests.get(base_url + "v1/search_events", params={"endDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Found end date argument but no start date.")


def test_search_start_date_wrong_format():
    r = requests.get(base_url + "v1/search_events", params={"startDate": "May 5th 2012", "endDate": test_event["endDate"]})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")


def test_search_start_date_in_past():
    r = requests.get(base_url + "v1/search_events", params={"startDate": "2012-01-01", "endDate": test_event["endDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Can't search in the past.")


def test_search_end_date_wrong_format():
    r = requests.get(base_url + "v1/search_events", params={"startDate": test_event["startDate"], "endDate": "May 5th 2012"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")


def test_search_end_date_before_start_date():
    r = requests.get(base_url + "v1/search_events", params={"startDate": test_event["endDate"], "endDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "End date may not be before start date.")


def test_search_event_name_empty():
    r = requests.get(base_url + "v1/search_events", params={"eventName": " "})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Event name argument was empty.")


def test_search_place_empty():
    r = requests.get(base_url + "v1/search_events", params={"place": " "})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Place argument was empty.")


def test_search_place_with_results():
    r = requests.get(base_url + "v1/search_events", params={"place": "Vienna"})
    assert r.status_code == 200
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], "Vienna")
    assert json["nrFoundEvents"] > 0
    assert len(json["results"]) == json["nrFoundEvents"]
    for result in json["results"]:
        eq_(result["city"], "Vienna")
        eq_(result["country"], "Austria")
        eq_(result["continent"], "Europe")


def test_search_place_with_no_results():
    r = requests.get(base_url + "v1/search_events", params={"place": "Vatican City"})
    assert r.status_code == 404
    json = r.json()
    assert "message" not in json
    eq_(json["foundLocationName"], None)
    assert json["nrFoundEvents"] == 0
    assert len(json["results"]) == json["nrFoundEvents"]
