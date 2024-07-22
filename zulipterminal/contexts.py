"""
Tracks the currently focused widget in the UI
"""
import re
from typing import Dict, List, Optional, Tuple, Union

import urwid

from zulipterminal.config.themes import ThemeSpec


# These include contexts that do not have any help hints as well,
# for the sake of completeness
AUTOHIDE_PREFIXES: Dict[Tuple[Union[int, str], ...], str] = {
    (1, 0, 0): "menu_button",
    (1, 0, 1, "body"): "stream_topic_button",
    (1, 0, 1, "header"): "left_panel_search_box",
    (1, "body"): "message_box",
    (1, "header"): "message_search_box",
    (1, "footer"): "compose_box",
    (1, 1, "header"): "user_search_box",
    (1, 1, "body"): "user_button",
}

NON_AUTOHIDE_PREFIXES: Dict[Tuple[Union[int, str], ...], str] = {
    (0, 0): "menu_button",
    (0, 1, "body"): "stream_topic_button",
    (0, 1, "header"): "left_panel_search_box",
    (1, "body"): "message_box",
    (1, "header"): "message_search_box",
    (1, "footer"): "compose_box",
    (2, "header"): "user_search_box",
    (2, "body"): "user_button",
}


class FocusTrackingMainLoop(urwid.MainLoop):
    def __init__(
        self,
        widget: urwid.Widget,
        palette: ThemeSpec,
        screen: Optional[urwid.BaseScreen],
    ) -> None:
        super().__init__(widget, palette, screen)
        self.previous_focus_path = None
        self.view = widget

    def process_input(self, input: List[str]) -> None:
        super().process_input(input)
        self.track_focus_change()

    def track_focus_change(self) -> None:
        focus_path = self.widget.get_focus_path()
        if focus_path != self.previous_focus_path:
            # Update view's context irrespective of the focused widget
            self.view.context = self.get_context_name(focus_path)

            self.previous_focus_path = focus_path

    def get_context_name(self, focus_path: Tuple[Union[int, str]]) -> str:
        widget_in_focus = self.get_widget_in_focus(focus_path)

        if self.widget != self.view:
            overlay_widget_to_context_map = {
                "msg_info_popup": "msg_info",
                "stream_info_popup": "stream_info",
                "emoji_list_popup": "emoji_list",
                "about_popup": "about",
            }
            return overlay_widget_to_context_map.get(widget_in_focus, "popup")

        widget_suffix_to_context_map = {
            "user_button": "user",
            "message_box": "message",
            "stream_topic_button": (
                "topic" if self.widget.left_panel.is_in_topic_view else "stream"
            ),
            "topic": "topic",
            "compose_box": "compose_box",
            "search_box": "editor",
            "button": "button",
        }
        for suffix, context in widget_suffix_to_context_map.items():
            if widget_in_focus.endswith(suffix):
                return context

        return "general"

    def get_widget_in_focus(self, focus_path: Tuple[Union[int, str], ...]) -> str:
        if isinstance(self.widget, urwid.Overlay):
            # NoticeView and PopUpConfirmationView do not shift focus path on opening,
            # until the user presses a recognized key that doesn't close the popup.
            if len(focus_path) > 2:
                # View -> AttrMap -> Frame -> LineBox -> the named Popup
                popup_widget = (
                    self.widget.contents[1][0].original_widget
                ).body.original_widget
                popup_widget_class = popup_widget.__class__.__name__

                if popup_widget_class == "EmojiPickerView":
                    popup_widget_class = (
                        "EmojiSearchView"
                        if focus_path[2] == "header"
                        else "EmojiListView"
                    )

                # PascalCase to snake_case
                return re.sub(
                    r"view",
                    r"popup",
                    re.sub(r"(?<!^)(?=[A-Z])", "_", popup_widget_class).lower(),
                )

            return "unrecognized_widget"

        focus_path = tuple(focus_path[1:])
        prefix_map = (
            AUTOHIDE_PREFIXES
            if self.widget.controller.autohide
            else NON_AUTOHIDE_PREFIXES
        )
        return next(
            (prefix_map[key] for key in prefix_map if focus_path[: len(key)] == key),
            "unrecognized_widget",
        )
