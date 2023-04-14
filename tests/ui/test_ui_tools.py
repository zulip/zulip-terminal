from collections import OrderedDict

import pytest
import urwid
from pytest import param as case
from urwid import Divider

from zulipterminal.config.keys import keys_for_command, primary_key_for_command
from zulipterminal.config.symbols import STATUS_ACTIVE
from zulipterminal.helper import powerset
from zulipterminal.ui_tools.views import (
    SIDE_PANELS_MOUSE_SCROLL_LINES,
    LeftColumnView,
    MessageView,
    MiddleColumnView,
    ModListWalker,
    RightColumnView,
    StreamsView,
    StreamsViewDivider,
    TabView,
    TopicsView,
    UsersView,
)


SUBDIR = "zulipterminal.ui_tools"
VIEWS = SUBDIR + ".views"
MESSAGEVIEW = VIEWS + ".MessageView"
MIDCOLVIEW = VIEWS + ".MiddleColumnView"


class TestModListWalker:
    @pytest.fixture
    def mod_walker(self, mocker):
        read_message = mocker.Mock(spec=lambda: None)
        return ModListWalker(contents=[list(range(1))], action=read_message)

    @pytest.mark.parametrize(
        "num_items, focus_position",
        [
            (5, 0),
            (0, 0),
        ],
    )
    def test_extend(self, num_items, focus_position, mod_walker, mocker):
        items = list(range(num_items))
        mocker.patch.object(mod_walker, "_set_focus")
        mod_walker.extend(items)
        mod_walker._set_focus.assert_called_once_with(focus_position)

    def test__set_focus(self, mod_walker, mocker):
        mod_walker._action.assert_not_called()
        mod_walker._set_focus(0)
        mod_walker._action.assert_called_once_with()

    def test_set_focus(self, mod_walker, mocker):
        mod_walker._action.assert_not_called()
        mod_walker.set_focus(0)
        mod_walker._action.assert_called_once_with()


class TestMessageView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.model = mocker.MagicMock()
        self.view = mocker.Mock()
        self.urwid = mocker.patch(VIEWS + ".urwid")

    @pytest.fixture
    def msg_view(self, mocker, msg_box):
        mocker.patch(MESSAGEVIEW + ".main_view", return_value=[msg_box])
        mocker.patch(MESSAGEVIEW + ".read_message")
        mocker.patch(MESSAGEVIEW + ".set_focus")
        msg_view = MessageView(self.model, self.view)
        msg_view.log = mocker.Mock()
        msg_view.body = mocker.Mock()
        return msg_view

    def test_init(self, mocker, msg_view, msg_box):
        assert msg_view.model == self.model
        msg_view.set_focus.assert_called_once_with(0)
        assert msg_view.old_loading is False
        assert msg_view.new_loading is False

    @pytest.mark.parametrize(
        "narrow_focus_pos, expected_focus_msg", [(None, 1), (0, 0)]
    )
    def test_main_view(self, mocker, narrow_focus_pos, expected_focus_msg):
        mocker.patch(MESSAGEVIEW + ".read_message")
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(MESSAGEVIEW + ".set_focus")
        msg_list = ["MSG1", "MSG2"]
        mocker.patch(VIEWS + ".create_msg_box_list", return_value=msg_list)
        self.model.get_focus_in_current_narrow.return_value = narrow_focus_pos

        msg_view = MessageView(self.model, self.view)

        assert msg_view.focus_msg == expected_focus_msg

    @pytest.mark.parametrize(
        "messages_fetched",
        [
            {},
            {201: "M1"},
            OrderedDict([(201, "M1"), (202, "M2")]),
        ],
    )
    @pytest.mark.parametrize(
        "ids_in_narrow",
        [
            set(),
            {0},  # Shouldn't apply to empty log case?
        ],
    )
    def test_load_old_messages_empty_log(
        self, mocker, msg_view, ids_in_narrow, messages_fetched
    ):
        # Expand parameters to use in test
        new_msg_ids = set(messages_fetched.keys())
        new_msg_widgets = list(messages_fetched.values())

        mocker.patch.object(
            msg_view.model,
            "get_message_ids_in_current_narrow",
            side_effect=[ids_in_narrow, ids_in_narrow | new_msg_ids],
        )

        create_msg_box_list = mocker.patch(
            VIEWS + ".create_msg_box_list", return_value=new_msg_widgets
        )
        # Specific to this version of the test
        msg_view.log = []

        msg_view.load_old_messages(0)

        assert msg_view.old_loading is False
        assert msg_view.log == list(messages_fetched.values())  # code vs orig
        if messages_fetched:
            create_msg_box_list.assert_called_once_with(msg_view.model, new_msg_ids)
            self.model.controller.update_screen.assert_called_once_with()
        else:
            create_msg_box_list.assert_not_called()
            self.model.controller.update_screen.assert_not_called()
        self.model.get_messages.assert_called_once_with(
            num_before=30, num_after=0, anchor=0
        )

    @pytest.mark.parametrize(
        "messages_fetched",
        [
            {},
            {201: "M1"},
            OrderedDict([(201, "M1"), (202, "M2")]),
        ],
    )
    @pytest.mark.parametrize(
        "top_id_in_narrow, other_ids_in_narrow",
        [
            (99, set()),
            (99, {101}),
            (99, {101, 103}),
        ],
    )
    def test_load_old_messages_mocked_log(
        self, mocker, msg_view, top_id_in_narrow, other_ids_in_narrow, messages_fetched
    ):
        # Expand parameters to use in test
        new_msg_ids = set(messages_fetched.keys())
        new_msg_widgets = list(messages_fetched.values())

        # Parameter constraints
        assert top_id_in_narrow not in other_ids_in_narrow
        assert top_id_in_narrow not in new_msg_ids
        assert other_ids_in_narrow & new_msg_ids == set()

        top_widget = mocker.Mock()
        top_widget.original_widget.message = {"id": top_id_in_narrow}

        ids_in_narrow = {top_id_in_narrow} | other_ids_in_narrow
        mocker.patch.object(
            msg_view.model,
            "get_message_ids_in_current_narrow",
            side_effect=[ids_in_narrow, ids_in_narrow | new_msg_ids],
        )
        create_msg_box_list = mocker.patch(
            VIEWS + ".create_msg_box_list",
            return_value=(new_msg_widgets + [top_widget]),
        )
        initial_log = [top_widget] + len(other_ids_in_narrow) * ["existing"]
        msg_view.log = initial_log[:]

        msg_view.load_old_messages(0)

        assert msg_view.old_loading is False
        assert msg_view.log == new_msg_widgets + initial_log
        if messages_fetched:
            create_msg_box_list.assert_called_once_with(
                msg_view.model, {top_id_in_narrow} | new_msg_ids
            )
            self.model.controller.update_screen.assert_called_once_with()
        else:
            create_msg_box_list.assert_not_called()
            self.model.controller.update_screen.assert_not_called()
        self.model.get_messages.assert_called_once_with(
            num_before=30, num_after=0, anchor=0
        )

    # FIXME: Improve this test by covering more parameters
    @pytest.mark.parametrize(
        "ids_in_narrow",
        [
            ({0}),
        ],
    )
    def test_load_new_messages_empty_log(self, mocker, msg_view, ids_in_narrow):
        mocker.patch.object(
            msg_view.model,
            "get_message_ids_in_current_narrow",
            return_value=ids_in_narrow,
        )
        create_msg_box_list = mocker.patch(
            VIEWS + ".create_msg_box_list", return_value=["M1", "M2"]
        )
        msg_view.log = []

        msg_view.load_new_messages(0)

        assert msg_view.new_loading is False
        assert msg_view.log == ["M1", "M2"]
        create_msg_box_list.assert_called_once_with(
            msg_view.model, set(), last_message=None
        )
        self.model.controller.update_screen.assert_called_once_with()
        self.model.get_messages.assert_called_once_with(
            num_before=0, num_after=30, anchor=0
        )

    # FIXME: Improve this test by covering more parameters
    @pytest.mark.parametrize(
        "ids_in_narrow",
        [
            ({0}),
        ],
    )
    def test_load_new_messages_mocked_log(self, mocker, msg_view, ids_in_narrow):
        mocker.patch.object(
            msg_view.model,
            "get_message_ids_in_current_narrow",
            return_value=ids_in_narrow,
        )
        create_msg_box_list = mocker.patch(
            VIEWS + ".create_msg_box_list", return_value=["M1", "M2"]
        )
        msg_view.log = [mocker.Mock()]

        msg_view.load_new_messages(0)

        assert msg_view.new_loading is False
        assert msg_view.log[-2:] == ["M1", "M2"]
        expected_last_msg = msg_view.log[0].original_widget.message
        create_msg_box_list.assert_called_once_with(
            msg_view.model, set(), last_message=expected_last_msg
        )
        self.model.controller.update_screen.assert_called_once_with()
        self.model.get_messages.assert_called_once_with(
            num_before=0, num_after=30, anchor=0
        )

    def test_mouse_event(self, mocker, msg_view, mouse_scroll_event, widget_size):
        event, button, keypress = mouse_scroll_event
        mocker.patch.object(msg_view, "keypress")
        size = widget_size(msg_view)
        msg_view.mouse_event(size, event, button, 0, 0, mocker.Mock())
        msg_view.keypress.assert_called_once_with(size, keypress)

    @pytest.mark.parametrize("key", keys_for_command("GO_DOWN"))
    def test_keypress_GO_DOWN(self, mocker, msg_view, key, widget_size):
        size = widget_size(msg_view)
        msg_view.new_loading = False
        mocker.patch(MESSAGEVIEW + ".focus_position", return_value=0)
        mocker.patch(MESSAGEVIEW + ".set_focus_valign")
        msg_view.log.next_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.next_position.assert_called_once_with(msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, "above")
        msg_view.set_focus_valign.assert_called_once_with("middle")

    @pytest.mark.parametrize("view_is_focused", [True, False])
    @pytest.mark.parametrize("key", keys_for_command("GO_DOWN"))
    def test_keypress_GO_DOWN_exception(
        self, mocker, msg_view, key, widget_size, view_is_focused
    ):
        size = widget_size(msg_view)
        msg_view.new_loading = False
        mocker.patch(MESSAGEVIEW + ".focus_position", return_value=0)
        mocker.patch(MESSAGEVIEW + ".set_focus_valign")

        msg_view.log.next_position = Exception()
        mocker.patch(
            MESSAGEVIEW + ".focus",
            mocker.MagicMock() if view_is_focused else None,
        )
        mocker.patch.object(msg_view, "load_new_messages")

        return_value = msg_view.keypress(size, key)

        if view_is_focused:
            msg_view.load_new_messages.assert_called_once_with(
                msg_view.focus.original_widget.message["id"],
            )
        else:
            msg_view.load_new_messages.assert_not_called()
        assert return_value == key

    @pytest.mark.parametrize("key", keys_for_command("GO_UP"))
    def test_keypress_GO_UP(self, mocker, msg_view, key, widget_size):
        size = widget_size(msg_view)
        mocker.patch(MESSAGEVIEW + ".focus_position", return_value=0)
        mocker.patch(MESSAGEVIEW + ".set_focus_valign")
        msg_view.old_loading = False
        msg_view.log.prev_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.prev_position.assert_called_once_with(msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, "below")
        msg_view.set_focus_valign.assert_called_once_with("middle")

    @pytest.mark.parametrize("view_is_focused", [True, False])
    @pytest.mark.parametrize("key", keys_for_command("GO_UP"))
    def test_keypress_GO_UP_exception(
        self, mocker, msg_view, key, widget_size, view_is_focused
    ):
        size = widget_size(msg_view)
        msg_view.old_loading = False
        mocker.patch(MESSAGEVIEW + ".focus_position", return_value=0)
        mocker.patch(MESSAGEVIEW + ".set_focus_valign")

        msg_view.log.prev_position = Exception()
        mocker.patch(
            MESSAGEVIEW + ".focus",
            mocker.MagicMock() if view_is_focused else None,
        )
        mocker.patch.object(msg_view, "load_old_messages")

        return_value = msg_view.keypress(size, key)

        if view_is_focused:
            msg_view.load_old_messages.assert_called_once_with(
                msg_view.focus.original_widget.message["id"],
            )
        else:
            msg_view.load_old_messages.assert_not_called()
        assert return_value == key

    def test_read_message(self, mocker, msg_box):
        mocker.patch(MESSAGEVIEW + ".main_view", return_value=[msg_box])
        self.urwid.SimpleFocusListWalker.return_value = mocker.Mock()
        mocker.patch(MESSAGEVIEW + ".set_focus")
        mocker.patch(MESSAGEVIEW + ".update_search_box_narrow")
        msg_view = MessageView(self.model, self.view)
        msg_view.model.is_search_narrow = lambda: False
        msg_view.model.controller.in_explore_mode = False
        msg_view.log = mocker.Mock()
        msg_view.body = mocker.Mock()
        msg_w = mocker.MagicMock()
        msg_view.model.controller.view = mocker.Mock()
        msg_view.model.controller.view.body.focus_col = 1
        msg_w.attr_map = {None: "unread"}
        msg_w.original_widget.message = {"id": 1}
        msg_w.set_attr_map.return_value = None
        msg_view.body.get_focus.return_value = (msg_w, 0)
        msg_view.body.get_prev.return_value = (None, 1)
        msg_view.model.narrow = []
        msg_view.model.index = {
            "messages": {
                1: {
                    "flags": [],
                }
            },
            "pointer": {"[]": 0},
        }
        mocker.patch(MESSAGEVIEW + ".focus_position")
        msg_view.focus_position = 1
        msg_view.model.controller.view.body.focus_col = 1
        msg_view.log = list(msg_view.model.index["messages"])
        msg_view.read_message()
        assert msg_view.update_search_box_narrow.called
        assert msg_view.model.index["messages"][1]["flags"] == ["read"]
        self.model.mark_message_ids_as_read.assert_called_once_with([1])

    def test_message_calls_search_and_header_bar(self, mocker, msg_view):
        msg_w = mocker.MagicMock()
        msg_w.original_widget.message = {"id": 1}
        msg_view.update_search_box_narrow(msg_w.original_widget)
        msg_w.original_widget.recipient_header.assert_called_once_with()
        msg_w.original_widget.top_search_bar.assert_called_once_with()

    def test_read_message_no_msgw(self, mocker, msg_view):
        # MSG_W is NONE CASE
        msg_view.body.get_focus.return_value = (None, 0)

        msg_view.read_message()

        self.model.mark_message_ids_as_read.assert_not_called()

    def test_read_message_in_explore_mode(self, mocker, msg_box):
        mocker.patch(MESSAGEVIEW + ".main_view", return_value=[msg_box])
        mocker.patch(MESSAGEVIEW + ".set_focus")
        mocker.patch(MESSAGEVIEW + ".update_search_box_narrow")
        msg_view = MessageView(self.model, self.view)
        msg_w = mocker.Mock()
        msg_view.body = mocker.Mock()
        msg_view.body.get_focus.return_value = (msg_w, 0)
        msg_view.model.is_search_narrow = lambda: False
        msg_view.model.controller.in_explore_mode = True

        msg_view.read_message()

        assert msg_view.update_search_box_narrow.called
        assert not self.model.mark_message_ids_as_read.called

    def test_read_message_search_narrow(self, mocker, msg_box):
        mocker.patch(MESSAGEVIEW + ".main_view", return_value=[msg_box])
        mocker.patch(MESSAGEVIEW + ".set_focus")
        mocker.patch(MESSAGEVIEW + ".update_search_box_narrow")
        msg_view = MessageView(self.model, self.view)
        msg_view.model.controller.view = mocker.Mock()
        msg_w = mocker.Mock()
        msg_view.body = mocker.Mock()
        msg_view.body.get_focus.return_value = (msg_w, 0)
        msg_view.model.is_search_narrow = lambda: True
        msg_view.model.controller.in_explore_mode = False

        msg_view.read_message()

        assert msg_view.update_search_box_narrow.called
        assert not self.model.mark_message_ids_as_read.called

    def test_read_message_last_unread_message_focused(
        self, mocker, message_fixture, empty_index, msg_box
    ):
        mocker.patch(MESSAGEVIEW + ".main_view", return_value=[msg_box])
        mocker.patch(MESSAGEVIEW + ".set_focus")
        msg_view = MessageView(self.model, self.view)
        msg_view.model.is_search_narrow = lambda: False
        msg_view.model.controller.in_explore_mode = False
        msg_view.log = [0, 1]
        msg_view.body = mocker.Mock()
        msg_view.update_search_box_narrow = mocker.Mock()

        self.model.controller.view = mocker.Mock()
        self.model.controller.view.body.focus_col = 0
        self.model.index = empty_index

        msg_w = mocker.Mock()
        msg_w.attr_map = {None: "unread"}
        msg_w.original_widget.message = message_fixture

        msg_view.body.get_focus.return_value = (msg_w, 1)
        msg_view.body.get_prev.return_value = (None, 0)
        msg_view.read_message(1)
        self.model.mark_message_ids_as_read.assert_called_once_with(
            [message_fixture["id"]]
        )


class TestStreamsViewDivider:
    def test_init(self):
        streams_view_divider = StreamsViewDivider()

        assert isinstance(streams_view_divider, Divider)
        assert streams_view_divider.stream_id == -1
        assert streams_view_divider.stream_name == ""


class TestStreamsView:
    @pytest.fixture
    def stream_view(self, mocker):
        mocker.patch(VIEWS + ".threading.Lock")
        self.view = mocker.Mock()
        self.stream_search_box = mocker.patch(VIEWS + ".PanelSearchBox")
        stream_btn = mocker.Mock()
        stream_btn.stream_name = "FOO"
        self.streams_btn_list = [stream_btn]
        return StreamsView(self.streams_btn_list, view=self.view)

    def test_init(self, mocker, stream_view):
        assert stream_view.view == self.view
        assert stream_view.streams_btn_list == self.streams_btn_list
        assert stream_view.stream_search_box
        self.stream_search_box.assert_called_once_with(
            stream_view, "SEARCH_STREAMS", stream_view.update_streams
        )

    @pytest.mark.parametrize(
        "new_text, expected_log, to_pin",
        [
            # NOTE: '' represents StreamsViewDivider's stream name.
            ("f", ["fan", "FOO", "foo", "FOOBAR"], []),
            ("bar", ["bar"], []),
            ("foo", ["FOO", "foo", "FOOBAR"], []),
            ("FOO", ["FOO", "foo", "FOOBAR"], []),
            ("test", ["test here"], []),
            ("here", ["test here"], []),
            ("test here", ["test here"], []),
            # With 'foo' pinned.
            ("f", ["foo", "", "fan", "FOO", "FOOBAR"], ["foo"]),
            ("FOO", ["foo", "", "FOO", "FOOBAR"], ["foo"]),
            # With 'bar' pinned.
            ("bar", ["bar"], ["bar"]),
            ("baar", "search error", []),
        ],
    )
    def test_update_streams(self, mocker, stream_view, new_text, expected_log, to_pin):
        stream_names = ["FOO", "FOOBAR", "foo", "fan", "boo", "BOO", "bar", "test here"]
        stream_names.sort(key=lambda stream_name: stream_name.lower())
        self.view.pinned_streams = [{"name": name} for name in to_pin]
        stream_names.sort(
            key=lambda stream_name: stream_name in to_pin,
            reverse=True,
        )
        self.view.controller.is_in_editor_mode = lambda: True
        search_box = stream_view.stream_search_box
        stream_view.streams_btn_list = [
            mocker.Mock(stream_name=stream_name) for stream_name in stream_names
        ]
        stream_view.update_streams(search_box, new_text)
        if expected_log != "search error":
            assert [stream.stream_name for stream in stream_view.log] == expected_log
        else:
            assert hasattr(stream_view.log[0].original_widget, "text")
        self.view.controller.update_screen.assert_called_once_with()

    def test_mouse_event(self, mocker, stream_view, mouse_scroll_event, widget_size):
        event, button, key = mouse_scroll_event
        stream_view_keypress = mocker.patch.object(stream_view, "keypress")
        size = widget_size(stream_view)
        col = 1
        row = 1
        focus = "WIDGET"
        stream_view.mouse_event(size, event, button, col, row, focus)
        stream_view_keypress.assert_has_calls(
            [mocker.call(size, key)] * SIDE_PANELS_MOUSE_SCROLL_LINES
        )

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_STREAMS"))
    def test_keypress_SEARCH_STREAMS(self, mocker, stream_view, key, widget_size):
        size = widget_size(stream_view)
        mocker.patch.object(stream_view, "set_focus")
        mocker.patch.object(stream_view.stream_search_box, "set_caption")
        stream_view.log.extend(["FOO", "foo", "fan", "boo", "BOO"])
        stream_view.log.set_focus(3)

        stream_view.keypress(size, key)

        assert stream_view.focus_index_before_search == 3
        stream_view.set_focus.assert_called_once_with("header")
        stream_view.stream_search_box.set_caption.assert_called_once_with(" ")
        self.view.controller.enter_editor_mode_with.assert_called_once_with(
            stream_view.stream_search_box
        )

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, mocker, stream_view, key, widget_size):
        size = widget_size(stream_view)
        mocker.patch.object(stream_view, "set_focus")
        mocker.patch(VIEWS + ".urwid.Frame.keypress")
        mocker.patch.object(stream_view.stream_search_box, "reset_search_text")
        stream_view.streams_btn_list = ["FOO", "foo", "fan", "boo", "BOO"]
        stream_view.focus_index_before_search = 3

        # Simulate search
        stream_view.log.clear()
        stream_view.log.extend(stream_view.streams_btn_list[3])
        stream_view.log.set_focus(0)
        stream_view.keypress(size, primary_key_for_command("GO_DOWN"))
        assert stream_view.log.get_focus()[1] != stream_view.focus_index_before_search

        # Exit search
        stream_view.keypress(size, key)

        # Check state reset after search
        stream_view.set_focus.assert_called_once_with("body")
        assert stream_view.stream_search_box.reset_search_text.called
        assert stream_view.log == stream_view.streams_btn_list
        assert stream_view.log.get_focus()[1] == stream_view.focus_index_before_search


class TestTopicsView:
    @pytest.fixture
    def topic_view(self, mocker, stream_button):
        self.stream_button = stream_button
        mocker.patch(VIEWS + ".threading.Lock")
        self.topic_search_box = mocker.patch(VIEWS + ".PanelSearchBox")
        self.view = mocker.Mock()
        self.view.controller = mocker.Mock()
        topic_btn = mocker.Mock()
        topic_btn.caption = "BOO"
        self.topics_btn_list = [topic_btn]
        self.header_list = mocker.patch(VIEWS + ".urwid.Pile")
        self.divider = mocker.patch(VIEWS + ".urwid.Divider")
        return TopicsView(self.topics_btn_list, self.view, self.stream_button)

    def test_init(self, mocker, topic_view):
        assert topic_view.stream_button == self.stream_button
        assert topic_view.view == self.view
        assert topic_view.topic_search_box
        self.topic_search_box.assert_called_once_with(
            topic_view, "SEARCH_TOPICS", topic_view.update_topics
        )
        self.header_list.assert_called_once_with(
            [
                topic_view.stream_button,
                self.divider("─"),
                topic_view.topic_search_box,
                self.divider("─"),
            ]
        )

    @pytest.mark.parametrize(
        "stream_id, saved_topic_state, expected_focus_index",
        [
            case(1, None, 0, id="initial_condition-no_topic_is_stored"),
            case(2, "Topic 3", 2, id="topic_is_stored_and_present_in_topic_list"),
            case(3, "Topic 4", 0, id="topic_is_stored_but_not_present_in_topic_list"),
        ],
    )
    def test__focus_position_for_topic_name(
        self, mocker, stream_id, saved_topic_state, topic_view, expected_focus_index
    ):
        topic_view.stream_button.stream_id = stream_id
        topic_view.list_box = mocker.MagicMock(spec=urwid.ListBox)
        topic_view.list_box.body = [
            mocker.Mock(topic_name="Topic 1"),
            mocker.Mock(topic_name="Topic 2"),
            mocker.Mock(topic_name="Topic 3"),
        ]
        topic_view.log = urwid.SimpleFocusListWalker(topic_view.list_box.body)
        mocker.patch.object(
            topic_view.view, "saved_topic_in_stream_id", return_value=saved_topic_state
        )

        topic_view.list_box.focus_position = topic_view._focus_position_for_topic_name()

        assert topic_view.list_box.focus_position == expected_focus_index

    @pytest.mark.parametrize(
        "new_text, expected_log",
        [
            ("f", ["FOO", "FOOBAR", "foo", "fan"]),
            ("a", ["FOOBAR", "fan", "bar"]),
            ("bar", ["FOOBAR", "bar"]),
            ("foo", ["FOO", "FOOBAR", "foo"]),
            ("FOO", ["FOO", "FOOBAR", "foo"]),
            ("(no", ["(no topic)"]),
            ("topic", ["(no topic)"]),
            ("cc", "search error"),
        ],
    )
    def test_update_topics(self, mocker, topic_view, new_text, expected_log):
        topic_names = ["FOO", "FOOBAR", "foo", "fan", "boo", "BOO", "bar", "(no topic)"]
        self.view.controller.is_in_editor_mode = lambda: True
        new_text = new_text
        search_box = topic_view.topic_search_box
        topic_view.topics_btn_list = [
            mocker.Mock(topic_name=topic_name) for topic_name in topic_names
        ]
        topic_view.update_topics(search_box, new_text)
        if expected_log != "search error":
            assert [topic.topic_name for topic in topic_view.log] == expected_log
        else:
            assert hasattr(topic_view.log[0].original_widget, "text")
        self.view.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize(
        "topic_name, topic_initial_log, topic_final_log",
        [
            ("TOPIC3", ["TOPIC2", "TOPIC3", "TOPIC1"], ["TOPIC3", "TOPIC2", "TOPIC1"]),
            ("TOPIC1", ["TOPIC1", "TOPIC2", "TOPIC3"], ["TOPIC1", "TOPIC2", "TOPIC3"]),
            (
                "TOPIC4",
                ["TOPIC1", "TOPIC2", "TOPIC3"],
                ["TOPIC4", "TOPIC1", "TOPIC2", "TOPIC3"],
            ),
            ("TOPIC1", [], ["TOPIC1"]),
        ],
        ids=[
            "reorder_topic3",
            "topic1_discussion_continues",
            "new_topic4",
            "first_topic_1",
        ],
    )
    def test_update_topics_list(
        self, mocker, topic_view, topic_name, topic_initial_log, topic_final_log
    ):
        mocker.patch(SUBDIR + ".buttons.TopButton.__init__", return_value=None)
        set_focus_valign = mocker.patch(VIEWS + ".urwid.ListBox.set_focus_valign")
        topic_view.view.controller.model.stream_dict = {86: {"name": "PTEST"}}
        topic_view.view.controller.model.is_muted_topic = mocker.Mock(
            return_value=False
        )
        topic_view.log = [
            mocker.Mock(topic_name=topic_name) for topic_name in topic_initial_log
        ]

        topic_view.update_topics_list(86, topic_name, 1001)
        assert [topic.topic_name for topic in topic_view.log] == topic_final_log
        set_focus_valign.assert_called_once_with("bottom")

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_TOPICS"))
    def test_keypress_SEARCH_TOPICS(self, mocker, topic_view, key, widget_size):
        size = widget_size(topic_view)
        mocker.patch(VIEWS + ".TopicsView.set_focus")
        mocker.patch.object(topic_view.topic_search_box, "set_caption")
        topic_view.log.extend(["FOO", "foo", "fan", "boo", "BOO"])
        topic_view.log.set_focus(3)

        topic_view.keypress(size, key)

        topic_view.set_focus.assert_called_once_with("header")
        topic_view.header_list.set_focus.assert_called_once_with(2)
        assert topic_view.focus_index_before_search == 3
        topic_view.topic_search_box.set_caption.assert_called_once_with(" ")
        self.view.controller.enter_editor_mode_with.assert_called_once_with(
            topic_view.topic_search_box
        )

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, mocker, topic_view, key, widget_size):
        size = widget_size(topic_view)
        mocker.patch(VIEWS + ".TopicsView.set_focus")
        mocker.patch(VIEWS + ".urwid.Frame.keypress")
        mocker.patch.object(topic_view.topic_search_box, "reset_search_text")
        topic_view.topics_btn_list = ["FOO", "foo", "fan", "boo", "BOO"]
        topic_view.focus_index_before_search = 3

        # Simulate search
        topic_view.log.clear()
        topic_view.log.extend(topic_view.topics_btn_list[3])
        topic_view.log.set_focus(0)
        topic_view.keypress(size, primary_key_for_command("GO_DOWN"))
        assert topic_view.log.get_focus()[1] != topic_view.focus_index_before_search

        # Exit search
        topic_view.keypress(size, key)

        # Check state reset after search
        topic_view.set_focus.assert_called_once_with("body")
        assert topic_view.topic_search_box.reset_search_text.called
        assert topic_view.log == topic_view.topics_btn_list
        assert topic_view.log.get_focus()[1] == topic_view.focus_index_before_search

    def test_mouse_event(self, mocker, topic_view, mouse_scroll_event, widget_size):
        event, button, key = mouse_scroll_event
        topic_view_keypress = mocker.patch.object(topic_view, "keypress")
        size = widget_size(topic_view)
        col = 1
        row = 1
        focus = "WIDGET"
        topic_view.mouse_event(size, event, button, col, row, focus)
        topic_view_keypress.assert_has_calls(
            [mocker.call(size, key)] * SIDE_PANELS_MOUSE_SCROLL_LINES
        )


class TestUsersView:
    @pytest.fixture
    def user_view(self, mocker):
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        controller = mocker.Mock()
        return UsersView(controller, "USER_BTN_LIST")

    def test_mouse_event(self, mocker, user_view, mouse_scroll_event, widget_size):
        event, button, key = mouse_scroll_event
        user_view_keypress = mocker.patch.object(user_view, "keypress")
        size = widget_size(user_view)
        col = 1
        row = 1
        focus = "WIDGET"
        user_view.mouse_event(size, event, button, col, row, focus)
        user_view_keypress.assert_has_calls(
            [mocker.call(size, key)] * SIDE_PANELS_MOUSE_SCROLL_LINES
        )

    def test_mouse_event_left_click(
        self, mocker, user_view, widget_size, compose_box_is_open
    ):
        super_mouse_event = mocker.patch(VIEWS + ".urwid.ListBox.mouse_event")
        user_view.controller.is_in_editor_mode.return_value = compose_box_is_open
        size = widget_size(user_view)
        focus = mocker.Mock()

        user_view.mouse_event(size, "mouse press", 1, 1, 1, focus)

        if compose_box_is_open:
            super_mouse_event.assert_not_called()
        else:
            super_mouse_event.assert_called_once_with(
                size, "mouse press", 1, 1, 1, focus
            )

    @pytest.mark.parametrize(
        "event, button",
        [
            ("mouse release", 0),
            ("mouse press", 3),
            ("mouse release", 4),
        ],
        ids=[
            "unsupported_mouse_release_action",
            "unsupported_right_click_mouse_press_action",
            "invalid_event_button_combination",
        ],
    )
    def test_mouse_event_invalid(self, user_view, event, button, widget_size):
        size = widget_size(user_view)
        col = 1
        row = 1
        focus = "WIDGET"
        return_value = user_view.mouse_event(size, event, button, col, row, focus)
        assert return_value is False


class TestMiddleColumnView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        mocker.patch(MESSAGEVIEW + "", return_value="MSG_LIST")
        self.model = mocker.Mock()
        self.view = mocker.Mock()
        self.write_box = mocker.Mock()
        self.search_box = mocker.Mock()
        self.super = mocker.patch(VIEWS + ".urwid.Frame.__init__")
        self.super_keypress = mocker.patch(VIEWS + ".urwid.Frame.keypress")
        self.model.controller = mocker.Mock()

    @pytest.fixture
    def mid_col_view(self):
        return MiddleColumnView(self.view, self.model, self.write_box, self.search_box)

    def test_init(self, mid_col_view):
        assert mid_col_view.model == self.model
        assert mid_col_view.controller == self.model.controller
        assert mid_col_view.search_box == self.search_box
        assert self.view.message_view == "MSG_LIST"
        self.super.assert_called_once_with(
            "MSG_LIST", header=self.search_box, footer=self.write_box
        )

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_MESSAGES"))
    def test_keypress_focus_header(self, mid_col_view, mocker, key, widget_size):
        size = widget_size(mid_col_view)
        mid_col_view.focus_part = "header"
        mid_col_view.keypress(size, key)
        self.super_keypress.assert_called_once_with(size, key)

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_MESSAGES"))
    def test_keypress_SEARCH_MESSAGES(self, mid_col_view, mocker, key, widget_size):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mocker.patch(MIDCOLVIEW + ".set_focus")

        mid_col_view.keypress(size, key)

        mid_col_view.controller.enter_editor_mode_with.assert_called_once_with(
            mid_col_view.search_box
        )
        mid_col_view.set_focus.assert_called_once_with("header")

    @pytest.mark.parametrize("reply_message_key", keys_for_command("REPLY_MESSAGE"))
    def test_keypress_REPLY_MESSAGE(
        self, mid_col_view, mocker, widget_size, reply_message_key
    ):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".body")
        mocker.patch(MIDCOLVIEW + ".footer")
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mocker.patch(MIDCOLVIEW + ".set_focus")

        mid_col_view.keypress(size, reply_message_key)

        mid_col_view.body.keypress.assert_called_once_with(size, reply_message_key)
        mid_col_view.set_focus.assert_called_once_with("footer")
        assert mid_col_view.footer.focus_position == 1

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MESSAGE"))
    def test_keypress_STREAM_MESSAGE(self, mid_col_view, mocker, key, widget_size):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".body")
        mocker.patch(MIDCOLVIEW + ".footer")
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mocker.patch(MIDCOLVIEW + ".set_focus")

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with("footer")
        assert mid_col_view.footer.focus_position == 0

    @pytest.mark.parametrize("key", keys_for_command("REPLY_AUTHOR"))
    def test_keypress_REPLY_AUTHOR(self, mid_col_view, mocker, key, widget_size):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".body")
        mocker.patch(MIDCOLVIEW + ".footer")
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mocker.patch(MIDCOLVIEW + ".set_focus")

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with("footer")
        assert mid_col_view.footer.focus_position == 1

    @pytest.mark.parametrize("key", keys_for_command("NEXT_UNREAD_TOPIC"))
    def test_keypress_NEXT_UNREAD_TOPIC_stream(
        self, mid_col_view, mocker, widget_size, key
    ):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")

        mid_col_view.model.stream_dict = {1: {"name": "stream"}}
        mid_col_view.model.get_next_unread_topic.return_value = (1, "topic")

        return_value = mid_col_view.keypress(size, key)

        mid_col_view.controller.narrow_to_topic.assert_called_once_with(
            stream_name="stream", topic_name="topic"
        )
        assert return_value == key

    @pytest.mark.parametrize("key", keys_for_command("NEXT_UNREAD_TOPIC"))
    def test_keypress_NEXT_UNREAD_TOPIC_no_stream(
        self, mid_col_view, mocker, widget_size, key
    ):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mid_col_view.model.get_next_unread_topic.return_value = None

        return_value = mid_col_view.keypress(size, key)

        assert mid_col_view.controller.narrow_to_topic.called is False
        assert return_value == key

    @pytest.mark.parametrize("key", keys_for_command("NEXT_UNREAD_PM"))
    def test_keypress_NEXT_UNREAD_PM_stream(
        self, mid_col_view, mocker, key, widget_size
    ):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")

        mid_col_view.model.user_id_email_dict = {1: "EMAIL"}
        mid_col_view.model.get_next_unread_pm.return_value = 1

        mid_col_view.keypress(size, key)

        mid_col_view.controller.narrow_to_user.assert_called_once_with(
            recipient_emails=["EMAIL"],
            contextual_message_id=1,
        )

    @pytest.mark.parametrize("key", keys_for_command("NEXT_UNREAD_PM"))
    def test_keypress_NEXT_UNREAD_PM_no_pm(
        self, mid_col_view, mocker, key, widget_size
    ):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mid_col_view.model.get_next_unread_pm.return_value = None

        return_value = mid_col_view.keypress(size, key)

        assert return_value == key

    @pytest.mark.parametrize("key", keys_for_command("PRIVATE_MESSAGE"))
    def test_keypress_PRIVATE_MESSAGE(self, mid_col_view, mocker, key, widget_size):
        size = widget_size(mid_col_view)
        mocker.patch(MIDCOLVIEW + ".focus_position")
        mid_col_view.model.get_next_unread_pm.return_value = None
        mid_col_view.footer = mocker.Mock()
        return_value = mid_col_view.keypress(size, key)
        mid_col_view.footer.private_box_view.assert_called_once_with()
        assert mid_col_view.footer.focus_position == 0
        assert return_value == key


class TestRightColumnView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.view = mocker.Mock()
        self.user_search = mocker.patch(VIEWS + ".PanelSearchBox")
        self.connect_signal = mocker.patch(VIEWS + ".urwid.connect_signal")
        self.pile = mocker.patch(VIEWS + ".urwid.Pile")
        self.thread = mocker.patch(VIEWS + ".threading")
        self.super = mocker.patch(VIEWS + ".urwid.Frame.__init__")
        self.view.model.unread_counts = {  # Minimal, though an UnreadCounts
            "unread_pms": {
                1: 1,
                2: 1,
            }
        }

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
        self.super.assert_called_once_with(
            right_col_view.users_view(),
            header=self.pile(right_col_view.user_search),
        )

    def test_update_user_list_editor_mode(self, mocker, right_col_view):
        right_col_view.view.controller.update_screen = mocker.Mock()
        right_col_view.view.controller.is_in_editor_mode = lambda: False

        right_col_view.update_user_list("SEARCH_BOX", "NEW_TEXT")

        right_col_view.view.controller.update_screen.assert_not_called()

    @pytest.mark.parametrize(
        "search_string, assert_list, match_return_value",
        [("U", ["USER1", "USER2"], True), ("F", [], False)],
        ids=[
            "user match",
            "no user match",
        ],
    )
    def test_update_user_list(
        self, right_col_view, mocker, search_string, assert_list, match_return_value
    ):
        right_col_view.view.controller.is_in_editor_mode = lambda: True
        self.view.users = ["USER1", "USER2"]
        mocker.patch(VIEWS + ".match_user", return_value=match_return_value)
        mocker.patch(VIEWS + ".UsersView")
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list("SEARCH_BOX", search_string)
        if assert_list:
            right_col_view.users_view.assert_called_with(assert_list)
        set_body.assert_called_once_with(right_col_view.body)

    def test_update_user_presence(self, right_col_view, mocker, user_list):
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list(user_list=user_list)

        right_col_view.users_view.assert_called_with(user_list)
        set_body.assert_called_once_with(right_col_view.body)

    @pytest.mark.parametrize(
        "users, users_btn_len, editor_mode, status",
        [
            (None, 1, False, "active"),
            (
                [
                    {
                        "user_id": 2,
                        "status": "inactive",
                    }
                ],
                1,
                True,
                "active",
            ),
            (None, 0, False, "inactive"),
        ],
    )
    def test_users_view(self, users, users_btn_len, editor_mode, status, mocker):
        self.view.users = [{"user_id": 1, "status": status}]
        self.view.controller.is_in_editor_mode = lambda: editor_mode
        user_btn = mocker.patch(VIEWS + ".UserButton")
        users_view = mocker.patch(VIEWS + ".UsersView")
        right_col_view = RightColumnView(self.view)
        if status != "inactive":
            user_btn.assert_called_once_with(
                user=self.view.users[0],
                controller=self.view.controller,
                view=self.view,
                color="user_" + self.view.users[0]["status"],
                state_marker=STATUS_ACTIVE,
                count=1,
                is_current_user=False,
            )
        users_view.assert_called_once_with(
            self.view.controller, right_col_view.users_btn_list
        )
        assert len(right_col_view.users_btn_list) == users_btn_len

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    def test_keypress_SEARCH_PEOPLE(self, right_col_view, mocker, key, widget_size):
        size = widget_size(right_col_view)
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        mocker.patch.object(right_col_view.user_search, "set_caption")
        right_col_view.keypress(size, key)
        right_col_view.set_focus.assert_called_once_with("header")
        right_col_view.user_search.set_caption.assert_called_once_with(" ")
        self.view.controller.enter_editor_mode_with.assert_called_once_with(
            right_col_view.user_search
        )

    @pytest.mark.parametrize("key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, right_col_view, mocker, key, widget_size):
        size = widget_size(right_col_view)
        mocker.patch(VIEWS + ".UsersView")
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        mocker.patch(VIEWS + ".RightColumnView.set_body")
        mocker.patch.object(right_col_view.user_search, "reset_search_text")
        right_col_view.users_btn_list = []

        right_col_view.keypress(size, key)

        right_col_view.set_body.assert_called_once_with(right_col_view.body)
        right_col_view.set_focus.assert_called_once_with("body")
        assert right_col_view.user_search.reset_search_text.called


class TestLeftColumnView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()
        self.view.model.unread_counts = {  # Minimal, though an UnreadCounts
            "all_msg": 2,
            "all_pms": 0,
            "streams": {
                86: 1,
                14: 1,
                99: 1,
                1: 1,
                2: 1,
                1000: 1,
            },
            "unread_topics": {
                (205, "TOPIC1"): 34,
                (205, "TOPIC2"): 100,
            },
            "all_mentions": 1,
        }
        self.view.model.initial_data = {
            "starred_messages": [1117554, 1117558, 1117574],
        }
        self.view.controller = mocker.Mock()
        self.super_mock = mocker.patch(VIEWS + ".urwid.Pile.__init__")

    def test_menu_view(self, mocker):
        self.streams_view = mocker.patch(VIEWS + ".LeftColumnView.streams_view")
        home_button = mocker.patch(VIEWS + ".HomeButton")
        pm_button = mocker.patch(VIEWS + ".PMButton")
        starred_button = mocker.patch(VIEWS + ".StarredButton")
        mocker.patch(VIEWS + ".urwid.ListBox")
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        mocker.patch(VIEWS + ".StreamButton.mark_muted")
        left_col_view = LeftColumnView(self.view)
        home_button.assert_called_once_with(
            controller=left_col_view.controller, count=2
        )
        pm_button.assert_called_once_with(controller=left_col_view.controller, count=0)
        starred_button.assert_called_once_with(
            controller=left_col_view.controller, count=3
        )

    @pytest.mark.parametrize("pinned", powerset([1, 2, 99, 999, 1000]))
    def test_streams_view(self, mocker, streams, pinned):
        self.view.unpinned_streams = [s for s in streams if s["id"] not in pinned]
        self.view.pinned_streams = [s for s in streams if s["id"] in pinned]
        stream_button = mocker.patch(VIEWS + ".StreamButton")
        mocker.patch(VIEWS + ".StreamsView")
        mocker.patch(VIEWS + ".urwid.LineBox")
        divider = mocker.patch(VIEWS + ".StreamsViewDivider")

        LeftColumnView(self.view)

        if pinned:
            assert divider.called
        else:
            divider.assert_not_called()

        stream_button.assert_has_calls(
            [
                mocker.call(
                    properties=stream,
                    controller=self.view.controller,
                    view=self.view,
                    count=mocker.ANY,
                )
                for stream in (self.view.pinned_streams + self.view.unpinned_streams)
            ]
        )

    def test_topics_view(self, mocker, stream_button):
        mocker.patch(VIEWS + ".LeftColumnView.streams_view")
        mocker.patch(VIEWS + ".LeftColumnView.menu_view")
        topic_button = mocker.patch(VIEWS + ".TopicButton")
        mocker.patch(VIEWS + ".TopicsView")
        mocker.patch(VIEWS + ".urwid.LineBox")
        topic_list = ["TOPIC1", "TOPIC2", "TOPIC3"]
        unread_count_list = [34, 100, 0]
        self.view.model.topics_in_stream = mocker.Mock(return_value=topic_list)
        left_col_view = LeftColumnView(self.view)

        left_col_view.topics_view(stream_button)

        self.view.model.topics_in_stream.assert_called_once_with(205)
        topic_button.assert_has_calls(
            [
                mocker.call(
                    stream_id=205,
                    topic=topic,
                    controller=self.view.controller,
                    view=self.view,
                    count=count,
                )
                for topic, count in zip(topic_list, unread_count_list)
            ]
        )


class TestTabView:
    @pytest.fixture
    def tab_view(self):
        return TabView("❰ TEST ❱")

    @pytest.mark.parametrize(
        "expected_output",
        [
            [
                b"   ",
                b" \xe2\x9d\xb0 ",
                b"   ",
                b" T ",
                b" E ",
                b" S ",
                b" T ",
                b"   ",
                b" \xe2\x9d\xb1 ",
                b"   ",
            ]
        ],
    )
    @pytest.mark.parametrize("tab_width, tab_height", [(3, 10)])
    def test_tab_render(self, tab_view, tab_width, tab_height, expected_output):
        render_output = tab_view._w.render((tab_width, tab_height)).text
        assert render_output == expected_output
