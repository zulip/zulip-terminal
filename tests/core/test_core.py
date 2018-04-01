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

    @pytest.fixture
    def controller(self) -> None:
        self.config_file = 'path/to/zuliprc'
        self.theme = 'default'
        return Controller(self.config_file, self.theme)

    def test_initialize_controller(self, controller) -> None:
        self.client.assert_called_once_with(
            config_file=self.config_file,
            client='ZulipTerminal/0.1.0 ' + platform(),
        )
        self.model.assert_called_once_with(controller)
        self.view.assert_called_once_with(controller)
        assert controller.theme == self.theme

    def test_narrow_to_stream(self, mocker, controller,
                              stream_button, index_stream) -> None:
        controller.model.narrow = []
        controller.model.index = index_stream
        controller.model.msg_view = mocker.patch('urwid.SimpleFocusListWalker')
        controller.model.msg_list = mocker.patch('urwid.ListBox')
        controller.narrow_to_stream(stream_button)
        assert controller.model.stream_id == stream_button.stream_id
        assert controller.model.narrow == [['stream', stream_button.caption]]
        controller.model.msg_view.clear.assert_called_once_with()
        controller.model.msg_list.set_focus.assert_called_once_with(0)
