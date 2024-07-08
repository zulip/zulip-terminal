"""
Keybindings and their helper functions
"""

from typing import Dict, List

from typing_extensions import NotRequired, TypedDict
from urwid.command_map import (
    ACTIVATE,
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
    key_contexts: List[str]


# fmt: off
KEY_BINDINGS: Dict[str, KeyBinding] = {
    # Key that is displayed in the UI is determined by the method
    # primary_key_for_command. (Currently the first key in the list)

    'HELP': {
        'keys': ['?'],
        'help_text': 'Show/hide Help Menu',
        'excluded_from_random_tips': True,
        'key_category': 'general',
        'key_contexts': ['general'],
    },
    'MARKDOWN_HELP': {
        'keys': ['meta m'],
        'help_text': 'Show/hide Markdown Help Menu',
        'key_category': 'general',
        'key_contexts': ['general'],
    },
    'ABOUT': {
        'keys': ['meta ?'],
        'help_text': 'Show/hide About Menu',
        'key_category': 'general',
        'key_contexts': ['general'],
    },
    'OPEN_DRAFT': {
        'keys': ['d'],
        'help_text': 'Open draft message saved in this session',
        'key_category': 'open_compose',
        'key_contexts': ['general'],
    },
    'COPY_ABOUT_INFO': {
        'keys': ['c'],
        'help_text': 'Copy information from About Menu to clipboard',
        'key_category': 'general',
        'key_contexts': ['about'],
    },
    'EXIT_POPUP': {
        'keys': ['esc'],
        'help_text': 'Close popup',
        'key_category': 'navigation',
        'key_contexts': ['popup'],
    },
    'GO_UP': {
        'keys': ['up', 'k'],
        'help_text': 'Go up / Previous message',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'GO_DOWN': {
        'keys': ['down', 'j'],
        'help_text': 'Go down / Next message',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'GO_LEFT': {
        'keys': ['left', 'h'],
        'help_text': 'Go left',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'GO_RIGHT': {
        'keys': ['right', 'l'],
        'help_text': 'Go right',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'SCROLL_UP': {
        'keys': ['page up', 'K'],
        'help_text': 'Scroll up',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'SCROLL_DOWN': {
        'keys': ['page down', 'J'],
        'help_text': 'Scroll down',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'GO_TO_BOTTOM': {
        'keys': ['end', 'G'],
        'help_text': 'Go to bottom / Last message',
        'key_category': 'navigation',
        'key_contexts': ['general'],
    },
    'ACTIVATE_BUTTON': {
        'keys': ['enter', ' '],
        'help_text': 'Trigger the selected entry',
        'key_category': 'navigation',
        'key_contexts': ['button'],
    },
    'REPLY_MESSAGE': {
        'keys': ['r', 'enter'],
        'help_text': 'Reply to the current message',
        'key_category': 'open_compose',
        'key_contexts': ['message'],
    },
    'MENTION_REPLY': {
        'keys': ['@'],
        'help_text': 'Reply mentioning the sender of the current message',
        'key_category': 'open_compose',
        'key_contexts': ['message'],
    },
    'QUOTE_REPLY': {
        'keys': ['>'],
        'help_text': 'Reply quoting the current message text',
        'key_category': 'open_compose',
        'key_contexts': ['message'],
    },
    'REPLY_AUTHOR': {
        'keys': ['R'],
        'help_text': 'Reply directly to the sender of the current message',
        'key_category': 'open_compose',
        'key_contexts': ['message'],
    },
    'EDIT_MESSAGE': {
        'keys': ['e'],
        'help_text': "Edit message's content or topic",
        'key_category': 'msg_actions',
        'key_contexts': ['message'],
    },
    'STREAM_MESSAGE': {
        'keys': ['c'],
        'help_text': 'New message to a stream',
        'key_category': 'open_compose',
        'key_contexts': ['general'],
    },
    'PRIVATE_MESSAGE': {
        'keys': ['x'],
        'help_text': 'New message to a person or group of people',
        'key_category': 'open_compose',
        'key_contexts': ['general'],
    },
    'CYCLE_COMPOSE_FOCUS': {
        'keys': ['tab'],
        'help_text': 'Cycle through recipient and content boxes',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'SEND_MESSAGE': {
        'keys': ['ctrl d', 'meta enter'],
        'help_text': 'Send a message',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'SAVE_AS_DRAFT': {
        'keys': ['meta s'],
        'help_text': 'Save current message as a draft',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'AUTOCOMPLETE': {
        'keys': ['ctrl f'],
        'help_text': ('Autocomplete @mentions, #stream_names, :emoji:'
                      ' and topics'),
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'AUTOCOMPLETE_REVERSE': {
        'keys': ['ctrl r'],
        'help_text': 'Cycle through autocomplete suggestions in reverse',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'ADD_REACTION': {
        'keys': [':'],
        'help_text': 'Show/hide emoji picker for current message',
        'key_category': 'msg_actions',
        'key_contexts': ['message'],
    },
    'STREAM_NARROW': {
        'keys': ['s'],
        'help_text': 'View the stream of the current message',
        'key_category': 'narrowing',
        'key_contexts': ['message'],
    },
    'TOPIC_NARROW': {
        'keys': ['S'],
        'help_text': 'View the topic of the current message',
        'key_category': 'narrowing',
        'key_contexts': ['message'],
    },
    'TOGGLE_NARROW': {
        'keys': ['z'],
        'help_text':
            "Zoom in/out the message's conversation context",
        'key_category': 'narrowing',
        'key_contexts': ['message'],
    },
    'NARROW_MESSAGE_RECIPIENT': {
        'keys': ['meta .'],
        'help_text': 'Switch message view to the compose box target',
        'key_category': 'narrowing',
        'key_contexts': ['compose_box'],
    },
    'EXIT_COMPOSE': {
        'keys': ['esc'],
        'help_text': 'Exit message compose box',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'REACTION_AGREEMENT': {
        'keys': ['='],
        'help_text': 'Toggle first emoji reaction on selected message',
        'key_category': 'msg_actions',
        'key_contexts': ['message'],
    },
    'TOGGLE_TOPIC': {
        'keys': ['t'],
        'help_text': 'Toggle topics in a stream',
        'key_category': 'stream_list',
        'key_contexts': ['stream', 'topic'],
    },
    'ALL_MESSAGES': {
        'keys': ['a', 'esc'],
        'help_text': 'View all messages',
        'key_category': 'narrowing',
        'key_contexts': ['message'],
    },
    'ALL_PM': {
        'keys': ['P'],
        'help_text': 'View all direct messages',
        'key_category': 'narrowing',
        'key_contexts': ['general'],
    },
    'ALL_STARRED': {
        'keys': ['f'],
        'help_text': 'View all starred messages',
        'key_category': 'narrowing',
        'key_contexts': ['general'],
    },
    'ALL_MENTIONS': {
        'keys': ['#'],
        'help_text': "View all messages in which you're mentioned",
        'key_category': 'narrowing',
        'key_contexts': ['general'],
    },
    'NEXT_UNREAD_TOPIC': {
        'keys': ['n'],
        'help_text': 'Next unread topic',
        'key_category': 'narrowing',
        'key_contexts': ['general'],
    },
    'NEXT_UNREAD_PM': {
        'keys': ['p'],
        'help_text': 'Next unread direct message',
        'key_category': 'narrowing',
        'key_contexts': ['general'],
    },
    'SEARCH_PEOPLE': {
        'keys': ['w'],
        'help_text': 'Search users',
        'key_category': 'searching',
        'key_contexts': ['general'],
    },
    'SEARCH_MESSAGES': {
        'keys': ['/'],
        'help_text': 'Search messages',
        'key_category': 'searching',
        'key_contexts': ['general'],
    },
    'SEARCH_STREAMS': {
        'keys': ['q'],
        'help_text': 'Search streams',
        'key_category': 'searching',
        'key_contexts': ['general'],
        'excluded_from_random_tips': True,
        # TODO: condition check required
    },
    'SEARCH_TOPICS': {
        'keys': ['q'],
        'help_text': 'Search topics in a stream',
        'key_category': 'searching',
        'key_contexts': ['general'],
        'excluded_from_random_tips': True,
        # TODO: condition check required
    },
    'SEARCH_EMOJIS': {
        'keys': ['p'],
        'help_text': 'Search emojis from emoji picker',
        'excluded_from_random_tips': True,
        'key_category': 'searching',
        'key_contexts': ['emoji_list'],
    },
    'EXECUTE_SEARCH': {
        'keys': ['enter'],
        'help_text': 'Submit search and browse results',
        'key_category': 'searching',
        'key_contexts': ['search_box'],
    },
    'CLEAR_SEARCH': {
        'keys': ['esc'],
        'help_text': 'Clear search in current panel',
        'key_category': 'searching',
        'key_contexts': ['message', 'stream', 'topic', 'user'],
        'excluded_from_random_tips': True,
        # TODO: condition check required
    },
    'TOGGLE_MUTE_STREAM': {
        'keys': ['m'],
        'help_text': 'Mute/unmute streams',
        'key_category': 'stream_list',
        'key_contexts': ['stream'],
    },
    'THUMBS_UP': {
        'keys': ['+'],
        'help_text': 'Toggle thumbs-up reaction to the current message',
        'key_category': 'msg_actions',
        'key_contexts': ['message'],
    },
    'TOGGLE_STAR_STATUS': {
        'keys': ['ctrl s', '*'],
        'help_text': 'Toggle star status of the current message',
        'key_category': 'msg_actions',
        'key_contexts': ['message'],
    },
    'MSG_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide message information',
        'key_category': 'msg_actions',
        'key_contexts': ['message', 'msg_info'],
    },
    'MSG_SENDER_INFO': {
        'keys': ['u'],
        'help_text': 'Show/hide message sender information',
        'key_category': 'msg_actions',
        'key_contexts': ['msg_info'],
    },
    'EDIT_HISTORY': {
        'keys': ['e'],
        'help_text': 'Show/hide edit history (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
        'key_contexts': ['msg_info'],
    },
    'VIEW_IN_BROWSER': {
        'keys': ['v'],
        'help_text':
            'View current message in browser (from message information)',
        'excluded_from_random_tips': True,
        'key_category': 'msg_actions',
        'key_contexts': ['msg_info'],
    },
    'STREAM_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide stream information & modify settings',
        'key_category': 'stream_list',
        'key_contexts': ['stream', 'stream_info'],
    },
    'STREAM_MEMBERS': {
        'keys': ['m'],
        'help_text': 'Show/hide stream members (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
        'key_contexts': ['stream_info'],
    },
    'COPY_STREAM_EMAIL': {
        'keys': ['c'],
        'help_text':
            'Copy stream email to clipboard (from stream information)',
        'excluded_from_random_tips': True,
        'key_category': 'stream_list',
        'key_contexts': ['stream_info'],
    },
    'REDRAW': {
        'keys': ['ctrl l'],
        'help_text': 'Redraw screen',
        'key_category': 'general',
        'key_contexts': ['global'],
    },
    'QUIT': {
        'keys': ['ctrl c'],
        'help_text': 'Quit',
        'key_category': 'general',
        'key_contexts': ['global'],
    },
    'USER_INFO': {
        'keys': ['i'],
        'help_text': 'Show/hide user information (from users list)',
        'key_category': 'general',
        'key_contexts': ['user'],
    },
    'BEGINNING_OF_LINE': {
        'keys': ['ctrl a', 'home'],
        'help_text': 'Start of line',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'END_OF_LINE': {
        'keys': ['ctrl e', 'end'],
        'help_text': 'End of line',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'ONE_WORD_BACKWARD': {
        'keys': ['meta b', 'shift left'],
        'help_text': 'Start of current or previous word',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'ONE_WORD_FORWARD': {
        'keys': ['meta f', 'shift right'],
        'help_text': 'Start of next word',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'PREV_LINE': {
        'keys': ['up', 'ctrl p'],
        'help_text': 'Previous line',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'NEXT_LINE': {
        'keys': ['down', 'ctrl n'],
        'help_text': 'Next line',
        'key_category': 'editor_navigation',
        'key_contexts': ['editor'],
    },
    'UNDO_LAST_ACTION': {
        'keys': ['ctrl _'],
        'help_text': 'Undo last action',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CLEAR_MESSAGE': {
        'keys': ['ctrl l'],
        'help_text': 'Clear text box',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CUT_TO_END_OF_LINE': {
        'keys': ['ctrl k'],
        'help_text': 'Cut forwards to the end of the line',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CUT_TO_START_OF_LINE': {
        'keys': ['ctrl u'],
        'help_text': 'Cut backwards to the start of the line',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CUT_TO_END_OF_WORD': {
        'keys': ['meta d'],
        'help_text': 'Cut forwards to the end of the current word',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CUT_TO_START_OF_WORD': {
        'keys': ['ctrl w', 'meta backspace'],
        'help_text': 'Cut backwards to the start of the current word',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'CUT_WHOLE_LINE': {
        'keys': ['meta x'],
        'help_text': 'Cut the current line',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'PASTE_LAST_CUT': {
        'keys': ['ctrl y'],
        'help_text': 'Paste last cut section',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'DELETE_LAST_CHARACTER': {
        'keys': ['ctrl h'],
        'help_text': 'Delete previous character',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'TRANSPOSE_CHARACTERS': {
        'keys': ['ctrl t'],
        'help_text': 'Swap with previous character',
        'key_category': 'editor_text_manipulation',
        'key_contexts': ['editor'],
    },
    'NEW_LINE': {
        # urwid_readline's command
        # This obvious hotkey is added to clarify against 'enter' to send
        # and to differentiate from other hotkeys using 'enter'.
        'keys': ['enter'],
        'help_text': 'Insert new line',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'OPEN_EXTERNAL_EDITOR': {
        'keys': ['ctrl o'],
        'help_text': 'Open an external editor to edit the message content',
        'key_category': 'compose_box',
        'key_contexts': ['compose_box'],
    },
    'FULL_RENDERED_MESSAGE': {
        'keys': ['f'],
        'help_text': 'Show/hide full rendered message (from message information)',
        'key_category': 'msg_actions',
        'key_contexts': ['msg_info'],
    },
    'FULL_RAW_MESSAGE': {
        'keys': ['r'],
        'help_text': 'Show/hide full raw message (from message information)',
        'key_category': 'msg_actions',
        'key_contexts': ['msg_info'],
    },
    'NEW_HINT': {
        'keys': ['tab'],
        'help_text': 'New footer hotkey hint',
        'key_category': 'general',
        'key_contexts': ['general'],
    },
}
# fmt: on

HELP_CATEGORIES = {
    "general": "General",
    "navigation": "Navigation",
    "narrowing": "Switching Messages View",
    "searching": "Searching",
    "msg_actions": "Message actions",
    "stream_list": "Stream list actions",
    "open_compose": "Begin composing a message",
    "compose_box": "Writing a message",
    "editor_navigation": "Editor: Navigation",
    "editor_text_manipulation": "Editor: Text Manipulation",
}

HELP_CONTEXTS: Dict[str, str] = {
    "global": "Global",
    "general": "General",  # not in an editor or a popup
    "editor": "Editor",
    "compose_box": "Compose box",
    "stream": "Stream list",
    "topic": "Topic list",
    "user": "User list",
    "message": "Message",
    "stream_info": "Stream information",
    "msg_info": "Message information",
    "emoji_list": "Emoji list",
    "about": "About information",
    "popup": "Popup",
    "button": "Button",
    "search_box": "Search box",
}

ZT_TO_URWID_CMD_MAPPING = {
    "GO_UP": CURSOR_UP,
    "GO_DOWN": CURSOR_DOWN,
    "GO_LEFT": CURSOR_LEFT,
    "GO_RIGHT": CURSOR_RIGHT,
    "SCROLL_UP": CURSOR_PAGE_UP,
    "SCROLL_DOWN": CURSOR_PAGE_DOWN,
    "GO_TO_BOTTOM": CURSOR_MAX_RIGHT,
    "ACTIVATE_BUTTON": ACTIVATE,
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
    if urwid_key == " ":
        return "Space"

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


def commands_for_random_tips(context: str = "") -> List[KeyBinding]:
    """
    Return list of commands which may be displayed as a random tip
    """
    if not context or context not in HELP_CONTEXTS:
        context = "global"
    random_tips: List[KeyBinding] = [
        key_binding
        for key_binding in KEY_BINDINGS.values()
        if not key_binding.get("excluded_from_random_tips", False)
        and context in key_binding["key_contexts"]
    ]
    if len(random_tips) == 0:
        return commands_for_random_tips("global")
    return random_tips


# Refer urwid/command_map.py
# Adds alternate keys for standard urwid navigational commands.
for zt_cmd, urwid_cmd in ZT_TO_URWID_CMD_MAPPING.items():
    for key in keys_for_command(zt_cmd):
        command_map[key] = urwid_cmd
