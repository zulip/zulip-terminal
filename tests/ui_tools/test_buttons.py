import pytest
from urwid import AttrMap

from zulipterminal.ui_tools.buttons import MessageLinkButton


BUTTONS = "zulipterminal.ui_tools.buttons"


class TestMessageLinkButton:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        self.super_init = mocker.patch(BUTTONS + '.urwid.Button.__init__')
        self.connect_signal = mocker.patch(BUTTONS + '.urwid.connect_signal')

    def message_link_button(self, caption='', link='', display_attr=None):
        self.caption = caption
        self.link = link
        self.display_attr = display_attr
        return MessageLinkButton(self.controller, self.caption, self.link,
                                 self.display_attr)

    def test_init(self, mocker):
        self.update_widget = (
            mocker.patch(BUTTONS + '.MessageLinkButton.update_widget')
        )

        mocked_button = self.message_link_button()

        assert mocked_button.controller == self.controller
        assert mocked_button.link == self.link
        self.super_init.assert_called_once_with('')
        self.update_widget.assert_called_once_with(self.caption,
                                                   self.display_attr)
        assert self.connect_signal.called

    @pytest.mark.parametrize('caption, expected_cursor_position', [
        ('Test', 5),
        ('Check', 6),
    ])
    def test_update_widget(self, mocker, caption, expected_cursor_position,
                           display_attr=None):
        self.selectable_icon = mocker.patch(BUTTONS + '.urwid.SelectableIcon')

        # The method update_widget() is called in MessageLinkButton's init.
        mocked_button = self.message_link_button(caption=caption,
                                                 display_attr=display_attr)

        self.selectable_icon.assert_called_once_with(
            caption, cursor_position=expected_cursor_position
        )
        assert isinstance(mocked_button._w, AttrMap)
