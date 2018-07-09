KEY_BINDINGS = {
    'k':
        ('up', 'scroll up'),
    'j':
        ('down', 'scroll down'),
    'h':
        ('left', 'Go left'),
    'l':
        ('right', 'Go right'),
    'K':
        ('page up', 'scroll to top'),
    'J':
        ('page down', 'scroll to bottom'),
    'G':
        ('end', 'Go to last message in view'),
    'x':
        ('x', 'New private message'),
}


def get_key(key: str) -> str:
    """
    Returns the mapped binding for a key if mapped
    or the key otherwise.
    """
    return KEY_BINDINGS.get(key, (key,))[0]
