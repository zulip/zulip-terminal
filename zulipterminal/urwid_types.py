from typing import Any, Optional, Sequence, Tuple, Union


urwid_Fixed = Tuple[()]
urwid_Flow = Tuple[int]
urwid_Box = Tuple[int, int]
urwid_Size = Union[urwid_Fixed, urwid_Flow, urwid_Box]

TextMarkupType = Union[
    # e.g., "hello"
    str,
    # e.g., ["This", "is", "a", "text"]
    Sequence[str],
    # e.g., ("red", "Styled text")
    Tuple[Optional[str], Any],
    # e.g., [(None, "Not styled"), ("red", "Styled")]
    Sequence[Tuple[Optional[str], Any]],
]

urwidTextMarkup = Union[TextMarkupType, Sequence[TextMarkupType]]
