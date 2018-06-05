import pytest

from zulipterminal.ui_tools.views import MessageView

VIEWS = "zulipterminal.ui_tools.views"


class TestMessageView:

    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.model = mocker.MagicMock()
        self.urwid = mocker.patch(VIEWS + ".urwid")

    @pytest.fixture
    def msg_view(self, mocker, msg_box):
        mocker.patch(VIEWS + ".MessageView.main_view", return_value=[msg_box])
        mocker.patch(VIEWS + ".MessageView.read_message")
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_view = MessageView(self.model)
        return msg_view

    def test_init(self, mocker, msg_view, msg_box):
        assert msg_view.model == self.model
        self.urwid.SimpleFocusListWalker.assert_called_once_with([msg_box])
        msg_view.set_focus.assert_called_once_with(0)
        assert msg_view.old_loading is False
        assert msg_view.new_loading is False

    @pytest.mark.parametrize("index, focus_msg", [
        ({
            'pointer': {
                "[]": set(),
            }
        }, 1),
        ({
            'pointer': {
                "[]": 0,
            }
        }, 0)
    ])
    def test_main_view(self, mocker, index, focus_msg):
        mocker.patch(VIEWS + ".MessageView.read_message")
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_list = ["MSG1", "MSG2"]
        mocker.patch(VIEWS + ".create_msg_box_list",
                     return_value=msg_list)
        self.model.index = index
        self.model.narrow = '[]'
        msg_view = MessageView(self.model)
        assert msg_view.focus_msg == focus_msg

    @pytest.mark.parametrize("narrow, index, current_ids", [
        ([], {
            "all_messages": {0, 1}
        }, {0, 1}),
        ([['stream', 'FOO']], {
            "all_stream": {
                1: {0, 1}
            }
        }, {0, 1}),
        ([['stream', 'FOO'],
         ['topic', 'BOO']], {
             'stream': {
                 1: {
                     'BOO': {0, 1}
                 }
             }
         }, {0, 1}),
        ([['is', 'private']], {
            'all_private': {0, 1}
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {
            'private': {
                frozenset({1, 2}): {0, 1}
            }
        }, {0, 1}),
        ([['search', 'FOO']], {
            'search': {0, 1}
        }, {0, 1})
    ])
    def test_get_current_ids(self, mocker, msg_view, narrow, index,
                             current_ids):
        msg_view.model.recipients = frozenset({1, 2})
        msg_view.model.stream_id = 1
        msg_view.model.narrow = narrow
        msg_view.index = index
        return_value = msg_view.get_current_ids()
        assert return_value == current_ids

    def test_load_old_messages(self, mocker, msg_view):
        mocker.patch.object(msg_view, "get_current_ids", return_value={0})
        self.model.get_messages.return_value = {}
        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=["M1", "M2"])
        msg_view.load_old_messages(0)
        assert msg_view.old_loading is False
        assert msg_view.model.anchor == 0
        assert msg_view.model.num_after == 0
        assert msg_view.model.num_before == 30
        assert msg_view.index == {}
        create_msg_box_list.assert_called_once_with(msg_view.model, set())
        self.model.controller.loop.draw_screen.assert_called_once_with()

    def test_load_new_messages(self, mocker, msg_view):
        mocker.patch.object(msg_view, "get_current_ids", return_value={0})
        self.model.get_messages.return_value = {}
        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=["M1", "M2"])
        msg_view.load_new_messages(0)
        assert msg_view.new_loading is False
        assert msg_view.model.anchor == 0
        assert msg_view.model.num_after == 30
        assert msg_view.model.num_before == 0
        assert msg_view.index == {}
        msg_view.log.extend.assert_called_once_with(['M1', 'M2'])
        create_msg_box_list.assert_called_once_with(msg_view.model, set())
        self.model.controller.loop.draw_screen.assert_called_once_with()

    @pytest.mark.parametrize("event, button, keypress", [
        ("mouse press", 4, "up"),
        ("mouse press", 5, "down"),
    ])
    def test_mouse_event(self, mocker, msg_view, event, button, keypress):
        mocker.patch.object(msg_view, "keypress")
        msg_view.mouse_event((20,), event, button, 0, 0, mocker.Mock())
        msg_view.keypress.assert_called_once_with((20,), keypress)

    # down key tests
    def test_keypress_down_key(self, mocker, msg_view):
        size = (20,)
        key = "down"
        msg_view.new_loading = False
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        msg_view.log.next_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.next_position.assert_called_once_with(
            msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, 'above')

    def test_keypress_down_key_exception(self, mocker, msg_view):
        size = (20,)
        key = "down"
        msg_view.new_loading = False
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)

        # Raise exception
        msg_view.log.next_position = Exception()
        mocker.patch(VIEWS + ".MessageView.focus", return_value=True)
        mocker.patch.object(msg_view, "load_new_messages")
        msg_view.keypress(size, key)
        msg_view.load_new_messages.assert_called_once_with(
            msg_view.focus.original_widget.message['id'],
        )

        # No message in focus
        msg_view.focus = False
        return_value = msg_view.keypress(size, key)
        assert return_value == key

    # up key tests
    def test_keypress_up(self, mocker, msg_view):
        key = "up"
        size = (20,)
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        msg_view.old_loading = False
        msg_view.log.prev_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.prev_position.assert_called_once_with(
            msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, 'below')

    def test_keypress_up_raise_exception(self, mocker, msg_view):
        key = "up"
        size = (20,)
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        msg_view.old_loading = False

        # Raise exception
        msg_view.log.prev_position = Exception()
        mocker.patch(VIEWS + ".MessageView.focus", return_value=True)
        mocker.patch.object(msg_view, "load_old_messages")

        msg_view.keypress(size, key)
        msg_view.load_old_messages.assert_called_once_with(
            msg_view.focus.original_widget.message['id'],
        )

        # No message in focus
        msg_view.focus = False
        return_value = msg_view.keypress(size, key)
        msg_view.load_old_messages.assert_called_with()
        assert return_value == key

    def test_read_message(self, mocker, msg_box):
        mocker.patch(VIEWS + ".MessageView.main_view", return_value=[msg_box])
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_view = MessageView(self.model)
        msg_w = mocker.MagicMock()
        msg_w.attr_map = {None: 'unread'}
        msg_w.original_widget.message = {'id': 1}
        msg_w.set_attr_map.return_value = None
        msg_view.body.get_focus.return_value = (msg_w, 0)
        msg_view.body.get_prev.return_value = (None, 1)
        update_flag = mocker.patch(VIEWS + ".update_flag")
        msg_view.model.narrow = []
        msg_view.model.index = {
            'messages': {
                1: {
                    'flags': [],
                }
            },
            'pointer': {
                '[]': 0
            }
        }
        mocker.patch(VIEWS + ".MessageView.focus_position")
        msg_view.focus_position = 1
        msg_view.read_message()
        assert msg_view.model.index['messages'][1]['flags'] == ['read']
        update_flag.assert_called_once_with([1], self.model.controller)

    def test_read_message_no_msgw(self, mocker, msg_view):
        # MSG_W is NONE CASE
        msg_view.body.get_focus.return_value = (None, 0)
        update_flag = mocker.patch(VIEWS + ".update_flag")
        msg_view.read_message()
        update_flag.assert_not_called()
