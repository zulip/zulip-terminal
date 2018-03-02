import zulip
import urwid
from typing import Any
import json
import itertools

from ui_tools import create_msg_box_list
from helper import async
from model import ZulipModel
from ui import ZulipView

class ZulipController:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str) -> None:
        self.client = zulip.Client(config_file=config_file)
        self.model = ZulipModel(self)
        self.view = ZulipView(self)

    def narrow_to_stream(self, button: Any) -> None:
        self.model.narrow = [['stream', button.caption]]
        self.model.msg_view.clear()
        messages = self.model.messages[button.stream_id]
        if len(messages) == 0:
            self.model.num_after = 10
            self.model.num_before = 30
            classified_msgs = self.model.load_old_messages(True)
            messages = classified_msgs[button.stream_id]
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
                }]
        self.model.msg_view.extend(create_msg_box_list(messages, self.model))

    def narrow_to_user(self, button: Any) -> None:
        self.model.narrow = [["pm_with", button.email]]
        self.model.msg_view.clear()
        messages = self.model.messages[button.email]
        if len(messages) == 0:
            self.model.num_after = 10
            self.model.num_before = 30
            classified_msgs = self.model.load_old_messages(True)
            messages = classified_msgs[button.email]
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
                }]
        self.model.msg_view.extend(create_msg_box_list(messages, self.model))

    def show_all_messages(self, button: Any) -> None:
        self.model.msg_view.clear()
        self.model.msg_view.extend(create_msg_box_list(itertools.chain.from_iterable(self.model.messages.values()), self.model))
        self.num_before = len(list(itertools.chain.from_iterable(self.model.messages.values())))

    @async
    def update(self) -> None:
        self.client.call_on_each_message(self.model.update_messages)

    def main(self) -> None:
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.update()
        self.loop.run()
