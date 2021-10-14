"""
GRUVBOX
-------
This theme uses the official gruvbox color scheme.
For color reference see:
    https://github.com/dracula/vim/blob/d1864ac0734ce51150affa96a35a1e01ade08b79/colors/dracula.vim

For further details on themefiles look at the theme contribution guide
"""
from enum import Enum

from zulipterminal.config.color import color_properties


# fmt: off
class DraculaColor(Enum):
    # color          =  16code          256code   24code
    DEFAULT          = 'default         default   default'
    BG_DARK          = 'dark            h235      #21222C'
    BG_LIGHT         = 'white           h253      #F8F8F2'
    COMMENT          = 'brown           h61       #6C72A4'
    SELECTION        = 'dark_blue       h239      #44475A'
    SUBTLE           = 'blue            h238      #424450'
    CYAN             = 'cyan            h117      #8BE9FD'
    GREEN            = 'green           h84       #50FA7B'
    ORANGE           = 'orange          h215      #FFB86C'
    PINK             = 'pink            h212      #FF79C6'
    PURPLE           = 'magenta         h141      #BD93F9'
    RED              = 'red             h203      #FF5555'
    YELLOW           = 'yellow          h228      #F1FA8C'

Color = color_properties(DraculaColor, 'BOLD')


STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.BG_LIGHT,              Color.BG_DARK),
    'selected'         : (Color.BG_DARK,               Color.BG_LIGHT),
    'msg_selected'     : (Color.BG_DARK,               Color.BG_LIGHT),
    'header'           : (Color.SUBTLE,                Color.CYAN),
    'general_narrow'   : (Color.BG_LIGHT,              Color.CYAN),
    'general_bar'      : (Color.BG_LIGHT,              Color.BG_DARK),
    'name'             : (Color.ORANGE__BOLD,          Color.BG_DARK),
    'unread'           : (Color.PURPLE,                Color.BG_DARK),
    'user_active'      : (Color.GREEN,                 Color.BG_DARK),
    'user_idle'        : (Color.ORANGE,                Color.BG_DARK),
    'user_offline'     : (Color.BG_LIGHT,              Color.BG_DARK),
    'user_inactive'    : (Color.BG_LIGHT,              Color.BG_DARK),
    'title'            : (Color.BG_LIGHT__BOLD,        Color.BG_DARK),
    'column_title'     : (Color.BG_LIGHT__BOLD,        Color.BG_DARK),
    'time'             : (Color.COMMENT,               Color.BG_DARK),
    'bar'              : (Color.BG_LIGHT,              Color.SELECTION),
    'popup_contrast'   : (Color.BG_DARK,               Color.SELECTION),
    'msg_emoji'        : (Color.PURPLE,                Color.BG_DARK),
    'reaction'         : (Color.PURPLE__BOLD,          Color.BG_DARK),
    'reaction_mine'    : (Color.BG_DARK,               Color.PURPLE),
    'msg_mention'      : (Color.RED__BOLD,             Color.BG_DARK),
    'msg_link'         : (Color.COMMENT,               Color.BG_DARK),
    'msg_link_index'   : (Color.COMMENT__BOLD,         Color.BG_DARK),
    'msg_quote'        : (Color.YELLOW,                Color.BG_DARK),
    'msg_code'         : (Color.BG_DARK,               Color.BG_LIGHT),
    'msg_bold'         : (Color.BG_LIGHT__BOLD,        Color.BG_DARK),
    'msg_time'         : (Color.BG_DARK,               Color.BG_LIGHT),
    'footer'           : (Color.BG_DARK,               Color.BG_LIGHT),
    'footer_contrast'  : (Color.BG_LIGHT,              Color.BG_DARK),
    'starred'          : (Color.RED__BOLD,             Color.BG_DARK),
    'popup_category'   : (Color.COMMENT__BOLD,         Color.BG_DARK),
    'unread_count'     : (Color.ORANGE,                Color.BG_DARK),
    'starred_count'    : (Color.BG_LIGHT,              Color.BG_DARK),
    'table_head'       : (Color.BG_LIGHT__BOLD,        Color.BG_DARK),
    'filter_results'   : (Color.BG_DARK,               Color.GREEN),
    'edit_topic'       : (Color.BG_DARK,               Color.SELECTION),
    'edit_tag'         : (Color.BG_DARK,               Color.SELECTION),
    'edit_author'      : (Color.ORANGE,                Color.BG_DARK),
    'edit_time'        : (Color.COMMENT,               Color.BG_DARK),
    'current_user'     : (Color.BG_LIGHT,              Color.BG_DARK),
    'muted'            : (Color.COMMENT,               Color.BG_DARK),
    'popup_border'     : (Color.BG_LIGHT,              Color.BG_DARK),
    'area:help'        : (Color.BG_DARK,               Color.GREEN),
    'area:msg'         : (Color.BG_DARK,               Color.RED),
    'area:stream'      : (Color.BG_DARK,               Color.COMMENT),
    'area:error'       : (Color.BG_LIGHT,              Color.PINK),
    'search_error'     : (Color.RED,                   Color.BG_DARK),
    'task:success'     : (Color.BG_DARK,               Color.GREEN),
    'task:error'       : (Color.BG_LIGHT,              Color.PINK),
    'task:warning'     : (Color.BG_DARK,               Color.RED),
}
# fmt: on
