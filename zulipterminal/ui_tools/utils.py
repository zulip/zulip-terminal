"""
The `MessageBox` for every message displayed is created here
"""

from typing import Any, Iterable, List, Optional

import urwid

from zulipterminal.api_types import Message
from zulipterminal.ui_tools.messages import MessageBox,PlaceholderMessageBox
from typing import List, Any

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
        message_list = [model.index["messages"][id] for id in messages if id in model.index["messages"]]
    else:
        message_list = []
    if not message_list:
        placeholder = urwid.AttrMap(PlaceholderMessageBox("No messages here"), None, "msg_selected")
        model.set_focus_in_current_narrow(0)
        return [placeholder]

    message_list.sort(key=lambda msg: msg["timestamp"])
    w_list = []
    focus_msg = None
    last_msg = last_message
    muted_msgs = 0  # No of messages that are muted.
    for msg in message_list:
        if is_unsubscribed_message(msg, model):
            continue
        if is_muted(msg, model):
            muted_msgs += 1
            if model.narrow == []:  # Don't show in 'All messages'.
                continue
        msg_flag: Optional[str] = "unread"
        flags = msg.get("flags")
        if flags and ("read" in flags):
            msg_flag = None
        elif (focus_msg is None) and (last_msg is None):  # type: ignore[redundant-expr]
            focus_msg = message_list.index(msg) - muted_msgs
        if msg["id"] == focus_msg_id:
            focus_msg = message_list.index(msg) - muted_msgs
        # Skip invalid last_msg from placeholder
        if last_msg and "type" not in last_msg:
            last_msg = None
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
