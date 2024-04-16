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
    key_context: str


# fmt: off
KEY_BINDINGS: Dict[str, KeyBinding] = {
    # Key that is displayed in the UI is determined by the method
    # primary_key_for_command. (Currently the first key in the list)

    'HELP': {
        'keys': ['?'],
        'help_text': 'Show/hide help menu',
        'excluded_from_random_tips': True,
        'key_category': 'general',
        'key_context': 'general',
    },
    'MARKDOWN_HELP': {
        'keys': ['meta m'],
        'help_text': 'Show/hide markdown help menu',
        'key_category': 'general',
        'key_context': 'general',
    },
    'ABOUT': {
        'keys': ['meta ?'],
        'help_text': 'Show/hide about menu',
        'key_category': 'general',
        'key_context': 'general',
    },
    'GO_BACK': {
        'keys': ['esc'],
        'help_text': 'Go Back',
        'excluded_from_random_tips': False,
        'key_category': 'general',
        'key_context': 'general',
    },
    'OPEN_DRAFT': {
        'keys': ['d'],
        'help_text': 'Open draft message saved in this session',
        'key_category': 'general',
        'key_context': 'general',
    },
    'GO_UP': {
        'keys': ['up', 'k'],
        'help_text': 'Go up / Previous message',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'GO_DOWN': {
        'keys': ['down', 'j'],
        'help_text': 'Go down / Next message',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'GO_LEFT': {
        'keys': ['left', 'h'],
        'help_text': 'Go left',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'GO_RIGHT': {
        'keys': ['right', 'l'],
        'help_text': 'Go right',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'SCROLL_UP': {
        'keys': ['page up', 'K'],
        'help_text': 'Scroll up',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'SCROLL_DOWN': {
        'keys': ['page down', 'J'],
        'help_text': 'Scroll down',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'GO_TO_BOTTOM': {
        'keys': ['end', 'G'],
        'help_text': 'Go to bottom / Last message',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'REPLY_MESSAGE': {
        'keys': ['r', 'enter'],
        'help_text': 'Reply to the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'MENTION_REPLY': {
        'keys': ['@'],
        'help_text': 'Reply mentioning the sender of the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'QUOTE_REPLY': {
        'keys': ['>'],
        'help_text': 'Reply quoting the current message text',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'REPLY_AUTHOR': {
        'keys': ['R'],
        'help_text': 'Reply directly to the sender of the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'EDIT_MESSAGE': {
        'keys': ['e'],
        'help_text': "Edit message's content or topic",
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'STREAM_MESSAGE': {
        'keys': ['c'],
        'help_text': 'New message to a stream',
        'key_category': 'msg_actions',
        'key_context': 'general',
    },
    'PRIVATE_MESSAGE': {
        'keys': ['x'],
        'help_text': 'New message to a person or group of people',
        'key_category': 'msg_actions',
        'key_context': 'general',
    },
    'CYCLE_COMPOSE_FOCUS': {
        'keys': ['tab'],
        'help_text': 'Cycle through recipient and content boxes',
        'key_category': 'msg_compose',
        'key_context': 'write_box',
    },
    'SEND_MESSAGE': {
        'keys': ['ctrl d', 'meta enter'],
        'help_text': 'Send a message',
        'key_category': 'msg_compose',
        'key_context': 'write_box',
    },
    'SAVE_AS_DRAFT': {
        'keys': ['meta s'],
        'help_text': 'Save current message as a draft',
        'key_category': 'msg_compose',
        'key_context': 'write_box',
    },
    'AUTOCOMPLETE': {
        'keys': ['ctrl f'],
        'help_text': ('Autocomplete @mentions, #stream_names, :emoji:'
                      ' and topics'),
        'key_category': 'msg_compose',
        'key_context': 'editor',
    },
    'AUTOCOMPLETE_REVERSE': {
        'keys': ['ctrl r'],
        'help_text': 'Cycle through autocomplete suggestions in reverse',
        'key_category': 'msg_compose',
        'key_context': 'editor',
    },
    'ADD_REACTION': {
        'keys': [':'],
        'help_text': 'Show/hide Emoji picker popup for current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'STREAM_NARROW': {
        'keys': ['s'],
        'help_text': 'Narrow to the stream of the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'TOPIC_NARROW': {
        'keys': ['S'],
        'help_text': 'Narrow to the topic of the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'NARROW_MESSAGE_RECIPIENT': {
        'keys': ['meta .'],
        'help_text': 'Narrow to compose box message recipient',
        'key_category': 'msg_compose',
        'key_context': 'write_box',
    },
    'TOGGLE_NARROW': {
        'keys': ['z'],
        'help_text':
            'Narrow to a topic/direct-chat, or stream/all-direct-messages',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'REACTION_AGREEMENT': {
        'keys': ['='],
        'help_text': 'Toggle first emoji reaction on selected message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'TOGGLE_TOPIC': {
        'keys': ['t'],
        'help_text': 'Toggle topics in a stream',
        'key_category': 'stream_list',
        'key_context': 'stream_view',
    },
    'ALL_MESSAGES': {
        'keys': ['a', 'esc'],
        'help_text': 'Narrow to all messages',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'ALL_PM': {
        'keys': ['P'],
        'help_text': 'Narrow to all direct messages',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'ALL_STARRED': {
        'keys': ['f'],
        'help_text': 'Narrow to all starred messages',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'ALL_MENTIONS': {
        'keys': ['#'],
        'help_text': "Narrow to messages in which you're mentioned",
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'NEXT_UNREAD_TOPIC': {
        'keys': ['n'],
        'help_text': 'Next unread topic',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'NEXT_UNREAD_PM': {
        'keys': ['p'],
        'help_text': 'Next unread direct message',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'SEARCH_PEOPLE': {
        'keys': ['w'],
        'help_text': 'Search Users',
        'key_category': 'searching',
        'key_context': 'general',
    },
    'SEARCH_MESSAGES': {
        'keys': ['/'],
        'help_text': 'Search Messages',
        'key_category': 'searching',
        'key_context': 'general',
    },
    'SEARCH_STREAMS': {
        'keys': ['q'],
        'help_text': 'Search Streams',
        'key_category': 'searching',
        'key_context': 'general',
    },
    'SEARCH_TOPICS': {
        'keys': ['q'],
        'help_text': 'Search topics in a stream',
        'key_category': 'searching',
        'key_context': 'topic_view',
    },
    'SEARCH_EMOJIS': {
        'keys': ['p'],
        'help_text': 'Search emojis from Emoji-picker popup',
        'excluded_from_random_tips': True,
        'key_category': 'searching',
        'key_context': 'emoji_picker_view',
    },
    'TOGGLE_MUTE_STREAM': {
        'keys': ['m'],
        'help_text': 'Mute/unmute Streams',
        'key_category': 'stream_list',
        'key_context': 'stream_view',
    },
    'ENTER': {
        'keys': ['enter'],
        'help_text': 'Perform current action',
        'key_category': 'navigation',
        'key_context': 'general',
    },
    'THUMBS_UP': {
        'keys': ['+'],
        'help_text': 'Add/remove thumbs-up reaction to the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'TOGGLE_STAR_STATUS': {
        'keys': ['ctrl s', '*'],
        'help_text': 'Add/remove star status of the current message',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'MSG_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide message information',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'MSG_SENDER_INFO': {
        'keys': ['u'],
        'help_text': 'Show/hide message sender information',
        'key_category': 'msg_actions',
        'key_context': 'message_view',
    },
    'EDIT_HISTORY': {
        'keys': ['e'],
        'help_text': 'Show/hide edit history (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
        'key_context': 'msg_info_view',
    },
    'VIEW_IN_BROWSER': {
        'keys': ['v'],
        'help_text':
            'View current message in browser (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
        'key_context': 'msg_info_view',
    },
    'STREAM_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide stream information & modify settings',
        'key_category': 'stream_list',
        'key_context': 'stream_view',
    },
    'STREAM_MEMBERS': {
        'keys': ['m'],
        'help_text': 'Show/hide stream members (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
        'key_context': 'stream_info_view',
    },
    'COPY_STREAM_EMAIL': {
        'keys': ['c'],
        'help_text':
            'Copy stream email to clipboard (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
        'key_context': 'stream_info_view',
    },
    'REDRAW': {
        'keys': ['ctrl l'],
        'help_text': 'Redraw screen',
        'key_category': 'general',
        'key_context': 'general',
    },
    'QUIT': {
        'keys': ['ctrl c'],
        'help_text': 'Quit',
        'key_category': 'general',
        'key_context': 'general',
    },
    'USER_INFO': {
        'keys': ['i'],
        'help_text': 'View user information (From Users list)',
        'key_category': 'general',
        'key_context': 'user_view',
    },
    'BEGINNING_OF_LINE': {
        'keys': ['ctrl a'],
        'help_text': 'Jump to the beginning of line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'END_OF_LINE': {
        'keys': ['ctrl e'],
        'help_text': 'Jump to the end of line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'ONE_WORD_BACKWARD': {
        'keys': ['meta b'],
        'help_text': 'Jump backward one word',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'ONE_WORD_FORWARD': {
        'keys': ['meta f'],
        'help_text': 'Jump forward one word',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'DELETE_LAST_CHARACTER': {
        'keys': ['ctrl h'],
        'help_text': 'Delete previous character (to left)',
        'key_category': 'msg_compose',
        'key_context': 'editor',
    },
    'TRANSPOSE_CHARACTERS': {
        'keys': ['ctrl t'],
        'help_text': 'Transpose characters',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'CUT_TO_END_OF_LINE': {
        'keys': ['ctrl k'],
        'help_text': 'Cut forwards to the end of the line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'CUT_TO_START_OF_LINE': {
        'keys': ['ctrl u'],
        'help_text': 'Cut backwards to the start of the line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'CUT_TO_END_OF_WORD': {
        'keys': ['meta d'],
        'help_text': 'Cut forwards to the end of the current word',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'CUT_TO_START_OF_WORD': {
        'keys': ['ctrl w'],
        'help_text': 'Cut backwards to the start of the current word',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'PASTE_LAST_CUT': {
        'keys': ['ctrl y'],
        'help_text': 'Paste last cut section',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'UNDO_LAST_ACTION': {
        'keys': ['ctrl _'],
        'help_text': 'Undo last action',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'PREV_LINE': {
        'keys': ['up', 'ctrl p'],
        'help_text': 'Jump to the previous line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'NEXT_LINE': {
        'keys': ['down', 'ctrl n'],
        'help_text': 'Jump to the next line',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'CLEAR_MESSAGE': {
        'keys': ['ctrl l'],
        'help_text': 'Clear compose box',
        'key_category': 'msg_compose',
        'key_context': 'message_view_editor',
    },
    'FULL_RENDERED_MESSAGE': {
        'keys': ['f'],
        'help_text': 'Show/hide full rendered message (from message information)',
        'key_category': 'msg_actions',
        'key_context': 'msg_info_view',
    },
    'FULL_RAW_MESSAGE': {
        'keys': ['r'],
        'help_text': 'Show/hide full raw message (from message information)',
        'key_category': 'msg_actions',
        'key_context': 'msg_info_view',
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


URWID_KEY_TO_DISPLAY_KEY_MAPPING = {
    "page up": "PgUp",
    "page down": "PgDn",
}


def display_key_for_urwid_key(urwid_key: str) -> str:
    """
    Returns a displayable user-centric format of the urwid key.
    """
    for urwid_map_key, display_map_key in URWID_KEY_TO_DISPLAY_KEY_MAPPING.items():
        if urwid_map_key in urwid_key:
            urwid_key = urwid_key.replace(urwid_map_key, display_map_key)
    display_key = [
        keyboard_key.capitalize()
        if len(keyboard_key) > 1 and keyboard_key[0].islower()
        else keyboard_key
        for keyboard_key in urwid_key.split()
    ]
    return " ".join(display_key)


def display_keys_for_command(command: str) -> List[str]:
    """
    Returns the user-friendly display keys for a given mapped command
    """
    return [
        display_key_for_urwid_key(urwid_key) for urwid_key in keys_for_command(command)
    ]


def primary_display_key_for_command(command: str) -> str:
    """
    Primary Display Key is the formatted display version of the primary key
    """
    return display_key_for_urwid_key(primary_key_for_command(command))


HELP_CONTEXTS: Dict[str, str] = {
    "general": "General actions",
    "editor": "Editor actions",  # urwid.Edit (PanelSearchBox)
    "message_view_editor": "Message-column Editor actions",
    # (MessageSearchBox, WriteBox) (overrides editor)
    # Both editors in message_view use urwid_readline.ReadlineEdit
    "write_box": "Compose-box actions",  # WriteBox
    # (overrides message_view_editor and editor)
    "stream_view": "Stream list actions",
    "topic_view": "Topic list actions",
    "user_view": "User list actions",
    "message_view": "Message actions",
    "stream_info_view": "Stream-Info Popup actions",
    "msg_info_view": "Message-Info Popup actions",
    "emoji_picker_view": "Emoji-picker Popup actions",
}


def commands_for_random_tips(context: str = "") -> List[KeyBinding]:
    """
    Return list of commands which may be displayed as a random tip
    """
    if not context or context not in HELP_CONTEXTS:
        return commands_for_random_tips("general")
    random_tips: List[KeyBinding] = [
        key_binding
        for key_binding in KEY_BINDINGS.values()
        if not key_binding.get("excluded_from_random_tips", False)
        and key_binding["key_context"] == context
    ]
    if len(random_tips) == 0:
        return commands_for_random_tips("general")
    return random_tips


# Refer urwid/command_map.py
# Adds alternate keys for standard urwid navigational commands.
for zt_cmd, urwid_cmd in ZT_TO_URWID_CMD_MAPPING.items():
    for key in keys_for_command(zt_cmd):
        command_map[key] = urwid_cmd
