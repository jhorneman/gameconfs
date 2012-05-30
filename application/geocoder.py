# coding=iso-8859-1
"""
    application.geocoder
    ====================

    Adds geocoding support and general location business logic.

    :copyright: (c) 2012 by Jurie Horneman.
"""

import logging
import datetime
import codecs
from urllib import urlencode
from urllib2 import urlopen
import json
import xml.dom.minidom
from xml.parsers.expat import ExpatError

logger = logging.getLogger(__name__)

#TODO: Add region biasing (see Google documentation) based on region of user

# Derived from: http://services.sapo.pt/GIS/GetCountries
# See: http://stackoverflow.com/questions/1283158/geolocation-api
continents_per_country_code = {"AD":"Europe","AE":"Asia","AF":"Asia","AG":"North America","AI":"North America","AL":"Europe","AM":"Asia","AN":"North America","AO":"Africa","AQ":"Antarctica","AR":"South America","AS":"Australia","AT":"Europe","AU":"Australia","AW":"North America","AZ":"Asia","BA":"Europe","BB":"North America","BD":"Asia","BE":"Europe","BF":"Africa","BG":"Europe","BH":"Asia","BI":"Africa","BJ":"Africa","BM":"North America","BN":"Asia","BO":"South America","BR":"South America","BS":"North America","BT":"Asia","BW":"Africa","BY":"Europe","BZ":"North America","CA":"North America","CC":"Asia","CD":"Africa","CF":"Africa","CG":"Africa","CH":"Europe","CI":"Africa","CK":"Australia","CL":"South America","CM":"Africa","CN":"Asia","CO":"South America","CR":"North America","CU":"North America","CV":"Africa","CX":"Asia","CY":"Asia","CZ":"Europe","DE":"Europe","DJ":"Africa","DK":"Europe","DM":"North America","DO":"North America","DZ":"Africa","EC":"South America","EE":"Europe","EG":"Africa","EH":"Africa","ER":"Africa","ES":"Europe","ET":"Africa","FI":"Europe","FJ":"Australia","FK":"South America","FM":"Australia","FO":"Europe","FR":"Europe","GA":"Africa","GB":"Europe","GD":"North America","GE":"Asia","GF":"South America","GG":"Europe","GH":"Africa","GI":"Europe","GL":"North America","GM":"Africa","GN":"Africa","GP":"North America","GQ":"Africa","GR":"Europe","GS":"Antarctica","GT":"North America","GU":"Australia","GW":"Africa","GY":"South America","HK":"Asia","HN":"North America","HR":"Europe","HT":"North America","HU":"Europe","ID":"Asia","IE":"Europe","IL":"Asia","IM":"Europe","IN":"Asia","IO":"Asia","IQ":"Asia","IR":"Asia","IS":"Europe","IT":"Europe","JE":"Europe","JM":"North America","JO":"Asia","JP":"Asia","KE":"Africa","KG":"Asia","KH":"Asia","KI":"Australia","KM":"Africa","KN":"North America","KP":"Asia","KR":"Asia","KW":"Asia","KY":"North America","KZ":"Asia","LA":"Asia","LB":"Asia","LC":"North America","LI":"Europe","LK":"Asia","LR":"Africa","LS":"Africa","LT":"Europe","LU":"Europe","LV":"Europe","LY":"Africa","MA":"Africa","MC":"Europe","MD":"Europe","ME":"Europe","MG":"Africa","MH":"Australia","MK":"Europe","ML":"Africa","MM":"Asia","MN":"Asia","MO":"Asia","MP":"Australia","MQ":"North America","MR":"Africa","MS":"North America","MT":"Europe","MU":"Africa","MV":"Asia","MW":"Africa","MX":"North America","MY":"Asia","MZ":"Africa","NA":"Africa","NC":"Australia","NE":"Africa","NF":"Australia","NG":"Africa","NI":"North America","NL":"Europe","NO":"Europe","NP":"Asia","NR":"Australia","NU":"Australia","NZ":"Australia","OM":"Asia","PA":"North America","PE":"South America","PF":"Australia","PG":"Australia","PH":"Asia","PK":"Asia","PL":"Europe","PM":"North America","PN":"Australia","PR":"North America","PS":"Asia","PT":"Europe","PW":"Australia","PY":"South America","QA":"Asia","RE":"Africa","RO":"Europe","RS":"Europe","RU":"Europe","RW":"Africa","SA":"Asia","SB":"Australia","SC":"Africa","SD":"Africa","SE":"Europe","SG":"Asia","SH":"Africa","SI":"Europe","SJ":"Europe","SK":"Europe","SL":"Africa","SM":"Europe","SN":"Africa","SO":"Africa","SR":"South America","ST":"Africa","SV":"North America","SY":"Asia","SZ":"Africa","TC":"North America","TD":"Africa","TF":"Antarctica","TG":"Africa","TH":"Asia","TJ":"Asia","TK":"Australia","TM":"Asia","TN":"Africa","TO":"Australia","TR":"Asia","TT":"North America","TV":"Australia","TW":"Asia","TZ":"Africa","UA":"Europe","UG":"Africa","US":"North America","UY":"South America","UZ":"Asia","VC":"North America","VE":"South America","VG":"North America","VI":"North America","VN":"Asia","VU":"Australia","WF":"Australia","WS":"Australia","YE":"Asia","YT":"Africa","ZA":"Africa","ZM":"Africa","ZW":"Africa"}

all_continents = list(set(continents_per_country_code.values()))

countries_with_states = ["United States", "Australia", "Canada", "Brazil"]


class GeocodeResults(object):
    """
    Results of geocoding a query string into location information using the Google Maps API.
    """

    cache_dict = {}

    @staticmethod
    def save_cache(_filename):
        with codecs.open(_filename, 'w', 'utf8') as f:
            f.write(json.dumps(GeocodeResults.cache_dict))

    @staticmethod
    def load_cache(_filename):
        with codecs.open(_filename, 'r', 'utf8') as f:
            try:
                GeocodeResults.cache_dict = json.loads(f.read())
            except ValueError:
                GeocodeResults.cache_dict = {}

    def __init__(self, _query, _use_cache=True):
        #: the original query string
        if isinstance(_query, unicode):
            self.query = _query.encode('utf-8', 'replace')
        else:
            self.query = _query
        #: True if geocoding succeeded
        self.is_valid = False
        #: the full formatted address
        self.formatted_address = "<Unknown>"
        #: the name of the city the location is in
        self.city = "<Unknown>"
        #: the name of the state the city is in, or None if states are not support for this country
        self.state = None
        #: the abbreviated name of the state (e.g. 'CA'), or empty if not supported
        self.state_abbr = ""
        #: the name of the country the city is in
        self.country = "<Unknown>"
        #: the name of the continent the country is in
        self.continent = "<Unknown>"

        if _use_cache and GeocodeResults.cache_dict.has_key(_query):
            logger.info("Geocoding query '%s': Using results from cache" % self.query)

            (retrieval_datetime, results) = GeocodeResults.cache_dict[_query]

            self.url = "<retrieved from cache>"
            self.raw_json = None
        else:
            logger.info("Geocoding query '%s': Using Google Maps API" % self.query)

            # Heavily inspired by geopy: http://code.google.com/p/geopy/
            # Google documentation: https://developers.google.com/maps/documentation/geocoding/

            # Call Google Maps API and read result
            params = {
                'address': self.query,
                'sensor': "false"
            }
            self.url = "http://maps.googleapis.com/maps/api/geocode/json?%s" % urlencode(params)
            page = urlopen(self.url)
            contents = page.read()

            # Convert result to Unicode
            # (HTTP 1.1 defines iso-8859-1 as the 'implied' encoding if none is given)
            encoding = page.headers.getparam("charset") or None
            if not encoding:
                try:
                    encoding = xml.dom.minidom.parseString(contents).encoding
                except ExpatError:
                    encoding = 'iso-8859-1'
                    pass
            self.raw_json = unicode(contents, encoding=encoding).encode('utf-8')

            # Parse JSON
            results = json.loads(self.raw_json)

            # Store in cache if results were OK
            if results["status"] == u"OK":
                GeocodeResults.cache_dict[_query] = (datetime.datetime.now().strftime("%Y%m%dT%H%M%S"), results)

        # Interpret results
        if results["status"] == u"OK":
            if len(results["results"]) == 0:
                logger.error("Geocoding query '%s': Status was 'OK' but no results were returned" % self.query)
            else:
                if len(results["results"]) > 1:
                    logger.info("Geocoding query '%s': More than 1 result was returned: using first one" % self.query)

                self.result = results["results"][0]
                self.is_valid = True

                self.formatted_address = self.result["formatted_address"]

                for component in self.result["address_components"]:
                    if u"locality" in component["types"]:
                        self.city = component["long_name"]

                    # Get state info
                    if u"administrative_area_level_1" in component["types"]:
                        self.state = component["long_name"]
                        # Get state abbreviation if the short name is different from the long name
                        if (self.state != component["short_name"]):
                            self.state_abbr = component["short_name"]

                    if u"country" in component["types"]:
                        self.country = component["long_name"]
                        self.continent = continents_per_country_code[component["short_name"]]

                # Reset state data if we don't support state for this country
                if self.country not in countries_with_states:
                    self.state = None
                    self.state_abbr = ""
        else:
            logger.error("Geocoding query '%s': Status was '%s' instead of 'OK'" % (self.query.decode('ascii', 'replace'), results["status"]))

    @property
    def is_in_a_state(self):
        """True if a state was found (e.g. California)"""
        return self.state != None

    def __unicode__(self):
        format_string = u"Address: {formatted_address}\nCity: {city}\n"
        if self.state:
            format_string += "State: {state}"
            if len(self.state_abbr):
                format_string += " ({state_abbr})"
            format_string += "\n"
        format_string += "Country: {country}\nContinent: {continent}"
        return format_string.format(**self.__dict__)

    def __str__(self):
        return self.__unicode__().encode('ascii', 'replace')


if __name__ == "__main__":
    for query in ["Naturhistorisches Museum in Vienna, Austria", "One Wimpole Street, London",
        "Luftkastellet, Malmö", "Moscone, 747 Howard Street, San Francisco", "Maceió, Alagoas, Brazil",
        "Shanghai International Convention Center, Shanghai", "Adelaide Convention Centre, Adelaide",
        "Koelnmesse, Köln, Germany"]:
        g = GeocodeResults(query)
        print unicode(g)
        print
    print json.dumps(GeocodeResults.cache_dict)
