import random
import re
import time
from sys import platform
from typing import Any, List, Optional

import urwid

from zulipterminal.config.keys import commands_for_random_tips, is_command_key
from zulipterminal.config.symbols import (
    APPLICATION_TITLE_BAR_LINE,
    COLUMN_TITLE_BAR_LINE,
)
from zulipterminal.helper import asynch
from zulipterminal.platform_code import PLATFORM
from zulipterminal.ui_tools.boxes import SearchBox, WriteBox
from zulipterminal.ui_tools.views import (
    LeftColumnView,
    MiddleColumnView,
    RightColumnView,
)
from zulipterminal.urwid_types import urwid_Box


class View(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """

    LEFT_WIDTH = 27
    RIGHT_WIDTH = 23

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.palette = controller.theme
        self.model = controller.model
        self.users = self.model.users
        self.pinned_streams = self.model.pinned_streams
        self.unpinned_streams = self.model.unpinned_streams
        self.write_box = WriteBox(self)
        self.search_box = SearchBox(self.controller)

        self.message_view: Any = None
        self.displaying_selection_hint = False

        super().__init__(self.main_window())

    def left_column_view(self) -> Any:
        return LeftColumnView(self)

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
            trcorner="│",
            tlcorner="│",
        )

    def right_column_view(self) -> Any:
        self.users_view = RightColumnView(self)
        return urwid.LineBox(
            self.users_view,
            title="Users",
            title_attr="column_title",
            tlcorner=COLUMN_TITLE_BAR_LINE,
            tline=COLUMN_TITLE_BAR_LINE,
            trcorner=COLUMN_TITLE_BAR_LINE,
            lline="",
            blcorner="─",
            rline="",
            bline="",
            brcorner="",
        )

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
        if text_list is None:
            text = self.get_random_help()
        else:
            text = text_list
        self._w.footer.set_text(text)
        self._w.footer.set_attr_map({None: style})
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
        self.left_panel = self.left_column_view()
        self.center_panel = self.middle_column_view()
        self.right_panel = self.right_column_view()
        if self.controller.autohide:
            body = [
                (View.LEFT_WIDTH, self.left_panel),
                ("weight", 10, self.center_panel),
                (0, self.right_panel),
            ]
        else:
            body = [
                (View.LEFT_WIDTH, self.left_panel),
                ("weight", 10, self.center_panel),
                (View.RIGHT_WIDTH, self.right_panel),
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

        w = urwid.Frame(
            self.body, title_bar, focus_part="body", footer=self.footer_view()
        )
        return w

    def show_left_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return
        width = View.LEFT_WIDTH if visible else 0
        self.body.contents[0] = (
            self.left_panel,
            self.body.options(width_type="given", width_amount=width),
        )
        if visible:
            self.body.focus_position = 0

    def show_right_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return
        width = View.RIGHT_WIDTH if visible else 0
        self.body.contents[2] = (
            self.right_panel,
            self.body.options(width_type="given", width_amount=width),
        )
        if visible:
            self.body.focus_position = 2

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
            self.body.focus_col = 1
            self.middle_column.keypress(size, key)
            return key
        elif is_command_key("ALL_PM", key):
            self.model.controller.narrow_to_all_pm()
            self.body.focus_col = 1
        elif is_command_key("ALL_STARRED", key):
            self.model.controller.narrow_to_all_starred()
            self.body.focus_col = 1
        elif is_command_key("ALL_MENTIONS", key):
            self.model.controller.narrow_to_all_mentions()
            self.body.focus_col = 1
        elif is_command_key("SEARCH_PEOPLE", key):
            # Start User Search if not in editor_mode
            self.body.focus_position = 2
            self.users_view.keypress(size, key)
            self.show_left_panel(visible=False)
            self.show_right_panel(visible=True)
            return key
        elif is_command_key("SEARCH_STREAMS", key) or is_command_key(
            "SEARCH_TOPICS", key
        ):
            # jump stream search
            self.body.focus_position = 0
            self.left_panel.keypress(size, key)
            self.show_right_panel(visible=False)
            self.show_left_panel(visible=True)
            return key
        elif is_command_key("OPEN_DRAFT", key):
            saved_draft = self.model.session_draft_message()
            if saved_draft:
                if saved_draft["type"] == "stream":
                    stream_id = self.model.stream_id_from_name(saved_draft["to"])
                    self.write_box.stream_box_view(
                        caption=saved_draft["to"],
                        title=saved_draft["subject"],
                        stream_id=stream_id,
                    )
                elif saved_draft["type"] == "private":
                    email_list = saved_draft["to"]
                    recipient_user_ids = [
                        self.model.user_dict[email.strip()]["user_id"]
                        for email in email_list
                    ]
                    self.write_box.private_box_view(
                        emails=email_list,
                        recipient_user_ids=recipient_user_ids,
                    )
                content = saved_draft["content"]
                self.write_box.msg_write_box.edit_text = content
                self.write_box.msg_write_box.edit_pos = len(content)
                self.body.focus_col = 1
                self.middle_column.set_focus("footer")
            else:
                self.controller.report_error(
                    "No draft message was saved in this session."
                )
            return key
        elif is_command_key("ABOUT", key):
            self.controller.show_about()
            return key
        elif is_command_key("HELP", key):
            # Show help menu
            self.controller.show_help()
            return key
        # replace alternate keys with arrow/functional keys
        # This is needed for navigating in widgets
        # other than message_view.
        elif is_command_key("GO_UP", key):
            key = "up"
        elif is_command_key("GO_DOWN", key):
            key = "down"
        elif is_command_key("GO_LEFT", key):
            key = "left"
        elif is_command_key("GO_RIGHT", key):
            key = "right"
        elif is_command_key("SCROLL_UP", key):
            key = "page up"
        elif is_command_key("SCROLL_DOWN", key):
            key = "page down"
        elif is_command_key("GO_TO_BOTTOM", key):
            key = "end"
        return super().keypress(size, key)

    def mouse_event(
        self, size: urwid_Box, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse drag":
            selection_key = "Fn + Alt" if platform == "darwin" else "Shift"
            self.model.controller.view.set_footer_text(
                [
                    "Try pressing ",
                    ("footer_contrast", f" {selection_key} "),
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
