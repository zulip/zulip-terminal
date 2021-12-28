"""
ZT DARK
-------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide.
"""
from pygments.styles.material import MaterialStyle

from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.WHITE,               Color.BLACK),
    'selected'        : (Color.WHITE,               Color.DARK_BLUE),
    'msg_selected'    : (Color.WHITE,               Color.DARK_BLUE),
    'header'          : (Color.DARK_CYAN,           Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.WHITE,               Color.BLACK),
    'name'            : (Color.YELLOW__BOLD,        Color.BLACK),
    'unread'          : (Color.DARK_BLUE,           Color.BLACK),
    'user_active'     : (Color.LIGHT_GREEN,         Color.BLACK),
    'user_idle'       : (Color.YELLOW,              Color.BLACK),
    'user_offline'    : (Color.WHITE,               Color.BLACK),
    'user_inactive'   : (Color.WHITE,               Color.BLACK),
    'title'           : (Color.WHITE__BOLD,         Color.BLACK),
    'column_title'    : (Color.WHITE__BOLD,         Color.BLACK),
    'time'            : (Color.LIGHT_BLUE,          Color.BLACK),
    'bar'             : (Color.WHITE,               Color.DARK_GRAY),
    'msg_emoji'       : (Color.LIGHT_MAGENTA,       Color.BLACK),
    'reaction'        : (Color.LIGHT_MAGENTA__BOLD, Color.BLACK),
    'reaction_mine'   : (Color.BLACK,               Color.LIGHT_MAGENTA),
    'msg_heading'     : (Color.LIGHT_CYAN__BOLD,    Color.DARK_MAGENTA),
    'msg_math'        : (Color.LIGHT_GRAY,          Color.DARK_GRAY),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Color.BLACK),
    'msg_link'        : (Color.LIGHT_BLUE,          Color.BLACK),
    'msg_link_index'  : (Color.LIGHT_BLUE__BOLD,    Color.BLACK),
    'msg_quote'       : (Color.BROWN,               Color.BLACK),
    'msg_code'        : (Color.BLACK,               Color.WHITE),
    'msg_bold'        : (Color.WHITE__BOLD,         Color.BLACK),
    'msg_time'        : (Color.BLACK,               Color.WHITE),
    'footer'          : (Color.BLACK,               Color.LIGHT_GRAY),
    'footer_contrast' : (Color.WHITE,               Color.BLACK),
    'starred'         : (Color.LIGHT_RED__BOLD,     Color.BLACK),
    'unread_count'    : (Color.YELLOW,              Color.BLACK),
    'starred_count'   : (Color.LIGHT_GRAY,          Color.BLACK),
    'table_head'      : (Color.WHITE__BOLD,         Color.BLACK),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_GRAY),
    'edit_tag'        : (Color.WHITE,               Color.DARK_GRAY),
    'edit_author'     : (Color.YELLOW,              Color.BLACK),
    'edit_time'       : (Color.LIGHT_BLUE,          Color.BLACK),
    'current_user'    : (Color.WHITE,               Color.BLACK),
    'muted'           : (Color.LIGHT_BLUE,          Color.BLACK),
    'popup_border'    : (Color.WHITE,               Color.BLACK),
    'popup_category'  : (Color.LIGHT_BLUE__BOLD,    Color.BLACK),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_GRAY),
    'popup_important' : (Color.LIGHT_RED__BOLD,     Color.BLACK),
    'widget_disabled' : (Color.DARK_GRAY,           Color.BLACK),
    'area:help'       : (Color.WHITE,               Color.DARK_GREEN),
    'area:msg'        : (Color.WHITE,               Color.BROWN),
    'area:stream'     : (Color.WHITE,               Color.DARK_CYAN),
    'area:error'      : (Color.WHITE,               Color.DARK_RED),
    'area:user'       : (Color.WHITE,               Color.DARK_BLUE),
    'search_error'    : (Color.LIGHT_RED,           Color.BLACK),
    'task:success'    : (Color.WHITE,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.WHITE,               Color.BROWN),
}

META = {
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
