from typing import Any, Iterable, List, Union, Dict

import urwid

from zulipterminal.ui_tools.boxes import MessageBox


def create_msg_box_list(model: Any, messages: Union[None, Iterable[Any]]=None,
                        focus_msg_id: Union[None, int]=None,
                        last_message: Union[None, Any]=None) -> List[Any]:
    """
    MessageBox for every message displayed is created here.
    """
    if not model.narrow and messages is None:
        messages = list(model.index['all_messages'])
    if messages is not None:
        message_list = [model.index['messages'][id] for id in messages]
    message_list.sort(key=lambda msg: msg['timestamp'])
    w_list = []
    focus_msg = None
    last_msg = last_message
    muted_msgs = 0  # No of messages that are muted.
    for msg in message_list:
        # Remove messages of muted topics / streams.
        if is_muted(msg, model):
            muted_msgs += 1
            continue

        msg_flag = 'unread'  # type: Union[str, None]
        flags = msg.get('flags')
        # update_messages sends messages with no flags
        # but flags are set to [] when fetching old messages.
        if flags and ('read' in flags):
            msg_flag = None
        elif focus_msg is None:
            focus_msg = message_list.index(msg) - muted_msgs
        if msg['id'] == focus_msg_id:
            focus_msg = message_list.index(msg) - muted_msgs
        w_list.append(urwid.AttrMap(
                    MessageBox(msg, model, last_msg),
                    msg_flag,
                    'msg_selected'
        ))
        last_msg = msg
    if focus_msg is not None:
        model.set_focus_in_current_narrow(focus_msg)
    return w_list


def is_muted(msg: Dict[Any, Any], model: Any) -> bool:
    # PMs cannot be muted
    if msg['type'] == 'private':
        return False
    # In a topic narrow
    elif len(model.narrow) == 2:
        return False
    elif msg['stream_id'] in model.muted_streams:
        return True
    elif [msg['display_recipient'], msg['subject']] in model.muted_topics:
        return True
    return False
