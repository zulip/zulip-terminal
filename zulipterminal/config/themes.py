from typing import Dict, List, Tuple, Optional

ThemeSpec = List[Tuple[Optional[str], ...]]

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
        ('selected',     'light magenta',   'dark blue'),
        ('msg_selected', 'light green',     'black'),
        ('header',       'dark cyan',       'dark blue',  'bold'),
        ('custom',       'white',           'dark blue',  'underline'),
        ('content',      'white',           'black',      'standout'),
        ('name',         'yellow, bold',    'black'),
        ('unread',       'light blue',      'black'),
        ('active',       'white',           'black'),
        ('idle',         'yellow',          'black'),
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
    'gruvbox': [
        # default colorscheme on 16 colors, gruvbox colorscheme
        # on 256 colors
        (None,           'white',           'black',
         None,           WHITE,             BLACK),
        ('selected',     'light magenta',   'dark blue',
         None,           'light magenta',   DARKBLUE),
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
        ('active',       'white',           'black',
         None,           WHITE,             BLACK),
        ('idle',         'yellow',          'black',
         None,           YELLOW,            BLACK),
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
        (None,           'black',        'white'),
        ('selected',     'white',        'dark blue'),
        ('msg_selected', 'dark blue',    'light gray'),
        ('header',       'white',        'dark blue',  'bold'),
        ('custom',       'white',        'dark blue',  'underline'),
        ('content',      'black',        'light gray', 'standout'),
        ('name',         'dark magenta', 'light gray', 'bold'),
    ],
    'blue': [
        (None,           'black',        'light blue'),
        ('selected',     'white',        'dark blue'),
        ('msg_selected', 'black',        'light gray'),
        ('header',       'black',        'dark blue',  'bold'),
        ('custom',       'white',        'dark blue',  'underline'),
        ('content',      'black',        'light gray', 'standout'),
        ('name',         'dark red',     'light gray', 'bold'),
    ]
}  # type: Dict[str, ThemeSpec]
