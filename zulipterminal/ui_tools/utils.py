from typing import Any, Iterable, List, Optional

import urwid

from zulipterminal.api_types import Message
from zulipterminal.ui_tools.boxes import MessageBox


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


def is_muted(msg: Message, model: Any) -> bool:
    # PMs cannot be muted
    if msg["type"] == "private":
        return False
    # In a topic narrow
    elif len(model.narrow) == 2:
        return False
    elif model.is_muted_stream(msg["stream_id"]):
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
