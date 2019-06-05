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
    'help',
    'emoji',
    'span',
    'link',
    'blockquote',
    'code',
    'bold',
    'footer',
    'starred',
}

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
        (None,           'white',           ''),
        ('selected',     'white',           'dark blue'),
        ('msg_selected', 'light green',     ''),
        ('header',       'dark cyan',       'dark blue', 'bold'),
        ('custom',       'white',           'dark blue', 'underline'),
        ('content',      'white',           '',          'standout'),
        ('name',         'yellow, bold',    ''),
        ('unread',       'light blue',      ''),
        ('active',       'light green',     ''),
        ('idle',         'yellow',          ''),
        ('offline',      'white',           ''),
        ('inactive',     'white',           ''),
        ('title',        'white, bold',     ''),
        ('time',         'light blue',      ''),
        ('bar',          'white',           'dark gray'),
        ('help',         'white',           'dark gray'),
        ('emoji',        'light magenta',   ''),
        ('span',         'light red, bold', ''),
        ('link',         'light blue',      ''),
        ('blockquote',   'brown',           ''),
        ('code',         'black',           'white'),
        ('bold',         'white, bold',     ''),
        ('footer',       'white',           'dark red',  'bold'),
        ('starred',      'light red, bold', ''),
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
        ('help',         'black',           'dark gray',
         None,           BLACK,             GRAY),
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
        ('help',         'white',           'dark gray'),
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
        ('help',         'white',           'dark gray'),
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
