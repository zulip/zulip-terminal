"""
COLORS FOR SOLARIZED THEMES
-------------------------
Contains color definitions or functions common accross solarized themes.
For further details on themefiles look at the theme contribution guide.

This file uses the official solarized colors.
For color reference see:
    https://github.com/altercation/solarized/blob/master/vim-colors-solarized/colors/solarized.vim
"""

from enum import Enum

from zulipterminal.config.color import DefaultBoldColor, color_properties

class SolarizedColor(Enum):
    # color          =  16code          256code   24code
    base03           = 'dark_gray       h234      #002b36'
    base02           = 'black           h235      #073642'
    base01           = 'light_green     h239      #586e75'
    base00           = 'dark_gray       h240      #657b83'
    base0            = 'light_blue      h244      #839496'
    base1            = 'light_cyan      h245      #93a1a1'
    base2            = 'light_gray      h187      #eee8d5'
    base3            = 'white           h230      #fdf6e3'
    yellow           = 'yellow          h136      #b58900'
    orange           = 'light_red       h166      #cb4b16'
    red              = 'dark_red        h124      #dc322f'
    magenta          = 'dark_magenta    h125      #d33682'
    violet           = 'light_magenta   h61       #6c71c4'
    blue             = 'dark_blue       h33       #268bd2'
    cyan             = 'dark_cyan       h37       #2aa198'
    green            = 'dark_green      h64       #859900'




DefaultBoldColor = color_properties(SolarizedColor, "BOLD")

    