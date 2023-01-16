"""
Types from the urwid API, to improve type checking
"""

from typing import Optional, Tuple, Union


urwid_Fixed = Tuple[()]
urwid_Flow = Tuple[int]
urwid_Box = Tuple[int, int]
urwid_Size = Union[urwid_Fixed, urwid_Flow, urwid_Box]

urwid_MarkupTuple = Tuple[Optional[str], str]
