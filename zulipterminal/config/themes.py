from typing import Dict, List, Tuple, Optional

ThemeSpec = List[Tuple[Optional[str], ...]]

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
