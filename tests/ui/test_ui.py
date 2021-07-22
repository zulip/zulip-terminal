from typing import Any, Callable, List, Optional, Tuple

import pytest
from pytest_mock import MockerFixture
from typing_extensions import Literal
from urwid import Columns, Widget

from zulipterminal.api_types import Composition
from zulipterminal.config.keys import keys_for_command
from zulipterminal.core import Layout
from zulipterminal.ui import LEFT_WIDTH, MAX_APP_WIDTH, RIGHT_WIDTH, TAB_WIDTH, View
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
        self.search_box = mocker.patch(MODULE + ".SearchBox")
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
        assert view.mode == "normal"

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

    def test_set_footer_text_default(self, view: View, mocker: MockerFixture) -> None:
        mocker.patch(VIEW + ".get_random_help", return_value=["some help text"])

        view.set_footer_text()

        view.frame.footer.set_text.assert_called_once_with(["some help text"])
        view.controller.update_screen.assert_called_once_with()

    def test_set_footer_text_specific_text(
        self, view: View, text: str = "blah"
    ) -> None:
        view.set_footer_text([text])

        view.frame.footer.set_text.assert_called_once_with([text])
        view.controller.update_screen.assert_called_once_with()

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
        self.controller.layout = "autohide"
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

    @pytest.mark.parametrize("layout", ["autohide", "no_autohide", "dynamic"])
    @pytest.mark.parametrize("visible", [True, False])
    @pytest.mark.parametrize("test_method", ["left_panel", "right_panel"])
    @pytest.mark.parametrize(
        "mode, width_options",
        [
            ("small", ("given", LEFT_WIDTH)),
            ("normal", ("given", LEFT_WIDTH)),
            ("wide", ("given", LEFT_WIDTH)),
        ],
    )
    def test_show_panel_methods(
        self,
        mocker: MockerFixture,
        visible: bool,
        width_options: Tuple[str, int],
        layout: Layout,
        test_method: str,
        mode: Literal["small", "normal", "wide"],
    ) -> None:
        self.controller.layout = layout
        if mode == "small":
            self.controller.layout = "autohide"
        view = View(self.controller)
        view.frame.body = view.body
        view.mode = mode

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

        if layout == "autohide" or mode == "small":
            if visible:
                assert (expected_panel, mocker.ANY) in view.frame.body.top_w.contents
                assert view.frame.body.bottom_w == view.body
                assert view.frame.body.contents[1][1] == tuple(expected_overlay_options)
            else:
                assert (expected_tab, mocker.ANY) in view.frame.body.contents
        else:
            # No change
            assert view.frame.body.contents[0][0] == view.left_panel
            assert view.frame.body.contents[2][0] == view.right_panel

    @pytest.mark.parametrize(
        "focus_pos, overlay",
        [
            (0, True),
            (2, True),
            (0, False),
            (1, False),
            (2, False),
        ],
    )
    def test_focus_panel_property_getter(
        self, view: View, focus_pos: int, overlay: bool
    ) -> None:
        if overlay:
            top_w = view.frame.body.top_w
            default_options = ("weight", 1, True)
            if focus_pos == 0:
                top_w.contents[0] = (view.left_panel, default_options)
            else:
                top_w.contents[1] = (view.right_panel, default_options)
        view.frame.body = view.body
        view.body.focus_position = focus_pos

        focus_panel = view.focus_panel

        assert focus_panel == focus_pos

    @pytest.mark.parametrize(
        "focus_pos, left_visible, right_visible",
        [
            (0, True, False),
            (1, False, False),
            (2, False, True),
        ],
    )
    def test_focus_panel_property_setter(
        self,
        mocker: MockerFixture,
        view: View,
        focus_pos: int,
        left_visible: bool,
        right_visible: bool,
    ) -> None:
        show_left_panel = mocker.patch(VIEW + ".show_left_panel")
        show_right_panel = mocker.patch(VIEW + ".show_right_panel")

        view.focus_panel = focus_pos

        assert view.body.focus_position == focus_pos
        show_left_panel.assert_called_once_with(visible=left_visible)
        show_right_panel.assert_called_once_with(visible=right_visible)

    def test_keypress_normal_mode_navigation(
        self,
        view: View,
        mocker: MockerFixture,
        # TODO: Improve `widget_size`'s return type, likely via Protocols.
        widget_size: Callable[[Widget], urwid_Box],
        navigation_key_expected_key_pair: Tuple[str, str],
    ) -> None:
        key, expected_key = navigation_key_expected_key_pair
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = widget_size(view)

        super_keypress = mocker.patch(MODULE + ".urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: False

        view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)

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
    def test_keypress_STREAM_MESSAGE_from_different_panel(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        mocked_middle_column = mocker.patch.object(view, "middle_column", create=True)
        view.controller.is_in_editor_mode = lambda: False
        size = widget_size(view)
        view.frame.body = view.body
        view.focus_panel = 0

        returned_key = view.keypress(size, key)

        mocked_middle_column.keypress.assert_called_once_with(size, key)
        assert returned_key == key
        assert view.focus_panel == 1

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    def test_keypress_SEARCH_PEOPLE_from_different_panel(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        mocked_users_view = mocker.patch.object(view, "users_view", create=True)
        size = widget_size(view)
        view.controller.is_in_editor_mode = lambda: False
        view.frame.body = view.body
        view.focus_panel = 0

        view.keypress(size, key)

        mocked_users_view.keypress.assert_called_once_with(size, key)
        assert view.focus_panel == 2

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_STREAMS"))
    def test_keypress_SEARCH_STREAMS_from_different_panel(
        self,
        view: View,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.left_panel = mocker.Mock()
        size = widget_size(view)
        view.controller.is_in_editor_mode = lambda: False
        view.frame.body = view.body
        view.focus_panel = 1

        view.keypress(size, key)

        view.left_panel.keypress.assert_called_once_with(size, key)
        assert view.focus_panel == 0

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
                "to": ["foo@zulip.com", "bar@gmail.com"],
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
    def test_keypress_OPEN_DRAFT(
        self,
        view: View,
        mocker: MockerFixture,
        draft: Composition,
        key: str,
        widget_size: Callable[[Widget], urwid_Box],
    ) -> None:
        view.frame.body = view.body
        view.middle_column = mocker.Mock()
        view.controller.report_error = mocker.Mock()
        view.controller.is_in_editor_mode = lambda: False
        view.model.stream_id_from_name.return_value = 10
        view.model.session_draft_message.return_value = draft
        view.model.user_dict = {
            "foo@zulip.com": {"user_id": 1},
            "bar@gmail.com": {"user_id": 2},
        }
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
                    emails=draft["to"], recipient_user_ids=[1, 2]
                )

            assert view.focus_panel == 1
            assert view.write_box.msg_write_box.edit_text == draft["content"]
            assert view.write_box.msg_write_box.edit_pos == len(draft["content"])
            view.middle_column.set_focus.assert_called_once_with("footer")
        else:
            view.controller.report_error.assert_called_once_with(
                "No draft message was saved in this session."
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

        super_view = mocker.patch(MODULE + ".urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: True
        size = widget_size(view)

        view.keypress(size, key)

        view.controller.current_editor().keypress.assert_called_once_with(
            (size[1],), key
        )

    @pytest.mark.parametrize("maxcols", [50, MAX_APP_WIDTH, 600])
    @pytest.mark.parametrize(
        "has_border", [True, False], ids=["has_border", "has_no_border"]
    )
    def test_add_padding_and_border_to_frame(
        self,
        view: View,
        mocker: MockerFixture,
        maxcols: int,
        has_border: bool,
    ) -> None:
        view.has_border = has_border

        view.add_padding_and_border_to_frame(maxcols)

        if maxcols > MAX_APP_WIDTH and not has_border:
            assert view._w.align == "center"
        elif maxcols < MAX_APP_WIDTH and has_border:
            assert view._w == view.frame
        assert view.has_border is False if maxcols <= MAX_APP_WIDTH else True

    @pytest.mark.parametrize("mode", ["small", "normal", "wide"])
    @pytest.mark.parametrize("focus_pos", [0, 1, 2], ids=["left", "center", "right"])
    @pytest.mark.parametrize(
        "size, expected_mode, expected_width_type, expected_width_amount",
        [
            ((80, 24), "small", ["given", "given"], [TAB_WIDTH, TAB_WIDTH]),
            ((102, 24), "small", ["given", "given"], [TAB_WIDTH, TAB_WIDTH]),
            ((103, 24), "normal", ["given", "given"], [LEFT_WIDTH, RIGHT_WIDTH]),
            ((140, 24), "normal", ["given", "given"], [LEFT_WIDTH, RIGHT_WIDTH]),
            ((159, 24), "normal", ["given", "given"], [LEFT_WIDTH, RIGHT_WIDTH]),
            ((160, 24), "wide", ["weight", "weight"], [20, 20]),
            ((200, 24), "wide", ["weight", "weight"], [20, 20]),
        ],
    )
    def test_render_dynamic_layout(
        self,
        mocker: MockerFixture,
        view: View,
        mode: Literal["small", "normal", "wide"],
        focus_pos: int,
        size: urwid_Box,
        expected_mode: Literal["small", "normal", "wide"],
        expected_width_type: List[str],
        expected_width_amount: List[int],
    ) -> None:
        def side_panel_options() -> Tuple[List[str], List[int]]:
            width_type = [view.body.contents[c][1][0] for c in [0, 2]]
            width_amount = [view.body.contents[c][1][1] for c in [0, 2]]
            return width_type, width_amount

        mocker.patch(MODULE + ".urwid.widget.validate_size", return_value=None)
        mocked_padding_func = mocker.patch(VIEW + ".add_padding_and_border_to_frame")
        view.layout = "dynamic"
        view.mode = mode
        view.body = Columns(
            [(5, view.left_panel), mocker.Mock(), (5, view.right_panel)]
        )
        view.frame.body = view.body
        view.focus_panel = focus_pos
        mode_changed = expected_mode != mode
        old_width_type, old_width_amount = side_panel_options()

        view.render(size, focus=False)

        new_width_type, new_width_amount = side_panel_options()
        # Check focus doesn't change
        # in small mode `show_panel` takes care of width which is already tested
        assert view.focus_panel == focus_pos

        assert view.mode == expected_mode
        mocked_padding_func.assert_called_once_with(size[0])

        if mode_changed:
            assert new_width_type == expected_width_type
            assert new_width_amount == expected_width_amount
        else:
            # No change
            assert new_width_amount == old_width_amount
            assert new_width_type == old_width_type
