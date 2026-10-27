"""
OXOCARBON LIGHT
---------------

The light variant of oxocarbon: a near-white background (#ffffff) with a
dark slate foreground (#37474f) and the carbon accent colors, adjusted for
contrast on a light background (deeper blue/purple, where the dark theme
uses their paler counterparts).

For syntax highlighting, this theme uses the Lovelace pygments style as a
light base (a cohesive, cool-leaning light palette), with a few token
overrides nudged towards the oxocarbon accent colors.

For further details on themefiles look at the theme contribution guide.
"""

from pygments.styles.lovelace import LovelaceStyle

from zulipterminal.config.color import Background
from zulipterminal.themes.colors_oxocarbon import DefaultBoldColor as Color


# fmt: off

STYLES = {
    # style_name       :  foreground                   background
    None               : (Color.SLATE,                 Background.COLOR),
    'selected'         : (Color.WHITE,                  Color.BLUE_DEEP),
    'msg_selected'     : (Color.WHITE,                  Color.BLUE_DEEP),
    'header'           : (Color.WHITE,                  Color.BLUE_DEEP),
    'general_narrow'   : (Color.WHITE,                  Color.BLUE_DEEP),
    'general_bar'      : (Color.SLATE,                  Background.COLOR),
    'msg_sender'       : (Color.PINK__BOLD,             Background.COLOR),
    'unread'           : (Color.PURPLE_DEEP,            Background.COLOR),
    'user_active'      : (Color.GREEN,                  Background.COLOR),
    'user_idle'        : (Color.PINK,                   Background.COLOR),
    'user_offline'     : (Color.BG3,                    Background.COLOR),
    'user_inactive'    : (Color.BG3,                    Background.COLOR),
    'user_bot'         : (Color.BG3,                    Background.COLOR),
    'title'            : (Color.BG__BOLD,               Background.COLOR),
    'column_title'     : (Color.BG__BOLD,               Background.COLOR),
    'time'             : (Color.BLUE_DEEP,              Background.COLOR),
    'bar'              : (Color.SLATE,                  Color.FG_DIM),
    'msg_emoji'        : (Color.PURPLE_DEEP,            Background.COLOR),
    'reaction'         : (Color.PURPLE_DEEP__BOLD,      Background.COLOR),
    'reaction_mine'    : (Color.WHITE,                  Color.PURPLE_DEEP),
    'msg_heading'      : (Color.BG__BOLD,               Color.GREEN),
    'msg_math'         : (Color.SLATE,                  Color.FG_DIM),
    'msg_mention'      : (Color.PINK__BOLD,             Background.COLOR),
    'msg_link'         : (Color.BLUE_DEEP,              Background.COLOR),
    'msg_link_index'   : (Color.BLUE_DEEP__BOLD,        Background.COLOR),
    'msg_quote'        : (Color.BG3,                    Background.COLOR),
    'msg_bold'         : (Color.BG__BOLD,               Background.COLOR),
    'msg_time'         : (Color.WHITE,                  Color.SLATE),
    'footer'           : (Color.WHITE,                  Color.BG3),
    'footer_contrast'  : (Color.SLATE,                  Background.COLOR),
    'starred'          : (Color.PINK__BOLD,             Background.COLOR),
    'unread_count'     : (Color.PINK,                   Background.COLOR),
    'starred_count'    : (Color.GRAY,                   Background.COLOR),
    'table_head'       : (Color.BG__BOLD,               Background.COLOR),
    'filter_results'   : (Color.BG,                     Color.GREEN),
    'edit_topic'       : (Color.SLATE,                  Color.FG_DIM),
    'edit_tag'         : (Color.SLATE,                  Color.FG_DIM),
    'edit_author'      : (Color.PINK,                   Background.COLOR),
    'edit_time'        : (Color.BLUE_DEEP,              Background.COLOR),
    'current_user'     : (Color.SLATE,                  Background.COLOR),
    'muted'            : (Color.BLUE_DEEP,              Background.COLOR),
    'popup_border'     : (Color.SLATE,                  Background.COLOR),
    'popup_category'   : (Color.BLUE_DEEP__BOLD,        Background.COLOR),
    'popup_contrast'   : (Color.SLATE,                  Color.FG_DIM),
    'popup_important'  : (Color.PINK__BOLD,             Background.COLOR),
    'widget_disabled'  : (Color.GRAY,                   Background.COLOR),
    'area:help'        : (Color.BG,                     Color.GREEN),
    'area:msg'         : (Color.WHITE,                  Color.PURPLE_DEEP),
    'area:stream'      : (Color.WHITE,                  Color.BLUE_DEEP),
    'area:error'       : (Color.WHITE,                  Color.PINK),
    'area:user'        : (Color.BG,                     Color.PINK_LIGHT),
    'search_error'     : (Color.PINK,                   Background.COLOR),
    'task:success'     : (Color.BG,                     Color.GREEN),
    'task:error'       : (Color.WHITE,                  Color.PINK),
    'task:warning'     : (Color.WHITE,                  Color.PURPLE_DEEP),
    'ui_code'          : (Color.SLATE,                  Color.FG_DIM),
}

META = {
    'background': Color.WHITE,
    'pygments': {
        'styles'    : LovelaceStyle().styles,
        'background': '#f2f4f8',
        'overrides' : {
            'c'   : '#ee5396, italics',    # comment -> oxocarbon pink
            'cp'  : '#673ab7',             # preproc -> deep purple
            'cpf' : '#90a4ae',             # preproc continuation -> gray
            'ge'  : '#37474f, italics',    # generic emph -> slate
            'gh'  : '#37474f, bold',       # generic heading -> slate
            'gu'  : '#37474f, underline',  # generic subheading -> slate
            'gp'  : '#0f62fe, bold',       # generic prompt -> deep blue
            'gs'  : '#37474f, bold',       # generic strong -> slate
            'err' : '#ee5396',             # error -> pink
            'n'   : '#37474f',             # name -> slate
            'p'   : '#37474f',             # punctuation -> slate
            'w'   : '#90a4ae',             # whitespace -> gray
        }
    }
}
# fmt: on
