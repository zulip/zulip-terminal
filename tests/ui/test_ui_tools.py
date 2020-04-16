import datetime
from collections import OrderedDict, defaultdict

import pytest
from bs4 import BeautifulSoup
from urwid import AttrWrap, Columns, Padding, Text

from zulipterminal.config.keys import is_command_key, keys_for_command
from zulipterminal.helper import powerset
from zulipterminal.ui_tools.boxes import MessageBox
from zulipterminal.ui_tools.buttons import (
    StreamButton, TopButton, TopicButton, UserButton,
)
from zulipterminal.ui_tools.views import (
    HelpView, LeftColumnView, MessageView, MiddleColumnView, ModListWalker,
    MsgInfoView, PopUpConfirmationView, PopUpView, RightColumnView,
    StreamInfoView, StreamsView, TopicsView, UsersView,
)


VIEWS = "zulipterminal.ui_tools.views"
TOPBUTTON = "zulipterminal.ui_tools.buttons.TopButton"
STREAMBUTTON = "zulipterminal.ui_tools.buttons.StreamButton"
MESSAGEBOX = "zulipterminal.ui_tools.boxes.MessageBox"
BOXES = "zulipterminal.ui_tools.boxes"

SERVER_URL = "https://chat.zulip.zulip"


class TestModListWalker:
    @pytest.fixture
    def mod_walker(self):
        return ModListWalker([list(range(1))])

    @pytest.mark.parametrize("num_items, focus_position", [
        (5, 0),
        (0, 0),
    ])
    def test_extend(self, num_items, focus_position, mod_walker, mocker):
        items = list(range(num_items))
        mocker.patch.object(mod_walker, "_set_focus")
        mod_walker.extend(items)
        mod_walker._set_focus.assert_called_once_with(focus_position)

    def test__set_focus(self, mod_walker, mocker):
        mod_walker.read_message = mocker.Mock()
        mod_walker._set_focus(0)
        mod_walker.read_message.assert_called_once_with()

    def test_set_focus(self, mod_walker, mocker):
        mod_walker.read_message = mocker.Mock()
        mod_walker.set_focus(0)
        mod_walker.read_message.assert_called_once_with()


class TestMessageView:

    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.model = mocker.MagicMock()
        self.urwid = mocker.patch(VIEWS + ".urwid")

    @pytest.fixture
    def msg_view(self, mocker, msg_box):
        mocker.patch(VIEWS + ".MessageView.main_view", return_value=[msg_box])
        mocker.patch(VIEWS + ".MessageView.read_message")
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_view = MessageView(self.model)
        msg_view.log = mocker.Mock()
        msg_view.body = mocker.Mock()
        return msg_view

    def test_init(self, mocker, msg_view, msg_box):
        assert msg_view.model == self.model
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

    @pytest.mark.parametrize('key', keys_for_command('GO_DOWN'))
    def test_keypress_GO_DOWN(self, mocker, msg_view, key):
        size = (20,)
        msg_view.new_loading = False
        mocker.patch(VIEWS + ".MessageView.focus_position", return_value=0)
        mocker.patch(VIEWS + ".MessageView.set_focus_valign")
        msg_view.log.next_position.return_value = 1
        msg_view.keypress(size, key)
        msg_view.log.next_position.assert_called_once_with(
            msg_view.focus_position)
        msg_view.set_focus.assert_called_with(1, 'above')
        msg_view.set_focus_valign.assert_called_once_with('middle')

    @pytest.mark.parametrize('key', keys_for_command('GO_DOWN'))
    def test_keypress_GO_DOWN_exception(self, mocker, msg_view, key):
        size = (20,)
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

    @pytest.mark.parametrize('key', keys_for_command('GO_UP'))
    def test_keypress_GO_UP(self, mocker, msg_view, key):
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

    @pytest.mark.parametrize('key', keys_for_command('GO_UP'))
    def test_keypress_GO_UP_exception(self, mocker, msg_view, key):
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
        msg_view.log = mocker.Mock()
        msg_view.body = mocker.Mock()
        msg_w = mocker.MagicMock()
        msg_view.model.controller.view = mocker.Mock()
        msg_view.model.controller.view.body.focus_col = 1
        msg_w.attr_map = {None: 'unread'}
        msg_w.original_widget.message = {'id': 1}
        msg_w.set_attr_map.return_value = None
        msg_view.body.get_focus.return_value = (msg_w, 0)
        msg_view.body.get_prev.return_value = (None, 1)
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
        msg_view.model.controller.view.body.focus_col = 1
        msg_view.log = list(msg_view.model.index['messages'])
        msg_view.read_message()
        assert msg_view.update_search_box_narrow.called
        assert msg_view.model.index['messages'][1]['flags'] == ['read']
        self.model.mark_message_ids_as_read.assert_called_once_with([1])

    def test_message_calls_search_and_header_bar(self, mocker, msg_view):
        msg_w = mocker.MagicMock()
        msg_w.original_widget.message = {'id': 1}
        msg_view.update_search_box_narrow(msg_w.original_widget)
        msg_w.original_widget.top_header_bar.assert_called_once_with
        (msg_w.original_widget)
        msg_w.original_widget.top_search_bar.assert_called_once_with()

    def test_read_message_no_msgw(self, mocker, msg_view):
        # MSG_W is NONE CASE
        msg_view.body.get_focus.return_value = (None, 0)

        msg_view.read_message()

        self.model.mark_message_ids_as_read.assert_not_called()

    def test_read_message_last_unread_message_focused(self, mocker,
                                                      message_fixture,
                                                      empty_index, msg_box):
        mocker.patch(VIEWS + ".MessageView.main_view", return_value=[msg_box])
        mocker.patch(VIEWS + ".MessageView.set_focus")
        msg_view = MessageView(self.model)
        msg_view.log = [0, 1]
        msg_view.body = mocker.Mock()
        msg_view.update_search_box_narrow = mocker.Mock()

        self.model.controller.view = mocker.Mock()
        self.model.controller.view.body.focus_col = 0
        self.model.index = empty_index

        msg_w = mocker.Mock()
        msg_w.attr_map = {None: 'unread'}
        msg_w.original_widget.message = message_fixture

        msg_view.body.get_focus.return_value = (msg_w, 1)
        msg_view.body.get_prev.return_value = (None, 0)
        msg_view.read_message(1)
        self.model.mark_message_ids_as_read.assert_called_once_with(
            [message_fixture['id']])


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
            stream_view, 'SEARCH_STREAMS', stream_view.update_streams)

    @pytest.mark.parametrize('new_text, expected_log', [
        ('f', ['FOO', 'FOOBAR', 'foo', 'fan']),
        ('a', ['FOOBAR', 'fan', 'bar']),
        ('bar', ['FOOBAR', 'bar']),
        ('foo', ['FOO', 'FOOBAR', 'foo']),
        ('FOO', ['FOO', 'FOOBAR', 'foo']),
        ('test', ['test here']),
        ('here', ['test here']),
    ])
    def test_update_streams(self, mocker, stream_view, new_text, expected_log):
        stream_names = [
            'FOO', 'FOOBAR', 'foo', 'fan',
            'boo', 'BOO', 'bar', 'test here',
        ]
        self.view.controller.editor_mode = True
        new_text = new_text
        search_box = "SEARCH_BOX"
        stream_view.streams_btn_list = [
            mocker.Mock(stream_name=stream_name)
            for stream_name in stream_names
        ]
        stream_view.update_streams(search_box, new_text)
        assert [stream.stream_name for stream in stream_view.log
                ] == expected_log
        self.view.controller.update_screen.assert_called_once_with()

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

    @pytest.mark.parametrize('key', keys_for_command('SEARCH_STREAMS'))
    def test_keypress_SEARCH_STREAMS(self, mocker, stream_view, key):
        size = (20,)
        mocker.patch.object(stream_view, 'set_focus')
        stream_view.keypress(size, key)
        stream_view.set_focus.assert_called_once_with("header")

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_keypress_GO_BACK(self, mocker, stream_view, key):
        size = (20,)
        mocker.patch.object(stream_view, 'set_focus')
        mocker.patch.object(stream_view.stream_search_box, 'reset_search_text')
        stream_view.keypress(size, key)
        stream_view.set_focus.assert_called_once_with("body")
        assert stream_view.stream_search_box.reset_search_text.called
        assert stream_view.log == self.streams_btn_list

    @pytest.mark.parametrize('search_streams_key',
                             keys_for_command('SEARCH_STREAMS'))
    @pytest.mark.parametrize('go_back_key', keys_for_command('GO_BACK'))
    @pytest.mark.parametrize('current_focus, stream', [
        (0, 'FOO'),
        (2, 'fan'),
        (4, 'BOO'),
    ])
    def test_return_to_focus_after_search(self, mocker, stream_view,
                                          current_focus, stream,
                                          search_streams_key, go_back_key):
        # Initialize log
        stream_view.streams_btn_list = [
            mocker.Mock(stream_name=stream_name) for stream_name in [
                'FOO', 'foo', 'fan', 'boo', 'BOO']]
        stream_view.log.extend(stream_view.streams_btn_list)

        # Set initial stream focus to 'current_focus' and name to 'stream'
        stream_view.log.set_focus(current_focus)
        stream_view.focus_index_before_search = current_focus
        previous_focus = stream_view.log.get_focus()[1]
        previous_focus_stream_name = stream

        # Toggle Stream Search
        size = (20,)
        stream_view.keypress(size, search_streams_key)

        # Exit Stream Search
        size = (20,)
        stream_view.keypress(size, go_back_key)

        # Obtain new stream focus
        new_focus = stream_view.log.get_focus()[1]
        new_focus_stream_name = stream_view.log[new_focus].stream_name
        assert new_focus == previous_focus
        assert previous_focus_stream_name == new_focus_stream_name


class TestTopicsView:

    @pytest.fixture
    def topic_view(self, mocker, stream_button):
        self.log = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker",
                                return_value=[])
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
        assert topic_view.log == []  # topic_view patches this
        assert topic_view.stream_button == self.stream_button
        assert topic_view.view == self.view
        assert topic_view.topic_search_box
        self.topic_search_box.assert_called_once_with(
            topic_view, 'SEARCH_TOPICS', topic_view.update_topics)
        self.header_list.assert_called_once_with([topic_view.stream_button,
                                                  self.divider('─'),
                                                  topic_view.topic_search_box])

    @pytest.mark.parametrize('new_text, expected_log', [
        ('f', ['FOO', 'FOOBAR', 'foo', 'fan']),
        ('a', ['FOOBAR', 'fan', 'bar']),
        ('bar', ['FOOBAR', 'bar']),
        ('foo', ['FOO', 'FOOBAR', 'foo']),
        ('FOO', ['FOO', 'FOOBAR', 'foo']),
        ('(no', ['(no topic)']),
        ('topic', ['(no topic)']),
    ])
    def test_update_topics(self, mocker, topic_view, new_text, expected_log):
        topic_names = [
            'FOO', 'FOOBAR', 'foo', 'fan',
            'boo', 'BOO', 'bar', '(no topic)',
        ]
        self.view.controller.editor_mode = True
        new_text = new_text
        search_box = "SEARCH_BOX"
        topic_view.topics_btn_list = [
            mocker.Mock(topic_name=topic_name)
            for topic_name in topic_names
        ]
        topic_view.update_topics(search_box, new_text)
        assert [topic.topic_name for topic in topic_view.log
                ] == expected_log
        self.view.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize('topic_name, topic_initial_log,\
                              topic_final_log', [
        ('TOPIC3', ['TOPIC2', 'TOPIC3', 'TOPIC1'],
            ['TOPIC3', 'TOPIC2', 'TOPIC1']),
        ('TOPIC1', ['TOPIC1', 'TOPIC2', 'TOPIC3'],
            ['TOPIC1', 'TOPIC2', 'TOPIC3']),
        ('TOPIC4', ['TOPIC1', 'TOPIC2', 'TOPIC3'],
            ['TOPIC4', 'TOPIC1', 'TOPIC2', 'TOPIC3']),
        ('TOPIC1', [], ['TOPIC1'])
    ], ids=['reorder_topic3', 'topic1_discussion_continues', 'new_topic4',
            'first_topic_1'])
    def test_update_topics_list(self, mocker, topic_view, topic_name,
                                topic_initial_log, topic_final_log):
        mocker.patch(TOPBUTTON + '.__init__', return_value=None)
        set_focus_valign = mocker.patch(
            'zulipterminal.ui_tools.buttons.urwid.ListBox.set_focus_valign')
        topic_view.view.controller.model.stream_dict = {
            86: {'name': 'PTEST'}
        }
        topic_view.view.controller.model.muted_topics = []
        topic_view.log = [mocker.Mock(topic_name=topic_name)
                          for topic_name in topic_initial_log]

        topic_view.update_topics_list(86, topic_name, 1001)
        assert [topic.topic_name for topic in topic_view.log
                ] == topic_final_log
        set_focus_valign.assert_called_once_with('bottom')

    @pytest.mark.parametrize('key', keys_for_command('TOGGLE_TOPIC'))
    def test_keypress_EXIT_TOGGLE_TOPIC(self, mocker, topic_view, key):
        size = (200, 20)
        mocker.patch(VIEWS + '.urwid.Frame.keypress')
        topic_view.view.left_panel = mocker.Mock()
        topic_view.view.left_panel.contents = [mocker.Mock(), mocker.Mock()]
        topic_view.keypress(size, key)
        (topic_view.view.left_panel.
            options.assert_called_once_with(height_type="weight"))

    @pytest.mark.parametrize('key', keys_for_command('GO_RIGHT'))
    def test_keypress_GO_RIGHT(self, mocker, topic_view, key):
        size = (200, 20)
        mocker.patch(VIEWS + '.urwid.Frame.keypress')
        topic_view.view.body.focus_col = None
        topic_view.keypress(size, key)
        assert topic_view.view.body.focus_col == 1
        topic_view.view.show_left_panel.assert_called_once_with(visible=False)

    @pytest.mark.parametrize('key', keys_for_command('SEARCH_TOPICS'))
    def test_keypress_SEARCH_TOPICS(self, mocker, topic_view, key):
        size = (200, 20)
        mocker.patch(VIEWS + '.TopicsView.set_focus')
        topic_view.keypress(size, key)
        topic_view.header_list.set_focus.assert_called_once_with(2)

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_keypress_GO_BACK(self, mocker, topic_view, key):
        size = (200, 20)
        mocker.patch(VIEWS + '.TopicsView.set_focus')
        mocker.patch.object(topic_view.topic_search_box, 'reset_search_text')
        topic_view.keypress(size, key)
        topic_view.set_focus.assert_called_once_with("body")
        assert topic_view.topic_search_box.reset_search_text.called
        assert topic_view.log == self.topics_btn_list


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

    @pytest.mark.parametrize('event, button', [
            ('mouse release', 0),
            ('mouse press', 1),
            ('mouse press', 3),
            ('mouse release', 4),
        ],
        ids=[
            'unsupported_mouse_release_action',
            'unsupported_left_click_mouse_press_action',
            'unsupported_right_click_mouse_press_action',
            'invalid_event_button_combination',
        ]
    )
    def test_mouse_event_invalid(self, user_view, event, button):
        size = (200, 20)
        col = 1
        row = 1
        focus = 'WIDGET'
        return_value = user_view.mouse_event(size, event, button, col, row,
                                             focus)
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

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_keypress_GO_BACK(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.header')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.header.keypress.assert_called_once_with(size, key)
        mid_col_view.footer.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with('body')
        self.super_keypress.assert_called_once_with(size, key)

    @pytest.mark.parametrize('key', keys_for_command('SEARCH_MESSAGES'))
    def test_keypress_focus_header(self, mid_col_view, mocker, key):
        size = (20,)
        mid_col_view.focus_part = 'header'
        mid_col_view.keypress(size, key)
        self.super_keypress.assert_called_once_with(size, key)

    @pytest.mark.parametrize('key', keys_for_command('SEARCH_MESSAGES'))
    def test_keypress_SEARCH_MESSAGES(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        assert mid_col_view.controller.editor_mode is True
        assert mid_col_view.controller.editor == mid_col_view.search_box
        mid_col_view.set_focus.assert_called_once_with('header')

    @pytest.mark.parametrize('enter_key', keys_for_command('ENTER'))
    @pytest.mark.parametrize('reply_message_key',
                             keys_for_command('REPLY_MESSAGE'))
    def test_keypress_REPLY_MESSAGE(self, mid_col_view, mocker,
                                    reply_message_key, enter_key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, reply_message_key)

        mid_col_view.body.keypress.assert_called_once_with(size, enter_key)
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 1

    @pytest.mark.parametrize('key', keys_for_command('STREAM_MESSAGE'))
    def test_keypress_STREAM_MESSAGE(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 0

    @pytest.mark.parametrize('key', keys_for_command('REPLY_AUTHOR'))
    def test_keypress_REPLY_AUTHOR(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.body')
        mocker.patch(VIEWS + '.MiddleColumnView.footer')
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        mocker.patch(VIEWS + '.MiddleColumnView.set_focus')

        mid_col_view.keypress(size, key)

        mid_col_view.body.keypress.assert_called_once_with(size, key)
        mid_col_view.set_focus.assert_called_once_with('footer')
        assert mid_col_view.footer.focus_position == 1

    @pytest.mark.parametrize('key', keys_for_command('NEXT_UNREAD_TOPIC'))
    def test_keypress_NEXT_UNREAD_TOPIC_stream(self, mid_col_view, mocker,
                                               key):
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

    @pytest.mark.parametrize('key', keys_for_command('NEXT_UNREAD_TOPIC'))
    def test_keypress_NEXT_UNREAD_TOPIC_no_stream(self, mid_col_view, mocker,
                                                  key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        topic_btn = mocker.patch(VIEWS + '.TopicButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_topic',
                     return_value=None)

        return_value = mid_col_view.keypress(size, key)
        assert return_value == key

    @pytest.mark.parametrize('key', keys_for_command('NEXT_UNREAD_PM'))
    def test_keypress_NEXT_UNREAD_PM_stream(self, mid_col_view, mocker, key):
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

    @pytest.mark.parametrize('key', keys_for_command('NEXT_UNREAD_PM'))
    def test_keypress_NEXT_UNREAD_PM_no_pm(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        pm_btn = mocker.patch(VIEWS + '.UnreadPMButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_pm',
                     return_value=None)

        return_value = mid_col_view.keypress(size, key)
        assert return_value == key

    @pytest.mark.parametrize('key', keys_for_command('PRIVATE_MESSAGE'))
    def test_keypress_PRIVATE_MESSAGE(self, mid_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + '.MiddleColumnView.focus_position')
        pm_btn = mocker.patch(VIEWS + '.UnreadPMButton')
        mocker.patch(VIEWS + '.MiddleColumnView.get_next_unread_pm',
                     return_value=None)
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
        self.line_box = mocker.patch(VIEWS + ".urwid.LineBox")
        self.thread = mocker.patch(VIEWS + ".threading")
        self.super = mocker.patch(VIEWS + ".urwid.Frame.__init__")
        self.view.model.unread_counts = {  # Minimal, though an UnreadCounts
            'unread_pms': {
                1: 1,
                2: 1,
            }
        }

    @pytest.fixture
    def right_col_view(self, mocker, width=50):
        mocker.patch(VIEWS + ".RightColumnView.users_view")
        return RightColumnView(width, self.view)

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

    def test_update_user_list_editor_mode(self, mocker, right_col_view):
        right_col_view.view.controller.update_screen = mocker.Mock()
        right_col_view.view.controller.editor_mode = False

        right_col_view.update_user_list("SEARCH_BOX", "NEW_TEXT")

        right_col_view.view.controller.update_screen.assert_not_called()

    @pytest.mark.parametrize('search_string, assert_list, \
                              match_return_value', [
        ('U', ["USER1", "USER2"], True),
        ('F', [], False)
    ], ids=[
        'user match', 'no user match',
    ])
    def test_update_user_list(self, right_col_view, mocker,
                              search_string, assert_list, match_return_value):
        right_col_view.view.controller.editor_mode = True
        self.view.users = ["USER1", "USER2"]
        mocker.patch(VIEWS + ".match_user", return_value=match_return_value)
        mocker.patch(VIEWS + ".UsersView")
        list_w = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list("SEARCH_BOX", search_string)

        right_col_view.users_view.assert_called_with(assert_list)
        set_body.assert_called_once_with(right_col_view.body)

    def test_update_user_presence(self, right_col_view, mocker,
                                  user_list):
        set_body = mocker.patch(VIEWS + ".urwid.Frame.set_body")

        right_col_view.update_user_list(user_list=user_list)

        right_col_view.users_view.assert_called_with(user_list)
        set_body.assert_called_once_with(right_col_view.body)

    @pytest.mark.parametrize('users, users_btn_len, editor_mode, status', [
        (None, 1, False, 'active'),
        ([{
            'user_id': 2,
            'status': 'inactive',
        }], 1, True, 'active'),
        (None, 0, False, 'inactive'),
    ])
    def test_users_view(self, users, users_btn_len, editor_mode, status,
                        mocker, width=40):
        self.view.users = [{
            'user_id': 1,
            'status': status
        }]
        self.view.controller.editor_mode = editor_mode
        user_btn = mocker.patch(VIEWS + ".UserButton")
        users_view = mocker.patch(VIEWS + ".UsersView")
        right_col_view = RightColumnView(width, self.view)
        if status != 'inactive':
            unread_counts = right_col_view.view.model.unread_counts
            user_btn.assert_called_once_with(
                self.view.users[0],
                controller=self.view.controller,
                view=self.view,
                width=width,
                color='user_' + self.view.users[0]['status'],
                count=1
            )
        users_view.assert_called_once_with(right_col_view.users_btn_list)
        assert len(right_col_view.users_btn_list) == users_btn_len

    @pytest.mark.parametrize('key', keys_for_command('SEARCH_PEOPLE'))
    def test_keypress_SEARCH_PEOPLE(self, right_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        right_col_view.keypress(size, key)
        right_col_view.set_focus.assert_called_once_with('header')

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_keypress_GO_BACK(self, right_col_view, mocker, key):
        size = (20,)
        mocker.patch(VIEWS + ".UsersView")
        mocker.patch(VIEWS + ".RightColumnView.set_focus")
        mocker.patch(VIEWS + ".RightColumnView.set_body")
        mocker.patch.object(right_col_view.user_search, 'reset_search_text')
        right_col_view.users_btn_list = []

        right_col_view.keypress(size, key)

        right_col_view.set_body.assert_called_once_with(right_col_view.body)
        right_col_view.set_focus.assert_called_once_with('body')
        assert right_col_view.user_search.reset_search_text.called


class TestLeftColumnView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()
        self.view.model.unread_counts = {  # Minimal, though an UnreadCounts
            'all_msg': 2,
            'all_pms': 0,
            'streams': {
                86: 1,
                14: 1,
                99: 1,
                1: 1,
                2: 1,
                1000: 1,
            },
            'unread_topics': {
                (205, 'TOPIC1'): 34,
                (205, 'TOPIC2'): 100,
            },
            'all_mentions': 1,
        }
        self.view.controller = mocker.Mock()
        self.super_mock = mocker.patch(VIEWS + ".urwid.Pile.__init__")

    def test_menu_view(self, mocker, width=40):
        self.streams_view = mocker.patch(
            VIEWS + ".LeftColumnView.streams_view")
        home_button = mocker.patch(VIEWS + ".HomeButton")
        pm_button = mocker.patch(VIEWS + ".PMButton")
        mocker.patch(VIEWS + ".urwid.ListBox")
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker")
        mocker.patch(STREAMBUTTON + ".mark_muted")
        left_col_view = LeftColumnView(width, self.view)
        home_button.assert_called_once_with(left_col_view.controller,
                                            count=2, width=width)
        pm_button.assert_called_once_with(left_col_view.controller,
                                          count=0, width=width)

    @pytest.mark.parametrize('pinned', powerset([1, 2, 99, 1000]))
    def test_streams_view(self, mocker, streams, pinned, width=40):
        self.view.unpinned_streams = [s for s in streams if s[1] not in pinned]
        self.view.pinned_streams = [s for s in streams if s[1] in pinned]
        stream_button = mocker.patch(VIEWS + '.StreamButton')
        stream_view = mocker.patch(VIEWS + '.StreamsView')
        line_box = mocker.patch(VIEWS + '.urwid.LineBox')
        divider = mocker.patch(VIEWS + '.urwid.Divider')
        mocker.patch(STREAMBUTTON + ".mark_muted")

        left_col_view = LeftColumnView(width, self.view)

        if pinned:
            divider.assert_called_once_with('-')
        else:
            divider.assert_not_called()

        stream_button.assert_has_calls(
            [mocker.call(stream,
                         controller=self.view.controller,
                         width=width,
                         view=self.view,
                         count=1)
             for stream in (self.view.pinned_streams +
                            self.view.unpinned_streams)])

    def test_topics_view(self, mocker, stream_button, width=40):
        mocker.patch(VIEWS + ".LeftColumnView.streams_view")
        mocker.patch(VIEWS + ".LeftColumnView.menu_view")
        topic_button = mocker.patch(VIEWS + '.TopicButton')
        topics_view = mocker.patch(VIEWS + '.TopicsView')
        line_box = mocker.patch(VIEWS + '.urwid.LineBox')
        topic_list = ['TOPIC1', 'TOPIC2', 'TOPIC3']
        unread_count_list = [34, 100, 0]
        self.view.model.index = {
            'topics': {
                205: topic_list,
            }
        }
        left_col_view = LeftColumnView(width, self.view)
        left_col_view.topics_view(stream_button)

        topic_button.assert_has_calls([
            mocker.call(stream_id=205,
                        topic=topic,
                        controller=self.view.controller,
                        width=40,
                        count=count)
            for topic, count in zip(topic_list, unread_count_list)
        ])


class TestPopUpView:
    @pytest.fixture(autouse=True)
    def pop_up_view(self, mocker):
        self.controller = mocker.Mock()
        self.command = 'COMMAND'
        self.widget = mocker.Mock()
        self.widgets = [self.widget, ]
        self.list_walker = mocker.patch(VIEWS + '.urwid.SimpleFocusListWalker',
                                        return_value=[])
        self.super_init = mocker.patch(VIEWS + '.urwid.ListBox.__init__')
        self.super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.pop_up_view = PopUpView(self.controller, self.widgets,
                                     self.command)

    def test_init(self):
        assert self.pop_up_view.controller == self.controller
        assert self.pop_up_view.command == self.command
        self.list_walker.assert_called_once_with(self.widgets)
        self.super_init.assert_called_once_with(self.pop_up_view.log)

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_keypress_GO_BACK(self, key):
        size = (200, 20)
        self.pop_up_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_command_key(self, mocker):
        size = (200, 20)
        mocker.patch(VIEWS + '.is_command_key', side_effect=(
            lambda command, key: command == self.command
        ))
        self.pop_up_view.keypress(size, 'cmd_key')
        assert self.controller.exit_popup.called

    def test_keypress_navigation(self, mocker,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = (200, 20)
        # Patch `is_command_key` to not raise an 'Invalid Command' exception
        # when its parameters are (self.command, key) as there is no
        # self.command='COMMAND' command in keys.py.
        mocker.patch(VIEWS + '.is_command_key', side_effect=(
            lambda command, key:
            False if command == self.command
            else is_command_key(command, key)
        ))
        self.pop_up_view.keypress(size, key)
        self.super_keypress.assert_called_once_with(size, expected_key)


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
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, key):
        size = (200, 20)
        self.help_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_keypress_navigation(self, mocker,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = (200, 20)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.help_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestPopUpConfirmationView:
    @pytest.fixture
    def popup_view(self, mocker, stream_button):
        self.controller = mocker.Mock()
        self.controller.view.LEFT_WIDTH = 27
        self.callback = mocker.Mock()
        self.list_walker = mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker",
                                        return_value=[])
        self.divider = mocker.patch(VIEWS + '.urwid.Divider')
        self.text = mocker.patch(VIEWS + '.urwid.Text')
        self.wrapper_w = mocker.patch(VIEWS + '.urwid.WidgetWrap')
        return PopUpConfirmationView(
            self.controller,
            self.text,
            self.callback,
        )

    def test_init(self, popup_view):
        assert popup_view.controller == self.controller
        assert popup_view.success_callback == self.callback
        self.divider.assert_called_once_with()
        self.list_walker.assert_called_once_with(
            [self.text, self.divider(), self.wrapper_w()])

    def test_exit_popup_yes(self, mocker, popup_view):
        popup_view.exit_popup_yes(mocker.Mock())
        self.callback.assert_called_once_with()
        assert self.controller.exit_popup.called

    def test_exit_popup_no(self, mocker, popup_view):
        popup_view.exit_popup_no(mocker.Mock())
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called

    @pytest.mark.parametrize('key', keys_for_command('GO_BACK'))
    def test_exit_popup_GO_BACK(self, mocker, popup_view, key):
        size = (20, 20)
        popup_view.keypress(size, key)
        self.callback.assert_not_called()
        assert self.controller.exit_popup.called


class TestStreamInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch):
        self.controller = mocker.Mock()
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        self.stream_info_view = StreamInfoView(self.controller, '', '', '')

    def test_keypress_navigation(self, mocker,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = (200, 20)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.stream_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestMsgInfoView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, monkeypatch, message_fixture):
        self.controller = mocker.Mock()
        mocker.patch(VIEWS + ".urwid.SimpleFocusListWalker", return_value=[])
        self.msg_info_view = MsgInfoView(self.controller, message_fixture)

    def test_keypress_any_key(self):
        key = "a"
        size = (200, 20)
        self.msg_info_view.keypress(size, key)
        assert not self.controller.exit_popup.called

    @pytest.mark.parametrize('key', keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, key):
        size = (200, 20)
        self.msg_info_view.keypress(size, key)
        assert self.controller.exit_popup.called

    def test_height_noreactions(self, message_fixture):
        self.msg_info_view = MsgInfoView(self.controller, message_fixture)
        expected_height = 5
        assert self.msg_info_view.height == expected_height

    # FIXME This is the same parametrize as MessageBox:test_reactions_view
    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'reactions': [{
                'emoji_name': 'thumbs_up',
                'emoji_code': '1f44d',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'AARON@zulip.com',
                    'full_name': 'aaron',
                    'id': 1,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'heart',
                'emoji_code': '2764',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }]}
        ])
    def test_height_reactions(self, message_fixture, to_vary_in_each_message):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        self.msg_info_view = MsgInfoView(self.controller, varied_message)
        expected_height = 8
        assert self.msg_info_view.height == expected_height

    def test_keypress_navigation(self, mocker,
                                 navigation_key_expected_key_pair):
        key, expected_key = navigation_key_expected_key_pair
        size = (200, 20)
        super_keypress = mocker.patch(VIEWS + '.urwid.ListBox.keypress')
        self.msg_info_view.keypress(size, key)
        super_keypress.assert_called_once_with(size, expected_key)


class TestMessageBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.model = mocker.MagicMock()
        self.model.index = initial_index

    @pytest.mark.parametrize('message_type, set_fields', [
        ('stream',
            [('stream_name', ''), ('stream_id', None), ('topic_name', '')]),
        ('private',
            [('email', ''), ('user_id', None)]),
    ])
    def test_init(self, mocker, message_type, set_fields):
        mocker.patch.object(MessageBox, 'main_view')
        message = dict(display_recipient=[
            {
                'id': 7,
                'email': 'boo@zulip.com',
                'full_name': 'Boo is awesome'
            }],
            stream_id=5,
            subject='hi',
            sender_email='foo@zulip.com',
            sender_id=4209,
            type=message_type)

        msg_box = MessageBox(message, self.model, None)

        assert msg_box.last_message == defaultdict(dict)
        for field, invalid_default in set_fields:
            assert getattr(msg_box, field) != invalid_default

    def test_init_fails_with_bad_message_type(self):
        message = dict(type='BLAH')

        with pytest.raises(RuntimeError):
            msg_box = MessageBox(message, self.model, None)

    def test_private_message_to_self(self, mocker):
        message = dict(
            type='private',
            display_recipient=[{'full_name': 'Foo Foo',
                                'email': 'foo@zulip.com',
                                'id': None}],
            sender_id=9,
            content="<p> self message. </p>",
            sender_full_name='Foo Foo',
            sender_email='foo@zulip.com',
            timestamp=150989984,
        )
        self.model.user_email = 'foo@zulip.com'
        mocker.patch(MESSAGEBOX + '._is_private_message_to_self',
                     return_value=True)
        mocker.patch.object(MessageBox, 'main_view')
        msg_box = MessageBox(message, self.model, None)

        assert msg_box.recipients_emails == 'foo@zulip.com'
        msg_box._is_private_message_to_self.assert_called_once_with()

    @pytest.mark.parametrize('content, markup', [
        ('', []),
        ('<p>hi</p>', ['', 'hi']),
        ('<span class="user-mention">@Bob Smith',
            [('msg_mention', '@Bob Smith')]),
        ('<span class="user-group-mention">@A Group',
            [('msg_mention', '@A Group')]),
        ('<code>some code', [('msg_code', 'some code')]),
        ('<div class="codehilite">some code', [('msg_code', 'some code')]),
        ('<strong>Something', [('msg_bold', 'Something')]),
        ('<em>Something', [('msg_bold', 'Something')]),
        ('<blockquote>stuff', [('msg_quote', ['', 'stuff'])]),
        ('<div class="message_embed">',
            ['[EMBEDDED CONTENT NOT RENDERED]']),  # FIXME Unsupported
        ('<a href="http://foo">http://foo</a>', [('msg_link', 'http://foo')]),
        ('<a href="http://foo/bar.png">http://foo/bar.png</a>',
            [('msg_link', 'http://foo/bar.png')]),
        ('<a href="http://foo">bar</a>', [('msg_link', '[bar](http://foo)')]),
        ('<a href="/user_uploads/blah"',
            [('msg_link', '[]({}/user_uploads/blah)'.format(SERVER_URL))]),
        ('<a href="/api"',
            [('msg_link', '[]({}/api)'.format(SERVER_URL))]),
        ('<a href="some/relative_url">{}/some/relative_url</a>'
         .format(SERVER_URL),
            [('msg_link', '{}/some/relative_url'.format(SERVER_URL))]),
        ('<li>Something', ['  * ', '', 'Something']),
        ('<li>Something<li>else',  # NOTE Real items are newline-separated?
            ['  * ', '', 'Something', '  * ', '', 'else']),
        ('<br>', []), ('<br/>', []),
        ('<hr>', ['[RULER NOT RENDERED]']),
        ('<hr/>', ['[RULER NOT RENDERED]']),
        ('<img>', ['[IMAGE NOT RENDERED]']),
        ('<img/>', ['[IMAGE NOT RENDERED]']),
        ('<table><thead><tr><th>Firstname</th><th>Lastname</th></tr></thead>'
         '<tbody><tr><td>John</td><td>Doe</td></tr><tr><td>Mary</td><td>Moe'
         '</td></tr></tbody></table>', [
            '┌─', '─────────', '─┬─', '────────', '─┐\n',
            '│ ', ('table_head', 'Firstname'), ' │ ',
            ('table_head', 'Lastname'), ' │\n',
            '├─', '─────────', '─┼─', '────────', '─┤\n',
            '│ ', (None, 'John     '), ' │ ', (None, 'Doe     '), ' │\n',
            '│ ', (None, 'Mary     '), ' │ ', (None, 'Moe     '), ' │\n',
            '└─', '─────────', '─┴─', '────────', '─┘',
         ]),
        ('<table><thead><tr><th align="left">Name</th><th align="right">Id'
         '</th></tr></thead><tbody><tr><td align="left">Robert</td>'
         '<td align="right">1</td></tr><tr><td align="left">Mary</td>'
         '<td align="right">100</td></tr></tbody></table>', [
            '┌─', '──────', '─┬─', '───', '─┐\n',
            '│ ', ('table_head', 'Name  '), ' │ ', ('table_head', ' Id'),
            ' │\n',
            '├─', '──────', '─┼─', '───', '─┤\n',
            '│ ', (None, 'Robert'), ' │ ', (None,  '  1'), ' │\n',
            '│ ', (None, 'Mary  '), ' │ ', (None, '100'), ' │\n',
            '└─', '──────', '─┴─', '───', '─┘',
         ]),
        ('<table><thead><tr><th align="center">Name</th><th align="right">Id'
         '</th></tr></thead><tbody><tr><td align="center">Robert</td>'
         '<td align="right">1</td></tr><tr><td align="center">Mary</td>'
         '<td align="right">100</td></tr></tbody></table>', [
            '┌─', '──────', '─┬─', '───', '─┐\n',
            '│ ', ('table_head', ' Name '), ' │ ', ('table_head', ' Id'),
            ' │\n',
            '├─', '──────', '─┼─', '───', '─┤\n',
            '│ ', (None, 'Robert'), ' │ ', (None,  '  1'), ' │\n',
            '│ ', (None, ' Mary '), ' │ ', (None, '100'), ' │\n',
            '└─', '──────', '─┴─', '───', '─┘',
         ]),
        ('<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Foo</td>'
         '</tr><tr><td>Bar</td></tr><tr><td>Baz</td></tr></tbody></table>', [
            '┌─', '────', '─┐\n',
            '│ ', ('table_head', 'Name'), ' │\n',
            '├─', '────', '─┤\n',
            '│ ', (None, 'Foo '), ' │\n',
            '│ ', (None, 'Bar '), ' │\n',
            '│ ', (None, 'Baz '), ' │\n',
            '└─', '────', '─┘',
         ]),
        ('<table><thead><tr><th>Column1</th></tr></thead><tbody><tr><td></td>'
         '</tr></tbody></table>', [
            '┌─', '───────', '─┐\n',
            '│ ', ('table_head', 'Column1'), ' │\n',
            '├─', '───────', '─┤\n',
            '│ ', (None,  '       '), ' │\n',
            '└─', '───────', '─┘',
         ]),
        ('<span class="katex-display">some-math</span>', ['some-math']),
        ('<span class="katex">some-math</span>', ['some-math']),
        ('<ul><li>text</li></ul>', ['', '  * ', '', 'text']),
        ('<del>text</del>', ['', 'text']),  # FIXME Strikethrough
        ('<div class="message_inline_image">'
         '<a href="x"><img src="x"></a></div>', []),
        ('<div class="message_inline_ref">blah</div>', []),
        ('<span class="emoji">:smile:</span>', [('msg_emoji', ':smile:')]),
        ('<div class="inline-preview-twitter"',
            ['[TWITTER PREVIEW NOT RENDERED]']),
        ('<img class="emoji" title="zulip"/>', [('msg_emoji', ':zulip:')]),
        ('<img class="emoji" title="github"/>', [('msg_emoji', ':github:')]),
    ], ids=[
        'empty', 'p', 'user-mention', 'group-mention', 'code', 'codehilite',
        'strong', 'em', 'blockquote',
        'embedded_content',
        'link_sametext', 'link_sameimage', 'link_differenttext',
        'link_userupload', 'link_api', 'link_serverrelative_same',
        'listitem', 'listitems',
        'br', 'br2', 'hr', 'hr2', 'img', 'img2',
        'table_default',
        'table_with_left_and_right_alignments',
        'table_with_center_and_right_alignments',
        'table_with_single_column',
        'table_with_the_bare_minimum',
        'math', 'math2',
        'ul', 'strikethrough_del', 'inline_image', 'inline_ref',
        'emoji', 'preview-twitter', 'zulip_extra_emoji', 'custom_emoji'
    ])
    def test_soup2markup(self, content, markup):
        message = dict(display_recipient=['x'], stream_id=5, subject='hi',
                       sender_email='foo@zulip.com', id=4, sender_id=4209,
                       type='stream',  # NOTE Output should not vary with PM
                       flags=[], content=content, sender_full_name='bob smith',
                       is_me_message=False, timestamp=99, reactions=[])
        self.model.stream_dict = {
            5: {  # matches stream_id above
                'color': '#bd6',
            },
        }
        self.model.server_url = SERVER_URL
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
                'color': '#bd6',
            },
        }
        msg_box = MessageBox(message, self.model, last_message)

    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'is_me_message': True,  # will be overridden by test function.
            'flags': [],
            'content': '',  # will be overridden by test function.
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('content, is_me_message', [
        ('<p>/me is excited!</p>', True),
        ('<p>/me is excited! /me is not excited.</p>', True),
        ('<p>This is /me not.</p>', False),
        ('<p>/me is excited!</p>', False),
    ])
    def test_main_view_renders_slash_me(self, mocker, message, content,
                                        is_me_message):
        mocker.patch(VIEWS + ".urwid.Text")
        message['content'] = content
        message['is_me_message'] = is_me_message
        msg_box = MessageBox(message, self.model, message)
        msg_box.main_view()
        name_index = 11 if is_me_message else -1  # 11 = len(<str><strong>)
        assert msg_box.message['content'].find(
            message['sender_full_name']) == name_index

    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'is_me_message': False,
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
                'color': '#bd6',
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
            'id': 4,
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
            'is_me_message': False,
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

    @pytest.mark.parametrize('msg_narrow, msg_type, assert_header_bar,\
                              assert_search_bar', [
        ([], 0, 'PTEST >', 'All messages'),
        ([], 1, 'You and ', 'All messages'),
        ([], 2, 'You and ', 'All messages'),
        ([['stream', 'PTEST']], 0, 'PTEST >', ('bar', [('s#bd6', 'PTEST')])),
        ([['stream', 'PTEST'], ['topic', 'b']], 0, 'PTEST >',
         ('bar', [('s#bd6', 'PTEST'), ('s#bd6', ': topic narrow')])),
        ([['is', 'private']], 1, 'You and ', 'All private messages'),
        ([['is', 'private']], 2, 'You and ', 'All private messages'),
        ([['pm_with', 'boo@zulip.com']], 1, 'You and ',
         'Private conversation'),
        ([['pm_with', 'boo@zulip.com, bar@zulip.com']], 2, 'You and ',
         'Group private conversation'),
        ([['is', 'starred']], 0, 'PTEST >', 'Starred messages'),
        ([['is', 'starred']], 1, 'You and ', 'Starred messages'),
        ([['is', 'starred']], 2, 'You and ', 'Starred messages'),
        ([['is', 'starred'], ['search', 'FOO']], 1, 'You and ',
         'Starred messages'),
        ([['search', 'FOO']], 0, 'PTEST >', 'All messages'),
        ([['is', 'mentioned']], 0, 'PTEST >', 'Mentions'),
        ([['is', 'mentioned']], 1, 'You and ', 'Mentions'),
        ([['is', 'mentioned']], 2, 'You and ', 'Mentions'),
        ([['is', 'mentioned'], ['search', 'FOO']], 1, 'You and ',
         'Mentions'),
    ])
    def test_msg_generates_search_and_header_bar(self, mocker,
                                                 messages_successful_response,
                                                 msg_type, msg_narrow,
                                                 assert_header_bar,
                                                 assert_search_bar):
        self.model.stream_dict = {
            205: {
                'color': '#bd6',
            },
        }
        self.model.narrow = msg_narrow
        messages = messages_successful_response['messages']
        current_message = messages[msg_type]
        msg_box = MessageBox(current_message, self.model, messages[0])
        search_bar = msg_box.top_search_bar()
        header_bar = msg_box.top_header_bar(msg_box)

        assert header_bar.text.startswith(assert_header_bar)
        assert search_bar.text_to_fill == assert_search_bar

    # Assume recipient (PM/stream/topic) header is unchanged below
    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'is_me_message': False,
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('current_year', [2018, 2019, 2050],
                             ids=['now_2018', 'now_2019', 'now_2050'])
    @pytest.mark.parametrize('starred_msg', ['this', 'last', 'neither'],
                             ids=['this_starred', 'last_starred', 'no_stars'])
    @pytest.mark.parametrize('expected_header, to_vary_in_last_message', [
        (['alice', ' ', 'DAYDATETIME'], {'sender_full_name': 'bob'}),
        ([' ', ' ', 'DAYDATETIME'], {'timestamp': 1532103779}),
        (['alice', ' ', 'DAYDATETIME'], {'timestamp': 0}),
    ], ids=['show_author_as_authors_different',
            'merge_messages_as_only_slightly_earlier_message',
            'dont_merge_messages_as_much_earlier_message'])
    def test_main_view_content_header_without_header(self, mocker, message,
                                                     expected_header,
                                                     current_year,
                                                     starred_msg,
                                                     to_vary_in_last_message):
        date = mocker.patch('zulipterminal.ui_tools.boxes.date')
        date.today.return_value = datetime.date(current_year, 1, 1)
        date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

        stars = {msg: ({'flags': ['starred']} if msg == starred_msg else {})
                 for msg in ('this', 'last')}
        this_msg = dict(message, **stars['this'])
        all_to_vary = dict(to_vary_in_last_message, **stars['last'])
        last_msg = dict(message, **all_to_vary)
        msg_box = MessageBox(this_msg, self.model, last_msg)
        expected_header[1] = msg_box._time_for_message(message)
        if current_year > 2018:
            expected_header[1] = '2018 - ' + expected_header[1]
        expected_header[2] = '*' if starred_msg == 'this' else ' '

        view_components = msg_box.main_view()

        assert len(view_components) == 2
        assert isinstance(view_components[0], Columns)
        assert ([w.text for w in view_components[0].widget_list] ==
                expected_header)
        assert isinstance(view_components[1], Padding)

    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'sender_full_name': 'bob'},
        {'timestamp': 1532103779},
        {'timestamp': 0},
        {},
        {'flags': ['starred']},
    ], ids=['common_author', 'common_timestamp', 'common_early_timestamp',
            'common_unchanged_message', 'both_starred'])
    def test_main_view_compact_output(self, mocker, message_fixture,
                                      to_vary_in_each_message):
        message_fixture.update({'id': 4})
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, varied_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 1
        assert isinstance(view_components[0], Padding)

    def test_main_view_generates_EDITED_label(self, mocker,
                                              messages_successful_response):
        messages = messages_successful_response['messages']
        for message in messages:
            self.model.index['edited_messages'].add(message['id'])
            msg_box = MessageBox(message, self.model, message)
            view_components = msg_box.main_view()

            label = view_components[0].original_widget.contents[0]
            assert label[0].text == 'EDITED'
            assert label[1][1] == 7

    @pytest.mark.parametrize('key', keys_for_command('EDIT_MESSAGE'))
    @pytest.mark.parametrize('to_vary_in_each_message, realm_editing_allowed,\
                             expect_editing_to_succeed', [
        ({'sender_id': 2, 'timestamp': 45}, True, False),
        ({'sender_id': 1, 'timestamp': 1}, True, False),
        ({'sender_id': 1, 'timestamp': 45}, False, False),
        ({'sender_id': 1, 'timestamp': 45}, True, True),
    ], ids=['msg_sent_by_other_user',
            'time_limit_esceeded',
            'editing_not_allowed',
            'all_conditions_met'])
    def test_keypress_EDIT_MESSAGE(self, mocker, message_fixture,
                                   expect_editing_to_succeed,
                                   to_vary_in_each_message,
                                   realm_editing_allowed,
                                   key):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        size = (20,)
        msg_box = MessageBox(varied_message, self.model, message_fixture)
        msg_box.model.user_id = 1
        msg_box.model.initial_data = {
            'realm_allow_message_editing': realm_editing_allowed,
            'realm_message_content_edit_limit_seconds': 60,
        }
        msg_box.model.client.get_raw_message.return_value = {
            'raw_content': "Edit this message"
        }
        write_box = msg_box.model.controller.view.write_box
        write_box.msg_edit_id = None
        mocker.patch("zulipterminal.ui_tools.boxes.time", return_value=100)
        msg_box.keypress(size, key)

        if expect_editing_to_succeed:
            assert write_box.msg_edit_id == varied_message['id']
            write_box.msg_write_box.set_edit_text.assert_called_once_with(
                "Edit this message")
        else:
            assert write_box.msg_edit_id is None
            write_box.msg_write_box.set_edit_text.assert_not_called()

    @pytest.mark.parametrize('raw_html, expected_content', [
        ("""<blockquote>
                <p>A</p>
            </blockquote>
            <p>B</p>""", "░ A\n\nB"),
        ("""<blockquote>
                <blockquote>
                    <p>A</p>
                </blockquote>
                <p>B</p>
            </blockquote>
            <p>C</p>""", "░ ░ A\n\n░ B\n\nC"),
        ("""<blockquote>
                <blockquote>
                    <blockquote>
                        <p>A</p>
                    </blockquote>
                    <p>B</p>
                </blockquote>
                <p>C</p>
            </blockquote>
            <p>D</p>""", "░ ░ ░ A\n\n░ ░ B\n\n░ C\n\nD"),
        ("""<blockquote>
                <p>A<br/>B</p>
            </blockquote>
            <p>C</p>""", "░ A\n░ B\n\nC"),
        ("""<blockquote>
                <p><a href='https://chat.zulip.org/'</a>czo</p>
            </blockquote>""", "░ [czo](https://chat.zulip.org/)\n"),
        pytest.param("""<blockquote>
                            <blockquote>
                                <p>A<br>
                                B</p>
                            </blockquote>
                        </blockquote>
            """, "░ ░ A\n░ ░ B",
                     marks=pytest.mark.xfail(reason="rendered_bug")),
        pytest.param("""<blockquote>
                            <blockquote>
                                <p>A</p>
                            </blockquote>
                            <p>B</p>
                            <blockquote>
                                <p>C</p>
                            </blockquote>
                        </blockquote>
        """, "░ ░ A\n░ B\n░ ░ C",
                     marks=pytest.mark.xfail(reason="rendered_bug")),
    ], ids=[
        "quoted level 1",
        "quoted level 2",
        "quoted level 3",
        "multi-line quoting",
        "quoting with links",
        "multi-line level 2",
        "quoted level 2-1-2",
    ])
    def test_transform_content(self, mocker, raw_html, expected_content,
                               messages_successful_response):
        message = messages_successful_response['messages'][0]
        msg_box = MessageBox(message, self.model, message)
        msg_box.message['content'] = raw_html
        content = msg_box.transform_content()
        rendered_text = Text(content)
        assert rendered_text.text == expected_content

    # FIXME This is the same parametrize as MsgInfoView:test_height_reactions
    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'reactions': [{
                'emoji_name': 'thumbs_up',
                'emoji_code': '1f44d',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'zulip',
                'emoji_code': 'zulip',
                'user': {
                    'email': 'AARON@zulip.com',
                    'full_name': 'aaron',
                    'id': 1,
                },
                'reaction_type': 'zulip_extra_emoji'
            }, {
                'emoji_name': 'heart',
                'emoji_code': '2764',
                'user': {
                    'email': 'iago@zulip.com',
                    'full_name': 'Iago',
                    'id': 5,
                },
                'reaction_type': 'unicode_emoji'
            }]}
        ])
    def test_reactions_view(self, message_fixture, to_vary_in_each_message):
        self.model.user_id = 1
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, None)
        reactions = to_vary_in_each_message['reactions']

        reactions_view = msg_box.reactions_view(reactions)

        assert reactions_view.original_widget.text == (
                ':heart: 1 :thumbs_up: 1 :zulip: 2 '
        )
        assert reactions_view.original_widget.attrib == [
            ('reaction', 9), (None, 1),
            ('reaction', 13), (None, 1),
            ('reaction_mine', 9),
        ]

    @pytest.mark.parametrize(
        'key', keys_for_command('ENTER'),
        ids=lambda param: 'left_click-key:{}'.format(param)
    )
    def test_mouse_event_left_click(self, mocker, msg_box, key):
        size = (20, )
        col = 1
        row = 1
        focus = mocker.Mock()
        mocker.patch(BOXES + '.keys_for_command', return_value=[key])
        mocker.patch.object(msg_box, 'keypress')

        msg_box.mouse_event(size, 'mouse press', 1, col, row, focus)

        msg_box.keypress.assert_called_once_with(size, key)


class TestTopButton:
    @pytest.mark.parametrize('prefix', [
        None, '\N{BULLET}', '-', ('blue', 'o'), '',
    ])
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'ca…'),
        (9, 0, 'cap…'),
        (9, 1, 'ca…'),
        (10, 0, 'capt…'),
        (10, 1, 'cap…'),
        (11, 0, 'capti…'),
        (11, 1, 'capt…'),
        (11, 10, 'cap…'),
        (12, 0, 'caption'),
        (12, 1, 'capti…'),
        (12, 10, 'capt…'),
        (12, 100, 'cap…'),
        (13, 0, 'caption'),
        (13, 10, 'capti…'),
        (13, 100, 'capt…'),
        (13, 1000, 'cap…'),
        (15, 0, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capti…'),
        (25, 0, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          prefix,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        show_function = mocker.Mock()

        # To test having more space available with no bullet, but using
        # same short text, reduce the effective space available
        if prefix == '':
            width -= 2

        if isinstance(prefix, tuple):
            prefix = prefix[1]  # just checking text, not color

        if prefix is None:
            top_button = TopButton(controller=mocker.Mock(),
                                   caption=caption,
                                   show_function=show_function,
                                   width=width,
                                   count=count)
            prefix = '\N{BULLET}'
        else:
            top_button = TopButton(controller=mocker.Mock(),
                                   caption=caption,
                                   show_function=show_function,
                                   prefix_character=prefix,
                                   width=width,
                                   count=count)

        text = top_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        expected_text = ' {}{}{}{}'.format(
                (prefix + ' ') if prefix else '',
                short_text,
                (width - 2 - (2 if prefix else 0) - len(short_text) -
                 len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text


class TestStreamButton:
    @pytest.mark.parametrize('is_private, expected_prefix', [
        (True, 'P'),
        (False, '#'),
    ], ids=['private', 'not_private'])
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'ca…'),
        (9, 0, 'cap…'),
        (9, 1, 'ca…'),
        (10, 0, 'capt…'),
        (10, 1, 'cap…'),
        (11, 0, 'capti…'),
        (11, 1, 'capt…'),
        (11, 10, 'cap…'),
        (12, 0, 'caption'),
        (12, 1, 'capti…'),
        (12, 10, 'capt…'),
        (12, 100, 'cap…'),
        (13, 0, 'caption'),
        (13, 10, 'capti…'),
        (13, 100, 'capt…'),
        (13, 1000, 'cap…'),
        (15, 0, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capti…'),
        (25, 0, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          is_private, expected_prefix,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        controller = mocker.Mock()
        controller.model.muted_streams = {}
        properties = \
            [caption, 5, '#ffffff', is_private, 'Some Stream Description']
        view_mock = mocker.Mock()
        view_mock.palette = [(None, 'black', 'white')]
        stream_button = StreamButton(properties,
                                     controller=controller,
                                     view=view_mock,
                                     width=width,
                                     count=count)

        text = stream_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        expected_text = ' {} {}{}{}'.format(
                expected_prefix, short_text,
                (width - 4 - len(short_text) - len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text

    @pytest.mark.parametrize('stream_id, muted_streams, called_value,\
                             is_action_muting, updated_all_msgs', [
        (86, set(), 50, False, 400),
        (86, {86, 205}, None, True, 300),
        (205, {14, 99}, 0, False, 350),
    ], ids=[
        'unmuting stream 86 - 204 unreads',
        'muting stream 86',
        'unmuting stream 205 - 0 unreads',
    ])
    def test_mark_stream_muted(self, mocker, stream_button, is_action_muting,
                               stream_id, muted_streams, called_value,
                               updated_all_msgs) -> None:
        stream_button.stream_id = stream_id
        stream_button.count = 50  # Override value in fixture
        update_count = mocker.patch(TOPBUTTON + ".update_count")
        stream_button.controller.model.unread_counts = {
            'streams': {
                86: 50,
                14: 34,
            },
            'all_msg': 350,
        }
        stream_button.controller.model.is_muted_stream = (
            mocker.Mock(return_value=(stream_id in muted_streams))
        )
        stream_button.view.home_button.update_count = mocker.Mock()

        if is_action_muting:
            stream_button.mark_muted()
        else:
            stream_button.mark_unmuted()

        if called_value is not None:
            stream_button.update_count.assert_called_once_with(called_value)
        if called_value != 0:
            stream_button.view.home_button.update_count.\
                assert_called_once_with(updated_all_msgs)
        assert stream_button.model.unread_counts['all_msg'] == updated_all_msgs

    @pytest.mark.parametrize('key', keys_for_command('TOGGLE_TOPIC'))
    def test_keypress_ENTER_TOGGLE_TOPIC(self, mocker, stream_button, key):
        size = (200, 20)
        stream_button.view.left_panel = mocker.Mock()
        stream_button.view.left_panel.is_in_topic_view = None
        stream_button.view.left_panel.contents = [mocker.Mock(), mocker.Mock()]
        stream_button.keypress(size, key)

        assert stream_button.view.left_panel.is_in_topic_view is True
        (stream_button.view.left_panel.
            options.assert_called_once_with(height_type="weight"))

    @pytest.mark.parametrize('key', keys_for_command('TOGGLE_MUTE_STREAM'))
    def test_keypress_TOGGLE_MUTE_STREAM(self, mocker, stream_button, key):
        size = (20,)
        pop_up = mocker.patch(
            'zulipterminal.core.Controller.stream_muting_confirmation_popup')
        stream_button.keypress(size, key)
        pop_up.assert_called_once_with(stream_button)


class TestUserButton:
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'ca…'),
        (9, 0, 'cap…'),
        (9, 1, 'ca…'),
        (10, 0, 'capt…'),
        (10, 1, 'cap…'),
        (11, 0, 'capti…'),
        (11, 1, 'capt…'),
        (11, 10, 'cap…'),
        (12, 0, 'caption'),
        (12, 1, 'capti…'),
        (12, 10, 'capt…'),
        (12, 100, 'cap…'),
        (13, 0, 'caption'),
        (13, 10, 'capti…'),
        (13, 100, 'capt…'),
        (13, 1000, 'cap…'),
        (15, 0, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capti…'),
        (25, 0, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        user = {
            'email': 'some_email',  # value unimportant
            'user_id': 5,           # value unimportant
            'full_name': caption,
        }  # type: Dict[str, Any]
        user_button = UserButton(user,
                                 controller=mocker.Mock(),
                                 view=mocker.Mock(),
                                 width=width,
                                 color=None,  # FIXME test elsewhere?
                                 count=count)

        text = user_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        expected_text = ' \N{BULLET} {}{}{}'.format(
                short_text,
                (width - 4 - len(short_text) - len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text


class TestTopicButton:
    @pytest.mark.parametrize('width, count, stream_id, title, stream_name', [
        (8, 2, 86, 'topic1', 'Django'),
        (9, 1, 14, 'topic2', 'GSoC'),
        (25, 1000, 205, 'topic3', 'PTEST'),
    ])
    def test_init_calls_top_button(self, mocker, width, count, title,
                                   stream_id, stream_name):
        controller = mocker.Mock()
        controller.model.stream_dict = {
            205: {'name': 'PTEST'},
            86: {'name': 'Django'},
            14: {'name': 'GSoC'},
        }
        controller.model.muted_topics = []
        top_button = mocker.patch(TOPBUTTON+'.__init__')
        params = dict(controller=controller,
                      width=width,
                      count=count)

        topic_button = TopicButton(stream_id=stream_id,
                                   topic=title, **params)
        top_button.assert_called_once_with(
            caption=title,
            prefix_character='',
            show_function=controller.narrow_to_topic,
            **params)
        assert topic_button.stream_name == stream_name
        assert topic_button.stream_id == stream_id
        assert topic_button.topic_name == title

    @pytest.mark.parametrize('stream_name, title, muted_topics,\
                              is_muted_called', [
        ('Django', 'topic1', [['Django', 'topic1']], True),
        ('Django', 'topic2', [['Django', 'topic1']], False),
        ('GSoC', 'topic1', [['Django', 'topic1']], False),
    ], ids=[
        'stream_and_topic_match',
        'topic_mismatch',
        'stream_mismatch',
    ])
    def test_init_calls_mark_muted(self, mocker, stream_name, title,
                                   muted_topics, is_muted_called):
        mark_muted = mocker.patch(
            'zulipterminal.ui_tools.buttons.TopicButton.mark_muted')
        controller = mocker.Mock()
        controller.model.muted_topics = muted_topics
        controller.model.stream_dict = {
            205: {'name': stream_name}
        }
        topic_button = TopicButton(stream_id=205,
                                   topic=title, controller=controller,
                                   width=40, count=0)
        if is_muted_called:
            mark_muted.assert_called_once_with()
        else:
            mark_muted.assert_not_called()
