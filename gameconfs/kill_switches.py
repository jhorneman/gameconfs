# -*- coding: utf-8 -*-

import logging
import os
from app_logging import add_logger
from project import PROJECT_NAME


logger = logging.getLogger(__name__)
add_logger(logger)

feature_names = ["CACHE", "EDITING", "EMAIL", "SPONSORING", "CE_RETARGET"]


def _build_kill_switch_name(_feature_name):
    if _feature_name not in feature_names:
        logger.error("Unknown kill switch feature '{0}'.".format(_feature_name))
        return None
    return PROJECT_NAME.upper() + "_KILL_" + _feature_name


def get_boolean_from_environment_variable(_environment_variable_name):
    value = os.environ.get(_environment_variable_name, False)
    if isinstance(value, basestring):
        return value.lower() in ["1", "yes", "y", "true"]
    else:
        return bool(value)


def _load_kill_switch(_app, _feature_name):
    kill_switch_name = _build_kill_switch_name(_feature_name)
    if kill_switch_name:
        environment_variable_name = PROJECT_NAME.upper() + "_" + kill_switch_name
        _app.config[kill_switch_name] = get_boolean_from_environment_variable(environment_variable_name)


def load_all_kill_switches(_app):
    for kill_switch_name in feature_names:
        _load_kill_switch(_app, kill_switch_name)


def is_feature_on(_app, _feature_name):
    kill_switch_name = _build_kill_switch_name(_feature_name)
    if kill_switch_name:
        return not _app.config[kill_switch_name]
    else:
        return False


def _set_feature_kill_switch(_app, _feature_name, _new_value):
    kill_switch_name = _build_kill_switch_name(_feature_name)
    if kill_switch_name:
        _app.config[kill_switch_name] = _new_value


def turn_feature_on(_app, _feature_name):
    _set_feature_kill_switch(_app, _feature_name, False)


def turn_feature_off(_app, _feature_name):
    _set_feature_kill_switch(_app, _feature_name, True)
