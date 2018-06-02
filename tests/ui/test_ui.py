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
