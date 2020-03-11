from collections import OrderedDict
from typing import Dict, List, Set

from mypy_extensions import TypedDict


KeyBinding = TypedDict('KeyBinding', {
    'keys': Set[str],
    'help_text': str,
    'excluded_from_random_tips': bool,
    'key_category': str,
}, total=False)

KEY_BINDINGS = OrderedDict([
    ('HELP', {
        'keys': {'?'},
        'help_text': 'Show/hide help menu',
        'excluded_from_random_tips': True,
        'key_category': 'general',
    }),
    ('GO_BACK', {
        'keys': {'esc'},
        'help_text': 'Go Back',
        'excluded_from_random_tips': False,
        'key_category': 'general',
    }),
    ('GO_UP', {
        'keys': {'k', 'up'},
        'help_text': 'Go up/Previous message',
        'key_category': 'navigation',
    }),
    ('GO_DOWN', {
        'keys': {'j', 'down'},
        'help_text': 'Go down/Next message',
        'key_category': 'navigation',
    }),
    ('GO_LEFT', {
        'keys': {'h', 'left'},
        'help_text': 'Go left',
        'key_category': 'navigation',
    }),
    ('GO_RIGHT', {
        'keys': {'l', 'right'},
        'help_text': 'Go right',
        'key_category': 'navigation',
    }),
    ('SCROLL_UP', {
        'keys': {'K', 'page up'},
        'help_text': 'Scroll up',
        'key_category': 'navigation',
    }),
    ('SCROLL_DOWN', {
        'keys': {'J', 'page down'},
        'help_text': 'Scroll down',
        'key_category': 'navigation',
    }),
    ('GO_TO_BOTTOM', {
        'keys': {'G', 'end'},
        'help_text': 'Go to bottom/last message in view',
        'key_category': 'navigation',
    }),
    ('REPLY_MESSAGE', {
        'keys': {'r', 'enter'},
        'help_text': 'Reply to the current message',
        'key_category': 'msg_actions',
    }),
    ('MENTION_REPLY', {
        'keys': {'@'},
        'help_text': 'Reply mentioning the sender of the current message',
        'key_category': 'msg_actions',
    }),
    ('QUOTE_REPLY', {
        'keys': {'>'},
        'help_text': 'Reply quoting the current message text',
        'key_category': 'msg_actions',
    }),
    ('REPLY_AUTHOR', {
        'keys': {'R'},
        'help_text': 'Reply privately to the sender of the current message',
        'key_category': 'msg_actions',
    }),
    ('EDIT_MESSAGE', {
        'keys': {'e'},
        'help_text': "Edit current message's text or topic",
        'key_category': 'msg_actions'
    }),
    ('STREAM_MESSAGE', {
        'keys': {'c'},
        'help_text': 'New message to a stream',
        'key_category': 'msg_actions',
    }),
    ('PRIVATE_MESSAGE', {
        'keys': {'x'},
        'help_text': 'New message to a person or group of people',
        'key_category': 'msg_actions',
    }),
    ('TAB', {
        'keys': {'tab'},
        'help_text': 'Toggle focus box in compose box',
        'key_category': 'msg_compose',
    }),
    ('SEND_MESSAGE', {
        'keys': {'meta enter', 'ctrl d'},
        'help_text': 'Send a message',
        'key_category': 'msg_compose',
    }),
    ('AUTOCOMPLETE', {
        'keys': {'ctrl f'},
        'help_text': 'Autocomplete @mentions and #stream_names',
        'key_category': 'msg_compose',
    }),
    ('AUTOCOMPLETE_REVERSE', {
        'keys': {'ctrl r'},
        'help_text': 'Cycle through autocomplete suggestions in reverse',
        'key_category': 'msg_compose',
    }),
    ('STREAM_NARROW', {
        'keys': {'s'},
        'help_text': 'Narrow to the stream of the current message',
        'key_category': 'msg_actions',
    }),
    ('TOPIC_NARROW', {
        'keys': {'S'},
        'help_text': 'Narrow to the topic of the current message',
        'key_category': 'msg_actions',
    }),
    ('TOGGLE_NARROW', {
        'keys': {'z'},
        'help_text':
            'Narrow to a topic/private-chat, or stream/all-private-messages',
        'key_category': 'msg_actions',
    }),
    ('TOGGLE_TOPIC', {
        'keys': {'t'},
        'help_text': 'Toggle topics in a stream',
        'key_category': 'stream_list',
    }),
    ('ALL_PM', {
        'keys': {'P'},
        'help_text': 'Narrow to all private messages',
        'key_category': 'navigation',
    }),
    ('ALL_STARRED', {
        'keys': {'f'},
        'help_text': 'Narrow to all starred messages',
        'key_category': 'navigation',
    }),
    ('ALL_MENTIONS', {
        'keys': {'#'},
        'help_text': "Narrow to messages in which you're mentioned",
        'key_category': 'navigation',
    }),
    ('NEXT_UNREAD_TOPIC', {
        'keys': {'n'},
        'help_text': 'Next unread topic',
        'key_category': 'navigation',
    }),
    ('NEXT_UNREAD_PM', {
        'keys': {'p'},
        'help_text': 'Next unread private message',
        'key_category': 'navigation',
    }),
    ('SEARCH_PEOPLE', {
        'keys': {'w'},
        'help_text': 'Search users',
        'key_category': 'searching',
    }),
    ('SEARCH_MESSAGES', {
        'keys': {'/'},
        'help_text': 'Search Messages',
        'key_category': 'searching',
    }),
    ('SEARCH_STREAMS', {
        'keys': {'q'},
        'help_text': 'Search Streams',
        'key_category': 'searching',
    }),
    ('SEARCH_TOPICS', {
        'keys': {'q'},
        'help_text': 'Search topics in a stream',
        'key_category': 'searching',
    }),
    ('TOGGLE_MUTE_STREAM', {
        'keys': {'m'},
        'help_text': 'Mute/unmute Streams',
        'key_category': 'stream_list',
    }),
    ('ENTER', {
        'keys': {'enter'},
        'help_text': 'Perform current action',
        'key_category': 'navigation',
    }),
    ('THUMBS_UP', {
        'keys': {'+'},
        'help_text': 'Add/remove thumbs-up reaction to the current message',
        'key_category': 'msg_actions',
    }),
    ('TOGGLE_STAR_STATUS', {
        'keys': {'ctrl s', '*'},
        'help_text': 'Add/remove star status of the current message',
        'key_category': 'msg_actions',
    }),
    ('MSG_INFO', {
        'keys': {'i'},
        'help_text': 'View message information',
        'key_category': 'msg_actions',
    }),
    ('STREAM_DESC', {
        'keys': {'i'},
        'help_text': 'View stream description',
        'key_category': 'stream_list',
    }),
    ('REDRAW', {
        'keys': {'ctrl l'},
        'help_text': 'Redraw screen',
        'key_category': 'general',
    }),
    ('QUIT', {
        'keys': {'ctrl c'},
        'help_text': 'Quit',
        'key_category': 'general',
    }),
    ('BEGINNING_OF_LINE', {
        'keys': {'ctrl a'},
        'help_text': 'Jump to the beginning of the line',
        'key_category': 'msg_compose',
    }),
    ('END_OF_LINE', {
        'keys': {'ctrl e'},
        'help_text': 'Jump to the end of the line',
        'key_category': 'msg_compose',
    }),
    ('ONE_WORD_BACKWARD', {
        'keys': {'meta b'},
        'help_text': 'Jump backward one word',
        'key_category': 'msg_compose',
    }),
    ('ONE_WORD_FORWARD', {
        'keys': {'meta f'},
        'help_text': 'Jump forward one word',
        'key_category': 'msg_compose',
    }),
    ('CUT_TO_END_OF_LINE', {
        'keys': {'ctrl k'},
        'help_text': 'Cut forward to the end of the line',
        'key_category': 'msg_compose',
    }),
    ('CUT_TO_START_OF_LINE', {
        'keys': {'ctrl u'},
        'help_text': 'Cut backward to the start of the line',
        'key_category': 'msg_compose',
    }),
    ('CUT_TO_END_OF_WORD', {
        'keys': {'meta d'},
        'help_text': 'Cut forward to the end of the current word',
        'key_category': 'msg_compose',
    }),
    ('CUT_TO_START_OF_WORD', {
        'keys': {'ctrl w'},
        'help_text': 'Cut backward to the start of the current word',
        'key_category': 'msg_compose',
    }),
    ('PREV_LINE', {
        'keys': {'ctrl p', 'up'},
        'help_text': 'Jump to the previous line',
        'key_category': 'msg_compose',
    }),
    ('NEXT_LINE', {
        'keys': {'ctrl n', 'down'},
        'help_text': 'Jump to the next line',
        'key_category': 'msg_compose',
    }),
    ('CLEAR_MESSAGE', {
        'keys': {'ctrl l'},
        'help_text': 'Clear compose screen',
        'key_category': 'msg_compose',
    }),
])  # type: OrderedDict[str, KeyBinding]

HELP_CATEGORIES = OrderedDict([
    ('general', 'General'),
    ('navigation', 'Navigation'),
    ('searching', 'Searching'),
    ('msg_actions', 'Actions for the selected message'),
    ('stream_list', 'Stream list actions'),
    ('msg_compose', 'Composing a Message'),
])


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
