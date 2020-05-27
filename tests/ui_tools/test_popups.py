from collections import OrderedDict

import pytest

from zulipterminal.config.keys import keys_for_command
from zulipterminal.ui_tools.views import EditHistoryView


VIEWS = "zulipterminal.ui_tools.views"


class TestEditHistoryView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        mocker.patch.object(self.controller, 'maximum_popup_dimensions',
                            return_value=(64, 64))
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

    @pytest.mark.parametrize('key', keys_for_command('MSG_INFO'))
    def test_keypress_exit_popup(self, key):
        size = (200, 20)

        self.edit_history_view.keypress(size, key)

        assert self.controller.exit_popup.called

    def test_keypress_exit_popup_invalid_key(self):
        size = (200, 20)
        key = 'a'

        self.edit_history_view.keypress(size, key)

        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', {*keys_for_command('EDIT_HISTORY'),
                                     *keys_for_command('GO_BACK')})
    def test_keypress_show_msg_info(self, key):
        size = (200, 20)

        self.edit_history_view.keypress(size, key)

        self.controller.show_msg_info.assert_called_once_with(
            msg=self.message,
            message_links=OrderedDict(),
            time_mentions=list(),
        )

    def test_keypress_navigation(self, mocker,
                                 navigation_key_expected_key_pair):
        size = (200, 20)
        key, expected_key = navigation_key_expected_key_pair
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')

        self.edit_history_view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)
