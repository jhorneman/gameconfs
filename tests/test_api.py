# -*- coding: utf-8 -*-

import datetime
from nose.tools import *
import requests

base_url = "http://127.0.0.1:5000/api/"

test_event = {
    "startDate": datetime.date(2016, 7, 18),
    "endDate": datetime.date(2016, 7, 20),
    "place": "Vienna",
    "city": "Vienna",
    "country": "Austria",
    "name": "nucl.ai 2016"
}


def test_no_slug_404s():
    r = requests.get(base_url)
    assert r.status_code == 404


def test_wrong_slug_404s():
    r = requests.get(base_url + "v1/screw_up")
    assert r.status_code == 404


def test_wrong_version_404s():
    r = requests.get(base_url + "v0/upcoming")
    assert r.status_code == 404


def test_search_no_data_fails():
    r = requests.post(base_url + "v1/search_events", data={})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "No query parameters found in request.")


def test_search_wrong_data_fails():
    r = requests.post(base_url + "v1/search_events", data={"blah": 0})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Query must contain at least one criterion.")


def test_search_right_date():
    r = requests.post(base_url + "v1/search_events", data={"date": test_event["startDate"]})
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
    r = requests.post(base_url + "v1/search_events", data={"date": "May 5th 2012"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")
    assert json["message"].endswith("in query field 'date'.")


def test_search_date_in_past():
    r = requests.post(base_url + "v1/search_events", data={"date": "2012-01-01"})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Can't search in the past.")


def test_search_start_date_but_no_end_date():
    r = requests.post(base_url + "v1/search_events", data={"startDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Found start date query field but no end date.")


def test_search_end_date_but_no_start_date():
    r = requests.post(base_url + "v1/search_events", data={"endDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Found end date query field but no start date.")


def test_search_start_date_wrong_format():
    r = requests.post(base_url + "v1/search_events", data={"startDate": "May 5th 2012", "endDate": test_event["endDate"]})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")
    assert json["message"].endswith("in query field 'startDate'.")


def test_search_start_date_in_past():
    r = requests.post(base_url + "v1/search_events", data={"startDate": "2012-01-01", "endDate": test_event["endDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "Can't search in the past.")


def test_search_end_date_wrong_format():
    r = requests.post(base_url + "v1/search_events", data={"startDate": test_event["startDate"], "endDate": "May 5th 2012"})
    assert r.status_code == 400
    json = r.json()
    assert json["message"].startswith("Couldn't parse date")
    assert json["message"].endswith("in query field 'endDate'.")


def test_search_end_date_before_start_date():
    r = requests.post(base_url + "v1/search_events", data={"startDate": test_event["endDate"], "endDate": test_event["startDate"]})
    assert r.status_code == 400
    json = r.json()
    eq_(json["message"], "End date may not be before start date.")
