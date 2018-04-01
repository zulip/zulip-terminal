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
        # FIXME: E TypeError: __init__() should return None, not 'MagicMock'
        #        without __init__
        self.view = mocker.patch('zulipterminal.ui.View.__init__',
                                 return_value=None)

    def test_initialize_controller(self) -> None:
        config_file = 'path/to/zuliprc'
        theme = 'default'
        self.controller = Controller(config_file, theme)
        self.client.assert_called_once_with(
            config_file=config_file,
            client='ZulipTerminal/0.1.0 ' + platform(),
        )
        self.model.assert_called_once_with(self.controller)
        self.view.assert_called_once_with(self.controller)
        assert self.controller.theme == theme
