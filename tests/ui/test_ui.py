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

    def test_menu_view(self, view, mocker):
        view.model.unread_counts.get.return_value = 1
        home_button = mocker.patch('zulipterminal.ui.HomeButton')
        pm_button = mocker.patch('zulipterminal.ui.PMButton')
        list_box = mocker.patch('zulipterminal.ui.urwid.ListBox')
        walker = mocker.patch('zulipterminal.ui.urwid.SimpleFocusListWalker')
        return_value = view.menu_view()
        home_button.assert_called_once_with(self.controller, count=1)
        pm_button.assert_called_once_with(self.controller, count=1)
        walker.assert_called_once_with([
            home_button(), pm_button()
        ])
        list_box.assert_called_once_with(walker())
        assert return_value == list_box()

    def test_streams_view(self, view, mocker, streams):
        view.streams = streams
        view.model.unread_counts.get.return_value = 1
        stream_button = mocker.patch('zulipterminal.ui.StreamButton')
        stream_view = mocker.patch('zulipterminal.ui.StreamsView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.streams_view()
        stream_button.assert_called_with(
            streams[1],
            controller=self.controller,
            view=view,
            count=1)
        stream_view.assert_called_once_with([
            stream_button(), stream_button()
        ])
        line_box.assert_called_once_with(stream_view(), title="Streams")
        assert return_value == line_box()

    def test_left_column_view(self, view, mocker):
        menu_view = mocker.patch('zulipterminal.ui.View.menu_view')
        streams_view = mocker.patch('zulipterminal.ui.View.streams_view')
        pile = mocker.patch('zulipterminal.ui.urwid.Pile')
        return_value = view.left_column_view()
        menu_view.assert_called_once_with()
        streams_view.assert_called_once_with()
        pile.assert_called_once_with([
            (4, menu_view()),
            streams_view(),
        ])
        assert return_value == pile()

    def test_message_view(self, view, mocker):
        middle_view = mocker.patch('zulipterminal.ui.MiddleColumnView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.message_view()
        middle_view.assert_called_once_with(view.model, view.write_box,
                                            view.search_box)
        assert view.middle_column == middle_view()
        line_box.assert_called_once_with(view.middle_column)
        assert return_value == line_box()

    def test_right_column_view(self, view, mocker):
        right_view = mocker.patch('zulipterminal.ui.RightColumnView')
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        return_value = view.right_column_view()
        right_view.assert_called_once_with(view)
        assert view.users_view == right_view()
        line_box.assert_called_once_with(view.users_view, title=u"Users")
        assert return_value == line_box()

    def test_main_window(self, mocker):
        left = mocker.patch('zulipterminal.ui.View.left_column_view')
        center = mocker.patch('zulipterminal.ui.View.message_view')
        right = mocker.patch('zulipterminal.ui.View.right_column_view')
        col = mocker.patch("zulipterminal.ui.urwid.Columns")
        line_box = mocker.patch('zulipterminal.ui.urwid.LineBox')
        view = View(self.controller)
        left.assert_called_once_with()
        center.assert_called_once_with()
        right.assert_called_once_with()
        col.assert_called_once_with([
            ('weight', 3, left()),
            ('weight', 10, center()),
            ('weight', 3, right()),
        ], focus_column=1)
        assert view.body == col()
        line_box.assert_called_once_with(view.body, title=u"Zulip")
