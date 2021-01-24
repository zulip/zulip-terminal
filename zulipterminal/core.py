import os
import signal
import sys
import time
from collections import OrderedDict
from functools import partial
from platform import platform
from types import TracebackType
from typing import Any, List, Optional, Tuple, Type

import urwid
import zulip
from typing_extensions import Literal

from zulipterminal.config.themes import ThemeSpec
from zulipterminal.helper import Message, asynch
from zulipterminal.model import Model
from zulipterminal.ui import Screen, View
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.views import (
    AboutView,
    EditHistoryView,
    EditModeView,
    HelpView,
    MsgInfoView,
    NoticeView,
    PopUpConfirmationView,
    StreamInfoView,
    StreamMembersView,
)
from zulipterminal.version import ZT_VERSION


ExceptionInfo = Tuple[Type[BaseException], BaseException, TracebackType]


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str, theme_name: str, theme: ThemeSpec,
                 color_depth: int, in_explore_mode: bool,
                 autohide: bool, notify: bool, footlinks: bool) -> None:
        self.theme_name = theme_name
        self.theme = theme
        self.color_depth = color_depth
        self.in_explore_mode = in_explore_mode
        self.autohide = autohide
        self.notify_enabled = notify
        self.footlinks_enabled = footlinks

        self._editor = None  # type: Optional[Any]

        self.show_loading()
        self.client = zulip.Client(config_file=config_file,
                                   client='ZulipTerminal/{} {}'.
                                          format(ZT_VERSION, platform()))
        self.model = Model(self)
        self.view = View(self)
        # Start polling for events after view is rendered.
        self.model.poll_for_events()

        screen = Screen()
        screen.set_terminal_properties(colors=self.color_depth)
        self.loop = urwid.MainLoop(self.view,
                                   self.theme,
                                   screen=screen)

        # urwid pipe for concurrent screen update handling
        self._update_pipe = self.loop.watch_pipe(self._draw_screen)

        # data and urwid pipe for inter-thread exception handling
        self._exception_info = None  # type: Optional[ExceptionInfo]
        self._critical_exception = False
        self._exception_pipe = self.loop.watch_pipe(self._raise_exception)

        # Register new ^C handler
        signal.signal(signal.SIGINT, self.exit_handler)

    def raise_exception_in_main_thread(self,
                                       exc_info: ExceptionInfo,
                                       *, critical: bool) -> None:
        """
        Sets an exception from another thread, which is cleanly handled
        from within the Controller thread via _raise_exception
        """
        # Exceptions shouldn't occur before the pipe is set
        assert hasattr(self, '_exception_pipe')

        if isinstance(exc_info, tuple):
            self._exception_info = exc_info
            self._critical_exception = critical
        else:
            self._exception_info = (
                RuntimeError,
                "Invalid cross-thread exception info '{}'".format(exc_info),
                None
            )
            self._critical_exception = True
        os.write(self._exception_pipe, b'1')

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

    @asynch
    def show_loading(self) -> None:

        def spinning_cursor() -> Any:
            while True:
                yield from '|/-\\'

        spinner = spinning_cursor()
        sys.stdout.write("\033[92mWelcome to Zulip.\033[0m\n")
        while not hasattr(self, 'view'):
            next_spinner = "Loading " + next(spinner)
            sys.stdout.write(next_spinner)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b' * len(next_spinner))

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
        # Update should not happen until pipe is set
        assert hasattr(self, '_update_pipe')
        # Write something to update pipe to trigger draw_screen
        os.write(self._update_pipe, b'1')

    def _draw_screen(self, *args: Any, **kwargs: Any) -> Literal[True]:
        self.loop.draw_screen()
        return True  # Always retain pipe

    def maximum_popup_dimensions(self) -> Tuple[int, int]:
        """
        Returns 3/4th of the screen estate's columns and rows.
        """
        max_cols, max_rows = map(lambda num: 3 * num // 4,
                                 self.loop.screen.get_cols_rows())
        return max_cols, max_rows

    def show_pop_up(self, to_show: Any, style: str) -> None:
        border_lines = dict(tlcorner='▛', tline='▀', trcorner='▜',
                            rline='▐', lline='▌',
                            blcorner='▙', bline='▄', brcorner='▟')
        text = urwid.Text(to_show.title, align='center')
        title_map = urwid.AttrMap(urwid.Filler(text), style)
        title_box_adapter = urwid.BoxAdapter(title_map, height=1)
        title_box = urwid.LineBox(
            title_box_adapter, tlcorner='▄', tline='▄', trcorner='▄',
            rline='', lline='', blcorner='', bline='', brcorner=''
        )
        title = urwid.AttrMap(title_box, 'popup_border')
        content = urwid.LineBox(to_show, **border_lines)
        self.loop.widget = urwid.Overlay(
            urwid.AttrMap(urwid.Frame(header=title, body=content),
                          'popup_border'),
            self.view,
            align='center',
            valign='middle',
            # +2 to both of the following, due to LineBox
            # +2 to height, due to title enhancement
            width=to_show.width + 2,
            height=to_show.height + 4,
        )

    def exit_popup(self) -> None:
        self.loop.widget = self.view

    def show_help(self) -> None:
        help_view = HelpView(self, "Help Menu (up/down scrolls)")
        self.show_pop_up(help_view, 'area:help')

    def show_topic_edit_mode(self, button: Any) -> None:
        self.show_pop_up(EditModeView(self, button), 'area:msg')

    def show_msg_info(self, msg: Message,
                      message_links: 'OrderedDict[str, Tuple[str, int, bool]]',
                      time_mentions: List[Tuple[str, str]],
                      ) -> None:
        msg_info_view = MsgInfoView(self, msg,
                                    "Message Information (up/down scrolls)",
                                    message_links, time_mentions)
        self.show_pop_up(msg_info_view, 'area:msg')

    def show_stream_info(self, stream_id: int) -> None:
        show_stream_view = StreamInfoView(self, stream_id)
        self.show_pop_up(show_stream_view, 'area:stream')

    def show_stream_members(self, stream_id: int) -> None:
        stream_members_view = StreamMembersView(self, stream_id)
        self.show_pop_up(stream_members_view, 'area:stream')

    def popup_with_message(self, text: str, width: int) -> None:
        self.show_pop_up(NoticeView(self, text, width, "NOTICE"),
                         'area:error')

    def show_about(self) -> None:
        self.show_pop_up(
            AboutView(self, 'About', zt_version=ZT_VERSION,
                      server_version=self.model.server_version,
                      server_feature_level=self.model.server_feature_level,
                      theme_name=self.theme_name, color_depth=self.color_depth,
                      autohide_enabled=self.autohide,
                      footlink_enabled=self.footlinks_enabled),
            'area:help'
        )

    def show_edit_history(
        self, message: Message,
        message_links: 'OrderedDict[str, Tuple[str, int, bool]]',
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        self.show_pop_up(
            EditHistoryView(self, message, message_links, time_mentions,
                            'Edit History (up/down scrolls)'),
            'area:msg'
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

    def save_draft_confirmation_popup(self, message: Message) -> None:
        question = urwid.Text('Save this message as a draft?'
                              ' (This will overwrite the existing draft.)')
        save_draft = partial(self.model.save_draft, message)
        self.loop.widget = PopUpConfirmationView(self, question, save_draft)

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
        queue_id = self.model.queue_id
        self.client.deregister(queue_id, 1.0)

    def exit_handler(self, signum: int, frame: Any) -> None:
        self.deregister_client()
        sys.exit(0)

    def _raise_exception(self, *args: Any, **kwargs: Any) -> Literal[True]:
        if self._exception_info is not None:
            exc = self._exception_info
            if self._critical_exception:
                raise exc[0].with_traceback(exc[1], exc[2])
            else:
                import traceback
                exception_logfile = "zulip-terminal-thread-exceptions.log"
                with open(exception_logfile, "a") as logfile:
                    traceback.print_exception(*exc, file=logfile)
                message = (
                    "An exception occurred:"
                    + "\n\n"
                    + "".join(traceback.format_exception_only(exc[0], exc[1]))
                    + "\n"
                    + "The application should continue functioning, but you "
                    + "may notice inconsistent behavior in this session."
                    + "\n\n"
                    + "Please report this to us either in"
                    + "\n"
                    + "* the #zulip-terminal stream"
                    + "\n"
                    + "  (https://chat.zulip.org/#narrow/stream/"
                    + "206-zulip-terminal in the webapp)"
                    + "\n"
                    + "* an issue at "
                    + "https://github.com/zulip/zulip-terminal/issues"
                    + "\n\n"
                    + "Details of the exception can be found in "
                    + exception_logfile
                )
                self.popup_with_message(message, width=80)
                self._exception_info = None
        return True  # If don't raise, retain pipe

    def main(self) -> None:
        try:
            # TODO: Enable resuming? (in which case, remove ^Z below)
            disabled_keys = {
                'susp': 'undefined',  # Disable ^Z - no suspending
                'stop': 'undefined',  # Disable ^S - enabling shortcut key use
                'quit': 'undefined',  # Disable ^\, ^4
            }
            old_signal_list = self.loop.screen.tty_signal_keys(**disabled_keys)
            self.loop.run()

        except Exception:
            self.restore_stdout()
            self.loop.screen.tty_signal_keys(*old_signal_list)
            raise

        finally:
            self.restore_stdout()
            self.loop.screen.tty_signal_keys(*old_signal_list)
