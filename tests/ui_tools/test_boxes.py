import datetime
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional
from unittest import mock

import pytest
import urwid
from pytest import param as case
from pytest_mock import MockerFixture
from urwid import Widget
from urwid_readline import ReadlineEdit

from zulipterminal.config.keys import keys_for_command, primary_key_for_command
from zulipterminal.config.symbols import (
    INVALID_MARKER,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
    STREAM_MARKER_WEB_PUBLIC,
)
from zulipterminal.config.ui_mappings import StreamAccessType
from zulipterminal.helper import Index
from zulipterminal.ui_tools.boxes import PanelSearchBox, WriteBox, _MessageEditState
from zulipterminal.urwid_types import urwid_Size


MODULE = "zulipterminal.ui_tools.boxes"
WRITEBOX = MODULE + ".WriteBox"


class TestWriteBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(
        self, mocker: MockerFixture, initial_index: Index
    ) -> None:
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()

    @pytest.fixture()
    def write_box(
        self,
        mocker: MockerFixture,
        users_fixture: List[Dict[str, Any]],
        user_groups_fixture: List[Dict[str, Any]],
        streams_fixture: List[Dict[str, Any]],
        unicode_emojis: "OrderedDict[str, Dict[str, Any]]",
        user_dict: Dict[str, Dict[str, Any]],
    ) -> WriteBox:
        self.view.model.active_emoji_data = unicode_emojis
        self.view.model.all_emoji_names = list(unicode_emojis.keys())
        write_box = WriteBox(self.view)
        write_box.view.users = users_fixture
        write_box.model.user_dict = user_dict
        write_box.model.max_stream_name_length = 60
        write_box.model.max_topic_length = 60
        write_box.model.max_message_length = 10000
        write_box.model.user_group_names = [
            groups["name"] for groups in user_groups_fixture
        ]

        write_box.view.pinned_streams = []
        write_box.view.unpinned_streams = sorted(
            [{"name": stream["name"]} for stream in streams_fixture],
            key=lambda stream: stream["name"].lower(),
        )

        return write_box

    def test_init(self, write_box: WriteBox) -> None:
        assert write_box.model == self.view.model
        assert write_box.view == self.view
        assert write_box.compose_box_status == "closed"
        assert write_box.msg_edit_state is None
        assert write_box.msg_body_edit_enabled is True
        assert write_box.stream_id is None
        assert write_box.recipient_user_ids == []
        assert write_box.typing_recipient_user_ids == []
        assert write_box.to_write_box is None
        assert isinstance(write_box.send_next_typing_update, datetime.datetime)
        assert isinstance(write_box.last_key_update, datetime.datetime)
        assert write_box.idle_status_tracking is False
        assert write_box.sent_start_typing_status is False

    def test_not_calling_typing_method_without_recipients(
        self, mocker: MockerFixture, write_box: WriteBox
    ) -> None:
        write_box.model.send_typing_status_by_user_ids = mocker.Mock()
        write_box.private_box_view(recipient_user_ids=[])
        # Set idle_status_tracking to True to avoid setting off the
        # idleness tracker function.
        write_box.idle_status_tracking = True

        # Changing the edit_text triggers on_type_send_status.
        write_box.msg_write_box.edit_text = "random text"

        assert not write_box.model.send_typing_status_by_user_ids.called

    @pytest.mark.parametrize(
        "text, state, is_valid_stream, required_typeahead",
        [
            ("#**Stream 1>T", 0, True, "#**Stream 1>Topic 1**"),
            ("#**Stream 1>T", 1, True, "#**Stream 1>This is a topic**"),
            ("#**Stream 1>T", 2, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>T", 3, True, "#**Stream 1>He-llo there!**"),
            ("#**Stream 1>T", 4, True, "#**Stream 1>Hello t/here!**"),
            ("#**Stream 1>T", 5, True, None),
            ("#**Stream 1>T", -1, True, "#**Stream 1>Hello t/here!**"),
            ("#**Stream 1>T", -2, True, "#**Stream 1>He-llo there!**"),
            ("#**Stream 1>T", -3, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>T", -4, True, "#**Stream 1>This is a topic**"),
            ("#**Stream 1>T", -5, True, "#**Stream 1>Topic 1**"),
            ("#**Stream 1>T", -6, True, None),
            ("#**Stream 1>To", 0, True, "#**Stream 1>Topic 1**"),
            ("#**Stream 1>H", 0, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>Hello ", 0, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>", 0, True, "#**Stream 1>Topic 1**"),
            ("#**Stream 1>", 1, True, "#**Stream 1>This is a topic**"),
            ("#**Stream 1>", 2, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>", 3, True, "#**Stream 1>He-llo there!**"),
            ("#**Stream 1>", 4, True, "#**Stream 1>Hello t/here!**"),
            ("#**Stream 1>", 5, True, "#**Stream 1>Hello from out-er_space!**"),
            ("#**Stream 1>", 6, True, None),
            ("#**Stream 1>", -1, True, "#**Stream 1>Hello from out-er_space!**"),
            ("#**Stream 1>", -2, True, "#**Stream 1>Hello t/here!**"),
            ("#**Stream 1>", -3, True, "#**Stream 1>He-llo there!**"),
            ("#**Stream 1>", -4, True, "#**Stream 1>Hello there!**"),
            ("#**Stream 1>", -5, True, "#**Stream 1>This is a topic**"),
            ("#**Stream 1>", -6, True, "#**Stream 1>Topic 1**"),
            ("#**Stream 1>", -7, True, None),
            # Fenced prefix
            ("#**Stream 1**>T", 0, True, "#**Stream 1>Topic 1**"),
            # Unfenced prefix
            ("#Stream 1>T", 0, True, "#**Stream 1>Topic 1**"),
            ("#Stream 1>T", 1, True, "#**Stream 1>This is a topic**"),
            ("#Stream 1>T", 2, True, "#**Stream 1>Hello there!**"),
            # Invalid stream
            ("#**invalid stream>", 0, False, None),
            ("#**invalid stream**>", 0, False, None),
            ("#invalid stream>", 0, False, None),
            # Invalid prefix format
            ("#**Stream 1*>", 0, True, None),
            ("#*Stream 1>", 0, True, None),
            # Complex autocomplete prefixes.
            ("(#**Stream 1>", 0, True, "(#**Stream 1>Topic 1**"),
            ("&#**Stream 1>", 0, True, "&#**Stream 1>Topic 1**"),
            ("@#**Stream 1>", 0, True, "@#**Stream 1>Topic 1**"),
            ("@_#**Stream 1>", 0, True, "@_#**Stream 1>Topic 1**"),
            (":#**Stream 1>", 0, True, ":#**Stream 1>Topic 1**"),
            ("(#**Stream 1**>", 0, True, "(#**Stream 1>Topic 1**"),
        ],
    )
    def test_generic_autocomplete_stream_and_topic(
        self,
        write_box: WriteBox,
        text: str,
        state: Optional[int],
        is_valid_stream: bool,
        required_typeahead: Optional[str],
        topics: List[str],
        stream_dict: Dict[int, Dict[str, Any]],
    ) -> None:
        write_box.model.topics_in_stream.return_value = topics
        write_box.model.is_valid_stream.return_value = is_valid_stream
        write_box.model.stream_dict = stream_dict
        write_box.model.muted_streams = set()
        typeahead_string = write_box.generic_autocomplete(text, state)

        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "user_ids, expect_method_called, typing_recipient_user_ids",
        [
            ([1001], False, []),
            ([1001, 11], True, [11]),
        ],
        ids=["pm_only_with_oneself", "group_pm"],
    )
    def test_not_calling_typing_method_to_oneself(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        expect_method_called: bool,
        logged_on_user: Dict[str, Any],
        user_ids: List[int],
        typing_recipient_user_ids: List[int],
        user_id_email_dict: Dict[int, str],
    ) -> None:
        write_box.model.send_typing_status_by_user_ids = mocker.Mock()
        write_box.model.user_id_email_dict = user_id_email_dict
        write_box.model.user_id = logged_on_user["user_id"]
        write_box.private_box_view(recipient_user_ids=user_ids)
        # Set idle_status_tracking to True to avoid setting off the
        # idleness tracker function.
        write_box.idle_status_tracking = True

        # Triggers possible sending of typing status only once
        write_box.msg_write_box.edit_text = "random text"

        assert (
            write_box.model.send_typing_status_by_user_ids.called
            == expect_method_called
        )

        if expect_method_called:
            write_box.model.send_typing_status_by_user_ids.assert_called_with(
                typing_recipient_user_ids, status="start"
            )
            write_box.send_stop_typing_status()
            write_box.model.send_typing_status_by_user_ids.assert_called_with(
                typing_recipient_user_ids, status="stop"
            )

    @pytest.mark.parametrize("key", keys_for_command("SEND_MESSAGE"))
    def test_not_calling_send_private_message_without_recipients(
        self,
        key: str,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        write_box.model.send_private_message = mocker.Mock()
        write_box.private_box_view(recipient_user_ids=[])
        write_box.msg_write_box.edit_text = "random text"

        size = widget_size(write_box)
        write_box.keypress(size, key)

        assert not write_box.model.send_private_message.called

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test__compose_attributes_reset_for_private_compose(
        self,
        key: str,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
        user_id_email_dict: Dict[int, str],
    ) -> None:
        mocker.patch("urwid.connect_signal")
        write_box.model.user_id_email_dict = user_id_email_dict
        write_box.private_box_view(recipient_user_ids=[11])
        write_box.msg_write_box.edit_text = "random text"

        size = widget_size(write_box)
        write_box.keypress(size, key)

        assert write_box.to_write_box is None
        assert write_box.msg_write_box.edit_text == ""
        assert write_box.compose_box_status == "closed"

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test__compose_attributes_reset_for_stream_compose(
        self,
        key: str,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        mocker.patch(WRITEBOX + "._set_stream_write_box_style")
        write_box.stream_box_view(stream_id=1)
        write_box.msg_write_box.edit_text = "random text"

        size = widget_size(write_box)
        write_box.keypress(size, key)

        assert write_box.stream_id is None
        assert write_box.msg_write_box.edit_text == ""
        assert write_box.compose_box_status == "closed"

    @pytest.mark.parametrize(
        ["raw_recipients", "tidied_recipients"],
        [
            ("Human 1 person1@example.com", "Human 1 <person1@example.com>"),
            (
                "Human 2 person2@example.com random text",
                "Human 2 <person2@example.com>",
            ),
            (
                "Human Myself FOOBOO@gmail.com random, Human 1 <person1@example.com>",
                "Human Myself <FOOBOO@gmail.com>, Human 1 <person1@example.com>",
            ),
            (
                "Human Myself <FOOBOO@gmail.com>, Human 1 person1@example.com random",
                "Human Myself <FOOBOO@gmail.com>, Human 1 <person1@example.com>",
            ),
            (
                "Human Myself FOOBOO@gmail.com random,"
                "Human 1 person1@example.com random",
                "Human Myself <FOOBOO@gmail.com>, Human 1 <person1@example.com>",
            ),
            (
                "Human Myself FOOBOO@gmail.com random, Human 1 person1@example.com "
                "random, Human 2 person2@example.com random",
                "Human Myself <FOOBOO@gmail.com>, Human 1 <person1@example.com>, "
                "Human 2 <person2@example.com>",
            ),
            (
                "Human Myself FOOBOO@gmail.com, Human 1 person1@example.com random, "
                "Human 2 person2@example.com",
                "Human Myself <FOOBOO@gmail.com>, Human 1 <person1@example.com>, "
                "Human 2 <person2@example.com>",
            ),
        ],
        ids=[
            "untidy_with_improper_formatting",
            "untidy_with_extra_text",
            "untidy_first_recipient_out_of_two",
            "untidy_second_recipient_out_of_two",
            "two_untidy_recipients",
            "three_untidy_recipients",
            "untidy_middle_recipient_out_of_three",
        ],
    )
    @pytest.mark.parametrize(
        "key",
        keys_for_command("SEND_MESSAGE")
        + keys_for_command("SAVE_AS_DRAFT")
        + keys_for_command("CYCLE_COMPOSE_FOCUS"),
    )
    def test_tidying_recipients_on_keypresses(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
        key: str,
        raw_recipients: str,
        tidied_recipients: str,
    ) -> None:
        write_box.model.is_valid_private_recipient = mocker.Mock(return_value=True)
        write_box.private_box_view()
        assert write_box.to_write_box is not None
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = write_box.FOCUS_HEADER_BOX_RECIPIENT

        write_box.to_write_box.set_edit_text(raw_recipients)
        write_box.to_write_box.set_edit_pos(len(raw_recipients))

        size = widget_size(write_box)
        write_box.keypress(size, key)

        assert write_box.to_write_box.edit_text == tidied_recipients

    @pytest.mark.parametrize(
        ["raw_recipients", "invalid_recipients"],
        [
            ("Human 1 <person2@example.com>", "Human 1 <person2@example.com>"),
            ("person1@example.com", "person1@example.com"),
            ("Human 1", "Human 1"),
        ],
        ids=["name_email_mismatch", "no_name_specified", "no_email_specified"],
    )
    @pytest.mark.parametrize(
        "key",
        keys_for_command("SEND_MESSAGE")
        + keys_for_command("SAVE_AS_DRAFT")
        + keys_for_command("CYCLE_COMPOSE_FOCUS"),
    )
    def test_footer_notification_on_invalid_recipients(
        self,
        write_box: WriteBox,
        key: str,
        mocker: MockerFixture,
        widget_size: Callable[[Widget], urwid_Size],
        raw_recipients: str,
        invalid_recipients: str,
    ) -> None:
        write_box.model.is_valid_private_recipient = mocker.Mock(return_value=False)
        write_box.private_box_view()
        assert write_box.to_write_box is not None
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = write_box.FOCUS_HEADER_BOX_RECIPIENT

        write_box.to_write_box.edit_text = raw_recipients
        write_box.to_write_box.set_edit_pos(len(raw_recipients))
        expected_lines = [
            "Invalid recipient(s) - " + invalid_recipients,
            " - Use ",
            ("footer_contrast", primary_key_for_command("AUTOCOMPLETE")),
            " or ",
            ("footer_contrast", primary_key_for_command("AUTOCOMPLETE_REVERSE")),
            " to autocomplete.",
        ]

        size = widget_size(write_box)
        write_box.keypress(size, key)

        self.view.controller.report_error.assert_called_once_with(expected_lines)
        # If there are invalid recipients, we expect the focus
        # to remain in the to_write_box.
        assert write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER
        assert (
            write_box.header_write_box.focus_col == write_box.FOCUS_HEADER_BOX_RECIPIENT
        )

    @pytest.mark.parametrize(
        "header, expected_recipient_emails, expected_recipient_user_ids",
        [
            case(
                "Human 1 <person1@example.com>",
                ["person1@example.com"],
                [11],
                id="single_recipient",
            ),
            case(
                "Human 1 <person1@example.com>, Human 2 <person2@example.com>",
                ["person1@example.com", "person2@example.com"],
                [11, 12],
                id="multiple_recipients",
            ),
        ],
    )
    def test_update_recipients(
        self,
        write_box: WriteBox,
        header: str,
        expected_recipient_emails: List[str],
        expected_recipient_user_ids: List[int],
    ) -> None:
        write_box.private_box_view()
        assert write_box.to_write_box is not None
        write_box.to_write_box.edit_text = header

        write_box.update_recipients(write_box.to_write_box)

        assert write_box.recipient_emails == expected_recipient_emails
        assert write_box.recipient_user_ids == expected_recipient_user_ids

    @pytest.mark.parametrize(
        "text, state",
        [
            ("Plain Text", 0),
            ("Plain Text", 1),
        ],
    )
    def test_generic_autocomplete_no_prefix(
        self, write_box: WriteBox, text: str, state: Optional[int]
    ) -> None:
        return_val = write_box.generic_autocomplete(text, state)
        assert return_val == text
        write_box.view.set_typeahead_footer.assert_not_called()

    @pytest.mark.parametrize(
        "text, state, footer_text",
        [
            # no-text mentions
            (
                "@",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                    "Group 1",
                    "Group 2",
                    "Group 3",
                    "Group 4",
                ],
            ),
            ("@*", 0, ["Group 1", "Group 2", "Group 3", "Group 4"]),
            (
                "@**",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            # mentions
            (
                "@Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@**Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@_Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            ("@_*Human", None, []),  # NOTE: Optional single star fails
            (
                "@_**Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@Human",
                None,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            ("@NoMatch", None, []),
            # streams
            (
                "#Stream",
                0,
                [
                    "Stream 1",
                    "Stream 2",
                    "Secret stream",
                    "Some general stream",
                    "Web public stream",
                ],
            ),
            ("#*Stream", None, []),  # NOTE: Optional single star fails
            (
                "#**Stream",
                0,
                [
                    "Stream 1",
                    "Stream 2",
                    "Secret stream",
                    "Some general stream",
                    "Web public stream",
                ],
            ),  # Optional 2-stars
            (
                "#Stream",
                None,
                [
                    "Stream 1",
                    "Stream 2",
                    "Secret stream",
                    "Some general stream",
                    "Web public stream",
                ],
            ),
            ("#NoMatch", None, []),
            # emojis
            (":smi", 0, ["smile", "smiley", "smirk"]),
            (":smi", None, ["smile", "smiley", "smirk"]),
            (":NoMatch", None, []),
        ],
    )
    def test_generic_autocomplete_set_footer(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        state: Optional[int],
        footer_text: List[Any],
        text: str,
        stream_dict: Dict[int, Dict[str, Any]],
    ) -> None:
        write_box.view.set_typeahead_footer = mocker.patch(
            "zulipterminal.ui.View.set_typeahead_footer"
        )
        write_box.model.stream_dict = stream_dict
        write_box.model.muted_streams = set()
        write_box.generic_autocomplete(text, state)

        write_box.view.set_typeahead_footer.assert_called_once_with(
            footer_text, state, False
        )

    @pytest.mark.parametrize(
        "text, state, required_typeahead",
        [
            ("@Human", 0, "@**Human Myself**"),
            ("@Human", 1, "@**Human 1**"),
            ("@Human", 2, "@**Human 2**"),
            ("@Human", 3, "@**Human Duplicate|13**"),
            ("@Human", 4, "@**Human Duplicate|14**"),
            ("@Human", -1, "@**Human Duplicate|14**"),
            ("@Human", -2, "@**Human Duplicate|13**"),
            ("@Human", -3, "@**Human 2**"),
            ("@Human", -4, "@**Human 1**"),
            ("@Human", -5, "@**Human Myself**"),
            ("@Human", -6, None),
            ("@_Human", 0, "@_**Human Myself**"),
            ("@_Human", 1, "@_**Human 1**"),
            ("@_Human", 2, "@_**Human 2**"),
            ("@_Human", 3, "@_**Human Duplicate|13**"),
            ("@_Human", 4, "@_**Human Duplicate|14**"),
            ("@H", 1, "@**Human 1**"),
            ("@Hu", 1, "@**Human 1**"),
            ("@Hum", 1, "@**Human 1**"),
            ("@Huma", 1, "@**Human 1**"),
            ("@Human", 1, "@**Human 1**"),
            ("@Human 1", 0, "@**Human 1**"),  # Space-containing text
            ("@_H", 1, "@_**Human 1**"),
            ("@_Hu", 1, "@_**Human 1**"),
            ("@_Hum", 1, "@_**Human 1**"),
            ("@_Huma", 1, "@_**Human 1**"),
            ("@_Human", 1, "@_**Human 1**"),
            ("@_Human 1", 0, "@_**Human 1**"),  # Space-containing text
            ("@Group", 0, "@*Group 1*"),
            ("@Group", 1, "@*Group 2*"),
            ("@G", 0, "@*Group 1*"),
            ("@Gr", 0, "@*Group 1*"),
            ("@Gro", 0, "@*Group 1*"),
            ("@Grou", 0, "@*Group 1*"),
            ("@G", 1, "@*Group 2*"),
            ("@Gr", 1, "@*Group 2*"),
            ("@Gro", 1, "@*Group 2*"),
            ("@Grou", 1, "@*Group 2*"),
            # Expected sequence of autocompletes from '@'
            ("@", 0, "@**Human Myself**"),
            ("@", 1, "@**Human 1**"),
            ("@", 2, "@**Human 2**"),
            ("@", 3, "@**Human Duplicate|13**"),
            ("@", 4, "@**Human Duplicate|14**"),
            ("@", 5, "@*Group 1*"),
            ("@", 6, "@*Group 2*"),
            ("@", 7, "@*Group 3*"),
            ("@", 8, "@*Group 4*"),
            ("@", 9, None),  # Reached last match
            ("@", 10, None),  # Beyond end
            # Expected sequence of autocompletes from '@**' (no groups)
            ("@**", 0, "@**Human Myself**"),
            ("@**", 1, "@**Human 1**"),
            ("@**", 2, "@**Human 2**"),
            ("@", 3, "@**Human Duplicate|13**"),
            ("@", 4, "@**Human Duplicate|14**"),
            ("@**", 5, None),  # Reached last match
            ("@**", 6, None),  # Beyond end
            ("@**Human 1", 0, "@**Human 1**"),  # Space-containing text
            # Expected sequence of autocompletes from '@*' (only groups)
            ("@*", 0, "@*Group 1*"),
            ("@*", 1, "@*Group 2*"),
            ("@*", 2, "@*Group 3*"),
            ("@*", 3, "@*Group 4*"),
            ("@*", 4, None),  # Reached last match
            ("@*", 5, None),  # Beyond end
            # Expected sequence of autocompletes from '@_'
            ("@_", 0, "@_**Human Myself**"),  # NOTE: No silent group mention
            ("@_", 1, "@_**Human 1**"),
            ("@_", 2, "@_**Human 2**"),
            ("@_", 3, "@_**Human Duplicate|13**"),
            ("@_", 4, "@_**Human Duplicate|14**"),
            ("@_", 5, None),  # Reached last match
            ("@_", 6, None),  # Beyond end
            ("@_", -1, "@_**Human Duplicate|14**"),
            ("@_Human 1", 0, "@_**Human 1**"),  # Space-containing text
            ("@_**Human 1", 0, "@_**Human 1**"),  # Space-containing text
            # Complex autocomplete prefixes.
            ("(@H", 0, "(@**Human Myself**"),
            ("(@H", 1, "(@**Human 1**"),
            ("-@G", 0, "-@*Group 1*"),
            ("-@G", 1, "-@*Group 2*"),
            ("_@H", 0, "_@**Human Myself**"),
            ("_@G", 0, "_@*Group 1*"),
            ("@@H", 0, "@@**Human Myself**"),
            (":@H", 0, ":@**Human Myself**"),
            ("#@H", 0, "#@**Human Myself**"),
            ("@_@H", 0, "@_@**Human Myself**"),
            (">@_H", 0, ">@_**Human Myself**"),
            (">@_H", 1, ">@_**Human 1**"),
            ("@_@_H", 0, "@_@_**Human Myself**"),
            ("@@_H", 0, "@@_**Human Myself**"),
            (":@_H", 0, ":@_**Human Myself**"),
            ("#@_H", 0, "#@_**Human Myself**"),
            ("@@_H", 0, "@@_**Human Myself**"),
            ("@@_*H", 0, None),  # Optional single star fails
            ("@@_**H", 0, "@@_**Human Myself**"),  # Optional stars
        ],
    )
    def test_generic_autocomplete_mentions(
        self,
        write_box: WriteBox,
        text: str,
        required_typeahead: Optional[str],
        state: Optional[int],
    ) -> None:
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, state, required_typeahead, recipients",
        [
            ("@", 0, "@**Human 2**", [12]),
            ("@", 1, "@**Human Myself**", [12]),
            ("@", 2, "@**Human 1**", [12]),
            ("@", -1, "@*Group 4*", [12]),
            ("@", 0, "@**Human 1**", [11, 12]),
            ("@", 1, "@**Human 2**", [11, 12]),
            ("@", 2, "@**Human Myself**", [11, 12]),
            ("@", -1, "@*Group 4*", [11, 12]),
        ],
    )
    def test_generic_autocomplete_mentions_subscribers(
        self,
        write_box: WriteBox,
        text: str,
        required_typeahead: str,
        state: Optional[int],
        recipients: List[int],
    ) -> None:
        write_box.recipient_user_ids = recipients
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, expected_distinct_prefix",
        # Add 3 different lists of tuples, with each tuple containing a combination
        # of the text to be autocompleted and the corresponding typeahead prefix to
        # be added to the typeahead suggestions. Only the "@" case has to be ignored
        # while building the parameters, because it includes group suggestions too.
        [("@" + "Human"[: index + 1], "@") for index in range(len("Human"))]
        + [("@**" + "Human"[:index], "@") for index in range(len("Human") + 1)]
        + [("@_" + "Human"[:index], "@_") for index in range(len("Human") + 1)],
    )
    def test_generic_autocomplete_user_mentions(
        self,
        write_box: WriteBox,
        mocker: MockerFixture,
        text: str,
        expected_distinct_prefix: str,
        state: Optional[int] = 1,
    ) -> None:
        _process_typeaheads = mocker.patch(WRITEBOX + "._process_typeaheads")

        write_box.generic_autocomplete(text, state)

        matching_users = [
            "Human Myself",
            "Human 1",
            "Human 2",
            "Human Duplicate",
            "Human Duplicate",
        ]
        distinct_matching_users = [
            expected_distinct_prefix + "**Human Myself**",
            expected_distinct_prefix + "**Human 1**",
            expected_distinct_prefix + "**Human 2**",
            expected_distinct_prefix + "**Human Duplicate|13**",
            expected_distinct_prefix + "**Human Duplicate|14**",
        ]
        _process_typeaheads.assert_called_once_with(
            distinct_matching_users, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, state_and_required_typeahead, stream_categories",
        [
            (
                # With no streams in stream_categories.
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Stream 2**",
                    2: "#**Secret stream**",
                    3: "#**Some general stream**",
                    4: "#**Web public stream**",
                },
                {},
            ),
            (
                "#S",
                {
                    0: "#**Secret stream**",
                    1: "#**Some general stream**",
                    2: "#**Stream 1**",
                    3: "#**Stream 2**",
                    4: "#**Web public stream**",
                    -1: "#**Web public stream**",
                    -2: "#**Stream 2**",
                    -3: "#**Stream 1**",
                    -4: "#**Some general stream**",
                    -5: "#**Secret stream**",
                    -6: None,
                },
                {},
            ),
            ("#So", {0: "#**Some general stream**", 1: None}, {}),
            ("#Se", {0: "#**Secret stream**", 1: None}, {}),
            ("#St", {0: "#**Stream 1**", 1: "#**Stream 2**"}, {}),
            ("#g", {0: "#**Some general stream**", 1: None}, {}),
            ("#Stream 1", {0: "#**Stream 1**"}, {}),  # Complete match.
            ("#nomatch", {0: None}, {}),
            ("#ene", {0: None}, {}),
            # Complex autocomplete prefixes.
            ("[#Stream", {0: "[#**Stream 1**"}, {}),
            ("(#Stream", {1: "(#**Stream 2**"}, {}),
            ("@#Stream", {0: "@#**Stream 1**"}, {}),
            ("@_#Stream", {0: "@_#**Stream 1**"}, {}),
            (":#Stream", {0: ":#**Stream 1**"}, {}),
            ("##Stream", {0: "##**Stream 1**"}, {}),
            ("##*Stream", {0: None}, {}),  # NOTE: Optional single star fails
            ("##**Stream", {0: "##**Stream 1**"}, {}),  # Optional 2-stars
            # With 'Secret stream' pinned.
            (
                "#Stream",
                {
                    0: "#**Secret stream**",
                    1: "#**Stream 1**",
                    2: "#**Stream 2**",
                    3: "#**Some general stream**",
                    4: "#**Web public stream**",
                },
                {"pinned": ["Secret stream"]},
            ),
            # With 'Stream 1' and 'Secret stream' pinned.
            (
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Secret stream**",
                    2: "#**Stream 2**",
                    3: "#**Some general stream**",
                    4: "#**Web public stream**",
                },
                {"pinned": ["Secret stream", "Stream 1"]},
            ),
            # With 'Secret stream' muted.
            (
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Stream 2**",
                    2: "#**Some general stream**",
                    3: "#**Web public stream**",
                    4: "#**Secret stream**",
                },
                {"muted": ["Secret stream"]},
            ),
            # With 'Stream 1' and 'Secret stream' muted.
            (
                "#Stream",
                {
                    0: "#**Stream 2**",
                    1: "#**Some general stream**",
                    2: "#**Web public stream**",
                    3: "#**Stream 1**",
                    4: "#**Secret stream**",
                },
                {"muted": ["Secret stream", "Stream 1"]},
            ),
            # With 'Stream 1' and 'Secret stream' pinned, 'Secret stream' muted.
            (
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Secret stream**",
                    2: "#**Stream 2**",
                    3: "#**Some general stream**",
                    4: "#**Web public stream**",
                },
                {"pinned": ["Secret stream", "Stream 1"], "muted": ["Secret stream"]},
            ),
            # With 'Stream 1' and 'Secret stream' pinned,
            # 'Some general stream' and 'Stream 2' muted.
            (
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Secret stream**",
                    2: "#**Web public stream**",
                    3: "#**Stream 2**",
                    4: "#**Some general stream**",
                },
                {
                    "pinned": ["Secret stream", "Stream 1"],
                    "muted": ["Some general stream", "Stream 2"],
                },
            ),
            # With 'Stream 1' and 'Secret stream' pinned,
            # 'Secret stream' and 'Stream 2' muted.
            (
                "#Stream",
                {
                    0: "#**Stream 1**",
                    1: "#**Secret stream**",
                    2: "#**Some general stream**",
                    3: "#**Web public stream**",
                    4: "#**Stream 2**",
                },
                {
                    "pinned": ["Secret stream", "Stream 1"],
                    "muted": ["Secret stream", "Stream 2"],
                },
            ),
            # With 'Stream 1' as current stream.
            (
                "#S",
                {
                    0: "#**Stream 1**",
                    1: "#**Secret stream**",
                    2: "#**Some general stream**",
                    3: "#**Stream 2**",
                    4: "#**Web public stream**",
                },
                {"current_stream": 1},
            ),
            # With 'Stream 1' and 'Secret stream' pinned,
            # 'Secret stream' and 'Stream 2' muted, 'Stream 2' as current stream.
            (
                "#Stream",
                {
                    0: "#**Stream 2**",
                    1: "#**Stream 1**",
                    2: "#**Secret stream**",
                    3: "#**Some general stream**",
                    4: "#**Web public stream**",
                },
                {
                    "pinned": ["Secret stream", "Stream 1"],
                    "muted": ["Secret stream", "Stream 2"],
                    "current_stream": 2,
                },
            ),
        ],
    )
    def test_generic_autocomplete_streams(
        self,
        write_box: WriteBox,
        text: str,
        state_and_required_typeahead: Dict[int, Optional[str]],
        stream_categories: Dict[str, Any],
        stream_dict: Dict[int, Dict[str, Any]],
    ) -> None:
        streams_to_pin = (
            [{"name": stream_name} for stream_name in stream_categories["pinned"]]
            if "pinned" in stream_categories
            else []
        )
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        write_box.stream_id = stream_categories.get("current_stream", None)
        write_box.model.stream_dict = stream_dict
        write_box.model.muted_streams = {
            stream["stream_id"]
            for stream in stream_dict.values()
            if stream["name"] in stream_categories.get("muted", set())
        }
        states = state_and_required_typeahead.keys()
        required_typeaheads = list(state_and_required_typeahead.values())
        typeahead_strings = [
            write_box.generic_autocomplete(text, state) for state in states
        ]
        assert typeahead_strings == required_typeaheads

    @pytest.mark.parametrize(
        "text, state, required_typeahead",
        [
            (":rock_o", 0, ":rock_on:"),
            (":rock_o", 1, None),
            (":rock_o", -1, ":rock_on:"),
            (":rock_o", -2, None),
            (":smi", 0, ":smile:"),
            (":smi", 1, ":smiley:"),
            (":smi", 2, ":smirk:"),
            (":jo", 0, ":joker:"),
            (":jo", 1, ":joy_cat:"),
            (":jok", 0, ":joker:"),
            (":", 0, ":happy:"),
            (":", 1, ":joker:"),
            (":", -3, ":smiley:"),
            (":", -2, ":smirk:"),
            (":nomatch", 0, None),
            (":nomatch", -1, None),
            # Complex autocomplete prefixes.
            ("(:smi", 0, "(:smile:"),
            ("&:smi", 1, "&:smiley:"),
            ("@:smi", 0, "@:smile:"),
            ("@_:smi", 0, "@_:smile:"),
            ("#:smi", 0, "#:smile:"),
        ],
    )
    def test_generic_autocomplete_emojis(
        self,
        write_box: WriteBox,
        text: str,
        state: Optional[int],
        required_typeahead: Optional[str],
    ) -> None:
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, matching_users, matching_users_info",
        [
            (
                "",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Human Myself <FOOBOO@gmail.com>",
                    "Human 1 <person1@example.com>",
                    "Human 2 <person2@example.com>",
                    "Human Duplicate <personduplicate1@example.com>",
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            ("My", ["Human Myself"], ["Human Myself <FOOBOO@gmail.com>"]),
        ],
        ids=[
            "no_search_text",
            "single_word_search_text",
        ],
    )
    def test__to_box_autocomplete(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        text: str,
        matching_users: List[str],
        matching_users_info: List[str],
        state: Optional[int] = 1,
    ) -> None:
        _process_typeaheads = mocker.patch(WRITEBOX + "._process_typeaheads")

        write_box._to_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_users_info, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Hu", "Human Myself <FOOBOO@gmail.com>"),
            ("Human M", "Human Myself <FOOBOO@gmail.com>"),
            ("Human Myself <FOOBOO", "Human Myself <FOOBOO@gmail.com>"),
        ],
    )
    def test__to_box_autocomplete_with_spaces(
        self,
        write_box: WriteBox,
        text: str,
        expected_text: str,
        widget_size: Callable[[Widget], urwid_Size],
        user_id_email_dict: Dict[int, str],
    ) -> None:
        write_box.model.user_id_email_dict = user_id_email_dict
        write_box.private_box_view(recipient_user_ids=[1])
        assert write_box.to_write_box is not None
        write_box.to_write_box.set_edit_text(text)
        write_box.to_write_box.set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.to_write_box.edit_text == expected_text

    @pytest.mark.parametrize(
        "text, matching_users, matching_users_info",
        [
            (
                "Welcome Bot <welcome-bot@zulip.com>, Human",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Myself <FOOBOO@gmail.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human 1 <person1@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human 2 <person2@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Duplicate <personduplicate1@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            (
                "Welcome Bot <welcome-bot@zulip.com>, Notification Bot "
                "<notification-bot@zulip.com>, person2",
                ["Human 2"],
                [
                    "Welcome Bot <welcome-bot@zulip.com>, Notification Bot "
                    "<notification-bot@zulip.com>, Human 2 <person2@example.com>"
                ],
            ),
            (
                "Email Gateway <emailgateway@zulip.com>,Human",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Myself <FOOBOO@gmail.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human 1 <person1@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human 2 <person2@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Duplicate <personduplicate1@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            (
                "Human 1 <person1@example.com>, Notification Bot "
                "<notification-bot@zulip.com>,person2",
                ["Human 2"],
                [
                    "Human 1 <person1@example.com>, Notification Bot "
                    "<notification-bot@zulip.com>, Human 2 <person2@example.com>"
                ],
            ),
        ],
        ids=[
            "name_search_text_with_space_after_separator",
            "email_search_text_with_space_after_separator",
            "name_search_text_without_space_after_separator",
            "email_search_text_without_space_after_separator",
        ],
    )
    def test__to_box_autocomplete_with_multiple_recipients(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        text: str,
        matching_users: List[str],
        matching_users_info: List[str],
        state: Optional[int] = 1,
    ) -> None:
        _process_typeaheads = mocker.patch(WRITEBOX + "._process_typeaheads")

        write_box._to_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_users_info, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, state, to_pin, matching_streams",
        [
            (
                "",
                1,
                [],
                [
                    "Secret stream",
                    "Some general stream",
                    "Stream 1",
                    "Stream 2",
                    "Web public stream",
                ],
            ),
            (
                "",
                1,
                ["Stream 2"],
                [
                    "Stream 2",
                    "Secret stream",
                    "Some general stream",
                    "Stream 1",
                    "Web public stream",
                ],
            ),
            (
                "St",
                1,
                [],
                [
                    "Stream 1",
                    "Stream 2",
                    "Secret stream",
                    "Some general stream",
                    "Web public stream",
                ],
            ),
            (
                "St",
                1,
                ["Stream 2"],
                [
                    "Stream 2",
                    "Stream 1",
                    "Secret stream",
                    "Some general stream",
                    "Web public stream",
                ],
            ),
        ],
        ids=[
            "no_search_text",
            "no_search_text_with_pinned_stream",
            "single_word_search_text",
            "single_word_search_text_with_pinned_stream",
        ],
    )
    def test__stream_box_autocomplete(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        text: str,
        state: Optional[int],
        to_pin: List[str],
        matching_streams: List[str],
    ) -> None:
        streams_to_pin = [{"name": stream_name} for stream_name in to_pin]
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        _process_typeaheads = mocker.patch(WRITEBOX + "._process_typeaheads")

        write_box._stream_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_streams, state, matching_streams
        )

    @pytest.mark.parametrize(
        "stream_name, stream_id, is_valid_stream, stream_access_type,"
        " expected_marker, expected_color",
        [
            (
                "Web public stream",
                999,
                True,
                "web-public",
                STREAM_MARKER_WEB_PUBLIC,
                "#ddd",
            ),
            ("Secret stream", 99, True, "private", STREAM_MARKER_PRIVATE, "#ccc"),
            ("Stream 1", 1, True, "public", STREAM_MARKER_PUBLIC, "#b0a5fd"),
            ("Stream 0", 0, False, None, INVALID_MARKER, "general_bar"),
        ],
        ids=[
            "web_public_stream",
            "private_stream",
            "public_stream",
            "invalid_stream_name",
        ],
    )
    def test__set_stream_write_box_style_markers(
        self,
        write_box: WriteBox,
        stream_id: int,
        stream_name: str,
        is_valid_stream: bool,
        stream_access_type: StreamAccessType,
        expected_marker: str,
        stream_dict: Dict[int, Any],
        expected_color: str,
    ) -> None:
        # FIXME: Refactor when we have ~ Model.is_private_stream
        write_box.model.stream_dict = stream_dict
        write_box.model.is_valid_stream.return_value = is_valid_stream
        write_box.model.stream_id_from_name.return_value = stream_id
        write_box.model.stream_access_type.return_value = stream_access_type

        write_box.stream_box_view(stream_id)

        write_box._set_stream_write_box_style(write_box, stream_name)

        stream_marker = write_box.header_write_box[write_box.FOCUS_HEADER_PREFIX_STREAM]

        assert stream_marker.text == expected_marker
        assert stream_marker.attrib[0][0] == expected_color

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Som", "Some general stream"),
            ("Some gen", "Some general stream"),
        ],
    )
    def test__stream_box_autocomplete_with_spaces(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
        text: str,
        expected_text: str,
    ) -> None:
        mocker.patch(WRITEBOX + "._set_stream_write_box_style")
        write_box.stream_box_view(1000)
        stream_focus = write_box.FOCUS_HEADER_BOX_STREAM
        write_box.header_write_box[stream_focus].set_edit_text(text)
        write_box.header_write_box[stream_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = stream_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.header_write_box[stream_focus].edit_text == expected_text

    @pytest.mark.parametrize(
        "text, matching_topics",
        [
            (
                "",
                [
                    "Topic 1",
                    "This is a topic",
                    "Hello there!",
                    "He-llo there!",
                    "Hello t/here!",
                    "Hello from out-er_space!",
                ],
            ),
            ("Th", ["This is a topic", "Hello there!", "He-llo there!"]),
            ("ll", ["He-llo there!"]),
            ("her", ["Hello t/here!"]),
            ("er", ["Hello from out-er_space!"]),
            ("spa", ["Hello from out-er_space!"]),
        ],
        ids=[
            "no_search_text",
            "single_word_search_text",
            "split_in_first_word",
            "split_in_second_word",
            "first_split_in_third_word",
            "second_split_in_third_word",
        ],
    )
    def test__topic_box_autocomplete(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        text: str,
        topics: List[str],
        matching_topics: List[str],
        state: Optional[int] = 1,
    ) -> None:
        write_box.model.topics_in_stream.return_value = topics
        _process_typeaheads = mocker.patch(WRITEBOX + "._process_typeaheads")

        write_box._topic_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_topics, state, matching_topics
        )

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Th", "This is a topic"),
            ("This i", "This is a topic"),
        ],
    )
    def test__topic_box_autocomplete_with_spaces(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
        text: str,
        expected_text: str,
        topics: List[str],
    ) -> None:
        mocker.patch(WRITEBOX + "._set_stream_write_box_style")
        write_box.stream_box_view(1000)
        write_box.model.topics_in_stream.return_value = topics
        topic_focus = write_box.FOCUS_HEADER_BOX_TOPIC
        write_box.header_write_box[topic_focus].set_edit_text(text)
        write_box.header_write_box[topic_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = topic_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.header_write_box[topic_focus].edit_text == expected_text

    @pytest.mark.parametrize(
        "suggestions, state, expected_state, expected_typeahead, is_truncated",
        [
            (["zero", "one", "two"], 1, 1, "*one*", False),
            (["zero", "one", "two"] * 4, 1, 1, "*one*", True),
            (["zero", "one", "two"], None, None, None, False),
            (["zero", "one", "two"], 5, None, None, False),
            (["zero", "one", "two"], -5, None, None, False),
        ],
        ids=[
            "fewer_than_10_typeaheads",
            "more_than_10_typeaheads",
            "invalid_state-None",
            "invalid_state-greater_than_possible_index",
            "invalid_state-less_than_possible_index",
        ],
    )
    def test__process_typeaheads(
        self,
        write_box: WriteBox,
        suggestions: List[str],
        state: Optional[int],
        expected_state: Optional[int],
        expected_typeahead: Optional[str],
        is_truncated: bool,
        mocker: MockerFixture,
    ) -> None:
        write_box.view.set_typeahead_footer = mocker.patch(
            "zulipterminal.ui.View.set_typeahead_footer"
        )
        # Use an example formatting to differentiate between
        # typeaheads and suggestions.
        typeaheads = [f"*{s}*" for s in suggestions]

        typeahead = write_box._process_typeaheads(typeaheads, state, suggestions)

        assert typeahead == expected_typeahead
        write_box.view.set_typeahead_footer.assert_called_once_with(
            suggestions[:10], expected_state, is_truncated
        )

    @pytest.mark.parametrize(
        "topic_entered_by_user, topic_sent_to_server",
        [
            ("", "(no topic)"),
            ("hello", "hello"),
            ("  ", "(no topic)"),
        ],
        ids=[
            "empty_topic",
            "non_empty_topic",
            "topic_with_whitespace",
        ],
    )
    @pytest.mark.parametrize(
        "msg_edit_state",
        [_MessageEditState(message_id=10, old_topic="old topic"), None],
        ids=["update_message", "send_message"],
    )
    @pytest.mark.parametrize("key", keys_for_command("SEND_MESSAGE"))
    def test_keypress_SEND_MESSAGE_no_topic(
        self,
        mocker: MockerFixture,
        write_box: WriteBox,
        msg_edit_state: Optional[_MessageEditState],
        topic_entered_by_user: str,
        topic_sent_to_server: str,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
        propagate_mode: str = "change_one",
    ) -> None:
        write_box.stream_write_box = mocker.Mock()
        write_box.msg_write_box = mocker.Mock(edit_text="")
        write_box.title_write_box = mocker.Mock(edit_text=topic_entered_by_user)
        write_box.compose_box_status = "open_with_stream"
        size = widget_size(write_box)
        write_box.msg_edit_state = msg_edit_state
        write_box.edit_mode_button = mocker.Mock(mode=propagate_mode)

        write_box.keypress(size, key)

        if msg_edit_state:
            write_box.model.update_stream_message.assert_called_once_with(
                topic=topic_sent_to_server,
                content=write_box.msg_write_box.edit_text,
                message_id=msg_edit_state.message_id,
                propagate_mode=propagate_mode,
            )
        else:
            write_box.model.send_stream_message.assert_called_once_with(
                stream=write_box.stream_write_box.edit_text,
                topic=topic_sent_to_server,
                content=write_box.msg_write_box.edit_text,
            )

    @pytest.mark.parametrize(
        "key, current_typeahead_mode, expected_typeahead_mode, expect_footer_was_reset",
        [
            # footer does not reset
            (primary_key_for_command("AUTOCOMPLETE"), False, False, False),
            (primary_key_for_command("AUTOCOMPLETE_REVERSE"), False, False, False),
            (primary_key_for_command("AUTOCOMPLETE"), True, True, False),
            (primary_key_for_command("AUTOCOMPLETE_REVERSE"), True, True, False),
            # footer resets
            (primary_key_for_command("GO_BACK"), True, False, True),
            ("space", True, False, True),
            ("k", True, False, True),
        ],
    )
    def test_keypress_typeahead_mode_autocomplete_key(
        self,
        write_box: WriteBox,
        widget_size: Callable[[Widget], urwid_Size],
        current_typeahead_mode: bool,
        expected_typeahead_mode: bool,
        expect_footer_was_reset: bool,
        key: str,
    ) -> None:
        write_box.is_in_typeahead_mode = current_typeahead_mode
        size = widget_size(write_box)

        write_box.keypress(size, key)

        assert write_box.is_in_typeahead_mode == expected_typeahead_mode
        if expect_footer_was_reset:
            self.view.set_footer_text.assert_called_once_with()
        else:
            self.view.set_footer_text.assert_not_called()

    @pytest.mark.parametrize(
        [
            "initial_focus_name",
            "initial_focus_col_name",
            "box_type",
            "msg_body_edit_enabled",
            "message_being_edited",
            "expected_focus_name",
            "expected_focus_col_name",
        ],
        [
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                "stream",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="stream_name_to_topic_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                True,
                False,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="topic_to_message_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                False,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                id="topic_edit_only-topic_to_edit_mode_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                "stream",
                False,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="topic_edit_only-edit_mode_to_topic_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "stream",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                id="message_to_stream_name_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="edit_box-stream_name_to_topic_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                id="edit_box-topic_to_edit_mode_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                "stream",
                True,
                True,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="edit_box-edit_mode_to_message_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="edit_box-message_to_stream_name_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_RECIPIENT",
                "private",
                True,
                False,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="recipient_to_message_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "private",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_RECIPIENT",
                id="message_to_recipient_box",
            ),
        ],
    )
    @pytest.mark.parametrize("tab_key", keys_for_command("CYCLE_COMPOSE_FOCUS"))
    def test_keypress_CYCLE_COMPOSE_FOCUS(
        self,
        write_box: WriteBox,
        tab_key: str,
        initial_focus_name: str,
        expected_focus_name: str,
        initial_focus_col_name: str,
        expected_focus_col_name: str,
        box_type: str,
        msg_body_edit_enabled: bool,
        message_being_edited: bool,
        widget_size: Callable[[Widget], urwid_Size],
        mocker: MockerFixture,
        stream_id: int = 10,
    ) -> None:
        mocker.patch(WRITEBOX + "._set_stream_write_box_style")

        if box_type == "stream":
            if message_being_edited:
                mocker.patch(MODULE + ".EditModeButton")
                write_box.stream_box_edit_view(stream_id)
                write_box.msg_edit_state = _MessageEditState(
                    message_id=10, old_topic="some old topic"
                )
            else:
                write_box.stream_box_view(stream_id)
        else:
            write_box.private_box_view()
        size = widget_size(write_box)

        def focus_val(x: str) -> int:
            return getattr(write_box, "FOCUS_" + x)

        write_box.focus_position = focus_val(initial_focus_name)
        write_box.msg_body_edit_enabled = msg_body_edit_enabled
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            write_box.header_write_box.focus_col = focus_val(initial_focus_col_name)
        write_box.model.get_invalid_recipient_emails.return_value = []
        write_box.model.user_dict = mocker.MagicMock()

        write_box.keypress(size, tab_key)

        assert write_box.focus_position == focus_val(expected_focus_name)
        # FIXME: Needs refactoring?
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            assert write_box.header_write_box.focus_col == focus_val(
                expected_focus_col_name
            )
        else:
            assert write_box.FOCUS_MESSAGE_BOX_BODY == focus_val(  # noqa: SIM300
                expected_focus_col_name
            )

    def test__setup_common_private_compose(self, mocker: MockerFixture) -> None:
        write_box = WriteBox(self.view)
        write_box.to_write_box = mocker.MagicMock()
        write_box.msg_write_box = mocker.MagicMock()

        enable_autocomplete_mock = mocker.patch.object(
            ReadlineEdit, "enable_autocomplete"
        )
        write_box._setup_common_private_compose()
        connect_signal_mock = mocker.patch.object(urwid, "connect_signal")
        assert hasattr(write_box, "msg_write_box")
        connect_signal_mock.assert_not_called()
        enable_autocomplete_mock.assert_called_once()

        enable_autocomplete_mock.assert_has_calls(
            [
                mock.call(
                    func=write_box.generic_autocomplete,
                    key=primary_key_for_command("AUTOCOMPLETE"),
                    key_reverse=primary_key_for_command("AUTOCOMPLETE_REVERSE"),
                ),
            ]
        )
        assert write_box.focus_position == 1

    @pytest.mark.parametrize("key", keys_for_command("MARKDOWN_HELP"))
    def test_keypress_MARKDOWN_HELP(
        self, write_box: WriteBox, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(write_box)

        write_box.keypress(size, key)

        write_box.view.controller.show_markdown_help.assert_called_once_with()

    @pytest.mark.parametrize(
        "msg_type, expected_box_size",
        [
            ("private", 1),
            ("stream", 4),
            ("stream_edit", 5),
        ],
        ids=[
            "private_message",
            "stream_message",
            "stream_edit_message",
        ],
    )
    def test_write_box_header_contents(
        self,
        write_box: WriteBox,
        expected_box_size: int,
        mocker: MockerFixture,
        msg_type: str,
        user_id_email_dict: Dict[int, str],
    ) -> None:
        mocker.patch(WRITEBOX + "._set_stream_write_box_style")
        mocker.patch(WRITEBOX + ".set_editor_mode")
        write_box.model.user_id_email_dict = user_id_email_dict
        if msg_type == "stream":
            write_box.stream_box_view(1000)
        elif msg_type == "stream_edit":
            write_box.stream_box_edit_view(1000)
        else:
            write_box.private_box_view(recipient_user_ids=[1])

        assert len(write_box.header_write_box.widget_list) == expected_box_size


class TestPanelSearchBox:
    search_caption = " Search Results  "

    @pytest.fixture
    def panel_search_box(self, mocker: MockerFixture) -> PanelSearchBox:
        # X is the return from keys_for_command("UNTESTED_TOKEN")
        mocker.patch(MODULE + ".keys_for_command", return_value="X")
        panel_view = mocker.Mock()
        update_func = mocker.Mock()
        return PanelSearchBox(panel_view, "UNTESTED_TOKEN", update_func)

    def test_init(self, panel_search_box: PanelSearchBox) -> None:
        assert panel_search_box.search_text == " Search [X]: "
        assert panel_search_box.caption == panel_search_box.search_text
        assert panel_search_box.edit_text == ""

    def test_reset_search_text(self, panel_search_box: PanelSearchBox) -> None:
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_search_box.reset_search_text()

        assert panel_search_box.caption == panel_search_box.search_text
        assert panel_search_box.edit_text == ""

    @pytest.mark.parametrize(
        "search_text, entered_string, expected_result",
        [
            # NOTE: In both backspace cases it is not validated (backspace is not
            #       shown), but still is handled during editing as normal
            # NOTE: Unicode backspace case likely doesn't get triggered
            case("", "backspace", False, id="no_text-disallow_urwid_backspace"),
            case("", "\u0008", False, id="no_text-disallow_unicode_backspace"),
            case("", "\u2003", False, id="no_text-disallow_unicode_em_space"),
            case("", "x", True, id="no_text-allow_entry_of_x"),
            case("", "\u0394", True, id="no_text-allow_entry_of_delta"),
            case("", " ", False, id="no_text-disallow_entry_of_space"),
            case("x", " ", True, id="text-allow_entry_of_space"),
            case("x", "backspace", False, id="text-disallow_urwid_backspace"),
        ],
    )
    def test_valid_char(
        self,
        panel_search_box: PanelSearchBox,
        search_text: str,
        entered_string: str,
        expected_result: bool,
    ) -> None:
        panel_search_box.edit_text = search_text

        result = panel_search_box.valid_char(entered_string)

        assert result == expected_result

    @pytest.mark.parametrize(
        "log, expect_body_focus_set", [([], False), (["SOMETHING"], True)]
    )
    @pytest.mark.parametrize("enter_key", keys_for_command("ENTER"))
    def test_keypress_ENTER(
        self,
        panel_search_box: PanelSearchBox,
        widget_size: Callable[[Widget], urwid_Size],
        enter_key: str,
        log: List[str],
        expect_body_focus_set: bool,
    ) -> None:
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = lambda: True
        panel_search_box.panel_view.log = log
        empty_search = not log
        panel_search_box.panel_view.empty_search = empty_search
        panel_search_box.set_caption("")
        panel_search_box.edit_text = "key words"

        panel_search_box.keypress(size, enter_key)

        # Update this display
        # FIXME We can't test for the styled version?
        # We'd compare to [('filter_results', 'Search Results'), ' ']

        assert panel_search_box.edit_text == "key words"

        panel_view = panel_search_box.panel_view
        if expect_body_focus_set:
            assert panel_search_box.caption == self.search_caption
            # Leave editor mode
            panel_view.view.controller.exit_editor_mode.assert_called_once_with()
            # Switch focus to body; if have results, move to them
            panel_view.set_focus.assert_called_once_with("body")
            panel_view.body.set_focus.assert_called_once_with(0)
        else:
            assert panel_search_box.caption == ""
            panel_view.view.controller.exit_editor_mode.assert_not_called()
            panel_view.set_focus.assert_not_called()
            panel_view.body.set_focus.assert_not_called()

    @pytest.mark.parametrize("back_key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(
        self,
        panel_search_box: PanelSearchBox,
        back_key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = lambda: True
        panel_search_box.panel_view.view.controller.is_any_popup_open = lambda: False
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_view = panel_search_box.panel_view

        panel_search_box.keypress(size, back_key)

        # Reset display
        assert panel_search_box.caption == panel_search_box.search_text
        assert panel_search_box.edit_text == ""

        # Leave editor mode
        panel_view.view.controller.exit_editor_mode.assert_called_once_with()

        # Switch focus to body; focus should return to previous in body
        panel_view.set_focus.assert_called_once_with("body")

        # pass keypress back
        # FIXME This feels hacky to call keypress (with hardcoded 'esc' too)
        #       - should we add a second callback to update the panel?
        panel_view.keypress.assert_called_once_with(size, "esc")
