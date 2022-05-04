import re
import typing
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from time import sleep, time
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import dateutil.parser
import urwid
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from typing_extensions import Literal
from tzlocal import get_localzone
from urwid_readline import ReadlineEdit

from zulipterminal.api_types import Composition, PrivateComposition, StreamComposition
from zulipterminal.config.keys import (
    is_command_key,
    keys_for_command,
    primary_key_for_command,
)
from zulipterminal.config.regexes import (
    REGEX_CLEANED_RECIPIENT,
    REGEX_RECIPIENT_EMAIL,
    REGEX_STREAM_AND_TOPIC_FENCED,
    REGEX_STREAM_AND_TOPIC_FENCED_HALF,
    REGEX_STREAM_AND_TOPIC_UNFENCED,
)
from zulipterminal.config.symbols import (
    INVALID_MARKER,
    MESSAGE_CONTENT_MARKER,
    MESSAGE_HEADER_DIVIDER,
    QUOTED_TEXT_MARKER,
    STREAM_TOPIC_SEPARATOR,
    TIME_MENTION_MARKER,
)
from zulipterminal.config.ui_mappings import STATE_ICON, STREAM_ACCESS_TYPE
from zulipterminal.helper import (
    Message,
    asynch,
    format_string,
    get_unused_fence,
    match_emoji,
    match_group,
    match_stream,
    match_topics,
    match_user,
    match_user_name_and_email,
)
from zulipterminal.server_url import near_message_url
from zulipterminal.ui_tools.buttons import EditModeButton
from zulipterminal.ui_tools.tables import render_table
from zulipterminal.urwid_types import urwid_Size


if typing.TYPE_CHECKING:
    from zulipterminal.model import Model


class _MessageEditState(NamedTuple):
    message_id: int
    old_topic: str


DELIMS_MESSAGE_COMPOSE = "\t\n;"


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super().__init__(self.main_view(True))
        self.model = view.model
        self.view = view

        # Used to indicate user's compose status, "closed" by default
        self.compose_box_status: Literal[
            "open_with_private", "open_with_stream", "closed"
        ]

        # If editing a message, its state - otherwise None
        self.msg_edit_state: Optional[_MessageEditState]
        # Determines if the message body (content) can be edited
        self.msg_body_edit_enabled: bool

        self.is_in_typeahead_mode = False

        # Set to int for stream box only
        self.stream_id: Optional[int]

        # Used in PM and stream boxes
        # (empty list implies PM box empty, or not initialized)
        # Prioritizes autocomplete in message body
        self.recipient_user_ids: List[int]

        # Updates server on PM typing events
        # Is separate from recipient_user_ids because we
        # don't include the user's own id in this list
        self.typing_recipient_user_ids: List[int]

        # Private message recipient text entry, None if stream-box
        # or not initialized
        self.to_write_box: Optional[ReadlineEdit]

        # For tracking sending typing status updates
        self.send_next_typing_update: datetime
        self.last_key_update: datetime
        self.idle_status_tracking: bool
        self.sent_start_typing_status: bool

        self._set_compose_attributes_to_defaults()

        # Constant indices into self.contents
        # (CONTAINER=vertical, HEADER/MESSAGE=horizontal)
        self.FOCUS_CONTAINER_HEADER = 0
        self.FOCUS_HEADER_BOX_RECIPIENT = 0
        self.FOCUS_HEADER_BOX_STREAM = 1
        self.FOCUS_HEADER_BOX_TOPIC = 3
        self.FOCUS_HEADER_BOX_EDIT = 4
        self.FOCUS_CONTAINER_MESSAGE = 1
        self.FOCUS_MESSAGE_BOX_BODY = 0
        # These are included to allow improved clarity
        # FIXME: These elements don't acquire focus; replace prefix & in above?
        self.FOCUS_HEADER_PREFIX_STREAM = 0
        self.FOCUS_HEADER_PREFIX_TOPIC = 2

    def _set_compose_attributes_to_defaults(self) -> None:
        self.compose_box_status = "closed"

        self.msg_edit_state = None
        self.msg_body_edit_enabled = True

        self.stream_id = None
        self.to_write_box = None

        # Maintain synchrony between *_user_ids by setting them
        # to empty lists together using the helper method.
        self._set_regular_and_typing_recipient_user_ids(None)

        self.send_next_typing_update = datetime.now()
        self.last_key_update = datetime.now()
        self.idle_status_tracking = False
        self.sent_start_typing_status = False

        if hasattr(self, "msg_write_box"):
            self.msg_write_box.edit_text = ""

    def main_view(self, new: bool) -> Any:
        if new:
            return []
        else:
            self.contents.clear()

    def set_editor_mode(self) -> None:
        self.view.controller.enter_editor_mode_with(self)

    def _set_regular_and_typing_recipient_user_ids(
        self, user_id_list: Optional[List[int]]
    ) -> None:
        if user_id_list:
            self.recipient_user_ids = user_id_list
            self.typing_recipient_user_ids = [
                user_id
                for user_id in self.recipient_user_ids
                if user_id != self.model.user_id
            ]
        else:
            self.recipient_user_ids = list()
            self.typing_recipient_user_ids = list()

    def send_stop_typing_status(self) -> None:
        # Send 'stop' updates only for PM narrows, when there are recipients
        # to send to and a prior 'start' status has already been sent.
        if (
            self.compose_box_status == "open_with_private"
            and self.typing_recipient_user_ids
            and self.sent_start_typing_status
        ):
            self.model.send_typing_status_by_user_ids(
                self.typing_recipient_user_ids, status="stop"
            )
            self.send_next_typing_update = datetime.now()
            self.idle_status_tracking = False
            self.sent_start_typing_status = False

    def private_box_view(
        self,
        *,
        recipient_user_ids: Optional[List[int]] = None,
    ) -> None:

        self.set_editor_mode()

        self.compose_box_status = "open_with_private"

        if recipient_user_ids:
            self._set_regular_and_typing_recipient_user_ids(recipient_user_ids)
            self.recipient_emails = [
                self.model.user_id_email_dict[user_id]
                for user_id in self.recipient_user_ids
            ]
            recipient_info = ", ".join(
                [
                    f"{self.model.user_dict[email]['full_name']} <{email}>"
                    for email in self.recipient_emails
                ]
            )
        else:
            self._set_regular_and_typing_recipient_user_ids(None)
            self.recipient_emails = []
            recipient_info = ""

        self.send_next_typing_update = datetime.now()
        self.to_write_box = ReadlineEdit("To: ", edit_text=recipient_info)
        self.to_write_box.enable_autocomplete(
            func=self._to_box_autocomplete,
            key=primary_key_for_command("AUTOCOMPLETE"),
            key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
        )
        self.to_write_box.set_completer_delims("")

        self.msg_write_box = ReadlineEdit(
            multiline=True, max_char=self.model.max_message_length
        )
        self.msg_write_box.enable_autocomplete(
            func=self.generic_autocomplete,
            key=primary_key_for_command("AUTOCOMPLETE"),
            key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
        )
        self.msg_write_box.set_completer_delims(DELIMS_MESSAGE_COMPOSE)

        self.header_write_box = urwid.Columns([self.to_write_box])
        header_line_box = urwid.LineBox(
            self.header_write_box,
            tlcorner="━",
            tline="━",
            trcorner="━",
            lline="",
            blcorner="─",
            bline="─",
            brcorner="─",
            rline="",
        )
        self.contents = [
            (header_line_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.focus_position = self.FOCUS_CONTAINER_MESSAGE

        # Typing status is sent in regular intervals to limit the number of
        # notifications sent. Idleness should also prompt a notification.
        # Refer to https://zulip.com/api/set-typing-status for the protocol
        # on typing notifications sent by clients.
        TYPING_STARTED_WAIT_PERIOD = 10
        TYPING_STOPPED_WAIT_PERIOD = 5

        start_period_delta = timedelta(seconds=TYPING_STARTED_WAIT_PERIOD)
        stop_period_delta = timedelta(seconds=TYPING_STOPPED_WAIT_PERIOD)

        def on_type_send_status(edit: object, new_edit_text: str) -> None:
            if new_edit_text and self.typing_recipient_user_ids:
                self.last_key_update = datetime.now()
                if self.last_key_update > self.send_next_typing_update:
                    self.model.send_typing_status_by_user_ids(
                        self.typing_recipient_user_ids, status="start"
                    )
                    self.send_next_typing_update += start_period_delta
                    self.sent_start_typing_status = True
                    # Initiate tracker function only if it isn't already
                    # initiated.
                    if not self.idle_status_tracking:
                        self.idle_status_tracking = True
                        track_idleness_and_update_status()

        @asynch
        def track_idleness_and_update_status() -> None:
            while datetime.now() < self.last_key_update + stop_period_delta:
                idle_check_time = (
                    self.last_key_update + stop_period_delta - datetime.now()
                )
                sleep(idle_check_time.total_seconds())
            self.send_stop_typing_status()

        urwid.connect_signal(self.msg_write_box, "change", on_type_send_status)

    def update_recipients(self, write_box: ReadlineEdit) -> None:
        self.recipient_emails = re.findall(REGEX_RECIPIENT_EMAIL, write_box.edit_text)
        self._set_regular_and_typing_recipient_user_ids(
            [self.model.user_dict[email]["user_id"] for email in self.recipient_emails]
        )

    def _tidy_valid_recipients_and_notify_invalid_ones(
        self, write_box: ReadlineEdit
    ) -> bool:
        tidied_recipients = list()
        invalid_recipients = list()

        recipients = [
            recipient.strip()
            for recipient in write_box.edit_text.split(",")
            if recipient.strip()  # This condition avoids whitespace recipients (",  ,")
        ]

        for recipient in recipients:
            cleaned_recipient_list = re.findall(REGEX_CLEANED_RECIPIENT, recipient)
            recipient_name, recipient_email, invalid_text = cleaned_recipient_list[0]
            # Discard invalid_text as part of tidying up the recipient.

            if recipient_email and self.model.is_valid_private_recipient(
                recipient_email, recipient_name
            ):
                tidied_recipients.append(f"{recipient_name} <{recipient_email}>")
            else:
                invalid_recipients.append(recipient)
                tidied_recipients.append(recipient)

        write_box.edit_text = ", ".join(tidied_recipients)
        write_box.edit_pos = len(write_box.edit_text)

        if invalid_recipients:
            invalid_recipients_error = [
                "Invalid recipient(s) - " + ", ".join(invalid_recipients),
                " - Use ",
                ("footer_contrast", primary_key_for_command("AUTOCOMPLETE")),
                " or ",
                (
                    "footer_contrast",
                    primary_key_for_command("AUTOCOMPLETE_REVERSE"),
                ),
                " to autocomplete.",
            ]
            self.view.controller.report_error(invalid_recipients_error)
            return False

        return True

    def _setup_common_stream_compose(
        self, stream_id: int, caption: str, title: str
    ) -> None:
        self.set_editor_mode()
        self.compose_box_status = "open_with_stream"
        self.stream_id = stream_id
        self.recipient_user_ids = self.model.get_other_subscribers_in_stream(
            stream_id=stream_id
        )
        self.msg_write_box = ReadlineEdit(
            multiline=True, max_char=self.model.max_message_length
        )
        self.msg_write_box.enable_autocomplete(
            func=self.generic_autocomplete,
            key=primary_key_for_command("AUTOCOMPLETE"),
            key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
        )
        self.msg_write_box.set_completer_delims(DELIMS_MESSAGE_COMPOSE)

        self.title_write_box = ReadlineEdit(
            edit_text=title, max_char=self.model.max_topic_length
        )
        self.title_write_box.enable_autocomplete(
            func=self._topic_box_autocomplete,
            key=primary_key_for_command("AUTOCOMPLETE"),
            key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
        )
        self.title_write_box.set_completer_delims("")

        # NOTE: stream marker should be set during initialization
        self.header_write_box = urwid.Columns(
            [
                ("pack", urwid.Text(("default", "?"))),
                self.stream_write_box,
                ("pack", urwid.Text(STREAM_TOPIC_SEPARATOR)),
                self.title_write_box,
            ],
            dividechars=1,
        )
        header_line_box = urwid.LineBox(
            self.header_write_box,
            tlcorner="━",
            tline="━",
            trcorner="━",
            lline="",
            blcorner="─",
            bline="─",
            brcorner="─",
            rline="",
        )
        write_box = [
            (header_line_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def stream_box_view(
        self, stream_id: int, caption: str = "", title: str = ""
    ) -> None:
        self.stream_write_box = ReadlineEdit(
            edit_text=caption, max_char=self.model.max_stream_name_length
        )
        self.stream_write_box.enable_autocomplete(
            func=self._stream_box_autocomplete,
            key=primary_key_for_command("AUTOCOMPLETE"),
            key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
        )
        self.stream_write_box.set_completer_delims("")
        self._setup_common_stream_compose(stream_id, caption, title)

        # Use and set a callback to set the stream marker
        self._set_stream_write_box_style(None, caption)
        urwid.connect_signal(
            self.stream_write_box, "change", self._set_stream_write_box_style
        )

    def stream_box_edit_view(
        self, stream_id: int, caption: str = "", title: str = ""
    ) -> None:
        self.stream_write_box = urwid.Text(caption)
        self._setup_common_stream_compose(stream_id, caption, title)

        self.edit_mode_button = EditModeButton(
            controller=self.model.controller,
            width=20,
        )
        self.header_write_box.widget_list.append(self.edit_mode_button)

        # Use callback to set stream marker - it shouldn't change, so don't need signal
        self._set_stream_write_box_style(None, caption)

    def _set_stream_write_box_style(self, widget: ReadlineEdit, new_text: str) -> None:
        # FIXME: Refactor when we have ~ Model.is_private_stream
        stream_marker = INVALID_MARKER
        color = "general_bar"
        if self.model.is_valid_stream(new_text):
            stream_id = self.model.stream_id_from_name(new_text)
            stream_access_type = self.model.stream_access_type(stream_id)
            stream_marker = STREAM_ACCESS_TYPE[stream_access_type]["icon"]
            stream = self.model.stream_dict[stream_id]
            color = stream["color"]
        self.header_write_box[self.FOCUS_HEADER_PREFIX_STREAM].set_text(
            (color, stream_marker)
        )

    def _to_box_autocomplete(self, text: str, state: Optional[int]) -> Optional[str]:
        users_list = self.view.users
        recipients = text.rsplit(",", 1)

        # Use the most recent recipient for autocomplete.
        previous_recipients = f"{recipients[0]}, " if len(recipients) > 1 else ""
        latest_text = recipients[-1].strip()

        matching_users = [
            user for user in users_list if match_user_name_and_email(user, latest_text)
        ]

        # Append the potential autocompleted recipients to the string
        # containing the previous recipients.
        updated_recipients = [
            f"{previous_recipients}{user['full_name']} <{user['email']}>"
            for user in matching_users
        ]

        user_names = [user["full_name"] for user in matching_users]

        return self._process_typeaheads(updated_recipients, state, user_names)

    def _topic_box_autocomplete(self, text: str, state: Optional[int]) -> Optional[str]:
        topic_names = self.model.topics_in_stream(self.stream_id)

        topic_typeaheads = match_topics(topic_names, text)

        # Typeaheads and suggestions are the same.
        return self._process_typeaheads(topic_typeaheads, state, topic_typeaheads)

    def _stream_box_autocomplete(
        self, text: str, state: Optional[int]
    ) -> Optional[str]:
        streams_list = self.view.pinned_streams + self.view.unpinned_streams
        streams = [stream["name"] for stream in streams_list]

        # match_streams takes stream names and typeaheads,
        # but we don't have typeaheads here.
        # FIXME: Refactor match_stream
        stream_data = list(zip(streams, streams))
        matched_streams = match_stream(stream_data, text, self.view.pinned_streams)

        # matched_streams[0] and matched_streams[1] contains the same data.
        return self._process_typeaheads(matched_streams[0], state, matched_streams[1])

    def generic_autocomplete(self, text: str, state: Optional[int]) -> Optional[str]:
        autocomplete_map = OrderedDict(
            [
                ("@_", self.autocomplete_users),
                ("@_**", self.autocomplete_users),
                ("@", self.autocomplete_mentions),
                ("@*", self.autocomplete_groups),
                ("@**", self.autocomplete_users),
                ("#", self.autocomplete_streams),
                ("#**", self.autocomplete_streams),
                (":", self.autocomplete_emojis),
            ]
        )

        # Look in a reverse order to find the last autocomplete prefix used in
        # the text. For instance, if text='@#example', use '#' as the prefix.
        # FIXME: Mentions can actually start with '#', and streams with
        #        anything; this implementation simply chooses the right-most
        #        match of the longest length
        prefix_indices = {prefix: text.rfind(prefix) for prefix in autocomplete_map}

        text = self.validate_and_patch_autocomplete_stream_and_topic(
            text, autocomplete_map, prefix_indices
        )

        found_prefix_indices = {
            prefix: index for prefix, index in prefix_indices.items() if index > -1
        }
        # Return text if it doesn't have any of the autocomplete prefixes.
        if not found_prefix_indices:
            return text

        # Use latest longest matching prefix (so @_ wins vs @)
        prefix_index = max(found_prefix_indices.values())
        prefix = max(
            (len(prefix), prefix)
            for prefix, index in found_prefix_indices.items()
            if index == prefix_index
        )[1]
        autocomplete_func = autocomplete_map[prefix]

        # NOTE: The following block only executes if any of the autocomplete
        # prefixes exist.
        typeaheads, suggestions = autocomplete_func(text[prefix_index:], prefix)

        typeahead = self._process_typeaheads(typeaheads, state, suggestions)
        if typeahead:
            typeahead = text[:prefix_index] + typeahead
        return typeahead

    def _process_typeaheads(
        self, typeaheads: List[str], state: Optional[int], suggestions: List[str]
    ) -> Optional[str]:
        num_suggestions = 10
        fewer_typeaheads = typeaheads[:num_suggestions]
        reduced_suggestions = suggestions[:num_suggestions]
        is_truncated = len(fewer_typeaheads) != len(typeaheads)

        if (
            state is not None
            and state < len(fewer_typeaheads)
            and state >= -len(fewer_typeaheads)
        ):
            typeahead: Optional[str] = fewer_typeaheads[state]
        else:
            typeahead = None
            state = None
        self.is_in_typeahead_mode = True
        self.view.set_typeahead_footer(reduced_suggestions, state, is_truncated)
        return typeahead

    def autocomplete_mentions(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        # Handles user mentions (@ mentions and silent mentions)
        # and group mentions.

        user_typeahead, user_names = self.autocomplete_users(text, prefix_string)
        group_typeahead, groups = self.autocomplete_groups(text, prefix_string)

        combined_typeahead = user_typeahead + group_typeahead
        combined_names = user_names + groups

        return combined_typeahead, combined_names

    def autocomplete_users(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        users_list = self.view.users
        matching_users = [
            user for user in users_list if match_user(user, text[len(prefix_string) :])
        ]
        matching_ids = set([user["user_id"] for user in matching_users])
        matching_recipient_ids = set(self.recipient_user_ids) & set(matching_ids)
        # Display subscribed users/recipients first.
        sorted_matching_users = sorted(
            matching_users,
            key=lambda user: user["user_id"] in matching_recipient_ids,
            reverse=True,
        )

        user_names = [user["full_name"] for user in sorted_matching_users]

        # Counter holds a count of each name in the list of users' names in a
        # dict-like manner, which is a more efficient approach when compared to
        # slicing the original list on each name.
        # FIXME: Use a persistent counter rather than generate one on each autocomplete.
        user_names_counter = Counter(user_names)

        # Append user_id's to users with the same names.
        user_names_with_distinct_duplicates = [
            f"{user['full_name']}|{user['user_id']}"
            if user_names_counter[user["full_name"]] > 1
            else user["full_name"]
            for user in sorted_matching_users
        ]

        extra_prefix = "{}{}".format(
            "*" if prefix_string[-1] != "*" else "",
            "*" if prefix_string[-2:] != "**" else "",
        )
        user_typeahead = format_string(
            user_names_with_distinct_duplicates, prefix_string + extra_prefix + "{}**"
        )

        return user_typeahead, user_names

    def autocomplete_groups(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        prefix_length = len(prefix_string)
        groups = [
            group_name
            for group_name in self.model.user_group_names
            if match_group(group_name, text[prefix_length:])
        ]

        extra_prefix = "*" if prefix_string[-1] != "*" else ""
        group_typeahead = format_string(groups, prefix_string + extra_prefix + "{}*")
        return group_typeahead, groups

    def autocomplete_streams(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        streams_list = self.view.pinned_streams + self.view.unpinned_streams
        streams = [stream["name"] for stream in streams_list]
        stream_typeahead = format_string(streams, "#**{}**")
        stream_data = list(zip(stream_typeahead, streams))

        prefix_length = len(prefix_string)

        matched_data = match_stream(
            stream_data, text[prefix_length:], self.view.pinned_streams
        )
        return matched_data

    def autocomplete_stream_and_topic(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        match = re.search(REGEX_STREAM_AND_TOPIC_FENCED_HALF, text)

        stream = match.group(1) if match else ""

        if self.model.is_valid_stream(stream):
            stream_id = self.model.stream_id_from_name(stream)
            topic_names = self.model.topics_in_stream(stream_id)
        else:
            topic_names = []

        topic_suggestions = match_topics(topic_names, text[len(prefix_string) :])

        topic_typeaheads = format_string(topic_suggestions, prefix_string + "{}**")

        return topic_typeaheads, topic_suggestions

    def validate_and_patch_autocomplete_stream_and_topic(
        self,
        text: str,
        autocomplete_map: "OrderedDict[str, Callable[..., Any]]",
        prefix_indices: Dict[str, int],
    ) -> str:
        """
        Checks if a prefix string is possible candidate for stream+topic autocomplete.
        If the prefix matches, we update the autocomplete_map and prefix_indices,
        and return the (updated) text.
        """
        match = re.search(REGEX_STREAM_AND_TOPIC_FENCED_HALF, text)
        match_fenced = re.search(REGEX_STREAM_AND_TOPIC_FENCED, text)
        match_unfenced = re.search(REGEX_STREAM_AND_TOPIC_UNFENCED, text)
        if match:
            prefix = f"#**{match.group(1)}>"
            prefix_indices[prefix] = match.start()
        elif match_fenced:
            # Amending the prefix to remove stream fence `**`
            prefix = f"#**{match_fenced.group(1)}>"
            prefix_with_topic = prefix + match_fenced.group(2)
            prefix_indices[prefix] = match_fenced.start()
            # Amending the text to have new prefix (without `**` fence)
            text = text[: match_fenced.start()] + prefix_with_topic
        elif match_unfenced:
            prefix = f"#**{match_unfenced.group(1)}>"
            prefix_with_topic = prefix + match_unfenced.group(2)
            prefix_indices[prefix] = match_unfenced.start()
            # Amending the text to have new prefix (with `**` fence)
            text = text[: match_unfenced.start()] + prefix_with_topic
        if match or match_fenced or match_unfenced:
            autocomplete_map.update({prefix: self.autocomplete_stream_and_topic})

        return text

    def autocomplete_emojis(
        self, text: str, prefix_string: str
    ) -> Tuple[List[str], List[str]]:
        emoji_list = self.model.all_emoji_names
        emojis = [emoji for emoji in emoji_list if match_emoji(emoji, text[1:])]
        emoji_typeahead = format_string(emojis, ":{}:")

        return emoji_typeahead, emojis

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if self.is_in_typeahead_mode:
            if not (
                is_command_key("AUTOCOMPLETE", key)
                or is_command_key("AUTOCOMPLETE_REVERSE", key)
            ):
                # set default footer when done with autocomplete
                self.is_in_typeahead_mode = False
                self.view.set_footer_text()

        if is_command_key("SEND_MESSAGE", key):
            self.send_stop_typing_status()
            if self.compose_box_status == "open_with_stream":
                if re.fullmatch(r"\s*", self.title_write_box.edit_text):
                    topic = "(no topic)"
                else:
                    topic = self.title_write_box.edit_text

                if self.msg_edit_state is not None:
                    trimmed_topic = topic.strip()
                    # Trimmed topic must be compared since that is server check
                    if trimmed_topic == self.msg_edit_state.old_topic:
                        propagate_mode = "change_one"  # No change in topic
                    else:
                        propagate_mode = self.edit_mode_button.mode

                    args = dict(
                        message_id=self.msg_edit_state.message_id,
                        topic=topic,  # NOTE: Send untrimmed topic always for now
                        propagate_mode=propagate_mode,
                    )
                    if self.msg_body_edit_enabled:
                        args["content"] = self.msg_write_box.edit_text

                    success = self.model.update_stream_message(**args)
                else:
                    success = self.model.send_stream_message(
                        stream=self.stream_write_box.edit_text,
                        topic=topic,
                        content=self.msg_write_box.edit_text,
                    )
            else:
                if self.msg_edit_state is not None:
                    success = self.model.update_private_message(
                        content=self.msg_write_box.edit_text,
                        msg_id=self.msg_edit_state.message_id,
                    )
                else:
                    all_valid = self._tidy_valid_recipients_and_notify_invalid_ones(
                        self.to_write_box
                    )
                    if not all_valid:
                        return key
                    self.update_recipients(self.to_write_box)
                    if self.recipient_user_ids:
                        success = self.model.send_private_message(
                            recipients=self.recipient_user_ids,
                            content=self.msg_write_box.edit_text,
                        )
                    else:
                        self.view.controller.report_error(
                            ["Cannot send message without specifying recipients."]
                        )
                        success = None
            if success:
                self.msg_write_box.edit_text = ""
                if self.msg_edit_state is not None:
                    self.keypress(size, primary_key_for_command("GO_BACK"))
                    assert self.msg_edit_state is None
        elif is_command_key("NARROW_MESSAGE_RECIPIENT", key):
            if self.compose_box_status == "open_with_stream":
                self.model.controller.narrow_to_topic(
                    stream_name=self.stream_write_box.edit_text,
                    topic_name=self.title_write_box.edit_text,
                    contextual_message_id=None,
                )
            elif self.compose_box_status == "open_with_private":
                self.recipient_emails = [
                    self.model.user_id_email_dict[user_id]
                    for user_id in self.recipient_user_ids
                ]
                if self.recipient_user_ids:
                    self.model.controller.narrow_to_user(
                        recipient_emails=self.recipient_emails,
                        contextual_message_id=None,
                    )
                else:
                    self.view.controller.report_error(
                        "Cannot narrow to message without specifying recipients."
                    )
        elif is_command_key("GO_BACK", key):
            self.send_stop_typing_status()
            self._set_compose_attributes_to_defaults()
            self.view.controller.exit_editor_mode()
            self.main_view(False)
            self.view.middle_column.set_focus("body")
        elif is_command_key("MARKDOWN_HELP", key):
            self.view.controller.show_markdown_help()
            return key
        elif is_command_key("SAVE_AS_DRAFT", key):
            if self.msg_edit_state is None:
                if self.compose_box_status == "open_with_private":
                    all_valid = self._tidy_valid_recipients_and_notify_invalid_ones(
                        self.to_write_box
                    )
                    if not all_valid:
                        return key
                    self.update_recipients(self.to_write_box)
                    this_draft: Composition = PrivateComposition(
                        type="private",
                        to=self.recipient_user_ids,
                        content=self.msg_write_box.edit_text,
                    )
                elif self.compose_box_status == "open_with_stream":
                    this_draft = StreamComposition(
                        type="stream",
                        to=self.stream_write_box.edit_text,
                        content=self.msg_write_box.edit_text,
                        subject=self.title_write_box.edit_text,
                    )
                saved_draft = self.model.session_draft_message()
                if not saved_draft:
                    self.model.save_draft(this_draft)
                elif this_draft != saved_draft:
                    self.view.controller.save_draft_confirmation_popup(
                        this_draft,
                    )
        elif is_command_key("CYCLE_COMPOSE_FOCUS", key):
            if len(self.contents) == 0:
                return key
            header = self.header_write_box
            # toggle focus position
            if self.focus_position == self.FOCUS_CONTAINER_HEADER:
                if self.compose_box_status == "open_with_stream":
                    if header.focus_col == self.FOCUS_HEADER_BOX_STREAM:
                        if self.msg_edit_state is None:
                            stream_name = header[self.FOCUS_HEADER_BOX_STREAM].edit_text
                        else:
                            stream_name = header[self.FOCUS_HEADER_BOX_STREAM].text
                        if not self.model.is_valid_stream(stream_name):
                            invalid_stream_error = (
                                "Invalid stream name."
                                " Use {} or {} to autocomplete.".format(
                                    primary_key_for_command("AUTOCOMPLETE"),
                                    primary_key_for_command("AUTOCOMPLETE_REVERSE"),
                                )
                            )
                            self.view.controller.report_error([invalid_stream_error])
                            return key
                        user_ids = self.model.get_other_subscribers_in_stream(
                            stream_name=stream_name
                        )
                        self.recipient_user_ids = user_ids
                        self.stream_id = self.model.stream_id_from_name(stream_name)

                        header.focus_col = self.FOCUS_HEADER_BOX_TOPIC
                        return key
                    elif (
                        header.focus_col == self.FOCUS_HEADER_BOX_TOPIC
                        and self.msg_edit_state is not None
                    ):
                        header.focus_col = self.FOCUS_HEADER_BOX_EDIT
                        return key
                    elif header.focus_col == self.FOCUS_HEADER_BOX_EDIT:
                        if self.msg_body_edit_enabled:
                            header.focus_col = self.FOCUS_HEADER_BOX_STREAM
                            self.focus_position = self.FOCUS_CONTAINER_MESSAGE
                        else:
                            header.focus_col = self.FOCUS_HEADER_BOX_TOPIC
                        return key
                    else:
                        header.focus_col = self.FOCUS_HEADER_BOX_STREAM
                else:
                    all_valid = self._tidy_valid_recipients_and_notify_invalid_ones(
                        self.to_write_box
                    )
                    if not all_valid:
                        return key
                    # We extract recipients' user_ids and emails only once we know
                    # that all the recipients are valid, to avoid including any
                    # invalid ones.
                    self.update_recipients(self.to_write_box)

            if not self.msg_body_edit_enabled:
                return key
            if self.focus_position == self.FOCUS_CONTAINER_HEADER:
                self.focus_position = self.FOCUS_CONTAINER_MESSAGE
            else:
                self.focus_position = self.FOCUS_CONTAINER_HEADER
            if self.compose_box_status == "open_with_stream":
                if self.msg_edit_state is not None:
                    header.focus_col = self.FOCUS_HEADER_BOX_TOPIC
                else:
                    header.focus_col = self.FOCUS_HEADER_BOX_STREAM
            else:
                header.focus_col = self.FOCUS_HEADER_BOX_RECIPIENT

        key = super().keypress(size, key)
        return key


class MessageBox(urwid.Pile):
    # type of last_message is Optional[Message], but needs refactoring
    def __init__(self, message: Message, model: "Model", last_message: Any) -> None:
        self.model = model
        self.message = message
        self.header: List[Any] = []
        self.content: urwid.Text = urwid.Text("")
        self.footer: List[Any] = []
        self.stream_name = ""
        self.stream_id: Optional[int] = None
        self.topic_name = ""
        self.email = ""  # FIXME: Can we remove this?
        self.user_id: Optional[int] = None
        self.message_links: "OrderedDict[str, Tuple[str, int, bool]]" = OrderedDict()
        self.topic_links: "OrderedDict[str, Tuple[str, int, bool]]" = OrderedDict()
        self.time_mentions: List[Tuple[str, str]] = list()
        self.last_message = last_message
        # if this is the first message
        if self.last_message is None:
            self.last_message = defaultdict(dict)

        if self.message["type"] == "stream":
            # Set `topic_links` if present
            for link in self.message.get("topic_links", []):
                # Modernized response
                self.topic_links[link["url"]] = (
                    link["text"],
                    len(self.topic_links) + 1,
                    True,
                )

            self.stream_name = self.message["display_recipient"]
            self.stream_id = self.message["stream_id"]
            self.topic_name = self.message["subject"]
        elif self.message["type"] == "private":
            self.email = self.message["sender_email"]
            self.user_id = self.message["sender_id"]
        else:
            raise RuntimeError("Invalid message type")

        if self.message["type"] == "private":
            if self._is_private_message_to_self():
                recipient = self.message["display_recipient"][0]
                self.recipients_names = recipient["full_name"]
                self.recipient_emails = [self.model.user_email]
                self.recipient_ids = [self.model.user_id]
            else:
                self.recipients_names = ", ".join(
                    list(
                        recipient["full_name"]
                        for recipient in self.message["display_recipient"]
                        if recipient["email"] != self.model.user_email
                    )
                )
                self.recipient_emails = [
                    recipient["email"]
                    for recipient in self.message["display_recipient"]
                    if recipient["email"] != self.model.user_email
                ]
                self.recipient_ids = [
                    recipient["id"]
                    for recipient in self.message["display_recipient"]
                    if recipient["id"] != self.model.user_id
                ]

        super().__init__(self.main_view())

    def need_recipient_header(self) -> bool:
        # Prevent redundant information in recipient bar
        if len(self.model.narrow) == 1 and self.model.narrow[0][0] == "pm_with":
            return False
        if len(self.model.narrow) == 2 and self.model.narrow[1][0] == "topic":
            return False

        last_msg = self.last_message
        if self.message["type"] == "stream":
            return not (
                last_msg["type"] == "stream"
                and self.topic_name == last_msg["subject"]
                and self.stream_name == last_msg["display_recipient"]
            )
        elif self.message["type"] == "private":
            recipient_ids = [
                {
                    recipient["id"]
                    for recipient in message["display_recipient"]
                    if "id" in recipient
                }
                for message in (self.message, last_msg)
                if "display_recipient" in message
            ]
            return not (
                len(recipient_ids) == 2
                and recipient_ids[0] == recipient_ids[1]
                and last_msg["type"] == "private"
            )
        else:
            raise RuntimeError("Invalid message type")

    def _is_private_message_to_self(self) -> bool:
        recipient_list = self.message["display_recipient"]
        return (
            len(recipient_list) == 1
            and recipient_list[0]["email"] == self.model.user_email
        )

    def stream_header(self) -> Any:
        assert self.stream_id is not None
        color = self.model.stream_dict[self.stream_id]["color"]
        bar_color = f"s{color}"
        stream_title_markup = (
            "bar",
            [
                (bar_color, f"{self.stream_name} {STREAM_TOPIC_SEPARATOR} "),
                ("title", f" {self.topic_name}"),
            ],
        )
        stream_title = urwid.Text(stream_title_markup)
        header = urwid.Columns(
            [
                ("pack", stream_title),
                (1, urwid.Text((color, " "))),
                urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER), color),
            ]
        )
        header.markup = stream_title_markup
        return header

    def private_header(self) -> Any:
        title_markup = (
            "header",
            [("general_narrow", "You and "), ("general_narrow", self.recipients_names)],
        )
        title = urwid.Text(title_markup)
        header = urwid.Columns(
            [
                ("pack", title),
                (1, urwid.Text(("general_bar", " "))),
                urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER), "general_bar"),
            ]
        )
        header.markup = title_markup
        return header

    def top_header_bar(self, message_view: Any) -> Any:
        if self.message["type"] == "stream":
            return message_view.stream_header()
        else:
            return message_view.private_header()

    def top_search_bar(self) -> Any:
        curr_narrow = self.model.narrow
        is_search_narrow = self.model.is_search_narrow()
        if is_search_narrow:
            curr_narrow = [
                sub_narrow for sub_narrow in curr_narrow if sub_narrow[0] != "search"
            ]
        else:
            self.model.controller.view.search_box.text_box.set_edit_text("")
        if curr_narrow == []:
            text_to_fill = "All messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "private":
            text_to_fill = "All private messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "starred":
            text_to_fill = "Starred messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "mentioned":
            text_to_fill = "Mentions"
        elif self.message["type"] == "stream":
            assert self.stream_id is not None
            bar_color = self.model.stream_dict[self.stream_id]["color"]
            bar_color = f"s{bar_color}"
            if len(curr_narrow) == 2 and curr_narrow[1][0] == "topic":
                text_to_fill = (
                    "bar",  # type: ignore
                    [
                        (bar_color, self.stream_name),
                        (bar_color, ": topic narrow"),
                    ],
                )
            else:
                text_to_fill = ("bar", [(bar_color, self.stream_name)])  # type: ignore
        elif len(curr_narrow) == 1 and len(curr_narrow[0][1].split(",")) > 1:
            text_to_fill = "Group private conversation"
        else:
            text_to_fill = "Private conversation"

        if is_search_narrow:
            title_markup = (
                "header",
                [
                    ("general_narrow", text_to_fill),
                    (None, " "),
                    ("filter_results", "Search Results"),
                ],
            )
        else:
            title_markup = ("header", [("general_narrow", text_to_fill)])
        title = urwid.Text(title_markup)
        header = urwid.AttrWrap(title, "bar")
        header.text_to_fill = text_to_fill
        header.markup = title_markup
        return header

    def reactions_view(self, reactions: List[Dict[str, Any]]) -> Any:
        if not reactions:
            return ""
        try:
            MAXIMUM_USERNAMES_VISIBLE = 3
            my_user_id = self.model.user_id
            reaction_stats = defaultdict(list)
            for reaction in reactions:
                user_id = int(reaction["user"].get("id", -1))
                if user_id == -1:
                    user_id = int(reaction["user"]["user_id"])
                user_name = reaction["user"]["full_name"]
                if user_id == my_user_id:
                    user_name = "You"
                reaction_stats[reaction["emoji_name"]].append((user_id, user_name))

            for reaction, ids in reaction_stats.items():
                if (my_user_id, "You") in ids:
                    ids.remove((my_user_id, "You"))
                    ids.append((my_user_id, "You"))

            reaction_texts = [
                (
                    "reaction_mine"
                    if my_user_id in [id[0] for id in ids]
                    else "reaction",
                    f" :{reaction}: {len(ids)} "
                    if len(reactions) > MAXIMUM_USERNAMES_VISIBLE
                    else f" :{reaction}: {', '.join([id[1] for id in ids])} ",
                )
                for reaction, ids in reaction_stats.items()
            ]

            spaced_reaction_texts = [
                entry
                for pair in zip(reaction_texts, " " * len(reaction_texts))
                for entry in pair
            ]
            return urwid.Padding(
                urwid.Text(spaced_reaction_texts),
                align="left",
                width=("relative", 90),
                left=25,
                min_width=50,
            )
        except Exception:
            return ""

    # Use quotes as a workaround for OrderedDict typing issue.
    # See https://github.com/python/mypy/issues/6904.
    @staticmethod
    def footlinks_view(
        message_links: "OrderedDict[str, Tuple[str, int, bool]]",
        *,
        maximum_footlinks: int,
        padded: bool,
        wrap: str,
    ) -> Tuple[Any, int]:
        """
        Returns a Tuple that consists footlinks view (widget) and its required
        width.
        """
        # Return if footlinks are disabled by the user.
        if maximum_footlinks == 0:
            return None, 0

        footlinks = []
        counter = 0
        footlinks_width = 0
        for link, (text, index, show_footlink) in message_links.items():
            if counter == maximum_footlinks:
                break
            if not show_footlink:
                continue

            counter += 1
            styled_footlink = [
                ("msg_link_index", f"{index}:"),
                (None, " "),
                ("msg_link", link),
            ]
            footlinks_width = max(
                footlinks_width, sum([len(text) for style, text in styled_footlink])
            )
            footlinks.extend([*styled_footlink, "\n"])

        if not footlinks:
            return None, 0

        footlinks[-1] = footlinks[-1][:-1]  # Remove the last newline.

        text_widget = urwid.Text(footlinks, wrap=wrap)
        if padded:
            return (
                urwid.Padding(
                    text_widget,
                    align="left",
                    left=8,
                    width=("relative", 100),
                    min_width=10,
                    right=2,
                ),
                footlinks_width,
            )
        else:
            return text_widget, footlinks_width

    @classmethod
    def soup2markup(
        cls, soup: Any, metadata: Dict[str, Any], **state: Any
    ) -> Tuple[
        List[Any], "OrderedDict[str, Tuple[str, int, bool]]", List[Tuple[str, str]]
    ]:
        # Ensure a string is provided, in case the soup finds none
        # This could occur if eg. an image is removed or not shown
        markup: List[Union[str, Tuple[Optional[str], Any]]] = [""]
        if soup is None:  # This is not iterable, so return promptly
            return markup, metadata["message_links"], metadata["time_mentions"]
        unrendered_tags = {  # In pairs of 'tag_name': 'text'
            # TODO: Some of these could be implemented
            "br": "",  # No indicator of absence
            "hr": "RULER",
            "img": "IMAGE",
        }
        unrendered_div_classes = {  # In pairs of 'div_class': 'text'
            # TODO: Support embedded content & twitter preview?
            "message_embed": "EMBEDDED CONTENT",
            "inline-preview-twitter": "TWITTER PREVIEW",
            "message_inline_ref": "",  # Duplicate of other content
            "message_inline_image": "",  # Duplicate of other content
        }
        unrendered_template = "[{} NOT RENDERED]"
        for element in soup:
            if isinstance(element, Tag):
                # Caching element variables for use in the
                # if/elif/else chain below for improving legibility.
                tag = element.name
                tag_attrs = element.attrs
                tag_classes = tag_attrs.get("class", [])
                tag_text = element.text

            if isinstance(element, NavigableString):
                # NORMAL STRINGS
                if element == "\n" and metadata.get("bq_len", 0) > 0:
                    metadata["bq_len"] -= 1
                    continue
                markup.append(element)
            elif tag == "div" and (set(tag_classes) & set(unrendered_div_classes)):
                # UNRENDERED DIV CLASSES
                # NOTE: Though `matches` is generalized for multiple
                # matches it is very unlikely that there would be any.
                matches = set(unrendered_div_classes) & set(tag_classes)
                text = unrendered_div_classes[matches.pop()]
                if text:
                    markup.append(unrendered_template.format(text))
            elif tag == "img" and tag_classes == ["emoji"]:
                # CUSTOM EMOJIS AND ZULIP_EXTRA_EMOJI
                emoji_name = tag_attrs.get("title", [])
                markup.append(("msg_emoji", f":{emoji_name}:"))
            elif tag in unrendered_tags:
                # UNRENDERED SIMPLE TAGS
                text = unrendered_tags[tag]
                if text:
                    markup.append(unrendered_template.format(text))
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                # HEADING STYLE (h1 to h6)
                markup.append(("msg_heading", tag_text))
            elif tag in ("p", "del"):
                # PARAGRAPH, STRIKE-THROUGH
                markup.extend(cls.soup2markup(element, metadata)[0])
            elif tag == "span" and "emoji" in tag_classes:
                # EMOJI
                markup.append(("msg_emoji", tag_text))
            elif tag == "span" and ({"katex-display", "katex"} & set(tag_classes)):
                # MATH TEXT
                # FIXME: Add html -> urwid client-side logic for rendering KaTex text.
                # Avoid displaying multiple markups, and show only the source
                # as of now.
                if element.find("annotation"):
                    tag_text = element.find("annotation").text

                markup.append(("msg_math", tag_text))
            elif tag == "span" and (
                {"user-group-mention", "user-mention"} & set(tag_classes)
            ):
                # USER MENTIONS & USER-GROUP MENTIONS
                markup.append(("msg_mention", tag_text))
            elif tag == "a":
                # LINKS
                # Use rstrip to avoid anomalies and edge cases like
                # https://google.com vs https://google.com/.
                link = tag_attrs["href"].rstrip("/")
                text = element.img["src"] if element.img else tag_text
                text = text.rstrip("/")

                parsed_link = urlparse(link)
                if not parsed_link.scheme:  # => relative link
                    # Prepend org url to convert it to an absolute link
                    link = urljoin(metadata["server_url"], link)

                text = text if text else link

                show_footlink = True
                # Only use the last segment if the text is redundant.
                # NOTE: The 'without scheme' excerpt is to deal with the case
                # where a user puts a link without any scheme and the server
                # uses http as the default scheme but keeps the text as-is.
                # For instance, see how example.com/some/path becomes
                # <a href="http://example.com">example.com/some/path</a>.
                link_without_scheme, text_without_scheme = [
                    data.split("://")[1] if "://" in data else data
                    for data in [link, text]
                ]  # Split on '://' is for cases where text == link.
                if link_without_scheme == text_without_scheme:
                    last_segment = text.split("/")[-1]
                    if "." in last_segment:
                        new_text = last_segment  # Filename.
                    elif text.startswith(metadata["server_url"]):
                        # Relative URL.
                        new_text = text.split(metadata["server_url"])[-1]
                    else:
                        new_text = (
                            parsed_link.netloc
                            if parsed_link.netloc
                            else text.split("/")[0]
                        )  # Domain name.
                    if new_text != text_without_scheme:
                        text = new_text
                    else:
                        # Do not show as a footlink as the text is sufficient
                        # to represent the link.
                        show_footlink = False

                # Detect duplicate links to save screen real estate.
                if link not in metadata["message_links"]:
                    metadata["message_links"][link] = (
                        text,
                        len(metadata["message_links"]) + 1,
                        show_footlink,
                    )
                else:
                    # Append the text if its link already exist with a
                    # different text.
                    saved_text, saved_link_index, saved_footlink_status = metadata[
                        "message_links"
                    ][link]
                    if saved_text != text:
                        metadata["message_links"][link] = (
                            f"{saved_text}, {text}",
                            saved_link_index,
                            show_footlink or saved_footlink_status,
                        )

                markup.extend(
                    [
                        ("msg_link", text),
                        " ",
                        ("msg_link_index", f"[{metadata['message_links'][link][1]}]"),
                    ]
                )
            elif tag == "blockquote":
                # BLOCKQUOTE TEXT
                markup.append(("msg_quote", cls.soup2markup(element, metadata)[0]))
            elif tag == "code":
                # CODE (INLINE?)
                markup.append(("msg_code", tag_text))
            elif tag == "div" and "codehilite" in tag_classes:
                """
                CODE BLOCK
                -------------
                Structure:   # Language is optional
                    <div class="codehilite" data-code-language="python">
                      <pre>
                        <span></span>
                        <code>
                          Code HTML
                          Made of <span>'s and NavigableStrings
                        </code>
                      </pre>
                    </div>
                """
                code_soup = element.pre.code
                # NOTE: Old messages don't have the additional `code` tag.
                # Ref: https://github.com/Python-Markdown/markdown/pull/862
                if code_soup is None:
                    code_soup = element.pre

                for code_element in code_soup.contents:
                    code_text = (
                        code_element.text
                        if isinstance(code_element, Tag)
                        else code_element.string
                    )

                    if code_element.name == "span":
                        if len(code_text) == 0:
                            continue
                        css_style = code_element.attrs.get("class", ["w"])
                        markup.append((f"pygments:{css_style[0]}", code_text))
                    else:
                        markup.append(("pygments:w", code_text))
            elif tag in ("strong", "em"):
                # BOLD & ITALIC
                markup.append(("msg_bold", tag_text))
            elif tag in ("ul", "ol"):
                # LISTS (UL & OL)
                for part in element.contents:
                    if part == "\n":
                        part.replace_with("")

                if "indent_level" not in state:
                    state["indent_level"] = 1
                    state["list_start"] = True
                else:
                    state["indent_level"] += 1
                    state["list_start"] = False
                if tag == "ol":
                    start_number = int(tag_attrs.get("start", 1))
                    state["list_index"] = start_number
                    markup.extend(cls.soup2markup(element, metadata, **state)[0])
                    del state["list_index"]  # reset at end of this list
                else:
                    if "list_index" in state:
                        del state["list_index"]  # this is unordered
                    markup.extend(cls.soup2markup(element, metadata, **state)[0])
                del state["indent_level"]  # reset indents after any list
            elif tag == "li":
                # LIST ITEMS (LI)
                for part in element.contents:
                    if part == "\n":
                        part.replace_with("")
                if not state.get("list_start", False):
                    markup.append("\n")

                indent = state.get("indent_level", 1)
                if "list_index" in state:
                    markup.append(f"{'  ' * indent}{state['list_index']}. ")
                    state["list_index"] += 1
                else:
                    chars = [
                        "\N{BULLET}",
                        "\N{RING OPERATOR}",  # small hollow
                        "\N{HYPHEN}",
                    ]
                    markup.append(f"{'  ' * indent}{chars[(indent - 1) % 3]} ")
                state["list_start"] = False
                markup.extend(cls.soup2markup(element, metadata, **state)[0])
            elif tag == "table":
                markup.extend(render_table(element))
            elif tag == "time":
                # New in feature level 16, server version 3.0.
                # Render time in current user's local time zone.
                timestamp = element.get("datetime")

                # This should not happen. Regardless, we are interested in
                # debugging and reporting it to zulip/zulip if it does.
                assert timestamp is not None, "Could not find datetime attr"

                utc_time = dateutil.parser.parse(timestamp)
                local_time = utc_time.astimezone(get_localzone())
                # TODO: Address 12-hour format support with application-wide
                # support for different formats.
                time_string = local_time.strftime("%a, %b %-d %Y, %-H:%M (%Z)")
                markup.append(("msg_time", f" {TIME_MENTION_MARKER} {time_string} "))

                source_text = f"Original text was {tag_text.strip()}"
                metadata["time_mentions"].append((time_string, source_text))
            else:
                markup.extend(cls.soup2markup(element, metadata)[0])
        return markup, metadata["message_links"], metadata["time_mentions"]

    def main_view(self) -> List[Any]:

        # Recipient Header
        if self.need_recipient_header():
            if self.message["type"] == "stream":
                recipient_header = self.stream_header()
            else:
                recipient_header = self.private_header()
        else:
            recipient_header = None

        # Content Header
        message = {
            key: {
                "is_starred": "starred" in msg["flags"],
                "author": (
                    msg["sender_full_name"] if "sender_full_name" in msg else None
                ),
                "time": (
                    self.model.formatted_local_time(
                        msg["timestamp"], show_seconds=False
                    )
                    if "timestamp" in msg
                    else None
                ),
                "datetime": (
                    datetime.fromtimestamp(msg["timestamp"])
                    if "timestamp" in msg
                    else None
                ),
            }
            for key, msg in dict(this=self.message, last=self.last_message).items()
        }
        different = {  # How this message differs from the previous one
            "recipients": recipient_header is not None,
            "author": message["this"]["author"] != message["last"]["author"],
            "24h": (
                message["last"]["datetime"] is not None
                and ((message["this"]["datetime"] - message["last"]["datetime"]).days)
            ),
            "timestamp": (
                message["last"]["time"] is not None
                and message["this"]["time"] != message["last"]["time"]
            ),
            "star_status": (
                message["this"]["is_starred"] != message["last"]["is_starred"]
            ),
        }
        any_differences = any(different.values())

        if any_differences:  # Construct content_header, if needed
            TextType = Dict[str, Tuple[Optional[str], str]]
            text_keys = ("author", "star", "time", "status")
            text: TextType = {key: (None, " ") for key in text_keys}

            if any(different[key] for key in ("recipients", "author", "24h")):
                text["author"] = ("name", message["this"]["author"])

                # TODO: Refactor to use user ids for look up instead of emails.
                email = self.message.get("sender_email", "")
                user = self.model.user_dict.get(email, None)
                # TODO: Currently status of bots are shown as `inactive`.
                # Render bot users' status with bot marker as a follow-up
                status = user.get("status", "inactive") if user else "inactive"

                # The default text['status'] value is (None, ' ')
                if status in STATE_ICON:
                    text["status"] = (f"user_{status}", STATE_ICON[status])

            if message["this"]["is_starred"]:
                text["star"] = ("starred", "*")
            if any(different[key] for key in ("recipients", "author", "timestamp")):
                this_year = date.today().year
                msg_year = message["this"]["datetime"].year
                if this_year != msg_year:
                    text["time"] = ("time", f"{msg_year} - {message['this']['time']}")
                else:
                    text["time"] = ("time", message["this"]["time"])

            content_header = urwid.Columns(
                [
                    ("pack", urwid.Text(text["status"])),
                    ("weight", 10, urwid.Text(text["author"])),
                    (26, urwid.Text(text["time"], align="right")),
                    (1, urwid.Text(text["star"], align="right")),
                ],
                dividechars=1,
            )
        else:
            content_header = None

        # If the message contains '/me' emote then replace it with
        # sender's full name and show it in bold.
        if self.message["is_me_message"]:
            self.message["content"] = self.message["content"].replace(
                "/me", f"<strong>{self.message['sender_full_name']}</strong>", 1
            )

        # Transform raw message content into markup (As needed by urwid.Text)
        content, self.message_links, self.time_mentions = self.transform_content(
            self.message["content"], self.model.server_url
        )
        self.content.set_text(content)

        if self.message["id"] in self.model.index["edited_messages"]:
            edited_label_size = 7
            left_padding = 1
        else:
            edited_label_size = 0
            left_padding = 8

        wrapped_content = urwid.Padding(
            urwid.Columns(
                [
                    (edited_label_size, urwid.Text("EDITED")),
                    urwid.LineBox(
                        urwid.Columns(
                            [
                                (1, urwid.Text("")),
                                self.content,
                            ]
                        ),
                        tline="",
                        bline="",
                        rline="",
                        lline=MESSAGE_CONTENT_MARKER,
                    ),
                ]
            ),
            align="left",
            left=left_padding,
            width=("relative", 100),
            min_width=10,
            right=5,
        )

        # Reactions
        reactions = self.reactions_view(self.message["reactions"])

        # Footlinks.
        footlinks, _ = self.footlinks_view(
            self.message_links,
            maximum_footlinks=self.model.controller.maximum_footlinks,
            padded=True,
            wrap="ellipsis",
        )

        # Build parts together and return
        parts = [
            (recipient_header, recipient_header is not None),
            (content_header, any_differences),
            (wrapped_content, True),
            (footlinks, footlinks is not None),
            (reactions, reactions != ""),
        ]

        self.header = [part for part, condition in parts[:2] if condition]
        self.footer = [part for part, condition in parts[3:] if condition]

        return [part for part, condition in parts if condition]

    def update_message_author_status(self) -> bool:
        """
        Update the author status by resetting the entire message box
        if author field is present.
        """
        author_is_present = False
        author_column = 1  # Index of author field in content header

        if len(self.header) > 0:
            # -1 represents that content header is the last row of header field
            author_field = self.header[-1][author_column]
            author_is_present = author_field.text != " "

        if author_is_present:
            # Re initialize the message if update is required.
            # FIXME: Render specific element (here author field) instead?
            super().__init__(self.main_view())

        return author_is_present

    @classmethod
    def transform_content(
        cls, content: Any, server_url: str
    ) -> Tuple[
        Tuple[None, Any],
        "OrderedDict[str, Tuple[str, int, bool]]",
        List[Tuple[str, str]],
    ]:
        soup = BeautifulSoup(content, "lxml")
        body = soup.find(name="body")

        metadata = dict(
            server_url=server_url,
            message_links=OrderedDict(),
            time_mentions=list(),
        )  # type: Dict[str, Any]

        if body and body.find(name="blockquote"):
            metadata["bq_len"] = cls.indent_quoted_content(soup, QUOTED_TEXT_MARKER)

        markup, message_links, time_mentions = cls.soup2markup(body, metadata)
        return (None, markup), message_links, time_mentions

    @staticmethod
    def indent_quoted_content(soup: Any, padding_char: str) -> int:
        """
        We indent quoted text by padding them.
        The extent of indentation depends on their level of quoting.
        For example:
        [Before Padding]               [After Padding]

        <blockquote>                    <blockquote>
        <blockquote>                    <blockquote>
        <p>Foo</p>                      <p>▒ ▒ </p><p>Foo</p>
        </blockquote>       --->        </blockquote>
        <p>Boo</p>                      <p>▒ </p><p>Boo</p>
        </blockquote>                   </blockquote>
        """
        pad_count = 1
        blockquote_list = soup.find_all("blockquote")
        bq_len = len(blockquote_list)
        for tag in blockquote_list:
            child_list = tag.findChildren(recursive=False)
            child_block = tag.find_all("blockquote")
            actual_padding = f"{padding_char} " * pad_count
            if len(child_list) == 1:
                pad_count -= 1
                child_iterator = child_list
            else:
                if len(child_block) == 0:
                    child_iterator = child_list
                else:
                    # If there is some text at the begining of a
                    # quote, we pad it seperately.
                    if child_list[0].name == "p":
                        new_tag = soup.new_tag("p")
                        new_tag.string = f"\n{actual_padding}"
                        child_list[0].insert_before(new_tag)
                    child_iterator = child_list[1:]
            for child in child_iterator:
                new_tag = soup.new_tag("p")
                new_tag.string = actual_padding
                # If the quoted message is multi-line message
                # we deconstruct it and pad it at break-points (<br/>)
                for br in child.findAll("br"):
                    next_s = br.nextSibling
                    text = str(next_s.string).strip()
                    if text:
                        insert_tag = soup.new_tag("p")
                        insert_tag.string = f"\n{padding_char} {text}"
                        next_s.replace_with(insert_tag)
                child.insert_before(new_tag)
            pad_count += 1
        return bq_len

    def selectable(self) -> bool:
        # Returning True, indicates that this widget
        # is designed to take focus.
        return True

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press":
            if button == 1:
                if self.model.controller.is_in_editor_mode():
                    return True
                self.keypress(size, primary_key_for_command("ENTER"))
                return True

        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("REPLY_MESSAGE", key):
            if self.message["type"] == "private":
                self.model.controller.view.write_box.private_box_view(
                    recipient_user_ids=self.recipient_ids,
                )
            elif self.message["type"] == "stream":
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message["display_recipient"],
                    title=self.message["subject"],
                    stream_id=self.stream_id,
                )
        elif is_command_key("STREAM_MESSAGE", key):
            if len(self.model.narrow) != 0 and self.model.narrow[0][0] == "stream":
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message["display_recipient"],
                    stream_id=self.stream_id,
                )
            else:
                self.model.controller.view.write_box.stream_box_view(0)
        elif is_command_key("STREAM_NARROW", key):
            if self.message["type"] == "private":
                self.model.controller.narrow_to_user(
                    recipient_emails=self.recipient_emails,
                    contextual_message_id=self.message["id"],
                )
            elif self.message["type"] == "stream":
                self.model.controller.narrow_to_stream(
                    stream_name=self.stream_name,
                    contextual_message_id=self.message["id"],
                )
        elif is_command_key("TOGGLE_NARROW", key):
            self.model.unset_search_narrow()
            if self.message["type"] == "private":
                if len(self.model.narrow) == 1 and self.model.narrow[0][0] == "pm_with":
                    self.model.controller.narrow_to_all_pm(
                        contextual_message_id=self.message["id"],
                    )
                else:
                    self.model.controller.narrow_to_user(
                        recipient_emails=self.recipient_emails,
                        contextual_message_id=self.message["id"],
                    )
            elif self.message["type"] == "stream":
                if len(self.model.narrow) > 1:  # in a topic
                    self.model.controller.narrow_to_stream(
                        stream_name=self.stream_name,
                        contextual_message_id=self.message["id"],
                    )
                else:
                    self.model.controller.narrow_to_topic(
                        stream_name=self.stream_name,
                        topic_name=self.topic_name,
                        contextual_message_id=self.message["id"],
                    )
        elif is_command_key("TOPIC_NARROW", key):
            if self.message["type"] == "private":
                self.model.controller.narrow_to_user(
                    recipient_emails=self.recipient_emails,
                    contextual_message_id=self.message["id"],
                )
            elif self.message["type"] == "stream":
                self.model.controller.narrow_to_topic(
                    stream_name=self.stream_name,
                    topic_name=self.topic_name,
                    contextual_message_id=self.message["id"],
                )
        elif is_command_key("ALL_MESSAGES", key):
            self.model.controller.narrow_to_all_messages(
                contextual_message_id=self.message["id"]
            )
        elif is_command_key("REPLY_AUTHOR", key):
            # All subscribers from recipient_ids are not needed here.
            self.model.controller.view.write_box.private_box_view(
                recipient_user_ids=[self.message["sender_id"]],
            )
        elif is_command_key("MENTION_REPLY", key):
            self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))
            mention = f"@**{self.message['sender_full_name']}** "
            self.model.controller.view.write_box.msg_write_box.set_edit_text(mention)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(
                len(mention)
            )
            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("QUOTE_REPLY", key):
            self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))

            # To correctly quote a message that contains quote/code-blocks,
            # we need to fence quoted message containing ``` with ````,
            # ```` with ````` and so on.
            response = self.model.fetch_raw_message_content(self.message["id"])
            message_raw_content = response if response is not None else ""
            fence = get_unused_fence(message_raw_content)

            absolute_url = near_message_url(self.model.server_url[:-1], self.message)

            # Compose box should look something like this:
            #   @_**Zeeshan|514** [said](link to message):
            #   ```quote
            #   message_content
            #   ```
            quote = "@_**{0}|{1}** [said]({2}):\n{3}quote\n{4}\n{3}\n".format(
                self.message["sender_full_name"],
                self.message["sender_id"],
                absolute_url,
                fence,
                message_raw_content,
            )

            self.model.controller.view.write_box.msg_write_box.set_edit_text(quote)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(len(quote))
            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("EDIT_MESSAGE", key):
            # User can't edit messages of others that already have a subject
            # For private messages, subject = "" (empty string)
            # This also handles the realm_message_content_edit_limit_seconds == 0 case
            if (
                self.message["sender_id"] != self.model.user_id
                and self.message["subject"] != "(no topic)"
            ):
                if self.message["type"] == "stream":
                    self.model.controller.report_error(
                        [
                            " You can't edit messages sent by other users that"
                            " already have a topic."
                        ]
                    )
                else:
                    self.model.controller.report_error(
                        [" You can't edit private messages sent by other users."]
                    )
                return key
            # Check if editing is allowed in the realm
            elif not self.model.initial_data["realm_allow_message_editing"]:
                self.model.controller.report_error(
                    [" Editing sent message is disabled."]
                )
                return key
            # Check if message is still editable, i.e. within
            # the time limit. A limit of 0 signifies no limit
            # on message body editing.
            msg_body_edit_enabled = True
            if self.model.initial_data["realm_message_content_edit_limit_seconds"] > 0:
                if self.message["sender_id"] == self.model.user_id:
                    time_since_msg_sent = time() - self.message["timestamp"]
                    edit_time_limit = self.model.initial_data[
                        "realm_message_content_edit_limit_seconds"
                    ]
                    # Don't allow editing message body if time-limit exceeded.
                    if time_since_msg_sent >= edit_time_limit:
                        if self.message["type"] == "private":
                            self.model.controller.report_error(
                                [
                                    " Time Limit for editing the message has been exceeded."
                                ]
                            )
                            return key
                        elif self.message["type"] == "stream":
                            self.model.controller.report_warning(
                                [
                                    " Only topic editing allowed."
                                    " Time Limit for editing the message body"
                                    " has been exceeded."
                                ]
                            )
                            msg_body_edit_enabled = False
                elif self.message["type"] == "stream":
                    # Allow editing topic if the message has "(no topic)" subject
                    if self.message["subject"] == "(no topic)":
                        self.model.controller.report_warning(
                            [
                                " Only topic editing is allowed."
                                " This is someone else's message but with (no topic)."
                            ]
                        )
                        msg_body_edit_enabled = False
                    else:
                        self.model.controller.report_error(
                            [
                                " You can't edit messages sent by other users that"
                                " already have a topic."
                            ]
                        )
                        return key
                else:
                    # The remaining case is of a private message not belonging to user.
                    # Which should be already handled by the topmost if block
                    raise RuntimeError(
                        "Reached unexpected block. This should be handled at the top."
                    )

            if self.message["type"] == "private":
                self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))
            elif self.message["type"] == "stream":
                self.model.controller.view.write_box.stream_box_edit_view(
                    stream_id=self.stream_id,
                    caption=self.message["display_recipient"],
                    title=self.message["subject"],
                )
            msg_id = self.message["id"]
            response = self.model.fetch_raw_message_content(msg_id)
            msg = response if response is not None else ""
            write_box = self.model.controller.view.write_box
            write_box.msg_edit_state = _MessageEditState(
                message_id=msg_id, old_topic=self.message["subject"]
            )
            write_box.msg_write_box.set_edit_text(msg)
            write_box.msg_write_box.set_edit_pos(len(msg))
            write_box.msg_body_edit_enabled = msg_body_edit_enabled
            # Set focus to topic box if message body editing is disabled.
            if not msg_body_edit_enabled:
                write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
                write_box.header_write_box.focus_col = write_box.FOCUS_HEADER_BOX_TOPIC

            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("MSG_INFO", key):
            self.model.controller.show_msg_info(
                self.message, self.topic_links, self.message_links, self.time_mentions
            )
        elif is_command_key("ADD_REACTION", key):
            self.model.controller.show_emoji_picker(self.message)
        return key


class SearchBox(urwid.Pile):
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        super().__init__(self.main_view())

    def main_view(self) -> Any:
        search_text = f"Search [{', '.join(keys_for_command('SEARCH_MESSAGES'))}]: "
        self.text_box = ReadlineEdit(f"{search_text} ")
        # Add some text so that when packing,
        # urwid doesn't hide the widget.
        self.conversation_focus = urwid.Text(" ")
        self.search_bar = urwid.Columns(
            [
                ("pack", self.conversation_focus),
                ("pack", urwid.Text("  ")),
                self.text_box,
            ]
        )
        self.msg_narrow = urwid.Text("DONT HIDE")
        self.recipient_bar = urwid.LineBox(
            self.msg_narrow,
            title="Current message recipients",
            tline="─",
            lline="",
            trcorner="─",
            tlcorner="─",
            blcorner="─",
            rline="",
            bline="─",
            brcorner="─",
        )
        return [self.search_bar, self.recipient_bar]

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if (
            is_command_key("ENTER", key) and self.text_box.edit_text == ""
        ) or is_command_key("GO_BACK", key):
            self.text_box.set_edit_text("")
            self.controller.exit_editor_mode()
            self.controller.view.middle_column.set_focus("body")
            return key

        elif is_command_key("ENTER", key):
            self.controller.exit_editor_mode()
            self.controller.search_messages(self.text_box.edit_text)
            self.controller.view.middle_column.set_focus("body")
            return key

        key = super().keypress(size, key)
        return key


class PanelSearchBox(urwid.Edit):
    """
    Search Box to search panel views in real-time.
    """

    def __init__(
        self, panel_view: Any, search_command: str, update_function: Callable[..., None]
    ) -> None:
        self.panel_view = panel_view
        self.search_command = search_command
        self.search_text = f" Search [{', '.join(keys_for_command(search_command))}]: "
        self.search_error = urwid.AttrMap(
            urwid.Text([" ", INVALID_MARKER, " No Results"]), "search_error"
        )
        urwid.connect_signal(self, "change", update_function)
        super().__init__(caption=self.search_text, edit_text="")

    def reset_search_text(self) -> None:
        self.set_caption(self.search_text)
        self.set_edit_text("")

    def valid_char(self, ch: str) -> bool:
        # This method 'strips' leading space *before* entering it in the box
        if self.edit_text:
            # Use regular validation if already have text
            return super().valid_char(ch)
        elif len(ch) != 1:
            # urwid expands some unicode to strings to be useful
            # (so we need to work around eg 'backspace')
            return False
        else:
            # Skip unicode 'Control characters' and 'space Zeperators'
            # This includes various invalid characters and complex spaces
            return unicodedata.category(ch) not in ("Cc", "Zs")

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if (
            is_command_key("ENTER", key) and self.get_edit_text() == ""
        ) or is_command_key("GO_BACK", key):
            self.panel_view.view.controller.exit_editor_mode()
            self.reset_search_text()
            self.panel_view.set_focus("body")
            # Don't call 'Esc' when inside a popup search-box.
            if not self.panel_view.view.controller.is_any_popup_open():
                self.panel_view.keypress(size, primary_key_for_command("GO_BACK"))
        elif is_command_key("ENTER", key) and not self.panel_view.empty_search:
            self.panel_view.view.controller.exit_editor_mode()
            self.set_caption([("filter_results", " Search Results "), " "])
            self.panel_view.set_focus("body")
            if hasattr(self.panel_view, "log"):
                self.panel_view.body.set_focus(0)
        return super().keypress(size, key)
