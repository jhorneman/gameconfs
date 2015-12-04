# The Gameconfs API

Gameconfs has an API you can call over HTTP using GET requests.

The base URL is

    www.gameconfs.com/api/v1

The parameters are strings encoded as URL parameters (e.g. use %20 for spaces).

The results are returned in a JSON object.

The HTTP status code is used to indicate if there was a problem, e.g. 400 (bad request), 404 (no results found), 500 (internal error).

## /search_events

Searches for events. You cannot search in the past.

### Parameters

Dates must be in the format "yyyy-mm-dd", so for example "2016-07-19" represents July 19th 2016.

All parameters are optional but you must pass at least one search criterion.

| Parameter | Meaning |
|--|--|
| date | The date you want to search for events. If you pass date, start and end date parameters are ignored. Optional: when no date or date range is passed, all events starting from today are searched. |
| startDate | The start of the date range you want to search for events. Must be accompanied by endDate. Optional: when no date or date range is passed, all events starting from today are searched. |
| endDate | The end of the date range you want to search for events. Must be accompanied by startDate. |
| eventName | The name of the event you're searching for. |
| place | The continent, country, state or city you want to search for events. Optional: when left out, events from all over the world are searched. |

### Results

The HTTP status will be 404 when no events were found.

| Field | Meaning |
|--|--|
| message | Only occurs when something went wrong. Explains the problem. |
| searchedLocationName | The place parameter you sent, or null if it was left out. |
| foundLocationName | The place that was found, or null if there was no place parameter. |
| nrFoundEvents | The number of found events. |
| results | An array with data per found event. See below for a description of the event data. |

Each event has the following structure:

| Field | Meaning |
|--|--|
| name | The name of the event. |
| venue | The venue. |
| startDate | The start date (in the same format as date parameters). |
| endDate | The end date. |
| eventUrl | The URL of the event's website. |
| city | The city the event takes place in. |
| state | The state (if Gameconfs tracks states for this country, otherwise null). |
| country | The country. |
| continent | The continent. |

### Examples

    www.gameconfs.com/api/v1/search_events?date=2016-07-19

Returns a list of events that take place on 19th of July 2016.

## /upcoming

Returns upcoming events.


### Parameters

| Parameter | Meaning |
|--|--|
| nrMonths | Number of months from today you want to get upcoming events for. Must be between 1 and 12. Optional: defaults to 3. |
| place | The continent, country, state or city you want to get upcoming events for. Optional: when left out, events from all over the world are returned. |


### Results

The HTTP status will be 404 when no events were found.

| Field | Meaning |
|--|--|
| message | Only occurs when something went wrong. Explains the problem. |
| searchedLocationName | The place parameter you sent, or null if it was left out. |
| foundLocationName | The place that was found, or null if there was no place parameter. |
| nrMonths | The number of months value that was used. |
| nrFoundEvents | The number of found events. |
| results | An array with data per found event. See search_events, above, for a description of the event data. |

### Examples

    http://127.0.0.1:5000/api/v1/upcoming

Returns events happening in the next three months all over the world.

## Questions? Feedback?

<a href="mailto:admin@gameconfs.com">Email me</a>.