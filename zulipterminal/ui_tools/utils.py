from typing import Any, Iterable, List, Union

import urwid

from zulipterminal.ui_tools.boxes import MessageBox


def create_msg_box_list(model: Any, messages: Union[None, Iterable[Any]]=None,
                        focus_msg_id: Any=None) -> List[Any]:
    if model.narrow == [] and messages is None:
        messages = list(model.index['all_messages'])
    if messages is not None:
        message_list = [model.index['messages'][id] for id in messages]
    message_list.sort(key=lambda msg: msg['timestamp'])
    w_list = []
    focus_msg = None
    last_message = None
    for msg in message_list:
        msg_flag = 'unread'  # type: Union[str, None]
        flags = msg.get('flags')
        # update_messages sends messages with no flags
        # but flags are set to [] when fetching old messages.
        if flags and ('read' in flags):
            msg_flag = None
        elif focus_msg is None:
            focus_msg = message_list.index(msg)
        if msg['id'] == focus_msg_id:
            focus_msg = message_list.index(msg)
        w_list.append(urwid.AttrMap(
                    MessageBox(msg, model, last_message),
                    msg_flag,
                    'msg_selected'
        ))
        last_message = msg
    if focus_msg is not None:
        model.index['pointer'][str(model.narrow)] = focus_msg
    return w_list
