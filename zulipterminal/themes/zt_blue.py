"""
ZT BLUE
-------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide
"""

from pygments.styles.zenburn import ZenburnStyle

from zulipterminal.config.color import Background
from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.BLACK,               Background.COLOR),
    'selected'        : (Color.BLACK,               Color.LIGHT_GRAY),
    'msg_selected'    : (Color.BLACK,               Color.LIGHT_GRAY),
    'header'          : (Color.BLACK,               Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.DARK_BLUE,           Background.COLOR),
    'msg_sender'      : (Color.DARK_RED,            Background.COLOR),
    'unread'          : (Color.LIGHT_GRAY,          Background.COLOR),
    'user_active'     : (Color.LIGHT_GREEN__BOLD,   Background.COLOR),
    'user_idle'       : (Color.DARK_GRAY,           Background.COLOR),
    'user_offline'    : (Color.BLACK,               Background.COLOR),
    'user_inactive'   : (Color.BLACK,               Background.COLOR),
    'user_bot'        : (Color.BLACK,               Background.COLOR),
    'title'           : (Color.WHITE__BOLD,         Color.DARK_BLUE),
    'column_title'    : (Color.BLACK__BOLD,         Background.COLOR),
    'time'            : (Color.DARK_BLUE,           Background.COLOR),
    'bar'             : (Color.WHITE,               Color.DARK_BLUE),
    'msg_emoji'       : (Color.DARK_MAGENTA,        Background.COLOR),
    'reaction'        : (Color.DARK_MAGENTA__BOLD,  Background.COLOR),
    'reaction_mine'   : (Color.LIGHT_BLUE,          Color.DARK_MAGENTA),
    'msg_heading'     : (Color.WHITE__BOLD,         Color.BLACK),
    'msg_math'        : (Color.LIGHT_GRAY,          Color.DARK_GRAY),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'msg_link'        : (Color.DARK_BLUE,           Color.LIGHT_GRAY),
    'msg_link_index'  : (Color.DARK_BLUE__BOLD,     Color.LIGHT_GRAY),
    'msg_quote'       : (Color.BROWN,               Color.DARK_BLUE),
    'msg_bold'        : (Color.WHITE__BOLD,         Color.DARK_BLUE),
    'msg_time'        : (Color.DARK_BLUE,           Color.WHITE),
    'footer'          : (Color.WHITE,               Color.DARK_GRAY),
    'footer_contrast' : (Color.BLACK,               Color.WHITE),
    'starred'         : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'unread_count'    : (Color.YELLOW,              Background.COLOR),
    'starred_count'   : (Color.BLACK,               Background.COLOR),
    'table_head'      : (Color.BLACK__BOLD,         Background.COLOR),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_BLUE),
    'edit_tag'        : (Color.WHITE,               Color.DARK_BLUE),
    'edit_author'     : (Color.DARK_GRAY,           Background.COLOR),
    'edit_time'       : (Color.DARK_BLUE,           Background.COLOR),
    'current_user'    : (Color.LIGHT_GRAY,          Background.COLOR),
    'muted'           : (Color.LIGHT_GRAY,          Background.COLOR),
    'popup_border'    : (Color.WHITE,               Background.COLOR),
    'popup_category'  : (Color.LIGHT_GRAY__BOLD,    Background.COLOR),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_BLUE),
    'popup_important' : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'widget_disabled' : (Color.DARK_GRAY,           Background.COLOR),
    'area:help'       : (Color.WHITE,               Color.DARK_GREEN),
    'area:stream'     : (Color.WHITE,               Color.DARK_CYAN),
    'area:msg'        : (Color.WHITE,               Color.BROWN),
    'area:error'      : (Color.WHITE,               Color.DARK_RED),
    'area:user'       : (Color.WHITE,               Color.DARK_BLUE),
    'search_error'    : (Color.LIGHT_RED,           Background.COLOR),
    'task:success'    : (Color.WHITE,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.WHITE,               Color.BROWN),
    'ui_code'         : (Color.DARK_BLUE,           Color.WHITE),
}

META = {
    'background': Color.LIGHT_BLUE,
    'pygments': {
        'styles'    : ZenburnStyle().styles,
        'background': 'h25',
        'overrides' : {
            'err' : '#e37170, bold',
            'kt'  : '#dfdfbf, bold',
            'nt'  : '#e89393, bold',
            'ne'  : '#c3bf9f, bold',
            'si'  : '#dca3a3, bold',
            'c'   : '#7f9f7f, italics',
            'cp'  : '#dfaf8f, bold',
            'cs'  : '#dfdfdf, bold',
            'g'   : '#ecbcbc, bold',
            'ge'  : '#ffffff, bold',
            'go'  : '#5b605e, bold',
            'gh'  : '#efefef, bold',
            'gd'  : '#c3bf9f',
            'gi'  : '#709080, bold',
            'gt'  : '#80d4aa, bold',
            'gu'  : '#efefef, bold',
            'w'   : '#dcdccc',  # inline/plain-codeblock
        }
    }
}
# fmt: on
