from typing import Dict, List, Optional, Tuple


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
    'reaction',
    'span',
    'link',
    'blockquote',
    'code',
    'bold',
    'footer',
    'starred',
    'category',
    'unread_count',
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
LIGHTMAGENTA = 'h132'  # neutral_purple
LIGHTMAGENTABOLD = '%s, bold' % LIGHTMAGENTA

THEMES = {
    'default': [
        (None,           'white',           ''),
        ('selected',     'white',           'dark blue'),
        ('msg_selected', 'white',           'dark blue'),
        ('header',       'dark cyan',       'dark blue', 'bold'),
        ('custom',       'white',           'dark blue', 'underline'),
        ('content',      'white',           '',          'standout'),
        ('name',         'yellow, bold',    ''),
        ('unread',       'dark blue',       ''),
        ('active',       'light green',     ''),
        ('idle',         'yellow',          ''),
        ('offline',      'white',           ''),
        ('inactive',     'white',           ''),
        ('title',        'white, bold',     ''),
        ('time',         'light blue',      ''),
        ('bar',          'white',           'dark gray'),
        ('help',         'white',           'dark gray'),
        ('emoji',        'light magenta',   ''),
        ('reaction',     'light magenta, bold', ''),
        ('span',         'light red, bold', ''),
        ('link',         'light blue',      ''),
        ('blockquote',   'brown',           ''),
        ('code',         'black',           'white'),
        ('bold',         'white, bold',     ''),
        ('footer',       'white',           'dark red',  'bold'),
        ('starred',      'light red, bold', ''),
        ('category',     'light blue, bold', ''),
        ('unread_count', 'yellow',          ''),
    ],
    'gruvbox': [
        # default colorscheme on 16 colors, gruvbox colorscheme
        # on 256 colors
        (None,           'white',           'black',
         None,           WHITE,             BLACK),
        ('selected',     'black',           'white',
         None,           BLACK,             WHITE),
        ('msg_selected', 'black',           'white',
         None,           BLACK,             WHITE),
        ('header',       'dark cyan',       'dark blue',
         'bold',         'dark cyan',       DARKBLUE),
        ('custom',       'white',           'dark blue',
         'underline',    WHITE,             DARKBLUE),
        ('content',      'white',           'black',
         'standout',     WHITE,             BLACK),
        ('name',         'yellow, bold',    'black',
         None,           YELLOWBOLD,        BLACK),
        ('unread',       'light magenta',   'black',
         None,           LIGHTMAGENTA,      BLACK),
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
         None,           LIGHTMAGENTA,   BLACK),
        ('reaction',     'light magenta, bold', 'black',
         None,           LIGHTMAGENTABOLD,   BLACK),
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
        ('category',     'light blue, bold', 'black',
         None,           LIGHTBLUE,         BLACK),
        ('unread_count', 'yellow',          'black',
         None,           YELLOW,            BLACK),
    ],
    'light': [
        (None,           'black',           'white'),
        ('selected',     'black',           'light green'),
        ('msg_selected', 'black',           'light green'),
        ('header',       'white',           'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'black',           'light gray', 'standout'),
        ('name',         'dark green',      'white', 'bold'),
        ('unread',       'dark gray',       'light gray'),
        ('active',       'dark green',      'white'),
        ('idle',         'dark blue',       'white'),
        ('offline',      'black',           'white'),
        ('inactive',     'black',           'white'),
        ('title',        'white, bold',     'dark gray'),
        ('time',         'dark blue',           'white'),
        ('bar',          'white',           'dark gray'),
        ('help',         'white',           'dark gray'),
        ('emoji',        'light magenta',   'light gray'),
        ('reaction',     'light magenta, bold',   'light gray'),
        ('span',         'light red, bold', 'light gray'),
        ('link',         'dark blue',       'light gray'),
        ('blockquote',   'black',           'brown'),
        ('code',         'dark gray',       'white'),
        ('bold',         'white, bold',     'dark gray'),
        ('footer',       'white',           'dark red',   'bold'),
        ('starred',      'light red, bold', 'white'),
        ('category',     'dark gray, bold', 'light gray'),
        ('unread_count', 'dark blue, bold', 'white'),
    ],
    'blue': [
        (None,           'black',           'light blue'),
        ('selected',     'black',           'light gray'),
        ('msg_selected', 'black',           'light gray'),
        ('header',       'black',           'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'black',           'light gray', 'standout'),
        ('name',         'dark red',        'light blue', 'bold'),
        ('unread',       'light gray',      'light blue'),
        ('active',       'light green, bold', 'light blue'),
        ('idle',         'dark gray',       'light blue'),
        ('offline',      'black',           'light blue'),
        ('inactive',     'black',           'light blue'),
        ('title',        'white, bold',     'dark blue'),
        ('time',         'dark blue',       'light blue'),
        ('bar',          'white',           'dark blue'),
        ('help',         'white',           'dark blue'),
        ('emoji',        'dark magenta',   'light blue'),
        ('reaction',     'dark magenta, bold', 'light blue'),
        ('span',         'light red, bold', 'light blue'),
        ('link',         'dark blue',       'light gray'),
        ('blockquote',   'brown',           'dark blue'),
        ('code',         'dark blue',       'white'),
        ('bold',         'white, bold',     'dark blue'),
        ('footer',       'white',           'dark red',   'bold'),
        ('starred',      'light red, bold', 'light blue'),
        ('category',     'light gray, bold', 'light blue'),
        ('unread_count', 'yellow',          'light blue'),
    ]
}  # type: Dict[str, ThemeSpec]


def all_themes() -> List[str]:
    return list(THEMES.keys())


def complete_and_incomplete_themes() -> Tuple[List[str], List[str]]:
    complete = {name for name, styles in THEMES.items()
                if set(s[0] for s in styles).issuperset(required_styles)}
    incomplete = list(set(THEMES) - complete)
    return sorted(list(complete)), sorted(incomplete)
