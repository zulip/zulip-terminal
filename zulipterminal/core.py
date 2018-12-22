from platform import platform
from typing import Any, List
import os
import sys
import time

import urwid
import zulip

from zulipterminal.version import ZT_VERSION
from zulipterminal.helper import asynch
from zulipterminal.model import Model, GetMessagesArgs
from zulipterminal.ui import View, Screen
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.views import HelpView
from zulipterminal.config.themes import ThemeSpec


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme: ThemeSpec,
                 autohide: bool) -> None:
        self.theme = theme
        self.autohide = autohide

        self.show_loading()
        self.client = zulip.Client(config_file=config_file,
                                   client='ZulipTerminal/{} {}'.
                                          format(ZT_VERSION, platform()))
        # Register to the queue before initializing Model or View
        # so that we don't lose any updates while messages are being fetched.
        self.register_initial_desired_events()
        self.model = Model(self)
        self.view = View(self)
        # Start polling for events after view is rendered.
        self.model.poll_for_events()
        self.editor_mode = False  # type: bool
        self.editor = None  # type: Any

    @asynch
    def show_loading(self) -> None:

        def spinning_cursor() -> Any:
            while True:
                for cursor in '|/-\\':
                    yield cursor

        spinner = spinning_cursor()
        sys.stdout.write("\033[92mWelcome to Zulip.\033[0m\n")
        while not hasattr(self, 'view'):
            next_spinner = "Loading " + next(spinner)
            sys.stdout.write(next_spinner)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b'*len(next_spinner))

        sys.stdout.write('\n')
        self.capture_stdout()

    def capture_stdout(self, path: str='debug.log') -> None:
        if hasattr(self, '_stdout'):
            return

        self._stdout = sys.stdout
        sys.stdout = open(path, 'a')

    def restore_stdout(self) -> None:
        if not hasattr(self, '_stdout'):
            return

        sys.stdout.flush()
        sys.stdout.close()
        sys.stdout = self._stdout
        sys.stdout.write('\n')
        del self._stdout

    def update_screen(self) -> None:
        # Write something to update pipe to trigger draw_screen
        os.write(self.update_pipe, b'1')

    def draw_screen(self, *args: Any, **kwargs: Any) -> None:
        self.loop.draw_screen()

    def show_help(self) -> None:
        self.loop.widget = urwid.Overlay(
            urwid.LineBox(HelpView(self),
                          title="Help Menu ('q' quits, up/down scrolls)"),
            self.view,
            align='center',
            width=('relative', 100),
            valign='middle',
            height=('relative', 100)
        )

    def exit_help(self) -> None:
        self.loop.widget = self.view

    def search_messages(self, text: str) -> None:
        # Search for a text in messages
        self.model.set_narrow(search=text)

        self.update = False
        self.model.get_messages(num_after=0, num_before=30, anchor=10000000000)
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        focus_position = 0
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_list.set_focus(focus_position)

    def narrow_to_stream(self, button: Any) -> None:
        already_narrowed = self.model.set_narrow(stream=button.caption)
        if already_narrowed:
            return

        self.update = False
        # store the steam id in the model (required for get_message_ids...)
        self.model.stream_id = button.stream_id
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        # if no messages are found get more messages
        if len(msg_id_list) == 0:
            get_msg_opts = dict(num_before=30, num_after=10,
                                anchor=None)  # type: GetMessagesArgs
            if hasattr(button, 'message'):
                get_msg_opts['anchor'] = button.message['id']
            self.model.get_messages(**get_msg_opts)
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def narrow_to_topic(self, button: Any) -> None:
        already_narrowed = self.model.set_narrow(stream=button.caption,
                                                 topic=button.title)
        if already_narrowed:
            return

        self.update = False
        # store the steam id in the model (required for get_message_ids...)
        self.model.stream_id = button.stream_id
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if len(msg_id_list) == 0:
            get_msg_opts = dict(num_before=30, num_after=10,
                                anchor=None)  # type: GetMessagesArgs
            if hasattr(button, 'message'):
                get_msg_opts['anchor'] = button.message['id']
            self.model.get_messages(**get_msg_opts)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

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
            user_ids = {user['id']
                        for user in button.message['display_recipient']}
        else:
            user_emails = button.email
            user_ids = {self.model.user_id, button.user_id}

        already_narrowed = self.model.set_narrow(pm_with=user_emails)
        if already_narrowed:
            return

        self.update = False
        recipients = frozenset(user_ids)
        # store the recipients in the model (required for get_message_ids...)
        self.model.recipients = recipients
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if len(msg_id_list) == 0:
            get_msg_opts = dict(num_before=30, num_after=10,
                                anchor=None)  # type: GetMessagesArgs
            if hasattr(button, 'message'):
                get_msg_opts['anchor'] = button.message['id']
            self.model.get_messages(**get_msg_opts)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def show_all_messages(self, button: Any) -> None:
        already_narrowed = self.model.set_narrow()
        if already_narrowed:
            return

        self.update = False
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if hasattr(button, 'message'):
            w_list = create_msg_box_list(
                self.model, msg_id_list, button.message['id'])
        else:
            w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def show_all_pm(self, button: Any) -> None:
        already_narrowed = self.model.set_narrow(pms=True)
        if already_narrowed:
            return

        self.update = False
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if len(msg_id_list) == 0:
            self.model.get_messages(num_before=30, num_after=10, anchor=None)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def show_all_starred(self, button: Any) -> None:
        already_narrowed = self.model.set_narrow(starred=True)
        if already_narrowed:
            return

        self.update = False
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        if len(msg_id_list) == 0:
            self.model.get_messages(num_before=30, num_after=10, anchor=None)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)

        self._finalize_show(w_list)

    def _finalize_show(self, w_list: List[Any]) -> None:
        focus_position = self.model.get_focus_in_current_narrow()

        if focus_position == set():
            focus_position = len(w_list) - 1
        assert not isinstance(focus_position, set)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_list.set_focus(focus_position)

    @asynch
    def register_initial_desired_events(self) -> None:
        event_types = [
            'message',
            'update_message',
            'reaction',
            'typing',
            'update_message_flags',
        ]
        response = self.client.register(event_types=event_types,
                                        apply_markdown=True)
        self.max_message_id = response['max_message_id']
        self.queue_id = response['queue_id']
        self.last_event_id = response['last_event_id']

    def main(self) -> None:
        screen = Screen()
        screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(self.view,
                                   self.theme,
                                   screen=screen)
        self.update_pipe = self.loop.watch_pipe(self.draw_screen)

        try:
            # TODO: Enable resuming? (in which case, remove ^Z below)
            disabled_keys = {
                'susp': 'undefined',  # Disable ^Z for suspending
                'stop': 'undefined',  # Disable ^S, enabling shortcut key use
            }
            old_signal_list = screen.tty_signal_keys(**disabled_keys)
            self.loop.run()

        except Exception:
            self.restore_stdout()
            screen.tty_signal_keys(*old_signal_list)
            raise

        finally:
            self.restore_stdout()
            screen.tty_signal_keys(*old_signal_list)
