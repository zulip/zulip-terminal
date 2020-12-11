"""
ZT BLUE
-------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide
"""
from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.BLACK,               Color.LIGHT_BLUE),
    'selected'        : (Color.BLACK,               Color.LIGHT_GRAY),
    'msg_selected'    : (Color.BLACK,               Color.LIGHT_GRAY),
    'header'          : (Color.BLACK,               Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.DARK_BLUE,           Color.LIGHT_BLUE),
    'name'            : (Color.DARK_RED,            Color.LIGHT_BLUE),
    'unread'          : (Color.LIGHT_GRAY,          Color.LIGHT_BLUE),
    'user_active'     : (Color.LIGHT_GREEN__BOLD,   Color.LIGHT_BLUE),
    'user_idle'       : (Color.DARK_GRAY,           Color.LIGHT_BLUE),
    'user_offline'    : (Color.BLACK,               Color.LIGHT_BLUE),
    'user_inactive'   : (Color.BLACK,               Color.LIGHT_BLUE),
    'title'           : (Color.WHITE__BOLD,         Color.DARK_BLUE),
    'column_title'    : (Color.BLACK__BOLD,         Color.LIGHT_BLUE),
    'time'            : (Color.DARK_BLUE,           Color.LIGHT_BLUE),
    'bar'             : (Color.WHITE,               Color.DARK_BLUE),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_BLUE),
    'msg_emoji'       : (Color.DARK_MAGENTA,        Color.LIGHT_BLUE),
    'reaction'        : (Color.DARK_MAGENTA__BOLD,  Color.LIGHT_BLUE),
    'reaction_mine'   : (Color.LIGHT_BLUE,          Color.DARK_MAGENTA),
    'msg_math'        : (Color.LIGHT_GRAY,          Color.DARK_GRAY),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Color.LIGHT_BLUE),
    'msg_link'        : (Color.DARK_BLUE,           Color.LIGHT_GRAY),
    'msg_link_index'  : (Color.DARK_BLUE__BOLD,     Color.LIGHT_GRAY),
    'msg_quote'       : (Color.BROWN,               Color.DARK_BLUE),
    'msg_code'        : (Color.DARK_BLUE,           Color.WHITE),
    'msg_bold'        : (Color.WHITE__BOLD,         Color.DARK_BLUE),
    'msg_time'        : (Color.DARK_BLUE,           Color.WHITE),
    'footer'          : (Color.WHITE,               Color.DARK_GRAY),
    'footer_contrast' : (Color.BLACK,               Color.WHITE),
    'starred'         : (Color.LIGHT_RED__BOLD,     Color.LIGHT_BLUE),
    'popup_category'  : (Color.LIGHT_GRAY__BOLD,    Color.LIGHT_BLUE),
    'unread_count'    : (Color.YELLOW,              Color.LIGHT_BLUE),
    'starred_count'   : (Color.BLACK,               Color.LIGHT_BLUE),
    'table_head'      : (Color.BLACK__BOLD,         Color.LIGHT_BLUE),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_BLUE),
    'edit_tag'        : (Color.WHITE,               Color.DARK_BLUE),
    'edit_author'     : (Color.DARK_GRAY,           Color.LIGHT_BLUE),
    'edit_time'       : (Color.DARK_BLUE,           Color.LIGHT_BLUE),
    'current_user'    : (Color.LIGHT_GRAY,          Color.LIGHT_BLUE),
    'muted'           : (Color.LIGHT_GRAY,          Color.LIGHT_BLUE),
    'popup_border'    : (Color.WHITE,               Color.LIGHT_BLUE),
    'area:help'       : (Color.WHITE,               Color.DARK_GREEN),
    'area:stream'     : (Color.WHITE,               Color.DARK_CYAN),
    'area:msg'        : (Color.WHITE,               Color.BROWN),
    'area:error'      : (Color.WHITE,               Color.DARK_RED),
    'area:user'       : (Color.WHITE,               Color.DARK_BLUE),
    'search_error'    : (Color.LIGHT_RED,           Color.LIGHT_BLUE),
    'task:success'    : (Color.WHITE,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.WHITE,               Color.BROWN),
}
# fmt: on
