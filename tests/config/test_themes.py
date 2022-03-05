import re
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import pytest
from pygments.styles.perldoc import PerldocStyle
from pytest_mock import MockerFixture

from zulipterminal.config.regexes import REGEX_COLOR_VALID_FORMATS
from zulipterminal.config.themes import (
    REQUIRED_STYLES,
    THEMES,
    ThemeSpec,
    add_pygments_style,
    all_themes,
    complete_and_incomplete_themes,
    parse_themefile,
)


expected_complete_themes = {
    "zt_dark",
    "gruvbox_dark",
    "gruvbox_light",
    "zt_light",
    "zt_blue",
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


def test_all_themes() -> None:
    assert all_themes() == list(THEMES.keys())


# Check built-in themes are complete for quality-control purposes
@pytest.mark.parametrize(
    "theme_name",
    [
        theme
        if theme in expected_complete_themes
        else pytest.param(theme, marks=pytest.mark.xfail(reason="incomplete"))
        for theme in THEMES
    ],
)
def test_builtin_theme_completeness(theme_name: str) -> None:
    theme = THEMES[theme_name]
    theme_styles = theme.STYLES
    theme_colors = theme.Color
    theme_meta = theme.META

    # Explicitly test extra and missing styles to improve debugging
    extra_styles = theme_styles - REQUIRED_STYLES.keys()
    missing_styles = REQUIRED_STYLES.keys() - theme_styles
    assert extra_styles == set()
    assert missing_styles == set()

    # Check if colors are defined with all 3 color codes.
    for color in theme_colors:
        if "__" in color.name:
            continue

        codes = color.value.lower().split()
        assert len(codes) == 3
        # Check if 16-color alias is correct
        assert codes[0] in valid_16_color_codes
        # Check if 24-bit and 256 color is any of the valid color codes
        pattern = re.compile(REGEX_COLOR_VALID_FORMATS)
        for code in [codes[1], codes[2]]:
            code = pattern.match(code)
            assert code
            if code.group(1) and code.group(0).startswith("h"):
                assert int(code.group(1)) < 256
            elif code.group(1) and code.group(0).startswith("g"):
                assert int(code.group(1)) <= 100
    # Check if color used in STYLE exists in Color.
    for style_name, style_conf in theme_styles.items():
        fg, bg = style_conf
        assert fg in theme_colors and bg in theme_colors
    # Check completeness of META
    expected_META = {"pygments": ["styles", "background", "overrides"]}
    for metadata, config in expected_META.items():
        assert theme_meta[metadata]
        assert all([theme_meta[metadata][c] for c in config])


def test_complete_and_incomplete_themes() -> None:
    # These are sorted to ensure reproducibility
    result = (
        sorted(list(expected_complete_themes)),
        sorted(list(set(THEMES) - expected_complete_themes)),
    )
    assert result == complete_and_incomplete_themes()


@pytest.mark.parametrize(
    "color_depth, expected_urwid_theme",
    [
        (1, [("s1", "", "", ""), ("s2", "", "", "bold")]),
        (
            16,
            [
                ("s1", "white , bold", "dark magenta"),
                ("s2", "white , bold , italics", "dark magenta"),
            ],
        ),
        (
            256,
            [
                ("s1", "", "", "", "#fff , bold", "h90"),
                ("s2", "", "", "", "#fff , bold , italics", "h90"),
            ],
        ),
        (
            2**24,
            [
                ("s1", "", "", "", "#ffffff , bold", "#870087"),
                ("s2", "", "", "", "#ffffff , bold , italics", "#870087"),
            ],
        ),
    ],
    ids=[
        "mono-chrome",
        "16-color",
        "256-color",
        "24-bit-color",
    ],
)
def test_parse_themefile(
    mocker: MockerFixture, color_depth: int, expected_urwid_theme: ThemeSpec
) -> None:
    class Color(Enum):
        WHITE__BOLD = "white          #fff   #ffffff , bold"
        WHITE__BOLD_ITALICS = "white  #fff   #ffffff , bold , italics"
        DARK_MAGENTA = "dark_magenta  h90    #870087"

    STYLES: Dict[Optional[str], Tuple[Color, Color]] = {
        "s1": (Color.WHITE__BOLD, Color.DARK_MAGENTA),
        "s2": (Color.WHITE__BOLD_ITALICS, Color.DARK_MAGENTA),
    }

    req_styles = {"s1": "", "s2": "bold"}
    mocker.patch.dict("zulipterminal.config.themes.REQUIRED_STYLES", req_styles)
    assert parse_themefile(STYLES, color_depth) == expected_urwid_theme


@pytest.mark.parametrize(
    "theme_meta, expected_styles",
    [
        (
            {
                "pygments": {
                    "styles": PerldocStyle().styles,
                    "background": "#def",
                    "overrides": {
                        "k": "#abc",
                        "sd": "#123, bold",
                    },
                },
            },
            [
                ("pygments:k", "light blue, bold", "dark gray", "bold", "#abc", "#def"),
                (
                    "pygments:kr",
                    "light blue, bold",
                    "dark gray",
                    "bold",
                    "#abc",
                    "#def",
                ),
                (
                    "pygments:sd",
                    "light gray",
                    "dark gray",
                    "bold",
                    "#123, bold",
                    "#def",
                ),
            ],
        )
    ],
)
def test_add_pygments_style(
    mocker: MockerFixture, theme_meta: Dict[str, Any], expected_styles: ThemeSpec
) -> None:
    urwid_theme: ThemeSpec = [(None, "#xxx", "#yyy")]
    original_urwid_theme = deepcopy(urwid_theme)

    add_pygments_style(theme_meta, urwid_theme)

    # Check if original exists
    assert original_urwid_theme[0] in urwid_theme
    # Check for overrides(k,sd) and inheriting styles (kr)
    for style in expected_styles:
        assert style in urwid_theme
