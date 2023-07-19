"""
Keybindings and their helper functions
"""

from typing import Dict, List

from typing_extensions import NotRequired, TypedDict
from urwid.command_map import (
    CURSOR_DOWN,
    CURSOR_LEFT,
    CURSOR_MAX_RIGHT,
    CURSOR_PAGE_DOWN,
    CURSOR_PAGE_UP,
    CURSOR_RIGHT,
    CURSOR_UP,
    command_map,
)


class KeyBinding(TypedDict):
    keys: List[str]
    help_text: str
    excluded_from_random_tips: NotRequired[bool]
    key_category: str


# fmt: off
KEY_BINDINGS: Dict[str, KeyBinding] = {
    # Key that is displayed in the UI is determined by the method
    # primary_key_for_command. (Currently the first key in the list)

    'HELP': {
        'keys': ['?'],
        'help_text': 'Show/hide help menu',
        'excluded_from_random_tips': True,
        'key_category': 'general',
    },
    'MARKDOWN_HELP': {
        'keys': ['meta m'],
        'help_text': 'Show/hide markdown help menu',
        'key_category': 'general',
    },
    'ABOUT': {
        'keys': ['meta ?'],
        'help_text': 'Show/hide about menu',
        'key_category': 'general',
    },
    'GO_BACK': {
        'keys': ['esc'],
        'help_text': 'Go Back',
        'excluded_from_random_tips': False,
        'key_category': 'general',
    },
    'OPEN_DRAFT': {
        'keys': ['d'],
        'help_text': 'Open draft message saved in this session',
        'key_category': 'general',
    },
    'GO_UP': {
        'keys': ['up', 'k'],
        'help_text': 'Go up / Previous message',
        'key_category': 'navigation',
    },
    'GO_DOWN': {
        'keys': ['down', 'j'],
        'help_text': 'Go down / Next message',
        'key_category': 'navigation',
    },
    'GO_LEFT': {
        'keys': ['left', 'h'],
        'help_text': 'Go left',
        'key_category': 'navigation',
    },
    'GO_RIGHT': {
        'keys': ['right', 'l'],
        'help_text': 'Go right',
        'key_category': 'navigation',
    },
    'SCROLL_UP': {
        'keys': ['page up', 'K'],
        'help_text': 'Scroll up',
        'key_category': 'navigation',
    },
    'SCROLL_DOWN': {
        'keys': ['page down', 'J'],
        'help_text': 'Scroll down',
        'key_category': 'navigation',
    },
    'GO_TO_BOTTOM': {
        'keys': ['end', 'G'],
        'help_text': 'Go to bottom / Last message',
        'key_category': 'navigation',
    },
    'REPLY_MESSAGE': {
        'keys': ['r', 'enter'],
        'help_text': 'Reply to the current message',
        'key_category': 'msg_actions',
    },
    'MENTION_REPLY': {
        'keys': ['@'],
        'help_text': 'Reply mentioning the sender of the current message',
        'key_category': 'msg_actions',
    },
    'QUOTE_REPLY': {
        'keys': ['>'],
        'help_text': 'Reply quoting the current message text',
        'key_category': 'msg_actions',
    },
    'REPLY_AUTHOR': {
        'keys': ['R'],
        'help_text': 'Reply directly to the sender of the current message',
        'key_category': 'msg_actions',
    },
    'EDIT_MESSAGE': {
        'keys': ['e'],
        'help_text': "Edit message's content or topic",
        'key_category': 'msg_actions'
    },
    'STREAM_MESSAGE': {
        'keys': ['c'],
        'help_text': 'New message to a stream',
        'key_category': 'msg_actions',
    },
    'PRIVATE_MESSAGE': {
        'keys': ['x'],
        'help_text': 'New message to a person or group of people',
        'key_category': 'msg_actions',
    },
    'FILE_UPLOAD': {
        'keys': ['ctrl o'],
        'help_text': 'Upload file',
        'key_category': 'msg_compose',
    },
    'CYCLE_COMPOSE_FOCUS': {
        'keys': ['tab'],
        'help_text': 'Cycle through recipient and content boxes',
        'key_category': 'msg_compose',
    },
    'SEND_MESSAGE': {
        'keys': ['ctrl d', 'meta enter'],
        'help_text': 'Send a message',
        'key_category': 'msg_compose',
    },
    'SAVE_AS_DRAFT': {
        'keys': ['meta s'],
        'help_text': 'Save current message as a draft',
        'key_category': 'msg_compose',
    },
    'AUTOCOMPLETE': {
        'keys': ['ctrl f'],
        'help_text': ('Autocomplete @mentions, #stream_names, :emoji:'
                      ' and topics'),
        'key_category': 'msg_compose',
    },
    'AUTOCOMPLETE_REVERSE': {
        'keys': ['ctrl r'],
        'help_text': 'Cycle through autocomplete suggestions in reverse',
        'key_category': 'msg_compose',
    },
    'ADD_REACTION': {
        'keys': [':'],
        'help_text': 'Show/hide Emoji picker popup for current message',
        'key_category': 'msg_actions',
    },
    'STREAM_NARROW': {
        'keys': ['s'],
        'help_text': 'Narrow to the stream of the current message',
        'key_category': 'msg_actions',
    },
    'TOPIC_NARROW': {
        'keys': ['S'],
        'help_text': 'Narrow to the topic of the current message',
        'key_category': 'msg_actions',
    },
    'NARROW_MESSAGE_RECIPIENT': {
        'keys': ['meta .'],
        'help_text': 'Narrow to compose box message recipient',
        'key_category': 'msg_compose',
    },
    'TOGGLE_NARROW': {
        'keys': ['z'],
        'help_text':
            'Narrow to a topic/direct-chat, or stream/all-direct-messages',
        'key_category': 'msg_actions',
    },
    'TOGGLE_TOPIC': {
        'keys': ['t'],
        'help_text': 'Toggle topics in a stream',
        'key_category': 'stream_list',
    },
    'ALL_MESSAGES': {
        'keys': ['a', 'esc'],
        'help_text': 'Narrow to all messages',
        'key_category': 'navigation',
    },
    'ALL_PM': {
        'keys': ['P'],
        'help_text': 'Narrow to all direct messages',
        'key_category': 'navigation',
    },
    'ALL_STARRED': {
        'keys': ['f'],
        'help_text': 'Narrow to all starred messages',
        'key_category': 'navigation',
    },
    'ALL_MENTIONS': {
        'keys': ['#'],
        'help_text': "Narrow to messages in which you're mentioned",
        'key_category': 'navigation',
    },
    'NEXT_UNREAD_TOPIC': {
        'keys': ['n'],
        'help_text': 'Next unread topic',
        'key_category': 'navigation',
    },
    'NEXT_UNREAD_PM': {
        'keys': ['p'],
        'help_text': 'Next unread direct message',
        'key_category': 'navigation',
    },
    'SEARCH_PEOPLE': {
        'keys': ['w'],
        'help_text': 'Search Users',
        'key_category': 'searching',
    },
    'SEARCH_MESSAGES': {
        'keys': ['/'],
        'help_text': 'Search Messages',
        'key_category': 'searching',
    },
    'SEARCH_STREAMS': {
        'keys': ['q'],
        'help_text': 'Search Streams',
        'key_category': 'searching',
    },
    'SEARCH_TOPICS': {
        'keys': ['q'],
        'help_text': 'Search topics in a stream',
        'key_category': 'searching',
    },
    'SEARCH_EMOJIS': {
        'keys': ['p'],
        'help_text': 'Search emojis from Emoji-picker popup',
        'excluded_from_random_tips': True,
        'key_category': 'searching',
    },
    'TOGGLE_MUTE_STREAM': {
        'keys': ['m'],
        'help_text': 'Mute/unmute Streams',
        'key_category': 'stream_list',
    },
    'ENTER': {
        'keys': ['enter'],
        'help_text': 'Perform current action',
        'key_category': 'navigation',
    },
    'THUMBS_UP': {
        'keys': ['+'],
        'help_text': 'Add/remove thumbs-up reaction to the current message',
        'key_category': 'msg_actions',
    },
    'TOGGLE_STAR_STATUS': {
        'keys': ['ctrl s', '*'],
        'help_text': 'Add/remove star status of the current message',
        'key_category': 'msg_actions',
    },
    'MSG_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide message information',
        'key_category': 'msg_actions',
    },
    'MSG_SENDER_INFO': {
        'keys': ['u'],
        'help_text': 'Show/hide message sender information',
        'key_category': 'msg_actions',
    },
    'EDIT_HISTORY': {
        'keys': ['e'],
        'help_text': 'Show/hide edit history (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
    },
    'VIEW_IN_BROWSER': {
        'keys': ['v'],
        'help_text':
            'View current message in browser (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
    },
    'STREAM_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide stream information & modify settings',
        'key_category': 'stream_list',
    },
    'STREAM_MEMBERS': {
        'keys': ['m'],
        'help_text': 'Show/hide stream members (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
    },
    'COPY_STREAM_EMAIL': {
        'keys': ['c'],
        'help_text':
            'Copy stream email to clipboard (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
    },
    'REDRAW': {
        'keys': ['ctrl l'],
        'help_text': 'Redraw screen',
        'key_category': 'general',
    },
    'QUIT': {
        'keys': ['ctrl c'],
        'help_text': 'Quit',
        'key_category': 'general',
    },
    'USER_INFO': {
        'keys': ['i'],
        'help_text': 'View user information (From Users list)',
        'key_category': 'general',
    },
    'BEGINNING_OF_LINE': {
        'keys': ['ctrl a'],
        'help_text': 'Jump to the beginning of line',
        'key_category': 'msg_compose',
    },
    'END_OF_LINE': {
        'keys': ['ctrl e'],
        'help_text': 'Jump to the end of line',
        'key_category': 'msg_compose',
    },
    'ONE_WORD_BACKWARD': {
        'keys': ['meta b'],
        'help_text': 'Jump backward one word',
        'key_category': 'msg_compose',
    },
    'ONE_WORD_FORWARD': {
        'keys': ['meta f'],
        'help_text': 'Jump forward one word',
        'key_category': 'msg_compose',
    },
    'DELETE_LAST_CHARACTER': {
        'keys': ['ctrl h'],
        'help_text': 'Delete previous character (to left)',
        'key_category': 'msg_compose',
    },
    'TRANSPOSE_CHARACTERS': {
        'keys': ['ctrl t'],
        'help_text': 'Transpose characters',
        'key_category': 'msg_compose',
    },
    'CUT_TO_END_OF_LINE': {
        'keys': ['ctrl k'],
        'help_text': 'Cut forwards to the end of the line',
        'key_category': 'msg_compose',
    },
    'CUT_TO_START_OF_LINE': {
        'keys': ['ctrl u'],
        'help_text': 'Cut backwards to the start of the line',
        'key_category': 'msg_compose',
    },
    'CUT_TO_END_OF_WORD': {
        'keys': ['meta d'],
        'help_text': 'Cut forwards to the end of the current word',
        'key_category': 'msg_compose',
    },
    'CUT_TO_START_OF_WORD': {
        'keys': ['ctrl w'],
        'help_text': 'Cut backwards to the start of the current word',
        'key_category': 'msg_compose',
    },
    'PASTE_LAST_CUT': {
        'keys': ['ctrl y'],
        'help_text': 'Paste last cut section',
        'key_category': 'msg_compose',
    },
    'UNDO_LAST_ACTION': {
        'keys': ['ctrl _'],
        'help_text': 'Undo last action',
        'key_category': 'msg_compose',
    },
    'PREV_LINE': {
        'keys': ['up', 'ctrl p'],
        'help_text': 'Jump to the previous line',
        'key_category': 'msg_compose',
    },
    'NEXT_LINE': {
        'keys': ['down', 'ctrl n'],
        'help_text': 'Jump to the next line',
        'key_category': 'msg_compose',
    },
    'CLEAR_MESSAGE': {
        'keys': ['ctrl l'],
        'help_text': 'Clear compose box',
        'key_category': 'msg_compose',
    },
    'FULL_RENDERED_MESSAGE': {
        'keys': ['f'],
        'help_text': 'Show/hide full rendered message (from message information)',
        'key_category': 'msg_actions',
    },
    'FULL_RAW_MESSAGE': {
        'keys': ['r'],
        'help_text': 'Show/hide full raw message (from message information)',
        'key_category': 'msg_actions',
    },
}
# fmt: on

HELP_CATEGORIES = {
    "general": "General",
    "navigation": "Navigation",
    "searching": "Searching",
    "msg_actions": "Message actions",
    "stream_list": "Stream list actions",
    "msg_compose": "Composing a Message",
}

ZT_TO_URWID_CMD_MAPPING = {
    "GO_UP": CURSOR_UP,
    "GO_DOWN": CURSOR_DOWN,
    "GO_LEFT": CURSOR_LEFT,
    "GO_RIGHT": CURSOR_RIGHT,
    "SCROLL_UP": CURSOR_PAGE_UP,
    "SCROLL_DOWN": CURSOR_PAGE_DOWN,
    "GO_TO_BOTTOM": CURSOR_MAX_RIGHT,
}


class InvalidCommand(Exception):
    pass


def is_command_key(command: str, key: str) -> bool:
    """
    Returns the mapped binding for a key if mapped
    or the key otherwise.
    """
    try:
        return key in KEY_BINDINGS[command]["keys"]
    except KeyError as exception:
        raise InvalidCommand(command) from exception


def keys_for_command(command: str) -> List[str]:
    """
    Returns the actual keys for a given mapped command
    """
    try:
        return list(KEY_BINDINGS[command]["keys"])
    except KeyError as exception:
        raise InvalidCommand(command) from exception


def primary_key_for_command(command: str) -> str:
    """
    Primary Key is the key that will be displayed eg. in the UI
    """
    return keys_for_command(command).pop(0)


def commands_for_random_tips() -> List[KeyBinding]:
    """
    Return list of commands which may be displayed as a random tip
    """
    return [
        key_binding
        for key_binding in KEY_BINDINGS.values()
        if not key_binding.get("excluded_from_random_tips", False)
    ]


# Refer urwid/command_map.py
# Adds alternate keys for standard urwid navigational commands.
for zt_cmd, urwid_cmd in ZT_TO_URWID_CMD_MAPPING.items():
    for key in keys_for_command(zt_cmd):
        command_map[key] = urwid_cmd
