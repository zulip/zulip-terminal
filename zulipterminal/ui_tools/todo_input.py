"""Small input popup for interacting with TODO widgets."""

from typing import Any, Callable, Optional

import urwid
from urwid_readline import ReadlineEdit

from zulipterminal.config.keys import is_command_key
from zulipterminal.urwid_types import urwid_Size


class TodoTextInputPopup(urwid.Frame):
    def __init__(
        self,
        controller: Any,
        *,
        title: str,
        prompt: str,
        on_submit: Callable[[str], None],
        initial_text: str = "",
        footer_text: Optional[str] = None,
    ) -> None:
        self.controller = controller
        self.title = title
        self._on_submit = on_submit

        max_cols, max_rows = controller.maximum_popup_dimensions()
        requested_width = max(50, len(prompt) + len(initial_text) + 10)
        self.width = min(max_cols, requested_width)
        self.height = min(max_rows, 5 if footer_text else 3)

        self._edit = ReadlineEdit(f"{prompt} ", edit_text=initial_text)
        body = urwid.Filler(urwid.Padding(self._edit, left=1, right=1))

        footer = (
            urwid.Padding(urwid.Text(footer_text, align="center"), left=1, right=1)
            if footer_text
            else None
        )

        super().__init__(body=body, footer=footer)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("EXIT_POPUP", key):
            self.controller.exit_popup()
            return None

        if key == "enter":
            text = self._edit.edit_text.strip()
            self.controller.exit_popup()
            self._on_submit(text)
            return None

        return super().keypress(size, key)
