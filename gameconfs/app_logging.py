# -*- coding: utf-8 -*-

import sys
import logging
import geocoder


class StdoutHandler(logging.StreamHandler):
    def __init__(self):
        super(StdoutHandler, self).__init__(sys.stdout)

    def emit(self, record):
        super(StdoutHandler, self).emit(record)
        super(StdoutHandler, self).flush()


def set_up_logging(_app, _level=logging.INFO):
    handler = StdoutHandler()
    handler.setLevel(_level)
    handler.setFormatter(logging.Formatter('%(message)s'))
    for logger in [_app.logger, geocoder.logger]:
        logger.setLevel(_level)
        logger.addHandler(handler)
