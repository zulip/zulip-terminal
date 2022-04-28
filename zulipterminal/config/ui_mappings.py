from typing import Dict, Optional

from typing_extensions import Literal

from zulipterminal.api_types import EditPropagateMode
from zulipterminal.config.symbols import (
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_INACTIVE,
    STATUS_OFFLINE,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
    STREAM_MARKER_WEB_PUBLIC,
)


EDIT_MODE_CAPTIONS: Dict[EditPropagateMode, str] = {
    "change_one": "Change only this message topic",
    "change_later": "Also change later messages to this topic",
    "change_all": "Also change previous and following messages to this topic",
}


# Mapping that binds user activity status to corresponding markers.
STATE_ICON = {
    "active": STATUS_ACTIVE,
    "idle": STATUS_IDLE,
    "offline": STATUS_OFFLINE,
    "inactive": STATUS_INACTIVE,
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


ROLE_BY_ID: Dict[Optional[int], Dict[str, str]] = {
    100: {"bool": "is_owner", "name": "Owner"},
    200: {"bool": "is_admin", "name": "Administrator"},
    300: {"bool": "is_moderator", "name": "Moderator"},
    400: {"bool": "", "name": "Member"},
    600: {"bool": "is_guest", "name": "Guest"},
}

STREAM_POST_POLICY = {
    1: "Any user can post",
    2: "Only organization administrators can send to this stream",
    3: "Only organization administrators, moderators and full members can send to this stream",
    4: "Only organization administrators and moderators can send to this stream",
}
