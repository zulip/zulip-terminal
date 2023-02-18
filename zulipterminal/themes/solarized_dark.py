from pygments.style import Style
from pygments.token import (
    Keyword,
    Name,
    Comment,
    String,
    Error,
    Number,
    Operator,
    Generic,
    Whitespace,
    Punctuation,
    Other,
    Literal,
)

from zulipterminal.themes.colors_solarized import SolarizedDarkColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.BASE1,                  Color.BASE03),
    'selected'         : (Color.BASE03,                 Color.YELLOW),
    'msg_selected'     : (Color.BASE03,                 Color.YELLOW),
    'header'           : (Color.BLUE,                   Color.BASE02),
    'general_narrow'   : (Color.BASE1,                  Color.BASE02),
    'general_bar'      : (Color.BASE03,                 Color.BASE2),
    'msg_sender'       : (Color.ORANGE,                 Color.BASE2),
    'unread'           : (Color.VIOLET,                 Color.BASE2),
    'user_active'      : (Color.GREEN,                  Color.BASE2),
    'user_idle'        : (Color.ORANGE,                 Color.BASE2),
    'user_offline'     : (Color.BASE2,                  Color.BASE2),
    'user_inactive'    : (Color.BASE2,                  Color.BASE2),
    'title'            : (Color.BASE1,                  Color.BASE2),
    'column_title'     : (Color.BASE1,                  Color.BASE2),
    'time'             : (Color.BASE02,                 Color.BASE2),
    'bar'              : (Color.BASE03,                 Color.BASE1),
    'msg_emoji'        : (Color.VIOLET,                 Color.BASE2),
    'reaction'         : (Color.VIOLET,                 Color.BASE2),
    'reaction_mine'    : (Color.BASE2,                  Color.VIOLET),
    'msg_heading'      : (Color.BASE1,                  Color.GREEN),
    'msg_math'         : (Color.BASE1,                  Color.BASE02),
    'msg_mention'      : (Color.RED,                    Color.BASE2),
    'msg_link'         : (Color.BLUE,                   Color.BASE2),
    'msg_link_index'   : (Color.BLUE,                   Color.BASE2),
    'msg_quote'        : (Color.ORANGE,                 Color.BASE2),
    'msg_code'         : (Color.BASE1,                  Color.BASE02),
    'msg_bold'         : (Color.BASE1,                  Color.BASE2),
    'msg_time'         : (Color.BASE1,                  Color.BASE02),
    'footer'           : (Color.BASE1,                  Color.BASE3),
    'footer_contrast'  : (Color.BASE03,                 Color.BASE2),
    'starred'          : (Color.RED,                    Color.BASE2),
    'unread_count'     : (Color.ORANGE,                 Color.BASE2),
    'starred_count'    : (Color.BASE03,                 Color.BASE2),
    'table_head'       : (Color.BASE1,                  Color.BASE2),
    'filter_results'   : (Color.BASE1,                  Color.GREEN),
    'edit_topic'       : (Color.BASE1,                  Color.BASE02),
    'edit_tag'         : (Color.BASE1,                  Color.BASE02),
    'edit_author'      : (Color.ORANGE,                 Color.BASE2),
    'edit_time'        : (Color.BASE02,                 Color.BASE2),
    'current_user'    
}
