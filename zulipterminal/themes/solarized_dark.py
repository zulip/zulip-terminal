"""
SOLARIZED DARK
--------------


"""

from pygments.styles.solarized import SolarizedDarkStyle

from zulipterminal.themes.colors_solarized import DefaultBoldColor as Color

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.base0,                 Color.base03),
    'selected'         : (Color.base0,                 Color.base02),
    'msg_selected'     : (Color.base0,                 Color.base02),
    'header'           : (Color.cyan,                  Color.blue),
    'general_narrow'   : (Color.base0,                 Color.blue),
    'general_bar'      : (Color.base0,                 Color.base03),
    'name'             : (Color.red__BOLD,             Color.base03),
    'unread'           : (Color.violet,                Color.base03),
    'user_active'      : (Color.green,                 Color.base03),
    'user_idle'        : (Color.yellow,                Color.base03),
    'user_offline'     : (Color.base01,                Color.base03),
    'user_inactive'    : (Color.base01,                Color.base03),
    'title'            : (Color.base0__BOLD,           Color.base03),
    'column_title'     : (Color.base0__BOLD,           Color.base03),
    'time'             : (Color.base01,                Color.base03),
    'bar'              : (Color.base0,                 Color.base00),
    'msg_emoji'        : (Color.violet,                Color.base03),
    'reaction'         : (Color.violet__BOLD,          Color.base03),
    'reaction_mine'    : (Color.base03,                Color.violet),
    'msg_heading'      : (Color.base03__BOLD,          Color.base01),
    'msg_math'         : (Color.base02,                Color.base00),
    'msg_mention'      : (Color.orange__BOLD,          Color.base03),
    'msg_link'         : (Color.blue,                  Color.base03),
    'msg_link_index'   : (Color.blue__BOLD,            Color.base03),
    'msg_quote'        : (Color.base1,                 Color.base03),
    'msg_code'         : (Color.base03,                Color.base0),
    'msg_bold'         : (Color.base0__BOLD,           Color.base03),
    'msg_time'         : (Color.base03,                Color.base1),
    'footer'           : (Color.base03,                Color.base2),
    'footer_contrast'  : (Color.base2,                 Color.base03),
    'starred'          : (Color.orange__BOLD,          Color.base03),
    'unread_count'     : (Color.base1,                 Color.base03),
    'starred_count'    : (Color.base2,                 Color.base03),
    'table_head'       : (Color.base0__BOLD,           Color.base03),
    'filter_results'   : (Color.base03,                Color.base01),
    'edit_topic'       : (Color.base03,                Color.base00),
    'edit_tag'         : (Color.base03,                Color.base00),
    'edit_author'      : (Color.base1,                 Color.base03),
    'edit_time'        : (Color.base01,                Color.base03),
    'current_user'     : (Color.base0,                 Color.base03),
    'muted'            : (Color.base00,                Color.base03),
    'popup_border'     : (Color.base0,                 Color.base03),
    'popup_category'   : (Color.base0__BOLD,           Color.base03),
    'popup_contrast'   : (Color.base03,                Color.base00),
    'popup_important'  : (Color.orange__BOLD,          Color.base03),
    'widget_disabled'  : (Color.base00,                Color.base03),
    'area:help'        : (Color.base03,                Color.base01),
    'area:msg'         : (Color.base03,                Color.orange),
    'area:stream'      : (Color.base03,                Color.base0),
    'area:error'       : (Color.base0,                 Color.red),
    'area:user'        : (Color.base0,                 Color.blue),
    'search_error'     : (Color.orange,                Color.base03),
    'task:success'     : (Color.base03,                Color.base01),
    'task:error'       : (Color.base0,                 Color.red),
    'task:warning'     : (Color.base03,                Color.orange),   
}

META = {
    'pygments': {
        'styles'    : SolarizedDarkStyle().styles,
        'background': 'h234',
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