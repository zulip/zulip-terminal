"""
Process widgets (submessages) like polls, todo lists, etc.
"""

import json
from typing import Any


def find_widget_type(submessage: Any) -> str:
    if submessage and isinstance(submessage, list) and "content" in submessage[0]:
        try:
            content = json.loads(submessage[0]["content"])
            return content.get("widget_type", "unknown")
        except (json.JSONDecodeError, KeyError):
            return "unknown"
    else:
        return "unknown"
