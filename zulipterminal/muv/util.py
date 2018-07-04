"""Utilities"""
from functools import wraps

import urwid


def make_padding(left, right):
    """add paddings to left and right side of a widget"""
    def _padding(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """return padding function"""
            markups = func(*args, **kwargs)
            if not isinstance(markups, urwid.Widget):
                # default to Text widget if not already is
                markups = urwid.Text(urwid)
            return urwid.Padding(markups, align='left',
                                 width=('relative', 100), min_width=None,
                                 left=left, right=right)
        return wrapper
    return _padding


def check_if_italic():
    """Check whether current version of urwid support italic"""
    return 'italics' in urwid.display_common._ATTRIBUTES
