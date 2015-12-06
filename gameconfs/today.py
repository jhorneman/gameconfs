# -*- coding: utf-8 -*-

import datetime


__all__ = ["get_today", "get_now", "override_today"]


today_override = None


def get_today():
    global today_override
    return today_override if today_override else datetime.date.today()


def get_now():
    global today_override
    return datetime.datetime(today_override.year, today_override.month, today_override.day)\
        if today_override else datetime.datetime.now()


def override_today(_new_today):
    global today_override
    if isinstance(_new_today, datetime.datetime):
        _date = datetime.date(_new_today.year, _new_today.month, _new_today.day)
    today_override = _new_today
