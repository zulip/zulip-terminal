from typing import Set, Dict, List
from collections import OrderedDict
from mypy_extensions import TypedDict

KeyBinding = TypedDict('KeyBinding', {
    'keys': Set[str],
    'help_text': str,
    'excluded_from_random_tips': bool,
}, total=False)

KEY_BINDINGS = OrderedDict([
    ('HELP', {
        'keys': {'?'},
        'help_text': 'Show/hide help menu',
        'excluded_from_random_tips': True,
    }),
    ('GO_BACK', {
        'keys': {'esc'},
        'help_text': 'Go Back',
        'excluded_from_random_tips': False,
    }),
    ('PREVIOUS_MESSAGE', {
        'keys': {'k', 'up'},
        'help_text': 'Previous message',
    }),
    ('NEXT_MESSAGE', {
        'keys': {'j', 'down'},
        'help_text': 'Next message',
    }),
    ('GO_LEFT', {
        'keys': {'h', 'left'},
        'help_text': 'Go left',
    }),
    ('GO_RIGHT', {
        'keys': {'l', 'right'},
        'help_text': 'Go right',
    }),
    ('SCROLL_TO_TOP', {
        'keys': {'K', 'page up'},
        'help_text': 'Scroll to top',
    }),
    ('SCROLL_TO_BOTTOM', {
        'keys': {'J', 'page down'},
        'help_text': 'Scroll to bottom',
    }),
    ('END_MESSAGE', {
        'keys': {'G', 'end'},
        'help_text': 'Go to last message in view',
    }),
    ('REPLY_MESSAGE', {
        'keys': {'r', 'enter'},
        'help_text': 'Reply to the current message',
    }),
    ('MENTION_REPLY', {
        'keys': {'@'},
        'help_text': 'Reply mentioning the sender of the current message'
    }),
    ('QUOTE_REPLY', {
        'keys': {'>'},
        'help_text': 'Reply quoting the current message text',
    }),
    ('REPLY_AUTHOR', {
        'keys': {'R'},
        'help_text': 'Reply privately to the sender of the current message',
    }),
    ('EDIT_MESSAGE', {
        'keys': {'e'},
        'help_text': "Edit current message's text or topic",
    }),
    ('STREAM_MESSAGE', {
        'keys': {'c'},
        'help_text': 'New message to a stream',
    }),
    ('PRIVATE_MESSAGE', {
        'keys': {'x'},
        'help_text': 'New message to a person or group of people',
    }),
    ('TAB', {
        'keys': {'tab'},
        'help_text': 'Toggle focus box in compose box'
    }),
    ('SEND_MESSAGE', {
        'keys': {'meta enter', 'ctrl d'},
        'help_text': 'Send a message',
    }),
    ('STREAM_NARROW', {
        'keys': {'s'},
        'help_text': 'Narrow to the stream of the current message',
    }),
    ('TOPIC_NARROW', {
        'keys': {'S'},
        'help_text': 'Narrow to the topic of the current message',
    }),
    ('TOGGLE_NARROW', {
        'keys': {'z'},
        'help_text':
            'Narrow to a topic/private-chat, or stream/all-private-messages',
    }),
    ('TOGGLE_TOPIC', {
        'keys': {'t'},
        'help_text': 'Toggle topics in a stream',
    }),
    ('ALL_PM', {
        'keys': {'P'},
        'help_text': 'Narrow to all private messages',
    }),
    ('ALL_STARRED', {
        'keys': {'f'},
        'help_text': 'Narrow to all starred messages',
    }),
    ('NEXT_UNREAD_TOPIC', {
        'keys': {'n'},
        'help_text': 'Next unread topic',
    }),
    ('NEXT_UNREAD_PM', {
        'keys': {'p'},
        'help_text': 'Next unread private message',
    }),
    ('SEARCH_PEOPLE', {
        'keys': {'w'},
        'help_text': 'Search users',
    }),
    ('SEARCH_MESSAGES', {
        'keys': {'/'},
        'help_text': 'Search Messages',
    }),
    ('SEARCH_STREAMS', {
        'keys': {'q'},
        'help_text': 'Search Streams',
    }),
    ('TOGGLE_MUTE_STREAM', {
        'keys': {'m'},
        'help_text': 'Mute/unmute Streams'
    }),
    ('ENTER', {
        'keys': {'enter'},
        'help_text': 'Perform current action',
    }),
    ('THUMBS_UP', {
        'keys': {'+'},
        'help_text': 'Add/remove thumbs-up reaction to the current message',
    }),
    ('TOGGLE_STAR_STATUS', {
        'keys': {'ctrl s', '*'},
        'help_text': 'Add/remove star status of the current message',
    }),
    ('MSG_INFO', {
        'keys': {'i'},
        'help_text': 'View message information',
    }),
    ('QUIT', {
        'keys': {'ctrl c'},
        'help_text': 'Quit',
    }),
    ('BEGINNING_OF_LINE', {
        'keys': {'ctrl a'},
        'help_text': 'Jump to the beginning of the line',
    }),
    ('END_OF_LINE', {
        'keys': {'ctrl e'},
        'help_text': 'Jump to the end of the line',
    }),
    ('ONE_WORD_BACKWARD', {
        'keys': {'meta b'},
        'help_text': 'Jump backward one word',
    }),
    ('ONE_WORD_FORWARD', {
        'keys': {'meta f'},
        'help_text': 'Jump forward one word',
    }),
    ('CUT_TO_END_OF_LINE', {
        'keys': {'ctrl k'},
        'help_text': 'Cut forward to the end of the line',
    }),
    ('CUT_TO_START_OF_LINE', {
        'keys': {'ctrl u'},
        'help_text': 'Cut backward to the start of the line',
    }),
    ('CUT_TO_END_OF_WORD', {
        'keys': {'meta d'},
        'help_text': 'Cut forward to the end of the current word',
    }),
    ('CUT_TO_START_OF_WORD', {
        'keys': {'ctrl w'},
        'help_text': 'Cut backward to the start of the current word',
    }),
    ('PREV_LINE', {
        'keys': {'ctrl p', 'up'},
        'help_text': 'Jump to the previous line',
    }),
    ('NEXT_LINE', {
        'keys': {'ctrl n', 'down'},
        'help_text': 'Jump to the next line',
    }),
    ('CLEAR_MESSAGE', {
        'keys': {'ctrl l'},
        'help_text': 'Clear message',
    }),
])  # type: OrderedDict[str, KeyBinding]


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


def commands_for_random_tips() -> List[KeyBinding]:
    """
    Return list of commands which may be displayed as a random tip
    """
    return [key_binding for key_binding in KEY_BINDINGS.values()
            if not key_binding.get('excluded_from_random_tips', False)]
