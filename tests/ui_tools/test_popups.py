from collections import OrderedDict

import pytest
from urwid import Columns, Text

from zulipterminal.config.keys import keys_for_command
from zulipterminal.ui_tools.views import EditHistoryView


VIEWS = "zulipterminal.ui_tools.views"


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
