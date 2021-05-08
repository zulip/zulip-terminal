from collections import OrderedDict

import pytest
from urwid import Columns, Pile, Text

from zulipterminal.config.keys import is_command_key, keys_for_command
from zulipterminal.config.ui_mappings import EDIT_MODE_CAPTIONS
from zulipterminal.ui_tools.boxes import MessageBox
from zulipterminal.ui_tools.views import (
    AboutView,
    EditHistoryView,
    EditModeView,
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
from zulipterminal.version import MINIMUM_SUPPORTED_SERVER_VERSION, ZT_VERSION


MODULE = "zulipterminal.ui_tools.views"
LISTWALKER = MODULE + ".urwid.SimpleFocusListWalker"

# Test classes are grouped/ordered below as:
#  * an independent popup class
#  * the base general popup class
#  * classes derived from the base popup class, sorted alphabetically


class TestPopUpConfirmationView:
    @pytest.fixture
    def popup_view(self, mocker, stream_button):
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

    def test_init(self, popup_view):
        assert popup_view.controller == self.controller
        assert popup_view.success_callback == self.callback
        self.divider.assert_called_once_with()
        self.list_walker.assert_called_once_with(
            [self.text, self.divider(), self.wrapper_w()]
        )

    def test_exit_popup_yes(self, mocker, popup_view):
        popup_view.exit_popup_yes(mocker.Mock())
        self.callback.assert_called_once_with()
        assert self.controller.exit_popup.called

    def test_exit_popup_no(self, mocker, popup_view):
        popup_view.exit_popup_no(mocker.Mock())
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test_exit_popup_GO_BACK(self, mocker, popup_view, key, widget_size):
        size = widget_size(popup_view)
        popup_view.keypress(size, key)
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called


class TestPopUpView:
    @pytest.fixture(autouse=True)
    def pop_up_view(self, mocker):
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

    def test_init(self, mocker):
        assert self.pop_up_view.controller == self.controller
        assert self.pop_up_view.command == self.command
        assert self.pop_up_view.title == self.title
        assert self.pop_up_view.width == self.width
        self.list_walker.assert_called_once_with(self.body)
        self.super_init.assert_called_once_with(
            self.pop_up_view.body, header=mocker.ANY, footer=mocker.ANY
        )

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, key, widget_size):
        size = widget_size(self.pop_up_view)
        self.pop_up_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_command_key(self, mocker, widget_size):
        size = widget_size(self.pop_up_view)
        mocker.patch(
            MODULE + ".is_command_key",
            side_effect=(lambda command, key: command == self.command),
        )
        self.pop_up_view.keypress(size, "cmd_key")
        assert self.controller.exit_popup.called

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.pop_up_view)
        # Patch `is_command_key` to not raise an 'Invalid Command' exception
        # when its parameters are (self.command, key) as there is no
        # self.command='COMMAND' command in keys.py.
        mocker.patch(
            MODULE + ".is_command_key",
            side_effect=(
                lambda command, key: False
                if command == self.command
                else is_command_key(command, key)
            ),
        )
        self.pop_up_view.keypress(size, key)
        self.super_keypress.assert_called_once_with(size, expected_key)


class TestAboutView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(LISTWALKER, return_value=[])
        server_version, server_feature_level = MINIMUM_SUPPORTED_SERVER_VERSION

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
        )

    @pytest.mark.parametrize(
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("ABOUT")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        key = "a"
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.about_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.about_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)

    def test_feature_level_content(self, mocker, zulip_version):
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
        )

        assert len(about_view.feature_level_content) == (
            1 if server_feature_level else 0
        )


class TestUserInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, tidied_user_info_response):
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

        self.user_info_view = UserInfoView(
            self.controller, 10000, "User Info (up/down scrolls)"
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
        self, mocker, to_vary_in_each_user, expected_key, expected_value
    ):
        data = dict(self.user_data, **to_vary_in_each_user)

        mocker.patch.object(self.controller.model, "get_user_info", return_value=data)

        display_data = self.user_info_view._fetch_user_data(self.controller, 1)

        assert display_data.get(expected_key, None) == expected_value

    def test__fetch_user_data_USER_NOT_FOUND(self, mocker):
        mocker.patch.object(self.controller.model, "get_user_info", return_value=dict())

        display_data = self.user_info_view._fetch_user_data(self.controller, 1)

        assert display_data["Name"] == "(Unavailable)"
        assert display_data["Error"] == "User data not found"

    @pytest.mark.parametrize(
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("USER_INFO")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.user_info_view)
        self.user_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        key = "a"
        size = widget_size(self.user_info_view)
        self.user_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.user_info_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.user_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestFullRenderedMsgView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, msg_box, initial_index):
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(MODULE + ".MessageBox", return_value=msg_box)
        # NOTE: Given that the FullRenderedMsgView just uses the message ID from
        # the message data currently, message_fixture is not used to avoid
        # adding extra test runs unnecessarily.
        self.message = {"id": 1}
        self.full_rendered_message = FullRenderedMsgView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Full Rendered Message",
        )

    def test_init(self, mocker, msg_box):
        assert self.full_rendered_message.title == "Full Rendered Message"
        assert self.full_rendered_message.controller == self.controller
        assert self.full_rendered_message.message == self.message
        assert self.full_rendered_message.topic_links == OrderedDict()
        assert self.full_rendered_message.message_links == OrderedDict()
        assert self.full_rendered_message.time_mentions == list()
        assert self.full_rendered_message.header.widget_list == msg_box.header
        assert self.full_rendered_message.footer.widget_list == msg_box.footer

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.full_rendered_message)

        self.full_rendered_message.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        size = widget_size(self.full_rendered_message)
        key = "a"

        self.full_rendered_message.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key",
        {
            *keys_for_command("FULL_RENDERED_MESSAGE"),
            *keys_for_command("GO_BACK"),
        },
    )
    def test_keypress_show_msg_info(self, key, widget_size):
        size = widget_size(self.full_rendered_message)

        self.full_rendered_message.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        size = widget_size(self.full_rendered_message)
        key, expected_key = navigation_key_expected_key_pair
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")

        self.full_rendered_message.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)


class TestFullRawMsgView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, msg_box, initial_index):
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
        self.message = {"id": 1}
        self.full_raw_message = FullRawMsgView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Full Raw Message",
        )

    def test_init(self, mocker, msg_box):
        assert self.full_raw_message.title == "Full Raw Message"
        assert self.full_raw_message.controller == self.controller
        assert self.full_raw_message.message == self.message
        assert self.full_raw_message.topic_links == OrderedDict()
        assert self.full_raw_message.message_links == OrderedDict()
        assert self.full_raw_message.time_mentions == list()
        assert self.full_raw_message.header.widget_list == msg_box.header
        assert self.full_raw_message.footer.widget_list == msg_box.footer

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.full_raw_message)

        self.full_raw_message.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        size = widget_size(self.full_raw_message)
        key = "a"

        self.full_raw_message.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key",
        {
            *keys_for_command("FULL_RAW_MESSAGE"),
            *keys_for_command("GO_BACK"),
        },
    )
    def test_keypress_show_msg_info(self, key, widget_size):
        size = widget_size(self.full_raw_message)

        self.full_raw_message.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        size = widget_size(self.full_raw_message)
        key, expected_key = navigation_key_expected_key_pair
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")

        self.full_raw_message.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)


class TestEditHistoryView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
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
        self.message = {"id": 1}
        self.edit_history_view = EditHistoryView(
            controller=self.controller,
            message=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
            title="Edit History",
        )

    def test_init(self):
        assert self.edit_history_view.controller == self.controller
        assert self.edit_history_view.message == self.message
        assert self.edit_history_view.topic_links == OrderedDict()
        assert self.edit_history_view.message_links == OrderedDict()
        assert self.edit_history_view.time_mentions == list()
        self.controller.model.fetch_message_history.assert_called_once_with(
            message_id=self.message["id"],
        )

    @pytest.mark.parametrize("key", keys_for_command("MSG_INFO"))
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        size = widget_size(self.edit_history_view)
        key = "a"

        self.edit_history_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("EDIT_HISTORY"), *keys_for_command("GO_BACK")}
    )
    def test_keypress_show_msg_info(self, key, widget_size):
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            topic_links=OrderedDict(),
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        size = widget_size(self.edit_history_view)
        key, expected_key = navigation_key_expected_key_pair
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")

        self.edit_history_view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)

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
        mocker,
        snapshot,
        user_id,
        user_name_from_id_called,
        tag="(Current Version)",
    ):
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
        self, snapshot, to_vary_in_snapshot, tag, expected_author_prefix
    ):
        snapshot = dict(**snapshot, **to_vary_in_snapshot)

        return_value = EditHistoryView._get_author_prefix(snapshot, tag)

        assert return_value == expected_author_prefix


class TestEditModeView:
    @pytest.fixture(params=EDIT_MODE_CAPTIONS.keys())
    def edit_mode_view(self, mocker, request):
        button_launch_mode = request.param
        button = mocker.Mock(mode=button_launch_mode)

        controller = mocker.Mock()
        controller.maximum_popup_dimensions.return_value = (64, 64)

        return EditModeView(controller, button)

    def test_init(self, edit_mode_view):
        pass  # Just test init succeeds

    @pytest.mark.parametrize(
        "index_in_widgets, mode",
        [
            (0, "change_one"),
            (1, "change_later"),
            (2, "change_all"),
        ],
    )
    @pytest.mark.parametrize("key", keys_for_command("ENTER"))
    def test_select_edit_mode(
        self, mocker, edit_mode_view, widget_size, index_in_widgets, mode, key
    ):
        mode_button = edit_mode_view.edit_mode_button
        if mode_button.mode == mode:
            pytest.skip("button already selected")

        radio_button = edit_mode_view.widgets[index_in_widgets]
        size = widget_size(radio_button)

        radio_button.keypress(size, key)

        mode_button.set_selected_mode.assert_called_once_with(mode)


class TestMarkdownHelpView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.server_url = "https://chat.zulip.org/"

        self.markdown_help_view = MarkdownHelpView(
            self.controller,
            "Markdown Help Menu",
        )

    def test_keypress_any_key(self, widget_size):
        key = "a"
        size = widget_size(self.markdown_help_view)

        self.markdown_help_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("MARKDOWN_HELP")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.markdown_help_view)

        self.markdown_help_view.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_body_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.markdown_help_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")

        self.markdown_help_view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)


class TestHelpView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        mocker.patch(LISTWALKER, return_value=[])
        self.help_view = HelpView(self.controller, "Help Menu")

    def test_keypress_any_key(self, widget_size):
        key = "a"
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize(
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("HELP")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.help_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.help_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestMsgInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch, message_fixture):
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

    def test_init(self, message_fixture):
        assert self.msg_info_view.msg == message_fixture
        assert self.msg_info_view.topic_links == OrderedDict()
        assert self.msg_info_view.message_links == OrderedDict()
        assert self.msg_info_view.time_mentions == list()

    def test_keypress_any_key(self, widget_size):
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
        message_fixture,
        key,
        widget_size,
        realm_allow_edit_history,
        edited_message_id,
    ):
        self.controller.model.index = {
            "edited_messages": set([edited_message_id]),
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
    def test_keypress_full_rendered_message(self, message_fixture, key, widget_size):
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
    def test_keypress_full_raw_message(self, message_fixture, key, widget_size):
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
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("MSG_INFO")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.msg_info_view)
        self.msg_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("VIEW_IN_BROWSER"))
    def test_keypress_view_in_browser(self, mocker, widget_size, message_fixture, key):
        size = widget_size(self.msg_info_view)
        self.msg_info_view.server_url = "https://chat.zulip.org/"
        mocker.patch(MODULE + ".near_message_url")

        self.msg_info_view.keypress(size, key)

        assert self.controller.open_in_browser.called

    def test_height_noreactions(self):
        expected_height = 6
        # 6 = 1 (date & time) +1 (sender's name) +1 (sender's email)
        # +1 (view message in browser)
        # +1 (full rendered message)
        # +1 (full raw message)
        assert self.msg_info_view.height == expected_height

    # FIXME This is the same parametrize as MessageBox:test_reactions_view
    @pytest.mark.parametrize(
        "to_vary_in_each_message",
        [
            {
                "reactions": [
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
                        "user": {
                            "email": "iago@zulip.com",
                            "full_name": "Iago",
                            "id": 5,
                        },
                        "reaction_type": "zulip_extra_emoji",
                    },
                    {
                        "emoji_name": "zulip",
                        "emoji_code": "zulip",
                        "user": {
                            "email": "AARON@zulip.com",
                            "full_name": "aaron",
                            "id": 1,
                        },
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
            }
        ],
    )
    def test_height_reactions(self, message_fixture, to_vary_in_each_message):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        self.msg_info_view = MsgInfoView(
            self.controller,
            varied_message,
            "Message Information",
            OrderedDict(),
            OrderedDict(),
            list(),
        )
        # 12 = 6 labels + 1 blank line + 1 'Reactions' (category)
        # + 4 reactions (excluding 'Message Links').
        expected_height = 12
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
        initial_link,
        expected_text,
        expected_attr_map,
        expected_focus_map,
        expected_link_width,
    ):
        [link_w], link_width = self.msg_info_view.create_link_buttons(
            self.controller, initial_link
        )

        assert [link_w.link] == list(initial_link)
        assert link_w._wrapped_widget.original_widget.text == expected_text
        assert link_w._wrapped_widget.focus_map == expected_focus_map
        assert link_w._wrapped_widget.attr_map == expected_attr_map
        assert link_width == expected_link_width

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.msg_info_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.msg_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestStreamInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch.object(
            self.controller, "maximum_popup_dimensions", return_value=(64, 64)
        )
        self.controller.model.is_muted_stream.return_value = False
        self.controller.model.is_pinned_stream.return_value = False
        self.controller.model.is_visual_notifications_enabled.return_value = False
        mocker.patch(LISTWALKER, return_value=[])
        self.stream_id = 10
        self.controller.model.stream_dict = {
            self.stream_id: {
                "name": "books",
                "invite_only": False,
                "rendered_description": "<p>Hey</p>",
                "subscribers": [],
                "stream_weekly_traffic": 123,
            }
        }
        self.stream_info_view = StreamInfoView(self.controller, self.stream_id)

    def test_keypress_any_key(self, widget_size):
        key = "a"
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MEMBERS"))
    def test_keypress_stream_members(self, mocker, key, widget_size):
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        self.controller.show_stream_members.assert_called_once_with(
            stream_id=self.stream_id,
        )

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
    def test_markup_descrption(
        self, rendered_description, expected_markup, stream_id=10
    ):
        self.controller.model.stream_dict = {
            stream_id: {
                "name": "ZT",
                "invite_only": False,
                "subscribers": [],
                "stream_weekly_traffic": 123,
                "rendered_description": rendered_description,
            }
        }

        stream_info_view = StreamInfoView(self.controller, stream_id)

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
        self, message_links, expected_text, expected_attrib, expected_footlinks_width
    ):
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
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("STREAM_DESC")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.stream_info_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.stream_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)

    @pytest.mark.parametrize("key", (*keys_for_command("ENTER"), " "))
    def test_checkbox_toggle_mute_stream(self, mocker, key, widget_size):
        mute_checkbox = self.stream_info_view.widgets[-3]
        toggle_mute_status = self.controller.model.toggle_stream_muted_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(mute_checkbox)

        mute_checkbox.keypress(size, key)

        toggle_mute_status.assert_called_once_with(stream_id)

    @pytest.mark.parametrize("key", (*keys_for_command("ENTER"), " "))
    def test_checkbox_toggle_pin_stream(self, mocker, key, widget_size):
        pin_checkbox = self.stream_info_view.widgets[-2]
        toggle_pin_status = self.controller.model.toggle_stream_pinned_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(pin_checkbox)

        pin_checkbox.keypress(size, key)

        toggle_pin_status.assert_called_once_with(stream_id)

    @pytest.mark.parametrize("key", (*keys_for_command("ENTER"), " "))
    def test_checkbox_toggle_visual_notification(self, key, widget_size):
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
    def mock_external_classes(self, mocker, monkeypatch):
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
        "key", {*keys_for_command("GO_BACK"), *keys_for_command("STREAM_MEMBERS")}
    )
    def test_keypress_exit_popup(self, key, widget_size):
        stream_id = self.stream_members_view.stream_id
        size = widget_size(self.stream_members_view)
        self.stream_members_view.keypress(size, key)
        self.controller.show_stream_info.assert_called_once_with(
            stream_id=stream_id,
        )

    def test_keypress_navigation(
        self, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.stream_members_view)
        super_keypress = mocker.patch(MODULE + ".urwid.Frame.keypress")
        self.stream_members_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)
