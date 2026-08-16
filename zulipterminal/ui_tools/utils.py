"""
The `MessageBox` for every message displayed is created here
"""

from typing import Any, Iterable, List, Optional

import urwid

from zulipterminal.api_types import Message
from zulipterminal.ui_tools.messages import MessageBox


def create_msg_box_list(
    model: Any,
    messages: Optional[Iterable[Any]] = None,
    *,
    focus_msg_id: Optional[int] = None,
    last_message: Optional[Message] = None,
) -> List[Any]:
    """
    MessageBox for every message displayed is created here.
    """
    if not model.narrow and messages is None:
        messages = list(model.index["all_msg_ids"])
    if messages is not None:
        message_list = [model.index["messages"][id] for id in messages]
    message_list.sort(key=lambda msg: msg["timestamp"])
    w_list = []
    focus_msg = None
    last_msg = last_message
    muted_msgs = 0  # No of messages that are muted.

    # Add a dummy message if no new or old messages are found
    if not message_list and not last_msg:
        message_type = "stream" if model.stream_id is not None else "private"
        dummy_message = {
            "id": None,
            "content": (
                "No search hits" if model.is_search_narrow() else "No messages here"
            ),
            "is_me_message": False,
            "flags": ["read"],
            "reactions": [],
            "type": message_type,
            "stream_id": model.stream_id if message_type == "stream" else None,
            "stream_name": model.stream_dict[model.stream_id]["name"]
            if message_type == "stream"
            else None,
            "subject": next(
                (subnarrow[1] for subnarrow in model.narrow if subnarrow[0] == "topic"),
                "No topics in channel",
            )
            if message_type == "stream"
            else None,
            "display_recipient": (
                model.stream_dict[model.stream_id]["name"]
                if message_type == "stream"
                else [
                    {
                        "email": model.user_id_email_dict[recipient_id],
                        "full_name": model.user_dict[
                            model.user_id_email_dict[recipient_id]
                        ]["full_name"],
                        "id": recipient_id,
                    }
                    for recipient_id in model.recipients
                ]
            ),
        }
        message_list.append(dummy_message)

    for msg in message_list:
        if is_unsubscribed_message(msg, model):
            continue
        # Remove messages of muted topics / streams.
        if is_muted(msg, model):
            muted_msgs += 1
            if model.narrow == []:  # Don't show in 'All messages'.
                continue
        msg_flag: Optional[str] = "unread"
        flags = msg.get("flags")
        # update_messages sends messages with no flags
        # but flags are set to [] when fetching old messages.
        if flags and ("read" in flags):
            msg_flag = None
        elif focus_msg is None:
            focus_msg = message_list.index(msg) - muted_msgs
        if msg["id"] == focus_msg_id:
            focus_msg = message_list.index(msg) - muted_msgs
        w_list.append(
            urwid.AttrMap(MessageBox(msg, model, last_msg), msg_flag, "msg_selected")
        )
        last_msg = msg
    if focus_msg is not None:
        model.set_focus_in_current_narrow(focus_msg)
    return w_list


# The SIM114 warnings are ignored here since combining the branches would be less clear
def is_muted(msg: Message, model: Any) -> bool:
    # PMs cannot be muted
    if msg["type"] == "private":  # noqa: SIM114
        return False
    # In a topic narrow
    elif len(model.narrow) == 2:
        return False
    elif model.is_muted_stream(msg["stream_id"]):  # noqa: SIM114
        return True
    elif model.is_muted_topic(msg["stream_id"], msg["subject"]):
        return True
    return False


def is_unsubscribed_message(msg: Message, model: Any) -> bool:
    if msg["type"] == "private":
        return False
    if not model.is_user_subscribed_to_stream(msg["stream_id"]):
        return True
    return False
