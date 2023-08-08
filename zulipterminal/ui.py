"""
Defines the `View`, and controls where each component is displayed
"""

import random
import re
import time
from typing import Any, Dict, List, Optional

import urwid

from zulipterminal.config.keys import commands_for_random_tips, is_command_key
from zulipterminal.config.symbols import (
    APPLICATION_TITLE_BAR_LINE,
    AUTOHIDE_TAB_LEFT_ARROW,
    AUTOHIDE_TAB_RIGHT_ARROW,
    COLUMN_DIVIDER_LINE,
    COLUMN_TITLE_BAR_LINE,
)
from zulipterminal.config.ui_sizes import LEFT_WIDTH, RIGHT_WIDTH, TAB_WIDTH
from zulipterminal.helper import asynch
from zulipterminal.platform_code import MOUSE_SELECTION_KEY, PLATFORM
from zulipterminal.ui_tools.boxes import MessageSearchBox, WriteBox
from zulipterminal.ui_tools.views import (
    LeftColumnView,
    MiddleColumnView,
    RightColumnView,
    TabView,
)
from zulipterminal.urwid_types import urwid_Box


class View(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.palette = controller.theme
        self.model = controller.model
        self.users = self.model.users
        self.pinned_streams = self.model.pinned_streams
        self.unpinned_streams = self.model.unpinned_streams
        self.write_box = WriteBox(self)
        self.search_box = MessageSearchBox(self.controller)
        self.stream_topic_map: Dict[int, Optional[str]] = {}

        self.message_view: Any = None
        self.displaying_selection_hint = False

        super().__init__(self.main_window())

    def associate_stream_with_topic(self, stream_id: int, topic_name: str) -> None:
        self.stream_topic_map[stream_id] = topic_name

    def saved_topic_in_stream_id(self, stream_id: int) -> Optional[str]:
        return self.stream_topic_map.get(stream_id, None)

    def left_column_view(self) -> Any:
        tab = TabView(
            f"{AUTOHIDE_TAB_LEFT_ARROW} STREAMS & TOPICS {AUTOHIDE_TAB_LEFT_ARROW}"
        )
        panel = LeftColumnView(self)
        return panel, tab

    def middle_column_view(self) -> Any:
        self.middle_column = MiddleColumnView(
            self, self.model, self.write_box, self.search_box
        )
        return urwid.LineBox(
            self.middle_column,
            title="Messages",
            title_attr="column_title",
            tline=COLUMN_TITLE_BAR_LINE,
            bline="",
            trcorner=COLUMN_DIVIDER_LINE,
            tlcorner=COLUMN_DIVIDER_LINE,
        )

    def right_column_view(self) -> Any:
        tab = TabView(f"{AUTOHIDE_TAB_RIGHT_ARROW} USERS {AUTOHIDE_TAB_RIGHT_ARROW}")
        self.users_view = RightColumnView(self)
        panel = urwid.LineBox(
            self.users_view,
            title="Users",
            title_attr="column_title",
            tlcorner=COLUMN_TITLE_BAR_LINE,
            tline=COLUMN_TITLE_BAR_LINE,
            trcorner=COLUMN_TITLE_BAR_LINE,
            lline="",
            blcorner="",
            rline="",
            bline="",
            brcorner="",
        )
        return panel, tab

    def get_random_help(self) -> List[Any]:
        # Get random allowed hotkey (ie. eligible for being displayed as a tip)
        allowed_commands = commands_for_random_tips()
        if not allowed_commands:
            return ["Help(?): "]
        random_command = random.choice(allowed_commands)
        return [
            "Help(?): ",
            ("footer_contrast", " " + ", ".join(random_command["keys"]) + " "),
            " " + random_command["help_text"],
        ]

    @asynch
    def set_footer_text(
        self,
        text_list: Optional[List[Any]] = None,
        style: str = "footer",
        duration: Optional[float] = None,
    ) -> None:
        # Avoid updating repeatedly (then pausing and showing default text)
        # This is simple, though doesn't avoid starting one thread for each call
        if text_list == self._w.footer.text:
            return

        if text_list is None:
            text = self.get_random_help()
        else:
            text = text_list
        self.frame.footer.set_text(text)
        self.frame.footer.set_attr_map({None: style})
        self.controller.update_screen()
        if duration is not None:
            assert duration > 0
            time.sleep(duration)
            self.set_footer_text()

    @asynch
    def set_typeahead_footer(
        self, suggestions: List[str], state: Optional[int], is_truncated: bool
    ) -> None:
        if suggestions:
            # Wrap by space.
            footer_text: List[Any] = [" " + s + " " for s in suggestions]
            if state is not None:
                footer_text[state] = ("footer_contrast", footer_text[state])
            if is_truncated:
                footer_text += [" [more] "]
            footer_text.insert(0, [" "])  # Add leading space.
        else:
            footer_text = [" [No matches found]"]

        self.set_footer_text(footer_text)

    def footer_view(self) -> Any:
        text_header = self.get_random_help()
        return urwid.AttrWrap(urwid.Text(text_header), "footer")

    def main_window(self) -> Any:
        self.left_panel, self.left_tab = self.left_column_view()
        self.center_panel = self.middle_column_view()
        self.right_panel, self.right_tab = self.right_column_view()
        if self.controller.autohide:
            body = [
                (TAB_WIDTH, self.left_tab),
                ("weight", 10, self.center_panel),
                (TAB_WIDTH, self.right_tab),
            ]
        else:
            body = [
                (LEFT_WIDTH, self.left_panel),
                ("weight", 10, self.center_panel),
                (RIGHT_WIDTH, self.right_panel),
            ]
        self.body = urwid.Columns(body, focus_column=0)

        # NOTE: message_view is None, but middle_column_view is called above
        # and sets it.
        assert self.message_view is not None
        # NOTE: set_focus_changed_callback is actually called before the
        # focus is set, so the message is not read yet, it will be read when
        # the focus is changed again either vertically or horizontally.
        self.body._contents.set_focus_changed_callback(self.message_view.read_message)

        title_text = " {full_name} ({email}) - {server_name} ({url}) ".format(
            full_name=self.model.user_full_name,
            email=self.model.user_email,
            server_name=self.model.server_name,
            url=self.model.server_url,
        )

        title_bar = urwid.Columns(
            [
                urwid.Divider(div_char=APPLICATION_TITLE_BAR_LINE),
                (len(title_text), urwid.Text([title_text])),
                urwid.Divider(div_char=APPLICATION_TITLE_BAR_LINE),
            ]
        )

        self.frame = urwid.Frame(
            self.body, title_bar, focus_part="body", footer=self.footer_view()
        )

        # Show left panel on startup in autohide mode
        self.show_left_panel(visible=True)

        return self.frame

    def show_left_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return

        if visible:
            self.frame.body = urwid.Overlay(
                urwid.Columns(
                    [(LEFT_WIDTH, self.left_panel), (1, urwid.SolidFill("▏"))]
                ),
                self.body,
                align="left",
                width=LEFT_WIDTH + 1,
                valign="top",
                height=("relative", 100),
            )
        else:
            self.frame.body = self.body
            # FIXME: This can be avoided after fixing the "sacrificing 1st
            # unread msg" issue and setting focus_column=1 when initializing.
            self.body.focus_position = 1

    def show_right_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return

        if visible:
            self.frame.body = urwid.Overlay(
                urwid.Columns(
                    [(1, urwid.SolidFill("▕")), (RIGHT_WIDTH, self.right_panel)]
                ),
                self.body,
                align="right",
                width=RIGHT_WIDTH + 1,
                valign="top",
                height=("relative", 100),
            )
        else:
            self.frame.body = self.body
            # FIXME: This can be avoided after fixing the "sacrificing 1st
            # unread msg" issue and setting focus_column=1 when initializing.
            self.body.focus_position = 1

    def keypress(self, size: urwid_Box, key: str) -> Optional[str]:
        self.model.new_user_input = True
        if self.controller.is_in_editor_mode():
            return self.controller.current_editor().keypress((size[1],), key)
        # Redirect commands to message_view.
        elif (
            is_command_key("SEARCH_MESSAGES", key)
            or is_command_key("NEXT_UNREAD_TOPIC", key)
            or is_command_key("NEXT_UNREAD_PM", key)
            or is_command_key("STREAM_MESSAGE", key)
            or is_command_key("PRIVATE_MESSAGE", key)
        ):
            self.show_left_panel(visible=False)
            self.show_right_panel(visible=False)
            self.body.focus_col = 1
            self.middle_column.keypress(size, key)
            return key
        elif is_command_key("ALL_PM", key):
            self.pm_button.activate(key)
        elif is_command_key("ALL_STARRED", key):
            self.starred_button.activate(key)
        elif is_command_key("ALL_MENTIONS", key):
            self.mentioned_button.activate(key)
        elif is_command_key("SEARCH_PEOPLE", key):
            # Start User Search if not in editor_mode
            self.show_left_panel(visible=False)
            self.show_right_panel(visible=True)
            self.body.focus_position = 2
            self.users_view.keypress(size, key)
            return key
        elif is_command_key("SEARCH_STREAMS", key) or is_command_key(
            "SEARCH_TOPICS", key
        ):
            # jump stream search
            self.show_right_panel(visible=False)
            self.show_left_panel(visible=True)
            self.body.focus_position = 0
            self.left_panel.keypress(size, key)
            return key
        elif is_command_key("OPEN_DRAFT", key):
            saved_draft = self.model.session_draft_message()
            if saved_draft:
                self.show_left_panel(visible=False)
                self.show_right_panel(visible=False)
                if saved_draft["type"] == "stream":
                    stream_id = self.model.stream_id_from_name(saved_draft["to"])
                    self.write_box.stream_box_view(
                        caption=saved_draft["to"],
                        title=saved_draft["subject"],
                        stream_id=stream_id,
                    )
                elif saved_draft["type"] == "private":
                    recipient_user_ids = saved_draft["to"]
                    self.write_box.private_box_view(
                        recipient_user_ids=recipient_user_ids,
                    )
                content = saved_draft["content"]
                self.write_box.msg_write_box.edit_text = content
                self.write_box.msg_write_box.edit_pos = len(content)
                self.body.focus_col = 1
                self.middle_column.set_focus("footer")
            else:
                self.controller.report_error(
                    ["No draft message was saved in this session."]
                )
            return key
        elif is_command_key("ABOUT", key):
            self.controller.show_about()
            return key
        elif is_command_key("HELP", key):
            # Show help menu
            self.controller.show_help()
            return key
        elif is_command_key("MARKDOWN_HELP", key):
            self.controller.show_markdown_help()
            return key
        return super().keypress(size, key)

    def mouse_event(
        self, size: urwid_Box, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse drag":
            self.model.controller.view.set_footer_text(
                [
                    "Try pressing ",
                    ("footer_contrast", f" {MOUSE_SELECTION_KEY} "),
                    " and dragging to select text.",
                ],
                "task:warning",
            )
            self.displaying_selection_hint = True
        elif event == "mouse release" and self.displaying_selection_hint:
            self.model.controller.view.set_footer_text()
            self.displaying_selection_hint = False

        return super().mouse_event(size, event, button, col, row, focus)


class Screen(urwid.raw_display.Screen):
    def write(self, data: Any) -> None:
        if PLATFORM == "WSL":
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)
