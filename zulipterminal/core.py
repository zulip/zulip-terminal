"""
Defines the `Controller`, which sets up the `Model`, `View`, and how they interact
"""

import itertools
import os
import signal
import sys
import time
import webbrowser
from functools import partial
from platform import platform
from types import TracebackType
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import pyperclip
import urwid
import zulip
from typing_extensions import Literal

from zulipterminal.api_types import Composition, Message
from zulipterminal.config.symbols import POPUP_CONTENT_BORDER, POPUP_TOP_LINE
from zulipterminal.config.themes import ThemeSpec
from zulipterminal.config.ui_sizes import (
    MAX_LINEAR_SCALING_WIDTH,
    MIN_SUPPORTED_POPUP_WIDTH,
)
from zulipterminal.helper import asynch, suppress_output
from zulipterminal.model import Model
from zulipterminal.platform_code import PLATFORM
from zulipterminal.ui import Screen, View
from zulipterminal.ui_tools.boxes import WriteBox
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.views import (
    AboutView,
    EditHistoryView,
    EditModeView,
    EmojiPickerView,
    FileUploadView,
    FullRawMsgView,
    FullRenderedMsgView,
    HelpView,
    MarkdownHelpView,
    MsgInfoView,
    NoticeView,
    PopUpConfirmationView,
    StreamInfoView,
    StreamMembersView,
    UserInfoView,
)
from zulipterminal.version import ZT_VERSION


ExceptionInfo = Tuple[Type[BaseException], BaseException, TracebackType]


class Controller:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(
        self,
        *,
        config_file: str,
        maximum_footlinks: int,
        theme_name: str,
        theme: ThemeSpec,
        color_depth: int,
        debug_path: Optional[str],
        in_explore_mode: bool,
        autohide: bool,
        notify: bool,
    ) -> None:
        self.theme_name = theme_name
        self.theme = theme
        self.color_depth = color_depth
        self.in_explore_mode = in_explore_mode
        self.autohide = autohide
        self.notify_enabled = notify
        self.maximum_footlinks = maximum_footlinks

        self.debug_path = debug_path

        self._editor: Optional[Any] = None

        self.active_conversation_info: Dict[str, Any] = {}
        self.is_typing_notification_in_progress = False

        self.show_loading()
        client_identifier = f"ZulipTerminal/{ZT_VERSION} {platform()}"
        self.client = zulip.Client(config_file=config_file, client=client_identifier)
        self.model = Model(self)
        self.view = View(self)
        # Start polling for events after view is rendered.
        self.model.poll_for_events()

        screen = Screen()
        screen.set_terminal_properties(colors=self.color_depth)
        self.loop = urwid.MainLoop(self.view, self.theme, screen=screen)

        # urwid pipe for concurrent screen update handling
        self._update_pipe = self.loop.watch_pipe(self._draw_screen)

        # data and urwid pipe for inter-thread exception handling
        self._exception_info: Optional[ExceptionInfo] = None
        self._critical_exception = False
        self._exception_pipe = self.loop.watch_pipe(self._raise_exception)

        # Register new ^C handler
        signal.signal(signal.SIGINT, self.exit_handler)

    def raise_exception_in_main_thread(
        self, exc_info: ExceptionInfo, *, critical: bool
    ) -> None:
        """
        Sets an exception from another thread, which is cleanly handled
        from within the Controller thread via _raise_exception
        """
        # Exceptions shouldn't occur before the pipe is set
        assert hasattr(self, "_exception_pipe")

        if isinstance(exc_info, tuple):
            self._exception_info = exc_info
            self._critical_exception = critical
        else:
            self._exception_info = (
                RuntimeError,
                f"Invalid cross-thread exception info '{exc_info}'",
                None,
            )
            self._critical_exception = True
        os.write(self._exception_pipe, b"1")

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
                yield from "|/-\\"

        spinner = spinning_cursor()
        sys.stdout.write("\033[92mWelcome to Zulip.\033[0m\n")
        while not hasattr(self, "view"):
            next_spinner = "Loading " + next(spinner)
            sys.stdout.write(next_spinner)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write("\b" * len(next_spinner))

        self.capture_stdout()

    def capture_stdout(self) -> None:
        if hasattr(self, "_stdout"):
            return

        self._stdout = sys.stdout

        if self.debug_path is not None:
            # buffering=1 avoids need for flush=True with print() debugging
            sys.stdout = open(self.debug_path, "a", buffering=1)  # noqa: SIM115
        else:
            # Redirect stdout (print does nothing)
            sys.stdout = open(os.devnull, "a")  # noqa: SIM115

    def restore_stdout(self) -> None:
        if not hasattr(self, "_stdout"):
            return

        sys.stdout.flush()
        sys.stdout.close()
        sys.stdout = self._stdout
        sys.stdout.write("\n")
        del self._stdout

    def update_screen(self) -> None:
        # Update should not happen until pipe is set
        assert hasattr(self, "_update_pipe")
        # Write something to update pipe to trigger draw_screen
        os.write(self._update_pipe, b"1")

    def _draw_screen(self, *args: Any, **kwargs: Any) -> Literal[True]:
        self.loop.draw_screen()
        return True  # Always retain pipe

    def maximum_popup_dimensions(self) -> Tuple[int, int]:
        """
        Returns 3/4th of the screen estate's columns if columns are greater
        than MAX_LINEAR_SCALING_WIDTH else scales accordingly until
        popup width becomes full width at MIN_SUPPORTED_POPUP_WIDTH below
        which popup width remains full width.
        The screen estate's rows are always scaled by 3/4th to get the
        popup rows.
        """

        def clamp(n: int, minn: int, maxn: int) -> int:
            return max(min(maxn, n), minn)

        max_cols, max_rows = self.loop.screen.get_cols_rows()
        min_width = MIN_SUPPORTED_POPUP_WIDTH
        max_width = MAX_LINEAR_SCALING_WIDTH
        # Scale Width
        width = clamp(max_cols, min_width, max_width)
        scaling = 1 - ((width - min_width) / (4 * (max_width - min_width)))
        max_popup_cols = int(scaling * max_cols)
        # Scale Height
        max_popup_rows = 3 * max_rows // 4

        return max_popup_cols, max_popup_rows

    def show_pop_up(self, to_show: Any, style: str) -> None:
        text = urwid.Text(to_show.title, align="center")
        title_map = urwid.AttrMap(urwid.Filler(text), style)
        title_box_adapter = urwid.BoxAdapter(title_map, height=1)
        title_top = urwid.AttrMap(urwid.Divider(POPUP_TOP_LINE), "popup_border")
        title = urwid.Pile([title_top, title_box_adapter])

        content = urwid.LineBox(to_show, **POPUP_CONTENT_BORDER)

        self.loop.widget = urwid.Overlay(
            urwid.AttrMap(urwid.Frame(header=title, body=content), "popup_border"),
            self.view,
            align="center",
            valign="middle",
            # +2 to both of the following, due to LineBox
            # +2 to height, due to title enhancement
            width=to_show.width + 2,
            height=to_show.height + 4,
        )

    def is_any_popup_open(self) -> bool:
        return isinstance(self.loop.widget, urwid.Overlay)

    def exit_popup(self) -> None:
        self.loop.widget = self.view

    def show_help(self) -> None:
        help_view = HelpView(self, "Help Menu (up/down scrolls)")
        self.show_pop_up(help_view, "area:help")

    def show_markdown_help(self) -> None:
        markdown_view = MarkdownHelpView(self, "Markdown Help Menu (up/down scrolls)")
        self.show_pop_up(markdown_view, "area:help")

    def show_topic_edit_mode(self, button: Any) -> None:
        self.show_pop_up(EditModeView(self, button), "area:msg")

    def show_msg_info(
        self,
        msg: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        msg_info_view = MsgInfoView(
            self,
            msg,
            "Message Information (up/down scrolls)",
            topic_links,
            message_links,
            time_mentions,
        )
        self.show_pop_up(msg_info_view, "area:msg")

    def show_file_upload_popup(self, write_box: WriteBox) -> None:
        file_upload_view = FileUploadView(self, write_box, "Upload File")
        self.show_pop_up(file_upload_view, "area:msg")

    def show_emoji_picker(self, message: Message) -> None:
        all_emoji_units = [
            (emoji_name, emoji["code"], emoji["aliases"])
            for emoji_name, emoji in self.model.active_emoji_data.items()
        ]
        emoji_picker_view = EmojiPickerView(
            self, "Add/Remove Emojis", all_emoji_units, message, self.view
        )
        self.show_pop_up(emoji_picker_view, "area:msg")

    def show_stream_info(self, stream_id: int) -> None:
        show_stream_view = StreamInfoView(self, stream_id)
        self.show_pop_up(show_stream_view, "area:stream")

    def show_stream_members(self, stream_id: int) -> None:
        stream_members_view = StreamMembersView(self, stream_id)
        self.show_pop_up(stream_members_view, "area:stream")

    def popup_with_message(self, text: str, width: int) -> None:
        self.show_pop_up(NoticeView(self, text, width, "NOTICE"), "area:error")

    def show_about(self) -> None:
        self.show_pop_up(
            AboutView(
                self,
                "About",
                zt_version=ZT_VERSION,
                server_version=self.model.server_version,
                server_feature_level=self.model.server_feature_level,
                theme_name=self.theme_name,
                color_depth=self.color_depth,
                notify_enabled=self.notify_enabled,
                autohide_enabled=self.autohide,
                maximum_footlinks=self.maximum_footlinks,
            ),
            "area:help",
        )

    def show_user_info(self, user_id: int) -> None:
        self.show_pop_up(
            UserInfoView(
                self, user_id, "User Information (up/down scrolls)", "USER_INFO"
            ),
            "area:user",
        )

    def show_msg_sender_info(self, user_id: int) -> None:
        self.show_pop_up(
            UserInfoView(
                self,
                user_id,
                "Message Sender Information (up/down scrolls)",
                "MSG_SENDER_INFO",
            ),
            "area:user",
        )

    def show_full_rendered_message(
        self,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        self.show_pop_up(
            FullRenderedMsgView(
                self,
                message,
                topic_links,
                message_links,
                time_mentions,
                "Full rendered message (up/down scrolls)",
            ),
            "area:msg",
        )

    def show_full_raw_message(
        self,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        self.show_pop_up(
            FullRawMsgView(
                self,
                message,
                topic_links,
                message_links,
                time_mentions,
                "Full raw message (up/down scrolls)",
            ),
            "area:msg",
        )

    def show_edit_history(
        self,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        self.show_pop_up(
            EditHistoryView(
                self,
                message,
                topic_links,
                message_links,
                time_mentions,
                "Edit History (up/down scrolls)",
            ),
            "area:msg",
        )

    def open_in_browser(self, url: str) -> None:
        """
        Opens any provided URL in a graphical browser, if found, else
        prints an appropriate error message.
        """
        # Don't try to open web browser if running without a GUI
        # TODO: Explore and eventually support opening links in text-browsers.
        if (
            PLATFORM == "Linux"
            and not os.environ.get("DISPLAY")
            and os.environ.get("TERM")
        ):
            self.report_error(
                [
                    "No DISPLAY environment variable specified. This could "
                    "likely mean the ZT host is running without a GUI."
                ]
            )
            return
        try:
            # Checks for a runnable browser in the system and returns
            # its browser controller, if found, else reports an error
            browser_controller = webbrowser.get()
            # Suppress stdout and stderr when opening browser
            with suppress_output():
                browser_controller.open(url)
                self.report_success(
                    [
                        "The link was successfully opened using "
                        f"{browser_controller.name}"
                    ]
                )
        except webbrowser.Error as e:
            # Set a footer text if no runnable browser is located
            self.report_error([f"ERROR: {e}"])

    @asynch
    def show_typing_notification(self) -> None:
        self.is_typing_notification_in_progress = True
        dots = itertools.cycle(["", ".", "..", "..."])

        # Until conversation becomes "inactive" like when a `stop` event is sent
        while self.active_conversation_info:
            sender_name = self.active_conversation_info["sender_name"]
            self.view.set_footer_text(
                [
                    ("footer_contrast", " " + sender_name + " "),
                    " is typing" + next(dots),
                ]
            )
            time.sleep(0.45)

        self.is_typing_notification_in_progress = False
        self.view.set_footer_text()

    def report_error(
        self,
        text: List[Union[str, Tuple[Literal["footer_contrast"], str]]],
        duration: int = 3,
    ) -> None:
        """
        Helper to show an error message in footer
        """
        self.view.set_footer_text(text, "task:error", duration)

    def report_success(
        self,
        text: List[Union[str, Tuple[Literal["footer_contrast"], str]]],
        duration: int = 3,
    ) -> None:
        """
        Helper to show a success message in footer
        """
        self.view.set_footer_text(text, "task:success", duration)

    def report_warning(
        self,
        text: List[Union[str, Tuple[Literal["footer_contrast"], str]]],
        duration: int = 3,
    ) -> None:
        """
        Helper to show a warning message in footer
        """
        self.view.set_footer_text(text, "task:warning", duration)

    def show_media_confirmation_popup(
        self, func: Any, tool: str, media_path: str
    ) -> None:
        callback = partial(func, self, tool, media_path)
        question = urwid.Text(
            [
                "Your requested media has been downloaded to:\n",
                ("bold", media_path),
                "\n\nDo you want the application to open it with ",
                ("bold", tool),
                "?",
            ]
        )
        self.loop.widget = PopUpConfirmationView(
            self, question, callback, location="center"
        )

    def search_messages(self, text: str) -> None:
        # Search for a text in messages
        self.model.index["search"].clear()
        self.model.set_search_narrow(text)

        self.model.get_messages(num_after=0, num_before=30, anchor=10000000000)
        msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list)
        self.view.message_view.log.clear()
        self.view.message_view.log.extend(w_list)
        focus_position = 0
        if 0 <= focus_position < len(w_list):
            self.view.message_view.set_focus(focus_position)

    def save_draft_confirmation_popup(self, draft: Composition) -> None:
        question = urwid.Text(
            "Save this message as a draft? (This will overwrite the existing draft.)"
        )
        save_draft = partial(self.model.save_draft, draft)
        self.loop.widget = PopUpConfirmationView(self, question, save_draft)

    def stream_muting_confirmation_popup(
        self, stream_id: int, stream_name: str
    ) -> None:
        currently_muted = self.model.is_muted_stream(stream_id)
        type_of_action = "unmuting" if currently_muted else "muting"
        question = urwid.Text(
            ("bold", f"Confirm {type_of_action} of stream '{stream_name}' ?"),
            "center",
        )
        mute_this_stream = partial(self.model.toggle_stream_muted_status, stream_id)
        self.loop.widget = PopUpConfirmationView(self, question, mute_this_stream)

    def copy_to_clipboard(self, text: str, text_category: str) -> None:
        try:
            pyperclip.copy(text)
            clipboard_text = pyperclip.paste()
            if clipboard_text == text:
                self.report_success([f"{text_category} copied successfully"])
            else:
                self.report_warning(
                    [f"{text_category} copied, but the clipboard text does not match"]
                )
        except pyperclip.PyperclipException:
            body = [
                "Zulip terminal uses 'pyperclip', for copying texts to your clipboard,"
                " which could not find a copy/paste mechanism for your system. :("
                "\nThis error should only appear on Linux. You can fix this by"
                " installing any ONE of the copy/paste mechanisms below:\n",
                ("msg_bold", "- xclip\n- xsel"),
                "\n\nvia something like:\n",
                ("ui_code", "apt-get install xclip [Recommended]\n"),
                ("ui_code", "apt-get install xsel"),
            ]
            self.show_pop_up(
                NoticeView(self, body, 60, "UTILITY PACKAGE MISSING"), "area:error"
            )

    def _narrow_to(self, anchor: Optional[int], **narrow: Any) -> None:
        already_narrowed = self.model.set_narrow(**narrow)

        if already_narrowed and anchor is None:
            return

        msg_id_list = self.model.get_message_ids_in_current_narrow()

        # If no messages are found in the current narrow
        # OR, given anchor is not present in msg_id_list
        # then, get more messages.
        if len(msg_id_list) == 0 or (anchor is not None and anchor not in msg_id_list):
            self.model.get_messages(num_before=30, num_after=10, anchor=anchor)
            msg_id_list = self.model.get_message_ids_in_current_narrow()

        w_list = create_msg_box_list(self.model, msg_id_list, focus_msg_id=anchor)

        focus_position = self.model.get_focus_in_current_narrow()
        if focus_position is None:  # No available focus; set to end
            focus_position = len(w_list) - 1
        assert focus_position is not None

        self.view.message_view.log.clear()
        if 0 <= focus_position < len(w_list):
            self.view.message_view.log.extend(w_list, focus_position)
        else:
            self.view.message_view.log.extend(w_list)

    def narrow_to_stream(
        self, *, stream_name: str, contextual_message_id: Optional[int] = None
    ) -> None:
        self._narrow_to(anchor=contextual_message_id, stream=stream_name)

    def narrow_to_topic(
        self,
        *,
        stream_name: str,
        topic_name: str,
        contextual_message_id: Optional[int] = None,
    ) -> None:
        self._narrow_to(
            anchor=contextual_message_id,
            stream=stream_name,
            topic=topic_name,
        )

    def narrow_to_user(
        self,
        *,
        recipient_emails: List[str],
        contextual_message_id: Optional[int] = None,
    ) -> None:
        self._narrow_to(
            anchor=contextual_message_id,
            pm_with=", ".join(recipient_emails),
        )

    def narrow_to_all_messages(
        self, *, contextual_message_id: Optional[int] = None
    ) -> None:
        self._narrow_to(anchor=contextual_message_id)

    def narrow_to_all_pm(self, *, contextual_message_id: Optional[int] = None) -> None:
        self._narrow_to(anchor=contextual_message_id, pms=True)

    def narrow_to_all_starred(self) -> None:
        # NOTE: Should we allow maintaining anchor focus here?
        # (nothing currently requires narrowing around a message id)
        self._narrow_to(anchor=None, starred=True)

    def narrow_to_all_mentions(self) -> None:
        # NOTE: Should we allow maintaining anchor focus here?
        # (nothing currently requires narrowing around a message id)
        self._narrow_to(anchor=None, mentioned=True)

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
                "susp": "undefined",  # Disable ^Z - no suspending
                "stop": "undefined",  # Disable ^S - enabling shortcut key use
                "quit": "undefined",  # Disable ^\, ^4
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
