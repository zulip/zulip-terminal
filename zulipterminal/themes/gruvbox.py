"""
GRUVBOX
-------
This theme uses the official gruvbox color scheme.
For color reference see:
    https://github.com/morhetz/gruvbox/blob/master/colors/gruvbox.vim

For syntax highlighting, this theme uses the solarized dark styles
from pygments. This could be updated to a gruvbox style when the style
is released.

For further details on themefiles look at the theme contribution guide
"""
from enum import Enum

from pygments.styles.solarized import SolarizedDarkStyle

from zulipterminal.config.color import color_properties


# fmt: off
class GruvBoxColor(Enum):
    # color          =  16code          256code   24code
    DEFAULT          = 'default         default   default'
    DARK0_HARD       = 'black           h234      #1d2021'
    GRAY_244         = 'dark_gray       h244      #928374'
    LIGHT2           = 'white           h250      #d5c4a1'
    LIGHT4           = 'light_gray      h248      #bdae93'
    BRIGHT_BLUE      = 'light_blue      h109      #83a598'
    BRIGHT_GREEN     = 'light_green     h142      #b8bb26'
    BRIGHT_RED       = 'light_red       h167      #fb4934'
    NEUTRAL_PURPLE   = 'light_magenta   h132      #b16286'
    NEUTRAL_BLUE     = 'dark_cyan       h66       #458588'
    NEUTRAL_YELLOW   = 'yellow          h172      #d79921'
    FADED_BLUE       = 'dark_blue       h24       #076678'
    FADED_YELLOW     = 'brown           h136      #b57614'
    FADED_RED        = 'dark_red        h88       #9d0006'


Color = color_properties(GruvBoxColor, 'BOLD')


STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.LIGHT2,                Color.DARK0_HARD),
    'selected'         : (Color.LIGHT2,                Color.FADED_BLUE),
    'msg_selected'     : (Color.LIGHT2,                Color.FADED_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,          Color.FADED_BLUE),
    'general_narrow'   : (Color.LIGHT2,                Color.FADED_BLUE),
    'general_bar'      : (Color.LIGHT2,                Color.DARK0_HARD),
    'name'             : (Color.NEUTRAL_YELLOW__BOLD,  Color.DARK0_HARD),
    'unread'           : (Color.NEUTRAL_PURPLE,        Color.DARK0_HARD),
    'user_active'      : (Color.BRIGHT_GREEN,          Color.DARK0_HARD),
    'user_idle'        : (Color.NEUTRAL_YELLOW,        Color.DARK0_HARD),
    'user_offline'     : (Color.LIGHT2,                Color.DARK0_HARD),
    'user_inactive'    : (Color.LIGHT2,                Color.DARK0_HARD),
    'title'            : (Color.LIGHT2__BOLD,          Color.DARK0_HARD),
    'column_title'     : (Color.LIGHT2__BOLD,          Color.DARK0_HARD),
    'time'             : (Color.BRIGHT_BLUE,           Color.DARK0_HARD),
    'bar'              : (Color.LIGHT2,                Color.GRAY_244),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,        Color.DARK0_HARD),
    'reaction'         : (Color.NEUTRAL_PURPLE__BOLD,  Color.DARK0_HARD),
    'reaction_mine'    : (Color.DARK0_HARD,            Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.DARK0_HARD__BOLD,      Color.BRIGHT_GREEN),
    'msg_math'         : (Color.DARK0_HARD,            Color.GRAY_244),
    'msg_mention'      : (Color.BRIGHT_RED__BOLD,      Color.DARK0_HARD),
    'msg_link'         : (Color.BRIGHT_BLUE,           Color.DARK0_HARD),
    'msg_link_index'   : (Color.BRIGHT_BLUE__BOLD,     Color.DARK0_HARD),
    'msg_quote'        : (Color.FADED_YELLOW,          Color.DARK0_HARD),
    'msg_code'         : (Color.DARK0_HARD,            Color.LIGHT2),
    'msg_bold'         : (Color.LIGHT2__BOLD,          Color.DARK0_HARD),
    'msg_time'         : (Color.DARK0_HARD,            Color.LIGHT2),
    'footer'           : (Color.DARK0_HARD,            Color.LIGHT4),
    'footer_contrast'  : (Color.LIGHT2,                Color.DARK0_HARD),
    'starred'          : (Color.BRIGHT_RED__BOLD,      Color.DARK0_HARD),
    'unread_count'     : (Color.NEUTRAL_YELLOW,        Color.DARK0_HARD),
    'starred_count'    : (Color.LIGHT4,                Color.DARK0_HARD),
    'table_head'       : (Color.LIGHT2__BOLD,          Color.DARK0_HARD),
    'filter_results'   : (Color.DARK0_HARD,            Color.BRIGHT_GREEN),
    'edit_topic'       : (Color.DARK0_HARD,            Color.GRAY_244),
    'edit_tag'         : (Color.DARK0_HARD,            Color.GRAY_244),
    'edit_author'      : (Color.NEUTRAL_YELLOW,        Color.DARK0_HARD),
    'edit_time'        : (Color.BRIGHT_BLUE,           Color.DARK0_HARD),
    'current_user'     : (Color.LIGHT2,                Color.DARK0_HARD),
    'muted'            : (Color.BRIGHT_BLUE,           Color.DARK0_HARD),
    'popup_border'     : (Color.LIGHT2,                Color.DARK0_HARD),
    'popup_category'   : (Color.BRIGHT_BLUE__BOLD,     Color.DARK0_HARD),
    'popup_contrast'   : (Color.DARK0_HARD,            Color.GRAY_244),
    'popup_important'  : (Color.BRIGHT_RED__BOLD,      Color.DARK0_HARD),
    'widget_disabled'  : (Color.GRAY_244,              Color.DARK0_HARD),
    'area:help'        : (Color.DARK0_HARD,            Color.BRIGHT_GREEN),
    'area:msg'         : (Color.DARK0_HARD,            Color.BRIGHT_RED),
    'area:stream'      : (Color.DARK0_HARD,            Color.BRIGHT_BLUE),
    'area:error'       : (Color.LIGHT2,                Color.FADED_RED),
    'area:user'        : (Color.LIGHT2,                Color.FADED_BLUE),
    'search_error'     : (Color.BRIGHT_RED,            Color.DARK0_HARD),
    'task:success'     : (Color.DARK0_HARD,            Color.BRIGHT_GREEN),
    'task:error'       : (Color.LIGHT2,                Color.FADED_RED),
    'task:warning'     : (Color.DARK0_HARD,            Color.BRIGHT_RED),
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
            'n'   : '#bdae93',             # gruvbox: light4
            'p'   : '#bdae93',             # gruvbox: light4
            'w'   : '#bdae93',             # gruvbox: light4
        }
    }
}
# fmt: on
