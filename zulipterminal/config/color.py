"""
COLOR
-----
Contains color definitions or functions common across all themes.
For further details on themefiles look at the theme contribution guide.
"""
from enum import Enum
from typing import Any


# fmt: off
# NOTE: The 24bit color codes use 256 color which can be
# enhanced to be truly 24bit.
# NOTE: The 256code format can be moved to h0-255 to
# make use of the complete range instead of only 216 colors.
class DefaultColor(Enum):
    # color       =  16code          256code    24code
    DEFAULT       = 'default         default    default'
    BLACK         = 'black           g19        g19'
    DARK_RED      = 'dark_red        #a00       #a00'
    DARK_GREEN    = 'dark_green      #080       #080'
    BROWN         = 'brown           #880       #880'
    DARK_BLUE     = 'dark_blue       #24a       #24a'
    DARK_MAGENTA  = 'dark_magenta    h90        h90'      # #870087
    DARK_CYAN     = 'dark_cyan       #088       #088'
    DARK_GRAY     = 'dark_gray       #666       #666'
    LIGHT_RED     = 'light_red       #f00       #f00'
    LIGHT_GREEN   = 'light_green     #0f0       #0f0'
    YELLOW        = 'yellow          #ff0       #ff0'
    LIGHT_BLUE    = 'light_blue      #28d       #28d'
    LIGHT_MAGENTA = 'light_magenta   #c8f       #c8f'
    LIGHT_CYAN    = 'light_cyan      h152       h152'     # #afd7d7
    LIGHT_GRAY    = 'light_gray      #ccc       #ccc'
    WHITE         = 'white           #fff       #fff'
# fmt: on


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


DefaultBoldColor = color_properties(DefaultColor, "BOLD")
