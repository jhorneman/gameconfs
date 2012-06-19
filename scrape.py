# coding=utf-8

import re
import logging
import datetime
import codecs

import requests
from bs4 import BeautifulSoup

LOCAL_TEST_MODE = False

logger = logging.getLogger(__name__)

french_months = [u"Janvier", u"Février", u"Mars", u"Avril", u"Mai", u"Juxin", u"Juillet", u"Août", u"Septembre", u"Octobre", u"Novembre", u"Décembre"]
english_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def scrape_gibiz_event_list(_f):
    if LOCAL_TEST_MODE:
        soup = BeautifulSoup(open("data/gibiz_test.html"))
    else:
        r = requests.get("http://www.gamesindustry.biz/network/events")
        soup = BeautifulSoup(r.text)

    current_year = datetime.datetime.today().year

    date_rex = re.compile("\w\w\w (\d\d?)\w\w (\w\w\w)")
    date_range_rex = re.compile("\w\w\w (\d\d?)\w\w (\w\w\w) - \w\w\w (\d\d?)\w\w (\w\w\w)")

    for event_div in soup.find_all("div", "event"):
        tag = event_div.find("h3")
        tag = tag.find("a")
        title = tag.text.strip()
        detail_url = "http://www.gamesindustry.biz/" + tag["href"]

        # tag = event_div.find("p", "date")
        # results = date_rex.match(tag.text)
        # if results:
        #     start_date = datetime.datetime(day = int(results.group(1)), month = english_months.index(results.group(2)) + 1, year = current_year)
        # else:
        #     logger.error("Couldn't parse date '%s'" % tag.text)

        tag = event_div.find("p", "location")
        location = tag.text.strip()

        if LOCAL_TEST_MODE:
            detail_soup = BeautifulSoup(open("data/gibiz_detail_test.html"))
        else:
            r = requests.get(detail_url)
            detail_soup = BeautifulSoup(r.text)

        event_detail_div = detail_soup.find("div", "event")
        tag = event_detail_div.find("p", "meta")
        detail_text = tag.text

        date_start_index = detail_text.find("Date:")
        if date_start_index >= 0:
            raw_date = detail_text[date_start_index+6:]
            results = date_range_rex.match(raw_date)
            if results:
                start_date = datetime.datetime(day = int(results.group(1)), month = english_months.index(results.group(2)) + 1, year = current_year)
                end_date = datetime.datetime(day = int(results.group(3)), month = english_months.index(results.group(4)) + 1, year = current_year)
            else:
                logger.error("Couldn't parse date range '%s'" % raw_date)

        tag = tag.find("a")
        if tag:
            event_url = tag["href"].strip()
        else:
            event_url = ""

        _f.write("---\n")
        _f.write("name: %s\n" % title)
        _f.write("start_date: %s\n" % start_date.strftime("[%Y, %m, %d]"))
        _f.write("end_date: %s\n" % end_date.strftime("[%Y, %m, %d]"))
        _f.write('main_url: "%s"\n' % event_url)
        _f.write('twitter_hashtags: ""\n')
        _f.write("twitter_account:\n")
        _f.write("location: %s\n" % location)


def scrape_afjv_event_list(_f):
    if LOCAL_TEST_MODE:
        soup = BeautifulSoup(open("data/afjv_test.html"))
    else:
        r = requests.get("http://www.afjv.com/agenda_jeu_video.php")
        soup = BeautifulSoup(r.text)

    for event_div in soup.find_all("div", "ag_lign"):
        tag = event_div.find("time", itemprop="startDate")
        start_date = datetime.datetime.strptime(tag["datetime"][:10], "%Y-%m-%d")

        tag = event_div.find("time", itemprop="endDate")
        if tag:
            end_date = datetime.datetime.strptime(tag["datetime"][:10], "%Y-%m-%d")
        else:
            end_date = start_date

        tag = event_div.find("a", "ag_link")
        detail_url = "http://www.afjv.com" + tag["href"]

        tag = event_div.find("span", itemprop="summary")
        title = tag.text

        tag = event_div.find("span", itemprop="location")
        location = tag.text
        i = location.rfind(" - ")
        city = location[:i]
        country = location[i+3:]

        _f.write("---\n")
        _f.write("name: %s\n" % title)
        _f.write("start_date: %s\n" % start_date.strftime("[%Y, %m, %d]"))
        _f.write("end_date: %s\n" % end_date.strftime("[%Y, %m, %d]"))
        _f.write('main_url: ""\n')
        _f.write('twitter_hashtags: ""\n')
        _f.write("twitter_account:\n")
        _f.write("location: %s, %s\n" % (city, country))


if __name__ == "__main__":
    logging.basicConfig()
    with codecs.open('scraped.yaml', 'w', encoding='utf-8') as f:
        scrape_afjv_event_list(f)
        scrape_gibiz_event_list(f)