import pytest
from zulipterminal.ui import View


class TestView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.patch('zulipterminal.core.Controller',
                                       return_value=None)
        self.client = mocker.patch('zulipterminal.core.Controller.client')
        self.model = mocker.patch('zulipterminal.core.Controller.model')
        self.write_box = mocker.patch('zulipterminal.ui.WriteBox')
        self.search_box = mocker.patch('zulipterminal.ui.SearchBox')

    @pytest.fixture
    def view(self, mocker):
        main_window = mocker.patch('zulipterminal.ui.View.main_window')
        return View(self.controller)

    def test_init(self, mocker):
        main_window = mocker.patch('zulipterminal.ui.View.main_window')
        view = View(self.controller)
        assert view.controller == self.controller
        assert view.model == self.model
        assert view.client == self.client
        assert view.streams == self.model.streams
        self.write_box.assert_called_once_with(view)
        self.search_box.assert_called_once_with(self.controller)
        main_window.assert_called_once_with()

    def test_left_column_view(self, mocker, view):
        left_view = mocker.patch('zulipterminal.ui.LeftColumnView')
        return_value = view.left_column_view()
        assert return_value == left_view(view)

    def test_message_view(self, view, mocker):
        middle_view = mocker.patch('zulipterminal.ui.MiddleColumnView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.message_view()
        middle_view.assert_called_once_with(view.model, view.write_box,
                                            view.search_box)
        assert view.middle_column == middle_view()
        assert return_value == line_box()

    def test_right_column_view(self, view, mocker):
        right_view = mocker.patch('zulipterminal.ui.RightColumnView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.right_column_view()
        right_view.assert_called_once_with(view)
        assert view.users_view == right_view()
        assert return_value == line_box()

    def test_main_window(self, mocker):
        left = mocker.patch('zulipterminal.ui.View.left_column_view')
        center = mocker.patch('zulipterminal.ui.View.message_view')
        right = mocker.patch('zulipterminal.ui.View.right_column_view')
        col = mocker.patch("zulipterminal.ui.urwid.Columns")
        frame = mocker.patch('zulipterminal.ui.urwid.Frame')
        title_divider = mocker.patch('zulipterminal.ui.urwid.Divider')
        text = mocker.patch('zulipterminal.ui.urwid.Text')

        full_name = "Bob James"
        email = "Bob@bob.com"
        server = "https://chat.zulip.zulip"

        mocker.patch('zulipterminal.core.Controller.client.get_profile',
                     return_value=dict(full_name=full_name, email=email))
        self.controller.client.base_url = server
        title_length = (len(email) + len(full_name) + len(server) + 9)

        view = View(self.controller)

        left.assert_called_once_with()
        center.assert_called_once_with()
        right.assert_called_once_with()
        expected_column_calls = [
            mocker.call([
                (25, left()),
                ('weight', 10, center()),
                (25, right()),
                ], focus_column=1),
            mocker.call([
                title_divider(),
                (title_length, text()),
                title_divider(),
                ])
        ]
        col.assert_has_calls(expected_column_calls)

        assert view.body == col()
        frame.assert_called_once_with(view.body, col(),
                                      focus_part='body')

    def test_keypress(self, view, mocker):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = (20,)
        key = 'j'

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")

        # Test Normal Mode keypress
        view.controller.editor_mode = False
        view.keypress(size, 'down')
        super_view.assert_called_once_with(size, 'down')

    def test_keypress_w(self, view, mocker):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = (20,)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.editor_mode = False

        # Test "w" keypress
        view.keypress(size, "w")
        view.users_view.keypress.assert_called_once_with(size, "w")
        assert view.body.focus_col == 2
        view.user_search.set_edit_text.assert_called_once_with("")
        assert view.controller.editor_mode is True
        assert view.controller.editor == view.user_search

    def test_keypress_q(self, view, mocker):
        view.stream_w = mocker.Mock()
        view.left_col_w = mocker.Mock()
        view.stream_w.search_box = mocker.Mock()
        view.body = mocker.Mock()
        size = (20,)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.editor_mode = False

        # Test "q" keypress
        view.keypress(size, "q")
        view.left_col_w.keypress.assert_called_once_with(size, "q")
        assert view.body.focus_col == 0
        view.stream_w.search_box.set_edit_text.assert_called_once_with("")
        assert view.controller.editor_mode is True
        assert view.controller.editor == view.stream_w.search_box

    def test_keypress_edit_mode(self, view, mocker):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = (20,)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")

        # Test Edit Mode Keypress
        view.controller.editor_mode = True
        size = (130, 28)
        view.keypress(size, "w")
        view.controller.editor.keypress.assert_called_once_with((28,), "w")
