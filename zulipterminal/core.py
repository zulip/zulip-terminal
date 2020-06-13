import os
import signal
import sys
import time
from collections import OrderedDict
from functools import partial
from platform import platform
from typing import Any, Optional, Tuple

import urwid
import zulip

from zulipterminal.config.themes import ThemeSpec
from zulipterminal.helper import Message, asynch
from zulipterminal.model import Model
from zulipterminal.ui import Screen, View
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.views import (
    AboutView, HelpView, LoadingView, MsgInfoView, NoticeView,
    PopUpConfirmationView, StreamInfoView,
)
from zulipterminal.version import ZT_VERSION


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme: ThemeSpec,
                 color_depth: int,
                 autohide: bool, notify: bool, footlinks: bool) -> None:
        self.theme = theme
        self.color_depth = color_depth
        self.autohide = autohide
        self.notify_enabled = notify
        self.footlinks_enabled = footlinks

        self._editor = None  # type: Optional[Any]

        self.capture_stdout()
        self.client = zulip.Client(config_file=config_file,
                                   client='ZulipTerminal/{} {}'.
                                          format(ZT_VERSION, platform()))
        self.loading_view = LoadingView(self)
        self.init_model_view()

    @asynch
    def init_model_view(self) -> None:
        self.model = Model(self)
        self.view = View(self)
        self.model.poll_for_events()

    def is_in_editor_mode(self) -> bool:
        return self._editor is not None

    def enter_editor_mode_with(self, editor: Any) -> None:
        assert self._editor is None, "Already in editor mode"
        self._editor = editor

    def exit_editor_mode(self) -> None:
        self._editor = None

    def current_editor(self) -> Any:
        assert self._editor is not None, "Current editor is None"
        return self._editor

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
        if hasattr(self, 'update_pipe'):
            os.write(self.update_pipe, b'1')

    def draw_screen(self, *args: Any, **kwargs: Any) -> None:
        self.loop.draw_screen()

    def maximum_popup_dimensions(self) -> Tuple[int, int]:
        """
        Returns 3/4th of the screen estate's columns and rows.
        """
        max_cols, max_rows = map(lambda num: 3 * num // 4,
                                 self.loop.screen.get_cols_rows())
        return max_cols, max_rows

    def show_pop_up(self, to_show: Any) -> None:
        double_lines = dict(tlcorner='╔', tline='═', trcorner='╗',
                            rline='║', lline='║',
                            blcorner='╚', bline='═', brcorner='╝')
        self.loop.widget = urwid.Overlay(
            urwid.LineBox(to_show,
                          to_show.title,
                          **double_lines),
            self.view,
            align='center',
            valign='middle',
            # +2 to both of the following, due to LineBox
            width=to_show.width + 2,
            height=to_show.height + 2,
        )

    def exit_popup(self) -> None:
        self.loop.widget = self.view

    def show_help(self) -> None:
        help_view = HelpView(self, "Help Menu (up/down scrolls)")
        self.show_pop_up(help_view)

    def show_msg_info(self, msg: Message,
                      message_links: 'OrderedDict[str, Tuple[str, int, bool]]',
                      ) -> None:
        msg_info_view = MsgInfoView(self, msg,
                                    "Message Information (up/down scrolls)",
                                    message_links)
        self.show_pop_up(msg_info_view)

    def show_stream_info(self, stream_id: int) -> None:
        show_stream_view = StreamInfoView(self, stream_id)
        self.show_pop_up(show_stream_view)

    def popup_with_message(self, text: str, width: int) -> None:
        self.show_pop_up(NoticeView(self, text, width, "NOTICE"))

    def show_about(self) -> None:
        self.show_pop_up(
            AboutView(self, 'About', zt_version=ZT_VERSION,
                      server_version=self.model.server_version,
                      server_feature_level=self.model.server_feature_level)
        )

    def search_messages(self, text: str) -> None:
        # Search for a text in messages
        self.model.index['search'].clear()
        self.model.set_search_narrow(text)

        self.model.get_messages(num_after=0, num_before=30, anchor=10000000000)
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)
        self.view.message_view.log.clear()
        self.view.message_view.log.extend(w_list)
        focus_position = 0
        if 0 <= focus_position < len(w_list):
            self.view.message_view.set_focus(focus_position)

    def stream_muting_confirmation_popup(self, button: Any) -> None:
        currently_muted = self.model.is_muted_stream(button.stream_id)
        type_of_action = "unmuting" if currently_muted else "muting"
        question = urwid.Text(("bold", "Confirm " + type_of_action
                               + " of stream '" + button.stream_name + "' ?"),
                              "center")
        mute_this_stream = partial(self.model.toggle_stream_muted_status,
                                   button.stream_id)
        self.loop.widget = PopUpConfirmationView(self, question,
                                                 mute_this_stream)

    def _narrow_to(self, button: Any, anchor: Optional[int],
                   **narrow: Any) -> None:
        already_narrowed = self.model.set_narrow(**narrow)
        if already_narrowed:
            return

        # store the steam id in the model (required for get_message_ids...)
        if hasattr(button, 'stream_id'):  # FIXME Include in set_narrow?
            self.model.stream_id = button.stream_id

        msg_id_list = self.model.get_message_ids_in_current_narrow()

        # if no messages are found get more messages
        if len(msg_id_list) == 0:
            self.model.get_messages(num_before=30,
                                    num_after=10,
                                    anchor=anchor)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model,
                                     msg_id_list,
                                     focus_msg_id=anchor)

        focus_position = self.model.get_focus_in_current_narrow()
        if focus_position == set():  # No available focus; set to end
            focus_position = len(w_list) - 1
        assert not isinstance(focus_position, set)

        self.view.message_view.log.clear()
        if 0 <= focus_position < len(w_list):
            self.view.message_view.log.extend(w_list, focus_position)
        else:
            self.view.message_view.log.extend(w_list)

        self.exit_editor_mode()

    def narrow_to_stream(self, button: Any) -> None:
        if hasattr(button, 'message'):
            anchor = button.message['id']
        else:
            anchor = None

        self._narrow_to(button,
                        anchor=anchor,
                        stream=button.stream_name)

    def narrow_to_topic(self, button: Any) -> None:
        if hasattr(button, 'message'):
            anchor = button.message['id']
        else:
            anchor = None

        self._narrow_to(button,
                        anchor=anchor,
                        stream=button.stream_name,
                        topic=button.topic_name)

    def narrow_to_user(self, button: Any) -> None:
        if hasattr(button, 'message'):
            user_emails = button.recipients_emails
            anchor = button.message['id']
        else:
            user_emails = button.email
            anchor = None

        self._narrow_to(button,
                        anchor=anchor,
                        pm_with=user_emails)

    def show_all_messages(self, button: Any) -> None:
        if hasattr(button, 'message'):
            anchor = button.message['id']
        else:
            anchor = None

        self._narrow_to(button,
                        anchor=anchor)

    def show_all_pm(self, button: Any) -> None:
        if hasattr(button, 'message'):
            anchor = button.message['id']
        else:
            anchor = None

        self._narrow_to(button,
                        anchor=anchor,
                        pms=True)

    def show_all_starred(self, button: Any) -> None:
        # NOTE: Should we ensure we maintain anchor focus here?
        # (it seems to work fine without)
        self._narrow_to(button,
                        anchor=None,
                        starred=True)

    def show_all_mentions(self, button: Any) -> None:
        # NOTE: Should we ensure we maintain anchor focus here?
        # (As with starred, it seems to work fine without)
        self._narrow_to(button,
                        anchor=None,
                        mentioned=True)

    def deregister_client(self) -> None:
        # Deregister before model has loaded.
        if hasattr(self, 'model'):
            queue_id = self.model.queue_id
            self.client.deregister(queue_id, 1.0)

    def exit_handler(self, signum: int, frame: Any) -> None:
        self.deregister_client()
        sys.exit(0)

    @asynch
    def set_main_view(self) -> None:
        def spinning_cursor() -> Any:
            while True:
                for cursor in '|/-\\':
                    yield cursor

        self.capture_stdout()
        spinner = spinning_cursor()

        while not hasattr(self, 'view'):
            self.loading_view.set_spinner(next(spinner))
            self.update_screen()
            time.sleep(0.1)

        self.loop.widget = self.view
        self.loop.screen.register_palette(self.theme)
        self.update_screen()

    def main(self) -> None:
        screen = Screen()
        screen.set_terminal_properties(colors=self.color_depth)
        self.loop = urwid.MainLoop(self.loading_view,
                                   self.theme,
                                   screen=screen)
        self.update_pipe = self.loop.watch_pipe(self.draw_screen)

        # Register new ^C handler
        signal.signal(signal.SIGINT, self.exit_handler)

        try:
            # TODO: Enable resuming? (in which case, remove ^Z below)
            disabled_keys = {
                'susp': 'undefined',  # Disable ^Z - no suspending
                'stop': 'undefined',  # Disable ^S - enabling shortcut key use
                'quit': 'undefined',  # Disable ^\, ^4
            }
            old_signal_list = screen.tty_signal_keys(**disabled_keys)
            self.set_main_view()
            self.loop.run()

        except Exception:
            self.restore_stdout()
            screen.tty_signal_keys(*old_signal_list)
            raise

        finally:
            self.restore_stdout()
            screen.tty_signal_keys(*old_signal_list)
