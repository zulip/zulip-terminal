from typing import Dict, List, Tuple, Optional

ThemeSpec = List[Tuple[Optional[str], ...]]

required_styles = {
    None,
    'selected',
    'msg_selected',
    'header',
    'custom',
    'content',
    'name',
    'unread',
    'active',
    'idle',
    'offline',
    'inactive',
    'title',
    'time',
    'bar',
    'emoji',
    'span',
    'link',
    'blockquote',
    'code',
    'bold',
    'footer',
    'starred',
}


# These names map to the urwid names
# (also, approximately, to the xterm colors)
C256_base = dict(
    dark_red='#800',
    brown='#880',
    dark_blue='#008',
    dark_cyan='#088',
    dark_gray='#888',
    light_red='#f00',
    light_green='#0f0',
    yellow='#ff0',
    light_blue='#00f',
    light_magenta='#f0f',
    white='#fff',
    black='#000',
)

C256 = dict(C256_base,
            **{color + ':bold': code + ', bold'
               for color, code in C256_base.items()})

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

THEMES = {
    'default': [
        (None,           'white',                'black',
         None,           C256['white'],          C256['black']),
        ('selected',     'white',                'dark blue',
         None,           C256['white'],          C256['dark_blue']),
        ('msg_selected', 'light green',          'black',
         None,           C256['light_green'],    C256['black']),
        ('header',       'dark cyan',            'dark blue',
         'bold',         C256['dark_cyan'],      C256['dark_blue']),
        ('custom',       'white',                'dark blue',
         'underline',    C256['white'],          C256['dark_blue']),
        ('content',      'white',                'black',
         'standout',     C256['white'],          C256['black']),
        ('name',         'yellow, bold',         'black',
         None,           C256['yellow:bold'],    C256['black']),
        ('unread',       'light blue',           'black',
         None,           C256['light_blue'],     C256['black']),
        ('active',       'light green',          'black',
         None,           C256['light_green'],    C256['black']),
        ('idle',         'yellow',               'black',
         None,           C256['yellow'],         C256['black']),
        ('offline',      'white',                'black',
         None,           C256['white'],          C256['black']),
        ('inactive',     'white',                'black',
         None,           C256['white'],          C256['black']),
        ('title',        'white, bold',          'black',
         None,           C256['white:bold'],     C256['black']),
        ('time',         'light blue',           'black',
         None,           C256['light_blue'],     C256['black']),
        ('bar',          'white',                'dark gray',
         None,           C256['white'],          C256['dark_gray']),
        ('emoji',        'light magenta',        'black',
         None,           C256['light_magenta'],  C256['black']),
        ('span',         'light red, bold',      'black',
         None,           C256['light_red:bold'], C256['black']),
        ('link',         'light blue',           'black',
         None,           C256['light_blue'],     C256['black']),
        ('blockquote',   'brown',                'black',
         None,           C256['brown'],          C256['black']),
        ('code',         'black',                'white',
         None,           C256['black'],          C256['white']),
        ('bold',         'white, bold',          'black',
         None,           C256['white:bold'],     C256['black']),
        ('footer',       'white',                'dark red',
         'bold',         C256['white'],          C256['dark_red']),
        ('starred',      'light red, bold',      'black',
         None,           C256['light_red:bold'], C256['black']),
    ],
    'gruvbox': [
        # default colorscheme on 16 colors, gruvbox colorscheme
        # on 256 colors
        (None,           'white',           'black',
         None,           WHITE,             BLACK),
        ('selected',     'white',           'dark blue',
         None,           WHITE,             DARKBLUE),
        ('msg_selected', 'light green',     'black',
         None,           LIGHTGREEN,        BLACK),
        ('header',       'dark cyan',       'dark blue',
         'bold',         'dark cyan',       DARKBLUE),
        ('custom',       'white',           'dark blue',
         'underline',    WHITE,             DARKBLUE),
        ('content',      'white',           'black',
         'standout',     WHITE,             BLACK),
        ('name',         'yellow, bold',    'black',
         None,           YELLOWBOLD,        BLACK),
        ('unread',       'light blue',      'black',
         None,           LIGHTBLUE,         BLACK),
        ('active',       'light green',     'black',
         None,           LIGHTGREEN,        BLACK),
        ('idle',         'yellow',          'black',
         None,           YELLOW,            BLACK),
        ('offline',      'white',           'black',
         None,           WHITE,             BLACK),
        ('inactive',     'white',           'black',
         None,           WHITE,             BLACK),
        ('title',        'white, bold',     'black',
         None,           WHITEBOLD,         BLACK),
        ('time',         'light blue',      'black',
         None,           LIGHTBLUE,         BLACK),
        ('bar',          'white',           'dark gray',
         None,           WHITE,             GRAY),
        ('emoji',        'light magenta',   'black',
         None,           'light magenta',   BLACK),
        ('span',         'light red, bold', 'black',
         None,           LIGHTREDBOLD,      BLACK),
        ('link',         'light blue',      'black',
         None,           LIGHTBLUE,         BLACK),
        ('blockquote',   'brown',           'black',
         None,           'brown',           BLACK),
        ('code',         'black',           'white',
         None,           BLACK,             WHITE),
        ('bold',         'white, bold',     'black',
         None,           WHITEBOLD,         BLACK),
        ('footer',       'white',           'dark red',
         'bold',         WHITE,             DARKRED),
        ('starred',      'light red, bold', 'black',
         None,           LIGHTREDBOLD,      BLACK),
    ],
    'light': [
        (None,           'black',           'white'),
        ('selected',     'white',           'dark blue'),
        ('msg_selected', 'black',           'light gray'),
        ('header',       'white',           'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'black',           'light gray', 'standout'),
        ('name',         'black',           'light gray', 'bold'),
        ('unread',       'dark gray',       'light gray'),
        ('active',       'light green',     'dark gray'),
        ('idle',         'yellow',          'dark gray'),
        ('offline',      'white',           'dark gray'),
        ('inactive',     'white',           'dark gray'),
        ('title',        'white, bold',     'dark gray'),
        ('time',         'white',           'dark gray'),
        ('bar',          'white',           'dark gray'),
        ('emoji',        'light magenta',   'light gray'),
        ('span',         'light red, bold', 'light gray'),
        ('link',         'dark blue',       'light gray'),
        ('blockquote',   'brown',           'dark gray'),
        ('code',         'dark gray',       'white'),
        ('bold',         'white, bold',     'dark gray'),
        ('footer',       'white',           'dark red',   'bold'),
        ('starred',      'light red, bold', 'dark gray'),
    ],
    'blue': [
        (None,           'black',           'light blue'),
        ('selected',     'white',           'dark blue'),
        ('msg_selected', 'black',           'light gray'),
        ('header',       'black',           'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'black',           'light gray', 'standout'),
        ('name',         'dark red',        'light blue', 'bold'),
        ('unread',       'light gray',      'light blue'),
        ('active',       'light green',     'dark blue'),
        ('idle',         'yellow',          'dark blue'),
        ('offline',      'white',           'dark blue'),
        ('inactive',     'white',           'dark blue'),
        ('title',        'white, bold',     'dark blue'),
        ('time',         'white',           'dark blue'),
        ('bar',          'white',           'dark blue'),
        ('emoji',        'dark magenta',   'light blue'),
        ('span',         'light red, bold', 'light blue'),
        ('link',         'dark blue',       'light gray'),
        ('blockquote',   'brown',           'dark blue'),
        ('code',         'dark blue',       'white'),
        ('bold',         'white, bold',     'dark blue'),
        ('footer',       'white',           'dark red',   'bold'),
        ('starred',      'light red, bold', 'dark blue'),
    ]
}  # type: Dict[str, ThemeSpec]


def all_themes() -> List[str]:
    return list(THEMES.keys())


def complete_and_incomplete_themes() -> Tuple[List[str], List[str]]:
    complete = {name for name, styles in THEMES.items()
                if set(s[0] for s in styles).issuperset(required_styles)}
    incomplete = list(set(THEMES) - complete)
    return sorted(list(complete)), sorted(incomplete)
