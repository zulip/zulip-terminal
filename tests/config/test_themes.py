import re
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import pytest
from pygments.styles.perldoc import PerldocStyle
from pytest import param as case
from pytest_mock import MockerFixture

from zulipterminal.config.regexes import REGEX_COLOR_VALID_FORMATS
from zulipterminal.config.themes import (
    REQUIRED_STYLES,
    THEMES,
    InvalidThemeColorCode,
    ThemeSpec,
    add_pygments_style,
    all_themes,
    complete_and_incomplete_themes,
    create_focus_map,
    parse_themefile,
    valid_16_color_codes,
    validate_colors,
)


expected_complete_themes = {
    "zt_dark",
    "gruvbox_dark",
    "gruvbox_light",
    "zt_light",
    "zt_blue",
}


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


# Validate 16-color-codes
@pytest.mark.parametrize(
    "color_depth, theme_name",
    [
        (16, "zt_dark"),
        (16, "gruvbox_dark"),
        (16, "gruvbox_light"),
        (16, "zt_light"),
        (16, "zt_blue"),
    ],
)
def test_validate_colors(theme_name: str, color_depth: int) -> None:
    theme = THEMES[theme_name]

    header_text = f"Invalid 16-color codes in theme '{theme_name}':\n"

    # No invalid colors
    class Color(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "black           h234      #1d2021"
        GRAY_244 = "dark_gray       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    theme.Color = Color
    validate_colors(theme_name, 16)

    # One invalid color
    class Color1(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "blac           h234      #1d2021"
        GRAY_244 = "dark_gray       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    theme.Color = Color1
    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(theme_name, 16)
    assert str(e.value) == header_text + "- DARK0_HARD = blac"

    # Two invalid colors
    class Color2(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "blac           h234      #1d2021"
        GRAY_244 = "dark_gra       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    theme.Color = Color2
    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(theme_name, 16)
    assert (
        str(e.value) == header_text + "- DARK0_HARD = blac\n" + "- GRAY_244 = dark_gra"
    )

    # Multiple invalid colors
    class Color3(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "defaul         default   default"
        DARK0_HARD = "blac           h234      #1d2021"
        GRAY_244 = "dark_gra       h244      #928374"
        LIGHT2 = "whit           h250      #d5c4a1"

    theme.Color = Color3
    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(theme_name, 16)
    assert (
        str(e.value)
        == header_text
        + "- DEFAULT = defaul\n"
        + "- DARK0_HARD = blac\n"
        + "- GRAY_244 = dark_gra\n"
        + "- LIGHT2 = whit"
    )


@pytest.mark.parametrize(
    "palette, selected_style_name, is_mono, expected_additional_palette",
    [
        case(
            [
                (None, "", "", ""),
                ("selected", "", "", "standout"),
                ("msg_selected", "", "", "standout"),
                ("header", "", "", "bold"),
                ("general_narrow", "", "", ""),
            ],
            "selected",
            True,
            [],
            id="mono-with-focus:selected",
        ),
        case(
            [
                (None, "white", "black"),
                ("selected", "white", "dark blue"),
                ("msg_selected", "white", "dark red"),
                ("header", "dark cyan", "black"),
                ("general_narrow", "white", "dark blue"),
            ],
            "selected",
            False,
            [
                ("header_selected", "dark cyan", "dark blue"),
                ("general_narrow_selected", "white", "dark blue"),
            ],
            id="16-color-with-focus:selected",
        ),
        case(
            [
                (None, "", "", "", "#fff", "g19"),
                ("selected", "", "", "", "#fff", "#24a"),
                ("msg_selected", "", "", "", "#fff", "#53c"),
                ("header", "", "", "", "#088", "g19"),
                ("general_narrow", "", "", "", "#fff", "#34b"),
            ],
            "selected",
            False,
            [
                ("header_selected", "", "", "", "#088", "#24a"),
                ("general_narrow_selected", "", "", "", "#fff", "#34b"),
            ],
            id="256-color-with-focus:selected",
        ),
        case(
            [
                (None, "white", "black"),
                ("selected", "white", "dark blue"),
                ("msg_selected", "white", "dark red"),
                ("header", "dark cyan", "black"),
                ("general_narrow", "white", "dark blue"),
            ],
            "msg_selected",
            False,
            [
                ("header_msg_selected", "dark cyan", "dark red"),
                ("general_narrow_msg_selected", "white", "dark blue"),
            ],
            id="16-color-with-focus:msg_selected",
        ),
        case(
            [
                (None, "white", "black"),
                ("selected", "white", "dark blue"),
                ("msg_selected", "white", "dark red"),
                ("header", "dark cyan", "black"),
                ("general_narrow", "white", "dark blue"),
                ("header_selected", "dark gray", "green"),
            ],
            "selected",
            False,
            [
                ("general_narrow_selected", "white", "dark blue"),
            ],
            id="16-color-with-focus:selected-override:header",
        ),
    ],
)
def test_create_focus_map(
    mocker: MockerFixture,
    palette: ThemeSpec,
    selected_style_name: str,
    is_mono: bool,
    expected_additional_palette: ThemeSpec,
) -> None:
    view = mocker.Mock()
    view.palette = palette
    style_names = ["header", "general_narrow"]
    if is_mono:
        expected_focus_map = {
            style: "selected" for style in [None, "header", "general_narrow"]
        }
    else:
        expected_focus_map = {
            None: selected_style_name,
            "header": "header_" + selected_style_name,
            "general_narrow": "general_narrow_" + selected_style_name,
        }

    focus_map = create_focus_map(view, style_names, selected_style_name)

    assert focus_map == expected_focus_map
    for style in expected_additional_palette:
        assert style in view.palette
