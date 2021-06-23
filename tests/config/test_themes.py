import re

import pytest

from zulipterminal.config.themes import (
    NEW_THEMES,
    REQUIRED_STYLES,
    THEMES,
    all_themes,
    complete_and_incomplete_themes,
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
