"""
COLORS FOR GRUVBOX THEMES
-------------------------
Contains color definitions or functions common across gruvbox themes.
For further details on themefiles look at the theme contribution guide.

This file uses the official gruvbox colors where possible.
For color reference see:
    https://github.com/morhetz/gruvbox/blob/master/colors/gruvbox.vim
"""

from enum import Enum

from zulipterminal.config.color import color_properties


# fmt: off
# NOTE: The 24bit color codes use 256 color which can be
# enhanced to be truly 24bit.
# NOTE: The 256code format can be moved to h0-255 to
# make use of the complete range instead of only 216 colors.

class GruvBoxColor(Enum):
    # color          =  16code          256code   24code

    # Only or primarily dark mode - grayscales
    # - generally background
    DARK0_HARD       = 'black           h234      #1d2021'
    DARK0            = 'black           h235      #282828'
    DARK0_SOFT       = 'black           h236      #32302f'
    DARK1            = 'black           h237      #3c3836'
    DARK2            = 'black           h239      #504945'
    DARK3            = 'black           h241      #665c54'
    DARK4            = 'black           h243      #7c6f64'
    # - generally foreground
    LIGHT2           = 'white           h250      #d5c4a1'
    # - grays
    GRAY_244         = 'dark_gray       h244      #928374'
    GRAY_245         = 'dark_gray       h245      #928374'
    LIGHT4           = 'light_gray      h248      #bdae93'

    # Only or primarily light version - grayscales
    # - generally background
    LIGHT0_HARD      = 'white           h230      #f9f5d7'
    LIGHT0           = 'white           h229      #fbf1c7'
    LIGHT0_SOFT      = 'white           h228      #f2e5bc'
    LIGHT1           = 'white           h223      #ebdbb2'
    LIGHT4_256       = 'light_gray      h246      #a89984'

    # Dark mode only - colors
    BRIGHT_BLUE      = 'light_blue      h109      #83a598'
    BRIGHT_GREEN     = 'light_green     h142      #b8bb26'
    BRIGHT_RED       = 'light_red       h167      #fb4934'
    BRIGHT_YELLOW    = 'brown           h214      #fabd2f'

    # May be relevant to both modes
    NEUTRAL_BLUE     = 'dark_cyan       h66       #458588'
    NEUTRAL_PURPLE   = 'light_magenta   h132      #b16286'
    NEUTRAL_YELLOW   = 'brown           h172      #d79921'

    # Light mode only - colors
    FADED_BLUE       = 'dark_blue       h24       #076678'
    FADED_GREEN      = 'dark_green      h100      #79740e'
    FADED_RED        = 'dark_red        h88       #9d0006'
    FADED_YELLOW     = 'brown           h136      #b57614'

    # Additional colors
    BRIGHT_PURPLE    = 'light_magenta   h175      #d3869b'
    BRIGHT_AQUA      = 'light_cyan      h108      #8ec07c'
    BRIGHT_ORANGE    = 'light_red       h208      #fe8019'
    NEUTRAL_RED      = 'dark_red        h124      #cc241d'
    NEUTRAL_GREEN    = 'dark_green      h106      #98971a'
    NEUTRAL_AQUA     = 'dark_cyan       h72       #689d6a'
    NEUTRAL_ORANGE   = 'dark_red        h166      #d65d0e'
    FADED_PURPLE     = 'dark_magenta    h96       #8f3f71'
    FADED_AQUA       = 'dark_cyan       h66       #427b58'
    FADED_ORANGE     = 'dark_red        h130      #af3a03'

# fmt: on


DefaultBoldColor = color_properties(GruvBoxColor, "BOLD")
