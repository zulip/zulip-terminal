from typing import Any, Dict, List, Optional, Tuple, Union

from zulipterminal.themes import gruvbox, zt_blue, zt_dark, zt_light


StyleSpec = Union[
    Tuple[Optional[str], str, str],
    Tuple[Optional[str], str, str, Optional[str]],
    Tuple[Optional[str], str, str, Optional[str], str, str],
]
ThemeSpec = List[StyleSpec]

# fmt: off
# The keys in REQUIRED_STYLES specify what styles are necessary for a theme to
# be complete, while the values are those used to style each element in
# monochrome (1-bit) mode - independently of the specified theme
REQUIRED_STYLES = {
    # style name      : monochrome style
    None              : '',
    'selected'        : 'standout',
    'msg_selected'    : 'standout',
    'header'          : 'bold',
    'general_narrow'  : 'standout',
    'general_bar'     : '',
    'name'            : '',
    'unread'          : 'strikethrough',
    'user_active'     : 'bold',
    'user_idle'       : '',
    'user_offline'    : '',
    'user_inactive'   : '',
    'title'           : 'bold',
    'column_title'    : 'bold',
    'time'            : '',
    'bar'             : 'standout',
    'popup_contrast'  : 'standout',
    'msg_emoji'       : 'bold',
    'reaction'        : 'bold',
    'reaction_mine'   : 'standout',
    'msg_mention'     : 'bold',
    'msg_link'        : '',
    'msg_link_index'  : 'bold',
    'msg_quote'       : 'underline',
    'msg_code'        : 'bold',
    'msg_bold'        : 'bold',
    'msg_time'        : 'bold',
    'footer'          : 'standout',
    'footer_contrast' : 'standout',
    'starred'         : 'bold',
    'popup_category'  : 'bold',
    'unread_count'    : 'bold',
    'starred_count'   : '',
    'table_head'      : 'bold',
    'filter_results'  : 'bold',
    'edit_topic'      : 'standout',
    'edit_tag'        : 'standout',
    'edit_author'     : 'bold',
    'edit_time'       : 'bold',
    'current_user'    : '',
    'muted'           : 'bold',
    'popup_border'    : 'bold',
    'area:help'       : 'standout',
    'area:msg'        : 'standout',
    'area:stream'     : 'standout',
    'area:error'      : 'standout',
    'search_error'    : 'standout',
    'task:success'    : 'standout',
    'task:error'      : 'standout',
    'task:warning'    : 'standout',
}
# fmt: on

THEMES = {
    "gruvbox_dark": gruvbox,
    "zt_dark": zt_dark,
    "zt_light": zt_light,
    "zt_blue": zt_blue,
}

THEME_ALIASES = {
    "default": "zt_dark",
    "gruvbox": "gruvbox_dark",
    "light": "zt_light",
    "blue": "zt_blue",
}


def all_themes() -> List[str]:
    return list(THEMES.keys())


def aliased_themes() -> Dict[str, str]:
    return dict(THEME_ALIASES)


def complete_and_incomplete_themes() -> Tuple[List[str], List[str]]:
    complete = {
        name
        for name, theme in THEMES.items()
        if set(theme.STYLES) == set(REQUIRED_STYLES)
    }
    incomplete = list(set(THEMES) - complete)
    return sorted(list(complete)), sorted(incomplete)


def generate_theme(theme_name: str, color_depth: int) -> ThemeSpec:
    theme_styles = THEMES[theme_name].STYLES
    urwid_theme = parse_themefile(theme_styles, color_depth)
    return urwid_theme


def parse_themefile(
    theme_styles: Dict[Optional[str], Tuple[Any, Any]], color_depth: int
) -> ThemeSpec:
    urwid_theme = []
    for style_name, (fg, bg) in theme_styles.items():
        fg_code16, fg_code256, fg_code24, *fg_props = fg.value.split()
        bg_code16, bg_code256, bg_code24, *bg_props = bg.value.split()

        new_style: StyleSpec
        if color_depth == 1:
            new_style = (style_name, "", "", REQUIRED_STYLES[style_name])

        elif color_depth == 16:
            fg = " ".join([fg_code16] + fg_props).replace("_", " ")
            bg = " ".join([bg_code16] + bg_props).replace("_", " ")
            new_style = (style_name, fg, bg)

        elif color_depth == 256:
            fg = " ".join([fg_code256] + fg_props)
            bg = " ".join([bg_code256] + bg_props)
            new_style = (style_name, "", "", "", fg, bg)

        elif color_depth == 2 ** 24:
            fg = " ".join([fg_code24] + fg_props)
            bg = " ".join([bg_code24] + bg_props)
            new_style = (style_name, "", "", "", fg, bg)

        urwid_theme.append(new_style)
    return urwid_theme
