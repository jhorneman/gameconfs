# -*- coding: utf-8 -*-

from datetime import date, datetime


__all__ = ["get_today", "get_now", "override_today"]


today_override = None


def get_today():
    global today_override
    return today_override if today_override else date.today()


def get_now():
    global today_override
    return datetime(today_override.year, today_override.month, today_override.day) if today_override else datetime.now()


def override_today(_new_today):
    global today_override
    today_override = _new_today
