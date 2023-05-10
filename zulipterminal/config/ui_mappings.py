"""
Relationships between state/API data and presentation in the UI
"""

from typing import Dict

from typing_extensions import Literal

from zulipterminal.api_types import EditPropagateMode
from zulipterminal.config.symbols import (
    BOT_MARKER,
    DOWN_ARROW_KEY,
    LEFT_ARROW_KEY,
    RIGHT_ARROW_KEY,
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_INACTIVE,
    STATUS_OFFLINE,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
    STREAM_MARKER_WEB_PUBLIC,
    UP_ARROW_KEY,
)


EDIT_MODE_CAPTIONS: Dict[EditPropagateMode, str] = {
    "change_one": "Change only this message topic",
    "change_later": "Also change later messages to this topic",
    "change_all": "Also change previous and following messages to this topic",
}


UserStatus = Literal["active", "idle", "offline", "inactive", "bot"]

# Mapping that binds user activity status to corresponding markers.
# NOTE: Ordering of keys affects display order
STATE_ICON: Dict[UserStatus, str] = {
    "active": STATUS_ACTIVE,
    "idle": STATUS_IDLE,
    "offline": STATUS_OFFLINE,
    "inactive": STATUS_INACTIVE,
    "bot": BOT_MARKER,
}


StreamAccessType = Literal["public", "private", "web-public"]

STREAM_ACCESS_TYPE = {
    "public": {"description": "Public", "icon": STREAM_MARKER_PUBLIC},
    "private": {"description": "Private", "icon": STREAM_MARKER_PRIVATE},
    "web-public": {"description": "Web public", "icon": STREAM_MARKER_WEB_PUBLIC},
}


BOT_TYPE_BY_ID = {
    1: "Generic Bot",
    2: "Incoming Webhook Bot",
    3: "Outgoing Webhook Bot",
    4: "Embedded Bot",
}


ROLE_BY_ID: Dict[int, Dict[str, str]] = {
    100: {"bool": "is_owner", "name": "Owner"},
    200: {"bool": "is_admin", "name": "Administrator"},
    300: {"bool": "is_moderator", "name": "Moderator"},
    400: {"bool": "", "name": "Member"},
    600: {"bool": "is_guest", "name": "Guest"},
}

STREAM_POST_POLICY = {
    1: "Any user can post",
    2: "Only organization administrators can send to this stream",
    3: "Only organization administrators, moderators and full members can send to this stream",  # noqa: E501
    4: "Only organization administrators and moderators can send to this stream",
}

EDIT_TOPIC_POLICY = {
    1: "Only organization administrators, moderators, full members and members can edit topic",  # noqa: E501
    2: "Only organization administrators can edit topic",
    3: "Only organization administrators, moderators and full members can edit topic",
    4: "Only organization administrators and moderators can edit topic",
    5: "Any user can edit topic",
}

URWID_KEY_TO_DISPLAY_KEY_MAPPING = {
    "meta m": "Meta m",
    "meta ?": "Meta ?",
    "meta enter": "Meta Enter",
    "meta s": "Meta s",
    "meta .": "Meta .",
    "meta b": "Meta b",
    "meta f": "Meta f",
    "meta d": "Meta d",
    "ctrl d": "Ctrl d",
    "ctrl f": "Ctrl f",
    "ctrl r": "Ctrl r",
    "ctrl s": "Ctrl s",
    "ctrl l": "Ctrl l",
    "ctrl c": "Ctrl c",
    "ctrl a": "Ctrl a",
    "ctrl e": "Ctrl e",
    "ctrl h": "Ctrl h",
    "ctrl t": "Ctrl t",
    "ctrl k": "Ctrl k",
    "ctrl u": "Ctrl u",
    "ctrl w": "Ctrl w",
    "ctrl y": "Ctrl y",
    "ctrl _": "Ctrl _",
    "ctrl p": "Ctrl p",
    "ctrl n": "Ctrl n",
    "esc": "Esc",
    "page up": "PgUp",
    "page down": "PgDn",
    "end": "End",
    "enter": "Enter",
    "tab": "Tab",
    "up": UP_ARROW_KEY,
    "down": DOWN_ARROW_KEY,
    "left": LEFT_ARROW_KEY,
    "right": RIGHT_ARROW_KEY,
    "?": "?",
    "@": "@",
    ">": ">",
    ":": ":",
    "#": "#",
    "/": "/",
    "+": "+",
    "*": "*",
    "d": "d",
    "k": "k",
    "j": "j",
    "h": "h",
    "l": "l",
    "r": "r",
    "e": "e",
    "c": "c",
    "x": "x",
    "s": "s",
    "z": "z",
    "t": "t",
    "a": "a",
    "f": "f",
    "n": "n",
    "p": "p",
    "w": "w",
    "q": "q",
    "m": "m",
    "i": "i",
    "v": "v",
    "K": "K",
    "J": "J",
    "G": "G",
    "R": "R",
    "S": "S",
    "P": "P",
}
