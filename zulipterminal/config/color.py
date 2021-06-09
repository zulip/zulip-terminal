"""
COLOR
-----
Contains color definitions or functions common across all themes.
For further details on themefiles look at the theme contribution guide.
"""
from enum import Enum
from typing import Any


def color_properties(colors: Any, *prop: str) -> Any:
    """
    Adds properties(Bold, Italics, etc...) to Enum Colors in theme files.
    Useage: color_properties(Color, 'BOLD', 'ITALICS', 'STRIKETHROUGH')

        NOTE: color_properties(Color, BOLD, ITALICS) would result in only
        Color.WHITE and Color.WHITE__BOLD_ITALICS
        but not Color.WHITE__BOLD or Color.WHITE__ITALICS.
        One would also have to do color_properties(Color, BOLD)
        and color_properties(Color, ITALICS) for the others to work
        >>> This function can be later extended to achieve all combinations
        with one call to the function.
    """
    prop_n = "_".join([p.upper() for p in prop])
    prop_v = " , ".join([p.lower() for p in prop])
    updated_colors: Any = Enum(  # type: ignore # Ref: python/mypy#529, #535 and #5317
        "Color",
        {
            **{c.name: c.value for c in colors},
            **{c.name + f"__{prop_n}": c.value + f" , {prop_v}" for c in colors},
        },
    )
    return updated_colors
