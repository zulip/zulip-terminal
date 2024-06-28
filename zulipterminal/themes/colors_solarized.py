"""
COLORS FOR SOLARIZED THEMES
---------------------------
Contains color definitions or functions common accross solarized themes.
For further details on themefiles look at the theme contribution guide.

This file uses the official solarized colors.
For color reference see:
    https://github.com/altercation/solarized/blob/master/vim-colors-solarized/colors/solarized.vim
"""

from enum import Enum

from zulipterminal.config.color import color_properties

class SolarizedColor(Enum):
    # color          =  16code          256code   24code
    BASE03           = 'dark_gray       h234      #002b36'
    BASE02           = 'black           h234      #073642' # check 16+256, not used in dark right now
    BASE01           = 'light_green     h239      #586e75'
    BASE00           = 'yellow          h240      #657b83' # neiljp update 16

    BASE0            = 'light_blue      h244      #839496'
    BASE1            = 'light_cyan      h245      #93a1a1'
    BASE2            = 'white           h187      #eee8d5' # neiljp update 16 swap down
    BASE3            = 'light_gray      h230      #fdf6e3' # neiljp update 16 swap ^

    # These aliases are chosen to make it easier to select unique names in themes
    # Default text should be FG_PRIMARY on BG_REGULAR
    # Highlight can be FG_EMPHASIZE on BG_HIGHLIGHT (same brightness difference)
    #  - note that this is a very light highlight
    DARK_FG_EMPHASIZE = BASE1
    DARK_FG_PRIMARY   = BASE0
    DARK_FG_SECONDARY = BASE01
    DARK_BG_HIGHLIGHT = BASE02
    DARK_BG_REGULAR   = BASE03

    LIGHT_FG_EMPHASIZE = BASE01
    LIGHT_FG_PRIMARY   = BASE00
    LIGHT_FG_SECONDARY = BASE1
    LIGHT_BG_HIGHLIGHT = BASE2
    LIGHT_BG_REGULAR   = BASE3

    YELLOW           = 'yellow          h136      #b58900'
    ORANGE           = 'light_red       h136      #cb4b16' # check 16+256, not used in dark right now
    RED              = 'dark_red        h124      #dc322f'
    MAGENTA          = 'dark_magenta    h125      #d33682'
    VIOLET           = 'light_magenta   h61       #6c71c4'
    BLUE             = 'dark_blue       h33       #268bd2'
    CYAN             = 'dark_cyan       h37       #2aa198'
    GREEN            = 'dark_green      h64       #859900'
