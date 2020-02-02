import pytest

from zulipterminal.config.themes import (
    THEMES, all_themes, complete_and_incomplete_themes, required_styles,
)


expected_complete_themes = {
    'default', 'gruvbox', 'light', 'blue'
}


def test_all_themes():
    assert all_themes() == list(THEMES.keys())


# Check built-in themes are complete for quality-control purposes
@pytest.mark.parametrize('theme_name', [
    theme if theme in expected_complete_themes
    else pytest.param(theme, marks=pytest.mark.xfail(reason="incomplete"))
    for theme in THEMES
])
def test_builtin_theme_completeness(theme_name):
    theme = THEMES[theme_name]
    styles_in_theme = {style[0] for style in theme}

    assert len(styles_in_theme) >= len(required_styles)
    assert all(required_style in styles_in_theme
               for required_style in required_styles)


def test_complete_and_incomplete_themes():
    # These are sorted to ensure reproducibility
    result = (sorted(list(expected_complete_themes)),
              sorted(list(set(THEMES)-expected_complete_themes)))
    assert result == complete_and_incomplete_themes()
