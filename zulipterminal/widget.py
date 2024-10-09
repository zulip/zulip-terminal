"""
Process widgets (submessages) like polls, todo lists, etc.
"""

import json
from typing import Any, Dict, List, Optional, Tuple


def find_widget_type(submessage: Any) -> str:
    if submessage and isinstance(submessage, list) and "content" in submessage[0]:
        try:
            content = json.loads(submessage[0]["content"])
            return content.get("widget_type", "unknown")
        except (json.JSONDecodeError, KeyError):
            return "unknown"
    else:
        return "unknown"


def process_poll_widget(
    poll_content: Optional[List[Dict[str, Any]]]
) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    if poll_content is None:
        return "", {}

    poll_question = ""
    options = {}

    for entry in poll_content:
        content = entry["content"]
        sender_id = entry["sender_id"]
        msg_type = entry["msg_type"]

        if msg_type == "widget":
            widget = json.loads(content)

            if widget.get("widget_type") == "poll":
                poll_question = widget["extra_data"]["question"]
                for i, option in enumerate(widget["extra_data"]["options"]):
                    option_id = f"canned,{i}"
                    options[option_id] = {"option": option, "votes": []}

            elif widget.get("type") == "question":
                poll_question = widget["question"]

            elif widget.get("type") == "vote":
                option_id = widget["key"]
                vote_type = widget["vote"]

                if option_id in options:
                    if vote_type == 1 and sender_id not in options[option_id]["votes"]:
                        options[option_id]["votes"].append(sender_id)
                    elif vote_type == -1 and sender_id in options[option_id]["votes"]:
                        options[option_id]["votes"].remove(sender_id)

            elif widget.get("type") == "new_option":
                idx = widget["idx"]
                new_option = widget["option"]
                option_id = f"{sender_id},{idx}"
                options[option_id] = {"option": new_option, "votes": []}

    return poll_question, options
