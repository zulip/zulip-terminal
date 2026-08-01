import re
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import pytest
from pygments.styles.material import MaterialStyle
from pygments.styles.perldoc import PerldocStyle
from pygments.token import STANDARD_TYPES, _TokenType
from pytest import param as case
from pytest_mock import MockerFixture

from zulipterminal.config.color import Background
from zulipterminal.config.regexes import REGEX_COLOR_VALID_FORMATS
from zulipterminal.config.themes import (
    REQUIRED_STYLES,
    STYLE_TRANSLATIONS,
    THEMES,
    InvalidThemeColorCode,
    MissingThemeAttributeError,
    ThemeSpec,
    all_themes,
    complete_and_incomplete_themes,
    generate_pygments_styles,
    generate_theme,
    generate_urwid_compatible_pygments_styles,
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
        (
            theme
            if theme in expected_complete_themes
            else pytest.param(theme, marks=pytest.mark.xfail(reason="incomplete"))
        )
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
        assert fg in theme_colors
        assert bg in theme_colors or bg in Background
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
        case({"META": "extra_field"}, True, id="META_with_extra_field"),
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
        STYLES = dict.fromkeys(REQUIRED_STYLES, (FakeColor.COLOR_1, FakeColor.COLOR_2))
        META: Dict[str, Any] = {
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
        elif action == "extra_field":
            FakeTheme.META["extra_field"] = 5  # Non-iterable misc data
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
    "META, expected_pygments_length",
    [
        case(None, 0, id="META_absent"),
        case(
            {
                "pygments": {
                    "styles": MaterialStyle().styles,
                    "background": "h80",
                    "overrides": {},
                }
            },
            len(STANDARD_TYPES),
            id="META_with_valid_values",
        ),
    ],
)
def test_generate_theme__has_required_attributes(
    mocker: MockerFixture,
    META: Optional[Dict[str, Dict[str, Any]]],
    expected_pygments_length: int,
    fake_theme_name: str = "fake_theme",
    depth: int = 256,  # Only test one depth; others covered in parse_themefile tests
    single_style: str = "somestyle",
) -> None:
    class FakeColor(Enum):
        COLOR_1 = "a a #"
        COLOR_2 = "k b #"

    theme_styles = {single_style: (FakeColor.COLOR_1, FakeColor.COLOR_2)}

    class FakeTheme:
        STYLES = theme_styles
        Color = FakeColor  # Required for validate_colors

    if META is not None:
        FakeTheme.META = META  # type: ignore [attr-defined]

    mocker.patch(MODULE + ".THEMES", {fake_theme_name: FakeTheme})

    generated_theme = generate_theme(
        fake_theme_name, color_depth=depth, transparent_background=False
    )

    assert len(generated_theme) == len(theme_styles) + expected_pygments_length
    assert (single_style, "", "", "", "a", "b") in generated_theme


def test_generate_theme__missing_attributes_in_theme(
    mocker: MockerFixture,
    fake_theme_name: str = "fake_theme",
    depth: int = 256,
    style: str = "somestyle",
) -> None:
    class FakeTheme:
        pass

    mocker.patch(MODULE + ".THEMES", {fake_theme_name: FakeTheme})

    kwargs: Dict[str, Any] = dict(color_depth=depth, transparent_background=False)

    # No attributes (STYLES or META) - flag missing Color
    with pytest.raises(MissingThemeAttributeError) as e:
        generate_theme(fake_theme_name, **kwargs)
    assert str(e.value) == "Theme is missing required attribute 'Color'"

    # Color but missing STYLES - flag missing STYLES
    class FakeColor(Enum):
        COLOR_1 = "a a #"
        COLOR_2 = "k b #"

    FakeTheme.Color = FakeColor  # type: ignore [attr-defined]

    with pytest.raises(MissingThemeAttributeError) as e:
        generate_theme(fake_theme_name, **kwargs)
    assert str(e.value) == "Theme is missing required attribute 'STYLES'"

    # Color, STYLES and META, but no pygments data in META
    not_all_styles = {style: (FakeColor.COLOR_1, FakeColor.COLOR_2)}
    FakeTheme.STYLES = not_all_styles  # type: ignore [attr-defined]
    FakeTheme.META = {}  # type: ignore [attr-defined]

    with pytest.raises(MissingThemeAttributeError) as e:
        generate_theme(fake_theme_name, **kwargs)
    assert str(e.value) == """Theme is missing required attribute 'META["pygments"]'"""

    # Color, STYLES and META, but incomplete pygments in META
    FakeTheme.META = {  # type: ignore [attr-defined]
        "pygments": {"styles": "", "background": ""}
    }

    with pytest.raises(MissingThemeAttributeError) as e:
        generate_theme(fake_theme_name, **kwargs)
    assert (
        str(e.value)
        == """Theme is missing required attribute 'META["pygments"]["overrides"]'"""
    )


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
    assert (
        parse_themefile(theme_styles, color_depth, Color.DARK_MAGENTA, False)
        == expected_urwid_theme
    )


@pytest.mark.parametrize(
    "pygments_data, expected_styles",
    [
        (
            {
                "styles": PerldocStyle().styles,
                "background": "#def",
                "overrides": {
                    "k": "#abc",
                    "sd": "#123, bold",
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
def test_generate_pygments_styles(
    mocker: MockerFixture, pygments_data: Dict[str, Any], expected_styles: ThemeSpec
) -> None:
    pygments_styles = generate_pygments_styles(pygments_data)

    # Check for overrides(k,sd) and inheriting styles (kr)
    for style in expected_styles:
        assert style in pygments_styles


def test_validate_colors(color_depth: int = 16) -> None:
    header_text = "Invalid 16-color codes found in this theme:\n"

    # No invalid colors
    class Color(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "black           h234      #1d2021"
        GRAY_244 = "dark_gray       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    validate_colors(Color, color_depth)

    # One invalid color
    class Color1(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "blac           h234      #1d2021"
        GRAY_244 = "dark_gray       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(Color1, color_depth)
    assert str(e.value) == header_text + "- DARK0_HARD = blac"

    # Two invalid colors
    class Color2(Enum):
        # color          =  16code          256code   24code
        DEFAULT = "default         default   default"
        DARK0_HARD = "blac           h234      #1d2021"
        GRAY_244 = "dark_gra       h244      #928374"
        LIGHT2 = "white           h250      #d5c4a1"

    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(Color2, color_depth)
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

    with pytest.raises(InvalidThemeColorCode) as e:
        validate_colors(Color3, color_depth)
    assert (
        str(e.value)
        == header_text
        + "- DEFAULT = defaul\n"
        + "- DARK0_HARD = blac\n"
        + "- GRAY_244 = dark_gra\n"
        + "- LIGHT2 = whit"
    )


@pytest.mark.parametrize(
    "pygments_styles, expected_styles, style_translations",
    [
        case(
            {},
            {},
            STYLE_TRANSLATIONS,
            id="empty_input",
        ),
        case(
            {
                "token1": "style1",
                "token2": "style2",
            },
            {
                "token1": "style1",
                "token2": "style2",
            },
            {},
            id="empty_translations",
        ),
        case(
            {
                "token1": "bold italic",  # pygments/pygments#2444
                "token2": "italic bold",  # + order shouldn't matter
                "token3": "italic #abc",  # + italic should work with color
            },
            {
                "token1": "bold,italics",
                "token2": "italics,bold",
                "token3": "italics,#abc",
            },
            STYLE_TRANSLATIONS,
            id="default_translations",
        ),
        case(
            {
                "token1": "style italic",
                "token2": "#abc",
            },
            {
                "token1": "newstyle italic",
                "token2": "#abc",
            },
            {"style": "newstyle"},
            id="custom_translations",
        ),
    ],
)
def test_generate_urwid_compatible_pygments_styles(
    pygments_styles: Dict[_TokenType, str],  # NOTE: placeholder string values used
    expected_styles: Dict[_TokenType, str],  #       in parametrized dict keys
    style_translations: Dict[str, str],
) -> None:
    generated_styles = generate_urwid_compatible_pygments_styles(
        pygments_styles, style_translations
    )

    assert set(expected_styles) == set(generated_styles)  # keys unchanged
    assert sorted(expected_styles.items()) == sorted(generated_styles.items())
