"""
SOLARIZED DARK
--------------


"""

from pygments.styles.solarized import SolarizedDarkStyle

from zulipterminal.themes.colors_solarized import SolarizedColor as Color

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR),
    'selected'         : (Color.DARK_BG_REGULAR,   Color.CYAN), # neiljp # inverted + COLOR
    'msg_selected'     : (Color.DARK_BG_REGULAR,   Color.CYAN), # neiljp # inverted + COLOR
    'header'           : (Color.CYAN,              Color.BLUE),
    'general_narrow'   : (Color.DARK_BG_REGULAR,   Color.BLUE), # neiljp # update fg for contrast
    'general_bar'      : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR),
    'msg_sender'       : (Color.RED,               Color.DARK_BG_REGULAR), # neiljp # update name
    'unread'           : (Color.VIOLET,            Color.DARK_BG_REGULAR),
    'user_active'      : (Color.GREEN,             Color.DARK_BG_REGULAR),
    'user_idle'        : (Color.YELLOW,            Color.DARK_BG_REGULAR),
    'user_offline'     : (Color.DARK_FG_SECONDARY, Color.DARK_BG_REGULAR),
    'user_inactive'    : (Color.DARK_FG_SECONDARY, Color.DARK_BG_REGULAR),
    'title'            : (Color.BASE0,             Color.DARK_BG_REGULAR),
    'column_title'     : (Color.BASE0,             Color.DARK_BG_REGULAR),
    'time'             : (Color.DARK_FG_SECONDARY, Color.DARK_BG_REGULAR),
    'bar'              : (Color.DARK_FG_PRIMARY,   Color.DARK_FG_PRIMARY), # neiljp # BASE00 -> FG_PRIM?
    'msg_emoji'        : (Color.VIOLET,            Color.DARK_BG_REGULAR),
    'reaction'         : (Color.VIOLET,            Color.DARK_BG_REGULAR),
    'reaction_mine'    : (Color.DARK_BG_REGULAR,   Color.VIOLET),
    'msg_heading'      : (Color.DARK_BG_REGULAR,   Color.DARK_FG_SECONDARY),
    'msg_math'         : (Color.DARK_BG_HIGHLIGHT, Color.DARK_FG_PRIMARY), # neiljp # BASE00 -> FG_PRIM?
    'msg_mention'      : (Color.ORANGE,            Color.DARK_BG_REGULAR),
    'msg_link'         : (Color.BLUE,              Color.DARK_BG_REGULAR),
    'msg_link_index'   : (Color.BLUE,              Color.DARK_BG_REGULAR),
    'msg_quote'        : (Color.DARK_FG_EMPHASIZE, Color.DARK_BG_REGULAR),
    'msg_code'         : (Color.DARK_BG_REGULAR,   Color.DARK_FG_PRIMARY),
    'msg_bold'         : (Color.BASE0,             Color.DARK_BG_REGULAR),
    'msg_time'         : (Color.DARK_BG_REGULAR,   Color.DARK_FG_EMPHASIZE),
    'footer'           : (Color.DARK_BG_REGULAR,   Color.BASE2),
    'footer_contrast'  : (Color.BASE2,             Color.DARK_BG_REGULAR),
    'starred'          : (Color.ORANGE,            Color.DARK_BG_REGULAR),
    'unread_count'     : (Color.DARK_FG_EMPHASIZE, Color.DARK_BG_REGULAR),
    'starred_count'    : (Color.BASE2,             Color.DARK_BG_REGULAR),
    'table_head'       : (Color.BASE0,             Color.DARK_BG_REGULAR),
    'filter_results'   : (Color.DARK_BG_REGULAR,   Color.DARK_FG_SECONDARY),
    'edit_topic'       : (Color.DARK_BG_REGULAR,   Color.DARK_FG_PRIMARY), # neiljp # BASE00 -> FG_PRIM?
    'edit_tag'         : (Color.DARK_BG_REGULAR,   Color.DARK_FG_PRIMARY), # neiljp # BASE00 -> FG_PRIM?
    'edit_author'      : (Color.DARK_FG_EMPHASIZE, Color.DARK_BG_REGULAR),
    'edit_time'        : (Color.DARK_FG_SECONDARY, Color.DARK_BG_REGULAR),
    'current_user'     : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR),
    'muted'            : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR), # neiljp # BASE00 -> FG_PRIM?
    'popup_border'     : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR),
    'popup_category'   : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR),
    'popup_contrast'   : (Color.DARK_BG_REGULAR,   Color.DARK_FG_PRIMARY), # neiljp # BASE00 -> FG_PRIM?
    'popup_important'  : (Color.ORANGE,            Color.DARK_BG_REGULAR),
    'widget_disabled'  : (Color.DARK_FG_PRIMARY,   Color.DARK_BG_REGULAR), # neiljp # BASE00 -> FG_PRIM?
    'area:help'        : (Color.DARK_BG_REGULAR,   Color.DARK_FG_SECONDARY),
    'area:msg'         : (Color.DARK_BG_REGULAR,   Color.ORANGE),
    'area:stream'      : (Color.DARK_BG_REGULAR,   Color.BASE0),
    'area:error'       : (Color.DARK_FG_PRIMARY,   Color.RED),
    'area:user'        : (Color.DARK_FG_PRIMARY,   Color.BLUE),
    'search_error'     : (Color.ORANGE,            Color.DARK_BG_REGULAR),
    'task:success'     : (Color.DARK_BG_REGULAR,   Color.DARK_FG_SECONDARY),
    'task:error'       : (Color.DARK_FG_PRIMARY,   Color.RED),
    'task:warning'     : (Color.DARK_BG_REGULAR,   Color.ORANGE),
}

META = {
    'pygments': {
        'styles'    : SolarizedDarkStyle().styles,
        'background': 'h234',
        'overrides' : {
            'c'   : '#586e75, italics',    # DARK_FG_SECONDARY
            'cp'  : '#d33682',             # MAGENTA
            'cpf' : '#586e75',             # DARK_FG_SECONDARY
            'ge'  : '#839496, italics',    # BASE0
            'gh'  : '#839496, bold',       # BASE0
            'gu'  : '#839496, underline',  # BASE0
            'gp'  : '#268bd2, bold',       # BLUE
            'gs'  : '#839496, bold',       # BASE0
            'err' : '#dc322f',             # RED
            'n'   : '#bdae93',             # gruvbox: light4
            'p'   : '#bdae93',             # gruvbox: light4
            'w'   : '#bdae93',             # gruvbox: light4
        }
    }
}
