from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest
from pytest import param as case
from pytest_mock import MockerFixture
from urwid import AttrMap, Overlay, Widget

from zulipterminal.api_types import Message
from zulipterminal.config.keys import keys_for_command
from zulipterminal.config.symbols import CHECK_MARK
from zulipterminal.ui_tools.buttons import (
    DecodedStream,
    EmojiButton,
    MessageLinkButton,
    ParsedNarrowLink,
    StarredButton,
    StreamButton,
    TopButton,
    TopicButton,
    UserButton,
)
from zulipterminal.urwid_types import urwid_Size


MODULE = "zulipterminal.ui_tools.buttons"
MSGLINKBUTTON = MODULE + ".MessageLinkButton"


SERVER_URL = "https://chat.zulip.zulip"


class TestTopButton:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        self.show_function = mocker.Mock()
        self.urwid = mocker.patch(MODULE + ".urwid")

    @pytest.fixture
    def top_button(self, mocker: MockerFixture) -> TopButton:
        top_button = TopButton(
            controller=self.controller,
            caption="caption",
            show_function=self.show_function,
            prefix_character="-",
            count=0,
        )
        return top_button

    def test_init(self, mocker: MockerFixture, top_button: TopButton) -> None:

        assert top_button.controller == self.controller
        assert top_button._caption == "caption"
        assert top_button.show_function == self.show_function
        assert top_button.prefix_character == "-"
        assert top_button.original_color is None
        assert top_button.count == 0
        assert top_button.count_style is None

        assert top_button._label.wrap == "ellipsis"
        assert top_button._label.get_cursor_coords("size") is None

        self.urwid.Columns.assert_called_once_with(
            [
                ("pack", top_button.button_prefix),
                top_button._label,
                ("pack", top_button.button_suffix),
            ]
        )
        self.urwid.AttrMap.assert_called_once_with(
            self.urwid.Columns(), None, "selected"
        )
        self.urwid.connect_signal.assert_called_once_with(
            top_button, "click", top_button.activate
        )

    @pytest.mark.parametrize("text_color", ["color", None])
    @pytest.mark.parametrize(
        "old_count, new_count, new_count_str",
        [(10, 11, "11"), (0, 1, "1"), (11, 10, "10"), (1, 0, "")],
    )
    def test_update_count(
        self,
        mocker: MockerFixture,
        top_button: TopButton,
        old_count: int,
        new_count: int,
        new_count_str: str,
        text_color: Optional[str],
    ) -> None:
        top_button.count = old_count
        top_button_update_widget = mocker.patch(MODULE + ".TopButton.update_widget")

        top_button.update_count(new_count, text_color)

        top_button_update_widget.assert_called_once_with(
            (top_button.count_style, new_count_str),
            text_color,
        )

    @pytest.mark.parametrize(
        "prefix, expected_prefix", [("-", [" ", "-", " "]), ("", [" "])]
    )
    @pytest.mark.parametrize("text_color", ["color", None])
    @pytest.mark.parametrize(
        "count_text, expected_suffix",
        [
            (("color", "3"), [" ", ("color", "3"), " "]),
            (("color", ""), ["  "]),
            ((None, "3"), [" ", (None, "3"), " "]),
            ((None, ""), ["  "]),
        ],
    )
    def test_update_widget(
        self,
        mocker: MockerFixture,
        top_button: TopButton,
        prefix: str,
        expected_prefix: List[str],
        text_color: Optional[str],
        count_text: Tuple[Optional[str], str],
        expected_suffix: List[Any],
    ) -> None:
        top_button.prefix_character = prefix
        top_button.button_prefix = mocker.patch(MODULE + ".urwid.Text")
        top_button.set_label = mocker.patch(MODULE + ".urwid.Button.set_label")
        top_button.button_suffix = mocker.patch(MODULE + ".urwid.Text")
        set_attr_map = mocker.patch.object(top_button._w, "set_attr_map")

        top_button.update_widget(count_text, text_color)

        top_button.button_prefix.set_text.assert_called_once_with(expected_prefix)
        top_button.set_label.assert_called_once_with(top_button._caption)
        top_button.button_suffix.set_text.assert_called_once_with(expected_suffix)
        set_attr_map.assert_called_once_with({None: text_color})


class TestStarredButton:
    def test_count_style_init_argument_value(
        self, mocker: MockerFixture, count: int = 10
    ) -> None:
        starred_button = StarredButton(controller=mocker.Mock(), count=count)
        assert starred_button.count_style == "starred_count"


class TestStreamButton:
    @pytest.mark.parametrize("key", keys_for_command("TOGGLE_TOPIC"))
    def test_keypress_ENTER_TOGGLE_TOPIC(
        self,
        mocker: MockerFixture,
        stream_button: StreamButton,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(stream_button)
        stream_button.view.left_panel = mocker.Mock()
        stream_button.keypress(size, key)

        stream_button.view.left_panel.show_topic_view.assert_called_once_with(
            stream_button
        )

    @pytest.mark.parametrize("key", keys_for_command("TOGGLE_MUTE_STREAM"))
    def test_keypress_TOGGLE_MUTE_STREAM(
        self,
        mocker: MockerFixture,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
        stream_button: StreamButton,
        stream_id: int = 205,
        stream_name: str = "PTEST",
    ) -> None:
        size = widget_size(stream_button)
        pop_up = mocker.patch(
            "zulipterminal.core.Controller.stream_muting_confirmation_popup"
        )
        stream_button.keypress(size, key)
        pop_up.assert_called_once_with(stream_id, stream_name)


class TestUserButton:
    # FIXME Place this in a general test of a derived class?
    @pytest.mark.parametrize("enter_key", keys_for_command("ENTER"))
    def test_activate_called_once_on_keypress(
        self,
        mocker: MockerFixture,
        enter_key: str,
        widget_size: Callable[[Widget], urwid_Size],
        caption: str = "some user",
        email: str = "some_email",
        user_id: int = 5,
    ) -> None:
        user: Dict[str, Any] = {
            "email": email,
            "user_id": user_id,
            "full_name": caption,
        }
        activate = mocker.patch(MODULE + ".UserButton.activate")
        user_button = UserButton(
            user=user,
            controller=mocker.Mock(),
            view=mocker.Mock(),
            color=mocker.Mock(),
            state_marker="*",
            count=mocker.Mock(),
        )
        size = widget_size(user_button)

        user_button.keypress(size, enter_key)

        assert activate.call_count == 1

    @pytest.mark.parametrize("key", keys_for_command("USER_INFO"))
    def test_keypress_USER_INFO(
        self,
        mocker: MockerFixture,
        user_button: UserButton,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(user_button)
        pop_up = mocker.patch("zulipterminal.core.Controller.show_user_info")

        user_button.keypress(size, key)

        pop_up.assert_called_once_with(user_button.user_id)


class TestEmojiButton:
    @pytest.mark.parametrize(
        "emoji_unit, to_vary_in_message, count",
        [
            case(
                ("working_on_it", "1f6e0", ["hammer_and_wrench", "tools"]),
                {"reactions": [{"emoji_name": "thumbs_up", "user": [{"id": 232}]}]},
                0,
                id="emoji_button_with_no_reaction",
            ),
            case(
                ("+1", "1f44d", ["thumbs_up", "like"]),
                {"reactions": [{"emoji_name": "+1", "user": [{"id": 10}]}]},
                1,
                id="emoji_button_with_a_reaction",
            ),
        ],
    )
    def test_init_calls_top_button(
        self,
        mocker: MockerFixture,
        emoji_unit: Tuple[str, str, List[str]],
        to_vary_in_message: Dict[str, Any],
        message_fixture: Message,
        count: int,
    ) -> None:
        controller = mocker.Mock()
        controller.model.has_user_reacted_to_message = mocker.Mock(return_value=False)
        update_widget = mocker.patch(MODULE + ".EmojiButton.update_widget")
        top_button = mocker.patch(MODULE + ".TopButton.__init__")
        caption = ", ".join([emoji_unit[0], *emoji_unit[2]])
        message_fixture["reactions"] = to_vary_in_message["reactions"]

        emoji_button = EmojiButton(
            controller=controller,
            emoji_unit=emoji_unit,
            message=message_fixture,
            reaction_count=count,
            is_selected=lambda *_: False,
            toggle_selection=lambda *_: None,
        )

        top_button.assert_called_once_with(
            controller=controller,
            caption=caption,
            prefix_character="",
            show_function=emoji_button.update_emoji_button,
        )
        assert emoji_button.emoji_name == emoji_unit[0]
        assert emoji_button.reaction_count == count

    @pytest.mark.parametrize("key", keys_for_command("ENTER"))
    @pytest.mark.parametrize(
        "emoji, has_user_reacted, is_selected_final, expected_reaction_count",
        [
            case(("smile", "1f642", []), True, False, 2, id="reacted_unselected_emoji"),
            case(("smile", "1f642", []), True, True, 0, id="reacted_selected_emoji"),
            case(("+1", "1f44d", []), False, False, 0, id="unreacted_unselected_emoji"),
            case(("+1", "1f44d", []), False, True, 2, id="unreacted_selected_emoji"),
        ],
    )
    def test_keypress_emoji_button(
        self,
        mocker: MockerFixture,
        key: str,
        emoji: Tuple[str, str, List[str]],
        has_user_reacted: bool,
        is_selected_final: bool,
        widget_size: Callable[[Widget], urwid_Size],
        message_fixture: Message,
        expected_reaction_count: int,
    ) -> None:
        controller = mocker.Mock()
        controller.model.has_user_reacted_to_message = mocker.Mock(
            return_value=has_user_reacted
        )
        message_fixture.update(
            {
                "reactions": [
                    {"emoji_name": "smile", "user": [{"id": 10}]},
                    {"emoji_name": "+1", "user": [{"id": 52}]},
                ],
            }
        )
        emoji_button = EmojiButton(
            controller=controller,
            emoji_unit=emoji,
            message=message_fixture,
            reaction_count=1,
            is_selected=lambda *_: is_selected_final,
            toggle_selection=lambda *_: None,
        )
        size = widget_size(emoji_button)

        emoji_button.keypress(size, key)

        reaction_count = emoji_button.reaction_count
        reaction_count_text = "" if reaction_count == 0 else f"{reaction_count}"
        suffix_text = (
            f"{CHECK_MARK} " + reaction_count_text
            if has_user_reacted != is_selected_final
            else reaction_count_text
        )
        assert emoji_button.emoji_name == emoji[0]
        assert reaction_count == expected_reaction_count
        assert emoji_button.button_suffix.get_text()[0].strip() == suffix_text


class TestTopicButton:
    @pytest.mark.parametrize(
        "count, stream_id, title, stream_name, is_resolved",
        [
            (2, 86, "topic1", "Django", False),
            (1, 14, "✔ topic2", "GSoC", True),
            (1000, 205, "topic3", "PTEST", False),
        ],
    )
    def test_init_calls_top_button(
        self,
        mocker: MockerFixture,
        count: int,
        title: str,
        stream_id: int,
        stream_name: str,
        is_resolved: bool,
    ) -> None:
        controller = mocker.Mock()
        controller.model.stream_dict = {
            205: {"name": "PTEST"},
            86: {"name": "Django"},
            14: {"name": "GSoC"},
        }
        controller.model.is_muted_topic = mocker.Mock(return_value=False)
        view = mocker.Mock()
        top_button = mocker.patch(MODULE + ".TopButton.__init__")
        params = dict(controller=controller, count=count)

        topic_button = TopicButton(
            stream_id=stream_id, topic=title, view=view, **params
        )

        top_button.assert_called_once_with(
            caption=title if not is_resolved else title[2:],
            prefix_character=" " if not is_resolved else title[:1],
            show_function=mocker.ANY,  # partial
            count_style="unread_count",
            **params,
        )
        assert topic_button.stream_name == stream_name
        assert topic_button.stream_id == stream_id
        assert topic_button.topic_name == title

    @pytest.mark.parametrize(
        "stream_name, title, is_muted_topic_return_value, is_muted_called",
        [
            ("Django", "topic1", True, True),
            ("Django", "topic2", False, False),
            ("GSoC", "topic1", False, False),
        ],
        ids=[
            # Assuming 'Django', 'topic1' is muted via muted_topics.
            "stream_and_topic_match",
            "topic_mismatch",
            "stream_mismatch",
        ],
    )
    def test_init_calls_mark_muted(
        self,
        mocker: MockerFixture,
        stream_name: str,
        title: str,
        is_muted_topic_return_value: bool,
        is_muted_called: bool,
    ) -> None:
        mark_muted = mocker.patch(MODULE + ".TopicButton.mark_muted")
        controller = mocker.Mock()
        controller.model.is_muted_topic = mocker.Mock(
            return_value=is_muted_topic_return_value
        )
        controller.model.stream_dict = {205: {"name": stream_name}}
        view = mocker.Mock()
        topic_button = TopicButton(
            stream_id=205,
            topic=title,
            controller=controller,
            view=view,
            count=0,
        )
        if is_muted_called:
            mark_muted.assert_called_once_with()
        else:
            mark_muted.assert_not_called()

    @pytest.mark.parametrize("key", keys_for_command("TOGGLE_TOPIC"))
    def test_keypress_EXIT_TOGGLE_TOPIC(
        self,
        mocker: MockerFixture,
        topic_button: TopicButton,
        key: str,
        widget_size: Callable[[Widget], urwid_Size],
    ) -> None:
        size = widget_size(topic_button)
        topic_button.view.left_panel = mocker.Mock()
        topic_button.keypress(size, key)
        topic_button.view.left_panel.show_stream_view.assert_called_once_with()


class TestMessageLinkButton:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: MockerFixture) -> None:
        self.controller = mocker.Mock()
        self.super_init = mocker.patch(MODULE + ".urwid.Button.__init__")
        self.connect_signal = mocker.patch(MODULE + ".urwid.connect_signal")

    def message_link_button(
        self, caption: str = "", link: str = "", display_attr: Optional[str] = None
    ) -> MessageLinkButton:
        self.caption = caption
        self.link = link
        self.display_attr = display_attr
        return MessageLinkButton(
            controller=self.controller,
            caption=self.caption,
            link=self.link,
            display_attr=self.display_attr,
        )

    def test_init(self, mocker: MockerFixture) -> None:
        self.update_widget = mocker.patch(MSGLINKBUTTON + ".update_widget")

        mocked_button = self.message_link_button()

        assert mocked_button.controller == self.controller
        assert mocked_button.model == self.controller.model
        assert mocked_button.view == self.controller.view
        assert mocked_button.link == self.link
        self.super_init.assert_called_once_with("")
        self.update_widget.assert_called_once_with(self.caption, self.display_attr)
        assert self.connect_signal.called

    @pytest.mark.parametrize(
        "caption, expected_cursor_position",
        [
            ("Test", 5),
            ("Check", 6),
        ],
    )
    def test_update_widget(
        self,
        mocker: MockerFixture,
        caption: str,
        expected_cursor_position: int,
        display_attr: Optional[str] = None,
    ) -> None:
        self.selectable_icon = mocker.patch(MODULE + ".urwid.SelectableIcon")

        # The method update_widget() is called in MessageLinkButton's init.
        mocked_button = self.message_link_button(
            caption=caption, display_attr=display_attr
        )

        self.selectable_icon.assert_called_once_with(
            caption, cursor_position=expected_cursor_position
        )
        assert isinstance(mocked_button._w, AttrMap)

    @pytest.mark.parametrize(
        "link, handle_narrow_link_called",
        [
            (SERVER_URL + "/#narrow/stream/1-Stream-1", True),
            (SERVER_URL + "/user_uploads/some/path/image.png", False),
            ("https://foo.com", False),
        ],
        ids=[
            "internal_narrow_link",
            "internal_media_link",
            "external_link",
        ],
    )
    def test_handle_link(
        self, mocker: MockerFixture, link: str, handle_narrow_link_called: bool
    ) -> None:
        self.controller.model.server_url = SERVER_URL
        self.handle_narrow_link = mocker.patch(MSGLINKBUTTON + ".handle_narrow_link")
        mocked_button = self.message_link_button(link=link)

        mocked_button.handle_link()

        assert self.handle_narrow_link.called == handle_narrow_link_called

    @pytest.mark.parametrize(
        "stream_data, expected_response",
        [
            ("206-zulip-terminal", DecodedStream(stream_id=206, stream_name=None)),
            ("Stream.201", DecodedStream(stream_id=None, stream_name="Stream 1")),
        ],
        ids=[
            "stream_data_current_version",
            "stream_data_deprecated_version",
        ],
    )
    def test__decode_stream_data(
        self, stream_data: str, expected_response: DecodedStream
    ) -> None:
        return_value = MessageLinkButton._decode_stream_data(stream_data)

        assert return_value == expected_response

    @pytest.mark.parametrize(
        "message_id, expected_return_value",
        [
            ("1", 1),
            ("foo", None),
        ],
    )
    def test__decode_message_id(
        self, message_id: str, expected_return_value: Optional[int]
    ) -> None:
        return_value = MessageLinkButton._decode_message_id(message_id)

        assert return_value == expected_return_value

    @pytest.mark.parametrize(
        "link, expected_parsed_link",
        [
            (
                SERVER_URL + "/#narrow/stream/1-Stream-1",
                ParsedNarrowLink(
                    narrow="stream", stream=DecodedStream(stream_id=1, stream_name=None)
                ),
            ),
            (
                SERVER_URL + "/#narrow/stream/Stream.201",
                ParsedNarrowLink(
                    narrow="stream",
                    stream=DecodedStream(stream_id=None, stream_name="Stream 1"),
                ),
            ),
            (
                SERVER_URL + "/#narrow/stream/1-Stream-1/topic/foo.20bar",
                ParsedNarrowLink(
                    narrow="stream:topic",
                    topic_name="foo bar",
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
            ),
            (
                SERVER_URL + "/#narrow/stream/1-Stream-1/near/1",
                ParsedNarrowLink(
                    narrow="stream:near",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
            ),
            (
                SERVER_URL + "/#narrow/stream/1-Stream-1/topic/foo/near/1",
                ParsedNarrowLink(
                    narrow="stream:topic:near",
                    topic_name="foo",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
            ),
            (SERVER_URL + "/#narrow/foo", ParsedNarrowLink()),
            (SERVER_URL + "/#narrow/stream/", ParsedNarrowLink()),
            (SERVER_URL + "/#narrow/stream/1-Stream-1/topic/", ParsedNarrowLink()),
            (SERVER_URL + "/#narrow/stream/1-Stream-1//near/", ParsedNarrowLink()),
            (
                SERVER_URL + "/#narrow/stream/1-Stream-1/topic/foo/near/",
                ParsedNarrowLink(),
            ),
        ],
        ids=[
            "modern_stream_narrow_link",
            "deprecated_stream_narrow_link",
            "topic_narrow_link",
            "stream_near_narrow_link",
            "topic_near_narrow_link",
            "invalid_narrow_link_1",
            "invalid_narrow_link_2",
            "invalid_narrow_link_3",
            "invalid_narrow_link_4",
            "invalid_narrow_link_5",
        ],
    )
    def test__parse_narrow_link(
        self, link: str, expected_parsed_link: ParsedNarrowLink
    ) -> None:
        return_value = MessageLinkButton._parse_narrow_link(link)

        assert return_value == expected_parsed_link

    @pytest.mark.parametrize(
        [
            "parsed_link",
            "is_user_subscribed_to_stream",
            "is_valid_stream",
            "topics_in_stream",
            "expected_error",
        ],
        [
            case(
                ParsedNarrowLink(
                    narrow="stream", stream=DecodedStream(stream_id=1, stream_name=None)
                ),
                True,
                None,
                None,
                "",
                id="valid_modern_stream_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream",
                    stream=DecodedStream(stream_id=462, stream_name=None),
                ),
                False,
                None,
                None,
                "The stream seems to be either unknown or unsubscribed",
                id="invalid_modern_stream_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream",
                    stream=DecodedStream(stream_id=None, stream_name="Stream 1"),
                ),
                None,
                True,
                None,
                "",
                id="valid_deprecated_stream_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream",
                    stream=DecodedStream(stream_id=None, stream_name="foo"),
                ),
                None,
                False,
                None,
                "The stream seems to be either unknown or unsubscribed",
                id="invalid_deprecated_stream_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:topic",
                    topic_name="Valid",
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                ["Valid"],
                "",
                id="valid_topic_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:topic",
                    topic_name="Invalid",
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                [],
                "Invalid topic name",
                id="invalid_topic_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:near",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                None,
                "",
                id="valid_stream_near_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:near",
                    message_id=None,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                None,
                "Invalid message ID",
                id="invalid_stream_near_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:topic:near",
                    topic_name="Valid",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                ["Valid"],
                "",
                id="valid_topic_near_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(
                    narrow="stream:topic:near",
                    topic_name="Valid",
                    message_id=None,
                    stream=DecodedStream(stream_id=1, stream_name=None),
                ),
                True,
                None,
                ["Valid"],
                "Invalid message ID",
                id="invalid_topic_near_narrow_parsed_link",
            ),
            case(
                ParsedNarrowLink(),
                None,
                None,
                None,
                "The narrow link seems to be either broken or unsupported",
                id="invalid_narrow_link",
            ),
        ],
    )
    def test__validate_narrow_link(
        self,
        stream_dict: Dict[int, Any],
        parsed_link: ParsedNarrowLink,
        is_user_subscribed_to_stream: Optional[bool],
        is_valid_stream: Optional[bool],
        topics_in_stream: Optional[List[str]],
        expected_error: str,
    ) -> None:
        self.controller.model.stream_dict = stream_dict
        self.controller.model.is_user_subscribed_to_stream.return_value = (
            is_user_subscribed_to_stream
        )
        self.controller.model.is_valid_stream.return_value = is_valid_stream
        self.controller.model.topics_in_stream.return_value = topics_in_stream
        mocked_button = self.message_link_button()

        return_value = mocked_button._validate_narrow_link(parsed_link)

        assert return_value == expected_error

    @pytest.mark.parametrize(
        [
            "parsed_link",
            "is_user_subscribed_to_stream",
            "is_valid_stream",
            "stream_id_from_name_return_value",
            "expected_parsed_link",
            "expected_error",
        ],
        [
            (
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=1, stream_name=None)
                ),  # ...
                True,
                None,
                None,
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1")
                ),
                "",
            ),
            (
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=462, stream_name=None)
                ),  # ...
                False,
                None,
                None,
                ParsedNarrowLink(stream=DecodedStream(stream_id=462, stream_name=None)),
                "The stream seems to be either unknown or unsubscribed",
            ),
            (
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=None, stream_name="Stream 1")
                ),  # ...
                None,
                True,
                1,
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1")
                ),
                "",
            ),
            (
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=None, stream_name="foo")
                ),  # ...
                None,
                False,
                None,
                ParsedNarrowLink(
                    stream=DecodedStream(stream_id=None, stream_name="foo")
                ),
                "The stream seems to be either unknown or unsubscribed",
            ),
        ],
        ids=[
            "valid_stream_data_with_stream_id",
            "invalid_stream_data_with_stream_id",
            "valid_stream_data_with_stream_name",
            "invalid_stream_data_with_stream_name",
        ],
    )
    def test__validate_and_patch_stream_data(
        self,
        stream_dict: Dict[int, Any],
        parsed_link: ParsedNarrowLink,
        is_user_subscribed_to_stream: Optional[bool],
        is_valid_stream: Optional[bool],
        stream_id_from_name_return_value: Optional[int],
        expected_parsed_link: ParsedNarrowLink,
        expected_error: str,
    ) -> None:
        self.controller.model.stream_dict = stream_dict
        self.controller.model.stream_id_from_name.return_value = (
            stream_id_from_name_return_value
        )
        self.controller.model.is_user_subscribed_to_stream.return_value = (
            is_user_subscribed_to_stream
        )
        self.controller.model.is_valid_stream.return_value = is_valid_stream
        mocked_button = self.message_link_button()

        error = mocked_button._validate_and_patch_stream_data(parsed_link)

        assert parsed_link == expected_parsed_link
        assert error == expected_error

    @pytest.mark.parametrize(
        "parsed_link, narrow_to_stream_called, narrow_to_topic_called",
        [
            (
                ParsedNarrowLink(
                    narrow="stream",
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1"),
                ),
                True,
                False,
            ),
            (
                ParsedNarrowLink(
                    narrow="stream:topic",
                    topic_name="Foo",
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1"),
                ),
                False,
                True,
            ),
            (
                ParsedNarrowLink(
                    narrow="stream:near",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1"),
                ),
                True,
                False,
            ),
            (
                ParsedNarrowLink(
                    narrow="stream:topic:near",
                    topic_name="Foo",
                    message_id=1,
                    stream=DecodedStream(stream_id=1, stream_name="Stream 1"),
                ),
                False,
                True,
            ),
        ],
        ids=[
            "stream_narrow",
            "topic_narrow",
            "stream_near_narrow",
            "topic_near_narrow",
        ],
    )
    def test__switch_narrow_to(
        self,
        parsed_link: ParsedNarrowLink,
        narrow_to_stream_called: bool,
        narrow_to_topic_called: bool,
    ) -> None:
        mocked_button = self.message_link_button()

        mocked_button._switch_narrow_to(parsed_link)

        assert (
            mocked_button.controller.narrow_to_stream.called == narrow_to_stream_called
        )
        assert mocked_button.controller.narrow_to_topic.called == narrow_to_topic_called

    @pytest.mark.parametrize(
        "error, report_error_called, _switch_narrow_to_called, exit_popup_called",
        [
            ("Some Validation Error", True, False, False),
            ("", False, True, True),
        ],
        ids=[
            "successful_narrow",
            "unsuccessful_narrow",
        ],
    )
    def test_handle_narrow_link(
        self,
        mocker: MockerFixture,
        error: str,
        report_error_called: bool,
        _switch_narrow_to_called: bool,
        exit_popup_called: bool,
    ) -> None:
        self.controller.loop.widget = mocker.Mock(spec=Overlay)
        mocked__parse_narrow_link = mocker.patch(MSGLINKBUTTON + "._parse_narrow_link")
        mocked__validate_narrow_link = mocker.patch(
            MSGLINKBUTTON + "._validate_narrow_link", return_value=error
        )
        mocked__switch_narrow_to = mocker.patch(MSGLINKBUTTON + "._switch_narrow_to")
        mocked_button = self.message_link_button()

        mocked_button.handle_narrow_link()

        assert mocked__parse_narrow_link.called
        assert mocked__validate_narrow_link.called
        assert mocked_button.controller.report_error.called == report_error_called
        assert mocked__switch_narrow_to.called == _switch_narrow_to_called
        assert mocked_button.controller.exit_popup.called == exit_popup_called
