"""
GRUVBOX LIGHT LOW CONTRAST
---------------------------

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
    None               : (Color.LIGHT4,                Background.COLOR),
    'selected'         : (Color.LIGHT1,                Color.NEUTRAL_BLUE),
    'msg_selected'     : (Color.LIGHT1,                Color.NEUTRAL_BLUE),
    'header'           : (Color.NEUTRAL_BLUE,          Color.BRIGHT_BLUE),
    'general_narrow'   : (Color.LIGHT1,                Color.BRIGHT_BLUE),
    'general_bar'      : (Color.LIGHT4,                Background.COLOR),
    'msg_sender'       : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'unread'           : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'user_active'      : (Color.BRIGHT_GREEN,          Background.COLOR),
    'user_idle'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'user_offline'     : (Color.LIGHT4,                Background.COLOR),
    'user_inactive'    : (Color.LIGHT4,                Background.COLOR),
    'user_bot'         : (Color.LIGHT4,                Background.COLOR),
    'title'            : (Color.LIGHT4,                Background.COLOR),
    'column_title'     : (Color.LIGHT4,                Background.COLOR),
    'time'             : (Color.BRIGHT_BLUE,           Background.COLOR),
    'bar'              : (Color.LIGHT4,                Color.GRAY_245),
    'msg_emoji'        : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'reaction'         : (Color.NEUTRAL_PURPLE,        Background.COLOR),
    'reaction_mine'    : (Color.LIGHT1,                Color.NEUTRAL_PURPLE),
    'msg_heading'      : (Color.LIGHT1,                Color.BRIGHT_GREEN),
    'msg_math'         : (Color.LIGHT1,                Color.GRAY_245),
    'msg_mention'      : (Color.BRIGHT_RED,            Background.COLOR),
    'msg_link'         : (Color.BRIGHT_BLUE,           Background.COLOR),
    'msg_link_index'   : (Color.BRIGHT_BLUE,           Background.COLOR),
    'msg_quote'        : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'msg_bold'         : (Color.LIGHT4,                Background.COLOR),
    'msg_time'         : (Color.LIGHT1,                Color.LIGHT4),
    'footer'           : (Color.LIGHT1,                Color.LIGHT4),
    'footer_contrast'  : (Color.LIGHT4,                Background.COLOR),
    'starred'          : (Color.BRIGHT_RED,            Background.COLOR),
    'unread_count'     : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'starred_count'    : (Color.LIGHT4,                Background.COLOR),
    'table_head'       : (Color.LIGHT4,                Background.COLOR),
    'filter_results'   : (Color.LIGHT1,                Color.BRIGHT_GREEN),
    'edit_topic'       : (Color.LIGHT1,                Color.GRAY_245),
    'edit_tag'         : (Color.LIGHT1,                Color.GRAY_245),
    'edit_author'      : (Color.NEUTRAL_YELLOW,        Background.COLOR),
    'edit_time'        : (Color.BRIGHT_BLUE,           Background.COLOR),
    'current_user'     : (Color.LIGHT4,                Background.COLOR),
    'muted'            : (Color.BRIGHT_BLUE,           Background.COLOR),
    'popup_border'     : (Color.LIGHT4,                Background.COLOR),
    'popup_category'   : (Color.BRIGHT_BLUE,           Background.COLOR),
    'popup_contrast'   : (Color.LIGHT1,                Color.GRAY_245),
    'popup_important'  : (Color.BRIGHT_RED,            Background.COLOR),
    'widget_disabled'  : (Color.GRAY_245,              Background.COLOR),
    'area:help'        : (Color.LIGHT1,                Color.BRIGHT_GREEN),
    'area:msg'         : (Color.LIGHT1,                Color.NEUTRAL_PURPLE),
    'area:stream'      : (Color.LIGHT1,                Color.BRIGHT_BLUE),
    'area:error'       : (Color.LIGHT1,                Color.BRIGHT_RED),
    'area:user'        : (Color.LIGHT1,                Color.BRIGHT_YELLOW),
    'search_error'     : (Color.BRIGHT_RED,            Background.COLOR),
    'task:success'     : (Color.LIGHT1,                Color.BRIGHT_GREEN),
    'task:error'       : (Color.LIGHT1,                Color.BRIGHT_RED),
    'task:warning'     : (Color.LIGHT1,                Color.NEUTRAL_PURPLE),
    'ui_code'          : (Color.LIGHT1,                Color.LIGHT4),
}

META = {
    'background': Color.LIGHT1,
    'pygments': {
        'styles'    : SolarizedLightStyle().styles,
        'background': 'h223',
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
