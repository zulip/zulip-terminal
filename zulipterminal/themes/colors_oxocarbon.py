"""
COLORS FOR OXOCARBON THEME
--------------------------
Contains the oxocarbon color palette used by the oxocarbon themes.
For further details on themefiles look at the theme contribution guide.

This palette is adapted from oxocarbon.nvim, which is distributed under
the MIT License:
    https://github.com/nyoom-engineering/oxocarbon.nvim

    MIT License

    Copyright (c) 2022 Riccardo Mazzarini

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from enum import Enum

from zulipterminal.config.color import color_properties


# fmt: off
# NOTE: The 256code values are approximations from the xterm 256-color
# cube/grayscale ramp; the 24code values are the exact oxocarbon hex codes
# and are what will be used on any true-color (24-bit) terminal.

class OxocarbonColor(Enum):
    # color          =  16code          256code   24code

    # Background / grayscale ramp (dark -> light)
    BG               = 'black           h234      #161616'
    BG1              = 'black           h235      #262626'
    BG2              = 'dark_gray       h237      #393939'
    BG3              = 'dark_gray       h239      #525252'
    FG_DIM           = 'white           h254      #dde1e6'
    FG               = 'white           h255      #f2f4f8'
    WHITE            = 'white           h231      #ffffff'

    # Accent colors
    CYAN             = 'dark_cyan       h36       #08bdba'
    CYAN_LIGHT       = 'light_cyan      h43       #3ddbd9'
    BLUE             = 'light_blue      h111      #78a9ff'
    BLUE_LIGHT       = 'light_blue      h75       #33b1ff'
    PINK             = 'light_magenta   h169      #ee5396'
    PINK_LIGHT       = 'light_magenta   h211      #ff7eb6'
    GREEN            = 'light_green     h78       #42be65'
    PURPLE           = 'light_magenta   h141      #be95ff'

    # Light-variant colors (oxocarbon background=light); accents above are
    # shared between both variants.
    SLATE            = 'dark_gray       h238      #37474f'
    GRAY             = 'light_gray      h109      #90a4ae'
    BLUE_DEEP        = 'dark_blue       h27       #0f62fe'
    PURPLE_DEEP      = 'dark_magenta    h61       #673ab7'


# fmt: on


DefaultBoldColor = color_properties(OxocarbonColor, "BOLD")
