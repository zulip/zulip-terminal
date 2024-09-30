"""
Process widgets (submessages) like polls, todo lists, etc.
"""

import json
from typing import Dict, List, Union


Submessage = Dict[str, Union[int, str]]


def find_widget_type(submessages: List[Submessage]) -> str:
    if submessages and "content" in submessages[0]:
        content = submessages[0]["content"]

        if isinstance(content, str):
            try:
                loaded_content = json.loads(content)
                return loaded_content.get("widget_type", "unknown")
            except json.JSONDecodeError:
                return "unknown"
        else:
            return "unknown"
    else:
        return "unknown"
