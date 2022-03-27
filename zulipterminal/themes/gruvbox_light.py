"""
GRUVBOX LIGHT
-------------

For syntax highlighting, this theme uses the solarized light styles
from pygments. This could be updated to a gruvbox style when the style
is released.

For further details on themefiles look at the theme contribution guide
"""
from pygments.styles.solarized import SolarizedLightStyle

from zulipterminal.themes.colors_gruvbox import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.DARK2,                  Color.LIGHT0_HARD),
    'selected'         : (Color.LIGHT0_HARD,            Color.NEUTRAL_BLUE),
    'msg_selected'     : (Color.LIGHT0_HARD,            Color.NEUTRAL_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,           Color.FADED_BLUE),
    'general_narrow'   : (Color.LIGHT0_HARD,            Color.FADED_BLUE),
    'general_bar'      : (Color.DARK2,                  Color.LIGHT0_HARD),
    'name'             : (Color.NEUTRAL_YELLOW,         Color.LIGHT0_HARD),
    'unread'           : (Color.NEUTRAL_PURPLE,         Color.LIGHT0_HARD),
    'user_active'      : (Color.FADED_GREEN,            Color.LIGHT0_HARD),
    'user_idle'        : (Color.NEUTRAL_YELLOW,         Color.LIGHT0_HARD),
    'user_offline'     : (Color.DARK2,                  Color.LIGHT0_HARD),
    'user_inactive'    : (Color.DARK2,                  Color.LIGHT0_HARD),
    'title'            : (Color.DARK2__BOLD,            Color.LIGHT0_HARD),
    'column_title'     : (Color.DARK2__BOLD,            Color.LIGHT0_HARD),
    'time'             : (Color.FADED_BLUE,             Color.LIGHT0_HARD),
    'bar'              : (Color.DARK2,                  Color.GRAY_245),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,         Color.LIGHT0_HARD),
    'reaction'         : (Color.NEUTRAL_PURPLE__BOLD,   Color.LIGHT0_HARD),
    'reaction_mine'    : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.LIGHT0_HARD__BOLD,      Color.FADED_GREEN),
    'msg_math'         : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'msg_mention'      : (Color.FADED_RED__BOLD,        Color.LIGHT0_HARD),
    'msg_link'         : (Color.FADED_BLUE,             Color.LIGHT0_HARD),
    'msg_link_index'   : (Color.FADED_BLUE__BOLD,       Color.LIGHT0_HARD),
    'msg_quote'        : (Color.NEUTRAL_YELLOW,         Color.LIGHT0_HARD),
    'msg_code'         : (Color.LIGHT0_HARD,            Color.DARK2),
    'msg_bold'         : (Color.DARK2__BOLD,            Color.LIGHT0_HARD),
    'msg_time'         : (Color.LIGHT0_HARD,            Color.DARK2),
    'footer'           : (Color.LIGHT0_HARD,            Color.DARK4),
    'footer_contrast'  : (Color.DARK2,                  Color.LIGHT0_HARD),
    'starred'          : (Color.FADED_RED__BOLD,        Color.LIGHT0_HARD),
    'unread_count'     : (Color.NEUTRAL_YELLOW,         Color.LIGHT0_HARD),
    'starred_count'    : (Color.DARK4,                  Color.LIGHT0_HARD),
    'table_head'       : (Color.DARK2__BOLD,            Color.LIGHT0_HARD),
    'filter_results'   : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'edit_topic'       : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'edit_tag'         : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'edit_author'      : (Color.NEUTRAL_YELLOW,         Color.LIGHT0_HARD),
    'edit_time'        : (Color.FADED_BLUE,             Color.LIGHT0_HARD),
    'current_user'     : (Color.DARK2,                  Color.LIGHT0_HARD),
    'muted'            : (Color.FADED_BLUE,             Color.LIGHT0_HARD),
    'popup_border'     : (Color.DARK2,                  Color.LIGHT0_HARD),
    'popup_category'   : (Color.FADED_BLUE__BOLD,       Color.LIGHT0_HARD),
    'popup_contrast'   : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'popup_important'  : (Color.FADED_RED__BOLD,        Color.LIGHT0_HARD),
    'widget_disabled'  : (Color.GRAY_245,               Color.LIGHT0_HARD),
    'area:help'        : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'area:msg'         : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
    'area:stream'      : (Color.LIGHT0_HARD,            Color.FADED_BLUE),
    'area:error'       : (Color.LIGHT0_HARD,            Color.FADED_RED),
    'area:user'        : (Color.LIGHT0_HARD,            Color.FADED_YELLOW),
    'search_error'     : (Color.FADED_RED,              Color.LIGHT0_HARD),
    'task:success'     : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'task:error'       : (Color.LIGHT0_HARD,            Color.FADED_RED),
    'task:warning'     : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
}

META = {
    'pygments': {
        'styles'    : SolarizedLightStyle().styles,
        'background': '#ffffcc',
        'overrides' : {
            'c'   : '#586E75, italics',    # base01
            'cp'  : '#859900',             # magenta
            'cpf' : '#586e75',             # base01
            'ge'  : '#93A1A1, italics',    # base0
            'gh'  : '#CB4B16, bold',       # base0
            'gu'  : '#CB4B16, underline',  # base0
            'gp'  : '#93A1A1, bold',       # blue
            'gs'  : '#93A1A1, bold',       # base0
            'err' : '#93A1A1',             # red
            'n'   : '#93A1A1',             # gruvbox: light4
            'p'   : '#93A1A1',             # gruvbox: light4
            'w'   : '#93A1A1',             # gruvbox: light4
        }
    }
}
# fmt: on
