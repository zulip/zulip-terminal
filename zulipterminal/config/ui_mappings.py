from typing import Dict

from zulipterminal.api_types import EditPropagateMode
from zulipterminal.config.symbols import (
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_INACTIVE,
    STATUS_OFFLINE,
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
