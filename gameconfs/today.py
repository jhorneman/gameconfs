# -*- coding: utf-8 -*-

from datetime import date


today_override = None


def get_today():
    global today_override
    return today_override if today_override else date.today()


def override_today(_new_today):
    global today_override
    today_override = _new_today
