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


HELP_TEXT = """\
Welcome to Zulip Terminal, a terminal interface for Zulip.
----------------------------------------------------------

(This help screen is scrollable. Hit Page Down to see more.)


> Hot Keys:
__________________________________________________________________________
| Command                                               | Key Combination |
| ----------------------------------------------------- | --------------- |
| Previous message                                      | Up / k          |
| Next message                                          | Down / j        |
| Go left                                               | left / h        |
| Go right                                              | right / l       |
| Go to the last message                                | G / end         |
| Narrow to private messages                            | P               |
| Scroll down                                           | PgDn / J        |
| Scroll up                                             | PgUp / K        |
| Reply to a message                                    | r               |
| Reply to an author                                    | R               |
| New stream message                                    | c               |
| Go Back                                               | esc             |
| Narrow to a stream                                    | S               |
| Narrow to a topic                                     | s               |
| Next Unread Topic                                     | n               |
| Next Unread PM                                        | p               |
| Send a message                                        | Alt Enter       |
| Search People                                         | w               |
| Search Messages                                       | /               |
| Beginning of line                                     | Ctrl + A        |
| Backward one character                                | Ctrl + B / ←    |
| Backward one word                                     | Meta + B        |
| Delete one character                                  | Ctrl + D        |
| Delete one word                                       | Meta + D        |
| End of line                                           | Ctrl + E        |
| Forward one character                                 | Ctrl + F / →    |
| Forward one word                                      | Meta + F        |
| Delete previous character                             | Ctrl + H        |
| Transpose characters                                  | Ctrl + T        |
| Kill (cut) forwards to the end of the line            | Ctrl + K        |
| Kill (cut) backwards to the start of the line         | Ctrl + U        |
| Kill (cut) forwards to the end of the current word    | Meta + D        |
| Kill (cut) backwards to the start of the current word | Ctrl + W        |
| Previous line                                         | Ctrl + P / ↑    |
| Next line                                             | Ctrl + N / ↓    |
| Clear screen                                          | Ctrl + L        |
|_______________________________________________________|_________________|
"""
