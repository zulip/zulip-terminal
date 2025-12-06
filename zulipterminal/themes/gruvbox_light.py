"""
GRUVBOX LIGHT
-------------

For syntax highlighting, this theme uses the solarized light styles
from pygments. This could be updated to a gruvbox style when the style
is released.

For further details on themefiles look at the theme contribution guide
"""

from pygments.styles.solarized import SolarizedLightStyle

from zulipterminal.config.color import Background
from zulipterminal.themes.colors_gruvbox import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.DARK2,                  Background.COLOR),
    'selected'         : (Color.LIGHT0_HARD,            Color.NEUTRAL_BLUE),
    'msg_selected'     : (Color.LIGHT0_HARD,            Color.NEUTRAL_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,           Color.FADED_BLUE),
    'general_narrow'   : (Color.LIGHT0_HARD,            Color.FADED_BLUE),
    'general_bar'      : (Color.DARK2,                  Background.COLOR),
    'msg_sender'       : (Color.NEUTRAL_YELLOW,         Background.COLOR),
    'unread'           : (Color.NEUTRAL_PURPLE,         Background.COLOR),
    'user_active'      : (Color.FADED_GREEN,            Background.COLOR),
    'user_idle'        : (Color.NEUTRAL_YELLOW,         Background.COLOR),
    'user_offline'     : (Color.DARK2,                  Background.COLOR),
    'user_inactive'    : (Color.DARK2,                  Background.COLOR),
    'user_bot'         : (Color.DARK2,                  Background.COLOR),
    'title'            : (Color.DARK2__BOLD,            Background.COLOR),
    'column_title'     : (Color.DARK2__BOLD,            Background.COLOR),
    'time'             : (Color.FADED_BLUE,             Background.COLOR),
    'bar'              : (Color.DARK2,                  Color.GRAY_245),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,         Background.COLOR),
    'reaction'         : (Color.NEUTRAL_PURPLE__BOLD,   Background.COLOR),
    'reaction_mine'    : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.LIGHT0_HARD__BOLD,      Color.FADED_GREEN),
    'msg_math'         : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'msg_mention'      : (Color.FADED_RED__BOLD,        Background.COLOR),
    'msg_link'         : (Color.FADED_BLUE,             Background.COLOR),
    'msg_link_index'   : (Color.FADED_BLUE__BOLD,       Background.COLOR),
    'msg_quote'        : (Color.NEUTRAL_YELLOW,         Background.COLOR),
    'msg_bold'         : (Color.DARK2__BOLD,            Background.COLOR),
    'msg_time'         : (Color.LIGHT0_HARD,            Color.DARK2),
    'footer'           : (Color.LIGHT0_HARD,            Color.DARK4),
    'footer_contrast'  : (Color.DARK2,                  Background.COLOR),
    'starred'          : (Color.FADED_RED__BOLD,        Background.COLOR),
    'unread_count'     : (Color.NEUTRAL_YELLOW,         Background.COLOR),
    'starred_count'    : (Color.DARK4,                  Background.COLOR),
    'table_head'       : (Color.DARK2__BOLD,            Background.COLOR),
    'filter_results'   : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'edit_topic'       : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'edit_tag'         : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'edit_author'      : (Color.NEUTRAL_YELLOW,         Background.COLOR),
    'edit_time'        : (Color.FADED_BLUE,             Background.COLOR),
    'current_user'     : (Color.DARK2,                  Background.COLOR),
    'muted'            : (Color.FADED_BLUE,             Background.COLOR),
    'popup_border'     : (Color.DARK2,                  Background.COLOR),
    'popup_category'   : (Color.FADED_BLUE__BOLD,       Background.COLOR),
    'popup_contrast'   : (Color.LIGHT0_HARD,            Color.GRAY_245),
    'popup_important'  : (Color.FADED_RED__BOLD,        Background.COLOR),
    'widget_disabled'  : (Color.GRAY_245,               Background.COLOR),
    'area:help'        : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'area:msg'         : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
    'area:stream'      : (Color.LIGHT0_HARD,            Color.FADED_BLUE),
    'area:error'       : (Color.LIGHT0_HARD,            Color.FADED_RED),
    'area:user'        : (Color.LIGHT0_HARD,            Color.FADED_YELLOW),
    'search_error'     : (Color.FADED_RED,              Background.COLOR),
    'task:success'     : (Color.LIGHT0_HARD,            Color.FADED_GREEN),
    'task:error'       : (Color.LIGHT0_HARD,            Color.FADED_RED),
    'task:warning'     : (Color.LIGHT0_HARD,            Color.NEUTRAL_PURPLE),
    'ui_code'          : (Color.LIGHT0_HARD,            Color.DARK2),
}

META = {
    'background': Color.LIGHT0_HARD,
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
