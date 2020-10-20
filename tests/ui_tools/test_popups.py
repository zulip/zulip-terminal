from collections import OrderedDict

import pytest
from urwid import Columns, Text

from zulipterminal.config.keys import keys_for_command
from zulipterminal.ui_tools.views import (
    AboutView, EditHistoryView, EditModeView, HelpView, MsgInfoView,
    StreamInfoView,
)
from zulipterminal.version import MINIMUM_SUPPORTED_SERVER_VERSION, ZT_VERSION


VIEWS = "zulipterminal.ui_tools.views"


class TestAboutView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        mocker.patch(VIEWS + '.urwid.SimpleFocusListWalker', return_value=[])
        server_version, server_feature_level = MINIMUM_SUPPORTED_SERVER_VERSION
        self.about_view = AboutView(self.controller, 'About',
                                    zt_version=ZT_VERSION,
                                    server_version=server_version,
                                    server_feature_level=server_feature_level)

    @pytest.mark.parametrize('key', {*keys_for_command('GO_BACK'),
                                     *keys_for_command('ABOUT')})
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        key = 'a'
        size = widget_size(self.about_view)
        self.about_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    def test_keypress_navigation(self, mocker, widget_size,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.about_view)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.about_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)

    def test_feature_level_content(self, mocker, zulip_version):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        mocker.patch(VIEWS + '.urwid.SimpleFocusListWalker', return_value=[])
        server_version, server_feature_level = zulip_version

        about_view = AboutView(self.controller, 'About', zt_version=ZT_VERSION,
                               server_version=server_version,
                               server_feature_level=server_feature_level)

        assert len(about_view.feature_level_content) == (
            1 if server_feature_level else 0
        )


class TestEditHistoryView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        self.controller.model.fetch_message_history = (
            mocker.Mock(return_value=[])
        )
        mocker.patch(VIEWS + '.urwid.SimpleFocusListWalker', return_value=[])
        # NOTE: Given that the EditHistoryView just uses the message ID from
        # the message data currently, message_fixture is not used to avoid
        # adding extra test runs unnecessarily.
        self.message = {'id': 1}
        self.edit_history_view = EditHistoryView(
            controller=self.controller,
            message=self.message,
            message_links=OrderedDict(),
            time_mentions=list(),
            title='Edit History',
        )

    def test_init(self):
        assert self.edit_history_view.controller == self.controller
        assert self.edit_history_view.message == self.message
        assert self.edit_history_view.message_links == OrderedDict()
        assert self.edit_history_view.time_mentions == list()
        self.controller.model.fetch_message_history.assert_called_once_with(
            message_id=self.message['id'],
        )

    @pytest.mark.parametrize('key', keys_for_command('MSG_INFO'))
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self, widget_size):
        size = widget_size(self.edit_history_view)
        key = 'a'

        self.edit_history_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', {*keys_for_command('EDIT_HISTORY'),
                                     *keys_for_command('GO_BACK')})
    def test_keypress_show_msg_info(self, key, widget_size):
        size = widget_size(self.edit_history_view)

        self.edit_history_view.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    def test_keypress_navigation(self, mocker, widget_size,
                                 navigation_key_expected_key_pair):
        size = widget_size(self.edit_history_view)
        key, expected_key = navigation_key_expected_key_pair
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')

        self.edit_history_view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)

    @pytest.mark.parametrize('snapshot', [{
            'content': 'Howdy!',
            'timestamp': 1530129134,
            'topic': 'party at my house',
            # ...
    }])
    @pytest.mark.parametrize('user_id, user_name_from_id_called', [
            (1001, True),
            (None, False),
        ],
        ids=[
            'with_user_id',
            'without_user_id',
        ]
    )
    def test__make_edit_block(self, mocker, snapshot, user_id,
                              user_name_from_id_called,
                              tag='(Current Version)'):
        self._get_author_prefix = mocker.patch(
            VIEWS + '.EditHistoryView._get_author_prefix',
        )
        snapshot = dict(**snapshot, user_id=user_id) if user_id else snapshot

        contents = self.edit_history_view._make_edit_block(snapshot, tag)

        assert isinstance(contents[0], Columns)  # Header.
        assert isinstance(contents[0][0], Text)  # Header: Topic.
        assert isinstance(contents[0][1], Text)  # Header: Tag.
        assert isinstance(contents[1], Columns)  # Subheader.
        assert isinstance(contents[1][0], Text)  # Subheader: Author.
        assert isinstance(contents[1][1], Text)  # Subheader: Timestamp.
        assert isinstance(contents[2], Text)     # Content.
        assert contents[0][1].text == tag
        assert (self.controller.model.user_name_from_id.called
                == user_name_from_id_called)

    @pytest.mark.parametrize('snapshot', [{
            'content': 'Howdy!',
            'timestamp': 1530129134,
            'topic': 'party at my house',
            # ...
    }])
    @pytest.mark.parametrize(['to_vary_in_snapshot', 'tag',
                              'expected_author_prefix'], [
            (
                {},
                '(Original Version)',
                'Posted',
            ),
            (
                {
                    'prev_content': 'Hi!',
                    'prev_topic': 'no party at my house',
                },
                '',
                'Content & Topic edited',
            ),
            (
                {
                    'prev_content': 'Hi!',
                },
                '',
                'Content edited',
            ),
            (
                {
                    'prev_topic': 'no party at my house',
                },
                '',
                'Topic edited',
            ),
            (
                {
                    'prev_content': 'Howdy!',
                    'prev_topic': 'party at my house',
                },
                '',
                'Edited but no changes made',
            ),
            (
                {
                    'prev_content': 'Hi!',
                    'prev_topic': 'party at my house',
                },
                '',
                'Content edited',
            ),
            (
                {
                    'prev_content': 'Howdy!',
                    'prev_topic': 'no party at my house',
                },
                '',
                'Topic edited',
            ),
        ],
        ids=[
            'posted',
            'content_&_topic_edited',
            'content_edited',
            'topic_edited',
            'false_alarm_content_&_topic',
            'content_edited_with_false_alarm_topic',
            'topic_edited_with_false_alarm_content',
        ]
    )
    def test__get_author_prefix(self, snapshot, to_vary_in_snapshot, tag,
                                expected_author_prefix):
        snapshot = dict(**snapshot, **to_vary_in_snapshot)

        return_value = EditHistoryView._get_author_prefix(snapshot, tag)

        assert return_value == expected_author_prefix


class TestEditModeView:
    @pytest.fixture()
    def edit_mode_view(self, mocker):
        controller = mocker.Mock()
        controller.maximum_popup_dimensions.return_value = (64, 64)
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        button = mocker.Mock()
        return EditModeView(controller, button)

    @pytest.mark.parametrize(['index_in_widgets', 'mode'], [
        (0, 'change_one'),
        (1, 'change_later'),
        (2, 'change_all'),
    ])
    @pytest.mark.parametrize('key', keys_for_command('ENTER'))
    def test_select_edit_mode(self, mocker, edit_mode_view, widget_size,
                              index_in_widgets, mode, key):
        radio_button = edit_mode_view.widgets[index_in_widgets]
        size = widget_size(radio_button)

        radio_button.keypress(size, key)

        mode_button = edit_mode_view.edit_mode_button
        mode_button.set_selected_mode.assert_called_once_with(mode)


class TestHelpView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        self.help_view = HelpView(self.controller, 'Help Menu')

    def test_keypress_any_key(self, widget_size):
        key = "a"
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', {*keys_for_command('GO_BACK'),
                                     *keys_for_command('HELP')})
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.help_view)
        self.help_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_navigation(self, mocker, widget_size,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.help_view)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.help_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestMsgInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch, message_fixture):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        # The subsequent patches (index and initial_data) set
        # show_edit_history_label to False for this autoused fixture.
        self.controller.model.index = {'edited_messages': set()}
        self.controller.model.initial_data = {
            'realm_allow_edit_history': False,
        }
        self.msg_info_view = MsgInfoView(self.controller, message_fixture,
                                         'Message Information', OrderedDict(),
                                         list())

    def test_keypress_any_key(self, widget_size):
        key = "a"
        size = widget_size(self.msg_info_view)
        self.msg_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', keys_for_command('EDIT_HISTORY'))
    @pytest.mark.parametrize('realm_allow_edit_history', [True, False])
    @pytest.mark.parametrize('edited_message_id', [
            537286,
            537287,
            537288,
        ],
        ids=[
            'stream_message_id',
            'pm_message_id',
            'group_pm_message_id',
        ]
    )
    def test_keypress_edit_history(self, message_fixture, key, widget_size,
                                   realm_allow_edit_history,
                                   edited_message_id):
        self.controller.model.index = {
            'edited_messages': set([edited_message_id]),
        }
        self.controller.model.initial_data = {
            'realm_allow_edit_history': realm_allow_edit_history,
        }
        msg_info_view = MsgInfoView(self.controller, message_fixture,
                                    title='Message Information',
                                    message_links=OrderedDict(),
                                    time_mentions=list())
        size = widget_size(msg_info_view)

        msg_info_view.keypress(size, key)

        if msg_info_view.show_edit_history_label:
            self.controller.show_edit_history.assert_called_once_with(
                message=message_fixture,
                message_links=OrderedDict(),
                time_mentions=list(),
            )
        else:
            self.controller.show_edit_history.assert_not_called()

    @pytest.mark.parametrize('key', {*keys_for_command('GO_BACK'),
                                     *keys_for_command('MSG_INFO')})
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.msg_info_view)
        self.msg_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_height_noreactions(self):
        expected_height = 3
        assert self.msg_info_view.height == expected_height

    # FIXME This is the same parametrize as MessageBox:test_reactions_view
    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'reactions': [{
                'emoji_name': 'thumbs_up',
                'emoji_code': '1f44d',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'AARON@zulip.com',
                    'full_name': 'aaron',
                    'id': 1,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'heart',
                'emoji_code': '2764',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }]}
        ])
    def test_height_reactions(self, message_fixture, to_vary_in_each_message):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        self.msg_info_view = MsgInfoView(self.controller, varied_message,
                                         'Message Information', OrderedDict(),
                                         list())
        # 9 = 3 labels + 1 blank line + 1 'Reactions' (category) + 4 reactions.
        expected_height = 9
        assert self.msg_info_view.height == expected_height

    def test_keypress_navigation(self, mocker, widget_size,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.msg_info_view)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.msg_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestStreamInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
        self.controller.model.is_muted_stream.return_value = False
        self.controller.model.is_pinned_stream.return_value = False
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        stream_id = 10
        self.controller.model.stream_dict = {stream_id: {'name': 'books',
                                                         'description': 'hey'}}
        self.stream_info_view = StreamInfoView(self.controller, stream_id)

    @pytest.mark.parametrize('key', {*keys_for_command('GO_BACK'),
                                     *keys_for_command('STREAM_DESC')})
    def test_keypress_exit_popup(self, key, widget_size):
        size = widget_size(self.stream_info_view)
        self.stream_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_navigation(self, mocker, widget_size,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = widget_size(self.stream_info_view)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.stream_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)

    @pytest.mark.parametrize('key', (*keys_for_command('ENTER'), ' '))
    def test_checkbox_toggle_mute_stream(self, mocker, key, widget_size):
        mute_checkbox = self.stream_info_view.widgets[3]
        toggle_mute_status = self.controller.model.toggle_stream_muted_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(mute_checkbox)

        mute_checkbox.keypress(size, key)

        toggle_mute_status.assert_called_once_with(stream_id)

    @pytest.mark.parametrize('key', (*keys_for_command('ENTER'), ' '))
    def test_checkbox_toggle_pin_stream(self, mocker, key, widget_size):
        pin_checkbox = self.stream_info_view.widgets[4]
        toggle_pin_status = self.controller.model.toggle_stream_pinned_status
        stream_id = self.stream_info_view.stream_id
        size = widget_size(pin_checkbox)

        pin_checkbox.keypress(size, key)

        toggle_pin_status.assert_called_once_with(stream_id)
