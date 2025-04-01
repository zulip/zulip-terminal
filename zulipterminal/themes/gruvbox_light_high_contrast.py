"""
GRUVBOX LIGHT HIGH CONTRAST
----------------------------

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
    None               : (Color.DARK0_HARD,            Background.COLOR),
    'selected'         : (Color.LIGHT0_HARD,           Color.NEUTRAL_BLUE),
    'msg_selected'     : (Color.LIGHT0_HARD,           Color.NEUTRAL_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,          Color.BRIGHT_BLUE),
    'general_narrow'   : (Color.LIGHT0_HARD,           Color.BRIGHT_BLUE),
    'general_bar'      : (Color.DARK0_HARD,            Background.COLOR),
    'msg_sender'       : (Color.NEUTRAL_YELLOW__BOLD,  Background.COLOR),
    'unread'           : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'user_active'      : (Color.BRIGHT_GREEN,          Background.COLOR),
    'user_idle'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'user_offline'     : (Color.DARK0_HARD,            Background.COLOR),
    'user_inactive'    : (Color.DARK0_HARD,            Background.COLOR),
    'user_bot'         : (Color.DARK0_HARD,            Background.COLOR),
    'title'            : (Color.DARK0_HARD__BOLD,      Background.COLOR),
    'column_title'     : (Color.DARK0_HARD__BOLD,      Background.COLOR),
    'time'             : (Color.BRIGHT_BLUE,           Background.COLOR),
    'bar'              : (Color.DARK0_HARD,            Color.GRAY_244),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'reaction'         : (Color.NEUTRAL_PURPLE__BOLD,  Background.COLOR),
    'reaction_mine'    : (Color.LIGHT0_HARD,           Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.LIGHT0_HARD__BOLD,     Color.BRIGHT_GREEN),
    'msg_math'         : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'msg_mention'      : (Color.BRIGHT_RED__BOLD,      Background.COLOR),
    'msg_link'         : (Color.BRIGHT_BLUE,           Background.COLOR),
    'msg_link_index'   : (Color.BRIGHT_BLUE__BOLD,     Background.COLOR),
    'msg_quote'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'msg_bold'         : (Color.DARK0_HARD__BOLD,      Background.COLOR),
    'msg_time'         : (Color.LIGHT0_HARD,           Color.DARK0_HARD),
    'footer'           : (Color.LIGHT0_HARD,           Color.LIGHT4),
    'footer_contrast'  : (Color.DARK0_HARD,            Background.COLOR),
    'starred'          : (Color.BRIGHT_RED__BOLD,      Background.COLOR),
    'unread_count'     : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'starred_count'    : (Color.LIGHT4,                Background.COLOR),
    'table_head'       : (Color.DARK0_HARD__BOLD,      Background.COLOR),
    'filter_results'   : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'edit_topic'       : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'edit_tag'         : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'edit_author'      : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'edit_time'        : (Color.BRIGHT_BLUE,           Background.COLOR),
    'current_user'     : (Color.DARK0_HARD,            Background.COLOR),
    'muted'            : (Color.BRIGHT_BLUE,           Background.COLOR),
    'popup_border'     : (Color.DARK0_HARD,            Background.COLOR),
    'popup_category'   : (Color.BRIGHT_BLUE__BOLD,     Background.COLOR),
    'popup_contrast'   : (Color.LIGHT0_HARD,           Color.GRAY_244),
    'popup_important'  : (Color.BRIGHT_RED__BOLD,      Background.COLOR),
    'widget_disabled'  : (Color.GRAY_244,              Background.COLOR),
    'area:help'        : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'area:msg'         : (Color.LIGHT0_HARD,           Color.NEUTRAL_PURPLE),
    'area:stream'      : (Color.LIGHT0_HARD,           Color.BRIGHT_BLUE),
    'area:error'       : (Color.LIGHT0_HARD,           Color.BRIGHT_RED),
    'area:user'        : (Color.LIGHT0_HARD,           Color.BRIGHT_YELLOW),
    'search_error'     : (Color.BRIGHT_RED,            Background.COLOR),
    'task:success'     : (Color.LIGHT0_HARD,           Color.BRIGHT_GREEN),
    'task:error'       : (Color.LIGHT0_HARD,           Color.BRIGHT_RED),
    'task:warning'     : (Color.LIGHT0_HARD,           Color.NEUTRAL_PURPLE),
    'ui_code'          : (Color.LIGHT0_HARD,           Color.DARK0_HARD),
}

META = {
    'background': Color.LIGHT0_HARD,
    'pygments': {
        'styles'    : SolarizedLightStyle().styles,
        'background': 'h230',
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