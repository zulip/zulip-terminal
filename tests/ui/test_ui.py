import pytest

from zulipterminal.config.keys import keys_for_command
from zulipterminal.ui import View


class TestView:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.patch(
            "zulipterminal.core.Controller", return_value=None
        )
        self.model = mocker.patch("zulipterminal.core.Controller.model")
        self.write_box = mocker.patch("zulipterminal.ui.WriteBox")
        self.search_box = mocker.patch("zulipterminal.ui.SearchBox")

    @pytest.fixture
    def view(self, mocker):
        main_window = mocker.patch("zulipterminal.ui.View.main_window")
        # View is an urwid.Frame instance, a Box widget.
        mocker.patch("zulipterminal.ui.View.sizing", return_value=frozenset({"box"}))
        return View(self.controller)

    def test_init(self, mocker):
        main_window = mocker.patch("zulipterminal.ui.View.main_window")
        view = View(self.controller)
        assert view.controller == self.controller
        assert view.model == self.model
        assert view.pinned_streams == self.model.pinned_streams
        assert view.unpinned_streams == self.model.unpinned_streams
        assert view.message_view is None
        self.write_box.assert_called_once_with(view)
        self.search_box.assert_called_once_with(self.controller)
        main_window.assert_called_once_with()

    def test_left_column_view(self, mocker, view):
        left_view = mocker.patch("zulipterminal.ui.LeftColumnView")
        return_value = view.left_column_view()
        assert return_value == left_view(view)

    def test_middle_column_view(self, view, mocker):
        middle_view = mocker.patch("zulipterminal.ui.MiddleColumnView")
        line_box = mocker.patch("zulipterminal.ui.urwid.LineBox")
        return_value = view.middle_column_view()
        middle_view.assert_called_once_with(
            view, view.model, view.write_box, view.search_box
        )
        assert view.middle_column == middle_view()
        assert return_value == line_box()

    def test_right_column_view(self, view, mocker):
        right_view = mocker.patch("zulipterminal.ui.RightColumnView")
        line_box = mocker.patch("zulipterminal.ui.urwid.LineBox")
        return_value = view.right_column_view()
        right_view.assert_called_once_with(View.RIGHT_WIDTH, view)
        assert view.users_view == right_view()
        assert return_value == line_box()

    def test_set_footer_text_default(self, view, mocker):
        mocker.patch(
            "zulipterminal.ui.View.get_random_help", return_value=["some help text"]
        )

        view.set_footer_text()

        view._w.footer.set_text.assert_called_once_with(["some help text"])
        view.controller.update_screen.assert_called_once_with()

    def test_set_footer_text_specific_text(self, view, text="blah"):
        view.set_footer_text([text])

        view._w.footer.set_text.assert_called_once_with([text])
        view.controller.update_screen.assert_called_once_with()

    def test_set_footer_text_with_duration(
        self, view, mocker, custom_text="custom", duration=5.3
    ):
        mocker.patch(
            "zulipterminal.ui.View.get_random_help", return_value=["some help text"]
        )
        mock_sleep = mocker.patch("time.sleep")

        view.set_footer_text([custom_text], duration)

        view._w.footer.set_text.assert_has_calls(
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
            (["some", "text"], 0, False, [[" "], ("code", " some "), " text "]),
            (
                ["some", "text"],
                0,
                True,
                [[" "], ("code", " some "), " text ", " [more] "],
            ),
            (["some", "text"], -1, False, [[" "], " some ", ("code", " text ")]),
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
        self, mocker, view, state, suggestions, truncated, footer_text
    ):
        set_footer_text = mocker.patch("zulipterminal.ui.View.set_footer_text")
        view.set_typeahead_footer(suggestions, state, truncated)
        set_footer_text.assert_called_once_with(footer_text)

    def test_footer_view(self, mocker, view):
        footer = view.footer_view()
        assert isinstance(footer.text, str)

    def test_main_window(self, mocker, monkeypatch):
        left = mocker.patch("zulipterminal.ui.View.left_column_view")

        # NOTE: Use monkeypatch not patch, as view doesn't exist until later
        def just_set_message_view(self):
            self.message_view = mocker.Mock(read_message=lambda: None)

        monkeypatch.setattr(View, "middle_column_view", just_set_message_view)

        right = mocker.patch("zulipterminal.ui.View.right_column_view")
        col = mocker.patch("zulipterminal.ui.urwid.Columns")
        frame = mocker.patch("zulipterminal.ui.urwid.Frame")
        title_divider = mocker.patch("zulipterminal.ui.urwid.Divider")
        text = mocker.patch("zulipterminal.ui.urwid.Text")
        footer_view = mocker.patch("zulipterminal.ui.View.footer_view")

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
                    (View.LEFT_WIDTH, left()),
                    ("weight", 10, mocker.ANY),  # ANY is a center
                    (0, right()),
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

    @pytest.mark.parametrize("autohide", [True, False])
    @pytest.mark.parametrize("visible, width", [(True, View.LEFT_WIDTH), (False, 0)])
    def test_show_left_panel(self, mocker, view, visible, width, autohide):
        view.left_panel = mocker.Mock()
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
        view.body.focus_position = None
        view.controller.autohide = autohide

        view.show_left_panel(visible=visible)

        if autohide:
            view.body.options.assert_called_once_with(
                width_type="given", width_amount=width
            )
            if visible:
                assert view.body.focus_position == 0
        else:
            view.body.options.assert_not_called()

    @pytest.mark.parametrize("autohide", [True, False])
    @pytest.mark.parametrize("visible, width", [(True, View.RIGHT_WIDTH), (False, 0)])
    def test_show_right_panel(self, mocker, view, visible, width, autohide):
        view.right_panel = mocker.Mock()
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
        view.body.focus_position = None
        view.controller.autohide = autohide

        view.show_right_panel(visible=visible)

        if autohide:
            view.body.options.assert_called_once_with(
                width_type="given", width_amount=width
            )
            if visible:
                assert view.body.focus_position == 2
        else:
            view.body.options.assert_not_called()

    def test_keypress_normal_mode_navigation(
        self, view, mocker, widget_size, navigation_key_expected_key_pair
    ):
        key, expected_key = navigation_key_expected_key_pair
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()
        size = widget_size(view)

        super_keypress = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: False

        view.keypress(size, key)

        super_keypress.assert_called_once_with(size, expected_key)

    @pytest.mark.parametrize("key", keys_for_command("ALL_MENTIONS"))
    def test_keypress_ALL_MENTIONS(self, view, mocker, key, widget_size):
        view.body = mocker.Mock()
        view.body.focus_col = None
        view.controller.is_in_editor_mode = lambda: False
        size = widget_size(view)
        view.model.controller.narrow_to_all_mentions = mocker.Mock()

        view.keypress(size, key)

        view.model.controller.narrow_to_all_mentions.assert_called_once_with()
        assert view.body.focus_col == 1

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MESSAGE"))
    def test_keypress_STREAM_MESSAGE(self, view, mocker, key, widget_size):
        view.middle_column = mocker.Mock()
        view.body = mocker.Mock()
        view.controller.is_in_editor_mode = lambda: False
        size = widget_size(view)

        returned_key = view.keypress(size, key)

        view.middle_column.keypress.assert_called_once_with(size, key)
        assert returned_key == key
        assert view.body.focus_col == 1

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_autohide_users(self, view, mocker, autohide, key, widget_size):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.controller.autohide = autohide
        view.body.contents = ["streams", "messages", mocker.Mock()]
        view.user_search = mocker.Mock()
        view.left_panel = mocker.Mock()
        view.right_panel = mocker.Mock()
        size = widget_size(view)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.is_in_editor_mode = lambda: False

        view.body.focus_position = None

        view.keypress(size, key)

        view.users_view.keypress.assert_called_once_with(size, key)
        assert view.body.focus_position == 2
        view.user_search.set_edit_text.assert_called_once_with("")
        view.controller.enter_editor_mode_with.assert_called_once_with(view.user_search)

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_STREAMS"))
    @pytest.mark.parametrize("autohide", [True, False], ids=["autohide", "no_autohide"])
    def test_keypress_autohide_streams(self, view, mocker, autohide, key, widget_size):
        view.stream_w = mocker.Mock()
        view.left_col_w = mocker.Mock()
        view.stream_w.stream_search_box = mocker.Mock()
        view.controller.autohide = autohide
        view.body = mocker.Mock()
        view.body.contents = [mocker.Mock(), "messages", "users"]
        view.left_panel = mocker.Mock()
        view.left_panel.is_in_topic_view = False
        view.right_panel = mocker.Mock()
        size = widget_size(view)

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")
        view.controller.is_in_editor_mode = lambda: False

        view.body.focus_position = None

        view.keypress(size, key)

        view.left_panel.keypress.assert_called_once_with(size, key)
        assert view.body.focus_position == 0
        view.stream_w.stream_search_box.set_edit_text.assert_called_once_with("")
        view.controller.enter_editor_mode_with.assert_called_once_with(
            view.stream_w.stream_search_box
        )

    @pytest.mark.parametrize("key", keys_for_command("SEARCH_PEOPLE"))
    def test_keypress_edit_mode(self, view, mocker, key, widget_size):
        view.users_view = mocker.Mock()
        view.body = mocker.Mock()
        view.user_search = mocker.Mock()

        super_view = mocker.patch("zulipterminal.ui.urwid.WidgetWrap.keypress")

        view.controller.is_in_editor_mode = lambda: True
        size = widget_size(view)

        view.keypress(size, key)

        view.controller.current_editor().keypress.assert_called_once_with(
            (size[1],), key
        )
