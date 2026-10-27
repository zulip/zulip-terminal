"""
ZT LIGHT
--------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide.
"""

from pygments.styles.perldoc import PerldocStyle

from zulipterminal.config.color import Background
from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.BLACK,               Background.COLOR),
    'selected'        : (Color.BLACK,               Color.LIGHT_GREEN),
    'msg_selected'    : (Color.BLACK,               Color.LIGHT_GREEN),
    'header'          : (Color.WHITE,               Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.DARK_BLUE,           Background.COLOR),
    'msg_sender'      : (Color.DARK_GREEN,          Background.COLOR),
    'unread'          : (Color.DARK_GRAY,           Color.LIGHT_GRAY),
    'user_active'     : (Color.DARK_GREEN,          Background.COLOR),
    'user_idle'       : (Color.DARK_BLUE,           Background.COLOR),
    'user_offline'    : (Color.BLACK,               Background.COLOR),
    'user_inactive'   : (Color.BLACK,               Background.COLOR),
    'user_bot'        : (Color.BLACK,               Background.COLOR),
    'title'           : (Color.WHITE__BOLD,         Color.DARK_GRAY),
    'column_title'    : (Color.BLACK__BOLD,         Background.COLOR),
    'time'            : (Color.DARK_BLUE,           Background.COLOR),
    'bar'             : (Color.WHITE,               Color.DARK_GRAY),
    'msg_emoji'       : (Color.LIGHT_MAGENTA,       Background.COLOR),
    'reaction'        : (Color.LIGHT_MAGENTA__BOLD, Background.COLOR),
    'reaction_mine'   : (Color.WHITE,               Color.LIGHT_MAGENTA),
    'msg_heading'     : (Color.WHITE__BOLD,         Color.DARK_RED),
    'msg_math'        : (Color.DARK_GRAY,           Color.LIGHT_GRAY),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'msg_link'        : (Color.DARK_BLUE,           Background.COLOR),
    'msg_link_index'  : (Color.DARK_BLUE__BOLD,     Background.COLOR),
    'msg_quote'       : (Color.BLACK,               Color.BROWN),
    'msg_bold'        : (Color.WHITE__BOLD,         Color.DARK_GRAY),
    'msg_time'        : (Color.WHITE,               Color.DARK_GRAY),
    'footer'          : (Color.WHITE,               Color.DARK_GRAY),
    'footer_contrast' : (Color.BLACK,               Background.COLOR),
    'starred'         : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'unread_count'    : (Color.DARK_BLUE__BOLD,     Background.COLOR),
    'starred_count'   : (Color.BLACK,               Background.COLOR),
    'table_head'      : (Color.BLACK__BOLD,         Background.COLOR),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_GRAY),
    'edit_tag'        : (Color.WHITE,               Color.DARK_GRAY),
    'edit_author'     : (Color.DARK_GREEN,          Background.COLOR),
    'edit_time'       : (Color.DARK_BLUE,           Background.COLOR),
    'current_user'    : (Color.DARK_GRAY,           Background.COLOR),
    'muted'           : (Color.DARK_GRAY,           Background.COLOR),
    'popup_border'    : (Color.BLACK,               Background.COLOR),
    'popup_category'  : (Color.DARK_GRAY__BOLD,     Color.LIGHT_GRAY),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_GRAY),
    'popup_important' : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'widget_disabled' : (Color.LIGHT_GRAY,          Background.COLOR),
    'area:help'       : (Color.BLACK,               Color.LIGHT_GREEN),
    'area:stream'     : (Color.BLACK,               Color.LIGHT_BLUE),
    'area:msg'        : (Color.BLACK,               Color.YELLOW),
    'area:error'      : (Color.BLACK,               Color.LIGHT_RED),
    'area:user'       : (Color.WHITE,               Color.DARK_BLUE),
    'search_error'    : (Color.LIGHT_RED,           Background.COLOR),
    'task:success'    : (Color.BLACK,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.BLACK,               Color.YELLOW),
    'ui_code'         : (Color.BLACK,               Color.LIGHT_GRAY),
}

META = {
    'background': Color.WHITE,
    'pygments': {
        'styles'    : PerldocStyle().styles,
        'background': PerldocStyle().background_color,
        'overrides' : {
            'cs'  : '#8B008B, bold',
            'sh'  : '#1c7e71, italics',
            'k'   : '#8B008B, bold',
            'nc'  : '#008b45, bold',
            'ne'  : '#008b45, bold',
            'nn'  : '#008b45, underline',
            'nt'  : '#8B008B, bold',
            'gh'  : '#000080, bold',
            'gu'  : '#800080, bold',
            'ge'  : 'default, italics',
            'gs'  : 'default, bold',
            'err' : '#a61717',
            'n'   : '#666666',
            'p'   : '#666666',
            'o'   : '#8B008B',
            'w'   : '#666666',  # inline/plain-codeblock
        }
    }
}
# fmt: on
