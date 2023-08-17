"""
UI views for larger elements such as Streams, Messages, Topics, Help, etc
"""

import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import pytz
import urwid
from typing_extensions import Literal

from zulipterminal.api_types import EditPropagateMode
from zulipterminal.config.keys import (
    HELP_CATEGORIES,
    KEY_BINDINGS,
    is_command_key,
    keys_for_command,
    primary_key_for_command,
)
from zulipterminal.config.markdown_examples import MARKDOWN_ELEMENTS
from zulipterminal.config.symbols import (
    CHECK_MARK,
    COLUMN_TITLE_BAR_LINE,
    PINNED_STREAMS_DIVIDER,
    SECTION_DIVIDER_LINE,
)
from zulipterminal.config.ui_mappings import (
    BOT_TYPE_BY_ID,
    EDIT_MODE_CAPTIONS,
    ROLE_BY_ID,
    STATE_ICON,
    STREAM_ACCESS_TYPE,
    STREAM_POST_POLICY,
)
from zulipterminal.config.ui_sizes import LEFT_WIDTH
from zulipterminal.helper import (
    Message,
    TidiedUserInfo,
    asynch,
    match_emoji,
    match_stream,
    match_user,
)
from zulipterminal.server_url import near_message_url
from zulipterminal.ui_tools.boxes import PanelSearchBox
from zulipterminal.ui_tools.buttons import (
    EmojiButton,
    HomeButton,
    MentionedButton,
    MessageLinkButton,
    PMButton,
    StarredButton,
    StreamButton,
    TopicButton,
    UserButton,
)
from zulipterminal.ui_tools.messages import MessageBox
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.urwid_types import urwid_Size


MIDDLE_COLUMN_MOUSE_SCROLL_LINES = 1
SIDE_PANELS_MOUSE_SCROLL_LINES = 5


class ModListWalker(urwid.SimpleFocusListWalker):
    def __init__(self, *, contents: List[Any], action: Callable[[], None]) -> None:
        self._action = action
        super().__init__(contents)

    def set_focus(self, position: int) -> None:
        # When setting focus via set_focus method.
        self.focus = position
        self._modified()

        self._action()

    def _set_focus(self, index: int) -> None:
        # This method is called when directly setting focus via
        # self.focus = focus_position
        if not self:
            self._focus = 0
            return
        if index < 0 or index >= len(self):
            raise IndexError(f"focus index is out of range: {index}")
        if index != int(index):
            raise IndexError(f"invalid focus index: {index}")
        index = int(index)
        if index != self._focus:
            self._focus_changed(index)
        self._focus = index

        self._action()

    def extend(self, items: List[Any], focus_position: Optional[int] = None) -> int:
        if focus_position is None:
            focus = self._adjust_focus_on_contents_modified(
                slice(len(self), len(self)), items
            )
        else:
            focus = focus_position
        rval = super(urwid.MonitoredFocusList, self).extend(items)
        self._set_focus(focus)
        return rval


class MessageView(urwid.ListBox):
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view
        # Initialize for reference
        self.focus_msg = 0
        self.log = ModListWalker(contents=self.main_view(), action=self.read_message)

        super().__init__(self.log)
        self.set_focus(self.focus_msg)
        # if loading new/old messages - True
        self.old_loading = False
        self.new_loading = False

    def main_view(self) -> List[Any]:
        msg_btn_list = create_msg_box_list(self.model)
        focus_msg = self.model.get_focus_in_current_narrow()
        if focus_msg is None:
            focus_msg = len(msg_btn_list) - 1
        self.focus_msg = focus_msg
        return msg_btn_list

    @asynch
    def load_old_messages(self, anchor: int) -> None:
        self.old_loading = True

        ids_to_keep = self.model.get_message_ids_in_current_narrow()
        if self.log:
            top_message_id = self.log[0].original_widget.message["id"]
            ids_to_keep.remove(top_message_id)  # update this id
            no_update_baseline = {top_message_id}
        else:
            no_update_baseline = set()

        self.model.get_messages(num_before=30, num_after=0, anchor=anchor)
        ids_to_process = self.model.get_message_ids_in_current_narrow() - ids_to_keep

        # Only update if more messages are provided
        if ids_to_process != no_update_baseline:
            if self.log:
                self.log.remove(self.log[0])  # avoid duplication when updating

            message_list = create_msg_box_list(self.model, ids_to_process)
            message_list.reverse()
            for msg_w in message_list:
                self.log.insert(0, msg_w)

            self.set_focus(self.focus_msg)  # Return focus to original message

            self.model.controller.update_screen()

        self.old_loading = False

    @asynch
    def load_new_messages(self, anchor: int) -> None:
        self.new_loading = True
        current_ids = self.model.get_message_ids_in_current_narrow()
        self.model.get_messages(num_before=0, num_after=30, anchor=anchor)
        new_ids = self.model.get_message_ids_in_current_narrow() - current_ids
        if self.log:
            last_message = self.log[-1].original_widget.message
        else:
            last_message = None

        message_list = create_msg_box_list(
            self.model, new_ids, last_message=last_message
        )
        self.log.extend(message_list)

        self.model.controller.update_screen()
        self.new_loading = False

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press":
            if button == 4:
                for _ in range(MIDDLE_COLUMN_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_UP"))
                return True
            if button == 5:
                for _ in range(MIDDLE_COLUMN_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_DOWN"))
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("GO_DOWN", key) and not self.new_loading:
            try:
                position = self.log.next_position(self.focus_position)
                self.set_focus(position, "above")
                self.set_focus_valign("middle")

                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message["id"]
                    self.load_new_messages(id)
                return key

        elif is_command_key("GO_UP", key) and not self.old_loading:
            try:
                position = self.log.prev_position(self.focus_position)
                self.set_focus(position, "below")
                self.set_focus_valign("middle")
                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message["id"]
                    self.load_old_messages(id)
                return key

        elif is_command_key("SCROLL_UP", key) and not self.old_loading:
            if self.focus is not None and self.focus_position == 0:
                return self.keypress(size, primary_key_for_command("GO_UP"))
            else:
                return super().keypress(size, primary_key_for_command("SCROLL_UP"))

        elif is_command_key("SCROLL_DOWN", key) and not self.old_loading:
            if self.focus is not None and self.focus_position == len(self.log) - 1:
                return self.keypress(size, primary_key_for_command("GO_DOWN"))
            else:
                return super().keypress(size, primary_key_for_command("SCROLL_DOWN"))

        elif is_command_key("THUMBS_UP", key) and self.focus is not None:
            message = self.focus.original_widget.message
            self.model.toggle_message_reaction(message, reaction_to_toggle="thumbs_up")

        elif is_command_key("TOGGLE_STAR_STATUS", key) and self.focus is not None:
            message = self.focus.original_widget.message
            self.model.toggle_message_star_status(message)

        key = super().keypress(size, key)
        return key

    def update_search_box_narrow(self, message_view: Any) -> None:
        if not hasattr(self.model.controller, "view"):
            return
        # if view is ready display current narrow
        # at the bottom of the view.
        recipient_bar = message_view.recipient_header()
        top_header = message_view.top_search_bar()
        self.model.controller.view.search_box.conversation_focus.set_text(
            top_header.markup
        )
        self.model.controller.view.search_box.msg_narrow.set_text(recipient_bar.markup)
        self.model.controller.update_screen()

    def read_message(self, index: int = -1) -> None:
        # Message currently in focus
        if hasattr(self.model.controller, "view"):
            view = self.model.controller.view
        else:
            return
        msg_w, curr_pos = self.body.get_focus()
        if msg_w is None:
            return
        self.update_search_box_narrow(msg_w.original_widget)

        # Do not read messages in explore mode.
        if self.model.controller.in_explore_mode:
            return

        # Do not read messages in any search narrow.
        if self.model.is_search_narrow():
            return

        # If this the last message in the view and focus is set on this message
        # then read the message.
        last_message_focused = curr_pos == len(self.log) - 1
        # Only allow reading a message when middle column is
        # in focus.
        if not (view.body.focus_col == 1 or last_message_focused):
            return
        # save the current focus
        self.model.set_focus_in_current_narrow(self.focus_position)
        # msg ids that have been read
        read_msg_ids = list()
        # until we find a read message above the current message
        while msg_w.attr_map == {None: "unread"}:
            msg_id = msg_w.original_widget.message["id"]
            read_msg_ids.append(msg_id)
            self.model.index["messages"][msg_id]["flags"].append("read")
            msg_w.set_attr_map({None: None})
            msg_w, curr_pos = self.body.get_prev(curr_pos)
            if msg_w is None:
                break
        self.model.mark_message_ids_as_read(read_msg_ids)


class StreamsViewDivider(urwid.Divider):
    """
    A custom urwid.Divider to visually separate pinned and unpinned streams.
    """

    def __init__(self) -> None:
        # FIXME: Necessary since the divider is treated as a StreamButton.
        # NOTE: This is specifically for stream search to work correctly.
        self.stream_id = -1
        self.stream_name = ""
        super().__init__(div_char=PINNED_STREAMS_DIVIDER)


class StreamsView(urwid.Frame):
    def __init__(self, streams_btn_list: List[Any], view: Any) -> None:
        self.view = view
        self.log = urwid.SimpleFocusListWalker(streams_btn_list)
        self.streams_btn_list = streams_btn_list
        self.focus_index_before_search = 0
        list_box = urwid.ListBox(self.log)
        self.stream_search_box = PanelSearchBox(
            self, "SEARCH_STREAMS", self.update_streams
        )
        super().__init__(
            list_box,
            header=urwid.Pile(
                [self.stream_search_box, urwid.Divider(SECTION_DIVIDER_LINE)]
            ),
        )
        self.search_lock = threading.Lock()
        self.empty_search = False

    @asynch
    def update_streams(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.is_in_editor_mode():
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong stream list.
        with self.search_lock:
            stream_buttons = [
                (stream, stream.stream_name) for stream in self.streams_btn_list.copy()
            ]
            streams_display = match_stream(
                stream_buttons, new_text, self.view.pinned_streams
            )[0]

            streams_display_num = len(streams_display)
            self.empty_search = streams_display_num == 0

            # Add a divider to separate pinned streams from the rest.
            pinned_stream_names = [
                stream["name"] for stream in self.view.pinned_streams
            ]
            first_unpinned_index = streams_display_num
            for index, stream in enumerate(streams_display):
                if stream.stream_name not in pinned_stream_names:
                    first_unpinned_index = index
                    break
            # Do not add a divider when it is already present. This can
            # happen when new_text=''.
            if first_unpinned_index not in [0, streams_display_num] and not isinstance(
                streams_display[first_unpinned_index], StreamsViewDivider
            ):
                streams_display.insert(first_unpinned_index, StreamsViewDivider())

            self.log.clear()
            if not self.empty_search:
                self.log.extend(streams_display)
            else:
                self.log.extend([self.stream_search_box.search_error])
            self.view.controller.update_screen()

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press":
            if button == 4:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_UP"))
                return True
            elif button == 5:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_DOWN"))
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("SEARCH_STREAMS", key):
            _, self.focus_index_before_search = self.log.get_focus()
            self.set_focus("header")
            self.stream_search_box.set_caption(" ")
            self.view.controller.enter_editor_mode_with(self.stream_search_box)
            return key
        elif is_command_key("GO_BACK", key):
            self.stream_search_box.reset_search_text()
            self.log.clear()
            self.log.extend(self.streams_btn_list)
            self.set_focus("body")
            self.log.set_focus(self.focus_index_before_search)
            self.view.controller.update_screen()
            return key
        return super().keypress(size, key)


class TopicsView(urwid.Frame):
    def __init__(
        self, topics_btn_list: List[Any], view: Any, stream_button: Any
    ) -> None:
        self.view = view
        self.log = urwid.SimpleFocusListWalker(topics_btn_list)
        self.topics_btn_list = topics_btn_list
        self.stream_button = stream_button
        self.focus_index_before_search = 0
        self.list_box = urwid.ListBox(self.log)
        self.topic_search_box = PanelSearchBox(
            self, "SEARCH_TOPICS", self.update_topics
        )
        self.header_list = urwid.Pile(
            [
                self.stream_button,
                urwid.Divider(SECTION_DIVIDER_LINE),
                self.topic_search_box,
                urwid.Divider(SECTION_DIVIDER_LINE),
            ]
        )
        super().__init__(
            self.list_box,
            header=self.header_list,
        )
        self.search_lock = threading.Lock()
        self.empty_search = False

    @asynch
    def update_topics(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.is_in_editor_mode():
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong topics list.
        with self.search_lock:
            new_text = new_text.lower()
            topics_to_display = [
                topic
                for topic in self.topics_btn_list.copy()
                if new_text in topic.topic_name.lower()
            ]
            self.empty_search = len(topics_to_display) == 0

            self.log.clear()
            if not self.empty_search:
                self.log.extend(topics_to_display)
            else:
                self.log.extend([self.topic_search_box.search_error])
            self.view.controller.update_screen()

    def update_topics_list(
        self, stream_id: int, topic_name: str, sender_id: int
    ) -> None:
        # More recent topics are found towards the beginning
        # of the list.
        for topic_iterator, topic_button in enumerate(self.log):
            if topic_button.topic_name == topic_name:
                self.log.insert(0, self.log.pop(topic_iterator))
                self.list_box.set_focus_valign("bottom")
                if sender_id == self.view.model.user_id:
                    self.list_box.set_focus(0)
                return
        # No previous topics with same topic names are found
        # hence we create a new topic button for it.
        new_topic_button = TopicButton(
            stream_id=stream_id,
            topic=topic_name,
            controller=self.view.controller,
            view=self.view,
            count=0,
        )
        self.log.insert(0, new_topic_button)
        self.list_box.set_focus_valign("bottom")
        if sender_id == self.view.model.user_id:
            self.list_box.set_focus(0)

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press":
            if button == 4:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_UP"))
                return True
            elif button == 5:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_DOWN"))
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("SEARCH_TOPICS", key):
            _, self.focus_index_before_search = self.log.get_focus()
            self.set_focus("header")
            self.header_list.set_focus(2)
            self.topic_search_box.set_caption(" ")
            self.view.controller.enter_editor_mode_with(self.topic_search_box)
            return key
        elif is_command_key("GO_BACK", key):
            self.topic_search_box.reset_search_text()
            self.log.clear()
            self.log.extend(self.topics_btn_list)
            self.set_focus("body")
            self.log.set_focus(self.focus_index_before_search)
            self.view.controller.update_screen()
            return key
        return super().keypress(size, key)


class UsersView(urwid.ListBox):
    def __init__(self, controller: Any, users_btn_list: List[Any]) -> None:
        self.users_btn_list = users_btn_list
        self.log = urwid.SimpleFocusListWalker(users_btn_list)
        self.controller = controller
        super().__init__(self.log)

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press":
            if button == 1 and self.controller.is_in_editor_mode():
                return True
            if button == 4:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_UP"))
                return True
            elif button == 5:
                for _ in range(SIDE_PANELS_MOUSE_SCROLL_LINES):
                    self.keypress(size, primary_key_for_command("GO_DOWN"))
        return super().mouse_event(size, event, button, col, row, focus)


class MiddleColumnView(urwid.Frame):
    def __init__(self, view: Any, model: Any, write_box: Any, search_box: Any) -> None:
        message_view = MessageView(model, view)
        self.model = model
        self.controller = model.controller
        self.view = view
        self.search_box = search_box
        view.message_view = message_view
        super().__init__(message_view, header=search_box, footer=write_box)

    def update_message_list_status_markers(self) -> None:
        for message_w in self.body.log:
            message_box = message_w.original_widget

            message_box.update_message_author_status()

        self.controller.update_screen()

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if self.focus_position in ["footer", "header"]:
            return super().keypress(size, key)

        elif is_command_key("SEARCH_MESSAGES", key):
            self.controller.enter_editor_mode_with(self.search_box)
            self.set_focus("header")
            return key

        elif is_command_key("REPLY_MESSAGE", key):
            self.body.keypress(size, key)
            if self.footer.focus is not None:
                self.set_focus("footer")
                self.footer.focus_position = 1
            return key

        elif is_command_key("STREAM_MESSAGE", key):
            self.body.keypress(size, key)
            # For new streams with no previous conversation.
            if self.footer.focus is None:
                stream_id = self.model.stream_id
                stream_dict = self.model.stream_dict
                self.footer.stream_box_view(caption=stream_dict[stream_id]["name"])
            self.set_focus("footer")
            self.footer.focus_position = 0
            return key

        elif is_command_key("REPLY_AUTHOR", key):
            self.body.keypress(size, key)
            if self.footer.focus is not None:
                self.set_focus("footer")
                self.footer.focus_position = 1
            return key

        elif is_command_key("NEXT_UNREAD_TOPIC", key):
            # narrow to next unread topic
            stream_topic = self.model.get_next_unread_topic()
            if stream_topic is None:
                return key
            stream_id, topic = stream_topic
            self.controller.narrow_to_topic(
                stream_name=self.model.stream_dict[stream_id]["name"],
                topic_name=topic,
            )
            return key
        elif is_command_key("NEXT_UNREAD_PM", key):
            # narrow to next unread pm
            pm = self.model.get_next_unread_pm()
            if pm is None:
                return key
            email = self.model.user_id_email_dict[pm]
            self.controller.narrow_to_user(
                recipient_emails=[email],
                contextual_message_id=pm,
            )
        elif is_command_key("PRIVATE_MESSAGE", key):
            # Create new PM message
            self.footer.private_box_view()
            self.set_focus("footer")
            self.footer.focus_position = 0
            return key
        elif is_command_key("GO_LEFT", key):
            self.view.show_left_panel(visible=True)
        elif is_command_key("GO_RIGHT", key):
            self.view.show_right_panel(visible=True)
        return super().keypress(size, key)


class RightColumnView(urwid.Frame):
    """
    Displays the users list on the right side of the app.
    """

    def __init__(self, view: Any) -> None:
        self.view = view
        self.user_search = PanelSearchBox(self, "SEARCH_PEOPLE", self.update_user_list)
        self.view.user_search = self.user_search
        search_box = urwid.Pile([self.user_search, urwid.Divider(SECTION_DIVIDER_LINE)])

        self.allow_update_user_list = True
        self.search_lock = threading.Lock()
        self.empty_search = False
        super().__init__(self.users_view(), header=search_box)

    @asynch
    def update_user_list(
        self,
        search_box: Any = None,
        new_text: Optional[str] = None,
        user_list: Any = None,
    ) -> None:
        """
        Updates user list via PanelSearchBox and _start_presence_updates.
        """
        assert (user_list is None and search_box is not None) or (  # PanelSearchBox.
            user_list is not None and search_box is None and new_text is None
        )  # _start_presence_updates.

        # Return if the method is called by PanelSearchBox (urwid.Edit) while
        # the search is inactive and user_list is None.
        # NOTE: The additional not user_list check is to not false trap
        # _start_presence_updates but allow it to update the user list.
        if not self.view.controller.is_in_editor_mode() and not user_list:
            return

        # Return if the method is called from _start_presence_updates while the
        # search, via PanelSearchBox, is active.
        if not self.allow_update_user_list and new_text is None:
            return

        # wait for any previously started search to finish to avoid
        # displaying wrong user list.
        with self.search_lock:
            if user_list:
                self.view.users = user_list

            users = self.view.users.copy()
            if new_text:
                users_display = [user for user in users if match_user(user, new_text)]
            else:
                users_display = users

            self.empty_search = len(users_display) == 0

            # FIXME Update log directly?
            if not self.empty_search:
                self.body = self.users_view(users_display)
            else:
                self.body = UsersView(
                    self.view.controller, [self.user_search.search_error]
                )
            self.set_body(self.body)
            self.view.controller.update_screen()

    def users_view(self, users: Any = None) -> Any:
        reset_default_view_users = False
        if users is None:
            users = self.view.users.copy()
            reset_default_view_users = True

        users_btn_list = list()
        for user in users:
            if user["user_id"] in self.view.model.muted_users:
                continue
            status = user["status"]
            # Only include `inactive` users in search result.
            if status == "inactive" and not self.view.controller.is_in_editor_mode():
                continue
            unread_count = self.view.model.unread_counts["unread_pms"].get(
                user["user_id"], 0
            )
            is_current_user = user["user_id"] == self.view.model.user_id
            users_btn_list.append(
                UserButton(
                    user=user,
                    controller=self.view.controller,
                    view=self.view,
                    state_marker=STATE_ICON[status],
                    color=f"user_{status}",
                    count=unread_count,
                    is_current_user=is_current_user,
                )
            )
        user_w = UsersView(self.view.controller, users_btn_list)
        # Do not reset them while searching.
        if reset_default_view_users:
            self.users_btn_list = users_btn_list
            self.view.user_w = user_w
        return user_w

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("SEARCH_PEOPLE", key):
            self.allow_update_user_list = False
            self.set_focus("header")
            self.user_search.set_caption(" ")
            self.view.controller.enter_editor_mode_with(self.user_search)
            return key
        elif is_command_key("GO_BACK", key):
            self.user_search.reset_search_text()
            self.allow_update_user_list = True
            self.body = UsersView(self.view.controller, self.users_btn_list)
            self.set_body(self.body)
            self.set_focus("body")
            self.view.controller.update_screen()
            return key
        elif is_command_key("GO_LEFT", key):
            self.view.show_right_panel(visible=False)
        return super().keypress(size, key)


class LeftColumnView(urwid.Pile):
    """
    Displays the buttons at the left column of the app.
    """

    def __init__(self, view: Any) -> None:
        self.model = view.model
        self.view = view
        self.controller = view.controller
        self.menu_v = self.menu_view()
        self.stream_v = self.streams_view()

        self.is_in_topic_view = False
        contents = [(4, self.menu_v), self.stream_v]
        super().__init__(contents)

    def menu_view(self) -> Any:
        count = self.model.unread_counts.get("all_msg", 0)
        self.view.home_button = HomeButton(controller=self.controller, count=count)

        count = self.model.unread_counts.get("all_pms", 0)
        self.view.pm_button = PMButton(controller=self.controller, count=count)

        self.view.mentioned_button = MentionedButton(
            controller=self.controller,
            count=self.model.unread_counts["all_mentions"],
        )

        # Starred messages are by definition read already
        count = len(self.model.initial_data["starred_messages"])
        self.view.starred_button = StarredButton(
            controller=self.controller, count=count
        )
        menu_btn_list = [
            self.view.home_button,
            self.view.pm_button,
            self.view.mentioned_button,
            self.view.starred_button,
        ]
        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self) -> Any:
        streams_btn_list = [
            StreamButton(
                properties=stream,
                controller=self.controller,
                view=self.view,
                count=self.model.unread_counts["streams"].get(stream["id"], 0),
            )
            for stream in self.view.pinned_streams
        ]

        if len(streams_btn_list):
            streams_btn_list += [StreamsViewDivider()]

        streams_btn_list += [
            StreamButton(
                properties=stream,
                controller=self.controller,
                view=self.view,
                count=self.model.unread_counts["streams"].get(stream["id"], 0),
            )
            for stream in self.view.unpinned_streams
        ]

        self.view.stream_id_to_button = {
            stream.stream_id: stream
            for stream in streams_btn_list
            if hasattr(stream, "stream_id")
        }

        self.view.stream_w = StreamsView(streams_btn_list, self.view)
        w = urwid.LineBox(
            self.view.stream_w,
            title="Streams",
            title_attr="column_title",
            tlcorner=COLUMN_TITLE_BAR_LINE,
            tline=COLUMN_TITLE_BAR_LINE,
            trcorner=COLUMN_TITLE_BAR_LINE,
            blcorner="",
            rline="",
            lline="",
            bline="",
            brcorner="",
        )
        return w

    def topics_view(self, stream_button: Any) -> Any:
        stream_id = stream_button.stream_id
        topics = self.model.topics_in_stream(stream_id)
        topics_btn_list = [
            TopicButton(
                stream_id=stream_id,
                topic=topic,
                controller=self.controller,
                view=self.view,
                count=self.model.unread_counts["unread_topics"].get(
                    (stream_id, topic), 0
                ),
            )
            for topic in topics
        ]

        self.view.topic_w = TopicsView(topics_btn_list, self.view, stream_button)
        w = urwid.LineBox(
            self.view.topic_w,
            title="Topics",
            title_attr="column_title",
            tlcorner=COLUMN_TITLE_BAR_LINE,
            tline=COLUMN_TITLE_BAR_LINE,
            trcorner=COLUMN_TITLE_BAR_LINE,
            blcorner="",
            rline="",
            lline="",
            bline="",
            brcorner="",
        )
        return w

    def is_in_topic_view_with_stream_id(self, stream_id: int) -> bool:
        return (
            self.is_in_topic_view
            and stream_id == self.view.topic_w.stream_button.stream_id
        )

    def update_stream_view(self) -> None:
        self.stream_v = self.streams_view()
        if not self.is_in_topic_view:
            self.show_stream_view()

    def show_stream_view(self) -> None:
        self.is_in_topic_view = False
        self.contents[1] = (self.stream_v, self.options(height_type="weight"))

    def show_topic_view(self, stream_button: Any) -> None:
        self.is_in_topic_view = True
        self.contents[1] = (
            self.topics_view(stream_button),
            self.options(height_type="weight"),
        )

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("SEARCH_STREAMS", key) or is_command_key(
            "SEARCH_TOPICS", key
        ):
            self.focus_position = 1
            if self.is_in_topic_view:
                self.view.topic_w.keypress(size, key)
            else:
                self.view.stream_w.keypress(size, key)
            return key
        elif is_command_key("GO_RIGHT", key):
            self.view.show_left_panel(visible=False)
        return super().keypress(size, key)


class TabView(urwid.WidgetWrap):
    """
    Displays a tab that takes up the whole containers height
    and has a flow width.
    Currently used as closed tabs in the autohide layout.
    """

    def __init__(self, text: str) -> None:
        tab_widget_list = [urwid.Text(char) for char in text]
        pile = urwid.Pile(tab_widget_list)
        tab = urwid.Padding(urwid.Filler(pile), left=1, right=1, width=1)

        super().__init__(tab)


# FIXME: This type could be improved, as Any isn't too explicit and clear.
# (this was previously str, but some types passed in can be more complex)
PopUpViewTableContent = Sequence[Tuple[str, Sequence[Union[str, Tuple[str, Any]]]]]


class PopUpView(urwid.Frame):
    def __init__(
        self,
        controller: Any,
        body: List[Any],
        command: str,
        requested_width: int,
        title: str,
        header: Optional[Any] = None,
        footer: Optional[Any] = None,
    ) -> None:
        self.controller = controller
        self.command = command
        self.title = title
        self.log = urwid.SimpleFocusListWalker(body)
        self.body = urwid.ListBox(self.log)

        max_cols, max_rows = controller.maximum_popup_dimensions()

        self.width = min(max_cols, requested_width)

        height = self.calculate_popup_height(body, header, footer, self.width)
        self.height = min(max_rows, height)

        super().__init__(self.body, header=header, footer=footer)

    @staticmethod
    def calculate_popup_height(
        body: List[Any],
        header: Optional[Any],
        footer: Optional[Any],
        popup_width: int,
    ) -> int:
        """
        Returns popup height. The popup height is calculated using urwid's
        .rows method on every widget.
        """
        height = sum(widget.rows((popup_width,)) for widget in body)
        height += header.rows((popup_width,)) if header else 0
        height += footer.rows((popup_width,)) if footer else 0

        return height

    @staticmethod
    def calculate_table_widths(
        contents: PopUpViewTableContent, title_len: int, dividechars: int = 2
    ) -> Tuple[int, List[int]]:
        """
        Returns a tuple that contains the required width for the popup and a
        list that has column widths.
        """
        # Add 4 (for 2 Unicode characters on either side) to the popup title
        # length to make sure that the title gets displayed even when the
        # content or the category is shorter than the title length (+4 Unicode
        # characters).
        title_width = title_len + 4

        category_width = 0
        text_width = 0
        strip_widths = []
        for category, content in contents:
            category_width = max(category_width, len(category))
            for row in content:
                if isinstance(row, str):
                    # Measure the longest line if the text is separated by
                    # newline(s).
                    text_width = max(text_width, len(max(row.split("\n"), key=len)))
                elif isinstance(row, tuple):
                    # Measure the longest line if the text is separated by
                    # newline(s).
                    max_row_lengths = [
                        len(max(text.split("\n"), key=len)) for text in row
                    ]
                    strip_widths.append(max_row_lengths)
        column_widths = [max(width) for width in zip(*strip_widths)]

        popup_width = max(
            sum(column_widths) + dividechars, title_width, category_width, text_width
        )
        return (popup_width, column_widths)

    @staticmethod
    def make_table_with_categories(
        contents: PopUpViewTableContent, column_widths: List[int], dividechars: int = 2
    ) -> List[Any]:
        """
        Returns a list of widgets to render a table with different categories.
        """
        widgets: List[Any] = []
        for category, content in contents:
            if category:
                if len(widgets) > 0:  # Separate categories with newline.
                    widgets.append(urwid.Text(""))
                widgets.append(urwid.Text(("popup_category", category)))
            for index, row in enumerate(content):
                if isinstance(row, str) and row:
                    widgets.append(urwid.Text(row))
                elif isinstance(row, tuple):
                    label, data = row
                    strip = urwid.Columns(
                        [(column_widths[0], urwid.Text(label)), urwid.Text(data)],
                        dividechars=dividechars,
                    )
                    widgets.append(
                        urwid.AttrWrap(strip, None if index % 2 else "popup_contrast")
                    )
        return widgets

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key) or is_command_key(self.command, key):
            self.controller.exit_popup()

        return super().keypress(size, key)


class NoticeView(PopUpView):
    def __init__(
        self, controller: Any, notice_text: Any, width: int, title: str
    ) -> None:
        widgets = [
            urwid.Divider(),
            urwid.Padding(urwid.Text(notice_text), left=1, right=1),
            urwid.Divider(),
        ]
        super().__init__(controller, widgets, "GO_BACK", width, title)


class AboutView(PopUpView):
    def __init__(
        self,
        controller: Any,
        title: str,
        *,
        zt_version: str,
        server_version: str,
        server_feature_level: Optional[int],
        theme_name: str,
        color_depth: int,
        autohide_enabled: bool,
        maximum_footlinks: int,
        notify_enabled: bool,
    ) -> None:
        self.feature_level_content = (
            [("Feature level", str(server_feature_level))]
            if server_feature_level
            else []
        )
        contents = [
            ("Application", [("Zulip Terminal", zt_version)]),
            ("Server", [("Version", server_version)] + self.feature_level_content),
            (
                "Application Configuration",
                [
                    ("Theme", theme_name),
                    ("Autohide", "enabled" if autohide_enabled else "disabled"),
                    ("Maximum footlinks", str(maximum_footlinks)),
                    ("Color depth", str(color_depth)),
                    ("Notifications", "enabled" if notify_enabled else "disabled"),
                ],
            ),
        ]

        popup_width, column_widths = self.calculate_table_widths(contents, len(title))
        widgets = self.make_table_with_categories(contents, column_widths)

        super().__init__(controller, widgets, "ABOUT", popup_width, title)


class UserInfoView(PopUpView):
    def __init__(self, controller: Any, user_id: int, title: str, command: str) -> None:
        display_data, display_custom_profile_data = self._fetch_user_data(
            controller, user_id
        )

        user_details = [
            (key, value) for key, value in display_data.items() if key != "Name"
        ]
        user_view_content = [(display_data["Name"], user_details)]

        if display_custom_profile_data:
            user_view_content.extend(
                [("Additional Details", list(display_custom_profile_data.items()))]
            )

        popup_width, column_widths = self.calculate_table_widths(
            user_view_content, len(title)
        )
        widgets = self.make_table_with_categories(user_view_content, column_widths)

        super().__init__(controller, widgets, command, popup_width, title)

    @staticmethod
    def _fetch_user_data(
        controller: Any, user_id: int
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        # Get user data from model
        data: TidiedUserInfo = controller.model.get_user_info(user_id)

        display_custom_profile_data = {}
        if not data:
            display_data = {
                "Name": "(Unavailable)",
                "Error": "User data not found",
            }
            return (display_data, display_custom_profile_data)

        # Style the data obtained to make it displayable
        display_data = {"Name": data["full_name"]}

        if data["email"]:
            display_data["Email"] = data["email"]
        if data["date_joined"]:
            display_data["Date joined"] = data["date_joined"][:10]
        if data["timezone"]:
            display_data["Timezone"] = data["timezone"].replace("_", " ")

            # Converting all timestamps to UTC
            utc_time = datetime.now()
            tz = pytz.timezone(data["timezone"])
            time = utc_time.astimezone(tz).replace(tzinfo=None).timestamp()

            # Take 24h vs AM/PM format into consideration
            local_time = controller.model.formatted_local_time(
                round(time), show_seconds=False
            )
            display_data["Local time"] = local_time[11:]

        if data["is_bot"]:
            assert data["bot_type"] is not None
            display_data["Role"] = BOT_TYPE_BY_ID.get(
                data["bot_type"], "Unknown Bot Type"
            )
            if data["bot_owner_name"]:
                display_data["Owner"] = data["bot_owner_name"]
        else:
            display_data["Role"] = ROLE_BY_ID[data["role"]]["name"]

            if data["last_active"]:
                display_data["Last active"] = data["last_active"]

        # This will be an empty dict in case of bot users
        custom_profile_data = data["custom_profile_data"]

        if custom_profile_data:
            for field in custom_profile_data:
                if field["type"] == 6:  # Person picker
                    user_names = [
                        controller.model.user_name_from_id(user)
                        for user in field["value"]
                    ]
                    field["value"] = ", ".join(user_names)
                # After conversion of field type 6, all values are str
                assert isinstance(field["value"], str)

                display_custom_profile_data[field["label"]] = field["value"]

        return (display_data, display_custom_profile_data)


class HelpView(PopUpView):
    def __init__(self, controller: Any, title: str) -> None:
        help_menu_content = []
        for category in HELP_CATEGORIES:
            keys_in_category = (
                binding
                for binding in KEY_BINDINGS.values()
                if binding["key_category"] == category
            )
            key_bindings = []
            for binding in keys_in_category:
                key_bindings.append((binding["help_text"], ", ".join(binding["keys"])))
            help_menu_content.append((HELP_CATEGORIES[category], key_bindings))

        popup_width, column_widths = self.calculate_table_widths(
            help_menu_content, len(title)
        )
        widgets = self.make_table_with_categories(help_menu_content, column_widths)

        super().__init__(controller, widgets, "HELP", popup_width, title)


class MarkdownHelpView(PopUpView):
    def __init__(self, controller: Any, title: str) -> None:
        raw_menu_content = []  # to calculate table dimensions
        rendered_menu_content = []  # to display rendered content in table
        user_name = controller.model.user_full_name

        for element in MARKDOWN_ELEMENTS:
            raw_content = element["raw_text"]
            html_element = element["html_element"].format(**dict(user=user_name))

            rendered_content, *_ = MessageBox.transform_content(
                html_element, controller.model.server_url
            )

            raw_menu_content.append((raw_content, raw_content))
            rendered_menu_content.append((raw_content, rendered_content))

        popup_width, column_widths = self.calculate_table_widths(
            [("", raw_menu_content)], len(title)
        )

        header_widgets = [
            urwid.Text([("popup_category", "You type")], align="center"),
            urwid.Text([("popup_category", "You get")], align="center"),
        ]
        header_columns = urwid.Columns(header_widgets)
        header = urwid.Pile([header_columns, urwid.Divider(COLUMN_TITLE_BAR_LINE)])

        body = self.make_table_with_categories(
            [("", rendered_menu_content)], column_widths
        )

        super().__init__(controller, body, "MARKDOWN_HELP", popup_width, title, header)


PopUpConfirmationViewLocation = Literal["top-left", "center"]


class PopUpConfirmationView(urwid.Overlay):
    def __init__(
        self,
        controller: Any,
        question: Any,
        success_callback: Callable[[], None],
        location: PopUpConfirmationViewLocation = "top-left",
    ) -> None:
        self.controller = controller
        self.success_callback = success_callback
        yes = urwid.Button("Yes", self.exit_popup_yes)
        no = urwid.Button("No", self.exit_popup_no)
        yes._w = urwid.AttrMap(urwid.SelectableIcon("Yes", 4), None, "selected")
        no._w = urwid.AttrMap(urwid.SelectableIcon("No", 4), None, "selected")
        display_widget = urwid.GridFlow([yes, no], 3, 5, 1, "center")
        wrapped_widget = urwid.WidgetWrap(display_widget)
        widgets = [question, urwid.Divider(), wrapped_widget]
        prompt = urwid.LineBox(urwid.ListBox(urwid.SimpleFocusListWalker(widgets)))

        if location == "top-left":
            align = "left"
            valign = "top"
            width = LEFT_WIDTH + 1
            height = 8
        else:
            align = "center"
            valign = "middle"

            max_cols, max_rows = controller.maximum_popup_dimensions()
            # +2 to compensate for the LineBox characters.
            width = min(max_cols, max(question.pack()[0], len("Yes"), len("No"))) + 2
            height = min(max_rows, sum(widget.rows((width,)) for widget in widgets)) + 2

        urwid.Overlay.__init__(
            self,
            prompt,
            self.controller.view,
            align=align,
            valign=valign,
            width=width,
            height=height,
        )

    def exit_popup_yes(self, args: Any) -> None:
        self.success_callback()
        self.controller.exit_popup()

    def exit_popup_no(self, args: Any) -> None:
        self.controller.exit_popup()

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key):
            self.controller.exit_popup()
        return super().keypress(size, key)


class StreamInfoView(PopUpView):
    def __init__(self, controller: Any, stream_id: int) -> None:
        self.stream_id = stream_id
        self.controller = controller
        stream = controller.model.stream_dict[stream_id]

        # New in feature level 30, server version 4.0
        stream_creation_date = stream["date_created"]
        date_created = (
            [
                (
                    "Created on",
                    controller.model.formatted_local_time(
                        stream_creation_date, show_seconds=False, show_year=True
                    ),
                )
            ]
            if stream_creation_date is not None
            else []
        )

        message_retention_days = [
            (
                "Message retention days",
                self.controller.model.cached_retention_text[self.stream_id],
            )
        ]

        if "stream_post_policy" in stream:
            stream_policy = STREAM_POST_POLICY[stream["stream_post_policy"]]
        else:
            if stream.get("is_announcement_only"):
                stream_policy = STREAM_POST_POLICY[2]
            else:
                stream_policy = STREAM_POST_POLICY[1]

        total_members = len(stream["subscribers"])

        stream_access_type = controller.model.stream_access_type(stream_id)
        type_of_stream = STREAM_ACCESS_TYPE[stream_access_type]["description"]
        stream_marker = STREAM_ACCESS_TYPE[stream_access_type]["icon"]

        availability_of_history = (
            "Public to Users"
            if stream["history_public_to_subscribers"]
            else "Not Public to Users"
        )
        member_keys = ", ".join(map(repr, keys_for_command("STREAM_MEMBERS")))
        self.stream_email = stream["email_address"]
        email_keys = ", ".join(map(repr, keys_for_command("COPY_STREAM_EMAIL")))

        weekly_traffic = stream["stream_weekly_traffic"]
        weekly_msg_count = (
            "Stream created recently" if weekly_traffic is None else str(weekly_traffic)
        )

        title = f"{stream_marker} {stream['name']}"
        rendered_desc = stream["rendered_description"]
        self.markup_desc, message_links, _ = MessageBox.transform_content(
            rendered_desc,
            self.controller.model.server_url,
        )
        desc = urwid.Text(self.markup_desc)

        stream_info_content = [
            (
                "Stream Details",
                [
                    ("Stream ID", f"{self.stream_id}"),
                    ("Type of Stream", f"{type_of_stream}"),
                ]
                + date_created
                + message_retention_days
                + [
                    ("Weekly Message Count", str(weekly_msg_count)),
                    (
                        "Stream Members",
                        f"{total_members} (Press {member_keys} to view list)",
                    ),
                    (
                        "Stream email",
                        f"Press {email_keys} to copy Stream email address",
                    ),
                    ("History of Stream", f"{availability_of_history}"),
                    ("Posting Policy", f"{stream_policy}"),
                ],
            ),
            ("Stream settings", []),
        ]  # type: PopUpViewTableContent

        popup_width, column_widths = self.calculate_table_widths(
            stream_info_content, len(title)
        )

        muted_setting = urwid.CheckBox(
            label="Muted",
            state=controller.model.is_muted_stream(stream_id),
            checked_symbol=CHECK_MARK,
        )
        urwid.connect_signal(muted_setting, "change", self.toggle_mute_status)
        pinned_state = controller.model.is_pinned_stream(stream_id)
        pinned_setting = urwid.CheckBox(
            label="Pinned to top", state=pinned_state, checked_symbol=CHECK_MARK
        )
        urwid.connect_signal(pinned_setting, "change", self.toggle_pinned_status)
        visual_notification = urwid.CheckBox(
            label="Visual notifications (Terminal/Web/Desktop)",
            state=controller.model.is_visual_notifications_enabled(stream_id),
            checked_symbol=CHECK_MARK,
        )
        urwid.connect_signal(
            visual_notification, "change", self.toggle_visual_notification
        )

        footlinks, footlinks_width = MessageBox.footlinks_view(
            message_links=message_links,
            maximum_footlinks=10,  # Show 'all', as no other way to add them
            padded=False,
            wrap="space",
        )

        # Manual because calculate_table_widths does not support checkboxes.
        # Add 4 to checkbox label to accommodate the checkbox itself.
        popup_width = max(
            popup_width,
            len(muted_setting.label) + 4,
            len(pinned_setting.label) + 4,
            desc.pack()[0],
            footlinks_width,
            len(visual_notification.label) + 4,
        )
        visual_notification_setting = [visual_notification]
        # If notifications is not configured or enabled by the user, then
        # disable the checkbox and mention it explicitly with a suffix text
        if not self.controller.notify_enabled:
            visual_notification_setting = [
                urwid.WidgetDisable(
                    urwid.AttrMap(visual_notification, "widget_disabled")
                ),
                urwid.Text(
                    ("popup_important", "    [notifications not configured or enabled]")
                ),
            ]
        self.widgets = self.make_table_with_categories(
            stream_info_content, column_widths
        )

        # Stream description.
        self.widgets.insert(0, desc)
        desc_newline = 1
        if footlinks:
            self.widgets.insert(1, footlinks)
            desc_newline = 2
        self.widgets.insert(desc_newline, urwid.Text(""))  # Add a newline.

        self.widgets.append(muted_setting)
        self.widgets.append(pinned_setting)
        self.widgets.extend(visual_notification_setting)
        super().__init__(controller, self.widgets, "STREAM_INFO", popup_width, title)

    def toggle_mute_status(self, button: Any, new_state: bool) -> None:
        self.controller.model.toggle_stream_muted_status(self.stream_id)

    def toggle_pinned_status(self, button: Any, new_state: bool) -> None:
        self.controller.model.toggle_stream_pinned_status(self.stream_id)

    def toggle_visual_notification(self, button: Any, new_state: bool) -> None:
        self.controller.model.toggle_stream_visual_notifications(self.stream_id)

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("STREAM_MEMBERS", key):
            self.controller.show_stream_members(stream_id=self.stream_id)
        elif is_command_key("COPY_STREAM_EMAIL", key):
            self.controller.copy_to_clipboard(self.stream_email, "Stream email")
        return super().keypress(size, key)


class StreamMembersView(PopUpView):
    def __init__(self, controller: Any, stream_id: int) -> None:
        self.stream_id = stream_id
        self.controller = controller
        model = controller.model

        user_ids = model.get_other_subscribers_in_stream(stream_id=stream_id)
        user_names = [model.user_name_from_id(id) for id in user_ids]
        sorted_user_names = sorted(user_names)
        sorted_user_names.insert(0, model.user_full_name)
        title = "Stream Members (up/down scrolls)"

        stream_users_content = [("", [(name, "") for name in sorted_user_names])]
        popup_width, column_width = self.calculate_table_widths(
            stream_users_content, len(title)
        )
        widgets = self.make_table_with_categories(stream_users_content, column_width)

        super().__init__(controller, widgets, "STREAM_INFO", popup_width, title)

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key) or is_command_key("STREAM_MEMBERS", key):
            self.controller.show_stream_info(stream_id=self.stream_id)
            return key
        return super().keypress(size, key)


class MsgInfoView(PopUpView):
    def __init__(
        self,
        controller: Any,
        msg: Message,
        title: str,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
    ) -> None:
        self.msg = msg
        self.topic_links = topic_links
        self.message_links = message_links
        self.time_mentions = time_mentions
        self.server_url = controller.model.server_url
        date_and_time = controller.model.formatted_local_time(
            msg["timestamp"], show_seconds=True, show_year=True
        )
        view_in_browser_keys = "[{}]".format(
            ", ".join(map(str, keys_for_command("VIEW_IN_BROWSER")))
        )

        full_rendered_message_keys = "[{}]".format(
            ", ".join(map(str, keys_for_command("FULL_RENDERED_MESSAGE")))
        )
        full_raw_message_keys = "[{}]".format(
            ", ".join(map(str, keys_for_command("FULL_RAW_MESSAGE")))
        )
        msg_info = [
            (
                "",
                [
                    ("Date & Time", date_and_time),
                    ("Sender", msg["sender_full_name"]),
                    ("Sender's Email ID", msg["sender_email"]),
                ],
            )
        ]

        # actions for message info popup
        viewing_actions = (
            "Viewing Actions",
            [
                ("Open in web browser", view_in_browser_keys),
                ("Full rendered message", full_rendered_message_keys),
                ("Full raw message", full_raw_message_keys),
            ],
        )
        msg_info.append(viewing_actions)
        # Only show the 'Edit History' label for edited messages.

        self.show_edit_history_label = (
            self.msg["id"] in controller.model.index["edited_messages"]
            and controller.model.initial_data["realm_allow_edit_history"]
        )
        if self.show_edit_history_label:
            msg_info[0][1][0] = ("Date & Time (Original)", date_and_time)

            keys = "[{}]".format(", ".join(map(str, keys_for_command("EDIT_HISTORY"))))
            msg_info[1][1].append(("Edit History", keys))
        # Render the category using the existing table methods if links exist.
        if message_links:
            msg_info.append(("Message Links", []))
        if topic_links:
            msg_info.append(("Topic Links", []))
        if time_mentions:
            msg_info.append(("Time mentions", time_mentions))
        if msg["reactions"]:
            reactions = sorted(
                (reaction["emoji_name"], reaction["user"]["full_name"])
                for reaction in msg["reactions"]
            )
            grouped_reactions: Dict[str, str] = dict()
            for reaction, user in reactions:
                if reaction in grouped_reactions:
                    grouped_reactions[reaction] += f"\n{user}"
                else:
                    grouped_reactions[reaction] = user
            msg_info.append(("Reactions", list(grouped_reactions.items())))

        popup_width, column_widths = self.calculate_table_widths(msg_info, len(title))
        widgets = self.make_table_with_categories(msg_info, column_widths)

        # To keep track of buttons (e.g., button links) and to facilitate
        # computing their slice indexes
        self.button_widgets: List[Any] = []

        if message_links:
            message_link_widgets, message_link_width = self.create_link_buttons(
                controller, message_links
            )

            # slice_index = Number of labels before message links + 1 newline
            #               + 1 'Message Links' category label.
            #               + 2 for Viewing Actions category label and its newline
            slice_index = len(msg_info[0][1]) + len(msg_info[1][1]) + 2 + 2

            slice_index += sum([len(w) + 2 for w in self.button_widgets])
            self.button_widgets.append(message_links)

            widgets = (
                widgets[:slice_index] + message_link_widgets + widgets[slice_index:]
            )
            popup_width = max(popup_width, message_link_width)

        if topic_links:
            topic_link_widgets, topic_link_width = self.create_link_buttons(
                controller, topic_links
            )

            # slice_index = Number of labels before topic links + 1 newline
            #               + 1 'Topic Links' category label.
            #               + 2 for Viewing Actions category label and its newline
            slice_index = len(msg_info[0][1]) + len(msg_info[1][1]) + 2 + 2
            slice_index += sum([len(w) + 2 for w in self.button_widgets])
            self.button_widgets.append(topic_links)

            widgets = widgets[:slice_index] + topic_link_widgets + widgets[slice_index:]
            popup_width = max(popup_width, topic_link_width)

        super().__init__(controller, widgets, "MSG_INFO", popup_width, title)

    @staticmethod
    def create_link_buttons(
        controller: Any, links: Dict[str, Tuple[str, int, bool]]
    ) -> Tuple[List[MessageLinkButton], int]:
        link_widgets = []
        link_width = 0

        for index, link in enumerate(links):
            text, link_index, _ = links[link]
            if text:
                caption = f"{link_index}: {text}\n{link}"
            else:
                caption = f"{link_index}: {link}"
            link_width = max(link_width, len(max(caption.split("\n"), key=len)))

            display_attr = None if index % 2 else "popup_contrast"
            link_widgets.append(
                MessageLinkButton(
                    controller=controller,
                    caption=caption,
                    link=link,
                    display_attr=display_attr,
                )
            )

        return link_widgets, link_width

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("EDIT_HISTORY", key) and self.show_edit_history_label:
            self.controller.show_edit_history(
                message=self.msg,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
        elif is_command_key("VIEW_IN_BROWSER", key):
            url = near_message_url(self.server_url[:-1], self.msg)
            self.controller.open_in_browser(url)
        elif is_command_key("FULL_RENDERED_MESSAGE", key):
            self.controller.show_full_rendered_message(
                message=self.msg,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
            return key
        elif is_command_key("FULL_RAW_MESSAGE", key):
            self.controller.show_full_raw_message(
                message=self.msg,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
            return key
        return super().keypress(size, key)


class EditModeView(PopUpView):
    def __init__(self, controller: Any, button: Any) -> None:
        self.edit_mode_button = button
        self.widgets: List[urwid.RadioButton] = []

        for mode in EDIT_MODE_CAPTIONS:
            self.add_radio_button(mode)
        super().__init__(
            controller, self.widgets, "ENTER", 62, "Topic edit propagation mode"
        )
        # Set cursor to marked checkbox.
        for i in range(len(self.widgets)):
            if self.widgets[i].state:
                self.body.set_focus(i)

    def set_selected_mode(self, button: Any, new_state: bool, mode: str) -> None:
        if new_state:
            self.edit_mode_button.set_selected_mode(mode)

    def add_radio_button(self, mode: EditPropagateMode) -> None:
        state = mode == self.edit_mode_button.mode
        radio_button = urwid.RadioButton(
            self.widgets, EDIT_MODE_CAPTIONS[mode], state=state
        )
        urwid.connect_signal(radio_button, "change", self.set_selected_mode, mode)

    def keypress(self, size: urwid_Size, key: str) -> str:
        # Use space to select radio-button and exit popup too.
        if key == " ":
            key = "enter"
        return super().keypress(size, key)


EditHistoryTag = Literal["(Current Version)", "(Original Version)", ""]


class EditHistoryView(PopUpView):
    def __init__(
        self,
        controller: Any,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
        title: str,
    ) -> None:
        self.controller = controller
        self.message = message
        self.topic_links = topic_links
        self.message_links = message_links
        self.time_mentions = time_mentions
        width = 64
        widgets: List[Any] = []

        message_history = self.controller.model.fetch_message_history(
            message_id=self.message["id"],
        )
        for index, snapshot in enumerate(message_history):
            if len(widgets) > 0:  # Separate edit blocks with newline.
                widgets.append(urwid.Text(""))

            tag: EditHistoryTag = ""
            if index == 0:
                tag = "(Original Version)"
            elif index == len(message_history) - 1:
                tag = "(Current Version)"

            widgets.append(self._make_edit_block(snapshot, tag))

        if not widgets:
            feedback = [
                "Could not find any message history. See ",
                ("msg_bold", "footer"),
                " for the error message.",
            ]
            widgets.append(urwid.Text(feedback, align="center"))

        super().__init__(controller, widgets, "MSG_INFO", width, title)

    def _make_edit_block(self, snapshot: Dict[str, Any], tag: EditHistoryTag) -> Any:
        content = snapshot["content"]
        topic = snapshot["topic"]
        date_and_time = self.controller.model.formatted_local_time(
            snapshot["timestamp"], show_seconds=True
        )

        user_id = snapshot.get("user_id")
        if user_id:
            author_name = self.controller.model.user_name_from_id(user_id)
        else:
            author_name = "Author N/A"
        author_prefix = self._get_author_prefix(snapshot, tag)
        author = f"{author_prefix} by {author_name}"

        header = [
            urwid.Text(("edit_topic", topic)),
            # 18 = max(EditHistoryTag).
            (18, urwid.Text(("edit_tag", tag), align="right")),
        ]
        subheader = [
            urwid.Text(("edit_author", author)),
            # 22 = len(timestamp).
            (22, urwid.Text(("edit_time", date_and_time), align="right")),
        ]

        edit_block = [
            urwid.AttrWrap(
                urwid.Columns(header, dividechars=2),
                "popup_contrast",
            ),
            urwid.Columns(subheader, dividechars=2),
            urwid.Text(content),
        ]
        return urwid.Pile(edit_block)

    @staticmethod
    def _get_author_prefix(snapshot: Dict[str, Any], tag: EditHistoryTag) -> str:
        if tag == "(Original Version)":
            return "Posted"

        # NOTE: The false alarm bit in the subsequent code block is a
        # workaround for the inconsistency in the message history.
        content = snapshot["content"]
        topic = snapshot["topic"]

        false_alarm_content = content == snapshot.get("prev_content")
        false_alarm_topic = topic == snapshot.get("prev_topic")
        if (
            "prev_topic" in snapshot
            and "prev_content" in snapshot
            and not (false_alarm_content or false_alarm_topic)
        ):
            author_prefix = "Content & Topic edited"
        elif "prev_content" in snapshot and not false_alarm_content:
            author_prefix = "Content edited"
        elif "prev_topic" in snapshot and not false_alarm_topic:
            author_prefix = "Topic edited"
        else:
            author_prefix = "Edited but no changes made"

        return author_prefix

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key) or is_command_key("EDIT_HISTORY", key):
            self.controller.show_msg_info(
                msg=self.message,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
            return key
        return super().keypress(size, key)


class FullRenderedMsgView(PopUpView):
    def __init__(
        self,
        controller: Any,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
        title: str,
    ) -> None:
        self.controller = controller
        self.message = message
        self.topic_links = topic_links
        self.message_links = message_links
        self.time_mentions = time_mentions
        max_cols, max_rows = controller.maximum_popup_dimensions()

        # Get rendered message
        msg_box = MessageBox(message, controller.model, None)

        super().__init__(
            controller,
            [msg_box.content],
            "MSG_INFO",
            max_cols,
            title,
            urwid.Pile(msg_box.header),
            urwid.Pile(msg_box.footer),
        )

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key) or is_command_key(
            "FULL_RENDERED_MESSAGE", key
        ):
            self.controller.show_msg_info(
                msg=self.message,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
            return key
        return super().keypress(size, key)


class FullRawMsgView(PopUpView):
    def __init__(
        self,
        controller: Any,
        message: Message,
        topic_links: Dict[str, Tuple[str, int, bool]],
        message_links: Dict[str, Tuple[str, int, bool]],
        time_mentions: List[Tuple[str, str]],
        title: str,
    ) -> None:
        self.controller = controller
        self.message = message
        self.topic_links = topic_links
        self.message_links = message_links
        self.time_mentions = time_mentions
        max_cols, max_rows = controller.maximum_popup_dimensions()

        # Get rendered message header and footer
        msg_box = MessageBox(message, controller.model, None)

        # Get raw message content widget list
        response = controller.model.fetch_raw_message_content(message["id"])

        if response is None:
            return

        body_list = [urwid.Text(response)]

        super().__init__(
            controller,
            body_list,
            "MSG_INFO",
            max_cols,
            title,
            urwid.Pile(msg_box.header),
            urwid.Pile(msg_box.footer),
        )

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key("GO_BACK", key) or is_command_key("FULL_RAW_MESSAGE", key):
            self.controller.show_msg_info(
                msg=self.message,
                topic_links=self.topic_links,
                message_links=self.message_links,
                time_mentions=self.time_mentions,
            )
            return key
        return super().keypress(size, key)


class EmojiPickerView(PopUpView):
    """
    Displays Emoji Picker view for messages.
    """

    def __init__(
        self,
        controller: Any,
        title: str,
        emoji_units: List[Tuple[str, str, List[str]]],
        message: Message,
        view: Any,
    ) -> None:
        self.view = view
        self.message = message
        self.controller = controller
        self.selected_emojis: Dict[str, str] = {}
        self.emoji_buttons = self.generate_emoji_buttons(emoji_units)
        width = max(len(button.label) for button in self.emoji_buttons)
        max_cols, max_rows = controller.maximum_popup_dimensions()
        popup_width = min(max_cols, width)
        self.emoji_search = PanelSearchBox(
            self, "SEARCH_EMOJIS", self.update_emoji_list
        )
        search_box = urwid.Pile(
            [self.emoji_search, urwid.Divider(SECTION_DIVIDER_LINE)]
        )
        self.empty_search = False
        self.search_lock = threading.Lock()
        super().__init__(
            controller,
            self.emoji_buttons,
            "ADD_REACTION",
            popup_width,
            title,
            header=search_box,
        )
        self.set_focus("header")
        self.controller.enter_editor_mode_with(self.emoji_search)

    @asynch
    def update_emoji_list(
        self,
        search_box: Any = None,
        new_text: Optional[str] = None,
        emoji_list: Any = None,
    ) -> None:
        """
        Updates emoji list via PanelSearchBox.
        """
        assert (emoji_list is None and search_box is not None) or (
            emoji_list is not None and search_box is None and new_text is None
        )

        # Return if the method is called by PanelSearchBox without
        # self.emoji_search being defined.
        if not hasattr(self, "emoji_search"):
            return

        with self.search_lock:
            self.emojis_display = list()
            if new_text and new_text != self.emoji_search.search_text:
                for button in self.emoji_buttons:
                    if match_emoji(button.emoji_name, new_text):
                        self.emojis_display.append(button)
                    else:
                        for alias in button.aliases:
                            if match_emoji(alias, new_text):
                                self.emojis_display.append(button)
                                break
            else:
                self.emojis_display = self.emoji_buttons

            self.empty_search = len(self.emojis_display) == 0

            body_content = self.emojis_display
            if self.empty_search:
                body_content = [self.emoji_search.search_error]

            self.contents["body"] = (
                urwid.ListBox(urwid.SimpleFocusListWalker(body_content)),
                None,
            )
            self.controller.update_screen()

    def is_selected_emoji(self, emoji_name: str) -> bool:
        return emoji_name in self.selected_emojis.values()

    def add_or_remove_selected_emoji(self, emoji_code: str, emoji_name: str) -> None:
        if emoji_name in self.selected_emojis.values():
            self.selected_emojis.pop(emoji_code, None)
        else:
            self.selected_emojis.update({emoji_code: emoji_name})

    def count_reactions(self, emoji_code: str) -> int:
        num_reacts = 0
        for reaction in self.message["reactions"]:
            if reaction["emoji_code"] == emoji_code:
                num_reacts += 1
        return num_reacts

    def generate_emoji_buttons(
        self, emoji_units: List[Tuple[str, str, List[str]]]
    ) -> List[EmojiButton]:
        emoji_buttons = [
            EmojiButton(
                controller=self.controller,
                emoji_unit=emoji_unit,
                message=self.message,
                reaction_count=self.count_reactions(emoji_unit[1]),
                is_selected=self.is_selected_emoji,
                toggle_selection=self.add_or_remove_selected_emoji,
            )
            for emoji_unit in emoji_units
        ]
        sorted_emoji_buttons = sorted(
            emoji_buttons, key=lambda button: button.reaction_count, reverse=True
        )
        return sorted_emoji_buttons

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: int
    ) -> bool:
        if event == "mouse press":
            if button == 1 and self.controller.is_in_editor_mode():
                super().keypress(size, "enter")
                return True
            if button == 4:
                self.keypress(size, "up")
                return True
            elif button == 5:
                self.keypress(size, "down")
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> str:
        if (
            is_command_key("SEARCH_EMOJIS", key)
            and not self.controller.is_in_editor_mode()
        ):
            self.set_focus("header")
            self.emoji_search.set_caption(" ")
            self.controller.enter_editor_mode_with(self.emoji_search)
            return key
        elif is_command_key("GO_BACK", key) or is_command_key("ADD_REACTION", key):
            for emoji_code, emoji_name in self.selected_emojis.items():
                self.controller.model.toggle_message_reaction(self.message, emoji_name)
            self.emoji_search.reset_search_text()
            self.controller.exit_editor_mode()
            self.controller.exit_popup()
            return key
        return super().keypress(size, key)
