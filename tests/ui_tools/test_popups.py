from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest.mock import patch

import pytest
from pytest import param as case
from pytest_mock import MockerFixture
from urwid import Columns, Pile, Text, Widget

from zulipterminal.api_types import Message
from zulipterminal.config.keys import is_command_key, keys_for_command
from zulipterminal.config.ui_mappings import EDIT_MODE_CAPTIONS
from zulipterminal.helper import CustomProfileData, TidiedUserInfo
from zulipterminal.ui_tools.messages import MessageBox
from zulipterminal.ui_tools.views import (
    AboutView,
    EditHistoryTag,
    EditHistoryView,
    EditModeView,
    EmojiPickerView,
    FullRawMsgView,
    FullRenderedMsgView,
    HelpView,
    MarkdownHelpView,
    MsgInfoView,
    PopUpConfirmationView,
    PopUpView,
    StreamInfoView,
    StreamMembersView,
    UserInfoView,
)
from zulipterminal.urwid_types import urwid_Size
from zulipterminal.version import MINIMUM_SUPPORTED_SERVER_VERSION, ZT_VERSION


MODULE = "zulipterminal.ui_tools.views"
LISTWALKER = MODULE + ".urwid.SimpleFocusListWalker"

# Test classes are grouped/ordered below as:
#  * an independent popup class
#  * the base general popup class
#  * classes derived from the base popup class, sorted alphabetically


class TestPopUpConfirmationView:
    @pytest.fixture
    def popup_view(self, mocker: MockerFixture) -> PopUpConfirmationView:
        self.controller = mocker.Mock()
        self.callback = mocker.Mock()
        self.list_walker = mocker.patch(LISTWALKER, return_value=[])
        self.divider = mocker.patch(MODULE + ".urwid.Divider")
        self.text = mocker.patch(MODULE + ".urwid.Text")
        self.wrapper_w = mocker.patch(MODULE + ".urwid.WidgetWrap")
        return PopUpConfirmationView(
            self.controller,
            self.text,
            self.callback,
        )

    def test_init(self, popup_view: PopUpConfirmationView) -> None:
        assert popup_view.controller == self.controller
        assert popup_view.success_callback == self.callback
        self.divider.assert_called_once_with()
        self.list_walker.assert_called_once_with(
            [self.text, self.divider(), self.wrapper_w()]
        )

    def test_exit_popup_yes(
        self, mocker: MockerFixture, popup_view: PopUpConfirmationView
    ) -> None:
        popup_view.exit_popup_yes(mocker.Mock())
        self.callback.assert_called_once_with()
        assert self.controller.exit_popup.called

    def test_exit_popup_no(
        self, mocker: MockerFixture, popup_view: PopUpConfirmationView
    ) -> None:
        popup_view.exit_popup_no(mocker.Mock())
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("EXIT_POPUP"))
    def test_exit_popup_EXIT_POPUP(
        self,
        popup_view: PopUpConfirmationView,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(popup_view)
        popup_view.keypress(size, key)
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called


class TestPopUpView:
    @pytest.fixture(autouse=True)
    def pop_up_view_autouse(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.command = "COMMAND"
        self.title = "Generic title"
        self.width = 16
        self.body = mocker.Mock()
        self.header = mocker.Mock()
        self.footer = mocker.Mock()
        mocker.patch.object(self.body, "rows", return_value=1)
        mocker.patch.object(self.header, "rows", return_value=1)
        mocker.patch.object(self.footer, "rows", return_value=1)
        self.body = [self.body]
        self.header = Pile([self.header])
        self.footer = Pile([self.footer])
        self.list_walker = mocker.patch(LISTWALKER, return_value=[])
        self.super_init = mocker.patch(MODULE + ".urwid.Frame.__init__")
        self.super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.pop_up_view = PopUpView(
            self.controller,
            self.body,
            self.command,
            self.width,
            self.title,
            self.header,
            self.footer,
        )

    def test_init(self, mocker: MockerFixture) -> None:
        assert self.pop_up_view.controller == self.controller
        assert self.pop_up_view.command == self.command
        assert self.pop_up_view.title == self.title
        assert self.pop_up_view.width == self.width
        self.list_walker.assert_called_once_with(self.body)
        self.super_init.assert_called_once_with(
            self.pop_up_view.body, header=mocker.ANY, footer=mocker.ANY
        )

    @pytest.mark.parametrize("key", keys_for_command("EXIT_POPUP"))
    def test_keypress_EXIT_POPUP(
        self,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(self.pop_up_view)
        self.pop_up_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_command_key(
        self,
        mocker: MockerFixture,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(self.pop_up_view)
        mocker.patch(
            MODULE + ".is_command_key",
            side_effect=(lambda command, key: command == self.command),
        )
        self.pop_up_view.keypress(size, "cmd_key")
        assert self.controller.exit_popup.called

    def test_keypress_navigation(
        self,
        mocker: MockerFixture,
        navigation_key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(self.pop_up_view)
        # Patch `is_command_key` to not raise an 'Invalid Command' exception
        # when its parameters are (self.command, key) as there is no
        # self.command='COMMAND' command in keys.py.
        mocker.patch(
            MODULE + ".is_command_key",
            side_effect=(
                lambda command, key: (
                    False if command == self.command else is_command_key(command, key)
                )
            ),
        )

        self.pop_up_view.keypress(size, navigation_key)

        self.super_keypress.assert_called_once_with(size, navigation_key)


class TestAboutView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        server_version, server_feature_level = MINIMUM_SUPPORTED_SERVER_VERSION

        # FIXME: Since we don't test on WSL explicitly, for now
        #        treat PLATFORM as WSL in order for it to be supported
        mocker.patch(MODULE + ".PLATFORM", "WSL")

        mocker.patch(MODULE + ".detected_python_in_full", lambda: "[Python version]")

        self.about_view = AboutView(
            self.controller,
            "About",
            zt_version=ZT_VERSION,
            server_version=server_version,
            server_feature_level=server_feature_level,
            theme_name="zt_dark",
            color_depth=256,
            notify_enabled=False,
            autohide_enabled=False,
            maximum_footlinks=3,
            exit_confirmation_enabled=False,
            transparency_enabled=False,
        )

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("ABOUT")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", {*keys_for_command("COPY_ABOUT_INFO")})
    def test_keypress_copy_info(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert self.controller.copy_to_clipboard.called

    def test_keypress_exit_popup_invalid_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    def test_feature_level_content(
        self, mocker: MockerFixture, zulip_version: Tuple[str, int]
    ) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(LISTWALKER, return_value=[])
        server_version, server_feature_level = zulip_version

        about_view = AboutView(
            self.controller,
            "About",
            zt_version=ZT_VERSION,
            server_version=server_version,
            server_feature_level=server_feature_level,
            theme_name="zt_dark",
            color_depth=256,
            notify_enabled=False,
            autohide_enabled=False,
            maximum_footlinks=3,
            exit_confirmation_enabled=False,
            transparency_enabled=False,
        )

        assert len(about_view.feature_level_content) == (
            1 if server_feature_level else 0
        )

    def test_categories(self) -> None:
        categories = [
            widget.text
            for widget in self.about_view.log
            if isinstance(widget, Text)
            and len(widget.attrib)
            and "popup_category" in widget.attrib[0][0]
        ]
        assert categories == [
            "Application",
            "Server",
            "Application Configuration",
            "Detected Environment",
            "Copy information to clipboard [c]",
        ]

    def test_copied_content(self) -> None:
        expected_output = f"""#### Application
Zulip Terminal: {ZT_VERSION}

#### Server
Version: {MINIMUM_SUPPORTED_SERVER_VERSION[0]}

#### Application Configuration
Theme: zt_dark
Autohide: disabled
Maximum footlinks: 3
Color depth: 256
Notifications: disabled
Exit confirmation: disabled
Transparency: disabled

#### Detected Environment
Platform: WSL
Python: [Python version]"""
        assert self.about_view.copy_info == expected_output


class TestUserInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(
        self, mocker: MockerFixture, tidied_user_info_response: TidiedUserInfo
    ) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(MODULE + ".urwid.SimpleFocusListWalker", return_value=[])

        self.user_data = tidied_user_info_response

        mocker.patch.object(
            self.controller.model, "get_user_info", return_value=self.user_data
        )
        mocker.patch.object(
            self.controller.model,
            "formatted_local_time",
            return_value="Tue Mar 13 10:55 AM",
        )

        mocked_user_name_from_id = {
            11: "Human 1",
            12: "Human 2",
            13: "Human 3",
        }
        self.controller.model.user_name_from_id = mocker.Mock(
            side_effect=lambda param: mocked_user_name_from_id.get(param, "(No name)")
        )

        self.user_info_view = UserInfoView(
            self.controller, 10000, "User Info (up/down scrolls)", "USER_INFO"
        )

    @pytest.mark.parametrize(
        [
            "to_vary_in_each_user",
            "expected_key",
            "expected_value",
        ],
        [
            ({}, "Email", "person2@example.com"),
            ({"email": ""}, "Email", None),
            ({"date_joined": "2021-03-18 16:52:48"}, "Date joined", "2021-03-18"),
            ({}, "Date joined", None),
            ({"timezone": "America/Los_Angeles"}, "Timezone", "America/Los Angeles"),
            ({}, "Timezone", None),
            (
                {"is_bot": True, "bot_type": 1, "bot_owner_name": "Test Owner"},
                "Owner",
                "Test Owner",
            ),
            ({}, "Owner", None),
            (
                {"last_active": "Tue Mar 13 10:55:22"},
                "Last active",
                "Tue Mar 13 10:55:22",
            ),
            ({}, "Last active", None),
            ({"is_bot": True, "bot_type": 1}, "Role", "Generic Bot"),
            ({"is_bot": True, "bot_type": 2}, "Role", "Incoming Webhook Bot"),
            ({"is_bot": True, "bot_type": 3}, "Role", "Outgoing Webhook Bot"),
            ({"is_bot": True, "bot_type": 4}, "Role", "Embedded Bot"),
            ({"role": 100}, "Role", "Owner"),
            ({"role": 200}, "Role", "Administrator"),
            ({"role": 300}, "Role", "Moderator"),
            ({"role": 600}, "Role", "Guest"),
            ({"role": 400}, "Role", "Member"),
        ],
        ids=[
            "user_email",
            "user_empty_email",
            "user_date_joined",
            "user_empty_date_joined",
            "user_timezone",
            "user_empty_timezone",
            "user_bot_owner",
            "user_empty_bot_owner",
            "user_last_active",
            "user_empty_last_active",
            "user_is_generic_bot",
            "user_is_incoming_webhook_bot",
            "user_is_outgoing_webhook_bot",
            "user_is_embedded_bot",
            "user_is_owner",
            "user_is_admin",
            "user_is_moderator",
            "user_is_guest",
            "user_is_member",
        ],
    )
    def test__fetch_user_data(
        self,
        to_vary_in_each_user: Dict[str, Any],
        expected_key: str,
        expected_value: Optional[str],
    ) -> None:
        data = dict(self.user_data, **to_vary_in_each_user)

        self.controller.model.get_user_info.return_value = data

        display_data, custom_profile_data = self.user_info_view._fetch_user_data(
            self.controller, 1
        )

        assert display_data.get(expected_key, None) == expected_value

    @pytest.mark.parametrize(
        [
            "to_vary_in_each_user",
            "expected_value",
        ],
        [
            case(
                [],
                {},
                id="user_has_no_custom_profile_data",
            ),
            case(
                [
                    {
                        "label": "Biography",
                        "value": "Simplicity",
                        "type": 2,
                        "order": 2,
                    },
                    {
                        "label": "Mentor",
                        "value": [11, 12],
                        "type": 6,
                        "order": 7,
                    },
                ],
                {"Biography": "Simplicity", "Mentor": "Human 1, Human 2"},
                id="user_has_custom_profile_data",
            ),
        ],
    )
    def test__fetch_user_data__custom_profile_data(
        self,
        to_vary_in_each_user: List[CustomProfileData],
        expected_value: Dict[str, str],
    ) -> None:
        data = dict(self.user_data)
        data["custom_profile_data"] = to_vary_in_each_user

        self.controller.model.get_user_info.return_value = data

        display_data, custom_profile_data = self.user_info_view._fetch_user_data(
            self.controller, 1
        )

        assert custom_profile_data == expected_value

    def test__fetch_user_data_USER_NOT_FOUND(self, mocker: MockerFixture) -> None:
        mocker.patch.object(self.controller.model, "get_user_info", return_value=dict())

        display_data, custom_profile_data = self.user_info_view._fetch_user_data(
            self.controller, 1
        )

        assert display_data["Name"] == "(Unavailable)"
        assert display_data["Error"] == "User data not found"
        assert custom_profile_data == {}

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("USER_INFO")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.user_info_view)
        self.user_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.user_info_view)
        self.user_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called


class TestFullRenderedMsgView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture, msg_box: MessageBox) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(MODULE + ".MessageBox", return_value=msg_box)
        # NOTE: Given that the FullRenderedMsgView just uses the message ID from
        # the message data currently, message_fixture is not used to avoid
        # adding extra test runs unnecessarily.
        self.message = Message(id=1)
        self.full_rendered_message = FullRenderedMsgView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Full Rendered Message",
        )

    def test_init(self, msg_box: MessageBox) -> None:
        assert self.full_rendered_message.title == "Full Rendered Message"
        assert self.full_rendered_message.controller == self.controller
        assert self.full_rendered_message.message == self.message
        assert self.full_rendered_message.topic_links == OrderedDict()
        assert self.full_rendered_message.message_links == OrderedDict()
        assert self.full_rendered_message.time_mentions == list()
        assert self.full_rendered_message.header.widget_list == msg_box.header
        assert self.full_rendered_message.footer.widget_list == msg_box.footer

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_rendered_message)

        self.full_rendered_message.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_rendered_message)
        key = "a"

        self.full_rendered_message.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key",
        {
            *keys_for_command("FULL_RENDERED_MESSAGE"),
            *keys_for_command("EXIT_POPUP"),
        },
    )
    def test_keypress_show_msg_info(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_rendered_message)

        self.full_rendered_message.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )


class TestFullRawMsgView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture, msg_box: MessageBox) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.fetch_raw_message_content = mocker.Mock(
            return_value="This is a `raw` message content :+1:"
        )
        mocker.patch(MODULE + ".MessageBox", return_value=msg_box)
        # NOTE: Given that the FullRawMsgView just uses the message ID from
        # the message data currently, message_fixture is not used to avoid
        # adding extra test runs unnecessarily.
        self.message = Message(id=1)
        self.full_raw_message = FullRawMsgView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Full Raw Message",
        )

    def test_init(self, msg_box: MessageBox) -> None:
        assert self.full_raw_message.title == "Full Raw Message"
        assert self.full_raw_message.controller == self.controller
        assert self.full_raw_message.message == self.message
        assert self.full_raw_message.topic_links == OrderedDict()
        assert self.full_raw_message.message_links == OrderedDict()
        assert self.full_raw_message.time_mentions == list()
        assert self.full_raw_message.header.widget_list == msg_box.header
        assert self.full_raw_message.footer.widget_list == msg_box.footer

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_raw_message)

        self.full_raw_message.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_raw_message)
        key = "a"

        self.full_raw_message.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key",
        {
            *keys_for_command("FULL_RAW_MESSAGE"),
            *keys_for_command("EXIT_POPUP"),
        },
    )
    def test_keypress_show_msg_info(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.full_raw_message)

        self.full_raw_message.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )


class TestEditHistoryView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.fetch_message_history = mocker.Mock(return_value=[])
        self.controller.model.formatted_local_time.return_value = "Tue Mar 13 10:55:22"
        mocker.patch(LISTWALKER, return_value=[])
        # NOTE: Given that the EditHistoryView just uses the message ID from
        # the message data currently, message_fixture is not used to avoid
        # adding extra test runs unnecessarily.
        self.message = Message(id=1)
        self.edit_history_view = EditHistoryView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Edit History",
        )

    def test_init(self) -> None:
        assert self.edit_history_view.controller == self.controller
        assert self.edit_history_view.message == self.message
        assert self.edit_history_view.topic_links == OrderedDict()
        assert self.edit_history_view.message_links == OrderedDict()
        assert self.edit_history_view.time_mentions == list()
        self.controller.model.fetch_message_history.assert_called_once_with(
            message_id=self.message["id"],
        )

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.edit_history_view)
        key = "a"

        self.edit_history_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EDIT_HISTORY"), *keys_for_command("EXIT_POPUP")}
    )
    def test_keypress_show_msg_info(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    @pytest.mark.parametrize(
        "snapshot",
        [
            {
                "content": "Howdy!",
                "timestamp": 1530129134,
                "topic": "party at my house",
                # ...
            }
        ],
    )
    @pytest.mark.parametrize(
        "user_id, user_name_from_id_called",
        [
            (1001, True),
            (None, False),
        ],
        ids=[
            "with_user_id",
            "without_user_id",
        ],
    )
    def test__make_edit_block(
        self,
        mocker: MockerFixture,
        snapshot: Dict[str, Any],
        user_id: Optional[int],
        user_name_from_id_called: bool,
        tag: EditHistoryTag = "(Current Version)",
    ) -> None:
        self._get_author_prefix = mocker.patch(
            MODULE + ".EditHistoryView._get_author_prefix",
        )
        snapshot = dict(**snapshot, user_id=user_id) if user_id else snapshot

        contents = self.edit_history_view._make_edit_block(snapshot, tag)

        assert isinstance(contents[0], Columns)  # Header.
        assert isinstance(contents[0][0], Text)  # Header: Topic.
        assert isinstance(contents[0][1], Text)  # Header: Tag.
        assert isinstance(contents[1], Columns)  # Subheader.
        assert isinstance(contents[1][0], Text)  # Subheader: Author.
        assert isinstance(contents[1][1], Text)  # Subheader: Timestamp.
        assert isinstance(contents[2], Text)  # Content.
        assert contents[0][1].text == tag
        assert (
            self.controller.model.user_name_from_id.called == user_name_from_id_called
        )

    @pytest.mark.parametrize(
        "snapshot",
        [
            {
                "content": "Howdy!",
                "timestamp": 1530129134,
                "topic": "party at my house",
                # ...
            }
        ],
    )
    @pytest.mark.parametrize(
        "to_vary_in_snapshot, tag, expected_author_prefix",
        [
            (
                {},
                "(Original Version)",
                "Posted",
            ),
            (
                {
                    "prev_content": "Hi!",
                    "prev_topic": "no party at my house",
                },
                "",
                "Content & Topic edited",
            ),
            (
                {
                    "prev_content": "Hi!",
                },
                "",
                "Content edited",
            ),
            (
                {
                    "prev_topic": "no party at my house",
                },
                "",
                "Topic edited",
            ),
            (
                {
                    "prev_content": "Howdy!",
                    "prev_topic": "party at my house",
                },
                "",
                "Edited but no changes made",
            ),
            (
                {
                    "prev_content": "Hi!",
                    "prev_topic": "party at my house",
                },
                "",
                "Content edited",
            ),
            (
                {
                    "prev_content": "Howdy!",
                    "prev_topic": "no party at my house",
                },
                "",
                "Topic edited",
            ),
        ],
        ids=[
            "posted",
            "content_&_topic_edited",
            "content_edited",
            "topic_edited",
            "false_alarm_content_&_topic",
            "content_edited_with_false_alarm_topic",
            "topic_edited_with_false_alarm_content",
        ],
    )
    def test__get_author_prefix(
        self,
        snapshot: Dict[str, Any],
        to_vary_in_snapshot: Dict[str, Any],
        tag: EditHistoryTag,
        expected_author_prefix: str,
    ) -> None:
        snapshot = dict(**snapshot, **to_vary_in_snapshot)

        return_value = EditHistoryView._get_author_prefix(snapshot, tag)

        assert return_value == expected_author_prefix


class TestEditModeView:
    @pytest.fixture(params=EDIT_MODE_CAPTIONS.keys())
    def edit_mode_view(self, mocker: MockerFixture, request: Any) -> EditModeView:
        button_launch_mode = request.param
        button = mocker.Mock(mode=button_launch_mode)

        controller = mocker.Mock()
        controller.maximum_popup_dimensions.return_value = (64, 64)

        return EditModeView(controller, button)

    def test_init(self, edit_mode_view: EditModeView) -> None:
        pass  # Just test init succeeds

    @pytest.mark.parametrize(
        "index_in_widgets, mode",
        [
            (0, "change_one"),
            (1, "change_later"),
            (2, "change_all"),
        ],
    )
    @pytest.mark.parametrize("key", keys_for_command("ACTIVATE_BUTTON"))
    def test_select_edit_mode(
        self,
        edit_mode_view: EditModeView,
        widget_size: Callable[[Widget], urwid_Size],
        index_in_widgets: int,
        mode: str,
        key: str,
    ) -> None:
        mode_button = edit_mode_view.edit_mode_button
        if mode_button.mode == mode:
            pytest.skip("button already selected")

        radio_button = edit_mode_view.widgets[index_in_widgets]
        size = widget_size(radio_button)

        radio_button.keypress(size, key)

        mode_button.set_selected_mode.assert_called_once_with(mode)


class TestMarkdownHelpView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.server_url = "https://chat.zulip.org/"

        self.markdown_help_view = MarkdownHelpView(
            self.controller,
            "Markdown Help Menu",
        )

    def test_keypress_any_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.markdown_help_view)

        self.markdown_help_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("MARKDOWN_HELP")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.markdown_help_view)

        self.markdown_help_view.keypress(size, key)

        assert self.controller.exit_popup.called


class TestHelpView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(LISTWALKER, return_value=[])
        self.help_view = HelpView(self.controller, "Help Menu")

    def test_keypress_any_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("HELP")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert self.controller.exit_popup.called


class TestMsgInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(
        self, mocker: MockerFixture, message_fixture: Message
    ) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(LISTWALKER, return_value=[])
        # The subsequent patches (index and initial_data) set
        # show_edit_history_label to False for this autoused fixture.
        self.controller.model.index = {"edited_messages": set()}
        self.controller.model.initial_data = {
            "realm_allow_edit_history": False,
        }
        self.controller.model.formatted_local_time.side_effect = [
            "Tue Mar 13 10:55:22",
            "Tue Mar 13 10:55:37",
        ]
        self.msg_info_view = MsgInfoView(
            self.controller,
            message_fixture,
            "Message Information",
            OrderedDict(),
            OrderedDict(),
            list(),
        )

    def test_init(self, message_fixture: Message) -> None:
        assert self.msg_info_view.msg == message_fixture
        assert self.msg_info_view.topic_links == OrderedDict()
        assert self.msg_info_view.message_links == OrderedDict()
        assert self.msg_info_view.time_mentions == list()

    def test_pop_up_info_order(self, message_fixture: Message) -> None:
        topic_links = OrderedDict([("https://bar.com", ("topic", 1, True))])
        message_links = OrderedDict([("image.jpg", ("image", 1, True))])
        msg_info_view = MsgInfoView(
            self.controller,
            message_fixture,
            title="Message Information",
            topic_links=topic_links,
            message_links=message_links,
            time_mentions=list(),
        )
        msg_links = msg_info_view.button_widgets
        assert msg_links == [message_links, topic_links]

    def test_keypress_any_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.msg_info_view)
        self.msg_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("EDIT_HISTORY"))
    @pytest.mark.parametrize("realm_allow_edit_history", [True, False])
    @pytest.mark.parametrize(
        "edited_message_id",
        [
            537286,
            537287,
            537288,
        ],
        ids=[
            "stream_message_id",
            "pm_message_id",
            "group_pm_message_id",
        ],
    )
    def test_keypress_edit_history(
        self,
        message_fixture: Message,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
        realm_allow_edit_history: bool,
        edited_message_id: int,
    ) -> None:
        self.controller.model.index = {
            "edited_messages": {edited_message_id},
        }
        self.controller.model.initial_data = {
            "realm_allow_edit_history": realm_allow_edit_history,
        }
        msg_info_view = MsgInfoView(
            self.controller,
            message_fixture,
            title="Message Information",
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )
        size = widget_size(msg_info_view)

        msg_info_view.keypress(size, key)

        if msg_info_view.show_edit_history_label:
            self.controller.show_edit_history.assert_called_once_with(
                message=message_fixture,
                topic_links=OrderedDict(),
                message_links=OrderedDict(),
                time_mentions=list(),
            )
        else:
            self.controller.show_edit_history.assert_not_called()

    @pytest.mark.parametrize("key", keys_for_command("FULL_RENDERED_MESSAGE"))
    def test_keypress_full_rendered_message(
        self,
        message_fixture: Message,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        msg_info_view = MsgInfoView(
            self.controller,
            message_fixture,
            title="Message Information",
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )
        size = widget_size(msg_info_view)

        msg_info_view.keypress(size, key)

        self.controller.show_full_rendered_message.assert_called_once_with(
            message=message_fixture,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    @pytest.mark.parametrize("key", keys_for_command("FULL_RAW_MESSAGE"))
    def test_keypress_full_raw_message(
        self,
        message_fixture: Message,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        msg_info_view = MsgInfoView(
            self.controller,
            message_fixture,
            title="Message Information",
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )
        size = widget_size(msg_info_view)

        msg_info_view.keypress(size, key)

        self.controller.show_full_raw_message.assert_called_once_with(
            message=message_fixture,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("MSG_INFO")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.msg_info_view)
        self.msg_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("VIEW_IN_BROWSER"))
    def test_keypress_view_in_browser(
        self,
        mocker: MockerFixture,
        widget_size: Callable[[Widget], urwid_Size],
        key: str,
    ) -> None:
        size = widget_size(self.msg_info_view)
        self.msg_info_view.server_url = "https://chat.zulip.org/"
        mocker.patch(MODULE + ".near_message_url")

        self.msg_info_view.keypress(size, key)

        assert self.controller.open_in_browser.called

    def test_height_noreactions(self) -> None:
        expected_height = 8
        # 6 = 1 (date & time) +1 (sender's name) +1 (sender's email)
        # +1 (display group header)
        # +1 (whitespace column)
        # +1 (view message in browser)
        # +1 (full rendered message)
        # +1 (full raw message)
        assert self.msg_info_view.height == expected_height

    # FIXME This is the same parametrize as MessageBox:test_reactions_view
    @pytest.mark.parametrize(
        "to_vary_in_each_message",
        [
            Message(
                reactions=[
                    {
                        "emoji_name": "thumbs_up",
                        "emoji_code": "1f44d",
                        "user": {
                            "email": "iago@zulip.com",
                            "full_name": "Iago",
                            "id": 5,
                        },
                        "reaction_type": "unicode_emoji",
                    },
                    {
                        "emoji_name": "zulip",
                        "emoji_code": "zulip",
                        "user_id": 5,
                        "reaction_type": "zulip_extra_emoji",
                    },
                    {
                        "emoji_name": "zulip",
                        "emoji_code": "zulip",
                        "user_id": 1,
                        "reaction_type": "zulip_extra_emoji",
                    },
                    {
                        "emoji_name": "heart",
                        "emoji_code": "2764",
                        "user": {
                            "email": "iago@zulip.com",
                            "full_name": "Iago",
                            "id": 5,
                        },
                        "reaction_type": "unicode_emoji",
                    },
                ]
            )
        ],
    )
    def test_height_reactions(
        self,
        message_fixture: Message,
        to_vary_in_each_message: Message,
    ) -> None:
        varied_message = message_fixture
        varied_message.update(to_vary_in_each_message)

        mock_all_users_by_id = {
            1: {"full_name": "aaron"},
            5: {"full_name": "Iago"},
        }

        def mock_get_user_id(reaction: Dict[str, Any]) -> int:
            if "user_id" in reaction:
                return reaction["user_id"]
            return reaction["user"]["id"]

        with patch.object(
            self.controller.model,
            "get_user_id_from_reaction",
            side_effect=mock_get_user_id,
        ), patch.object(
            self.controller.model, "_all_users_by_id", mock_all_users_by_id
        ):
            self.msg_info_view = MsgInfoView(
                self.controller,
                varied_message,
                "Message Information",
                OrderedDict(),
                OrderedDict(),
                list(),
            )

            # 12 = 7 labels + 2 blank lines + 1 'Reactions' (category)
            # + 4 reactions (excluding 'Message Links').
            expected_height = 14
            assert self.msg_info_view.height == expected_height

    @pytest.mark.parametrize(
        [
            "initial_link",
            "expected_text",
            "expected_attr_map",
            "expected_focus_map",
            "expected_link_width",
        ],
        [
            (
                OrderedDict([("https://bar.com", ("Foo", 1, True))]),
                "1: Foo\nhttps://bar.com",
                {None: "popup_contrast"},
                {None: "selected"},
                15,
            ),
            (
                OrderedDict([("https://foo.com", ("", 1, True))]),
                "1: https://foo.com",
                {None: "popup_contrast"},
                {None: "selected"},
                18,
            ),
        ],
        ids=[
            "link_with_link_text",
            "link_without_link_text",
        ],
    )
    def test_create_link_buttons(
        self,
        initial_link: "OrderedDict[str, Tuple[str, int, bool]]",
        expected_text: str,
        expected_attr_map: Dict[None, str],
        expected_focus_map: Dict[None, str],
        expected_link_width: int,
    ) -> None:
        [link_w], link_width = self.msg_info_view.create_link_buttons(
            self.controller, initial_link
        )

        assert [link_w.link] == list(initial_link)
        assert link_w._wrapped_widget.original_widget.text == expected_text
        assert link_w._wrapped_widget.focus_map == expected_focus_map
        assert link_w._wrapped_widget.attr_map == expected_attr_map
        assert link_width == expected_link_width


class TestStreamInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(
        self, mocker: MockerFixture, general_stream: Dict[str, Any]
    ) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.is_muted_stream.return_value = False
        self.controller.model.is_pinned_stream.return_value = False
        self.controller.model.formatted_local_time.return_value = ""
        self.controller.model.is_visual_notifications_enabled.return_value = False
        mocker.patch(LISTWALKER, return_value=[])
        self.stream_id = general_stream["stream_id"]
        self.controller.model.server_feature_level = 40
        self.controller.model.cached_retention_text = {self.stream_id: "10"}

        self.controller.model.stream_dict = {self.stream_id: general_stream}
        self.controller.model.stream_access_type.return_value = "public"

        self.stream_info_view = StreamInfoView(self.controller, self.stream_id)

    def test_keypress_any_key(
        self, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        key = "a"
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MEMBERS"))
    def test_keypress_stream_members(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        self.controller.show_stream_members.assert_called_once_with(
            stream_id=self.stream_id,
        )

    @pytest.mark.parametrize(
        [
            "to_vary_in_stream_data",
            "cached_message_retention_text",
            "server_feature_level",
            "expected_height",
        ],
        [
            case(
                {"date_created": None, "is_announcement_only": True},
                "74 [Organization default]",
                0,
                17,
                id="ZFL=0_no_date_created__no_retention_days__admins_only",
            ),
            case(
                {"date_created": None, "is_announcement_only": False},
                "74 [Organization default]",
                0,
                16,
                id="ZFL=0_no_date_created__no_retention_days__anyone_can_type",
            ),
            case(
                {"date_created": None, "stream_post_policy": 1},
                "74 [Organization default]",
                16,
                16,
                id="ZFL<30_no_date_created__ZFL<17_no_retention_days",
            ),
            case(
                {
                    "date_created": None,
                    "message_retention_days": 200,
                    "stream_post_policy": 2,
                },
                "200",
                17,
                17,
                id="ZFL<30_no_date_created__ZFL=17_custom_finite_retention_days",
            ),
            case(
                {
                    "date_created": None,
                    "message_retention_days": None,
                    "stream_post_policy": 3,
                },
                "Indefinite [Organization default]",
                29,
                18,
                id="ZFL<30_no_date_created__ZFL>17_default_indefinite_retention_days",
            ),
            case(
                {
                    "date_created": 1472091253,
                    "message_retention_days": 31,
                    "stream_post_policy": 4,
                },
                "31",
                30,
                18,
                id="ZFL=30_with_date_created__ZFL>17_custom_finite_retention_days",
            ),
            case(
                {
                    "date_created": 1472047124,
                    "message_retention_days": None,
                    "stream_post_policy": 2,
                },
                "72 [Organization default]",
                40,
                18,
                id="ZFL>30_with_date_created__ZFL>17_default_finite_retention_days",
            ),
            case(
                {
                    "date_created": 1472046489,
                    "stream_weekly_traffic": None,
                    "message_retention_days": 60,
                    "stream_post_policy": 1,
                },
                "60",
                50,
                17,
                id="ZFL>30_new_stream_with_date_created__ZFL>17_finite_retention_days",
            ),
        ],
    )
    def test_popup_height(
        self,
        general_stream: Dict[str, Any],
        to_vary_in_stream_data: Dict[str, Optional[int]],
        cached_message_retention_text: str,
        server_feature_level: int,
        expected_height: int,
    ) -> None:
        model = self.controller.model
        stream_id = general_stream["stream_id"]
        model.stream_dict = {stream_id: general_stream}
        model.stream_dict[stream_id].update(to_vary_in_stream_data)
        model.cached_retention_text = {stream_id: cached_message_retention_text}
        model.server_feature_level = server_feature_level

        stream_info_view = StreamInfoView(self.controller, stream_id)

        # height = 1(description) + 2(blank lines) + 2(category)
        # + 3(checkboxes) + [2-5](fields, depending upon server_feature_level)
        assert stream_info_view.height == expected_height

    def test_stream_info_content__sections(self) -> None:
        assert len(self.stream_info_view._stream_info_content) == 2

        stream_details, stream_settings = self.stream_info_view._stream_info_content
        assert stream_details[0] == "Stream Details"
        assert stream_settings[0] == "Stream settings"

    @pytest.mark.parametrize(
        "stream_email_present, expected_copy_text",
        [
            (False, "< Stream email is unavailable >"),
            (True, "Press 'c' to copy Stream email address"),
        ],
    )
    def test_stream_info_content__email_copy_text(
        self,
        general_stream: Dict[str, Any],
        stream_email_present: bool,
        expected_copy_text: str,
    ) -> None:
        if not stream_email_present:
            del general_stream["email_address"]
            self.controller.model.get_stream_email_address.return_value = None

        model = self.controller.model
        stream_id = general_stream["stream_id"]
        model.stream_dict = {stream_id: general_stream}

        # Custom, to enable variation of stream data before creation
        stream_info_view = StreamInfoView(self.controller, stream_id)

        stream_details, _ = stream_info_view._stream_info_content
        stream_details_data = stream_details[1]

        assert ("Stream email", expected_copy_text) in stream_details_data

    @pytest.mark.parametrize("normalized_email_address", ("user@example.com", None))
    @pytest.mark.parametrize("key", keys_for_command("COPY_STREAM_EMAIL"))
    def test_keypress_copy_stream_email(
        self,
        key: str,
        normalized_email_address: Optional[str],
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(self.stream_info_view)
        # This patches inside the object, which is fragile but tests the logic
        # Note that the assert uses the same variable
        self.stream_info_view._stream_email = normalized_email_address

        self.stream_info_view.keypress(size, key)

        if normalized_email_address is not None:
            self.controller.copy_to_clipboard.assert_called_once_with(
                self.stream_info_view._stream_email, "Stream email"
            )
        else:
            self.controller.copy_to_clipboard.assert_not_called()

    @pytest.mark.parametrize(
        "rendered_description, expected_markup",
        [
            (
                "<p>Simple</p>",
                (None, ["", "", "Simple"]),
            ),
            (
                '<p>A city in Italy <a href="http://genericlink.com">ABC</a>'
                "<strong>Bold</strong>",
                (
                    None,
                    [
                        "",
                        "",
                        "A city in Italy ",
                        ("msg_link", "ABC"),
                        " ",
                        ("msg_link_index", "[1]"),
                        ("msg_bold", "Bold"),
                    ],
                ),
            ),
        ],
    )
    def test_markup_description(
        self, rendered_description: str, expected_markup: Tuple[None, Any]
    ) -> None:
        model = self.controller.model
        model.stream_dict[self.stream_id]["rendered_description"] = rendered_description

        stream_info_view = StreamInfoView(self.controller, self.stream_id)

        assert stream_info_view.markup_desc == expected_markup

    @pytest.mark.parametrize(
        "message_links, expected_text, expected_attrib, expected_footlinks_width",
        [
            (
                OrderedDict(
                    [
                        ("https://example.com", ("Example", 1, True)),
                        ("https://generic.com", ("Generic", 2, True)),
                    ]
                ),
                "1: https://example.com\n2: https://generic.com",
                [
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 19),
                    (None, 1),
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 19),
                ],
                22,
            ),
        ],
    )
    def test_footlinks(
        self,
        message_links: "OrderedDict[str, Tuple[str, int, bool]]",
        expected_text: str,
        expected_attrib: List[Tuple[Optional[str], int]],
        expected_footlinks_width: int,
    ) -> None:
        footlinks, footlinks_width = MessageBox.footlinks_view(
            message_links,
            maximum_footlinks=10,
            padded=False,
            wrap="space",
        )

        assert footlinks.text == expected_text
        assert footlinks.attrib == expected_attrib
        assert footlinks_width == expected_footlinks_width

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("STREAM_INFO")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", (*keys_for_command("ACTIVATE_BUTTON"), " "))
    def test_checkbox_toggle_mute_stream(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        mute_checkbox = self.stream_info_view.widgets[-3]
        toggle_mute_status = self.controller.model.toggle_stream_muted_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(mute_checkbox)

        mute_checkbox.keypress(size, key)

        toggle_mute_status.assert_called_once_with(stream_id)

    @pytest.mark.parametrize("key", (*keys_for_command("ACTIVATE_BUTTON"), " "))
    def test_checkbox_toggle_pin_stream(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        pin_checkbox = self.stream_info_view.widgets[-2]
        toggle_pin_status = self.controller.model.toggle_stream_pinned_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(pin_checkbox)

        pin_checkbox.keypress(size, key)

        toggle_pin_status.assert_called_once_with(stream_id)

    @pytest.mark.parametrize("key", (*keys_for_command("ACTIVATE_BUTTON"), " "))
    def test_checkbox_toggle_visual_notification(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        visual_notify_checkbox = self.stream_info_view.widgets[-1]
        toggle_visual_notify_status = (
            self.controller.model.toggle_stream_visual_notifications
        )
        stream_id = self.stream_info_view.stream_id
        size = widget_size(visual_notify_checkbox)

        visual_notify_checkbox.keypress(size, key)

        toggle_visual_notify_status.assert_called_once_with(stream_id)


class TestStreamMembersView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.get_other_subscribers_in_stream.return_value = []
        self.controller.model.user_full_name = ""
        mocker.patch(LISTWALKER, return_value=[])
        stream_id = 10
        self.stream_members_view = StreamMembersView(self.controller, stream_id)

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("STREAM_MEMBERS")}
    )
    def test_keypress_exit_popup(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        stream_id = self.stream_members_view.stream_id
        size = widget_size(self.stream_members_view)
        self.stream_members_view.keypress(size, key)
        self.controller.show_stream_info.assert_called_once_with(
            stream_id=stream_id,
        )


class TestEmojiPickerView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(
        self, mocker: MockerFixture, message_fixture: Message
    ) -> None:
        self.controller = mocker.Mock()
        self.view = self.controller.view
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(MODULE + ".urwid.SimpleFocusListWalker", return_value=[])
        self.emoji_picker_view = EmojiPickerView(
            self.controller,
            "ADD EMOJI",
            [("zulip", "4", [])],
            message_fixture,
            self.view,
        )

    @pytest.mark.parametrize(
        "emoji_units",
        [
            (
                ("action", "1f3ac", []),
                ("alien", "1f47d", ["ufo"]),
                ("angel", "1f47c", []),
                ("anger", "1f4a2", ["bam", "pow"]),
                ("angry", "1f620", []),
                ("eight", "0038-20e3", []),
                ("email", "2709", ["envelope", "mail"]),
                ("eye", "1f441", []),
                ("ball", "26f9", ["sports"]),
                ("cat", "1f408", ["meow"]),
                ("heart", "2764", ["love", "love_you"]),
                ("lightning", "1f329", ["lightning_storm"]),
                ("smile", "1f642", []),
                ("smiley", "1f603", []),
                ("smirk", "1f60f", ["smug"]),
                ("smoking", "1f6ac", []),
            )
        ],
    )
    @pytest.mark.parametrize(
        ["search_string", "assert_list"],
        [
            ("e", ["eight", "email", "eye"]),
            ("sm", ["smile", "smiley", "smirk", "smoking"]),
            ("ang", ["angel", "anger", "angry"]),
            ("abc", []),
            ("q", []),
        ],
    )
    def test_update_emoji_list(
        self,
        emoji_units: List[Tuple[str, str, List[str]]],
        search_string: str,
        assert_list: List[str],
    ) -> None:
        self.emoji_picker_view.emoji_buttons = (
            self.emoji_picker_view.generate_emoji_buttons(emoji_units)
        )

        self.emoji_picker_view.update_emoji_list("SEARCH_EMOJIS", search_string)
        self.emojis_display = self.emoji_picker_view.emojis_display
        emojis_display_name = [emoji.emoji_name for emoji in self.emojis_display]

        assert emojis_display_name == assert_list
        assert self.emoji_picker_view.get_focus() == "header"

    @pytest.mark.parametrize(
        "event, button, keypress",
        [
            ("mouse press", 4, "up"),
            ("mouse press", 5, "down"),
        ],
    )
    def test_mouse_event(
        self,
        mocker: MockerFixture,
        widget_size: Callable[[Widget], urwid_Size],
        event: str,
        button: int,
        keypress: str,
    ) -> None:
        emoji_picker = self.emoji_picker_view
        mocked_emoji_picker_keypress = mocker.patch.object(emoji_picker, "keypress")
        size = widget_size(emoji_picker)
        emoji_picker.mouse_event(size, event, button, 0, 0, mocker.Mock())
        mocked_emoji_picker_keypress.assert_called_once_with(size, keypress)

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_EMOJIS"))
    def test_keypress_search_emoji(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.emoji_picker_view)
        self.controller.is_in_editor_mode.return_value = False

        self.emoji_picker_view.keypress(size, key)

        assert self.emoji_picker_view.get_focus() == "header"

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EXIT_POPUP"), *keys_for_command("ADD_REACTION")}
    )
    def test_keypress_exit_called(
        self, key: str, widget_size: Callable[[Widget], urwid_Size]
    ) -> None:
        size = widget_size(self.emoji_picker_view)

        self.emoji_picker_view.keypress(size, key)

        assert self.controller.exit_popup.called
