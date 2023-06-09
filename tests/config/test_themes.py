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
    parse_themefile,
    valid_16_color_codes,
    validate_colors,
)


MODULE = "zulipterminal.config.themes"

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
            code_match = pattern.match(code)
            assert code_match
            if code_match.group(1) and code_match.group(0).startswith("h"):
                assert int(code_match.group(1)) < 256
            elif code_match.group(1) and code_match.group(0).startswith("g"):
                assert int(code_match.group(1)) <= 100
    # Check if color used in STYLE exists in Color.
    for style_name, style_conf in theme_styles.items():
        fg, bg = style_conf
        assert fg in theme_colors and bg in theme_colors
    # Check completeness of META
    expected_META = {"pygments": ["styles", "background", "overrides"]}
    for metadata, config in expected_META.items():
        assert theme_meta[metadata]
        assert all(theme_meta[metadata][c] for c in config)


def test_complete_and_incomplete_themes__bundled_theme_output() -> None:
    # These are sorted to ensure reproducibility
    result = (
        sorted(expected_complete_themes),
        sorted(set(THEMES) - expected_complete_themes),
    )
    assert result == complete_and_incomplete_themes()


@pytest.mark.parametrize(
    "missing, expected_complete",
    [
        case({}, True, id="keys_complete"),
        case({"Color": None}, False, id="Color_absent"),
        case({"STYLES": None}, False, id="STYLES_absent"),
        case({"STYLES": "incomplete_style"}, False, id="STYLES_incomplete"),
        case({"META": None}, False, id="META_absent"),
        case({"META": {}}, False, id="META_empty"),
        case({"META": {"pygments": {}}}, False, id="META_pygments_empty"),
    ],
)
def test_complete_and_incomplete_themes__single_theme_completeness(
    mocker: MockerFixture,
    missing: Dict[str, Any],
    expected_complete: bool,
    style: str = "s",
    fake_theme_name: str = "sometheme",
) -> None:
    class FakeColor(Enum):
        COLOR_1 = "a a #"
        COLOR_2 = "k b #"

    class FakeTheme:
        Color = FakeColor
        STYLES = {
            style: (FakeColor.COLOR_1, FakeColor.COLOR_2) for style in REQUIRED_STYLES
        }
        META = {
            "pygments": {
                "styles": None,
                "background": None,
                "overrides": None,
            }
        }

    incomplete_style = {style: (FakeColor.COLOR_1, FakeColor.COLOR_2)}

    for field, action in missing.items():
        if action == "incomplete_style":
            setattr(FakeTheme, field, incomplete_style)
        elif action is None:
            delattr(FakeTheme, field)
        else:
            setattr(FakeTheme, field, action)

    mocker.patch(MODULE + ".THEMES", {fake_theme_name: FakeTheme})

    if expected_complete:
        assert complete_and_incomplete_themes() == ([fake_theme_name], [])
    else:
        assert complete_and_incomplete_themes() == ([], [fake_theme_name])


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

    theme_styles: Dict[Optional[str], Tuple[Color, Color]] = {
        "s1": (Color.WHITE__BOLD, Color.DARK_MAGENTA),
        "s2": (Color.WHITE__BOLD_ITALICS, Color.DARK_MAGENTA),
    }

    req_styles = {"s1": "", "s2": "bold"}
    mocker.patch.dict("zulipterminal.config.themes.REQUIRED_STYLES", req_styles)
    assert parse_themefile(theme_styles, color_depth) == expected_urwid_theme


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
