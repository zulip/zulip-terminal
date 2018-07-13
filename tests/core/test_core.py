from platform import platform
from typing import Any

import pytest

from zulipterminal.core import Controller


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
        mocker.patch('zulipterminal.core.Controller.show_loading')

    @pytest.fixture
    def controller(self, mocker) -> None:
        self.config_file = 'path/to/zuliprc'
        self.theme = 'default'
        mocker.patch('zulipterminal.core.Controller.'
                     'register_initial_desired_events')
        return Controller(self.config_file, self.theme)

    def test_initialize_controller(self, controller, mocker) -> None:
        self.client.assert_called_once_with(
            config_file=self.config_file,
            client='ZulipTerminal/0.1.0 ' + platform(),
        )
        self.model.assert_called_once_with(controller)
        self.view.assert_called_once_with(controller)
        self.model.poll_for_events.assert_called_once_with()
        controller.register_initial_desired_events.assert_called_once_with()
        assert controller.theme == self.theme

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
        assert controller.model.narrow == [['stream', stream_button.caption]]
        controller.model.msg_view.clear.assert_called_once_with()
        controller.model.msg_list.set_focus.assert_called_once_with(0)
        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        id_list = index_stream['all_stream'][stream_button.stream_id]
        assert {widget.original_widget.message['id']} == id_list

    def test_narrow_to_topic(self, mocker, controller,
                             msg_box, index_topic):
        expected_narrow = [['stream', msg_box.caption],
                           ['topic', msg_box.title]]
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
        controller.model.msg_list.set_focus.assert_called_once_with(0)
        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        id_list = index_topic['stream'][msg_box.stream_id][msg_box.title]
        assert {widget.original_widget.message['id']} == id_list

    def test_narrow_to_user(self, mocker, controller, user_button, index_user):
        controller.model.client = self.client
        controller.model.narrow = []
        controller.model.index = index_user
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.model.user_id = 5140
        controller.model.user_dict = {
            user_button.email: {
                'user_id': user_button.user_id
            }
        }
        controller.narrow_to_user(user_button)
        assert controller.model.narrow == [["pm_with", user_button.email]]
        controller.model.msg_view.clear.assert_called_once_with()
        controller.model.msg_list.set_focus.assert_called_once_with(0)
        recipients = frozenset([controller.model.user_id, user_button.user_id])
        assert controller.model.recipients == recipients
        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        id_list = index_user['private'][recipients]
        assert {widget.original_widget.message['id']} == id_list

    def test_show_all_messages(self, mocker, controller, index_all_messages):
        controller.model.client = self.client
        controller.model.narrow = [['stream', 'PTEST']]
        controller.model.index = index_all_messages
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
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
        controller.model.msg_list.set_focus.assert_called_once_with(1)
        widgets = controller.model.msg_view.extend.call_args_list[0][0][0]
        id_list = index_all_messages['all_messages']
        msg_ids = set(widget.original_widget.message['id']
                      for widget in widgets)
        assert msg_ids == id_list

    def test_show_all_pm(self, mocker, controller, index_user):
        controller.model.client = self.client
        controller.model.narrow = []
        controller.model.index = index_user
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.show_all_pm('')
        assert controller.model.narrow == [['is', 'private']]
        controller.model.msg_view.clear.assert_called_once_with()
        controller.model.msg_list.set_focus.assert_called_once_with(0)
        id_list = index_user['all_private']
        widget = controller.model.msg_view.extend.call_args_list[0][0][0][0]
        assert {widget.original_widget.message['id']} == id_list

    def test_register_initial_desired_events(self, mocker):
        self.config_file = 'path/to/zuliprc'
        self.theme = 'default'
        controller = Controller(self.config_file, self.theme)
        event_types = [
            'message',
            'update_message',
            'reaction'
        ]
        controller.client.register.assert_called_once_with(
                                   event_types=event_types)

    def test_main(self, mocker, controller):
        ret_mock = mocker.Mock()
        mock_loop = mocker.patch('urwid.MainLoop', return_value=ret_mock)
        controller.view.palette = {
            'default': 'theme_properties'
        }
        controller.main()
        assert mock_loop.call_count == 1
