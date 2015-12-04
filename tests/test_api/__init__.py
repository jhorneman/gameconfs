# -*- coding: utf-8 -*-

import datetime
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


def test_index_works():
    r = requests.get(base_url)
    assert r.status_code == 200


def test_wrong_slug_404s():
    r = requests.get(base_url + "v1/screw_up")
    assert r.status_code == 404


def test_wrong_version_404s():
    r = requests.get(base_url + "v0/upcoming")
    assert r.status_code == 404
