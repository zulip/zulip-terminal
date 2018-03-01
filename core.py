import zulip
import urwid
from typing import Any
import ujson
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
        self.view.narrow = ujson.dumps([['stream', button.caption]])
        self.model.msg_view.clear()
        messages = self.model.messages[button.caption]
        if len(messages) == 0:
            classified_msgs = self.model.load_old_messages(False)
            messages = classified_msgs[button.caption]
        self.model.msg_view.extend(create_msg_box_list(messages, self.model))
        self.model.num_before = len(messages)

    def narrow_to_user(self, button: Any) -> None:
        self.view.narrow = ujson.dumps([["pm_with", button.email]])
        self.model.msg_view.clear()
        messages = self.model.messages[button.email]
        if len(messages) == 0:
            classified_msgs = self.model.load_old_messages(False)
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
                }]
        self.model.msg_view.extend(create_msg_box_list(messages, self.model))
        self.model.num_before = len(messages)

    def show_all_messages(self, button: Any) -> None:
        self.view.narrow = ujson.dumps([])
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
