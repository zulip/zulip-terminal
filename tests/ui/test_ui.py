from typing import Any, Callable, List, Optional

import pytest
from pytest_mock import MockerFixture
from urwid import Widget

from zulipterminal.api_types import Composition
from zulipterminal.config.keys import keys_for_command
from zulipterminal.ui import LEFT_WIDTH, RIGHT_WIDTH, TAB_WIDTH, View
from zulipterminal.urwid_types import urwid_Box


CONTROLLER = "zulipterminal.core.Controller"
MODULE = "zulipterminal.ui"
VIEW = MODULE + ".View"


class TestView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.patch(CONTROLLER, return_value=None)
        self.model = mocker.patch(CONTROLLER + ".model")
        self.write_box = mocker.patch(MODULE + ".WriteBox")
        self.search_box = mocker.patch(MODULE + ".MessageSearchBox")
        mocker.patch(MODULE + ".TabView")
        mocker.patch(MODULE + ".LeftColumnView")
        mocker.patch("zulipterminal.ui_tools.views.urwid.Frame")
        mocker.patch("zulipterminal.ui_tools.views.MessageView")
        mocker.patch(MODULE + ".RightColumnView")

    @pytest.fixture
    def view(self, mocker: MockerFixture) -> View:
        # View is an urwid.Frame instance, a Box widget.
        mocker.patch(VIEW + ".sizing", return_value=frozenset({"box"}))

        return View(self.controller)

    def test_init(self, mocker: MockerFixture) -> None:
        main_window = mocker.patch(VIEW + ".main_window")
        view = View(self.controller)
        assert view.controller == self.controller
        assert view.model == self.model
        assert view.pinned_streams == self.model.pinned_streams
        assert view.unpinned_streams == self.model.unpinned_streams
        assert view.message_view is None
        self.write_box.assert_called_once_with(view)
        self.search_box.assert_called_once_with(self.controller)
        main_window.assert_called_once_with()

    def test_left_column_view(self, mocker: MockerFixture, view: View) -> None:
        left_view = mocker.patch(MODULE + ".LeftColumnView")
        left_tab = mocker.patch(MODULE + ".TabView")

        return_value = view.left_column_view()

        assert return_value == (left_view(view), left_tab())

    def test_middle_column_view(self, view: View, mocker: MockerFixture) -> None:
        middle_view = mocker.patch(MODULE + ".MiddleColumnView")
        line_box = mocker.patch(MODULE + ".urwid.LineBox")
        return_value = view.middle_column_view()
        middle_view.assert_called_once_with(
            view, view.model, view.write_box, view.search_box
        )
        assert view.middle_column == middle_view()
        assert return_value == line_box()

    def test_right_column_view(self, view: View, mocker: MockerFixture) -> None:
        right_view = mocker.patch(MODULE + ".RightColumnView")
        right_tab = mocker.patch(MODULE + ".TabView")
        line_box = mocker.patch(MODULE + ".urwid.LineBox")

        return_value = view.right_column_view()

        right_view.assert_called_once_with(view)
        assert view.users_view == right_view()
        assert return_value == (line_box(), right_tab())

    def test_set_footer_text_same_test(
        self, view: View, mocker: MockerFixture, text: List[str] = ["heya"]
    ) -> None:
        view._w.footer.text = text

        view.set_footer_text(text)

        view._w.footer.set_text.assert_not_called()

    def test_set_footer_text_default(self, view: View, mocker: MockerFixture) -> None:
        mocker.patch(VIEW + ".get_random_help", return_value=["some help text"])

        view.set_footer_text()

        view.frame.footer.set_text.assert_called_once_with(["some help text"])
        view.controller.update_screen.assert_called_once_with()
        assert view._is_footer_event_running is False

    def test_set_footer_text_specific_text(
        self, view: View, text: str = "blah"
    ) -> None:
        view.set_footer_text([text])

        view.frame.footer.set_text.assert_called_once_with([text])
        view.controller.update_screen.assert_called_once_with()
        assert view._is_footer_event_running is True

    def test_set_footer_text_with_duration(
        self,
        view: View,
        mocker: MockerFixture,
        custom_text: str = "custom",
        duration: Optional[float] = 5.3,
    ) -> None:
        mocker.patch(VIEW + ".get_random_help", return_value=["some help text"])
        mock_sleep = mocker.patch("time.sleep")

        view.set_footer_text([custom_text], duration=duration)

        view.frame.footer.set_text.assert_has_calls(
            [mocker.call([custom_text]), mocker.call(["some help text"])]
        )
        mock_sleep.assert_called_once_with(duration)
        assert view.controller.update_screen.call_count == 2
        assert view._is_footer_event_running is False

    @pytest.mark.parametrize("event_running", [True, False])
    def test_set_footer_text_on_context_change(
        self, view: View, mocker: MockerFixture, event_running: bool
    ) -> None:
        mocker.patch(VIEW + ".get_random_help", return_value=["some help text"])
        view._is_footer_event_running = event_running

        view.set_footer_text(context_change=True)

        if event_running:
            view.frame.footer.set_text.assert_not_called()
            view.controller.update_screen.assert_not_called()
        else:
            view.frame.footer.set_text.assert_called_once_with(["some help text"])
            view.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize(
        "suggestions, state, truncated, footer_text",
        [
            ([], None, False, [" [No matches found]"]),
            (["some", "text"], None, False, [[" "], " some ", " text "]),
            (["some", "text"], None, True, [[" "], " some ", " text ", " [more] "]),
            (
                ["some", "text"],
                0,
                False,
                [[" "], ("footer_contrast", " some "), " text "],
            ),
            (
                ["some", "text"],
                0,
                True,
                [[" "], ("footer_contrast", " some "), " text ", " [more] "],
            ),
            (
                ["some", "text"],
                -1,
                False,
                [[" "], " some ", ("footer_contrast", " text ")],
            ),
        ],
        ids=[
            "no_matches",
            "no_highlight",
            "no_highlight_truncated",
            "first_suggestion_highlighted",
            "first_suggestion_highlighted_truncated",
            "last_suggestion_highlighted",
        ],
    )
    def test_set_typeahead_footer(
        self,
        mocker: MockerFixture,
        view: View,
        state: Optional[int],
        suggestions: List[str],
        truncated: bool,
        footer_text: List[Any],
    ) -> None:
        set_footer_text = mocker.patch(VIEW + ".set_footer_text")
        view.set_typeahead_footer(suggestions, state, truncated)
        set_footer_text.assert_called_once_with(footer_text)

    def test_footer_view(self, mocker: MockerFixture, view: View) -> None:
        footer = view.footer_view()
        assert isinstance(footer.text, str)

    def test_main_window(
        self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        left = mocker.patch(VIEW + ".left_column_view", return_value=("PANEL", "TAB"))

        # NOTE: Use monkeypatch not patch, as view doesn't exist until later
        def just_set_message_view(self: Any) -> None:
            self.message_view = mocker.Mock(read_message=lambda: None)

        monkeypatch.setattr(View, "middle_column_view", just_set_message_view)

        right = mocker.patch(VIEW + ".right_column_view", return_value=("PANEL", "TAB"))
        col = mocker.patch(MODULE + ".urwid.Columns")
        frame = mocker.patch(MODULE + ".urwid.Frame")
        title_divider = mocker.patch(MODULE + ".urwid.Divider")
        text = mocker.patch(MODULE + ".urwid.Text")
        footer_view = mocker.patch(VIEW + ".footer_view")
        show_left_panel = mocker.patch(VIEW + ".show_left_panel")

        full_name = "Bob James"
        email = "Bob@bob.com"
        server = "https://chat.zulip.zulip/"
        server_name = "Test Organization"

        self.controller.model = self.model
        self.model.user_full_name = full_name
        self.model.user_email = email
        self.model.server_url = server
        self.model.server_name = server_name

        title_length = len(email) + len(full_name) + len(server) + len(server_name) + 11

        view = View(self.controller)

        left.assert_called_once_with()
        # NOTE: Don't check center here, as we're monkeypatching it
        right.assert_called_once_with()

        expected_column_calls = [
            mocker.call(
                [
                    (TAB_WIDTH, view.left_tab),
                    ("weight", 10, mocker.ANY),  # ANY is a center
                    (TAB_WIDTH, view.right_tab),
                ],
                focus_column=0,
            ),
            mocker.call()._contents.set_focus_changed_callback(
                view.message_view.read_message
            ),
            mocker.call(
                [
                    title_divider(),
                    (title_length, text()),
                    title_divider(),
                ]
            ),
        ]
        col.assert_has_calls(expected_column_calls)

        assert view.body == col()
        frame.assert_called_once_with(
            view.body, col(), focus_part="body", footer=footer_view()
        )
        assert view.frame == frame()
        show_left_panel.assert_called_once_with(visible=True)

    @pytest.mark.parametrize("autohide", [True, False])
    @pytest.mark.parametrize("visible", [True, False])
    @pytest.mark.parametrize("test_method", ["left_panel", "right_panel"])
    def test_show_panel_methods(
        self,
        mocker: MockerFixture,
        visible: bool,
        autohide: bool,
        test_method: str,
    ) -> None:
        self.controller.autohide = autohide
        view = View(self.controller)
        view.frame.body = view.body

        tail = [None, 0, 0, "top", None, "relative", 100, None, 0, 0]
        if test_method == "left_panel":
            expected_overlay_options = ["left", None, "given", LEFT_WIDTH + 1] + tail
            expected_tab = view.left_tab
            expected_panel = view.left_panel

            view.show_left_panel(visible=visible)
        else:
            expected_overlay_options = ["right", None, "given", RIGHT_WIDTH + 1] + tail
            expected_tab = view.right_tab
            expected_panel = view.right_panel

            view.show_right_panel(visible=visible)

        if autohide:
            if visible:
                assert (expected_panel, mocker.ANY) in view.frame.body.top_w.contents
                assert view.frame.body.bottom_w == view.body
                assert view.frame.body.contents[1][1] == tuple(expected_overlay_options)
            else:
                assert (expected_tab, mocker.ANY) in view.frame.body.contents
                assert view.body.focus_position == 1
        else:
            # No change
            assert view.frame.body.contents[0][0] == view.left_panel
            assert view.frame.body.contents[2][0] == view.right_panel

    def test_keypress_normal_mode_navigation(
        self,
        view: View,
        mocker: MockerFixture,
        # TODO: Improve `widget_size`'s return type, likely via Protocols.
        widget_size: Callable[[Widget], urwid_Box],
        navigation_key: str,
    ) -> None:
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = widget_size(view)

        super_keypress = mocker.patch(MODULE + ".urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: False

        view.keypress(size, navigation_key)

        super_keypress.assert_called_once_with(size, navigation_key)

    @pytest.mark.parametrize("key", keys_for_command("ALL_MENTIONS"))
    def test_keypress_ALL_MENTIONS(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.mentioned_button = mocker.Mock()
        view.mentioned_button.activate = mocker.Mock()
        view.controller.is_in_editor_mode = lambda: False
        size = widget_size(view)

        view.keypress(size, key)

        view.mentioned_button.activate.assert_called_once_with(key)

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MESSAGE"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_STREAM_MESSAGE(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        autohide: bool,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        mocked_middle_column = mocker.patch.object(view, "middle_column", create=True)
        view.body = mocker.Mock()
        view.controller.autohide = autohide
        view.body.contents = ["streams", "messages", "users"]
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        view.controller.is_in_editor_mode = lambda: False
        size = widget_size(view)

        returned_key = view.keypress(size, key)

        mocked_middle_column.keypress.assert_called_once_with(size, key)
        assert returned_key == key
        assert view.body.focus_col == 1

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_autohide_users(
        self,
        view: View,
        mocker: MockerFixture,
        autohide: bool,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        mocked_users_view = mocker.patch.object(view, "users_view", create=True)
        view.body = mocker.Mock()
        view.controller.autohide = autohide
        view.body.contents = ["streams", "messages", mocker.Mock()]
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        size = widget_size(view)
        view.controller.is_in_editor_mode = lambda: False
        view.body.focus_position = None

        view.keypress(size, key)

        mocked_users_view.keypress.assert_called_once_with(size, key)
        assert view.body.focus_position == 2

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_STREAMS"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_autohide_streams(
        self,
        view: View,
        mocker: MockerFixture,
        autohide: bool,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.left_col_w = mocker.Mock()
        view.controller.autohide = autohide
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), "messages", "users"]
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        size = widget_size(view)
        view.controller.is_in_editor_mode = lambda: False
        view.body.focus_position = None

        view.keypress(size, key)

        view.left_panel.keypress.assert_called_once_with(size, key)
        assert view.body.focus_position == 0

    @pytest.mark.parametrize(
        "draft",
        [
            {
                "type": "stream",
                "to": "zulip terminal",
                "subject": "open draft",
                "content": "this is a stream message content",
            },
            {
                "type": "private",
                "to": [1, 2],
                "content": "this is a private message content",
            },
            None,
        ],
        ids=[
            "stream_draft_composition",
            "private_draft_composition",
            "no_draft_composition",
        ],
    )
    @pytest.mark.parametrize("key", keys_for_command("OPEN_DRAFT"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_OPEN_DRAFT(
        self,
        view: View,
        mocker: MockerFixture,
        draft: Optional[Composition],
        key: str,
        autohide: bool,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.body = mocker.Mock()
        view.body.contents = ["streams", "messages", "users"]
        view.left_panel = mocker.Mock()
        view.middle_column = mocker.Mock()
        view.right_panel = mocker.Mock()
        view.controller.autohide = autohide
        view.controller.report_error = mocker.Mock()
        view.controller.is_in_editor_mode = lambda: False
        view.model.stream_id_from_name.return_value = 10
        view.model.session_draft_message.return_value = draft
        view.model.user_id_email_dict = {1: "foo@zulip.com", 2: "bar@gmail.com"}
        mocked_stream_box_view = mocker.patch.object(view.write_box, "stream_box_view")
        mocked_private_box_view = mocker.patch.object(
            view.write_box, "private_box_view"
        )

        size = widget_size(view)
        view.keypress(size, key)

        if draft:
            if draft["type"] == "stream":
                mocked_stream_box_view.assert_called_once_with(
                    caption=draft["to"], title=draft["subject"], stream_id=10
                )
            else:
                mocked_private_box_view.assert_called_once_with(
                    recipient_user_ids=draft["to"],
                )

            assert view.body.focus_col == 1
            assert view.write_box.msg_write_box.edit_text == draft["content"]
            assert view.write_box.msg_write_box.edit_pos == len(draft["content"])
            view.middle_column.set_focus.assert_called_once_with("footer")
        else:
            view.controller.report_error.assert_called_once_with(
                ["No draft message was saved in this session."]
            )

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    def test_keypress_edit_mode(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()

        mocker.patch(MODULE + ".urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: True
        size = widget_size(view)

        view.keypress(size, key)

        view.controller.current_editor().keypress.assert_called_once_with(
            (size[1],), key
        )
