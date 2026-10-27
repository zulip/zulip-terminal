"""
OXOCARBON DARK
--------------

For syntax highlighting, this theme uses the Material pygments style as a
base (closest stock match to oxocarbon's cool blue/cyan-leaning palette),
with a few token overrides nudged towards the oxocarbon accent colors.

For further details on themefiles look at the theme contribution guide
"""

from pygments.styles.material import MaterialStyle

from zulipterminal.config.color import Background
from zulipterminal.themes.colors_oxocarbon import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.FG_DIM,                Background.COLOR),
    'selected'         : (Color.BG,                    Color.BLUE_LIGHT),
    'msg_selected'     : (Color.BG,                    Color.BLUE_LIGHT),
    'header'           : (Color.BG,                    Color.BLUE_LIGHT),
    'general_narrow'   : (Color.BG,                    Color.BLUE_LIGHT),
    'general_bar'      : (Color.FG_DIM,                Background.COLOR),
    'msg_sender'       : (Color.PINK_LIGHT__BOLD,       Background.COLOR),
    'unread'           : (Color.PURPLE,                 Background.COLOR),
    'user_active'      : (Color.GREEN,                  Background.COLOR),
    'user_idle'        : (Color.PINK_LIGHT,              Background.COLOR),
    'user_offline'     : (Color.BG3,                     Background.COLOR),
    'user_inactive'    : (Color.BG3,                     Background.COLOR),
    'user_bot'         : (Color.BG3,                     Background.COLOR),
    'title'            : (Color.FG__BOLD,                Background.COLOR),
    'column_title'     : (Color.FG__BOLD,                Background.COLOR),
    'time'             : (Color.BLUE_LIGHT,               Background.COLOR),
    'bar'              : (Color.FG_DIM,                  Color.BG2),
    'msg_emoji'        : (Color.PURPLE,                  Background.COLOR),
    'reaction'         : (Color.PURPLE__BOLD,            Background.COLOR),
    'reaction_mine'    : (Color.BG,                      Color.PURPLE),
    'msg_heading'      : (Color.BG__BOLD,                Color.GREEN),
    'msg_math'         : (Color.BG,                      Color.BG2),
    'msg_mention'      : (Color.PINK__BOLD,              Background.COLOR),
    'msg_link'         : (Color.BLUE_LIGHT,              Background.COLOR),
    'msg_link_index'   : (Color.BLUE_LIGHT__BOLD,        Background.COLOR),
    'msg_quote'        : (Color.BG3,                     Background.COLOR),
    'msg_bold'         : (Color.FG__BOLD,                Background.COLOR),
    'msg_time'         : (Color.BG,                      Color.FG_DIM),
    'footer'           : (Color.BG,                      Color.FG_DIM),
    'footer_contrast'  : (Color.FG_DIM,                  Background.COLOR),
    'starred'          : (Color.PINK__BOLD,              Background.COLOR),
    'unread_count'     : (Color.PINK_LIGHT,              Background.COLOR),
    'starred_count'    : (Color.FG_DIM,                  Background.COLOR),
    'table_head'       : (Color.FG__BOLD,                Background.COLOR),
    'filter_results'   : (Color.BG,                      Color.GREEN),
    'edit_topic'       : (Color.BG,                      Color.BG2),
    'edit_tag'         : (Color.BG,                      Color.BG2),
    'edit_author'      : (Color.PINK_LIGHT,              Background.COLOR),
    'edit_time'        : (Color.BLUE_LIGHT,              Background.COLOR),
    'current_user'     : (Color.FG_DIM,                  Background.COLOR),
    'muted'            : (Color.BLUE_LIGHT,              Background.COLOR),
    'popup_border'     : (Color.FG_DIM,                  Background.COLOR),
    'popup_category'   : (Color.BLUE_LIGHT__BOLD,        Background.COLOR),
    'popup_contrast'   : (Color.BG,                      Color.BG2),
    'popup_important'  : (Color.PINK__BOLD,              Background.COLOR),
    'widget_disabled'  : (Color.BG3,                     Background.COLOR),
    'area:help'        : (Color.BG,                      Color.GREEN),
    'area:msg'         : (Color.BG,                      Color.PURPLE),
    'area:stream'      : (Color.BG,                      Color.BLUE_LIGHT),
    'area:error'       : (Color.BG,                      Color.PINK),
    'area:user'        : (Color.BG,                      Color.PINK_LIGHT),
    'search_error'     : (Color.PINK,                    Background.COLOR),
    'task:success'     : (Color.BG,                      Color.GREEN),
    'task:error'       : (Color.BG,                      Color.PINK),
    'task:warning'     : (Color.BG,                      Color.PURPLE),
    'ui_code'          : (Color.BG,                      Color.FG_DIM),
}

META = {
    'background': Color.BG,
    'pygments': {
        'styles'    : MaterialStyle().styles,
        'background': 'h234',
        'overrides' : {
            'c'   : '#ff7eb6, italics',    # comment -> oxocarbon pink_light
            'cp'  : '#be95ff',             # preproc -> purple
            'cpf' : '#525252',             # preproc continuation -> bg3
            'ge'  : '#dde1e6, italics',    # generic emph -> fg_dim
            'gh'  : '#dde1e6, bold',       # generic heading -> fg_dim
            'gu'  : '#dde1e6, underline',  # generic subheading -> fg_dim
            'gp'  : '#33b1ff, bold',       # generic prompt -> blue_light
            'gs'  : '#dde1e6, bold',       # generic strong -> fg_dim
            'err' : '#ee5396',             # error -> pink
            'n'   : '#dde1e6',             # name -> fg_dim
            'p'   : '#dde1e6',             # punctuation -> fg_dim
            'w'   : '#dde1e6',             # whitespace -> fg_dim
        }
    }
}
# fmt: on
