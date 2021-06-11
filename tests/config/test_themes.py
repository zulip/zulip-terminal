import re
from enum import Enum

import pytest

from zulipterminal.config.themes import (
    NEW_THEMES,
    REQUIRED_STYLES,
    THEMES,
    all_themes,
    complete_and_incomplete_themes,
    generate_theme,
    parse_themefile,
    theme_with_monochrome_added,
)


expected_complete_themes = {
    "zt_dark",
    "gruvbox_dark",
    "zt_light",
    "zt_blue",
    "gruvbox_dark24",
}
aliases_16_color = [
    "default",
    "black",
    "dark red",
    "dark green",
    "brown",
    "dark blue",
    "dark magenta",
    "dark cyan",
    "dark gray",
    "light red",
    "light green",
    "yellow",
    "light blue",
    "light magenta",
    "light cyan",
    "light gray",
    "white",
]


def test_all_themes():
    assert all_themes() == list(THEMES.keys())


# Check built-in themes are complete for quality-control purposes
@pytest.mark.parametrize(
    "theme_name",
    [
        theme
        if theme in expected_complete_themes
        else pytest.param(theme, marks=pytest.mark.xfail(reason="incomplete"))
        for theme in NEW_THEMES
    ],
)
def test_new_builtin_theme_completeness(theme_name):
    theme = NEW_THEMES[theme_name]
    theme_styles = theme.STYLES
    theme_colors = theme.Color

    # Check if STYLE and REQUIRED_STYLES use the same styles.
    assert len(theme_styles) == len(REQUIRED_STYLES)
    assert all(required_style in theme_styles for required_style in REQUIRED_STYLES)
    # Check if colors are defined with all 3 color codes.
    for color in theme_colors:
        if "__" in color.name:
            continue

        codes = color.value.split()
        assert len(codes) == 3
        # Check if 16-color alias is correct
        assert codes[0].replace("_", " ") in aliases_16_color
        # Check if 24-bit and 256 color is any of
        # #000000-#ffffff or #000-#fff or h0-h255 or g0-g100 0r g#00-g#ff
        pattern = re.compile(
            "#[\\da-f]{6}|#[\\da-f]{3}|(?:h|g)([\\d]{1,3})|g#[\\da-f]{2}|default$"
        )
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
def test_builtin_theme_completeness(theme_name):
    theme = THEMES[theme_name]
    styles_in_theme = {style[0] for style in theme}

    assert len(styles_in_theme) == len(REQUIRED_STYLES)
    assert all(required_style in styles_in_theme for required_style in REQUIRED_STYLES)


@pytest.mark.parametrize(
    "theme_name, depth",
    [
        ("zt_dark", 1),
        ("zt_dark", 16),
        ("zt_dark", 256),
        ("zt_light", 16),
        ("zt_blue", 16),
        ("gruvbox_dark", 16),
        ("gruvbox_dark", 256),
        ("gruvbox_dark24", 2 ** 24),
        ("gruvbox_dark24", 2 ** 24),
    ],
)
def test_migrated_themes(theme_name, depth):
    def split_and_strip(style):
        style = style.split(",")
        style = [s.strip() for s in style]
        return style

    old_theme = theme_with_monochrome_added(THEMES[theme_name])

    new_theme = generate_theme(theme_name.replace("24", ""), depth)

    for new_style, old_style in zip(new_theme, old_theme):
        assert new_style[0] == old_style[0]
        if depth == 1:
            assert new_style[3] == old_style[3]
        elif depth == 16:
            assert split_and_strip(new_style[1]) == split_and_strip(old_style[1])
            assert split_and_strip(new_style[2]) == split_and_strip(old_style[2])
        else:
            assert split_and_strip(new_style[4]) == split_and_strip(old_style[4])
            assert split_and_strip(new_style[5]) == split_and_strip(old_style[5])


def test_complete_and_incomplete_themes():
    # These are sorted to ensure reproducibility
    result = (
        sorted(list(expected_complete_themes)),
        sorted(list(set(THEMES) - expected_complete_themes)),
    )
    assert result == complete_and_incomplete_themes()


@pytest.mark.parametrize(
    "theme, expected_new_theme, req_styles",
    [
        ([("a", "another")], [], {}),
        ([("a", "another")], [("a", "another")], {"a": ""}),
        ([("a", "fg", "bg")], [("a", "fg", "bg", "x")], {"a": "x"}),
        ([("a", "fg", "bg", "bold")], [("a", "fg", "bg", "x")], {"a": "x"}),
        (
            [("a", "fg", "bg", "bold", "h1", "h2")],
            [("a", "fg", "bg", "x", "h1", "h2")],
            {"a": "x"},
        ),
    ],
    ids=[
        "incomplete_theme",
        "one_to_one",
        "16_color_add_mono",
        "16_color_mono_overwrite",
        "256_color",
    ],
)
def test_theme_with_monochrome_added(mocker, theme, expected_new_theme, req_styles):
    mocker.patch.dict("zulipterminal.config.themes.REQUIRED_STYLES", req_styles)
    assert theme_with_monochrome_added(theme) == expected_new_theme


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
            2 ** 24,
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
def test_parse_themefile(mocker, color_depth, expected_urwid_theme):
    class Color(Enum):
        WHITE__BOLD = "white          #fff   #ffffff , bold"
        WHITE__BOLD_ITALICS = "white  #fff   #ffffff , bold , italics"
        DARK_MAGENTA = "dark_magenta  h90    #870087"

    STYLES = {
        "s1": (Color.WHITE__BOLD, Color.DARK_MAGENTA),
        "s2": (Color.WHITE__BOLD_ITALICS, Color.DARK_MAGENTA),
    }

    req_styles = {"s1": "", "s2": "bold"}
    mocker.patch.dict("zulipterminal.config.themes.REQUIRED_STYLES", req_styles)
    assert parse_themefile(STYLES, color_depth) == expected_urwid_theme
