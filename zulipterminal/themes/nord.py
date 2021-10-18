"""
NORD
-------
This theme uses the official nord color scheme.
For color reference see:
    https://www.nordtheme.com/docs/colors-and-palettes

For syntax highlighting, this theme uses the solarized dark styles
from pygments. This could be updated to a nord style when the style
is released.

For further details on themefiles look at the theme contribution guide

NordColor Enum color names are the same as the Nord theme pallete:
https://www.nordtheme.com/docs/colors-and-palettes

"""
from enum import Enum

from pygments.styles.solarized import SolarizedDarkStyle

from zulipterminal.config.color import color_properties


# fmt: off

class NordColor(Enum):
    DEFAULT          = 'default         default   default'
    NORD_0           = 'black           h237      #2e3440'
    NORD_1           = 'dark_gray       h240      #3b4252'
    NORD_7           = 'light_blue      h153      #88c0d0'
    NORD_8           = 'white           h159      #8fbcbb'
    NORD_9           = 'dark_cyan       h147      #81a1c1'
    GREENISH         = 'light_green     h152      #83a598'
    NORD_14          = 'dark_green      h108      #a3be8c'
    NORD_11          = 'dark_red        h88       #bf616a'
    NORD_15          = 'light_magenta   h97       #b48ead'
    NORD_6           = 'white           h255      #eceff4'
    NORD_13          = 'yellow          h222      #ebcb8b'
    NORD_2           = 'dark_gray       h238      #434c5e'
    FADED_YELLOW     = 'brown           h214      #b57614'
    NORD_12          = 'light_red       h173      #d08770'


Color = color_properties(NordColor, 'BOLD')


STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.NORD_7,                Color.NORD_0),
    'selected'         : (Color.NORD_7,                Color.NORD_2),
    'msg_selected'     : (Color.NORD_7,                Color.NORD_2),
    'header'           : (Color.NORD_6,                Color.NORD_2),
    'general_narrow'   : (Color.NORD_7,                Color.NORD_2),
    'general_bar'      : (Color.NORD_7,                Color.NORD_0),
    'name'             : (Color.NORD_6__BOLD,          Color.NORD_0),
    'unread'           : (Color.NORD_8,                Color.NORD_0),
    'user_active'      : (Color.NORD_14,               Color.NORD_0),
    'user_idle'        : (Color.NORD_13,               Color.NORD_0),
    'user_offline'     : (Color.NORD_7,                Color.NORD_0),
    'user_inactive'    : (Color.NORD_7,                Color.NORD_0),
    'title'            : (Color.NORD_7__BOLD,          Color.NORD_0),
    'column_title'     : (Color.NORD_7__BOLD,          Color.NORD_0),
    'time'             : (Color.GREENISH,              Color.NORD_0),
    'bar'              : (Color.NORD_7,                Color.NORD_1),
    'msg_emoji'        : (Color.NORD_15,               Color.NORD_0),
    'reaction'         : (Color.NORD_15__BOLD,         Color.NORD_0),
    'reaction_mine'    : (Color.NORD_0,                Color.NORD_15),
    'msg_math'         : (Color.NORD_0,                Color.NORD_1),
    'msg_mention'      : (Color.NORD_15__BOLD,         Color.NORD_0),
    'msg_link'         : (Color.GREENISH,              Color.NORD_0),
    'msg_link_index'   : (Color.GREENISH__BOLD,        Color.NORD_0),
    'msg_quote'        : (Color.NORD_13,               Color.NORD_0),
    'msg_code'         : (Color.NORD_0,                Color.NORD_7),
    'msg_bold'         : (Color.NORD_7__BOLD,          Color.NORD_0),
    'msg_time'         : (Color.NORD_0,                Color.NORD_7),
    'footer'           : (Color.NORD_0,                Color.NORD_9),
    'footer_contrast'  : (Color.NORD_7,                Color.NORD_0),
    'starred'          : (Color.NORD_11__BOLD,         Color.NORD_0),
    'unread_count'     : (Color.NORD_9,                Color.NORD_0),
    'starred_count'    : (Color.NORD_9,                Color.NORD_0),
    'table_head'       : (Color.NORD_7__BOLD,          Color.NORD_0),
    'filter_results'   : (Color.NORD_0,                Color.NORD_14),
    'edit_topic'       : (Color.NORD_0,                Color.NORD_1),
    'edit_tag'         : (Color.NORD_0,                Color.NORD_1),
    'edit_author'      : (Color.NORD_13,               Color.NORD_0),
    'edit_time'        : (Color.GREENISH,              Color.NORD_0),
    'current_user'     : (Color.NORD_7,                Color.NORD_0),
    'muted'            : (Color.GREENISH,              Color.NORD_0),
    'popup_border'     : (Color.NORD_7,                Color.NORD_0),
    'popup_category'   : (Color.GREENISH__BOLD,        Color.NORD_0),
    'popup_contrast'   : (Color.NORD_0,                Color.NORD_1),
    'popup_important'  : (Color.NORD_11__BOLD,         Color.NORD_0),
    'widget_disabled'  : (Color.NORD_1,                Color.NORD_0),
    'area:help'        : (Color.NORD_0,                Color.NORD_14),
    'area:msg'         : (Color.NORD_0,                Color.NORD_11),
    'area:stream'      : (Color.NORD_0,                Color.GREENISH),
    'area:error'       : (Color.NORD_7,                Color.NORD_12),
    'area:user'        : (Color.NORD_7,                Color.NORD_2),
    'search_error'     : (Color.NORD_11,               Color.NORD_0),
    'task:success'     : (Color.NORD_0,                Color.NORD_14),
    'task:error'       : (Color.NORD_7,                Color.NORD_12),
    'task:warning'     : (Color.NORD_0,                Color.NORD_11),
}

META = {
    'pygments': {
        'styles'    : SolarizedDarkStyle().styles,
        'background': 'h236',
        'overrides' : {
            'c'   : '#586e75, italics',    # base01
            'cp'  : '#d33682',             # magenta
            'cpf' : '#586e75',             # base01
            'ge'  : '#839496, italics',    # base0
            'gh'  : '#839496, bold',       # base0
            'gu'  : '#839496, underline',  # base0
            'gp'  : '#268bd2, bold',       # blue
            'gs'  : '#839496, bold',       # base0
            'err' : '#dc322f',             # red
            'n'   : '#bdae93',             # gruvbox: NORD_9
            'p'   : '#bdae93',             # gruvbox: NORD_9
            'w'   : '#bdae93',             # gruvbox: NORD_9
        }
    }
}
# fmt: on
