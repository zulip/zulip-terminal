import pytest
from collections import defaultdict, OrderedDict
from bs4 import BeautifulSoup

from zulipterminal.ui_tools.views import (
    MessageView,
    MiddleColumnView,
    StreamsView,
    UsersView,
    RightColumnView,
    LeftColumnView,
    HelpView,
)
from zulipterminal.ui_tools.boxes import MessageBox

from urwid import AttrWrap, Columns, Padding, Text

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

    @pytest.mark.parametrize("narrow_focus_pos, focus_msg", [
        (set(), 1), (0, 0)
    ])
    def test_main_view(self, mocker, narrow_focus_pos, focus_msg):
        mocker.patch(VIEWS + ".MessageView.read_message")
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_list = ["MSG1", "MSG2"]
        mocker.patch(VIEWS + ".create_msg_box_list",
                     return_value=msg_list)
        self.model.get_focus_in_current_narrow.return_value = narrow_focus_pos
        msg_view = MessageView(self.model)
        assert msg_view.focus_msg == focus_msg

    @pytest.mark.parametrize('messages_fetched', [
        {},
        {201: "M1"},
        OrderedDict([(201, "M1"), (202, "M2")]),
    ])
    @pytest.mark.parametrize('ids_in_narrow', [
        set(),
        {0},  # Shouldn't apply to empty log case?
    ])
    def test_load_old_messages_empty_log(self, mocker, msg_view,
                                         ids_in_narrow, messages_fetched):
        # Expand parameters to use in test
        new_msg_ids = set(messages_fetched.keys())
        new_msg_widgets = list(messages_fetched.values())

        mocker.patch.object(msg_view.model,
                            "get_message_ids_in_current_narrow",
                            side_effect=[ids_in_narrow,
                                         ids_in_narrow | new_msg_ids])

        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=new_msg_widgets)
        # Specific to this version of the test
        msg_view.log = []

        msg_view.load_old_messages(0)

        assert msg_view.old_loading is False
        assert msg_view.log == list(messages_fetched.values())  # code vs orig
        if messages_fetched:
            (create_msg_box_list.
             assert_called_once_with(msg_view.model, new_msg_ids))
            self.model.controller.update_screen.assert_called_once_with()
        else:
            create_msg_box_list.assert_not_called()
            self.model.controller.update_screen.assert_not_called()
        self.model.get_messages.assert_called_once_with(num_before=30,
                                                        num_after=0,
                                                        anchor=0)

    @pytest.mark.parametrize('messages_fetched', [
        {},
        {201: "M1"},
        OrderedDict([(201, "M1"), (202, "M2")]),
    ])
    @pytest.mark.parametrize('top_id_in_narrow, other_ids_in_narrow', [
        (99, set()),
        (99, {101}),
        (99, {101, 103}),
    ])
    def test_load_old_messages_mocked_log(self, mocker, msg_view,
                                          top_id_in_narrow,
                                          other_ids_in_narrow,
                                          messages_fetched):
        # Expand parameters to use in test
        new_msg_ids = set(messages_fetched.keys())
        new_msg_widgets = list(messages_fetched.values())

        # Parameter constraints
        assert top_id_in_narrow not in other_ids_in_narrow
        assert top_id_in_narrow not in new_msg_ids
        assert other_ids_in_narrow & new_msg_ids == set()

        top_widget = mocker.Mock()
        top_widget.original_widget.message = {'id': top_id_in_narrow}

        ids_in_narrow = {top_id_in_narrow} | other_ids_in_narrow
        mocker.patch.object(msg_view.model,
                            "get_message_ids_in_current_narrow",
                            side_effect=[ids_in_narrow,
                                         ids_in_narrow | new_msg_ids])
        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=(new_msg_widgets +
                                                         [top_widget]))
        initial_log = [top_widget] + len(other_ids_in_narrow)*["existing"]
        msg_view.log = initial_log[:]

        msg_view.load_old_messages(0)

        assert msg_view.old_loading is False
        assert msg_view.log == new_msg_widgets + initial_log
        if messages_fetched:
            create_msg_box_list.assert_called_once_with(msg_view.model,
                                                        {top_id_in_narrow} |
                                                        new_msg_ids)
            self.model.controller.update_screen.assert_called_once_with()
        else:
            create_msg_box_list.assert_not_called()
            self.model.controller.update_screen.assert_not_called()
        self.model.get_messages.assert_called_once_with(num_before=30,
                                                        num_after=0,
                                                        anchor=0)

    # FIXME: Improve this test by covering more parameters
    @pytest.mark.parametrize('ids_in_narrow', [
        ({0}),
    ])
    def test_load_new_messages_empty_log(self, mocker, msg_view,
                                         ids_in_narrow):
        mocker.patch.object(msg_view.model,
                            "get_message_ids_in_current_narrow",
                            return_value=ids_in_narrow)
        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=["M1", "M2"])
        msg_view.log = []

        msg_view.load_new_messages(0)

        assert msg_view.new_loading is False
        assert msg_view.log == ['M1', 'M2']
        create_msg_box_list.assert_called_once_with(msg_view.model, set(),
                                                    last_message=None)
        self.model.controller.update_screen.assert_called_once_with()
        self.model.get_messages.assert_called_once_with(num_before=0,
                                                        num_after=30,
                                                        anchor=0)

    # FIXME: Improve this test by covering more parameters
    @pytest.mark.parametrize('ids_in_narrow', [
        ({0}),
    ])
    def test_load_new_messages_mocked_log(self, mocker, msg_view,
                                          ids_in_narrow):
        mocker.patch.object(msg_view.model,
                            "get_message_ids_in_current_narrow",
                            return_value=ids_in_narrow)
        create_msg_box_list = mocker.patch(VIEWS + ".create_msg_box_list",
                                           return_value=["M1", "M2"])
        msg_view.log = [mocker.Mock()]

        msg_view.load_new_messages(0)

        assert msg_view.new_loading is False
        assert msg_view.log[-2:] == ['M1', 'M2']
        expected_last_msg = msg_view.log[0].original_widget.message
        (create_msg_box_list.
         assert_called_once_with(msg_view.model, set(),
                                 last_message=expected_last_msg))
        self.model.controller.update_screen.assert_called_once_with()
        self.model.get_messages.assert_called_once_with(num_before=0,
                                                        num_after=30,
                                                        anchor=0)

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
        mocker.patch(VIEWS + ".MessageView.set_focus_valign")
        msg_view.log.next_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.next_position.assert_called_once_with(
            msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, 'above')
        msg_view.set_focus_valign.assert_called_once_with('middle')

    def test_keypress_down_key_exception(self, mocker, msg_view):
        size = (20,)
        key = "down"
        msg_view.new_loading = False
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        mocker.patch(VIEWS + ".MessageView.set_focus_valign")

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
        mocker.patch(VIEWS + ".MessageView.set_focus_valign")
        msg_view.old_loading = False
        msg_view.log.prev_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.prev_position.assert_called_once_with(
            msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, 'below')
        msg_view.set_focus_valign.assert_called_once_with('middle')

    def test_keypress_up_raise_exception(self, mocker, msg_view):
        key = "up"
        size = (20,)
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        mocker.patch(VIEWS + ".MessageView.set_focus_valign")
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
        mocker.patch(VIEWS + ".MessageView.update_search_box_narrow")
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
        assert msg_view.update_search_box_narrow.called
        assert msg_view.model.index['messages'][1]['flags'] == ['read']
        update_flag.assert_called_once_with([1], self.model.controller)

    def test_read_message_no_msgw(self, mocker, msg_view):
        # MSG_W is NONE CASE
        msg_view.body.get_focus.return_value = (None, 0)
        update_flag = mocker.patch(VIEWS + ".update_flag")
        msg_view.read_message()
        update_flag.assert_not_called()


class TestStreamsView:

    @pytest.fixture
    def stream_view(self, mocker):
        self.log = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker",
                                return_value=[])
        mocker.patch(VIEWS + ".urwid.connect_signal")
        mocker.patch(VIEWS + ".threading.Lock")
        self.view = mocker.Mock()
        self.search_box = mocker.patch(VIEWS + ".StreamSearchBox")
        stream_btn = mocker.Mock()
        stream_btn.caption = "FOO"
        self.streams_btn_list = [stream_btn]
        return StreamsView(self.streams_btn_list, view=self.view)

    def test_init(self, mocker, stream_view):
        assert stream_view.view == self.view
        assert stream_view.log == []
        assert stream_view.streams_btn_list == self.streams_btn_list
        assert stream_view.search_box
        self.search_box.assert_called_once_with(stream_view)

    def test_update_streams(self, mocker, stream_view):
        self.view.controller.editor_mode = True
        new_text = "F"
        search_box = "SEARCH_BOX"
        stream_view.update_streams(search_box, new_text)
        assert not stream_view.log

    def test_mouse_event(self, mocker, stream_view):
        mocker.patch.object(stream_view, 'keypress')
        size = (200, 20)
        col = 1
        row = 1
        focus = "WIDGET"
        # Left click
        stream_view.mouse_event(size, "mouse press", 4, col, row, focus)
        stream_view.keypress.assert_called_once_with(size, "up")

        # Right click
        stream_view.mouse_event(size, "mouse press", 5, col, row, focus)
        stream_view.keypress.assert_called_with(size, "down")

    def test_keypress_q(self, mocker, stream_view):
        key = "q"
        size = (20,)
        mocker.patch.object(stream_view, 'set_focus')
        stream_view.keypress(size, key)
        stream_view.set_focus.assert_called_once_with("header")

    def test_keypress_esc(self, mocker, stream_view):
        key = "esc"
        size = (20,)
        mocker.patch.object(stream_view, 'set_focus')
        stream_view.keypress(size, key)
        stream_view.set_focus.assert_called_once_with("body")
        stream_view.search_box.set_edit_text.assert_called_once_with(
            "Search streams")
        assert stream_view.log == self.streams_btn_list


class TestUsersView:

    @pytest.fixture
    def user_view(self, mocker):
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        return UsersView("USER_BTN_LIST")

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


class TestMiddleColumnView:

    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        mocker.patch(VIEWS + ".MessageView", return_value="MSG_LIST")
        self.model = mocker.Mock()
        self.view = mocker.Mock()
        self.write_box = mocker.Mock()
        self.search_box = mocker.Mock()
        self.super = mocker.patch(VIEWS + '.urwid.Frame.__init__')
        self.super_keypress = mocker.patch(VIEWS + '.urwid.Frame.keypress')
        self.model.controller == mocker.Mock()

    @pytest.fixture
    def mid_col_view(self):
        return MiddleColumnView(self.view, self.model,
                                self.write_box, self.search_box)

    def test_init(self, mid_col_view):
        assert mid_col_view.model == self.model
        assert mid_col_view.controller == self.model.controller
        assert mid_col_view.last_unread_topic is None
        assert mid_col_view.last_unread_pm is None
        assert mid_col_view.search_box == self.search_box
        assert self.model.msg_list == "MSG_LIST"
        self.super.assert_called_once_with("MSG_LIST", header=self.search_box,
                                           footer=self.write_box)

    def test_get_next_unread_topic(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_topics': {1: 1, 2: 1}
        }
        return_value = mid_col_view.get_next_unread_topic()
        assert return_value == 1
        assert mid_col_view.last_unread_topic == 1

    def test_get_next_unread_topic_again(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_topics': {1: 1, 2: 1}
        }
        mid_col_view.last_unread_topic = 1
        return_value = mid_col_view.get_next_unread_topic()
        assert return_value == 2
        assert mid_col_view.last_unread_topic == 2

    def test_get_next_unread_topic_no_unread(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_topics': {}
        }
        return_value = mid_col_view.get_next_unread_topic()
        assert return_value is None
        assert mid_col_view.last_unread_topic is None

    def test_get_next_unread_pm(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_pms': {1: 1, 2: 1}
        }
        return_value = mid_col_view.get_next_unread_pm()
        assert return_value == 1
        assert mid_col_view.last_unread_pm == 1

    def test_get_next_unread_pm_again(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_pms': {1: 1, 2: 1}
        }
        mid_col_view.last_unread_pm = 1
        return_value = mid_col_view.get_next_unread_pm()
        assert return_value == 2
        assert mid_col_view.last_unread_pm == 2

    def test_get_next_unread_pm_no_unread(self, mid_col_view):
        mid_col_view.model.unread_counts = {
            'unread_pms': {}
        }
        return_value = mid_col_view.get_next_unread_pm()
        assert return_value is None
        assert mid_col_view.last_unread_pm is None

    def test_keypress_esc(self, mid_col_view, mocker):
        key = "esc"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.header')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.header.keypress.assert_called_once_with(size, key)
        mid_col_view.footer.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with('body')
        self.super_keypress.assert_called_once_with(size, key)

    def test_keypress_focus_header(self, mid_col_view, mocker):
        key = "/"
        size = (20,)
        mid_col_view.focus_part = 'header'
        mid_col_view.keypress(size, key)
        self.super_keypress.assert_called_once_with(size, key)

    def test_keypress_search(self, mid_col_view, mocker):
        key = "/"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        assert mid_col_view.controller.editor_mode is True
        assert mid_col_view.controller.editor == mid_col_view.search_box
        mid_col_view.set_focus.assert_called_once_with('header')

    def test_keypress_r(self, mid_col_view, mocker):
        key = "r"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, 'enter')
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 1

    def test_keypress_c(self, mid_col_view, mocker):
        key = "c"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, 'c')
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 0

    def test_keypress_R(self, mid_col_view, mocker):
        key = "R"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, 'R')
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 1

    def test_keypress_n_stream(self, mid_col_view, mocker):
        key = "n"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        topic_btn = mocker.patch(VIEWS + '.TopicButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_topic',
                     return_value=('stream', 'topic'))

        mid_col_view.keypress(size, key)

        mid_col_view.get_next_unread_topic.assert_called_once_with()
        mid_col_view.controller.narrow_to_topic.assert_called_once_with(
            topic_btn('stream', 'topic', mid_col_view.model)
        )

    def test_keypress_n_no_stream(self, mid_col_view, mocker):
        key = "n"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        topic_btn = mocker.patch(VIEWS + '.TopicButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_topic',
                     return_value=None)

        return_value = mid_col_view.keypress(size, key)
        assert return_value == 'n'

    def test_keypress_p_stream(self, mid_col_view, mocker):
        key = "p"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        pm_btn = mocker.patch(VIEWS + '.UnreadPMButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_pm',
                     return_value=1)
        mid_col_view.model.user_id_email_dict = {1: "EMAIL"}

        mid_col_view.keypress(size, key)

        mid_col_view.controller.narrow_to_user.assert_called_once_with(
            pm_btn(1, 'EMAIL')
        )

    def test_keypress_p_no_pm(self, mid_col_view, mocker):
        key = "p"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        pm_btn = mocker.patch(VIEWS + '.UnreadPMButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_pm',
                     return_value=None)

        return_value = mid_col_view.keypress(size, key)
        assert return_value == 'p'

    def test_keypress_x(self, mid_col_view, mocker):
        key = "x"
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        pm_btn = mocker.patch(VIEWS + '.UnreadPMButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_pm',
                     return_value=None)
        mid_col_view.footer = mocker.Mock()
        return_value = mid_col_view.keypress(size, key)
        mid_col_view.footer.private_box_view.assert_called_once_with()
        assert mid_col_view.footer.focus_position == 0
        assert return_value == 'x'


class TestRightColumnView:

    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.view = mocker.Mock()
        self.user_search = mocker.patch(VIEWS + ".UserSearchBox")
        self.connect_signal = mocker.patch(VIEWS + ".urwid.connect_signal")
        self.line_box = mocker.patch(VIEWS + ".urwid.LineBox")
        self.thread = mocker.patch(VIEWS + ".threading")
        self.super = mocker.patch(VIEWS + ".urwid.Frame.__init__")

    @pytest.fixture
    def right_col_view(self, mocker):
        mocker.patch(VIEWS + ".RightColumnView.users_view")
        return RightColumnView(self.view)

    def test_init(self, right_col_view):
        assert right_col_view.view == self.view
        assert right_col_view.user_search == self.user_search(right_col_view)
        assert right_col_view.view.user_search == right_col_view.user_search
        self.thread.Lock.assert_called_with()
        assert right_col_view.search_lock == self.thread.Lock()
        self.super.assert_called_once_with(right_col_view.users_view(),
                                           header=self.line_box(
                                               right_col_view.user_search
        ))

    def test_update_user_list_editor_mode(self, right_col_view):
        right_col_view.view.controller.editor_mode = False
        right_col_view.update_user_list("SEARCH_BOX", "NEW_TEXT")
        right_col_view.search_lock.acquire.assert_not_called()

    def test_update_user_list_user_match(self, right_col_view, mocker):
        right_col_view.view.controller.editor_mode = True
        right_col_view.users_btn_list = ["USER1", "USER2"]
        mocker.patch(VIEWS + ".match_user", return_value=True)
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list("SEARCH_BOX", "F")

        right_col_view.search_lock.acquire.assert_called_once_with()
        list_w.assert_called_once_with(["USER1", "USER2"])
        set_body.assert_called_once_with(right_col_view.body)

    def test_update_user_list_no_user_match(self, right_col_view, mocker):
        right_col_view.view.controller.editor_mode = True
        right_col_view.users_btn_list = ["USER1", "USER2"]
        mocker.patch(VIEWS + ".match_user", return_value=False)
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list("SEARCH_BOX", "F")

        right_col_view.search_lock.acquire.assert_called_once_with()
        list_w.assert_called_once_with([])
        set_body.assert_called_once_with(right_col_view.body)

    def test_users_view(self, mocker):
        self.view.users = [{
            'user_id': 1,
            'status': 'active'
        }]
        self.view.model.unread_counts.get.return_value = 1
        user_btn = mocker.patch(VIEWS + ".UserButton")
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")

        right_col_view = RightColumnView(self.view)

        right_col_view.view.model.unread_counts.get.assert_called_once_with(1,
                                                                            0)
        user_btn.assert_called_once_with(
            self.view.users[0],
            controller=self.view.controller,
            view=self.view,
            color=self.view.users[0]['status'],
            count=1
        )
        list_w.assert_called_once_with(right_col_view.users_btn_list)

    def test_keypress_w(self, right_col_view, mocker):
        key = 'w'
        size = (20,)
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        right_col_view.keypress(size, key)
        right_col_view.set_focus.assert_called_once_with('header')

    def test_keypress_esc(self, right_col_view, mocker):
        key = 'esc'
        size = (20,)
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        mocker.patch(VIEWS + ".RightColumnView.set_body")
        right_col_view.users_btn_list = []

        right_col_view.keypress(size, key)

        right_col_view.user_search.set_edit_text.assert_called_once_with(
            "Search People"
        )
        right_col_view.set_body.assert_called_once_with(right_col_view.body)
        right_col_view.set_focus.assert_called_once_with('body')
        list_w.assert_called_once_with([])


class TestLeftColumnView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()
        self.view.model.unread_counts = {
            'all_msg': 2,
            'all_pms': 0,
            86: 1,
            14: 1,
            99: 1,
        }
        self.view.controller = mocker.Mock()
        self.super_mock = mocker.patch(VIEWS + ".urwid.Pile.__init__")

    def test_menu_view(self, mocker):
        self.streams_view = mocker.patch(
            VIEWS + ".LeftColumnView.streams_view")
        home_button = mocker.patch(VIEWS + ".HomeButton")
        pm_button = mocker.patch(VIEWS + ".PMButton")
        mocker.patch(VIEWS + ".urwid.ListBox")
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        left_col_view = LeftColumnView(self.view)
        home_button.assert_called_once_with(left_col_view.controller,
                                            count=2)
        pm_button.assert_called_once_with(left_col_view.controller,
                                          count=0)

    @pytest.mark.parametrize('pinned', [
        set(), {86}, {14}, {99}, {14, 99}, {99, 86}, {14, 86}, {14, 99, 86}
    ])
    def test_streams_view(self, mocker, streams, pinned):
        self.view.unpinned_streams = [s for s in streams if s[1] not in pinned]
        self.view.pinned_streams = [s for s in streams if s[1] in pinned]
        stream_button = mocker.patch(VIEWS + '.StreamButton')
        stream_view = mocker.patch(VIEWS + '.StreamsView')
        line_box = mocker.patch(VIEWS + '.urwid.LineBox')
        divider = mocker.patch(VIEWS + '.urwid.Divider')

        left_col_view = LeftColumnView(self.view)

        if pinned:
            divider.assert_called_once_with('-')
        else:
            divider.assert_not_called()

        stream_button.assert_has_calls(
            [mocker.call(stream,
                         controller=self.view.controller,
                         view=self.view,
                         count=1)
             for stream in (self.view.pinned_streams +
                            self.view.unpinned_streams)])


class TestHelpMenu:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        self.help_view = HelpView(self.controller)

    def test_keypress_any_key(self):
        key = "a"
        size = (200, 20)
        self.help_view.keypress(size, key)
        assert not self.controller.exit_help.called

    def test_keypress_q(self):
        key = "q"
        size = (200, 20)
        self.help_view.keypress(size, key)
        assert self.controller.exit_help.called


class TestMessageBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.model = mocker.Mock()

    @pytest.mark.parametrize('message_type, set_fields', [
        ('stream', [('caption', ''), ('stream_id', None), ('title', '')]),
        ('private', [('email', ''), ('user_id', None)]),
    ])
    def test_init(self, mocker, message_type, set_fields):
        mocker.patch.object(MessageBox, 'main_view')
        message = dict(display_recipient=['x'], stream_id=5, subject='hi',
                       sender_email='foo@zulip.com', sender_id=4209,
                       type=message_type)

        msg_box = MessageBox(message, self.model, None)

        assert msg_box.last_message == defaultdict(dict)
        for field, invalid_default in set_fields:
            assert getattr(msg_box, field) != invalid_default

    def test_init_fails_with_bad_message_type(self):
        message = dict(type='BLAH')

        with pytest.raises(RuntimeError):
            msg_box = MessageBox(message, self.model, None)

    @pytest.mark.parametrize('content, markup', [
        ('<p>hi</p>', ['', 'hi']),
        ('<span class="user-mention">@Bob Smith', [('span', '@Bob Smith')]),
        ('<span class="user-group-mention">@A Group', [('span', '@A Group')]),
        ('<code>some code', [('code', 'some code')]),
        ('<div class="codehilite">some code', [('code', 'some code')]),
        ('<strong>Something', [('bold', 'Something')]),
        ('<em>Something', [('bold', 'Something')]),
        ('<blockquote>stuff', [('blockquote', ['', 'stuff'])]),
        ('<div class="message_embed">',
            ['[EMBEDDED CONTENT NOT RENDERED]']),  # FIXME Unsupported
        ('<a href="foo">foo</a>', ['foo']),  # FIXME? Render with link style?
        ('<a href="foo">bar</a>', [('link', '[bar](foo)')]),
        ('<a href="/user_uploads/blah"',
            [('link', '[](SOME_BASE_URL/user_uploads/blah)')]),
        ('<li>Something', ['  * ', '', 'Something']),
        ('<li>Something<li>else',  # NOTE Real items are newline-separated?
            ['  * ', '', 'Something', '  * ', '', 'else']),
        ('<br>', []), ('<br/>', []),
        ('<hr>', ['[RULER NOT RENDERED]']),
        ('<hr/>', ['[RULER NOT RENDERED]']),
        ('<img>', ['[IMAGE NOT RENDERED]']),
        ('<img/>', ['[IMAGE NOT RENDERED]']),
        ('<table>stuff</table>', ['[TABLE NOT RENDERED]']),
        ('<span class="katex-display">some-math</span>', ['some-math']),
        ('<span class="katex">some-math</span>', ['some-math']),
        ('<ul><li>text</li></ul>', ['', '  * ', '', 'text']),
        ('<del>text</del>', ['', 'text']),  # FIXME Strikethrough
        ('<div class="message_inline_image">blah</div>', []),
        ('<div class="message_inline_ref">blah</div>', []),
        ('<span class="emoji">:smile:</span>', [':smile:']),
        ('<div class="inline-preview-twitter"',
            ['[TWITTER PREVIEW NOT RENDERED]']),
    ], ids=[
        'p', 'user-mention', 'group-mention', 'code', 'codehilite',
        'strong', 'em', 'blockquote',
        'embedded_content', 'link_sametext', 'link_differenttext',
        'link_userupload', 'listitem', 'listitems',
        'br', 'br2', 'hr', 'hr2', 'img', 'img2', 'table', 'math', 'math2',
        'ul', 'strikethrough_del', 'inline_image', 'inline_ref',
        'emoji', 'preview-twitter'
    ])
    def test_soup2markup(self, content, markup):
        message = dict(display_recipient=['x'], stream_id=5, subject='hi',
                       sender_email='foo@zulip.com', sender_id=4209,
                       type='stream',  # NOTE Output should not vary with PM
                       flags=[], content=content, sender_full_name='bob smith',
                       timestamp=99, reactions=[])
        self.model.stream_dict = {
            5: {  # matches stream_id above
                'color': '#bfd56f',
            },
        }
        self.model.client.base_url = "SOME_BASE_URL"
        # NOTE Absence of previous (last) message should not affect markup
        msg_box = MessageBox(message, self.model, None)

        soup = BeautifulSoup(message['content'], 'lxml').find(name='body')
        assert msg_box.soup2markup(soup) == [''] + markup

    @pytest.mark.parametrize('message, last_message', [
        ({
            'sender_id': 1,
            'display_recipient': 'Verona',
            'sender_full_name': 'aaron',
            'submessages': [],
            'stream_id': 5,
            'subject': 'Verona2',
            'id': 37,
            'subject_links': [],
            'recipient_id': 20,
            'content': "<p>It's nice and it feels more modern, but I think"
                       " this will take some time to get used to</p>",
            'timestamp': 1531716583,
            'sender_realm_str': 'zulip',
            'client': 'populate_db',
            'content_type': 'text/html',
            'reactions': [],
            'type': 'stream',
            'is_me_message': False,
            'sender_short_name': 'aaron',
            'flags': ['read'],
            'sender_email': 'AARON@zulip.com'
        }, None),
        ({
            'sender_id': 5,
            'display_recipient': [{
                'is_mirror_dummy': False,
                'short_name': 'aaron',
                'email': 'AARON@zulip.com',
                'id': 1,
                'full_name': 'aaron'
            }, {
                'is_mirror_dummy': False,
                'short_name': 'iago',
                'email': 'iago@zulip.com',
                'id': 5,
                'full_name': 'Iago'
            }],
            'sender_full_name': 'Iago',
            'submessages': [],
            'subject': '',
            'id': 107,
            'subject_links': [],
            'recipient_id': 1,
            'content': '<p>what are you planning to do this week</p>',
            'timestamp': 1532103879,
            'sender_realm_str': 'zulip',
            'client': 'ZulipTerminal',
            'content_type': 'text/html',
            'reactions': [],
            'type': 'private',
            'is_me_message': False,
            'sender_short_name': 'iago',
            'flags': ['read'],
            'sender_email': 'iago@zulip.com'
        }, None)
    ])
    def test_main_view(self, mocker, message, last_message):
        self.model.stream_dict = {
            5: {
                'color': '#bfd56f',
            },
        }
        msg_box = MessageBox(message, self.model, last_message)

    @pytest.mark.parametrize('message', [
        {
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('to_vary_in_last_message', [
            {'display_recipient': 'Verona offtopic'},
            {'subject': 'Test topic (previous)'},
            {'type': 'private'},
    ], ids=['different_stream_before', 'different_topic_before', 'PM_before'])
    def test_main_view_generates_stream_header(self, mocker, message,
                                               to_vary_in_last_message):
        mocker.patch(VIEWS + ".urwid.Text")
        self.model.stream_dict = {
            5: {
                'color': '#bfd56f',
            },
        }
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3
        assert isinstance(view_components[0], AttrWrap)
        assert view_components[0].get_attr() == 'bar'
        assert isinstance(view_components[1], Columns)
        assert isinstance(view_components[2], Padding)

    @pytest.mark.parametrize('message', [
        {
            'type': 'private',
            'sender_email': 'iago@zulip.com',
            'sender_id': 5,
            'display_recipient': [{
                'email': 'AARON@zulip.com',
                'id': 1,
                'full_name': 'aaron'
            }, {
                'email': 'iago@zulip.com',
                'id': 5,
                'full_name': 'Iago'
            }],
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        },
    ])
    @pytest.mark.parametrize('to_vary_in_last_message', [
            {
                'display_recipient': [{
                    'email': 'AARON@zulip.com',
                    'id': 1,
                    'full_name': 'aaron'
                }, {
                    'email': 'iago@zulip.com',
                    'id': 5,
                    'full_name': 'Iago'
                }, {
                    'email': 'SE@zulip.com',
                    'id': 6,
                    'full_name': 'Someone Else'
                }],
            },
            {'type': 'stream'},
    ], ids=['larger_pm_group', 'stream_before'])
    def test_main_view_generates_PM_header(self, mocker, message,
                                           to_vary_in_last_message):
        mocker.patch(VIEWS + ".urwid.Text")
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3
        assert isinstance(view_components[0], AttrWrap)
        assert view_components[0].get_attr() == 'bar'
        assert isinstance(view_components[1], Columns)
        assert isinstance(view_components[2], Padding)

    # Assume recipient (PM/stream/topic) header is unchanged below
    @pytest.mark.parametrize('message', [
        {
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('starred_msg', ['this', 'last', 'neither'],
                             ids=['this_starred', 'last_starred', 'no_stars'])
    @pytest.mark.parametrize('expected_header, to_vary_in_last_message', [
        (['alice', ' ', 'DAYDATETIME'], {'sender_full_name': 'bob'}),
        ([' ', ' ', 'DAYDATETIME'], {'timestamp': 1532103779}),  # 100 earlier
        (['alice', ' ', 'DAYDATETIME'], {'timestamp': 0}),  # much earlier!
    ], ids=['author_different', 'earlier_message', 'much_earlier_message'])
    def test_main_view_content_header_without_header(self, mocker, message,
                                                     expected_header,
                                                     starred_msg,
                                                     to_vary_in_last_message):
        stars = {msg: ({'flags': ['starred']} if msg == starred_msg else {})
                 for msg in ('this', 'last')}
        this_msg = dict(message, **stars['this'])
        all_to_vary = dict(to_vary_in_last_message, **stars['last'])
        last_msg = dict(message, **all_to_vary)
        msg_box = MessageBox(this_msg, self.model, last_msg)
        expected_header[1] = '*' if starred_msg == 'this' else ' '
        expected_header[2] = msg_box._time_for_message(message)

        view_components = msg_box.main_view()
        assert len(view_components) == 2
        assert isinstance(view_components[0], Columns)
        assert ([w.text for w in view_components[0].widget_list] ==
                expected_header)
        assert isinstance(view_components[1], Padding)

    @pytest.mark.parametrize('message', [
        {
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'alice',
            'timestamp': 1532103879,
        },
        {
            'type': 'private',
            'sender_email': 'iago@zulip.com',
            'sender_id': 5,
            'display_recipient': [{
                'email': 'AARON@zulip.com',
                'id': 1,
                'full_name': 'aaron'
            }, {
                'email': 'iago@zulip.com',
                'id': 5,
                'full_name': 'Iago'
            }],
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'sender_full_name': 'bob'},
        {'timestamp': 1532103779},
        {'timestamp': 0},
        {},
        {'flags': ['starred']},
    ], ids=['common_author', 'common_timestamp', 'common_early_timestamp',
            'common_unchanged_message', 'both_starred'])
    def test_main_view_compact_output(self, mocker, message,
                                      to_vary_in_each_message):
        varied_message = dict(message, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, varied_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 1
        assert isinstance(view_components[0], Padding)
