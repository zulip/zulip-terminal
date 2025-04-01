"""
GRUVBOX DARK LOW CONTRAST
--------------------------

For syntax highlighting, this theme uses the solarized dark styles
from pygments. This could be updated to a gruvbox style when the style
is released.

For further details on themefiles look at the theme contribution guide
"""

from pygments.styles.solarized import SolarizedDarkStyle

from zulipterminal.config.color import Background
from zulipterminal.themes.colors_gruvbox import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.GRAY_244,              Background.COLOR),
    'selected'         : (Color.DARK1,                 Color.NEUTRAL_BLUE),
    'msg_selected'     : (Color.DARK1,                 Color.NEUTRAL_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,          Color.BRIGHT_BLUE),
    'general_narrow'   : (Color.DARK1,                 Color.BRIGHT_BLUE),
    'general_bar'      : (Color.GRAY_244,              Background.COLOR),
    'msg_sender'       : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'unread'           : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'user_active'      : (Color.BRIGHT_GREEN,          Background.COLOR),
    'user_idle'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'user_offline'     : (Color.GRAY_244,              Background.COLOR),
    'user_inactive'    : (Color.GRAY_244,              Background.COLOR),
    'user_bot'         : (Color.GRAY_244,              Background.COLOR),
    'title'            : (Color.GRAY_244,              Background.COLOR),
    'column_title'     : (Color.GRAY_244,              Background.COLOR),
    'time'             : (Color.BRIGHT_BLUE,           Background.COLOR),
    'bar'              : (Color.GRAY_244,              Color.GRAY_245),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'reaction'         : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'reaction_mine'    : (Color.DARK1,                 Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.DARK1,                 Color.BRIGHT_GREEN),
    'msg_math'         : (Color.DARK1,                 Color.GRAY_245),
    'msg_mention'      : (Color.BRIGHT_RED,            Background.COLOR),
    'msg_link'         : (Color.BRIGHT_BLUE,           Background.COLOR),
    'msg_link_index'   : (Color.BRIGHT_BLUE,           Background.COLOR),
    'msg_quote'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'msg_bold'         : (Color.GRAY_244,              Background.COLOR),
    'msg_time'         : (Color.DARK1,                 Color.GRAY_244),
    'footer'           : (Color.DARK1,                 Color.LIGHT4),
    'footer_contrast'  : (Color.GRAY_244,              Background.COLOR),
    'starred'          : (Color.BRIGHT_RED,            Background.COLOR),
    'unread_count'     : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'starred_count'    : (Color.LIGHT4,                Background.COLOR),
    'table_head'       : (Color.GRAY_244,              Background.COLOR),
    'filter_results'   : (Color.DARK1,                 Color.BRIGHT_GREEN),
    'edit_topic'       : (Color.DARK1,                 Color.GRAY_245),
    'edit_tag'         : (Color.DARK1,                 Color.GRAY_245),
    'edit_author'      : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'edit_time'        : (Color.BRIGHT_BLUE,           Background.COLOR),
    'current_user'     : (Color.GRAY_244,              Background.COLOR),
    'muted'            : (Color.BRIGHT_BLUE,           Background.COLOR),
    'popup_border'     : (Color.GRAY_244,              Background.COLOR),
    'popup_category'   : (Color.BRIGHT_BLUE,           Background.COLOR),
    'popup_contrast'   : (Color.DARK1,                 Color.GRAY_245),
    'popup_important'  : (Color.BRIGHT_RED,            Background.COLOR),
    'widget_disabled'  : (Color.GRAY_245,              Background.COLOR),
    'area:help'        : (Color.DARK1,                 Color.BRIGHT_GREEN),
    'area:msg'         : (Color.DARK1,                 Color.NEUTRAL_PURPLE),
    'area:stream'      : (Color.DARK1,                 Color.BRIGHT_BLUE),
    'area:error'       : (Color.DARK1,                 Color.BRIGHT_RED),
    'area:user'        : (Color.DARK1,                 Color.BRIGHT_YELLOW),
    'search_error'     : (Color.BRIGHT_RED,            Background.COLOR),
    'task:success'     : (Color.DARK1,                 Color.BRIGHT_GREEN),
    'task:error'       : (Color.DARK1,                 Color.BRIGHT_RED),
    'task:warning'     : (Color.DARK1,                 Color.NEUTRAL_PURPLE),
    'ui_code'          : (Color.DARK1,                 Color.GRAY_244),
}

META = {
    'background': Color.DARK1,
    'pygments': {
        'styles'    : SolarizedDarkStyle().styles,
        'background': 'h237',
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