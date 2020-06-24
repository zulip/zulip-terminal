import pytest

from zulipterminal.ui import View


class TestView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.patch('zulipterminal.core.Controller',
                                       return_value=None)
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
        assert view.pinned_streams == self.model.pinned_streams
        assert view.unpinned_streams == self.model.unpinned_streams
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
        middle_view.assert_called_once_with(view, view.model,
                                            view.write_box, view.search_box)
        assert view.middle_column == middle_view()
        assert return_value == line_box()

    def test_right_column_view(self, view, mocker):
        right_view = mocker.patch('zulipterminal.ui.RightColumnView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.right_column_view()
        right_view.assert_called_once_with(View.RIGHT_WIDTH, view)
        assert view.users_view == right_view()
        assert return_value == line_box()

    def test_set_footer_text_default(self, view, mocker):
        mocker.patch('zulipterminal.ui.View.get_random_help',
                     return_value=['some help text'])

        view.set_footer_text()

        view._w.footer.set_text.assert_called_once_with(['some help text'])
        view.controller.update_screen.assert_called_once_with()

    def test_set_footer_text_specific_text(self, view, text='blah'):
        view.set_footer_text([text])

        view._w.footer.set_text.assert_called_once_with([text])
        view.controller.update_screen.assert_called_once_with()

    def test_set_footer_text_with_duration(self, view, mocker,
                                           custom_text="custom", duration=5.3):
        mocker.patch('zulipterminal.ui.View.get_random_help',
                     return_value=['some help text'])
        mock_sleep = mocker.patch('time.sleep')

        view.set_footer_text([custom_text], duration)

        view._w.footer.set_text.assert_has_calls([
            mocker.call([custom_text]),
            mocker.call(['some help text'])
        ])
        mock_sleep.assert_called_once_with(duration)
        assert view.controller.update_screen.call_count == 2

    def test_footer_view(self, mocker, view):
        footer = view.footer_view()
        assert isinstance(footer.text, str)

    def test_main_window(self, mocker):
        left = mocker.patch('zulipterminal.ui.View.left_column_view')
        center = mocker.patch('zulipterminal.ui.View.message_view')
        right = mocker.patch('zulipterminal.ui.View.right_column_view')
        col = mocker.patch("zulipterminal.ui.urwid.Columns")
        frame = mocker.patch('zulipterminal.ui.urwid.Frame')
        title_divider = mocker.patch('zulipterminal.ui.urwid.Divider')
        text = mocker.patch('zulipterminal.ui.urwid.Text')
        footer_view = mocker.patch('zulipterminal.ui.View.footer_view')

        full_name = "Bob James"
        email = "Bob@bob.com"
        server = "https://chat.zulip.zulip/"

        self.controller.model = self.model
        self.model.user_full_name = full_name
        self.model.user_email = email
        self.model.server_url = server

        title_length = (len(email) + len(full_name) + len(server) + 8)

        view = View(self.controller)

        left.assert_called_once_with()
        center.assert_called_once_with()
        right.assert_called_once_with()

        expected_column_calls = [
            mocker.call([
                (View.LEFT_WIDTH, left()),
                ('weight', 10, center()),
                (0, right()),
                ], focus_column=0),
            mocker.call()._contents.set_focus_changed_callback(
                view.model.msg_list.read_message),
            mocker.call([
                title_divider(),
                (title_length, text()),
                title_divider(),
                ])
        ]
        col.assert_has_calls(expected_column_calls)

        assert view.body == col()
        frame.assert_called_once_with(
            view.body, col(), focus_part='body', footer=footer_view())

    @pytest.mark.parametrize('autohide', [True, False])
    @pytest.mark.parametrize('visible, width', [
        (True, View.LEFT_WIDTH),
        (False, 0)
    ])
    def test_show_left_panel(self, mocker, view,
                             visible, width, autohide):
        view.left_panel = mocker.Mock()
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
        view.body.focus_position = None
        view.controller.autohide = autohide

        view.show_left_panel(visible=visible)

        if autohide:
            (view.body.options.
             assert_called_once_with(width_type='given', width_amount=width))
            if visible:
                assert view.body.focus_position == 0
        else:
            view.body.options.assert_not_called()

    @pytest.mark.parametrize('autohide', [True, False])
    @pytest.mark.parametrize('visible, width', [
        (True, View.RIGHT_WIDTH),
        (False, 0)
    ])
    def test_show_right_panel(self, mocker, view,
                              visible, width, autohide):
        view.right_panel = mocker.Mock()
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
        view.body.focus_position = None
        view.controller.autohide = autohide

        view.show_right_panel(visible=visible)

        if autohide:
            (view.body.options.
             assert_called_once_with(width_type='given', width_amount=width))
            if visible:
                assert view.body.focus_position == 2
        else:
            view.body.options.assert_not_called()

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

    @pytest.mark.parametrize('autohide', [True, False], ids=[
        'autohide', 'no_autohide'])
    def test_keypress_w(self, view, mocker, autohide):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.controller.autohide = autohide
        view.body.contents = ['streams', 'messages', mocker.Mock()]
        view.user_search = mocker.Mock()
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        size = (20,)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.editor_mode = False

        view.body.focus_position = None

        # Test "w" keypress
        view.keypress(size, "w")
        view.users_view.keypress.assert_called_once_with(size, "w")
        assert view.body.focus_position == 2
        view.user_search.set_edit_text.assert_called_once_with("")
        assert view.controller.editor_mode is True
        assert view.controller.editor == view.user_search

    @pytest.mark.parametrize('autohide', [True, False], ids=[
        'autohide', 'no_autohide'])
    def test_keypress_q(self, view, mocker, autohide):
        view.stream_w = mocker.Mock()
        view.left_col_w = mocker.Mock()
        view.stream_w.search_box = mocker.Mock()
        view.controller.autohide = autohide
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), 'messages', 'users']
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        size = (20,)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.editor_mode = False

        view.body.focus_position = None

        # Test "q" keypress
        view.keypress(size, "q")

        view.left_panel.keypress.assert_called_once_with(size, "q")
        assert view.body.focus_position == 0
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
