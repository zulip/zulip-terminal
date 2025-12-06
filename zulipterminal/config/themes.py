"""
Styles and their colour mappings in each theme, with helper functions
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from pygments.token import STANDARD_TYPES, _TokenType

from zulipterminal.config.color import Background, term16
from zulipterminal.themes import gruvbox_dark, gruvbox_light, zt_blue, zt_dark, zt_light


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
    'msg_sender'      : '',
    'unread'          : 'strikethrough',
    'user_active'     : 'bold',
    'user_idle'       : '',
    'user_offline'    : '',
    'user_inactive'   : '',
    'user_bot'        : '',
    'title'           : 'bold',
    'column_title'    : 'bold',
    'time'            : '',
    'bar'             : 'standout',
    'msg_emoji'       : 'bold',
    'reaction'        : 'bold',
    'reaction_mine'   : 'standout',
    'msg_heading'     : 'bold',
    'msg_math'        : 'standout',
    'msg_mention'     : 'bold',
    'msg_link'        : '',
    'msg_link_index'  : 'bold',
    'msg_quote'       : 'underline',
    'msg_bold'        : 'bold',
    'msg_time'        : 'bold',
    'footer'          : 'standout',
    'footer_contrast' : 'standout',
    'starred'         : 'bold',
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
    'popup_category'  : 'bold',
    'popup_contrast'  : 'standout',
    'popup_important' : 'bold',
    'widget_disabled' : 'strikethrough',
    'area:help'       : 'standout',
    'area:msg'        : 'standout',
    'area:stream'     : 'standout',
    'area:error'      : 'standout',
    'area:user'       : 'standout',
    'search_error'    : 'standout',
    'task:success'    : 'standout',
    'task:error'      : 'standout',
    'task:warning'    : 'standout',
    'ui_code'         : 'bold',
}

REQUIRED_META = {
    'pygments': {
        'styles'     : None,
        'background' : None,
        'overrides'  : None,
    }
}
# fmt: on

# This is the main list of themes
THEMES: Dict[str, Any] = {
    "gruvbox_dark": gruvbox_dark,
    "gruvbox_light": gruvbox_light,
    "zt_dark": zt_dark,
    "zt_light": zt_light,
    "zt_blue": zt_blue,
}

# These are older aliases to some of the above, for compatibility
# NOTE: Do not add to this section, and only modify if a theme name changes
THEME_ALIASES = {
    "default": "zt_dark",
    "gruvbox": "gruvbox_dark",
    "light": "zt_light",
    "blue": "zt_blue",
}

# These are urwid color names with underscores instead of spaces
valid_16_color_codes = [
    "default",
    "black",
    "dark_red",
    "dark_green",
    "brown",
    "dark_blue",
    "dark_magenta",
    "dark_cyan",
    "dark_gray",
    "light_red",
    "light_green",
    "yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "light_gray",
    "white",
]

# These are style_translations for translating pygments styles into
# urwid-compatible styles
STYLE_TRANSLATIONS = {
    " ": ",",
    "italic": "italics",
}


class ThemeError(Exception):
    pass


class InvalidThemeColorCode(ThemeError):
    pass


class MissingThemeAttributeError(ThemeError):
    def __init__(self, attribute: str) -> None:
        super().__init__(f"Theme is missing required attribute '{attribute}'")


def all_themes() -> List[str]:
    return list(THEMES.keys())


def aliased_themes() -> Dict[str, str]:
    return dict(THEME_ALIASES)


def complete_and_incomplete_themes() -> Tuple[List[str], List[str]]:
    complete = {
        name
        for name, theme in THEMES.items()
        if getattr(theme, "Color", None)
        if getattr(theme, "STYLES", None)
        if set(theme.STYLES) == set(REQUIRED_STYLES)
        if getattr(theme, "META", None)
        if set(theme.META).issuperset(set(REQUIRED_META))
        for meta, conf in REQUIRED_META.items()
        if set(conf) == set(theme.META.get(meta, {}))
    }
    incomplete = set(THEMES) - complete
    return sorted(complete), sorted(incomplete)


def generate_theme(
    name: str,
    *,
    color_depth: int,
    transparent_background: bool,
) -> ThemeSpec:
    theme_module = THEMES[name]

    try:
        theme_colors = theme_module.Color
    except AttributeError:
        raise MissingThemeAttributeError("Color") from None
    validate_colors(theme_colors, color_depth)

    try:
        theme_styles = theme_module.STYLES
    except AttributeError:
        raise MissingThemeAttributeError("STYLES") from None

    # META is not required, but if present should contain pygments data
    theme_meta = getattr(theme_module, "META", None)
    if theme_meta is not None:
        # FIXME: Is META now required? Or only if Background.COLOR present?
        # If used in styles and background is not specified, transparent by default!
        background_color = theme_meta.get("background", Background.COLOR)

        pygments_data = theme_meta.get("pygments", None)
        if pygments_data is None:
            raise MissingThemeAttributeError('META["pygments"]') from None
        for key in REQUIRED_META["pygments"]:
            if pygments_data.get(key) is None:
                raise MissingThemeAttributeError(f'META["pygments"]["{key}"]') from None
        pygments_styles = generate_pygments_styles(pygments_data)
    else:
        background_color = Background.COLOR
        pygments_styles = []

    urwid_theme = parse_themefile(
        theme_styles,
        color_depth,
        background_color,
        transparent_background,
    )
    urwid_theme.extend(pygments_styles)

    return urwid_theme


# color_enum can be one of many enums satisfying the specification
# There is currently no generic enum type
def validate_colors(color_enum: Any, color_depth: int) -> None:
    """
    This function validates color-codes for a given theme, given colors are in `Color`.

    If any color is not in accordance with urwid default 16-color codes then the
    function raises InvalidThemeColorCode with the invalid colors.
    """
    failure_text = []
    if color_depth == 16:
        for color in color_enum:
            color_16code = color.value.split()[0]
            if color_16code not in valid_16_color_codes:
                invalid_16_color_code = str(color.name)
                failure_text.append(f"- {invalid_16_color_code} = {color_16code}")
        if failure_text == []:
            return
        else:
            text = "\n".join(
                ["Invalid 16-color codes found in this theme:"] + failure_text
            )
            raise InvalidThemeColorCode(text)


def parse_themefile(
    theme_styles: Dict[Optional[str], Tuple[Any, Any]],
    color_depth: int,
    background_color: Any,
    transparent_background: bool,
) -> ThemeSpec:
    urwid_theme = []
    for style_name, (fg_name, bg_name) in theme_styles.items():
        fg_code16, fg_code256, fg_code24, *fg_props = fg_name.value.split()

        # Background.COLOR is transparent
        # => Replace with background_color, unless transparency is requested
        if bg_name == Background.COLOR and not transparent_background:
            bg_name = background_color  # noqa: PLW2901  # overwrite loop variable

        bg_code16, bg_code256, bg_code24, *bg_props = bg_name.value.split()

        new_style: StyleSpec
        if color_depth == 1:
            new_style = (style_name, "", "", REQUIRED_STYLES[style_name])

        elif color_depth == 16:
            fg = " ".join([fg_code16] + fg_props).replace("_", " ")
            bg = " ".join([bg_code16] + bg_props).replace("_", " ")
            new_style = (style_name, fg, bg)

        elif color_depth == 256:
            fg = " ".join([fg_code256] + fg_props).lower()
            bg = " ".join([bg_code256] + bg_props).lower()
            new_style = (style_name, "", "", "", fg, bg)

        elif color_depth == 2**24:
            fg = " ".join([fg_code24] + fg_props).lower()
            bg = " ".join([bg_code24] + bg_props).lower()
            new_style = (style_name, "", "", "", fg, bg)

        urwid_theme.append(new_style)
    return urwid_theme


def generate_urwid_compatible_pygments_styles(
    pygments_styles: Dict[_TokenType, str],
    style_translations: Dict[str, str] = STYLE_TRANSLATIONS,
) -> Dict[_TokenType, str]:
    urwid_compatible_styles = {}
    for token, style in pygments_styles.items():
        updated_style = style
        for old_value, new_value in style_translations.items():
            updated_style = updated_style.replace(old_value, new_value)
        urwid_compatible_styles[token] = updated_style
    return urwid_compatible_styles


def generate_pygments_styles(pygments: Dict[str, Any]) -> ThemeSpec:
    """
    This function adds pygments styles for use in syntax
    highlighting of code blocks and inline code.
    pygments["styles"]:
        one of those available in pygments/styles.
    pygments["background"]:
        used to set a different background for codeblocks instead of the
        one used in the syntax style, if it doesn't match with
        the overall zt theme.
        The default is available as Eg: MaterialStyle.background_color
    pygments["overrides"]:
        used to override certain pygments styles to match to urwid format.
        It can also be used to customize the syntax style.
    """
    pygments_styles = pygments["styles"]
    pygments_bg = pygments["background"]
    pygments_overrides = pygments["overrides"]

    term16_styles = term16.styles
    term16_bg = term16.background_color

    theme_styles_from_pygments: ThemeSpec = []
    pygments_styles = generate_urwid_compatible_pygments_styles(pygments_styles)

    for token, css_class in STANDARD_TYPES.items():
        if css_class in pygments_overrides:
            pygments_styles[token] = pygments_overrides[css_class]

        # Inherit parent pygments style if not defined.
        # Eg: Use `String` if `String.Double` is not present.
        if pygments_styles[token] == "":
            try:
                t = [k for k, v in STANDARD_TYPES.items() if v == css_class[0]]
                pygments_styles[token] = pygments_styles[t[0]]
            except IndexError:
                pass

        if term16_styles[token] == "":
            try:
                t = [k for k, v in STANDARD_TYPES.items() if v == css_class[0]]
                term16_styles[token] = term16_styles[t[0]]
            except IndexError:
                pass

        new_style = (
            f"pygments:{css_class}",
            term16_styles[token],
            term16_bg,
            "bold",  # Mono style
            pygments_styles[token],
            pygments_bg,
        )
        theme_styles_from_pygments.append(new_style)
    return theme_styles_from_pygments
