"""
ZT DARK
-------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide.
"""

from pygments.styles.material import MaterialStyle

from zulipterminal.config.color import Background
from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.WHITE,               Background.COLOR),
    'selected'        : (Color.WHITE,               Color.DARK_BLUE),
    'msg_selected'    : (Color.WHITE,               Color.DARK_BLUE),
    'header'          : (Color.DARK_CYAN,           Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.WHITE,               Background.COLOR),
    'msg_sender'      : (Color.YELLOW__BOLD,        Background.COLOR),
    'unread'          : (Color.DARK_BLUE,           Background.COLOR),
    'user_active'     : (Color.LIGHT_GREEN,         Background.COLOR),
    'user_idle'       : (Color.YELLOW,              Background.COLOR),
    'user_offline'    : (Color.WHITE,               Background.COLOR),
    'user_inactive'   : (Color.WHITE,               Background.COLOR),
    'user_bot'        : (Color.WHITE,               Background.COLOR),
    'title'           : (Color.WHITE__BOLD,         Background.COLOR),
    'column_title'    : (Color.WHITE__BOLD,         Background.COLOR),
    'time'            : (Color.LIGHT_BLUE,          Background.COLOR),
    'bar'             : (Color.WHITE,               Color.DARK_GRAY),
    'msg_emoji'       : (Color.LIGHT_MAGENTA,       Background.COLOR),
    'reaction'        : (Color.LIGHT_MAGENTA__BOLD, Background.COLOR),
    'reaction_mine'   : (Color.BLACK,               Color.LIGHT_MAGENTA),
    'msg_heading'     : (Color.LIGHT_CYAN__BOLD,    Color.DARK_MAGENTA),
    'msg_math'        : (Color.LIGHT_GRAY,          Color.DARK_GRAY),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'msg_link'        : (Color.LIGHT_BLUE,          Background.COLOR),
    'msg_link_index'  : (Color.LIGHT_BLUE__BOLD,    Background.COLOR),
    'msg_quote'       : (Color.BROWN,               Background.COLOR),
    'msg_bold'        : (Color.WHITE__BOLD,         Background.COLOR),
    'msg_time'        : (Color.BLACK,               Color.WHITE),
    'footer'          : (Color.BLACK,               Color.LIGHT_GRAY),
    'footer_contrast' : (Color.WHITE,               Background.COLOR),
    'starred'         : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'unread_count'    : (Color.YELLOW,              Background.COLOR),
    'starred_count'   : (Color.LIGHT_GRAY,          Background.COLOR),
    'table_head'      : (Color.WHITE__BOLD,         Background.COLOR),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_GRAY),
    'edit_tag'        : (Color.WHITE,               Color.DARK_GRAY),
    'edit_author'     : (Color.YELLOW,              Background.COLOR),
    'edit_time'       : (Color.LIGHT_BLUE,          Background.COLOR),
    'current_user'    : (Color.WHITE,               Background.COLOR),
    'muted'           : (Color.LIGHT_BLUE,          Background.COLOR),
    'popup_border'    : (Color.WHITE,               Background.COLOR),
    'popup_category'  : (Color.LIGHT_BLUE__BOLD,    Background.COLOR),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_GRAY),
    'popup_important' : (Color.LIGHT_RED__BOLD,     Background.COLOR),
    'widget_disabled' : (Color.DARK_GRAY,           Background.COLOR),
    'area:help'       : (Color.WHITE,               Color.DARK_GREEN),
    'area:msg'        : (Color.WHITE,               Color.BROWN),
    'area:stream'     : (Color.WHITE,               Color.DARK_CYAN),
    'area:error'      : (Color.WHITE,               Color.DARK_RED),
    'area:user'       : (Color.WHITE,               Color.DARK_BLUE),
    'search_error'    : (Color.LIGHT_RED,           Background.COLOR),
    'task:success'    : (Color.WHITE,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.WHITE,               Color.BROWN),
    'ui_code'         : (Color.BLACK,               Color.WHITE),
}

META = {
    'background': Color.BLACK,
    'pygments': {
        'styles'    : MaterialStyle().styles,
        'background': 'h235',
        'overrides' : {
            'kn' : MaterialStyle().cyan  + ', italics',
            'sd' : MaterialStyle().faded + ', italics',
            'ow' : MaterialStyle().cyan  + ', italics',
            'c'  : MaterialStyle().faded + ', italics',
            'n'  : MaterialStyle().paleblue,
            'no' : MaterialStyle().paleblue,
            'nx' : MaterialStyle().paleblue,
            'w'  : MaterialStyle().paleblue,  # inline/plain-codeblock
        }
    }
}
# fmt: on
