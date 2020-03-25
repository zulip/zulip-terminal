from platform import platform
from typing import Any

import pytest

from zulipterminal.core import THEMES, TUTORIAL, Controller
from zulipterminal.version import ZT_VERSION


CORE = "zulipterminal.core"


class TestController:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: Any) -> None:
        self.client = mocker.patch('zulip.Client')
        self.model = mocker.patch('zulipterminal.model.Model.__init__',
                                  return_value=None)
        self.view = mocker.patch('zulipterminal.ui.View.__init__',
                                 return_value=None)
        self.model.poll_for_events = mocker.patch('zulipterminal.model.Model'
                                                  '.poll_for_events')
        self.model.view = self.view
        self.view.focus_col = 1

    @pytest.fixture
    def controller(self, mocker) -> None:
        self.config_file = 'path/to/zuliprc'
        self.theme_name = 'default'
        self.autohide = True  # FIXME Add tests for no-autohide
        self.notify_enabled = False
        self.tutorial = True
        self.main_loop = mocker.patch(CORE + '.urwid.MainLoop',
                                      return_value=mocker.Mock())
        return Controller(self.config_file, self.theme_name, self.autohide,
                          self.notify_enabled, self.tutorial)

    def test_initialize_controller(self, controller, mocker) -> None:
        self.client.assert_called_once_with(
            config_file=self.config_file,
            client='ZulipTerminal/' + ZT_VERSION + ' ' + platform(),
        )
        self.model.assert_called_once_with(controller)
        assert controller.theme == THEMES[self.theme_name]

    def test_init_model(self, mocker) -> None:
        mocker.patch('zulipterminal.core.Controller.__init__',
                     return_value=None)
        controller = Controller('config', 'theme', True, True, True)
        controller.capture_stdout = mocker.Mock()
        controller.init_model()

        self.model.assert_called_once_with(controller)
        assert controller.capture_stdout.called

    def test_init_view(self, controller, mocker) -> None:
        controller.init_view()
        self.view.assert_called_once_with(controller)
        self.model.poll_for_events.assert_called_once_with()

    def test_raise_exception(self, controller) -> None:
        with pytest.raises(Exception):
            controller.raise_exception(Exception)

    @pytest.mark.parametrize('spinner, show_settings', [
        (['-'], True),
        (['|'], False),
    ])
    def test_loading_text(self, controller, spinner, show_settings):
        SETTINGS = ["\n\nTheme [t]: ",
                    ('starred', controller.theme_name),
                    "\nAutohide [a]: ",
                    ('starred', str(controller.autohide)),
                    "\nNotify [n]: ",
                    ('starred', str(controller.notify_enabled))]
        text = controller.loading_text(spinner, show_settings)
        if show_settings:
            assert text == [TUTORIAL, ('idle', ["\nLoaded "] + spinner),
                            SETTINGS]
        else:
            assert text == [TUTORIAL, ('idle', ["\nLoading "] + spinner)]

    def test_narrow_to_stream(self, mocker, controller,
                              stream_button, index_stream) -> None:
        controller.model.narrow = []
        controller.model.index = index_stream
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.stream_dict = {
            205: {
                'color': '#ffffff',
            }
        }
        controller.model.muted_streams = []
        controller.model.muted_topics = []
        controller.narrow_to_stream(stream_button)
        assert controller.model.stream_id == stream_button.stream_id
        assert controller.model.narrow == [['stream',
                                            stream_button.stream_name]]
        controller.model.msg_view.clear.assert_called_once_with()

        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        stream_id = stream_button.stream_id
        id_list = index_stream['stream_msg_ids_by_stream_id'][stream_id]
        assert {widget.original_widget.message['id']} == id_list

    def test_narrow_to_topic(self, mocker, controller,
                             msg_box, index_topic):
        expected_narrow = [['stream', msg_box.stream_name],
                           ['topic', msg_box.topic_name]]
        controller.model.narrow = []
        controller.model.index = index_topic
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.stream_dict = {
            205: {
                'color': '#ffffff',
            }
        }
        controller.model.muted_streams = []
        controller.model.muted_topics = []
        controller.narrow_to_topic(msg_box)
        assert controller.model.stream_id == msg_box.stream_id
        assert controller.model.narrow == expected_narrow
        controller.model.msg_view.clear.assert_called_once_with()

        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        stream_id, topic_name = msg_box.stream_id, msg_box.topic_name
        id_list = index_topic['topic_msg_ids'][stream_id][topic_name]
        assert {widget.original_widget.message['id']} == id_list

    def test_narrow_to_user(self, mocker, controller, user_button, index_user):
        controller.model.narrow = []
        controller.model.index = index_user
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.user_id = 5140
        controller.model.user_email = "some@email"
        controller.model.user_dict = {
            user_button.email: {
                'user_id': user_button.user_id
            }
        }
        controller.narrow_to_user(user_button)
        assert controller.model.narrow == [["pm_with", user_button.email]]
        controller.model.msg_view.clear.assert_called_once_with()
        recipients = frozenset([controller.model.user_id, user_button.user_id])
        assert controller.model.recipients == recipients
        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        id_list = index_user['private_msg_ids_by_user_ids'][recipients]
        assert {widget.original_widget.message['id']} == id_list

    def test_show_all_messages(self, mocker, controller, index_all_messages):
        controller.model.narrow = [['stream', 'PTEST']]
        controller.model.index = index_all_messages
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.user_email = "some@email"
        controller.model.stream_dict = {
            205: {
                'color': '#ffffff',
            }
        }
        controller.model.muted_streams = []
        controller.model.muted_topics = []

        controller.show_all_messages('')

        assert controller.model.narrow == []
        controller.model.msg_view.clear.assert_called_once_with()

        widgets = controller.model.msg_view.extend.call_args_list[0][0][0]
        id_list = index_all_messages['all_msg_ids']
        msg_ids = {widget.original_widget.message['id'] for widget in widgets}
        assert msg_ids == id_list

    def test_show_all_pm(self, mocker, controller, index_user):
        controller.model.narrow = []
        controller.model.index = index_user
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.user_email = "some@email"

        controller.show_all_pm('')

        assert controller.model.narrow == [['is', 'private']]
        controller.model.msg_view.clear.assert_called_once_with()

        widgets = controller.model.msg_view.extend.call_args_list[0][0][0]
        id_list = index_user['private_msg_ids']
        msg_ids = {widget.original_widget.message['id'] for widget in widgets}
        assert msg_ids == id_list

    def test_show_all_starred(self, mocker, controller, index_all_starred):
        controller.model.narrow = []
        controller.model.index = index_all_starred
        controller.model.muted_streams = set()  # FIXME Expand upon this
        controller.model.muted_topics = []  # FIXME Expand upon this
        controller.model.user_email = "some@email"
        controller.model.stream_dict = {
            205: {
                'color': '#ffffff',
            }
        }
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')

        controller.show_all_starred('')

        assert controller.model.narrow == [['is', 'starred']]
        controller.model.msg_view.clear.assert_called_once_with()

        id_list = index_all_starred['starred_msg_ids']
        widgets = controller.model.msg_view.extend.call_args_list[0][0][0]
        msg_ids = {widget.original_widget.message['id'] for widget in widgets}
        assert msg_ids == id_list

    def test_show_all_mentions(self, mocker, controller, index_all_mentions):
        controller.model.narrow = []
        controller.model.index = index_all_mentions
        controller.model.muted_streams = set()  # FIXME Expand upon this
        controller.model.muted_topics = []  # FIXME Expand upon this
        controller.model.user_email = "some@email"
        controller.model.stream_dict = {
            205: {
                'color': '#ffffff',
            }
        }
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')

        controller.show_all_mentions('')

        assert controller.model.narrow == [['is', 'mentioned']]
        controller.model.msg_view.clear.assert_called_once_with()

        id_list = index_all_mentions['mentioned_msg_ids']
        widgets = controller.model.msg_view.extend.call_args_list[0][0][0]
        msg_ids = {widget.original_widget.message['id'] for widget in widgets}
        assert msg_ids == id_list

    def test_main(self, mocker, controller):
        # pass
        controller.show_main_view = mocker.Mock()
        mock_tsk = mocker.patch('zulipterminal.ui.Screen.tty_signal_keys')
        controller.restore_stdout = mocker.Mock()
        controller.loop.screen.tty_signal_keys = mocker.Mock(return_value={})
        controller.main()

        controller.show_main_view.assert_called_once_with()
        controller.loop.run.assert_called_once_with()

    @pytest.mark.parametrize('muted_streams, action', [
        ({205, 89}, 'unmuting'),
        ({89}, 'muting')
    ])
    def test_stream_muting_confirmation_popup(self, mocker, controller,
                                              stream_button, muted_streams,
                                              action):
        pop_up = mocker.patch(CORE+'.PopUpConfirmationView')
        text = mocker.patch(CORE + '.urwid.Text')
        partial = mocker.patch(CORE + '.partial')
        controller.model.muted_streams = muted_streams
        controller.loop = mocker.Mock()

        controller.stream_muting_confirmation_popup(stream_button)
        text.assert_called_with(("bold", "Confirm " + action +
                                 " of stream '" +
                                 stream_button.stream_name +
                                 "' ?"), "center")
        pop_up.assert_called_once_with(controller, text(), partial())

    @pytest.mark.parametrize('initial_narrow, final_narrow', [
        ([], [['search', 'FOO']]),
        ([['search', 'BOO']], [['search', 'FOO']]),
        ([['stream', 'PTEST']], [['stream', 'PTEST'], ['search', 'FOO']]),
        ([['pm_with', 'foo@zulip.com'], ['search', 'BOO']],
         [['pm_with', 'foo@zulip.com'], ['search', 'FOO']]),
        ([['stream', 'PTEST'], ['topic', 'RDS']],
         [['stream', 'PTEST'], ['topic', 'RDS'], ['search', 'FOO']]),
    ], ids=[
        'Default_all_msg_search', 'redo_default_search',
        'search_within_stream', 'pm_search_again',
        'search_within_topic_narrow',
    ])
    @pytest.mark.parametrize('msg_ids', [
        ({200, 300, 400}),
        (set()),
        ({100})
    ])
    def test_search_message(self, initial_narrow, final_narrow,
                            controller, mocker, msg_ids):
        get_message = mocker.patch('zulipterminal.model.Model.get_messages')
        create_msg = mocker.patch('zulipterminal.core.create_msg_box_list')
        mocker.patch(
            'zulipterminal.model.Model.get_message_ids_in_current_narrow',
            return_value=msg_ids)
        controller.model.index = {'search': {500}}  # Any initial search index
        controller.model.msg_view = []
        controller.model.narrow = initial_narrow

        def set_msg_ids(*args, **kwargs):
            controller.model.index['search'].update(msg_ids)
        get_message.side_effect = set_msg_ids
        assert controller.model.index['search'] == {500}

        controller.search_messages('FOO')

        assert controller.model.narrow == final_narrow
        get_message.assert_called_once_with(
            num_after=0, num_before=30, anchor=10000000000)
        create_msg.assert_called_once_with(controller.model, msg_ids)
        assert controller.model.index == {'search': msg_ids}

    def test_initialize_loop(self, mocker, controller):
        assert self.main_loop.call_count == 1
        assert controller.loop.watch_pipe.call_count == 2

    @pytest.mark.parametrize('tutorial', [
        True, False
    ])
    def test_show_main_view_has_model(self, controller, mocker, tutorial):
        controller.capture_stdout = mocker.Mock()
        controller.model = mocker.Mock()
        controller.update_screen = mocker.Mock()
        controller.init_view = mocker.Mock()
        controller.txt = mocker.Mock()
        controller.loading_text = mocker.Mock()
        controller.view = mocker.Mock()
        controller.wait_after_loading = tutorial
        controller.show_main_view()

        if tutorial:
            assert controller.txt.set_text.called
            controller.update_screen.assert_called_once_with()
        else:
            controller.txt.keypress.assert_called_once_with((20, 20), 'enter')

    def test_show_settings_after_loading(self, controller, mocker):
        controller.txt = mocker.Mock()
        controller.update_screen = mocker.Mock()
        controller.loading_text = mocker.Mock()

        controller.show_settings_after_loading()

        assert controller.txt.set_text.called
        controller.loading_text.assert_called_once_with([
            u'\u2713  \nPress ',
            ('starred', 'Enter'),
            ' to continue >>\nPress ',
            ('starred', 'h'),
            ' to skip the tutorial from next time and continue.\n\n'
            'You can now toggle some of the settings below by pressing the'
            ' key next to them.'],
            show_settings=True
        )
        controller.update_screen.assert_called_once_with()
