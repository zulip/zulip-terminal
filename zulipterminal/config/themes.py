from typing import Dict, List, Optional, Tuple


ThemeSpec = List[Tuple[Optional[str], ...]]

# The keys in required_styles specify what styles are necessary for a theme to
# be complete, while the values are those used to style each element in
# monochrome (1-bit) mode - independently of the specified theme

required_styles = {  # style-name: monochrome-bit-depth-style
    None: '',
    'selected': 'standout',
    'msg_selected': 'standout',
    'header': 'bold',
    'general_narrow': 'standout',
    'general_bar': '',
    'name': '',
    'unread': 'strikethrough',
    'user_active': 'bold',
    'user_idle': '',
    'user_offline': '',
    'user_inactive': '',
    'title': 'bold',
    'time': '',
    'bar': 'standout',
    'popup_contrast': 'standout',
    'msg_emoji': 'bold',
    'reaction': 'bold',
    'reaction_mine': 'standout',
    'msg_mention': 'bold',
    'msg_link': '',
    'msg_quote': 'underline',
    'msg_code': 'bold',
    'msg_bold': 'bold',
    'footer': 'standout',
    'starred': 'bold',
    'popup_category': 'bold',
    'unread_count': 'bold',
    'filter_results': 'bold',
}


# 256-color base names for default theme (bold values added below)
DEF_base = dict(
    dark_red='#a00',
    brown='#880',
    dark_blue='#24a',
    dark_cyan='#088',
    dark_gray='#666',
    light_red='#f00',
    light_green='#0f0',
    dark_green='#080',
    yellow='#ff0',
    light_blue='#28d',
    light_magenta='#c8f',
    white='#fff',
    black='g19',
)

DEF = dict(DEF_base,
           **{color + ':bold': code + ', bold'
              for color, code in DEF_base.items()})

# Colors used in gruvbox-256
# See https://github.com/morhetz/gruvbox/blob/master/colors/gruvbox.vim
BLACK = 'h234'  # dark0_hard
WHITE = 'h246'  # light4_256
WHITEBOLD = '%s, bold' % WHITE
DARKBLUE = 'h24'  # faded_blue
DARKRED = 'h88'  # faded_red
LIGHTBLUE = 'h109'  # bright_blue
YELLOW = 'h172'  # neutral_yellow
YELLOWBOLD = '%s, bold' % YELLOW
LIGHTGREEN = 'h142'  # bright_green
LIGHTRED = 'h167'  # bright_red
LIGHTREDBOLD = '%s, bold' % LIGHTRED
GRAY = 'h244'  # gray_244
LIGHTMAGENTA = 'h132'  # neutral_purple
LIGHTMAGENTABOLD = '%s, bold' % LIGHTMAGENTA

THEME_ALIASES = {
    'default': 'zt_dark',
    'gruvbox': 'gruvbox_dark',
    'light': 'zt_light',
    'blue': 'zt_blue',
}

THEMES = {
    'zt_dark': [
        (None,             'white',                   'black',
         None,             DEF['white'],              DEF['black']),
        ('selected',       'white',                   'dark blue',
         None,             DEF['white'],              DEF['dark_blue']),
        ('msg_selected',   'white',                   'dark blue',
         None,             DEF['white'],              DEF['dark_blue']),
        ('header',         'dark cyan',               'dark blue',
         None,             DEF['dark_cyan'],          DEF['dark_blue']),
        ('general_narrow', 'white',                   'dark blue',
         None,             DEF['white'],              DEF['dark_blue']),
        ('general_bar',    'white',                   'black',
         None,             DEF['white'],              DEF['black']),
        ('name',           'yellow, bold',            'black',
         None,             DEF['yellow:bold'],        DEF['black']),
        ('unread',         'dark blue',               'black',
         None,             DEF['dark_blue'],          DEF['black']),
        ('user_active',    'light green',             'black',
         None,             DEF['light_green'],        DEF['black']),
        ('user_idle',      'yellow',                  'black',
         None,             DEF['yellow'],             DEF['black']),
        ('user_offline',   'white',                   'black',
         None,             DEF['white'],              DEF['black']),
        ('user_inactive',  'white',                   'black',
         None,             DEF['white'],              DEF['black']),
        ('title',          'white, bold',             'black',
         None,             DEF['white:bold'],         DEF['black']),
        ('time',           'light blue',              'black',
         None,             DEF['light_blue'],         DEF['black']),
        ('bar',            'white',                   'dark gray',
         None,             DEF['white'],              DEF['dark_gray']),
        ('popup_contrast', 'white',                   'dark gray',
         None,             DEF['white'],              DEF['dark_gray']),
        ('msg_emoji',      'light magenta',           'black',
         None,             DEF['light_magenta'],      DEF['black']),
        ('reaction',       'light magenta, bold',     'black',
         None,             DEF['light_magenta:bold'], DEF['black']),
        ('reaction_mine',  'black',                   'light magenta',
         None,             DEF['black'],              DEF['light_magenta']),
        ('msg_mention',    'light red, bold',         'black',
         None,             DEF['light_red:bold'],     DEF['black']),
        ('msg_link',       'light blue',              'black',
         None,             DEF['light_blue'],         DEF['black']),
        ('msg_quote',      'brown',                   'black',
         None,             DEF['brown'],              DEF['black']),
        ('msg_code',       'black',                   'white',
         None,             DEF['black'],              DEF['white']),
        ('msg_bold',       'white, bold',             'black',
         None,             DEF['white:bold'],         DEF['black']),
        ('footer',         'white',                   'dark red',
         None,             DEF['white'],              DEF['dark_red']),
        ('starred',        'light red, bold',         'black',
         None,             DEF['light_red:bold'],     DEF['black']),
        ('popup_category', 'light blue, bold',        'black',
         None,             DEF['light_blue:bold'],    DEF['black']),
        ('unread_count',   'yellow',                  'black',
         None,             DEF['yellow'],             DEF['black']),
        ('table_head',     'white, bold',             'black',
         None,             DEF['white:bold'],         DEF['black']),
        ('filter_results', 'white',                   'dark green',
         None,             DEF['white'],              DEF['dark_green']),
    ],
    'gruvbox_dark': [
        # default colorscheme on 16 colors, gruvbox colorscheme
        # on 256 colors
        (None,             'white',           'black',
         None,             WHITE,             BLACK),
        ('selected',       'black',           'white',
         None,             BLACK,             WHITE),
        ('msg_selected',   'black',           'white',
         None,             BLACK,             WHITE),
        ('header',         'dark cyan',       'dark blue',
         None,             'dark cyan',       DARKBLUE),
        ('general_narrow', 'white',           'dark blue',
         None,             WHITE,             DARKBLUE),
        ('general_bar',    'white',           'black',
         None,             WHITE,             BLACK),
        ('name',           'yellow, bold',    'black',
         None,             YELLOWBOLD,        BLACK),
        ('unread',         'light magenta',   'black',
         None,             LIGHTMAGENTA,      BLACK),
        ('user_active',    'light green',     'black',
         None,             LIGHTGREEN,        BLACK),
        ('user_idle',      'yellow',          'black',
         None,             YELLOW,            BLACK),
        ('user_offline',   'white',           'black',
         None,             WHITE,             BLACK),
        ('user_inactive',  'white',           'black',
         None,             WHITE,             BLACK),
        ('title',          'white, bold',     'black',
         None,             WHITEBOLD,         BLACK),
        ('time',           'light blue',      'black',
         None,             LIGHTBLUE,         BLACK),
        ('bar',            'white',           'dark gray',
         None,             WHITE,             GRAY),
        ('popup_contrast', 'black',           'dark gray',
         None,             BLACK,             GRAY),
        ('msg_emoji',      'light magenta',   'black',
         None,             LIGHTMAGENTA,   BLACK),
        ('reaction',       'light magenta, bold', 'black',
         None,             LIGHTMAGENTABOLD,   BLACK),
        ('reaction_mine',  'black',           'light magenta',
         None,             BLACK,             LIGHTMAGENTA),
        ('msg_mention',    'light red, bold', 'black',
         None,             LIGHTREDBOLD,      BLACK),
        ('msg_link',       'light blue',      'black',
         None,             LIGHTBLUE,         BLACK),
        ('msg_quote',      'brown',           'black',
         None,             'brown',           BLACK),
        ('msg_code',       'black',           'white',
         None,             BLACK,             WHITE),
        ('msg_bold',       'white, bold',     'black',
         None,             WHITEBOLD,         BLACK),
        ('footer',         'white',           'dark red',
         None,             WHITE,             DARKRED),
        ('starred',        'light red, bold', 'black',
         None,             LIGHTREDBOLD,      BLACK),
        ('popup_category', 'light blue, bold', 'black',
         None,             LIGHTBLUE,         BLACK),
        ('unread_count',   'yellow',          'black',
         None,             YELLOW,            BLACK),
        ('table_head',     'white, bold',     'black',
         None,             WHITEBOLD,         BLACK),
        ('filter_results', 'black',           'light green',
         None,             BLACK,             LIGHTGREEN),
    ],
    'zt_light': [
        (None,             'black',           'white'),
        ('selected',       'black',           'light green'),
        ('msg_selected',   'black',           'light green'),
        ('header',         'white',           'dark blue'),
        ('general_narrow', 'white',           'dark blue'),
        ('general_bar',    'dark blue',       'white'),
        ('name',           'dark green',      'white'),
        ('unread',         'dark gray',       'light gray'),
        ('user_active',    'dark green',      'white'),
        ('user_idle',      'dark blue',       'white'),
        ('user_offline',   'black',           'white'),
        ('user_inactive',  'black',           'white'),
        ('title',          'white, bold',     'dark gray'),
        ('time',           'dark blue',           'white'),
        ('bar',            'white',           'dark gray'),
        ('popup_contrast', 'white',           'dark gray'),
        ('msg_emoji',      'light magenta',   'white'),
        ('reaction',       'light magenta, bold',   'white'),
        ('reaction_mine',  'white',           'light magenta'),
        ('msg_mention',    'light red, bold', 'white'),
        ('msg_link',       'dark blue',       'white'),
        ('msg_quote',      'black',           'brown'),
        ('msg_code',       'black',           'light gray'),
        ('msg_bold',       'white, bold',     'dark gray'),
        ('footer',         'white',           'dark red'),
        ('starred',        'light red, bold', 'white'),
        ('popup_category', 'dark gray, bold', 'light gray'),
        ('unread_count',   'dark blue, bold', 'white'),
        ('table_head',     'black, bold',     'white'),
        ('filter_results', 'white',           'dark green'),
    ],
    'zt_blue': [
        (None,             'black',           'light blue'),
        ('selected',       'black',           'light gray'),
        ('msg_selected',   'black',           'light gray'),
        ('header',         'black',           'dark blue'),
        ('general_narrow', 'white',           'dark blue'),
        ('general_bar',    'dark blue',       'light blue'),
        ('name',           'dark red',        'light blue'),
        ('unread',         'light gray',      'light blue'),
        ('user_active',    'light green, bold', 'light blue'),
        ('user_idle',      'dark gray',       'light blue'),
        ('user_offline',   'black',           'light blue'),
        ('user_inactive',  'black',           'light blue'),
        ('title',          'white, bold',     'dark blue'),
        ('time',           'dark blue',       'light blue'),
        ('bar',            'white',           'dark blue'),
        ('popup_contrast', 'white',           'dark blue'),
        ('msg_emoji',      'dark magenta',   'light blue'),
        ('reaction',       'dark magenta, bold', 'light blue'),
        ('reaction_mine',  'light blue',      'dark magenta'),
        ('msg_mention',    'light red, bold', 'light blue'),
        ('msg_link',       'dark blue',       'light gray'),
        ('msg_quote',      'brown',           'dark blue'),
        ('msg_code',       'dark blue',       'white'),
        ('msg_bold',       'white, bold',     'dark blue'),
        ('footer',         'white',           'dark red'),
        ('starred',        'light red, bold', 'light blue'),
        ('popup_category', 'light gray, bold', 'light blue'),
        ('unread_count',   'yellow',          'light blue'),
        ('table_head',     'black, bold',     'light blue'),
        ('filter_results', 'white',           'dark green'),
    ]
}  # type: Dict[str, ThemeSpec]


def all_themes() -> List[str]:
    return list(THEMES.keys())


def aliased_themes() -> Dict[str, str]:
    return dict(THEME_ALIASES)


def complete_and_incomplete_themes() -> Tuple[List[str], List[str]]:
    complete = {name for name, styles in THEMES.items()
                if {s[0] for s in styles}.issuperset(required_styles)}
    incomplete = list(set(THEMES) - complete)
    return sorted(list(complete)), sorted(incomplete)


def theme_with_monochrome_added(theme: ThemeSpec) -> ThemeSpec:
    updated_theme = []
    for style in theme:
        style_name = style[0]
        if style_name not in required_styles:  # incomplete theme
            continue
        mono_style = required_styles[style_name]
        if len(style) > 4:     # 256 colors+
            new_style = style[:3] + (mono_style,) + style[4:]
        elif len(style) == 4:  # 16 colors + mono (overwrite mono)
            new_style = style[:3] + (mono_style,)
        elif len(style) == 3:  # 16 colors only
            new_style = style[:3] + (mono_style,)
        else:                  # 1-to-1 mapping (same as other style)
            new_style = style
        updated_theme.append(new_style)
    return updated_theme
