import os
import webbrowser
from platform import platform
from threading import Thread, Timer
from typing import Any, Dict, List, Optional, Set, Tuple

import pyperclip
import pytest
from pytest import param as case
from pytest_mock import MockerFixture

from zulipterminal.config.themes import generate_theme
from zulipterminal.core import Controller
from zulipterminal.helper import Index
from zulipterminal.version import ZT_VERSION


MODULE = "zulipterminal.core"
MODEL = MODULE + ".Model"
VIEW = MODULE + ".View"

SERVER_URL = "https://chat.zulip.zulip"


class TestController:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        mocker.patch("zulipterminal.ui_tools.messages.MessageBox.main_view")
        self.client = mocker.patch("zulip.Client")
        # Patch init only, in general, allowing specific patching elsewhere
        self.model = mocker.patch(MODEL + ".__init__", return_value=None)
        self.view = mocker.patch(MODULE + ".View.__init__", return_value=None)
        self.model.view = self.view
        self.view.focus_col = 1

    @pytest.fixture
    def controller(self, mocker: MockerFixture) -> Controller:
        # Patch these unconditionally to avoid calling in __init__
        self.poll_for_events = mocker.patch(MODEL + ".poll_for_events")
        mocker.patch(MODULE + ".Controller.show_loading")
        self.main_loop = mocker.patch(
            MODULE + ".urwid.MainLoop", return_value=mocker.Mock()
        )

        self.config_file = "path/to/zuliprc"
        self.theme_name = "zt_dark"
        self.theme = generate_theme("zt_dark", 256)
        self.in_explore_mode = False
        self.autohide = True  # FIXME Add tests for no-autohide
        self.notify_enabled = False
        self.maximum_footlinks = 3
        result = Controller(
            config_file=self.config_file,
            maximum_footlinks=self.maximum_footlinks,
            theme_name=self.theme_name,
            theme=self.theme,
            color_depth=256,
            in_explore_mode=self.in_explore_mode,
            debug_path=None,
            **dict(
                autohide=self.autohide,
                notify=self.notify_enabled,
            ),
        )
        result.view.message_view = mocker.Mock()  # set in View.__init__
        result.model.server_url = SERVER_URL
        return result

    def test_initialize_controller(
        self, controller: Controller, mocker: MockerFixture
    ) -> None:
        self.client.assert_called_once_with(
            config_file=self.config_file,
            client="ZulipTerminal/" + ZT_VERSION + " " + platform(),
        )
        self.model.assert_called_once_with(controller)
        self.view.assert_called_once_with(controller)
        self.poll_for_events.assert_called_once_with()
        assert controller.theme == self.theme
        assert controller.maximum_footlinks == self.maximum_footlinks
        assert self.main_loop.call_count == 1
        controller.loop.watch_pipe.assert_has_calls(
            [
                mocker.call(controller._draw_screen),
                mocker.call(controller._raise_exception),
            ]
        )

    def test_initial_editor_mode(self, controller: Controller) -> None:
        assert not controller.is_in_editor_mode()

    def test_current_editor_error_if_no_editor(self, controller: Controller) -> None:
        with pytest.raises(AssertionError):
            controller.current_editor()

    def test_editor_mode_entered_from_initial(
        self, mocker: MockerFixture, controller: Controller
    ) -> None:
        editor = mocker.Mock()

        controller.enter_editor_mode_with(editor)

        assert controller.is_in_editor_mode()
        assert controller.current_editor() == editor

    def test_editor_mode_error_on_multiple_enter(
        self, mocker: MockerFixture, controller: Controller
    ) -> None:
        controller.enter_editor_mode_with(mocker.Mock())

        with pytest.raises(AssertionError):
            controller.enter_editor_mode_with(mocker.Mock())

    def test_editor_mode_exits_after_entering(
        self, mocker: MockerFixture, controller: Controller
    ) -> None:
        controller.enter_editor_mode_with(mocker.Mock())
        controller.exit_editor_mode()

        assert not controller.is_in_editor_mode()

    def test_narrow_to_stream(
        self,
        mocker: MockerFixture,
        controller: Controller,
        index_stream: Index,
        stream_id: int = 205,
        stream_name: str = "PTEST",
    ) -> None:
        controller.model.narrow = []
        controller.model.index = index_stream
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.stream_dict = {
            stream_id: {
                "color": "#ffffff",
                "name": stream_name,
            }
        }
        controller.model.muted_streams = set()
        mocker.patch(MODEL + ".is_muted_topic", return_value=False)

        controller.narrow_to_stream(stream_name=stream_name)

        assert controller.model.stream_id == stream_id
        assert controller.model.narrow == [["stream", stream_name]]
        controller.view.message_view.log.clear.assert_called_once_with()

        widget = controller.view.message_view.log.extend.call_args_list[0][0][0][0]
        id_list = index_stream["stream_msg_ids_by_stream_id"][stream_id]
        assert {widget.original_widget.message["id"]} == id_list

    @pytest.mark.parametrize(
        ["initial_narrow", "initial_stream_id", "anchor", "expected_final_focus"],
        [
            ([], None, None, 537289),
            ([["stream", "PTEST"], ["topic", "Test"]], 205, 537286, 537286),
            ([["stream", "PTEST"], ["topic", "Test"]], 205, 537289, 537289),
        ],
        ids=[
            "all-messages_to_topic_narrow_no_anchor",
            "topic_narrow_to_same_topic_narrow_with_anchor",
            "topic_narrow_to_same_topic_narrow_with_other_anchor",
        ],
    )
    def test_narrow_to_topic(
        self,
        mocker: MockerFixture,
        controller: Controller,
        index_multiple_topic_msg: Index,
        initial_narrow: List[Any],
        initial_stream_id: Optional[int],
        anchor: Optional[int],
        expected_final_focus: int,
        stream_name: str = "PTEST",
        topic_name: str = "Test",
        stream_id: int = 205,
    ) -> None:
        expected_narrow = [
            ["stream", stream_name],
            ["topic", topic_name],
        ]
        controller.model.narrow = initial_narrow
        controller.model.index = index_multiple_topic_msg
        controller.model.stream_id = initial_stream_id
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.stream_dict = {
            stream_id: {
                "color": "#ffffff",
                "name": stream_name,
            }
        }
        controller.model.muted_streams = set()
        mocker.patch(MODEL + ".is_muted_topic", return_value=False)

        controller.narrow_to_topic(
            stream_name=stream_name,
            topic_name=topic_name,
            contextual_message_id=anchor,
        )

        assert controller.model.stream_id == stream_id
        assert controller.model.narrow == expected_narrow
        controller.view.message_view.log.clear.assert_called_once_with()

        widgets, focus = controller.view.message_view.log.extend.call_args_list[0][0]
        id_list = index_multiple_topic_msg["topic_msg_ids"][stream_id][topic_name]
        msg_ids = {widget.original_widget.message["id"] for widget in widgets}
        final_focus_msg_id = widgets[focus].original_widget.message["id"]
        assert msg_ids == id_list
        assert final_focus_msg_id == expected_final_focus

    def test_narrow_to_user(
        self,
        mocker: MockerFixture,
        controller: Controller,
        index_user: Index,
        user_email: str = "boo@zulip.com",
        user_id: int = 5179,
    ) -> None:
        controller.model.narrow = []
        controller.model.index = index_user
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.user_id = 5140
        controller.model.user_email = "some@email"
        controller.model.user_dict = {user_email: {"user_id": user_id}}

        emails = [user_email]

        controller.narrow_to_user(recipient_emails=emails)

        assert controller.model.narrow == [["pm-with", user_email]]
        controller.view.message_view.log.clear.assert_called_once_with()
        recipients = frozenset([controller.model.user_id, user_id])
        assert controller.model.recipients == recipients
        widget = controller.view.message_view.log.extend.call_args_list[0][0][0][0]
        id_list = index_user["private_msg_ids_by_user_ids"][recipients]
        assert {widget.original_widget.message["id"]} == id_list

    @pytest.mark.parametrize(
        "anchor, expected_final_focus_msg_id",
        [(None, 537288), (537286, 537286), (537288, 537288)],
    )
    def test_narrow_to_all_messages(
        self,
        mocker: MockerFixture,
        controller: Controller,
        index_all_messages: Index,
        anchor: Optional[int],
        expected_final_focus_msg_id: int,
    ) -> None:
        controller.model.narrow = [["stream", "PTEST"]]
        controller.model.index = index_all_messages
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.user_email = "some@email"
        controller.model.user_id = 1
        controller.model.stream_dict = {
            205: {
                "color": "#ffffff",
            }
        }
        controller.model.muted_streams = set()
        mocker.patch(MODEL + ".is_muted_topic", return_value=False)

        controller.narrow_to_all_messages(contextual_message_id=anchor)

        assert controller.model.narrow == []
        controller.view.message_view.log.clear.assert_called_once_with()

        widgets, focus = controller.view.message_view.log.extend.call_args_list[0][0]
        id_list = index_all_messages["all_msg_ids"]
        msg_ids = {widget.original_widget.message["id"] for widget in widgets}
        final_focus_msg_id = widgets[focus].original_widget.message["id"]
        assert msg_ids == id_list
        assert final_focus_msg_id == expected_final_focus_msg_id

    def test_narrow_to_all_pm(
        self, mocker: MockerFixture, controller: Controller, index_user: Index
    ) -> None:
        controller.model.narrow = []
        controller.model.index = index_user
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.user_id = 1
        controller.model.user_email = "some@email"

        controller.narrow_to_all_pm()  # FIXME: Add id narrowing test

        assert controller.model.narrow == [["is", "private"]]
        controller.view.message_view.log.clear.assert_called_once_with()

        widgets = controller.view.message_view.log.extend.call_args_list[0][0][0]
        id_list = index_user["private_msg_ids"]
        msg_ids = {widget.original_widget.message["id"] for widget in widgets}
        assert msg_ids == id_list

    def test_narrow_to_all_starred(
        self, mocker: MockerFixture, controller: Controller, index_all_starred: Index
    ) -> None:
        controller.model.narrow = []
        controller.model.index = index_all_starred
        controller.model.muted_streams = set()  # FIXME Expand upon this
        controller.model.user_id = 1
        # FIXME: Expand upon is_muted_topic().
        mocker.patch(MODEL + ".is_muted_topic", return_value=False)
        controller.model.user_email = "some@email"
        controller.model.stream_dict = {
            205: {
                "color": "#ffffff",
            }
        }
        controller.view.message_view = mocker.patch("urwid.ListBox")

        controller.narrow_to_all_starred()  # FIXME: Add id narrowing test

        assert controller.model.narrow == [["is", "starred"]]
        controller.view.message_view.log.clear.assert_called_once_with()

        id_list = index_all_starred["starred_msg_ids"]
        widgets = controller.view.message_view.log.extend.call_args_list[0][0][0]
        msg_ids = {widget.original_widget.message["id"] for widget in widgets}
        assert msg_ids == id_list

    def test_narrow_to_all_mentions(
        self, mocker: MockerFixture, controller: Controller, index_all_mentions: Index
    ) -> None:
        controller.model.narrow = []
        controller.model.index = index_all_mentions
        controller.model.muted_streams = set()  # FIXME Expand upon this
        # FIXME: Expand upon is_muted_topic().
        mocker.patch(MODEL + ".is_muted_topic", return_value=False)
        controller.model.user_email = "some@email"
        controller.model.user_id = 1
        controller.model.stream_dict = {
            205: {
                "color": "#ffffff",
            }
        }
        controller.view.message_view = mocker.patch("urwid.ListBox")

        controller.narrow_to_all_mentions()  # FIXME: Add id narrowing test

        assert controller.model.narrow == [["is", "mentioned"]]
        controller.view.message_view.log.clear.assert_called_once_with()

        id_list = index_all_mentions["mentioned_msg_ids"]
        widgets = controller.view.message_view.log.extend.call_args_list[0][0][0]
        msg_ids = {widget.original_widget.message["id"] for widget in widgets}
        assert msg_ids == id_list

    @pytest.mark.parametrize(
        "text_to_copy, pasted_text, expected_result",
        [
            ("copy this", "copy this", "success"),
            ("copy that", "other text", "failure"),
        ],
    )
    def test_copy_to_clipboard_no_exception(
        self,
        text_to_copy: str,
        pasted_text: str,
        expected_result: str,
        mocker: MockerFixture,
        controller: Controller,
        text_category: str = "Test",
    ) -> None:
        mocker.patch(MODULE + ".pyperclip.copy", return_value=None)
        mocker.patch(MODULE + ".pyperclip.paste", return_value=pasted_text)
        mock_success = mocker.patch(MODULE + ".Controller.report_success")
        mock_warning = mocker.patch(MODULE + ".Controller.report_warning")

        controller.copy_to_clipboard(text_to_copy, text_category)

        if expected_result == "success":
            mock_success.assert_called_once_with(
                [f"{text_category} copied successfully"]
            )
            mock_warning.assert_not_called()
        else:
            mock_success.assert_not_called()
            mock_warning.assert_called_once_with(
                [f"{text_category} copied, but the clipboard text does not match"]
            )

    def test_copy_to_clipboard_exception(
        self, mocker: MockerFixture, controller: Controller, text_category: str = "Test"
    ) -> None:
        popup = mocker.patch(MODULE + ".Controller.show_pop_up")
        mocker.patch(
            MODULE + ".pyperclip.copy", side_effect=pyperclip.PyperclipException()
        )
        mocker.patch(
            MODULE + ".Controller.maximum_popup_dimensions", return_value=(64, 64)
        )

        controller.copy_to_clipboard("copy text", text_category)

        popup.assert_called_once()
        assert popup.call_args_list[0][0][1] == "area:error"

    @pytest.mark.parametrize(
        "url",
        [
            "https://chat.zulip.org/#narrow/stream/test",
            "https://chat.zulip.org/user_uploads/sent/abcd/efg.png",
            "https://github.com/",
        ],
    )
    def test_open_in_browser_success(
        self, mocker: MockerFixture, controller: Controller, url: str
    ) -> None:
        # Set DISPLAY environ to be able to run test in CI
        os.environ["DISPLAY"] = ":0"
        mocked_report_success = mocker.patch(MODULE + ".Controller.report_success")
        mock_get = mocker.patch(MODULE + ".webbrowser.get")
        mock_open = mock_get.return_value.open

        controller.open_in_browser(url)

        mock_open.assert_called_once_with(url)
        mocked_report_success.assert_called_once_with(
            [f"The link was successfully opened using {mock_get.return_value.name}"]
        )

    def test_open_in_browser_fail__no_browser_controller(
        self, mocker: MockerFixture, controller: Controller
    ) -> None:
        os.environ["DISPLAY"] = ":0"
        error = "No runnable browser found"
        mocked_report_error = mocker.patch(MODULE + ".Controller.report_error")
        mocker.patch(MODULE + ".webbrowser.get").side_effect = webbrowser.Error(error)

        controller.open_in_browser("https://chat.zulip.org/#narrow/stream/test")

        mocked_report_error.assert_called_once_with([f"ERROR: {error}"])

    def test_main(self, mocker: MockerFixture, controller: Controller) -> None:
        controller.view.palette = {"default": "theme_properties"}
        mocker.patch(MODULE + ".Screen.tty_signal_keys")
        controller.loop.screen.tty_signal_keys = mocker.Mock(return_value={})

        controller.main()

        assert controller.loop.run.call_count == 1

    @pytest.mark.parametrize(
        "muted_streams, action", [({205, 89}, "unmuting"), ({89}, "muting")]
    )
    def test_stream_muting_confirmation_popup(
        self,
        mocker: MockerFixture,
        controller: Controller,
        muted_streams: Set[int],
        action: str,
        stream_id: int = 205,
        stream_name: str = "PTEST",
    ) -> None:
        pop_up = mocker.patch(MODULE + ".PopUpConfirmationView")
        text = mocker.patch(MODULE + ".urwid.Text")
        partial = mocker.patch(MODULE + ".partial")
        controller.model.muted_streams = muted_streams
        controller.loop = mocker.Mock()

        controller.stream_muting_confirmation_popup(stream_id, stream_name)

        text.assert_called_with(
            ("bold", f"Confirm {action} of stream '{stream_name}' ?"),
            "center",
        )
        pop_up.assert_called_once_with(controller, text(), partial())

    @pytest.mark.parametrize(
        "initial_narrow, final_narrow",
        [
            ([], [["search", "FOO"]]),
            ([["search", "BOO"]], [["search", "FOO"]]),
            ([["stream", "PTEST"]], [["stream", "PTEST"], ["search", "FOO"]]),
            (
                [["pm-with", "foo@zulip.com"], ["search", "BOO"]],
                [["pm-with", "foo@zulip.com"], ["search", "FOO"]],
            ),
            (
                [["stream", "PTEST"], ["topic", "RDS"]],
                [["stream", "PTEST"], ["topic", "RDS"], ["search", "FOO"]],
            ),
        ],
        ids=[
            "Default_all_msg_search",
            "redo_default_search",
            "search_within_stream",
            "pm_search_again",
            "search_within_topic_narrow",
        ],
    )
    @pytest.mark.parametrize("msg_ids", [({200, 300, 400}), (set()), ({100})])
    def test_search_message(
        self,
        initial_narrow: List[Any],
        final_narrow: List[Any],
        controller: Controller,
        mocker: MockerFixture,
        msg_ids: Set[int],
        index_search_messages: Index,
    ) -> None:
        get_message = mocker.patch(MODEL + ".get_messages")
        create_msg = mocker.patch(MODULE + ".create_msg_box_list")
        mocker.patch(MODEL + ".get_message_ids_in_current_narrow", return_value=msg_ids)
        controller.model.index = index_search_messages  # Any initial search index
        controller.view.message_view = mocker.patch("urwid.ListBox")
        controller.model.narrow = initial_narrow

        def set_msg_ids(*args: Any, **kwargs: Any) -> None:
            controller.model.index["search"].update(msg_ids)

        get_message.side_effect = set_msg_ids
        assert controller.model.index["search"] == {500}

        controller.search_messages("FOO")

        assert controller.model.narrow == final_narrow
        get_message.assert_called_once_with(
            num_after=0, num_before=30, anchor=10000000000
        )
        create_msg.assert_called_once_with(controller.model, msg_ids)
        assert controller.model.index == dict(index_search_messages, search=msg_ids)

    @pytest.mark.parametrize(
        "screen_size, expected_popup_size",
        [
            ((150, 90), (3 * 150 // 4, 3 * 90 // 4)),
            ((90, 75), (7 * 90 // 8, 3 * 75 // 4)),
            ((70, 60), (70, 3 * 60 // 4)),
        ],
        ids=[
            "above_linear_range",
            "in_linear_range",
            "below_linear_range",
        ],
    )
    def test_maximum_popup_dimensions(
        self,
        mocker: MockerFixture,
        controller: Controller,
        screen_size: Tuple[int, int],
        expected_popup_size: Tuple[int, int],
    ) -> None:
        controller.loop.screen.get_cols_rows = mocker.Mock(return_value=screen_size)

        popup_size = controller.maximum_popup_dimensions()

        assert popup_size == expected_popup_size

    @pytest.mark.parametrize(
        "active_conversation_info",
        [
            case({"sender_name": "hamlet"}, id="in_pm_narrow_with_sender_typing:start"),
            case({}, id="in_pm_narrow_with_sender_typing:stop"),
        ],
    )
    def test_show_typing_notification(
        self,
        mocker: MockerFixture,
        controller: Controller,
        active_conversation_info: Dict[str, str],
    ) -> None:
        set_footer_text = mocker.patch(VIEW + ".set_footer_text")
        mocker.patch(MODULE + ".time.sleep")
        controller.active_conversation_info = active_conversation_info

        def mock_typing() -> None:
            controller.active_conversation_info = {}

        Timer(0.1, mock_typing).start()
        Thread(controller.show_typing_notification()).start()

        if active_conversation_info:
            set_footer_text.assert_has_calls(
                [
                    mocker.call([("footer_contrast", " hamlet "), " is typing"]),
                    mocker.call([("footer_contrast", " hamlet "), " is typing."]),
                    mocker.call([("footer_contrast", " hamlet "), " is typing.."]),
                    mocker.call([("footer_contrast", " hamlet "), " is typing..."]),
                ]
            )
            set_footer_text.assert_called_with()
        else:
            set_footer_text.assert_called_once_with()
        assert controller.is_typing_notification_in_progress is False
        assert controller.active_conversation_info == {}
