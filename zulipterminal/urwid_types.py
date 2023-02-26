"""
Types from the urwid API, to improve type checking
"""

from typing import Optional, Tuple, Union


# FIXME: These should likely be migrated at least partially to urwid stubs

urwid_Fixed = Tuple[()]  # noqa: N816
urwid_Flow = Tuple[int]  # noqa: N816
urwid_Box = Tuple[int, int]  # noqa: N816
urwid_Size = Union[urwid_Fixed, urwid_Flow, urwid_Box]  # noqa: N816

urwid_MarkupTuple = Tuple[Optional[str], str]  # noqa: N816
