"""
CUSTOM HIGH CONTRAST
---------------------

This theme is inspired by the observed colors in the provided screenshot.
It uses a high-contrast color palette for better readability.

For further details on themefiles look at the theme contribution guide.
"""
from pygments.styles.solarized import SolarizedLightStyle

from zulipterminal.themes.colors_gruvbox import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'selected'         : (Color.LIGHT0_HARD,           Color.BRIGHT_YELLOW),
    'msg_selected'     : (Color.LIGHT0_HARD,           Color.BRIGHT_YELLOW),
    'header'           : (Color.BRIGHT_ORANGE,         Color.DARK0_HARD),
    'general_narrow'   : (Color.LIGHT0_HARD,           Color.DARK0_HARD),
    'general_bar'      : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'msg_sender'       : (Color.BRIGHT_GREEN,          Color.LIGHT0_HARD),
    'unread'           : (Color.BRIGHT_RED,            Color.LIGHT0_HARD),
    'user_active'      : (Color.BRIGHT_GREEN,          Color.LIGHT0_HARD),
    'user_idle'        : (Color.BRIGHT_YELLOW,         Color.LIGHT0_HARD),
    'user_offline'     : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'user_inactive'    : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'user_bot'         : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'title'            : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'column_title'     : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'time'             : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'bar'              : (Color.DARK0_HARD,            Color.GRAY_244),
    'msg_emoji'        : (Color.BRIGHT_PURPLE,         Color.LIGHT0_HARD),
    'reaction'         : (Color.BRIGHT_PURPLE,         Color.LIGHT0_HARD),
    'reaction_mine'    : (Color.LIGHT0_HARD,           Color.BRIGHT_PURPLE),
    'msg_heading'      : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'msg_math'         : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'msg_mention'      : (Color.BRIGHT_RED,            Color.LIGHT0_HARD),
    'msg_link'         : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'msg_link_index'   : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'msg_quote'        : (Color.BRIGHT_YELLOW,         Color.LIGHT0_HARD),
    'msg_bold'         : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'msg_time'         : (Color.LIGHT0_HARD,           Color.DARK0_HARD),
    'footer'           : (Color.LIGHT0_HARD,           Color.DARK2),
    'footer_contrast'  : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'starred'          : (Color.BRIGHT_RED,            Color.LIGHT0_HARD),
    'unread_count'     : (Color.BRIGHT_YELLOW,         Color.LIGHT0_HARD),
    'starred_count'    : (Color.DARK2,                 Color.LIGHT0_HARD),
    'table_head'       : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'filter_results'   : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'edit_topic'       : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'edit_tag'         : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'edit_author'      : (Color.BRIGHT_YELLOW,         Color.LIGHT0_HARD),
    'edit_time'        : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'current_user'     : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'muted'            : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'popup_border'     : (Color.DARK0_HARD,            Color.LIGHT0_HARD),
    'popup_category'   : (Color.BRIGHT_BLUE,           Color.LIGHT0_HARD),
    'popup_contrast'   : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'popup_important'  : (Color.BRIGHT_RED,            Color.LIGHT0_HARD),
    'widget_disabled'  : (Color.GRAY_244,              Color.LIGHT0_HARD),
    'area:help'        : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'area:msg'         : (Color.LIGHT0_HARD,           Color.BRIGHT_PURPLE),
    'area:stream'      : (Color.LIGHT0_HARD,           Color.BRIGHT_BLUE),
    'area:error'       : (Color.LIGHT0_HARD,           Color.BRIGHT_RED),
    'area:user'        : (Color.LIGHT0_HARD,           Color.BRIGHT_YELLOW),
    'search_error'     : (Color.BRIGHT_RED,            Color.LIGHT0_HARD),
    'task:success'     : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'task:error'       : (Color.LIGHT0_HARD,           Color.BRIGHT_RED),
    'task:warning'     : (Color.LIGHT0_HARD,           Color.BRIGHT_PURPLE),
    'ui_code'          : (Color.LIGHT0_HARD,           Color.DARK0_HARD),
}

META = {
    'background': Color.LIGHT0_HARD,
    'pygments': {
        'styles'    : SolarizedLightStyle().styles,
        'background': '#ffffff',
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
