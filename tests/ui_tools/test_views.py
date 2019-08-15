import pytest

from zulipterminal.ui_tools.views import (
    UsersView,
)

VIEWS = "zulipterminal.ui_tools.views"


class TestUsersView:
    @pytest.fixture
    def user_view(self, mocker):
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        self.view = mocker.Mock()
        return UsersView(self.view, "USER_BTN_LIST")

    def test_mouse_event(self, mocker, user_view):
        mocker.patch.object(user_view, 'keypress')
        size = (200, 20)
        col = 1
        row = 1
        focus = "WIDGET"
        # Left click
        user_view.mouse_event(size, "mouse press", 4, col, row, focus)
        user_view.keypress.assert_called_with(size, "up")

        # Right click
        user_view.mouse_event(size, "mouse press", 5, col, row, focus)
        user_view.keypress.assert_called_with(size, "down")

        # Other actions - No action
        return_value = user_view.mouse_event(
            size, "mouse release", 4, col, row, focus)
        assert return_value is False

        # Other clicks
        return_value = user_view.mouse_event(
            size, "mouse press", 1, col, row, focus)
        assert return_value is False

    def test_update_user_list_editor_mode(self, mocker, user_view):
        user_view.view.controller.update_screen = mocker.Mock()
        user_view.view.controller.editor_mode = False

        user_view.update_user_list("SEARCH_BOX", "NEW_TEXT")

        user_view.view.controller.update_screen.assert_not_called()

    @pytest.mark.parametrize('search_string, assert_list, \
                              match_return_value', [
        pytest.param('U', ["USER1", "USER2"], True,
                     marks=pytest.mark.xfail(reason="Unconnected")),
        pytest.param('F', [], False,
                     marks=pytest.mark.xfail(reason="Unconnected")),
    ], ids=[
        'user match', 'no user match',
    ])
    def test_update_user_list(self, user_view, mocker,
                              search_string, assert_list, match_return_value):
        user_view.view.controller.editor_mode = True
        self.view.users = ["USER1", "USER2"]
        mocker.patch(VIEWS + ".match_user", return_value=match_return_value)
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        user_view.update_user_list("SEARCH_BOX", search_string)

        user_view.users_view.assert_called_with(assert_list)
        set_body.assert_called_once_with(user_view.body)
