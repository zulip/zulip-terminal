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

SOLAR_BASE = dict(
    # Base03='#002b36',
    # Base02='#073642',
    # Base01='#586e75',
    # Base00='#657b83',
    # Base0='#839496',
    # Base1='#93a1a1',
    # Base2='#eee8d5',
    # Base3='#fdf6e3',
    # Yellow='#b58900',
    # Orange='#cb4b16',
    # Red='#dc322f',
    # Magenta='#d33682',
    # Violet='#6c71c4',
    # Blue='#268bd2',
    # Cyan='#2aa198',
    # Green='#859900',

    # Base03='#023',
    # Base02='#034',
    # Base01='#567',
    # Base00='#678',
    # Base0='#899',
    # Base1='#9aa',
    # Base2='#eed',
    # Base3='#ffe',
    # Yellow='#b80',
    # Orange='#c41',
    # Red='#d32',
    # Magenta='#d38',
    # Violet='#67c',
    # Blue='#28d',
    # Cyan='#2a9',
    # Green='#890',
# base03='#1c1c1c',
# base02='#262626',
# base01='#585858',
# base00='#626262',
# base0='#808080',
# base1='#8a8a8a',
# base2='#e4e4e4',
# base3='#ffffd7',
# yellow='#af8700',
# orange='#d75f00',
# red='#d70000',
# magenta='#af005f',
# violet=	'#5f5faf',
# blue='#0087ff',
# cyan='#00afaf',
# green='#5f8700',

Base03='#111',
Base02='#222',
Base01='#555',
Base00='#666',
Base0='#888',
Base1='#888',
Base2='#eee',
Base3='#ffd',
Yellow='#a80',
Orange='#d50',
Red='#d00',
Magenta='#a05',
Violet=	'#55a',
Blue='#08f',
Cyan='#0aa',
Green='#580',
)

SOLAR = dict(SOLAR_BASE,
             **{color + ':bold': code + ', bold'
                for color, code in SOLAR_BASE.items()})

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
        (None,           'white',           'black'),
        ('selected',     'white',           'dark blue'),
        ('msg_selected', 'light green',     'black'),
        ('header',       'dark cyan',       'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'white',           'black',      'standout'),
        ('name',         'yellow, bold',    'black'),
        ('unread',       'light blue',      'black'),
        ('active',       'light green',     'black'),
        ('idle',         'yellow',          'black'),
        ('offline',      'white',           'black'),
        ('inactive',     'white',           'black'),
        ('title',        'white, bold',     'black'),
        ('time',         'light blue',      'black'),
        ('bar',          'white',           'dark gray'),
        ('emoji',        'light magenta',   'black'),
        ('span',         'light red, bold', 'black'),
        ('link',         'light blue',      'black'),
        ('blockquote',   'brown',           'black'),
        ('code',         'black',           'white'),
        ('bold',         'white, bold',     'black'),
        ('footer',       'white',           'dark red',   'bold'),
        ('starred',      'light red, bold', 'black'),
    ],
# white -> Base0
# black -> Base03
# dark blue -> Blue
# light green -> Green
# dark cyan -> Base0 FIXME?
# yellow -> Yellow
# light blue -> Cyan
# dark gray -> Base01
# light magenta -> Magenta
# light red -> Red
# dark red -> Violet FIXME?
# brown -> Orange
    'solar_dark': [
        (None,           'white',                'black',
         None,           SOLAR['Base0'],          SOLAR['Base03']),
        ('selected',     'white',                'dark blue',
         None,           SOLAR['Base03'],          SOLAR['Blue']),  # black/blue
        ('msg_selected', 'light green',          'black',
         None,           SOLAR['Blue:bold'],    SOLAR['Base03']),  # blue/black
        ('header',       'dark cyan',            'dark blue',
         'bold',         SOLAR['Base0'],      SOLAR['Blue']),  # FIXME dark cyan?
        ('custom',       'white',                'dark blue',
         'underline',    SOLAR['Base03'],          SOLAR['Blue']),  # black/blue
        ('content',      'white',                'black',
         'standout',     SOLAR['Base0'],          SOLAR['Base03']),
        ('name',         'yellow, bold',         'black',
         None,           SOLAR['Yellow:bold'],    SOLAR['Base03']),
        ('unread',       'light blue',           'black',
         None,           SOLAR['Green:bold'],     SOLAR['Base03']),
        ('active',       'light green',          'black',
         None,           SOLAR['Green'],    SOLAR['Base03']),
        ('idle',         'yellow',               'black',
         None,           SOLAR['Yellow'],         SOLAR['Base03']),
        ('offline',      'white',                'black',
         None,           SOLAR['Base0'],          SOLAR['Base03']),
        ('inactive',     'white',                'black',
         None,           SOLAR['Base0'],          SOLAR['Base03']),
        ('title',        'white, bold',          'black',
         None,           SOLAR['Base0:bold'],     SOLAR['Base03']),
        ('time',         'light blue',           'black',
         None,           SOLAR['Cyan'],     SOLAR['Base03']),
        ('bar',          'white',                'dark gray',
         None,           SOLAR['Base0'],          SOLAR['Base01']),
        ('emoji',        'light magenta',        'black',
         None,           SOLAR['Magenta'],  SOLAR['Base03']),
        ('span',         'light red, bold',      'black',
         None,           SOLAR['Red:bold'], SOLAR['Base03']),
        ('link',         'light blue',           'black',
         None,           SOLAR['Cyan'],     SOLAR['Base03']),
        ('blockquote',   'brown',                'black',
         None,           SOLAR['Orange'],          SOLAR['Base03']),
        ('code',         'black',                'white',
         None,           SOLAR['Base03'],          SOLAR['Base0']),
        ('bold',         'white, bold',          'black',
         None,           SOLAR['Base0:bold'],     SOLAR['Base03']),
        ('footer',       'white',                'dark red',
         'bold',         SOLAR['Base03'],          SOLAR['Violet']),  # black/violet
        ('starred',      'light red, bold',      'black',
         None,           SOLAR['Red:bold'], SOLAR['Base03']),
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
