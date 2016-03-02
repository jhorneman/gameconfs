# -*- coding: utf-8 -*-

from __future__ import absolute_import

# See https://api.slack.com/docs/formatting#how_to_escape_characters
html_escape_table = {
    "&": "&amp;",
    ">": "&gt;",
    "<": "&lt;"
}


def escape_text_for_slack(_text):
    return "".join(html_escape_table.get(c, c) for c in _text)
