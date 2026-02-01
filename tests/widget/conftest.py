import json
from typing import Any, Callable, Dict, Union

import pytest

from zulipterminal.api_types import Submessage


@pytest.fixture
def make_submessage() -> Callable[..., Submessage]:
    def _make(
        *,
        content: Union[str, Dict[str, Any]],
        message_id: int,
        sender_id: int,
        submessage_id: int,
        msg_type: str = "widget",
        event_type: str = "submessage",
    ) -> Submessage:
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content)

        return {
            "type": event_type,
            "msg_type": msg_type,
            "message_id": message_id,
            "submessage_id": submessage_id,
            "sender_id": sender_id,
            "content": content_str,
        }

    return _make
