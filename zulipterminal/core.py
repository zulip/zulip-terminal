import os
import signal
import sys
import time
from functools import partial
from platform import platform
from typing import Any, List, Optional

import urwid
import zulip

from zulipterminal.config.themes import (
    THEMES, ThemeSpec, complete_and_incomplete_themes,
)
from zulipterminal.config.tutorial import TUTORIAL
from zulipterminal.helper import Message, asynch
from zulipterminal.model import GetMessagesArgs, Model, ServerConnectionFailure
from zulipterminal.ui import Screen, View
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.views import (
    HelpView, LoadingView, MsgInfoView, PopUpConfirmationView, StreamInfoView,
)
from zulipterminal.version import ZT_VERSION


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme_name: str,
                 autohide: bool, notify: bool, tutorial: bool) -> None:
        self.theme = THEMES[theme_name]
        self.theme_name = theme_name
        self.autohide = autohide
        self.notify_enabled = notify
        self.wait_after_loading = tutorial
        self.editor_mode = False  # type: bool
        self.editor = None  # type: Any
        self.zuliprc_path = os.path.expanduser(config_file)

        self.client = zulip.Client(config_file=config_file,
                                   client='ZulipTerminal/{} {}'.
                                          format(ZT_VERSION, platform()))
        self.init_model()
        # Show LoadingView first, then main View after
        # Model is initialized.
        self.initialize_loop()

    def init_view(self) -> None:
        self.view = View(self)
        # Start polling for events after view is rendered.
        self.model.poll_for_events()

    @asynch
    def init_model(self) -> None:
        try:
            self.model = Model(self)
        except Exception as e:
            self.exception = e
            os.write(self.exception_pipe, b'1')

        self.capture_stdout()

    def raise_exception(self, *args: Any, **kwargs: Any) -> None:
        raise self.exception

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

    def show_pop_up(self, to_show: Any, title: str) -> None:
        double_lines = dict(tlcorner='╔', tline='═', trcorner='╗',
                            rline='║', lline='║',
                            blcorner='╚', bline='═', brcorner='╝')
        cols, rows = self.loop.screen.get_cols_rows()
        self.loop.widget = urwid.Overlay(
            urwid.LineBox(to_show,
                          title,
                          **double_lines),
            self.view,
            align='center',
            valign='middle',
            # +2 to both of the following, due to LineBox
            width=to_show.width+2,
            height=min(3*rows//4, to_show.height)+2
        )

    def exit_popup(self) -> None:
        self.loop.widget = self.view

    def show_help(self) -> None:
        help_view = HelpView(self)
        self.show_pop_up(help_view, "Help Menu (up/down scrolls)")

    def show_msg_info(self, msg: Message) -> None:
        msg_info_view = MsgInfoView(self, msg)
        self.show_pop_up(msg_info_view,
                         "Message Information (up/down scrolls)")

    def show_stream_info(self, color: str, name: str, desc: str) -> None:
        show_stream_view = StreamInfoView(self, color, name, desc)
        self.show_pop_up(show_stream_view, "# {}".format(name))

    def search_messages(self, text: str) -> None:
        # Search for a text in messages
        self.model.index['search'].clear()
        self.model.set_search_narrow(text)

        self.model.found_newest = False
        self.model.get_messages(num_after=0, num_before=30, anchor=10000000000)
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)
        self.model.msg_view.clear()
        self.model.msg_view.extend(w_list)
        focus_position = 0
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_list.set_focus(focus_position)

    def stream_muting_confirmation_popup(self, button: Any) -> None:
        currently_muted = self.model.is_muted_stream(button.stream_id)
        type_of_action = "unmuting" if currently_muted else "muting"
        question = urwid.Text(("bold", "Confirm " + type_of_action +
                               " of stream '" + button.stream_name+"' ?"),
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

        self.model.found_newest = False

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

        self._finalize_show(w_list)

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

    def _finalize_show(self, w_list: List[Any]) -> None:
        focus_position = self.model.get_focus_in_current_narrow()
        if focus_position == set():
            focus_position = len(w_list) - 1
        assert not isinstance(focus_position, set)
        self.model.msg_view.clear()
        if focus_position >= 0 and focus_position < len(w_list):
            self.model.msg_view.extend(w_list, focus_position)
        else:
            self.model.msg_view.extend(w_list)
        self.editor_mode = False

    def deregister_client(self) -> None:
        queue_id = self.model.queue_id
        self.client.deregister(queue_id, 1.0)

    def exit_handler(self, signum: int, frame: Any) -> None:
        self.deregister_client()
        sys.exit(0)

    def loading_text(self, spinner: Any,
                     show_settings: bool=False) -> List[Any]:
        complete, incomplete = complete_and_incomplete_themes()
        SETTINGS = ["\n\nTheme [t]: ",
                    ('starred', self.theme_name),
                    "\nAutohide [a]: ",
                    ('starred', str(self.autohide)),
                    "\nNotify [n]: ",
                    ('starred', str(self.notify_enabled))]
        if self.theme_name in incomplete:
            WARNING = [('name',
                        "\nWARNING: Incomplete theme; "
                        "results may vary!\n"
                        "      (you could try: {})".
                        format(", ".join(complete)))]
            SETTINGS += WARNING
        if show_settings:
            return [TUTORIAL, ('idle', ["\nLoaded "] + spinner), SETTINGS]
        return [TUTORIAL, ('idle', ["\nLoading "] + spinner)]

    @asynch
    def show_main_view(self) -> None:
        def spinning_cursor() -> Any:
            while True:
                for cursor in '|/-\\':
                    yield cursor

        self.capture_stdout()
        spinner = spinning_cursor()
        while not hasattr(self, 'model'):
            self.txt.set_text(self.loading_text([next(spinner)]))
            self.update_screen()
            time.sleep(0.1)
        self.txt.set_controller(self)

        if self.wait_after_loading:
            self.show_settings_after_loading()
        else:
            self.txt.keypress((20, 20), 'enter')

    def show_settings_after_loading(self) -> None:
        self.txt.set_text(self.loading_text([
            u'\u2713  \nPress ',
            ('starred', 'Enter'),
            ' to continue >>\nPress ',
            ('starred', 'h'),
            ' to skip the tutorial from next time and continue.\n\n'
            'You can now toggle some of the settings below by pressing the'
            ' key next to them.'],
            show_settings=True
        ))
        self.update_screen()

    def initialize_loop(self) -> None:
        screen = Screen()
        screen.set_terminal_properties(colors=256)

        self.txt = LoadingView("", align="left")
        fill = urwid.Padding(self.txt, 'center', ('relative', 50))
        fill = urwid.Filler(fill)
        self.loop = urwid.MainLoop(fill,
                                   self.theme,
                                   screen=screen)
        self.update_pipe = self.loop.watch_pipe(self.draw_screen)
        self.exception_pipe = self.loop.watch_pipe(self.raise_exception)

        # Register new ^C handler
        signal.signal(signal.SIGINT, self.exit_handler)

    def main(self) -> None:
        try:
            # TODO: Enable resuming? (in which case, remove ^Z below)
            disabled_keys = {
                'susp': 'undefined',  # Disable ^Z - no suspending
                'stop': 'undefined',  # Disable ^S - enabling shortcut key use
                'quit': 'undefined',  # Disable ^\, ^4
            }
            old_signal_list = self.loop.screen.tty_signal_keys(**disabled_keys)
            self.show_main_view()
            self.loop.run()

        except Exception:
            self.restore_stdout()
            self.loop.screen.tty_signal_keys(*old_signal_list)
            raise

        finally:
            self.restore_stdout()
            self.loop.screen.tty_signal_keys(*old_signal_list)
