from typing import Any, List, Dict
import urwid

from zulipterminal.ui_tools.boxes import MessageBox


def create_msg_box_list(messages: List[Dict[str, Any]], model: Any,
                        narrow: bool=False, id: int=None) -> List[Any]:
    messages = sorted(messages, key=lambda msg: msg['time'])

    focus_msg_id = model.focus_all_msg
    if narrow:
        focus_msg_id = model.focus_narrow
    if id is not None:
        focus_msg_id = id

    focus_msg = len(messages) - 1
    for msg in messages:
        if msg['id'] == focus_msg_id:
            focus_msg = messages.index(msg)

    w_list = [urwid.AttrMap(
                MessageBox(item, model),
                item['color'],
                'msg_selected'
            ) for item in messages]
    if focus_msg > 0:
        focus_msg -= 1
    return w_list, focus_msg
