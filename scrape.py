# coding=utf-8

from bs4 import BeautifulSoup
import requests
import re
import logging
import datetime

logger = logging.getLogger()

french_months = [u"Janvier", u"Février", u"Mars", u"Avril", u"Mai", u"Juxin", u"Juillet", u"Août", u"Septembre", u"Octobre", u"Novembre", u"Décembre"]


def scrape_french_agenda(_page):
    soup = BeautifulSoup(_page)

    # Read months from headers
    # date_rex = re.compile(u"(\w+) (\d\d\d\d)", re.UNICODE)
    # for month_header in soup.find_all("h3", "cb"):
    #     results = date_rex.match(month_header.text)
    #     if results:
    #         try:
    #             month = french_months.index(results.group(1)) + 1
    #             print "Found month", month, int(results.group(2))
    #         except ValueError:
    #             logger.error("Didn't recognize month '%s'" % (results.group(1)))
    #     else:
    #         logger.error("Couldn't parse month header '%s'" % month_header.text)

    # for month_div in soup.find_all("div", "ag_sche"):
    #     print "Found month", month_div["id"][1:5], month_div["id"][5:]

    base_url = "http://www.afjv.com"

    for event_div in soup.find_all("div", "ag_lign"):
        tag = event_div.find("time", itemprop="startDate")
        start_date = datetime.datetime.strptime(tag["datetime"][:10], "%Y-%m-%d")

        tag = event_div.find("time", itemprop="endDate")
        if tag:
            end_date = datetime.datetime.strptime(tag["datetime"][:10], "%Y-%m-%d")
        else:
            end_date = start_date

        tag = event_div.find("a", "ag_link")
        url = base_url + tag["href"]

        tag = event_div.find("span", itemprop="summary")
        title = tag.text

        tag = event_div.find("span", itemprop="location")
        location = tag.text

        if start_date == end_date:
            print "Found event", title, "taking place on", start_date.strftime("%x"), "in", location
        else:
            print "Found event", title, "taking place from", start_date.strftime("%x"), "until", end_date.strftime("%x"), "in", location


if __name__ == "__main__":
    # r = requests.get("http://www.afjv.com/agenda_jeu_video.php")
    # scrape_french_agenda(r.text)

    scrape_french_agenda(open("test.html"))
