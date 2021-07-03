"""
ZT LIGHT
--------
This theme uses the default color scheme.
For further details on themefiles look at the theme contribution guide.
"""
from zulipterminal.config.color import DefaultBoldColor as Color


# fmt: off
STYLES = {
    # style_name      :  foreground                 background
    None              : (Color.BLACK,               Color.WHITE),
    'selected'        : (Color.BLACK,               Color.LIGHT_GREEN),
    'msg_selected'    : (Color.BLACK,               Color.LIGHT_GREEN),
    'header'          : (Color.WHITE,               Color.DARK_BLUE),
    'general_narrow'  : (Color.WHITE,               Color.DARK_BLUE),
    'general_bar'     : (Color.DARK_BLUE,           Color.WHITE),
    'name'            : (Color.DARK_GREEN,          Color.WHITE),
    'unread'          : (Color.DARK_GRAY,           Color.LIGHT_GRAY),
    'user_active'     : (Color.DARK_GREEN,          Color.WHITE),
    'user_idle'       : (Color.DARK_BLUE,           Color.WHITE),
    'user_offline'    : (Color.BLACK,               Color.WHITE),
    'user_inactive'   : (Color.BLACK,               Color.WHITE),
    'title'           : (Color.WHITE__BOLD,         Color.DARK_GRAY),
    'column_title'    : (Color.BLACK__BOLD,         Color.WHITE),
    'time'            : (Color.DARK_BLUE,           Color.WHITE),
    'bar'             : (Color.WHITE,               Color.DARK_GRAY),
    'popup_contrast'  : (Color.WHITE,               Color.DARK_GRAY),
    'msg_emoji'       : (Color.LIGHT_MAGENTA,       Color.WHITE),
    'reaction'        : (Color.LIGHT_MAGENTA__BOLD, Color.WHITE),
    'reaction_mine'   : (Color.WHITE,               Color.LIGHT_MAGENTA),
    'msg_mention'     : (Color.LIGHT_RED__BOLD,     Color.WHITE),
    'msg_link'        : (Color.DARK_BLUE,           Color.WHITE),
    'msg_link_index'  : (Color.DARK_BLUE__BOLD,     Color.WHITE),
    'msg_quote'       : (Color.BLACK,               Color.BROWN),
    'msg_code'        : (Color.BLACK,               Color.LIGHT_GRAY),
    'msg_bold'        : (Color.WHITE__BOLD,         Color.DARK_GRAY),
    'msg_time'        : (Color.WHITE,               Color.DARK_GRAY),
    'footer'          : (Color.WHITE,               Color.DARK_GRAY),
    'footer_contrast' : (Color.BLACK,               Color.WHITE),
    'starred'         : (Color.LIGHT_RED__BOLD,     Color.WHITE),
    'popup_category'  : (Color.DARK_GRAY__BOLD,     Color.LIGHT_GRAY),
    'unread_count'    : (Color.DARK_BLUE__BOLD,     Color.WHITE),
    'starred_count'   : (Color.BLACK,               Color.WHITE),
    'table_head'      : (Color.BLACK__BOLD,         Color.WHITE),
    'filter_results'  : (Color.WHITE,               Color.DARK_GREEN),
    'edit_topic'      : (Color.WHITE,               Color.DARK_GRAY),
    'edit_tag'        : (Color.WHITE,               Color.DARK_GRAY),
    'edit_author'     : (Color.DARK_GREEN,          Color.WHITE),
    'edit_time'       : (Color.DARK_BLUE,           Color.WHITE),
    'current_user'    : (Color.DARK_GRAY,           Color.WHITE),
    'muted'           : (Color.DARK_GRAY,           Color.WHITE),
    'popup_border'    : (Color.BLACK,               Color.WHITE),
    'area:help'       : (Color.BLACK,               Color.LIGHT_GREEN),
    'area:stream'     : (Color.BLACK,               Color.LIGHT_BLUE),
    'area:msg'        : (Color.BLACK,               Color.YELLOW),
    'area:error'      : (Color.BLACK,               Color.LIGHT_RED),
    'search_error'    : (Color.LIGHT_RED,           Color.WHITE),
    'task:success'    : (Color.BLACK,               Color.DARK_GREEN),
    'task:error'      : (Color.WHITE,               Color.DARK_RED),
    'task:warning'    : (Color.BLACK,               Color.YELLOW),
}
# fmt: on
