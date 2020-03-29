import pytest

from zulipterminal.config.themes import (
    THEMES, all_themes, complete_and_incomplete_themes,
    required_styles, get_transparent_theme_variant,
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
    
    
def test_get_transparent_theme_variant():
    theme = [       
        (None,           'white', 'black'),
        ('selected',     'white', 'blue'),
        ('msg_selected', 'white', 'black'),
        ('header',       'white', '', ''),
        ('custom',       'white', 'blue', 'underline'),
        ('content',      'white', 'black', 'standout'),
        ('name',         'white'),
        ('unread',       'white', ''),
        ('active',       'white', 'black'),
        ('idle',         'white', 'black'),
        ('offline',      'white', 'black'),
        ('inactive',     'white', 'black'),
        ('title',        'white', 'black'),
        ('time',         'white', 'black'),
        ('bar',          'white', 'blue'),
        ('help',         'white', 'gray'),
        ('emoji',        'white', 'black'),
        ('reaction',     'white', 'black'),
        ('span',         'white', 'black'),
        ('link',         'white', 'black'),
        ('blockquote',   'white', 'black'),
        ('code',         'white', 'white'),
        ('bold',         'white', 'black'),
        ('footer',       'white', 'green'),
        ('starred',      'white', 'black'),
        ('category',     'white', ''),
    ]
    expected_results = {
     None : '',
    'msg_selected' : '',
    'content' : '',
    'name' : '',
    'unread' : '',
    'active' : '',
    'idle' : '',
    'offline' : '',
    'inactive' : '',
    'title' : '',
    'time' : '',
    'emoji' : '',
    'reaction' : '',
    'span' : '',
    'link' : '',
    'blockquote' : '',
    'bold' : '',
    'starred' : '',
    'selected' : 'blue',
    'header' : '',
    'custom' : 'blue',
    'bar' : 'blue',
    'help' : 'gray',
    'code' : 'white',
    'category' : '',
    'footer' : 'green',
    } 
    
    result = get_transparent_theme_variant(theme)
    assert len(result[6]) == 2
    assert len(result) == len(expected_results)
    for r in result:
        assert(r[1] == 'white')
        if (len(r) > 2):
            assert(r[2] == expected_results[r[0]])
            

