import re
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urljoin, urlparse

import urwid
from typing_extensions import TypedDict

from zulipterminal.api_types import RESOLVED_TOPIC_PREFIX, EditPropagateMode
from zulipterminal.config.keys import is_command_key, primary_key_for_command
from zulipterminal.config.regexes import REGEX_INTERNAL_LINK_STREAM_ID
from zulipterminal.config.symbols import CHECK_MARK, MUTE_MARKER
from zulipterminal.config.ui_mappings import EDIT_MODE_CAPTIONS, STREAM_ACCESS_TYPE
from zulipterminal.helper import Message, StreamData, hash_util_decode, process_media
from zulipterminal.urwid_types import urwid_Size


class TopButton(urwid.Button):
    def __init__(
        self,
        *,
        controller: Any,
        caption: str,
        show_function: Callable[[], Any],
        prefix_character: Union[str, Tuple[Any, str]] = "\N{BULLET}",
        text_color: Optional[str] = None,
        count: int = 0,
        count_style: Optional[str] = None,
    ) -> None:
        self.controller = controller
        self._caption = caption
        self.show_function = show_function
        self.prefix_character = prefix_character
        self.original_color = text_color
        self.count = count
        self.count_style = count_style

        super().__init__("")

        self.button_prefix = urwid.Text("")
        self._label.set_wrap_mode("ellipsis")
        self._label.get_cursor_coords = lambda x: None
        self.button_suffix = urwid.Text("")

        cols = urwid.Columns(
            [
                ("pack", self.button_prefix),
                self._label,
                ("pack", self.button_suffix),
            ]
        )
        self._w = urwid.AttrMap(cols, None, "selected")

        self.update_count(count, text_color)

        urwid.connect_signal(self, "click", self.activate)

    def update_count(self, count: int, text_color: Optional[str] = None) -> None:
        new_color = self.original_color if text_color is None else text_color

        self.count = count
        if count == 0:
            count_text = ""
        else:
            count_text = str(count)

        self.update_widget((self.count_style, count_text), new_color)

    def update_widget(
        self, count_text: Tuple[Optional[str], str], text_color: Optional[str]
    ) -> Any:
        if self.prefix_character:
            prefix = [" ", self.prefix_character, " "]
        else:
            prefix = [" "]
        if count_text[1]:
            suffix = [" ", count_text, " "]
        else:
            suffix = ["  "]
        self.button_prefix.set_text(prefix)
        self.set_label(self._caption)
        self.button_suffix.set_text(suffix)
        self._w.set_attr_map({None: text_color})

    def activate(self, key: Any) -> None:
        self.controller.view.show_left_panel(visible=False)
        self.controller.view.show_right_panel(visible=False)
        self.controller.view.body.focus_col = 1
        self.show_function()

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("ENTER", key):
            self.activate(key)
            return None
        else:  # This is in the else clause, to avoid multiple activation
            return super().keypress(size, key)


class HomeButton(TopButton):
    def __init__(self, *, controller: Any, count: int) -> None:
        button_text = f"All messages     [{primary_key_for_command('ALL_MESSAGES')}]"

        super().__init__(
            controller=controller,
            caption=button_text,
            show_function=controller.narrow_to_all_messages,
            prefix_character="",
            count=count,
            count_style="unread_count",
        )


class PMButton(TopButton):
    def __init__(self, *, controller: Any, count: int) -> None:
        button_text = f"Private messages [{primary_key_for_command('ALL_PM')}]"

        super().__init__(
            controller=controller,
            caption=button_text,
            show_function=controller.narrow_to_all_pm,
            prefix_character="",
            count=count,
            count_style="unread_count",
        )


class MentionedButton(TopButton):
    def __init__(self, *, controller: Any, count: int) -> None:
        button_text = f"Mentions         [{primary_key_for_command('ALL_MENTIONS')}]"

        super().__init__(
            controller=controller,
            caption=button_text,
            show_function=controller.narrow_to_all_mentions,
            prefix_character="",
            count=count,
            count_style="unread_count",
        )


class StarredButton(TopButton):
    def __init__(self, *, controller: Any, count: int) -> None:
        button_text = f"Starred messages [{primary_key_for_command('ALL_STARRED')}]"

        super().__init__(
            controller=controller,
            caption=button_text,
            show_function=controller.narrow_to_all_starred,
            prefix_character="",
            count=count,  # Number of starred messages, not unread count
            count_style="starred_count",
        )


class StreamButton(TopButton):
    def __init__(
        self,
        *,
        properties: StreamData,
        controller: Any,
        view: Any,
        count: int,
    ) -> None:
        # FIXME Is having self.stream_id the best way to do this?
        # (self.stream_id is used elsewhere)
        self.stream_name = properties["name"]
        self.stream_id = properties["id"]
        self.color = properties["color"]
        stream_access_type = properties["stream_access_type"]
        self.description = properties["description"]

        self.model = controller.model
        self.count = count
        self.view = view

        for entry in view.palette:
            if entry[0] is None:
                background = entry[5] if len(entry) > 4 else entry[2]
                inverse_text = background if background else "black"
                break
        view.palette.append(
            (self.color, "", "", "bold", f"{self.color}, bold", background)
        )
        view.palette.append(
            ("s" + self.color, "", "", "standout", inverse_text, self.color)
        )

        stream_marker = STREAM_ACCESS_TYPE[stream_access_type]["icon"]

        narrow_function = partial(
            controller.narrow_to_stream,
            stream_name=self.stream_name,
        )
        super().__init__(
            controller=controller,
            caption=self.stream_name,
            show_function=narrow_function,
            prefix_character=(self.color, stream_marker),
            count=count,
            count_style="unread_count",
        )

        # Mark muted streams 'M' during button creation.
        if self.model.is_muted_stream(self.stream_id):
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget(("muted", MUTE_MARKER), "muted")
        self.view.home_button.update_count(self.model.unread_counts["all_msg"])

    def mark_unmuted(self, unread_count: int) -> None:
        self.update_count(unread_count)
        self.view.home_button.update_count(self.model.unread_counts["all_msg"])

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("TOGGLE_TOPIC", key):
            self.view.left_panel.show_topic_view(self)
        elif is_command_key("TOGGLE_MUTE_STREAM", key):
            self.controller.stream_muting_confirmation_popup(
                self.stream_id, self.stream_name
            )
        elif is_command_key("STREAM_DESC", key):
            self.model.controller.show_stream_info(self.stream_id)
        return super().keypress(size, key)


class UserButton(TopButton):
    def __init__(
        self,
        *,
        user: Dict[str, Any],
        controller: Any,
        view: Any,
        state_marker: str,
        color: Optional[str] = None,
        count: int,
        is_current_user: bool = False,
    ) -> None:
        # Properties accessed externally
        self.email = user["email"]
        self.user_id = user["user_id"]

        self.controller = controller
        self._view = view  # Used in _narrow_with_compose

        # FIXME Is this still needed?
        self.recipients = frozenset({self.user_id, view.model.user_id})

        super().__init__(
            controller=controller,
            caption=user["full_name"],
            show_function=self._narrow_with_compose,
            prefix_character=(color, state_marker),
            text_color=color,
            count=count,
        )
        if is_current_user:
            self.update_widget(("current_user", "(you)"), color)

    def _narrow_with_compose(self) -> None:
        # Switches directly to composing with user
        # FIXME should we just narrow?
        self.controller.narrow_to_user(
            recipient_emails=[self.email],
        )
        self._view.body.focus.original_widget.set_focus("footer")
        self._view.write_box.private_box_view(recipient_user_ids=[self.user_id])

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("USER_INFO", key):
            self.controller.show_user_info(self.user_id)
        return super().keypress(size, key)


class TopicButton(TopButton):
    def __init__(
        self,
        *,
        stream_id: int,
        topic: str,
        controller: Any,
        view: Any,
        count: int,
    ) -> None:
        self.stream_name = controller.model.stream_dict[stream_id]["name"]
        self.topic_name = topic
        self.stream_id = stream_id
        self.model = controller.model
        self.view = view

        narrow_function = partial(
            controller.narrow_to_topic,
            stream_name=self.stream_name,
            topic_name=self.topic_name,
        )

        # The space acts as a TopButton prefix and gives an effective 3 spaces for unresolved topics.
        topic_prefix = " "
        topic_name = self.topic_name
        if self.topic_name.startswith(RESOLVED_TOPIC_PREFIX):
            topic_prefix = self.topic_name[:1]
            topic_name = self.topic_name[2:]

        super().__init__(
            controller=controller,
            caption=topic_name,
            show_function=narrow_function,
            prefix_character=topic_prefix,
            count=count,
            count_style="unread_count",
        )

        if controller.model.is_muted_topic(self.stream_id, self.topic_name):
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget(("muted", MUTE_MARKER), "muted")

    # TODO: Handle event-based approach for topic-muting.

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("TOGGLE_TOPIC", key):
            # Exit topic view
            self.view.left_panel.show_stream_view()
        return super().keypress(size, key)


class EmojiButton(TopButton):
    def __init__(
        self,
        *,
        controller: Any,
        emoji_unit: Tuple[str, str, List[str]],  # (emoji_name, emoji_code, aliases)
        message: Message,
        reaction_count: int = 0,
        is_selected: Callable[[str], bool],
        toggle_selection: Callable[[str, str], None],
    ) -> None:
        self.controller = controller
        self.message = message
        self.is_selected = is_selected
        self.reaction_count = reaction_count
        self.toggle_selection = toggle_selection
        self.emoji_name, self.emoji_code, self.aliases = emoji_unit
        full_button_caption = ", ".join([self.emoji_name, *self.aliases])

        super().__init__(
            controller=controller,
            caption=full_button_caption,
            prefix_character="",
            show_function=self.update_emoji_button,
        )

        has_check_mark = self._has_user_reacted_to_msg() or is_selected(self.emoji_name)
        self.update_widget((None, self.get_update_widget_text(has_check_mark)), None)

    def _has_user_reacted_to_msg(self) -> bool:
        return self.controller.model.has_user_reacted_to_message(
            self.message, emoji_code=self.emoji_code
        )

    def get_update_widget_text(self, user_reacted: bool) -> str:
        count_text = str(self.reaction_count) if self.reaction_count > 0 else ""
        reacted_check_mark = CHECK_MARK if user_reacted else ""
        return f" {reacted_check_mark} {count_text} "

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: int
    ) -> bool:
        if event == "mouse press":
            if button == 1:
                self.keypress(size, primary_key_for_command("ENTER"))
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def update_emoji_button(self) -> None:
        self.toggle_selection(self.emoji_code, self.emoji_name)
        is_reaction_added = self._has_user_reacted_to_msg() != self.is_selected(
            self.emoji_name
        )
        self.reaction_count = (
            (self.reaction_count + 1)
            if is_reaction_added
            else (self.reaction_count - 1)
        )
        self.update_widget((None, self.get_update_widget_text(is_reaction_added)), None)


class DecodedStream(TypedDict):
    stream_id: Optional[int]
    stream_name: Optional[str]


class ParsedNarrowLink(TypedDict, total=False):
    narrow: str
    stream: DecodedStream
    topic_name: str
    message_id: Optional[int]


class MessageLinkButton(urwid.Button):
    def __init__(
        self, *, controller: Any, caption: str, link: str, display_attr: Optional[str]
    ) -> None:
        self.controller = controller
        self.model = self.controller.model
        self.view = self.controller.view
        self.link = link

        super().__init__("")
        self.update_widget(caption, display_attr)
        urwid.connect_signal(self, "click", callback=self.handle_link)

    def update_widget(self, caption: str, display_attr: Optional[str] = None) -> None:
        """
        Overrides the existing button widget for custom styling.
        """
        # Set cursor position next to len(caption) to avoid the cursor.
        icon = urwid.SelectableIcon(caption, cursor_position=len(caption) + 1)
        self._w = urwid.AttrMap(icon, display_attr, focus_map="selected")

    def handle_link(self, *_: Any) -> None:
        """
        Classifies and handles link.
        """
        server_url = self.model.server_url
        if self.link.startswith(urljoin(server_url, "/#narrow/")):
            self.handle_narrow_link()
        elif self.link.startswith(urljoin(server_url, "/user_uploads/")):
            # Exit pop-up promptly, let the media download in the background.
            if self.controller.is_any_popup_open():
                self.controller.exit_popup()
            process_media(self.controller, self.link)

    @staticmethod
    def _decode_stream_data(encoded_stream_data: str) -> DecodedStream:
        """
        Returns a dict with optional stream ID and stream name.
        """
        # Modern links come patched with the stream ID and '-' as delimiters.
        if re.match(REGEX_INTERNAL_LINK_STREAM_ID, encoded_stream_data):
            stream_id, *_ = encoded_stream_data.split("-")
            # Given how encode_stream() in zerver/lib/url_encoding.py
            # replaces ' ' with '-' in the stream name, skip extracting the
            # stream name to avoid any ambiguity.
            return DecodedStream(stream_id=int(stream_id), stream_name=None)
        else:
            # Deprecated links did not start with the stream ID.
            stream_name = hash_util_decode(encoded_stream_data)
            return DecodedStream(stream_id=None, stream_name=stream_name)

    @staticmethod
    def _decode_message_id(message_id: str) -> Optional[int]:
        """
        Returns either the compatible near message ID or None.
        """
        try:
            return int(message_id)
        except ValueError:
            return None

    @classmethod
    def _parse_narrow_link(cls, link: str) -> ParsedNarrowLink:
        """
        Returns either a dict with narrow parameters for supported links or an
        empty dict.
        """
        # NOTE: The optional stream_id link version is deprecated. The extended
        # support is for old messages.
        # We expect the fragment to be one of the following types:
        # a. narrow/stream/[{stream_id}-]{stream-name}
        # b. narrow/stream/[{stream_id}-]{stream-name}/near/{message_id}
        # c. narrow/stream/[{stream_id}-]{stream-name}/topic/
        #    {encoded.20topic.20name}
        # d. narrow/stream/[{stream_id}-]{stream-name}/topic/
        #    {encoded.20topic.20name}/near/{message_id}
        fragments = urlparse(link.rstrip("/")).fragment.split("/")
        len_fragments = len(fragments)
        parsed_link = ParsedNarrowLink()

        if len_fragments == 3 and fragments[1] == "stream":
            stream_data = cls._decode_stream_data(fragments[2])
            parsed_link = dict(narrow="stream", stream=stream_data)

        elif (
            len_fragments == 5 and fragments[1] == "stream" and fragments[3] == "topic"
        ):
            stream_data = cls._decode_stream_data(fragments[2])
            topic_name = hash_util_decode(fragments[4])
            parsed_link = dict(
                narrow="stream:topic", stream=stream_data, topic_name=topic_name
            )

        elif len_fragments == 5 and fragments[1] == "stream" and fragments[3] == "near":
            stream_data = cls._decode_stream_data(fragments[2])
            message_id = cls._decode_message_id(fragments[4])
            parsed_link = dict(
                narrow="stream:near", stream=stream_data, message_id=message_id
            )

        elif (
            len_fragments == 7
            and fragments[1] == "stream"
            and fragments[3] == "topic"
            and fragments[5] == "near"
        ):
            stream_data = cls._decode_stream_data(fragments[2])
            topic_name = hash_util_decode(fragments[4])
            message_id = cls._decode_message_id(fragments[6])
            parsed_link = dict(
                narrow="stream:topic:near",
                stream=stream_data,
                topic_name=topic_name,
                message_id=message_id,
            )

        return parsed_link

    def _validate_and_patch_stream_data(self, parsed_link: ParsedNarrowLink) -> str:
        """
        Validates stream data and patches the optional value in the nested
        DecodedStream dict.
        """
        stream_id = parsed_link["stream"]["stream_id"]
        stream_name = parsed_link["stream"]["stream_name"]
        assert (stream_id is None and stream_name is not None) or (
            stream_id is not None and stream_name is None
        )

        model = self.model
        # Validate stream ID and name.
        if (stream_id and not model.is_user_subscribed_to_stream(stream_id)) or (
            stream_name and not model.is_valid_stream(stream_name)
        ):
            # TODO: Narrow to the concerned stream in a 'preview' mode or
            # report whether the stream id is invalid instead.
            return "The stream seems to be either unknown or unsubscribed"

        # Patch the optional value.
        if not stream_id:
            stream_id = cast(int, model.stream_id_from_name(stream_name))
            parsed_link["stream"]["stream_id"] = stream_id
        else:
            stream_name = cast(str, model.stream_dict[stream_id]["name"])
            parsed_link["stream"]["stream_name"] = stream_name

        return ""

    def _validate_narrow_link(self, parsed_link: ParsedNarrowLink) -> str:
        """
        Returns either an empty string for a successful validation or an
        appropriate validation error.
        """
        if not parsed_link:
            return "The narrow link seems to be either broken or unsupported"

        # Validate stream data.
        if "stream" in parsed_link:
            error = self._validate_and_patch_stream_data(parsed_link)
            if error:
                return error

        # Validate topic name.
        if "topic_name" in parsed_link:
            topic_name = parsed_link["topic_name"]
            stream_id = parsed_link["stream"]["stream_id"]

            if topic_name not in self.model.topics_in_stream(stream_id):
                return "Invalid topic name"

        # Validate message ID for near.
        if "near" in parsed_link["narrow"]:
            message_id = parsed_link.get("message_id")

            if message_id is None:
                return "Invalid message ID"

        return ""

    def _switch_narrow_to(self, parsed_link: ParsedNarrowLink) -> None:
        """
        Switches narrow via narrow_to_* methods.
        """
        narrow = parsed_link["narrow"]
        if "stream" == narrow:
            self.controller.narrow_to_stream(
                stream_name=parsed_link["stream"]["stream_name"],
            )
        elif "stream:near" == narrow:
            self.controller.narrow_to_stream(
                stream_name=parsed_link["stream"]["stream_name"],
                contextual_message_id=parsed_link["message_id"],
            )
        elif "stream:topic" == narrow:
            self.controller.narrow_to_topic(
                stream_name=parsed_link["stream"]["stream_name"],
                topic_name=parsed_link["topic_name"],
            )
        elif "stream:topic:near" == narrow:
            self.controller.narrow_to_topic(
                stream_name=parsed_link["stream"]["stream_name"],
                topic_name=parsed_link["topic_name"],
                contextual_message_id=parsed_link["message_id"],
            )

    def handle_narrow_link(self) -> None:
        """
        Narrows to the respective narrow if the narrow link is valid or updates
        the footer with an appropriate validation error message.
        """
        parsed_link = self._parse_narrow_link(self.link)
        error = self._validate_narrow_link(parsed_link)

        if error:
            self.controller.report_error([f" {error}"])
        else:
            self._switch_narrow_to(parsed_link)

            # Exit pop-up if MessageLinkButton exists in one.
            if self.controller.is_any_popup_open():
                self.controller.exit_popup()


class EditModeButton(urwid.Button):
    def __init__(self, *, controller: Any, width: int) -> None:
        self.controller = controller
        self.width = width
        super().__init__(label="", on_press=controller.show_topic_edit_mode)
        self.set_selected_mode("change_later")  # set default mode

    def set_selected_mode(self, mode: EditPropagateMode) -> None:
        self.mode = mode
        self._w = urwid.AttrMap(
            urwid.SelectableIcon(EDIT_MODE_CAPTIONS[self.mode], self.width),
            None,
            "selected",
        )
