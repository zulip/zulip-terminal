from platform import platform
from typing import Any, List

import urwid
import zulip

from zulipterminal.model import Model
from zulipterminal.ui import View, Screen
from zulipterminal.ui_tools.utils import create_msg_box_list


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme: str) -> None:
        self.client = zulip.Client(config_file=config_file,
                                   client='ZulipTerminal/0.1.0 ' + platform())
        # Register to the queue before initializing Model or View
        # so that we don't lose any updates while messages are being fetched.
        self.register_initial_desired_events()
        self.model = Model(self)
        self.view = View(self)
        # Start polling for events after view is rendered.
        self.model.poll_for_events()
        self.theme = theme
        self.editor_mode = False  # type: bool
        self.editor = None  # type: Any

    def search_messages(self, text: str) -> None:
        # Search for a text in messages
        self.update = False
        self.model.narrow = [['search', text]]
        self.model.anchor = 10000000000
        self.model.num_after = 0
        self.model.num_before = 30
        self.model.get_messages(False)
        msg_id_list = self.model.index['search']
        w_list = create_msg_box_list(self.model, msg_id_list)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        focus_position = 0
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_list.set_focus(focus_position)

    def narrow_to_stream(self, button: Any) -> None:
        # return if already narrowed
        if self.model.narrow == [['stream', button.caption]]:
            return
        self.update = False
        # store the steam id in the model
        self.model.stream_id = button.stream_id
        # set the current narrow
        self.model.narrow = [['stream', button.caption]]
        # get the message ids of the current narrow
        msg_id_list = self.model.index['all_stream'][button.stream_id]
        # if no messages are found get more messages
        if len(msg_id_list) == 0:
            self.model.num_after = 10
            self.model.num_before = 30
            if hasattr(button, 'message'):
                self.model.anchor = button.message['id']
                self.model.get_messages(False)
            else:
                self.model.get_messages(True)
        msg_id_list = self.model.index['all_stream'][button.stream_id]
        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def narrow_to_topic(self, button: Any) -> None:
        if self.model.narrow == [['stream', button.caption],
                                 ['topic', button.title]]:
            return
        self.update = False
        self.model.stream_id = button.stream_id
        self.model.narrow = [["stream", button.caption],
                             ["topic", button.title]]
        msg_id_list = self.model.index['stream'][button.stream_id].get(
                                                    button.title, [])
        if len(msg_id_list) == 0:
            first_anchor = True
            if hasattr(button, 'message'):
                self.model.anchor = button.message['id']
                first_anchor = False
            self.model.num_after = 10
            self.model.num_before = 30
            self.model.get_messages(first_anchor)
            msg_id_list = self.model.index['stream'][button.stream_id].get(
                                                    button.title, [])
        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def narrow_to_user(self, button: Any) -> None:
        if hasattr(button, 'message'):
            emails = [recipient['email']
                      for recipient in button.message['display_recipient']
                      if recipient['email'] != self.model.client.email]
            user_emails = ', '.join(emails)
        else:
            user_emails = button.email
        if self.model.narrow == [["pm_with", user_emails]]:
            return

        button.user_id = self.model.user_dict[user_emails]['user_id']

        self.update = False
        self.model.narrow = [["pm_with", user_emails]]
        msg_id_list = self.model.index['private'].get(frozenset(
            [self.model.user_id, button.user_id]), [])

        self.model.num_after = 10
        self.model.num_before = 30
        if hasattr(button, 'message'):
            self.model.anchor = button.message['id']
            self.model.get_messages(False)
        elif len(msg_id_list) == 0:
            self.model.get_messages(True)
        recipients = frozenset([self.model.user_id, button.user_id])
        self.model.recipients = recipients
        msg_id_list = self.model.index['private'].get(recipients, [])
        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def show_all_messages(self, button: Any) -> None:
        if self.model.narrow == []:
            return
        self.update = False
        msg_list = self.model.index['all_messages']
        self.model.narrow = []
        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_list)

        self._finalize_show(w_list)

    def show_all_pm(self, button: Any) -> None:
        if self.model.narrow == [['is', 'private']]:
            return
        self.update = False
        self.model.narrow = [['is', 'private']]
        msg_list = self.model.index['all_private']
        if len(msg_list) == 0:
            self.model.num_after = 10
            self.model.num_before = 30
            self.model.get_messages(True)
            msg_list = self.model.index['all_private']
        w_list = create_msg_box_list(self.model, msg_list)

        self._finalize_show(w_list)

    def _finalize_show(self, w_list: List[Any]) -> None:
        focus_position = self.model.index['pointer'][str(self.model.narrow)]
        if focus_position == set():
            focus_position = len(w_list) - 1
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_list.set_focus(focus_position)

    def register_initial_desired_events(self) -> None:
        event_types = [
            'message',
            'update_message',
            'reaction',
        ]
        response = self.client.register(event_types=event_types)
        self.max_message_id = response['max_message_id']
        self.queue_id = response['queue_id']
        self.last_event_id = response['last_event_id']

    def main(self) -> None:
        try:
            screen = Screen()
            screen.set_terminal_properties(colors=256)
            self.loop = urwid.MainLoop(self.view,
                                       self.view.palette[self.theme],
                                       screen=screen)
        except KeyError:
            print('Following are the themes available:')
            for theme in self.view.palette.keys():
                print(theme,)
            return

        self.loop.run()
