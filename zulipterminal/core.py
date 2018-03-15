import zulip
import urwid
from typing import Any
import json
import itertools

from zulipterminal.ui_tools import create_msg_box_list
from zulipterminal.helper import async
from zulipterminal.model import ZulipModel
from zulipterminal.ui import ZulipView

class ZulipController:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme: str) -> None:
        self.client = zulip.Client(config_file=config_file)
        self.model = ZulipModel(self)
        self.view = ZulipView(self)
        self.theme = theme

    def narrow_to_stream(self, button: Any) -> None:
        if self.model.narrow == [['stream', button.caption]]:
            return
        self.model.narrow = [['stream', button.caption]]
        self.model.num_after = 10
        self.model.num_before = 30
        classified_msgs = self.model.load_old_messages(True)
        messages = classified_msgs[button.stream_id]
        if len(messages) < 41:
            self.model.update = True
        # FIXME EMPTY `messages` on old streams with no new messages
        if len(messages) == 0:
            messages = [{
                'content': '  No Messages yet! Why not start the conversation?',
                'title': '',
                'type': 'stream',
                'time': 0,
                'sender': '',
                'stream': button.caption,
                'sender_email': '',
                'id' : 10000000000,
                'color' : None
            }]
        w_list, focus_msg = create_msg_box_list(messages, self.model, narrow=True)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        self.model.msg_list.set_focus(focus_msg)

    def narrow_to_user(self, button: Any) -> None:
        if self.model.narrow == [["pm_with", button.email]]:
            return
        self.model.narrow = [["pm_with", button.email]]
        self.model.num_after = 10
        self.model.num_before = 30
        classified_msgs = self.model.load_old_messages(True)
        messages = classified_msgs[button.email]
        if len(messages) < 41:
            self.model.update = True
        if len(messages) == 0:
            messages = [{
                'content': '  No Messages yet! Why not start the conversation?',
                'title': '',
                'type': 'private',
                'time': 0,
                'sender': '',
                'stream': '',
                'sender_email': button.email,
                'id' : 10000000000,
                'color' : None,
            }]
        w_list, focus_msg = create_msg_box_list(messages, self.model, narrow=True)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        self.model.msg_list.set_focus(focus_msg)

    def show_all_messages(self, button: Any) -> None:
        self.model.msg_view.clear()
        msg_list = itertools.chain.from_iterable(self.model.messages.values())
        w_list, focus_msg = create_msg_box_list(msg_list, self.model)
        self.model.msg_view.extend(w_list)
        self.model.msg_list.set_focus(focus_msg)
        self.model.narrow = []

    def main(self) -> None:
        try:
            self.loop = urwid.MainLoop(self.view, self.view.palette[self.theme])
        except KeyError:
            print('Following are the themes available:')
            for theme in self.view.palette.keys():
                print(theme,)
            return

        self.loop.run()
