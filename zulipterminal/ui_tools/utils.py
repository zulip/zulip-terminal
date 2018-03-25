from typing import Any
import urwid

from zulipterminal.ui_tools.boxes import MessageBox


def create_msg_box_list(model: Any, messages=None, focus_msg_id=None):
    if model.narrow == [] and messages is None:
        messages = sorted(list(model.index['all_messages']))
    message_list = [model.index['messages'][id] for id in messages]
    message_list.sort(key=lambda msg: msg['timestamp'])
    w_list = []
    focus_msg = None
    for msg in message_list:
        msg_flag = 'unread'
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
                    MessageBox(msg, model),
                    msg_flag,
                    'msg_selected'
        ))
    if model.index['pointer'][str(model.narrow)] == set() and\
            focus_msg is not None:
        model.index['pointer'][str(model.narrow)] = focus_msg
    return w_list
