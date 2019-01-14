from typing import Set

KEY_BINDINGS = {
    'HELP': {
        'keys': {'?'},
        'help_text': 'Display help menu',
    },
    'GO_BACK': {
        'keys': {'esc'},
        'help_text': 'Go Back',
    },
    'PREVIOUS_MESSAGE': {
        'keys': {'k', 'up'},
        'help_text': 'Previous message',
    },
    'NEXT_MESSAGE': {
        'keys': {'j', 'down'},
        'help_text': 'Next message',
    },
    'GO_LEFT': {
        'keys': {'h', 'left'},
        'help_text': 'Go left',
    },
    'GO_RIGHT': {
        'keys': {'l', 'right'},
        'help_text': 'Go right',
    },
    'SCROLL_TO_TOP': {
        'keys': {'K', 'page up'},
        'help_text': 'Scroll to top',
    },
    'SCROLL_TO_BOTTOM': {
        'keys': {'J', 'page down'},
        'help_text': 'Scroll to bottom',
    },
    'END_MESSAGE': {
        'keys': {'G', 'end'},
        'help_text': 'Go to last message in view',
    },
    'REPLY_MESSAGE': {
        'keys': {'r', 'enter'},
        'help_text': 'Reply to the current message',
    },
    'MENTION_REPLY': {
        'keys': {'@'},
        'help_text': 'Reply mentioning the sender of the current message'
    },
    'QUOTE_REPLY': {
        'keys': {'>'},
        'help_text': 'Reply quoting the current message text',
    },
    'REPLY_AUTHOR': {
        'keys': {'R'},
        'help_text': 'Reply privately to the sender of the current message',
    },
    'STREAM_MESSAGE': {
        'keys': {'c'},
        'help_text': 'New message to a stream',
    },
    'PRIVATE_MESSAGE': {
        'keys': {'x'},
        'help_text': 'New message to a person or group of people',
    },
    'TAB': {
        'keys': {'tab'},
        'help_text': 'Toggle focus box in compose box'
    },
    'SEND_MESSAGE': {
        'keys': {'meta enter', 'ctrl d'},
        'help_text': 'Send a message',
    },
    'STREAM_NARROW': {
        'keys': {'s'},
        'help_text': 'Narrow to the stream of the current message',
    },
    'TOPIC_NARROW': {
        'keys': {'S'},
        'help_text': 'Narrow to the topic of the current message',
    },
    'ALL_PM': {
        'keys': {'P'},
        'help_text': 'Narrow to all private messages',
    },
    'ALL_STARRED': {
        'keys': {'f'},
        'help_text': 'Narrow to all starred messages',
    },
    'NEXT_UNREAD_TOPIC': {
        'keys': {'n'},
        'help_text': 'Next unread topic',
    },
    'NEXT_UNREAD_PM': {
        'keys': {'p'},
        'help_text': 'Next unread private message',
    },
    'SEARCH_PEOPLE': {
        'keys': {'w'},
        'help_text': 'Search People',
    },
    'SEARCH_MESSAGES': {
        'keys': {'/'},
        'help_text': 'Search Messages',
    },
    'SEARCH_STREAMS': {
        'keys': {'q'},
        'help_text': 'Search Streams',
    },
    'ENTER': {
        'keys': {'enter'},
        'help_text': 'Perform current action',
    },
    'THUMBS_UP': {
        'keys': {'+'},
        'help_text': 'Add/remove thumbs-up reaction to the current message',
    },
    'TOGGLE_STAR_STATUS': {
        'keys': {'ctrl s', '*'},
        'help_text': 'Add/remove star status of the current message',
    },
}


class InvalidCommand(Exception):
    pass


def is_command_key(command: str, key: str) -> bool:
    """
    Returns the mapped binding for a key if mapped
    or the key otherwise.
    """
    try:
        return key in KEY_BINDINGS[command]['keys']
    except KeyError as exception:
        raise InvalidCommand(command)


def keys_for_command(command: str) -> Set[str]:
    """
    Returns the actual keys for a given mapped command
    """
    try:
        return set(KEY_BINDINGS[command]['keys'])
    except KeyError as exception:
        raise InvalidCommand(command)
