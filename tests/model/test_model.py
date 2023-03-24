import json
from collections import OrderedDict
from copy import deepcopy
from typing import Any, List, Optional, Tuple

import pytest
from pytest import param as case
from zulip import Client, ZulipError

from zulipterminal.config.symbols import STREAM_TOPIC_SEPARATOR
from zulipterminal.helper import initial_index, powerset
from zulipterminal.model import (
    MAX_MESSAGE_LENGTH,
    MAX_STREAM_NAME_LENGTH,
    MAX_TOPIC_NAME_LENGTH,
    Model,
    ServerConnectionFailure,
    UserSettings,
)


MODULE = "zulipterminal.model"
MODEL = MODULE + ".Model"
CONTROLLER = "zulipterminal.core.Controller"


class TestModel:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: Any) -> None:
        self.urlparse = mocker.patch("urllib.parse.urlparse")
        self.controller = mocker.patch(CONTROLLER, return_value=None)
        self.client = mocker.patch(CONTROLLER + ".client", spec=Client)
        self.client.base_url = "chat.zulip.zulip"
        mocker.patch(MODEL + "._start_presence_updates")
        self.display_error_if_present = mocker.patch(
            MODULE + ".display_error_if_present"
        )
        self.notify_if_message_sent_outside_narrow = mocker.patch(
            MODULE + ".notify_if_message_sent_outside_narrow"
        )

    @pytest.fixture
    def model(self, mocker, initial_data, user_profile, unicode_emojis):
        mocker.patch(MODEL + ".get_messages", return_value="")
        self.client.register.return_value = initial_data
        mocker.patch(MODEL + ".get_all_users", return_value=[])
        # NOTE: PATCH WHERE USED NOT WHERE DEFINED
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )
        self.client.get_profile.return_value = user_profile
        mocker.patch(MODULE + ".unicode_emojis", EMOJI_DATA=unicode_emojis)
        model = Model(self.controller)
        return model

    def test_init(
        self,
        model,
        initial_data,
        user_profile,
        unicode_emojis,
        realm_emojis_data,
        zulip_emoji,
        stream_dict,
    ):
        assert hasattr(model, "controller")
        assert hasattr(model, "client")
        assert model.narrow == []
        assert model._have_last_message == {}
        assert model.stream_id is None
        assert model.stream_dict == stream_dict
        assert model.recipients == frozenset()
        assert model.index == initial_index
        assert model._last_unread_topic is None
        model.get_messages.assert_called_once_with(
            num_before=30, num_after=10, anchor=None
        )
        assert model.initial_data == initial_data
        assert model.server_version == initial_data["zulip_version"]
        assert model.server_feature_level == initial_data.get("zulip_feature_level")
        assert model.user_id == user_profile["user_id"]
        assert model.user_full_name == user_profile["full_name"]
        assert model.user_email == user_profile["email"]
        assert model.server_name == initial_data["realm_name"]
        # FIXME Add test here for model.server_url
        model.get_all_users.assert_called_once_with()
        assert model.users == []
        self.classify_unread_counts.assert_called_once_with(model)
        assert model.unread_counts == []
        assert model.active_emoji_data == OrderedDict(
            sorted(
                {**unicode_emojis, **realm_emojis_data, **zulip_emoji}.items(),
                key=lambda e: e[0],
            )
        )
        assert model.all_emoji_names == sorted(
            [
                name
                for emoji in {
                    **unicode_emojis,
                    **realm_emojis_data,
                    **zulip_emoji,
                }.items()
                for name in [emoji[0], *emoji[1]["aliases"]]
            ]
        )
        # Deactivated emoji is removed from active emojis set
        assert "green_tick" not in model.active_emoji_data
        # Custom emoji replaces unicode emoji with same name.
        assert model.active_emoji_data["joker"]["type"] == "realm_emoji"
        # zulip_extra_emoji replaces all other emoji types for 'zulip' emoji.
        assert model.active_emoji_data["zulip"]["type"] == "zulip_extra_emoji"

    @pytest.mark.parametrize(
        "sptn, expected_sptn_value",
        [(None, True), (True, True), (False, False)],
    )
    def test_init_user_settings(self, mocker, initial_data, sptn, expected_sptn_value):
        assert "user_settings" not in initial_data  # we add it in tests

        if sptn is not None:
            initial_data["user_settings"] = {"send_private_typing_notifications": sptn}

        mocker.patch(MODEL + ".get_messages", return_value="")
        self.client.register = mocker.Mock(return_value=initial_data)

        model = Model(self.controller)

        assert model.user_settings() == UserSettings(
            send_private_typing_notifications=expected_sptn_value,
            twenty_four_hour_time=initial_data["twenty_four_hour_time"],
            pm_content_in_desktop_notifications=initial_data[
                "pm_content_in_desktop_notifications"
            ],
        )

    def test_user_settings_expected_contents(self, model):
        expected_keys = {
            "send_private_typing_notifications",
            "twenty_four_hour_time",
            "pm_content_in_desktop_notifications",
        }
        settings = model.user_settings()
        assert set(settings) == expected_keys

        # Ensure original settings are unchanged through accessor
        settings["foo"] = "bar"
        assert set(model._user_settings) == expected_keys

    @pytest.mark.parametrize(
        "server_response, locally_processed_data, zulip_feature_level",
        [
            (
                [["Stream 1", "muted stream muted topic"]],
                {("Stream 1", "muted stream muted topic"): None},
                None,
            ),
            (
                [["Stream 2", "muted topic", 1530129122]],
                {("Stream 2", "muted topic"): 1530129122},
                1,
            ),
        ],
        ids=[
            "zulip_feature_level:None",
            "zulip_feature_level:1",
        ],
    )
    def test_init_muted_topics(
        self,
        mocker,
        initial_data,
        server_response,
        locally_processed_data,
        zulip_feature_level,
    ):
        mocker.patch(MODEL + ".get_messages", return_value="")
        initial_data["zulip_feature_level"] = zulip_feature_level
        initial_data["muted_topics"] = server_response
        self.client.register = mocker.Mock(return_value=initial_data)

        model = Model(self.controller)

        assert model._muted_topics == locally_processed_data

    def test_init_InvalidAPIKey_response(self, mocker, initial_data):
        # Both network calls indicate the same response
        mocker.patch(MODEL + ".get_messages", return_value="Invalid API key")
        mocker.patch(
            MODEL + "._register_desired_events", return_value="Invalid API key"
        )

        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        with pytest.raises(ServerConnectionFailure) as e:
            Model(self.controller)

        assert str(e.value) == "Invalid API key (get_messages, register)"

    def test_init_ZulipError_exception(self, mocker, initial_data, exception_text="X"):
        # Both network calls fail, resulting in exceptions
        mocker.patch(MODEL + ".get_messages", side_effect=ZulipError(exception_text))
        mocker.patch(
            MODEL + "._register_desired_events", side_effect=ZulipError(exception_text)
        )

        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        with pytest.raises(ServerConnectionFailure) as e:
            Model(self.controller)

        assert str(e.value) == exception_text + " (get_messages, register)"

    def test_register_initial_desired_events(self, mocker, initial_data):
        mocker.patch(MODEL + ".get_messages", return_value="")
        mocker.patch(MODEL + ".get_all_users")
        self.client.register.return_value = initial_data

        model = Model(self.controller)

        event_types = [
            "message",
            "update_message",
            "reaction",
            "subscription",
            "typing",
            "update_message_flags",
            "update_global_notifications",
            "update_display_settings",
            "user_settings",
            "realm_emoji",
            "realm_user",
        ]
        fetch_event_types = [
            "realm",
            "presence",
            "subscription",
            "message",
            "starred_messages",
            "update_message_flags",
            "muted_topics",
            "realm_user",
            "realm_user_groups",
            "update_global_notifications",
            "update_display_settings",
            "user_settings",
            "realm_emoji",
            "zulip_version",
        ]
        model.client.register.assert_called_once_with(
            event_types=event_types,
            fetch_event_types=fetch_event_types,
            apply_markdown=True,
            client_gravatar=True,
            include_subscribers=True,
        )

    @pytest.mark.parametrize(
        [
            "to_vary_in_stream_dict",
            "realm_msg_retention_days",
            "feature_level",
            "expect_msg_retention_text",
        ],
        [
            case(
                {1: {}},
                None,
                10,
                {1: "Indefinite [Organization default]"},
                id="ZFL=None_no_stream_retention_realm_retention=None",
            ),
            case(
                {1: {}, 2: {}},
                -1,
                16,
                {
                    1: "Indefinite [Organization default]",
                    2: "Indefinite [Organization default]",
                },
                id="ZFL=16_no_stream_retention_realm_retention=-1",
            ),
            case(
                {2: {"message_retention_days": 30}},
                60,
                17,
                {2: "30"},
                id="ZFL=17_stream_retention_days=30",
            ),
            case(
                {
                    1: {"message_retention_days": None},
                    2: {"message_retention_days": -1},
                },
                72,
                18,
                {1: "72 [Organization default]", 2: "Indefinite"},
                id="ZFL=18_stream_retention_days=[None, -1]",
            ),
        ],
    )
    def test_normalize_and_cache_message_retention_text(
        self,
        model,
        stream_dict,
        to_vary_in_stream_dict,
        realm_msg_retention_days,
        feature_level,
        expect_msg_retention_text,
    ):
        model.stream_dict = stream_dict
        model.server_feature_level = feature_level
        model.initial_data["realm_message_retention_days"] = realm_msg_retention_days
        for stream_id in to_vary_in_stream_dict:
            model.stream_dict[stream_id].update(to_vary_in_stream_dict[stream_id])

        model.normalize_and_cache_message_retention_text()

        for stream_id in to_vary_in_stream_dict:
            assert (
                model.cached_retention_text[stream_id]
                == expect_msg_retention_text[stream_id]
            )

    @pytest.mark.parametrize("msg_id", [1, 5, set()])
    @pytest.mark.parametrize(
        "narrow",
        [
            [],
            [["stream", "hello world"]],
            [["stream", "hello world"], ["topic", "what's it all about?"]],
            [["pm-with", "FOO@zulip.com"]],
            [["pm-with", "Foo@zulip.com, Bar@zulip.com"]],
            [["is", "private"]],
            [["is", "starred"]],
        ],
    )
    def test_get_focus_in_current_narrow_individually(self, model, msg_id, narrow):
        model.index = {"pointer": {str(narrow): msg_id}}
        model.narrow = narrow
        assert model.get_focus_in_current_narrow() == msg_id

    @pytest.mark.parametrize("msg_id", [1, 5])
    @pytest.mark.parametrize(
        "narrow",
        [
            [],
            [["stream", "hello world"]],
            [["stream", "hello world"], ["topic", "what's it all about?"]],
            [["pm-with", "FOO@zulip.com"]],
            [["pm-with", "Foo@zulip.com, Bar@zulip.com"]],
            [["is", "private"]],
            [["is", "starred"]],
        ],
    )
    def test_set_focus_in_current_narrow(self, mocker, model, narrow, msg_id):
        from collections import defaultdict

        model.index = dict(pointer=defaultdict(set))
        model.narrow = narrow
        model.set_focus_in_current_narrow(msg_id)
        assert model.index["pointer"][str(narrow)] == msg_id

    @pytest.mark.parametrize(
        "narrow, is_search_narrow",
        [
            ([], False),
            ([["search", "FOO"]], True),
            ([["is", "private"]], False),
            ([["is", "private"], ["search", "FOO"]], True),
            ([["search", "FOO"], ["is", "private"]], True),
            ([["stream", "PTEST"]], False),
            ([["stream", "PTEST"], ["search", "FOO"]], True),
            ([["stream", "7"], ["topic", "Test"]], False),
            ([["stream", "7"], ["topic", "Test"], ["search", "FOO"]], True),
            ([["stream", "7"], ["search", "FOO"], ["topic", "Test"]], True),
            ([["search", "FOO"], ["stream", "7"], ["topic", "Test"]], True),
        ],
    )
    def test_is_search_narrow(self, model, narrow, is_search_narrow):
        model.narrow = narrow
        assert model.is_search_narrow() == is_search_narrow

    @pytest.mark.parametrize(
        "bad_args",
        [
            dict(topic="some topic"),
            dict(stream="foo", pm_with="someone"),
            dict(topic="blah", pm_with="someone"),
            dict(pm_with="someone", topic="foo"),
        ],
    )
    def test_set_narrow_bad_input(self, model, bad_args):
        with pytest.raises(RuntimeError):
            model.set_narrow(**bad_args)

    @pytest.mark.parametrize(
        "narrow, good_args",
        [
            ([], dict()),
            ([["stream", "some stream"]], dict(stream="some stream")),
            (
                [["stream", "some stream"], ["topic", "some topic"]],
                dict(stream="some stream", topic="some topic"),
            ),
            ([["is", "starred"]], dict(starred=True)),
            ([["is", "mentioned"]], dict(mentioned=True)),
            ([["is", "private"]], dict(pms=True)),
            ([["pm-with", "FOO@zulip.com"]], dict(pm_with="FOO@zulip.com")),
        ],
    )
    def test_set_narrow_already_set(self, model, narrow, good_args):
        model.narrow = narrow
        assert model.set_narrow(**good_args)
        assert model.narrow == narrow

    @pytest.mark.parametrize(
        "initial_narrow, narrow, good_args",
        [
            ([["stream", "foo"]], [], dict()),
            ([], [["stream", "Stream 1"]], dict(stream="Stream 1")),
            (
                [],
                [["stream", "Stream 1"], ["topic", "some topic"]],
                dict(stream="Stream 1", topic="some topic"),
            ),
            ([], [["is", "starred"]], dict(starred=True)),
            ([], [["is", "mentioned"]], dict(mentioned=True)),
            ([], [["is", "private"]], dict(pms=True)),
            ([], [["pm-with", "FOOBOO@gmail.com"]], dict(pm_with="FOOBOO@gmail.com")),
        ],
    )
    def test_set_narrow_not_already_set(
        self, model, initial_narrow, narrow, good_args, user_dict, stream_dict
    ):
        model.narrow = initial_narrow
        model.user_dict = user_dict
        model.stream_dict = stream_dict
        assert not model.set_narrow(**good_args)
        assert model.narrow != initial_narrow
        assert model.narrow == narrow
        # FIXME: Add assert for recipients being updated (other tests too?)

    @pytest.mark.parametrize(
        "narrow, index, current_ids",
        [
            ([], {"all_msg_ids": {0, 1}}, {0, 1}),
            ([["stream", "FOO"]], {"stream_msg_ids_by_stream_id": {1: {0, 1}}}, {0, 1}),
            (
                [["stream", "FOO"], ["topic", "BOO"]],
                {"topic_msg_ids": {1: {"BOO": {0, 1}}}},
                {0, 1},
            ),
            (
                [["stream", "FOO"], ["topic", "BOOBOO"]],  # Covers one empty-set case
                {"topic_msg_ids": {1: {"BOO": {0, 1}}}},
                set(),
            ),
            ([["is", "private"]], {"private_msg_ids": {0, 1}}, {0, 1}),
            (
                [["pm-with", "FOO@zulip.com"]],
                {"private_msg_ids_by_user_ids": {frozenset({1, 2}): {0, 1}}},
                {0, 1},
            ),
            (
                [["pm-with", "FOO@zulip.com"]],
                {  # Covers recipient empty-set case
                    "private_msg_ids_by_user_ids": {
                        frozenset({1, 3}): {0, 1}  # NOTE {1,3} not {1,2}
                    }
                },
                set(),
            ),
            ([["search", "FOO"]], {"search": {0, 1}}, {0, 1}),
            ([["is", "starred"]], {"starred_msg_ids": {0, 1}}, {0, 1}),
            (
                [["stream", "FOO"], ["search", "FOO"]],
                {
                    "stream_msg_ids_by_stream_id": {
                        1: {0, 1, 2}  # NOTE Should not be returned
                    },
                    "search": {0, 1},
                },
                {0, 1},
            ),
            ([["is", "mentioned"]], {"mentioned_msg_ids": {0, 1}}, {0, 1}),
        ],
    )
    def test_get_message_ids_in_current_narrow(
        self, mocker, model, narrow, index, current_ids
    ):
        model.recipients = frozenset({1, 2})
        model.stream_id = 1
        model.narrow = narrow
        model.index = index
        assert current_ids == model.get_message_ids_in_current_narrow()

    @pytest.mark.parametrize(
        "response, expected_index, return_value",
        [
            (
                {"result": "success", "topics": [{"name": "Foo"}, {"name": "Boo"}]},
                {23: ["Foo", "Boo"]},
                "",
            ),
            ({"result": "success", "topics": []}, {23: []}, ""),
            (
                {"result": "failure", "msg": "Some Error", "topics": []},
                {23: []},
                "Some Error",
            ),
        ],
    )
    def test__fetch_topics_in_streams(
        self, mocker, response, model, return_value, expected_index
    ) -> None:
        self.client.get_stream_topics = mocker.Mock(return_value=response)

        result = model._fetch_topics_in_streams([23])

        self.client.get_stream_topics.assert_called_once_with(23)
        assert model.index["topics"] == expected_index
        assert result == return_value
        if response["result"] != "success":
            self.display_error_if_present.assert_called_once_with(
                response, self.controller
            )

    @pytest.mark.parametrize(
        "topics_index, fetched",
        [
            (["test"], False),
            ([], True),
        ],
    )
    def test_topics_in_stream(self, mocker, model, topics_index, fetched, stream_id=1):
        model.index["topics"][stream_id] = topics_index
        model._fetch_topics_in_streams = mocker.Mock()

        return_value = model.topics_in_stream(stream_id)

        assert model._fetch_topics_in_streams.called == fetched
        assert model.index["topics"][stream_id] == return_value
        assert model.index["topics"][stream_id] is not return_value

    # pre server v3 provide user_id or id as a property within user key
    # post server v3 provide user_id as a property outside the user key
    @pytest.mark.parametrize("user_key", ["user_id", "id", None])
    @pytest.mark.parametrize(
        "emoji_unit, existing_reactions, expected_method",
        [
            case(
                ("thumbs_up", "1f44d", "unicode_emoji"),
                [],
                "POST",
                id="add_unicode_original_no_existing_emoji",
            ),
            case(
                ("singing", "3", "realm_emoji"),
                [],
                "POST",
                id="add_realm_original_no_existing_emoji",
            ),
            case(
                ("joy_cat", "1f639", "unicode_emoji"),
                [dict(user="me", emoji_code="1f44d")],
                "POST",
                id="add_unicode_original_mine_existing_different_emoji",
            ),
            case(
                ("zulip", "zulip", "zulip_extra_emoji"),
                [dict(user="me", emoji_code="1f639")],
                "POST",
                id="add_zulip_original_mine_existing_different_emoji",
            ),
            case(
                ("rock_on", "1f918", "unicode_emoji"),
                [dict(user="not me", emoji_code="1f918")],
                "POST",
                id="add_unicode_original_others_existing_same_emoji",
            ),
            case(
                ("grinning", "1f600", "unicode_emoji"),
                [dict(user="not me", emoji_code="1f600")],
                "POST",
                id="add_unicode_alias_others_existing_same_emoji",
            ),
            case(
                ("smiley", "1f603", "unicode_emoji"),
                [dict(user="me", emoji_code="1f603")],
                "DELETE",
                id="remove_unicode_original_mine_existing_same_emoji",
            ),
            case(
                ("smug", "1f60f", "unicode_emoji"),
                [dict(user="me", emoji_code="1f60f")],
                "DELETE",
                id="remove_unicode_alias_mine_existing_same_emoji",
            ),
            case(
                ("zulip", "zulip", "zulip_extra_emoji"),
                [dict(user="me", emoji_code="zulip")],
                "DELETE",
                id="remove_zulip_original_mine_existing_same_emoji",
            ),
        ],
    )
    def test_toggle_message_reaction_with_valid_emoji(
        self,
        mocker,
        model,
        user_key,
        emoji_unit,
        existing_reactions,
        expected_method,
        msg_id=5,
    ):
        # Map 'id' to running user_id or an arbitrary other (+1)
        id = (
            model.user_id
            if existing_reactions and existing_reactions[0]["user"] == "me"
            else model.user_id + 1
        )
        full_existing_reactions = [
            dict(er, user={user_key: id})
            if user_key is not None
            else dict(user_id=id, emoji_code=er["emoji_code"])
            for er in existing_reactions
        ]
        message = dict(id=msg_id, reactions=full_existing_reactions)
        emoji_name, emoji_code, emoji_type = emoji_unit
        reaction_spec = dict(
            emoji_name=emoji_name,
            reaction_type=emoji_type,
            emoji_code=emoji_code,
            message_id=str(msg_id),
        )
        response = mocker.Mock()
        model.client.add_reaction.return_value = response
        model.client.remove_reaction.return_value = response

        model.toggle_message_reaction(message, emoji_name)

        if expected_method == "POST":
            model.client.add_reaction.assert_called_once_with(reaction_spec)
            model.client.remove_reaction.assert_not_called()
        elif expected_method == "DELETE":
            model.client.remove_reaction.assert_called_once_with(reaction_spec)
            model.client.add_reaction.assert_not_called()
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    def test_toggle_message_reaction_with_invalid_emoji(self, model):
        with pytest.raises(AssertionError):
            model.toggle_message_reaction(dict(), "x")

    @pytest.mark.parametrize(
        "emoji_code, reactions, expected_has_user_reacted",
        [
            case(
                "1f600",
                [{"user": {"id": 2}, "emoji_code": "1f602"}],
                False,
                id="id_inside_user_field__user_not_reacted",
            ),
            case(
                "1f44d",
                [{"user": {"user_id": 1}, "emoji_code": "1f44d"}],
                True,
                id="user_id_inside_user_field__user_has_reacted",
            ),
            case(
                "zulip",
                [{"user_id": 1, "emoji_code": "zulip"}],
                True,
                id="no_user_field_with_user_id__user_has_reacted",
            ),
            case(
                "1f639",
                [{"user_id": 2, "emoji_code": "1f44d"}],
                False,
                id="no_user_field_with_user_id__user_not_reacted",
            ),
        ],
    )
    def test_has_user_reacted_to_message(
        self,
        model,
        emoji_code,
        reactions,
        expected_has_user_reacted,
        user_id=1,
        message_id=5,
    ):
        model.user_id = user_id
        message = dict(id=message_id, reactions=reactions)

        has_reacted = model.has_user_reacted_to_message(message, emoji_code=emoji_code)

        assert has_reacted == expected_has_user_reacted

    @pytest.mark.parametrize("recipient_user_ids", [[5140], [5140, 5179]])
    @pytest.mark.parametrize("status", ["start", "stop"])
    def test_send_typing_status_by_user_ids(
        self, mocker, model, status, recipient_user_ids
    ):
        response = mocker.Mock()
        mock_api_query = mocker.patch(
            CONTROLLER + ".client.set_typing_status", return_value=response
        )
        model._user_settings["send_private_typing_notifications"] = True

        model.send_typing_status_by_user_ids(recipient_user_ids, status=status)

        mock_api_query.assert_called_once_with(
            {"to": recipient_user_ids, "op": status},
        )

        self.display_error_if_present.assert_called_once_with(response, self.controller)

    @pytest.mark.parametrize("status", ["start", "stop"])
    def test_send_typing_status_with_no_recipients(
        self, model, status, recipient_user_ids=[]
    ):
        with pytest.raises(RuntimeError):
            model.send_typing_status_by_user_ids(recipient_user_ids, status=status)

    @pytest.mark.parametrize("recipient_user_ids", [[5140], [5140, 5179]])
    @pytest.mark.parametrize("status", ["start", "stop"])
    def test_send_typing_status_avoided_due_to_user_setting(
        self, mocker, model, status, recipient_user_ids
    ):
        model._user_settings["send_private_typing_notifications"] = False

        mock_api_query = mocker.patch(CONTROLLER + ".client.set_typing_status")

        model.send_typing_status_by_user_ids(recipient_user_ids, status=status)

        assert not mock_api_query.called
        assert not self.display_error_if_present.called

    @pytest.mark.parametrize(
        "response, return_value",
        [
            ({"result": "success"}, True),
            ({"result": "some_failure"}, False),
        ],
    )
    @pytest.mark.parametrize("recipients", [[5179], [5179, 5180]])
    def test_send_private_message(
        self, mocker, model, recipients, response, return_value, content="hi!"
    ):
        self.client.send_message = mocker.Mock(return_value=response)

        result = model.send_private_message(recipients, content)

        req = dict(type="private", to=recipients, content=content)
        self.client.send_message.assert_called_once_with(req)

        assert result == return_value
        self.display_error_if_present.assert_called_once_with(response, self.controller)
        if result == "success":
            self.notify_if_message_sent_outside_narrow.assert_called_once_with(
                req, self.controller
            )

    def test_send_private_message_with_no_recipients(
        self, model, content="hi!", recipients=[]
    ):
        with pytest.raises(RuntimeError):
            model.send_private_message(recipients, content)

    @pytest.mark.parametrize(
        "response, return_value",
        [
            ({"result": "success"}, True),
            ({"result": "some_failure"}, False),
        ],
    )
    def test_send_stream_message(
        self,
        mocker,
        model,
        response,
        return_value,
        content="hi!",
        stream="foo",
        topic="bar",
    ):
        self.client.send_message = mocker.Mock(return_value=response)

        result = model.send_stream_message(stream, topic, content)

        req = dict(type="stream", to=stream, subject=topic, content=content)
        self.client.send_message.assert_called_once_with(req)

        assert result == return_value
        self.display_error_if_present.assert_called_once_with(response, self.controller)

        if result == "success":
            self.notify_if_message_sent_outside_narrow.assert_called_once_with(
                req, self.controller
            )

    @pytest.mark.parametrize(
        "response, return_value",
        [
            ({"result": "success"}, True),
            ({"result": "some_failure"}, False),
        ],
    )
    def test_update_private_message(
        self, mocker, model, response, return_value, content="hi!", msg_id=1
    ):
        self.client.update_message = mocker.Mock(return_value=response)

        result = model.update_private_message(msg_id, content)

        req = dict(message_id=msg_id, content=content)
        self.client.update_message.assert_called_once_with(req)

        assert result == return_value
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    @pytest.mark.parametrize(
        "response, return_value",
        [
            case({"result": "success"}, True, id="API_success"),
            case({"result": "some_failure"}, False, id="API_error"),
        ],
    )
    @pytest.mark.parametrize(
        "kwargs, expected_report_success",
        [
            case(
                {
                    "propagate_mode": "change_one",
                    "content": "hi!",
                    "topic": "old topic",
                },
                None,  # None as footer is not updated.
                id="topic_passed_but_same_so_not_changed:content_changed",
            ),
            case(
                {
                    "propagate_mode": "change_one",
                    "topic": "Topic change",
                },
                [
                    "You changed one message's topic from ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " old topic "),
                    " to ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " Topic change "),
                    " .",
                ],
                id="topic_changed[one]",
            ),
            case(
                {
                    "propagate_mode": "change_all",
                    "topic": "old topic",
                },
                None,  # None as footer is not updated.
                id="topic_passed_but_same_so_not_changed[all]",
            ),
            case(
                {
                    "propagate_mode": "change_later",
                    "content": ":smile:",
                    "topic": "old topic",
                },
                None,  # None as footer is not updated.
                id="topic_passed_but_same_so_not_changed[later]:content_changed",
            ),
            case(
                {
                    "propagate_mode": "change_later",
                    "content": ":smile:",
                    "topic": "new_terminal",
                },
                [
                    "You changed some messages' topic from ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " old topic "),
                    " to ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " new_terminal "),
                    " .",
                ],
                id="topic_changed[later]:content_changed",
            ),
            case(
                {
                    "propagate_mode": "change_one",
                    "content": "Hey!",
                    "topic": "grett",
                },
                [
                    "You changed one message's topic from ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " old topic "),
                    " to ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " grett "),
                    " .",
                ],
                id="topic_changed[one]:content_changed",
            ),
            case(
                {
                    "propagate_mode": "change_all",
                    "content": "Lets party!",
                    "topic": "party",
                },
                [
                    "You changed all messages' topic from ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " old topic "),
                    " to ",
                    ("footer_contrast", f" stream {STREAM_TOPIC_SEPARATOR} "),
                    ("footer_contrast", " party "),
                    " .",
                ],
                id="topic_changed[all]:content_changed",
            ),
        ],
    )
    def test_update_stream_message(
        self,
        mocker,
        model,
        response,
        return_value,
        kwargs,
        expected_report_success,
        old_content="old content",
        old_stream_name="stream",
        old_topic_name="old topic",
        message_id=1,
    ):
        self.client.update_message = mocker.Mock(return_value=response)
        model.index["messages"][message_id]["subject"] = old_topic_name
        model.index["messages"][message_id]["display_recipient"] = old_stream_name
        model.index["messages"][message_id]["content"] = old_content

        result = model.update_stream_message(message_id=message_id, **kwargs)

        assert result == return_value

        self.display_error_if_present.assert_called_once_with(response, self.controller)

        report_success = model.controller.report_success
        if result and expected_report_success is not None:
            report_success.assert_called_once_with(expected_report_success, duration=6)
        else:
            report_success.assert_not_called()

        # Implementation detail; only check here that it's always called
        assert self.client.update_message.called

    @pytest.mark.parametrize(
        "ZFL, expect_API_notify_args",
        [
            (None, False),
            (8, False),
            (9, True),
            (152, True),
        ],
    )
    @pytest.mark.parametrize(
        "notify_args, API_notify_old_thread, API_notify_new_thread",
        [
            ({}, False, False),
            (dict(notify_new=False), False, False),
            (dict(notify_old=False), False, False),
            (dict(notify_old=True), True, False),
            (dict(notify_new=True), False, True),
            (dict(notify_new=True, notify_old=True), True, True),
        ],
    )
    def test_update_stream_message__notify_thread_vs_ZFL(
        self,
        model,
        ZFL,
        expect_API_notify_args,
        notify_args,
        API_notify_old_thread,
        API_notify_new_thread,
        message_id=1,
        old_content="old content",
        old_topic="old topic",
        old_stream_name="old stream name",
        new_topic="new topic",
        mode="change_all",
    ) -> None:
        model.server_feature_level = ZFL
        model.index["messages"][message_id]["subject"] = old_topic
        model.index["messages"][message_id]["display_recipient"] = old_stream_name
        model.index["messages"][message_id]["content"] = old_content

        base_kwargs = dict(message_id=message_id, topic=new_topic, propagate_mode=mode)

        model.update_stream_message(**base_kwargs, **notify_args)

        # Implementation detail, but only way of testing
        if expect_API_notify_args:
            expected_API_args = dict(
                base_kwargs,
                send_notification_to_old_thread=API_notify_old_thread,
                send_notification_to_new_thread=API_notify_new_thread,
            )
        else:
            expected_API_args = dict(base_kwargs)
        self.client.update_message.assert_called_once_with(expected_API_args)

    @pytest.mark.parametrize(
        "response, return_value",
        [
            (
                {
                    "result": "success",
                    "messages": [
                        {
                            "subject": "hi!",
                            "stream_id": 1,
                        }
                    ],
                },
                {
                    "subject": "hi!",
                    "stream_id": 1,
                },
            ),
            (
                {
                    "result": "success",
                    "messages": [
                        {
                            "subject": "hi!",
                            "stream_id": 1,
                        },
                        {
                            "subject": "hi!",
                            "stream_id": 1,
                        },
                    ],
                },
                None,
            ),
            ({"result": "some_failure", "messages": []}, None),
            ({"result": "success", "messages": []}, None),
        ],
    )
    def test_get_latest_message_in_topic(
        self,
        mocker,
        model,
        response,
        return_value,
        topic_name="hi!",
        stream_id=1,
    ):
        self.client.get_messages = mocker.Mock(return_value=response)

        result = model.get_latest_message_in_topic(stream_id, topic_name)

        assert result == return_value
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    @pytest.mark.parametrize(
        "user_role, user_type",
        [
            (None, "_"),
            ({"role": 100}, "_owner"),
            ({"role": 200}, "_admin"),
            ({"role": 300}, "_moderator"),
            ({"role": 400}, "_member"),
            ({"role": 600}, "_guest"),
        ],
    )
    @pytest.mark.parametrize(
        "realm_editing_settings, expected_response",
        [
            case(
                {
                    "allow_message_editing": False,
                    "allow_community_topic_editing": True,
                },
                {
                    "_": ["User not found", False],
                    "_owner": ["Editing messages is disabled", False],
                    "_admin": ["Editing messages is disabled", False],
                    "_moderator": ["Editing messages is disabled", False],
                    "_member": ["Editing messages is disabled", False],
                    "_guest": ["Editing messages is disabled", False],
                },
                id="editing_msg_disabled:PreZulip4.0",
            ),
            case(
                {
                    "allow_message_editing": True,
                    "allow_community_topic_editing": False,
                },
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["Editing topic is disabled", False],
                    "_member": ["Editing topic is disabled", False],
                    "_guest": ["Editing topic is disabled", False],
                },
                id="editing_topic_disabled:PreZulip4.0",
            ),
            case(
                {
                    "allow_message_editing": True,
                    "allow_community_topic_editing": True,
                },
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["", True],
                    "_member": ["", True],
                    "_guest": ["", True],
                },
                id="editing_topic_and_msg_enabled:PreZulip4.0",
            ),
            case(
                {"allow_message_editing": False, "edit_topic_policy": 1},
                {
                    "_": ["User not found", False],
                    "_owner": ["Editing messages is disabled", False],
                    "_admin": ["Editing messages is disabled", False],
                    "_moderator": ["Editing messages is disabled", False],
                    "_member": ["Editing messages is disabled", False],
                    "_guest": ["Editing messages is disabled", False],
                },
                id="all_but_no_editing:Zulip4.0+:ZFL75",
            ),
            case(
                {"allow_message_editing": True, "edit_topic_policy": 1},
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["", True],
                    "_member": ["", True],
                    "_guest": [
                        "Only organization administrators, moderators, full members and"
                        " members can edit topic",
                        False,
                    ],
                },
                id="members:Zulip4.0+:ZFL75",
            ),
            case(
                {"allow_message_editing": True, "edit_topic_policy": 2},
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": [
                        "Only organization administrators can edit topic",
                        False,
                    ],
                    "_member": [
                        "Only organization administrators can edit topic",
                        False,
                    ],
                    "_guest": [
                        "Only organization administrators can edit topic",
                        False,
                    ],
                },
                id="admins:Zulip4.0+:ZFL75",
            ),
            case(
                {"allow_message_editing": True, "edit_topic_policy": 3},
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["", True],
                    "_member": ["", True],
                    "_guest": [
                        "Only organization administrators, moderators and full members"
                        " can edit topic",
                        False,
                    ],
                },
                id="full_members:Zulip4.0+:ZFL75",
            ),
            case(
                {"allow_message_editing": True, "edit_topic_policy": 4},
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["", True],
                    "_member": [
                        "Only organization administrators and moderators"
                        " can edit topic",
                        False,
                    ],
                    "_guest": [
                        "Only organization administrators and moderators"
                        " can edit topic",
                        False,
                    ],
                },
                id="moderators:Zulip4.0+:ZFL75",
            ),
            case(
                {"allow_message_editing": True, "edit_topic_policy": 5},
                {
                    "_": ["User not found", False],
                    "_owner": ["", True],
                    "_admin": ["", True],
                    "_moderator": ["", True],
                    "_member": ["", True],
                    "_guest": ["", True],
                },
                id="guests:Zulip4.0+:ZFL75",
            ),
        ],
    )
    def test_can_user_edit_topic(
        self,
        mocker,
        model,
        initial_data,
        user_role,
        user_type,
        realm_editing_settings,
        expected_response,
    ):
        model.get_user_info = mocker.Mock(return_value=user_role)
        model.initial_data = initial_data
        initial_data["realm_allow_message_editing"] = realm_editing_settings[
            "allow_message_editing"
        ]
        allow_community_topic_editing = realm_editing_settings.get(
            "allow_community_topic_editing", None
        )
        edit_topic_policy = realm_editing_settings.get("edit_topic_policy", None)
        if allow_community_topic_editing is None:
            assert edit_topic_policy is not None
            initial_data["realm_edit_topic_policy"] = edit_topic_policy
        else:
            assert edit_topic_policy is None
            initial_data[
                "realm_allow_community_topic_editing"
            ] = allow_community_topic_editing
        report_error = model.controller.report_error

        result = model.can_user_edit_topic()

        assert result == expected_response[user_type][1]
        if result:
            report_error.assert_not_called()
        else:
            report_error.assert_called_once_with(expected_response[user_type][0])

    # NOTE: This tests only getting next-unread, not a fixed anchor
    def test_success_get_messages(
        self,
        mocker,
        messages_successful_response,
        index_all_messages,
        initial_data,
        num_before=30,
        num_after=10,
    ):
        self.client.register.return_value = initial_data
        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        # Setup mocks before calling get_messages
        self.client.get_messages.return_value = messages_successful_response
        mocker.patch(MODULE + ".index_messages", return_value=index_all_messages)
        model = Model(self.controller)
        request = {
            "anchor": 0,
            "num_before": num_before,
            "num_after": num_after,
            "apply_markdown": True,
            "use_first_unread_anchor": True,
            "client_gravatar": True,
            "narrow": json.dumps(model.narrow),
        }
        model.client.get_messages.assert_called_once_with(message_filters=request)
        assert model.index == index_all_messages
        anchor = messages_successful_response["anchor"]
        if anchor < 10000000000000000:
            assert model.index["pointer"][repr(model.narrow)] == anchor
        assert model._have_last_message[repr(model.narrow)] is True

    @pytest.mark.parametrize(
        "messages, expected_messages_response",
        [
            (
                {"topic_links": [{"url": "www.foo.com", "text": "Bar"}]},
                {"topic_links": [{"url": "www.foo.com", "text": "Bar"}]},
            ),
            (
                {"topic_links": ["www.foo1.com"]},
                {"topic_links": [{"url": "www.foo1.com", "text": ""}]},
            ),
            (
                {"topic_links": []},
                {"topic_links": []},
            ),
            (
                {"subject_links": ["www.foo2.com"]},
                {"topic_links": [{"url": "www.foo2.com", "text": ""}]},
            ),
            (
                {"subject_links": []},
                {"topic_links": []},
            ),
        ],
        ids=[
            "Zulip_4.0+_ZFL46_response_with_topic_links",
            "Zulip_3.0+_ZFL1_response_with_topic_links",
            "Zulip_3.0+_ZFL1_response_empty_topic_links",
            "Zulip_2.1+_response_with_subject_links",
            "Zulip_2.1+_response_empty_subject_links",
        ],
    )
    def test_modernize_message_response(
        self, model, messages, expected_messages_response
    ):
        assert model.modernize_message_response(messages) == expected_messages_response

    @pytest.mark.parametrize(
        "feature_level, to_vary_in_initial_data",
        [
            (None, {}),
            (27, {}),
            (52, {}),
            (
                53,
                {
                    "max_stream_name_length": 30,
                    "max_topic_length": 20,
                    "max_message_length": 5000,
                },
            ),
        ],
        ids=[
            "Zulip_2.1.x_ZFL_None_no_restrictions",
            "Zulip_3.1.x_ZFL_27_no_restrictions",
            "Zulip_4.0.x_ZFL_52_no_restrictions",
            "Zulip_4.0.x_ZFL_53_with_restrictions",
        ],
    )
    def test__store_content_length_restrictions(
        self, model, initial_data, feature_level, to_vary_in_initial_data
    ):
        initial_data.update(to_vary_in_initial_data)
        model.initial_data = initial_data
        model.server_feature_level = feature_level

        model._store_content_length_restrictions()

        if to_vary_in_initial_data:
            assert (
                model.max_stream_name_length
                == to_vary_in_initial_data["max_stream_name_length"]
            )
            assert model.max_topic_length == to_vary_in_initial_data["max_topic_length"]
            assert (
                model.max_message_length
                == to_vary_in_initial_data["max_message_length"]
            )
        else:
            assert model.max_stream_name_length == MAX_STREAM_NAME_LENGTH
            assert model.max_topic_length == MAX_TOPIC_NAME_LENGTH
            assert model.max_message_length == MAX_MESSAGE_LENGTH

    def test_get_message_false_first_anchor(
        self,
        mocker,
        messages_successful_response,
        index_all_messages,
        initial_data,
        num_before=30,
        num_after=10,
    ):
        # TEST FOR get_messages() with first_anchor=False
        # and anchor=0

        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        # Setup mocks before calling get_messages
        messages_successful_response["anchor"] = 0
        self.client.get_messages.return_value = messages_successful_response
        mocker.patch(MODULE + ".index_messages", return_value=index_all_messages)

        model = Model(self.controller)
        model.get_messages(num_before=num_before, num_after=num_after, anchor=0)
        self.client.get_messages.return_value = messages_successful_response
        assert model.index["pointer"][repr(model.narrow)] == 0

        # TEST `query_range` < no of messages received
        # RESET model._have_last_message value
        model._have_last_message[repr(model.narrow)] = False
        model.get_messages(num_after=0, num_before=0, anchor=0)
        assert model._have_last_message[repr(model.narrow)] is False

    # FIXME This only tests the case where the get_messages is in __init__
    def test_fail_get_messages(
        self, mocker, error_response, initial_data, num_before=30, num_after=10
    ):
        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        # Setup mock before calling get_messages
        # FIXME This has no influence on the result
        # self.client.do_api_query.return_value = error_response

        with pytest.raises(ServerConnectionFailure):
            Model(self.controller)

    @pytest.mark.parametrize(
        "response, expected_raw_content, display_error_called",
        [
            (
                {
                    "result": "success",
                    "msg": "",
                    "raw_content": "Feels **great** to be back!",
                },
                "Feels **great** to be back!",
                False,
            ),
            (
                {
                    "result": "error",
                    "msg": "Invalid message(s)",
                    "code": "BAD_REQUEST",
                },
                None,
                True,
            ),
        ],
    )
    def test_fetch_raw_message_content(
        self,
        mocker,
        model,
        expected_raw_content,
        response,
        display_error_called,
        message_id=1,
    ):
        self.client.get_raw_message.return_value = response

        return_value = model.fetch_raw_message_content(message_id)

        self.client.get_raw_message.assert_called_once_with(message_id)
        assert self.display_error_if_present.called == display_error_called
        assert return_value == expected_raw_content

    @pytest.mark.parametrize(
        "initial_muted_streams, value",
        [
            ({315}, True),
            ({205, 315}, False),
            (set(), True),
            ({205}, False),
        ],
        ids=["muting_205", "unmuting_205", "first_muted_205", "last_unmuted_205"],
    )
    def test_toggle_stream_muted_status(
        self,
        mocker,
        model,
        initial_muted_streams,
        value,
        response={"result": "success"},
    ):
        model.muted_streams = initial_muted_streams
        model.client.update_subscription_settings.return_value = response
        model.toggle_stream_muted_status(205)
        request = [{"stream_id": 205, "property": "is_muted", "value": value}]
        model.client.update_subscription_settings.assert_called_once_with(request)
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    def test_stream_access_type(
        self, model, general_stream, secret_stream, web_public_stream
    ):
        assert model.stream_access_type(general_stream["stream_id"]) == "public"
        assert model.stream_access_type(secret_stream["stream_id"]) == "private"
        assert model.stream_access_type(web_public_stream["stream_id"]) == "web-public"

    @pytest.mark.parametrize(
        "flags_before, expected_operator",
        [
            ([], "add"),
            (["starred"], "remove"),
            (["read"], "add"),
            (["read", "starred"], "remove"),
            (["starred", "read"], "remove"),
        ],
    )
    def test_toggle_message_star_status(
        self, mocker, model, flags_before, expected_operator
    ):
        mocker.patch("zulip.Client")
        response = mocker.Mock()
        model.client.update_message_flags.return_value = response
        message = {
            "id": 99,
            "flags": flags_before,
        }
        model.toggle_message_star_status(message)

        request = {"flag": "starred", "messages": [99], "op": expected_operator}
        model.client.update_message_flags.assert_called_once_with(request)
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    def test_mark_message_ids_as_read(self, model, mocker: Any) -> None:
        mock_api_query = mocker.patch(CONTROLLER + ".client.update_message_flags")

        model.mark_message_ids_as_read([1, 2])

        mock_api_query.assert_called_once_with(
            {"flag": "read", "messages": [1, 2], "op": "add"},
        )

    def test_mark_message_ids_as_read_empty_message_view(self, model) -> None:
        assert model.mark_message_ids_as_read([]) is None

    def test__update_initial_data(self, model, initial_data):
        assert model.initial_data == initial_data

    def test__update_initial_data_raises_exception(self, mocker, initial_data):
        # Initialize Model
        mocker.patch(MODEL + ".get_messages", return_value="")
        mocker.patch(MODEL + ".get_all_users", return_value=[])
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )

        # Setup mocks before calling get_messages
        self.client.register.return_value = initial_data
        self.client.get_members.return_value = {"members": initial_data["realm_users"]}
        model = Model(self.controller)

        # Test if raises Exception
        self.client.register.side_effect = Exception()
        with pytest.raises(Exception):
            model._update_initial_data()

    def test__group_info_from_realm_user_groups(self, model, user_groups_fixture):
        user_group_names = model._group_info_from_realm_user_groups(user_groups_fixture)
        assert model.user_group_by_id == {
            group["id"]: {
                "members": group["members"],
                "name": group["name"],
                "description": group["description"],
            }
            for group in user_groups_fixture
        }
        assert user_group_names == ["Group 1", "Group 2", "Group 3", "Group 4"]

    @pytest.mark.parametrize(
        ["to_vary_in_each_user", "key", "expected_value"],
        [
            case(
                {"full_name": "Test User"},
                "full_name",
                "Test User",
                id="user_full_name",
            ),
            case({}, "full_name", "(No name)", id="user_empty_full_name"),
            case(
                {"email": "person1@example.com"},
                "email",
                "person1@example.com",
                id="user_email",
            ),
            case({}, "email", "", id="user_empty_email"),
            case(
                {"date_joined": "2021-02-28T19:58:29.035543+00:00"},
                "date_joined",
                "2021-02-28T19:58:29.035543+00:00",
                id="user_date_joined",
            ),
            case({}, "date_joined", "", id="user_empty_date_joined"),
            case(
                {"timezone": "Asia/Kolkata"},
                "timezone",
                "Asia/Kolkata",
                id="user_timezone",
            ),
            case({}, "timezone", "", id="user_empty_timezone"),
            case({"bot_type": 1}, "bot_type", 1, id="user_bot_type"),
            case({}, "bot_type", None, id="user_empty_bot_type"),
            case({"role": 100}, "role", 100, id="user_is_owner:Zulip_4.0+_ZFL59"),
            case({"role": 200}, "role", 200, id="user_is_admin:Zulip_4.0+_ZFL59"),
            case({"role": 300}, "role", 300, id="user_is_moderator:Zulip_4.0+_ZFL60"),
            case({"role": 600}, "role", 600, id="user_is_guest:Zulip_4.0+_ZFL59"),
            case({}, "role", 400, id="user_is_member"),
            case({"is_owner": True}, "role", 100, id="user_is_owner:Zulip_3.0+"),
            case({"is_admin": True}, "role", 200, id="user_is_admin:preZulip_4.0"),
            case({"is_guest": True}, "role", 600, id="user_is_guest:preZulip_4.0"),
            case({"is_bot": True}, "is_bot", True, id="user_is_bot"),
            case(
                {"bot_owner_id": 12},
                "bot_owner_name",
                "Human 2",
                id="user_bot_has_owner:Zulip_3.0+_ZFL1",
            ),
            case(
                {"bot_owner": "person2@example.com"},
                "bot_owner_name",
                "Human 2",
                id="user_bot_has_owner:preZulip_3.0",
            ),
            case({}, "bot_owner_name", "", id="user_bot_has_no_owner"),
        ],
    )
    def test_get_user_info(
        self,
        model,
        mocker,
        _all_users_by_id,
        user_dict,
        to_vary_in_each_user,
        key,
        expected_value,
    ):
        _all_users_by_id[11] = dict({"user_id": 11}, **to_vary_in_each_user)
        model._all_users_by_id = _all_users_by_id
        model.user_dict = user_dict

        assert model.get_user_info(11)[key] == expected_value

    def test_get_user_info_USER_NOT_FOUND(self, model):
        assert model.get_user_info(-1) is None

    def test_get_user_info_sample_response(
        self, model, _all_users_by_id, tidied_user_info_response
    ):
        model._all_users_by_id = _all_users_by_id
        assert model.get_user_info(12) == tidied_user_info_response

    def test_get_all_users(self, mocker, initial_data, user_list, user_dict, user_id):
        mocker.patch(MODEL + ".get_messages", return_value="")
        self.client.register.return_value = initial_data
        mocker.patch(MODEL + "._subscribe_to_streams")
        self.classify_unread_counts = mocker.patch(
            MODULE + ".classify_unread_counts", return_value=[]
        )
        model = Model(self.controller)
        assert model.user_dict == user_dict
        assert model.users == user_list

    @pytest.mark.parametrize("muted", powerset([99, 1000]))
    @pytest.mark.parametrize("visual_notification_enabled", powerset([99, 1000]))
    def test__subscribe_to_streams(
        self, initial_data, muted, visual_notification_enabled, model
    ):
        subs = [
            dict(
                entry,
                is_muted=entry["stream_id"] in muted,
                desktop_notifications=entry["stream_id"] in visual_notification_enabled,
            )
            for entry in initial_data["subscriptions"]
        ]

        model._subscribe_to_streams(subs)

        assert len(model.stream_dict)
        assert all(
            msg_id == msg["stream_id"] for msg_id, msg in model.stream_dict.items()
        )
        assert model.muted_streams == muted
        assert model.pinned_streams == []  # FIXME generalize/parametrize
        assert len(model.unpinned_streams)  # FIXME generalize/parametrize
        assert model.visual_notified_streams == visual_notification_enabled

    def test__handle_message_event_with_Falsey_log(
        self, mocker, model, message_fixture
    ):
        model._have_last_message[repr([])] = True
        mocker.patch(MODEL + "._update_topic_index")
        mocker.patch(MODULE + ".index_messages", return_value={})
        self.controller.view.message_view = mocker.Mock(log=[])
        create_msg_box_list = mocker.patch(
            MODULE + ".create_msg_box_list", return_value=["msg_w"]
        )
        model.notify_user = mocker.Mock()
        event = {"type": "message", "message": message_fixture}

        model._handle_message_event(event)

        assert len(self.controller.view.message_view.log) == 1  # Added "msg_w"
        model.notify_user.assert_called_once_with(event["message"])
        create_msg_box_list.assert_called_once_with(
            model, [message_fixture["id"]], last_message=None
        )

    def test__handle_message_event_with_valid_log(self, mocker, model, message_fixture):
        model._have_last_message[repr([])] = True
        mocker.patch(MODEL + "._update_topic_index")
        mocker.patch(MODULE + ".index_messages", return_value={})
        self.controller.view.message_view = mocker.Mock(log=[mocker.Mock()])
        create_msg_box_list = mocker.patch(
            MODULE + ".create_msg_box_list", return_value=["msg_w"]
        )
        model.notify_user = mocker.Mock()
        event = {"type": "message", "message": message_fixture}

        model._handle_message_event(event)

        log = self.controller.view.message_view.log
        assert len(log) == 2  # Added "msg_w"
        model.notify_user.assert_called_once_with(event["message"])
        # NOTE: So we expect the first element *was* the last_message parameter
        expected_last_msg = log[0].original_widget.message
        create_msg_box_list.assert_called_once_with(
            model, [message_fixture["id"]], last_message=expected_last_msg
        )

    def test__handle_message_event_with_flags(self, mocker, model, message_fixture):
        model._have_last_message[repr([])] = True
        mocker.patch(MODEL + "._update_topic_index")
        mocker.patch(MODULE + ".index_messages", return_value={})
        self.controller.view.message_view = mocker.Mock(log=[mocker.Mock()])
        mocker.patch(MODULE + ".create_msg_box_list", return_value=["msg_w"])
        model.notify_user = mocker.Mock()
        set_count = mocker.patch(MODULE + ".set_count")

        # Test event with flags
        event = {
            "type": "message",
            "message": message_fixture,
            "flags": ["read", "mentioned"],
        }

        model._handle_message_event(event)

        # set count not called since 'read' flag present.
        set_count.assert_not_called()

        # Test event without flags
        model.notify_user.assert_called_once_with(event["message"])
        self.controller.view.message_view.log = [mocker.Mock()]
        event = {
            "type": "message",
            "message": message_fixture,
            "flags": [],
        }

        model._handle_message_event(event)

        # set count called since the message is unread.
        set_count.assert_called_once_with([event["message"]["id"]], self.controller, 1)

    @pytest.mark.parametrize(
        "response, narrow, recipients, log",
        [
            case(
                {"type": "stream", "stream_id": 1, "subject": "FOO", "id": 1},
                [],
                frozenset(),
                ["msg_w"],
                id="stream_to_all_messages",
            ),
            case(
                {"type": "private", "id": 1},
                [["is", "private"]],
                frozenset(),
                ["msg_w"],
                id="private_to_all_private",
            ),
            case(
                {
                    "type": "stream",
                    "id": 1,
                    "stream_id": 1,
                    "subject": "FOO",
                    "display_recipient": "a",
                },
                [["stream", "a"]],
                frozenset(),
                ["msg_w"],
                id="stream_to_stream",
            ),
            case(
                {
                    "type": "stream",
                    "id": 1,
                    "stream_id": 1,
                    "subject": "b",
                    "display_recipient": "a",
                },
                [["stream", "a"], ["topic", "b"]],
                frozenset(),
                ["msg_w"],
                id="stream_to_topic",
            ),
            case(
                {
                    "type": "stream",
                    "id": 1,
                    "stream_id": 1,
                    "subject": "b",
                    "display_recipient": "a",
                },
                [["stream", "c"], ["topic", "b"]],
                frozenset(),
                [],
                id="stream_to_different_stream_same_topic",
            ),
            case(
                {
                    "type": "private",
                    "id": 1,
                    "display_recipient": [{"id": 5827}, {"id": 5}],
                },
                [["pm-with", "notification-bot@zulip.com"]],
                frozenset({5827, 5}),
                ["msg_w"],
                id="user_pm_x_appears_in_narrow_with_x",
            ),
            case(
                {"type": "private", "id": 1},
                [["is", "search"]],
                frozenset(),
                [],
                id="search",
            ),
            case(
                {
                    "type": "private",
                    "id": 1,
                    "display_recipient": [{"id": 5827}, {"id": 3212}],
                },
                [["pm-with", "notification-bot@zulip.com"]],
                frozenset({5827, 5}),
                [],
                id="user_pm_x_does_not_appear_in_narrow_without_x",
            ),
            case(
                {
                    "type": "stream",
                    "id": 1,
                    "stream_id": 1,
                    "subject": "c",
                    "display_recipient": "a",
                    "flags": ["mentioned"],
                },
                [["is", "mentioned"]],
                frozenset(),
                ["msg_w"],
                id="mentioned_msg_in_mentioned_msg_narrow",
            ),
        ],
    )
    def test__handle_message_event(
        self, mocker, user_profile, response, narrow, recipients, model, log
    ):
        model._have_last_message[repr(narrow)] = True
        mocker.patch(MODEL + "._update_topic_index")
        mocker.patch(MODULE + ".index_messages", return_value={})
        mocker.patch(MODULE + ".create_msg_box_list", return_value=["msg_w"])
        set_count = mocker.patch(MODULE + ".set_count")
        self.controller.view.message_view = mocker.Mock(log=[])
        (
            self.controller.view.left_panel.is_in_topic_view_with_stream_id.return_value
        ) = False
        model.notify_user = mocker.Mock()
        model.narrow = narrow
        model.recipients = recipients
        model.user_id = user_profile["user_id"]
        event = {
            "type": "message",
            "message": response,
            "flags": response["flags"] if "flags" in response else [],
        }

        model._handle_message_event(event)

        assert self.controller.view.message_view.log == log
        set_count.assert_called_once_with([response["id"]], self.controller, 1)

        model._have_last_message[repr(narrow)] = False
        model.notify_user.assert_called_once_with(response)

        model._handle_message_event(event)

        # LOG REMAINS THE SAME IF UPDATE IS FALSE
        assert self.controller.view.message_view.log == log

    @pytest.mark.parametrize(
        "topic_name, topic_order_initial, topic_order_final",
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
    def test__update_topic_index(
        self, topic_name, topic_order_initial, topic_order_final, model, mocker
    ):
        model.index = {
            "topics": {
                86: topic_order_initial,
            }
        }
        model.topics_in_stream = mocker.Mock(return_value=topic_order_initial)

        model._update_topic_index(86, topic_name)

        model.topics_in_stream.assert_called_once_with(86)
        assert model.index["topics"][86] == topic_order_final

    # TODO: Ideally message_fixture would use standardized ids?
    @pytest.mark.parametrize(
        [
            "user_id",
            "vary_each_msg",
            "visual_notification_status",
            "types_when_notify_called",
        ],
        [
            (
                5140,
                {"flags": ["mentioned", "wildcard_mentioned"]},
                True,
                [],
            ),  # message_fixture sender_id is 5140
            (5179, {"flags": ["mentioned"]}, False, ["stream", "private"]),
            (5179, {"flags": ["wildcard_mentioned"]}, False, ["stream", "private"]),
            (5179, {"flags": []}, True, ["stream"]),
            (5179, {"flags": []}, False, ["private"]),
        ],
        ids=[
            "not_notified_since_self_message",
            "notified_stream_and_private_since_directly_mentioned",
            "notified_stream_and_private_since_wildcard_mentioned",
            "notified_stream_since_stream_has_desktop_notifications",
            "notified_private_since_private_message",
        ],
    )
    def test_notify_users_calling_msg_type(
        self,
        mocker,
        model,
        message_fixture,
        user_id,
        vary_each_msg,
        visual_notification_status,
        types_when_notify_called,
    ):
        message_fixture.update(vary_each_msg)
        model.user_id = user_id
        mocker.patch(
            MODEL + ".is_visual_notifications_enabled",
            return_value=visual_notification_status,
        )
        notify = mocker.patch(MODULE + ".notify")

        model.notify_user(message_fixture)

        target = None
        if message_fixture["type"] in types_when_notify_called:
            who = message_fixture["type"]
            if who == "stream":
                target = "PTEST -> Test"
            elif who == "private":
                target = "you"
                if len(message_fixture["display_recipient"]) > 2:
                    target += ", Bar Bar"
        if target is not None:
            title = f"Test Organization Name:\nFoo Foo (to {target})"
            # TODO: Test message content too?
            notify.assert_called_once_with(title, mocker.ANY)
        else:
            notify.assert_not_called

    @pytest.mark.parametrize(
        "content, expected_notification_text",
        [
            case("<p>hi</p>", "hi", id="simple_text"),
            case(
                "\n".join(
                    [
                        '<div class="spoiler-block"><div class="spoiler-header">'
                        "<p>title of spoiler</p>"
                        '</div><div class="spoiler-content" aria-hidden="true">'
                        "<p>content of spoiler</p>"
                        "</div></div>"
                    ]
                ),
                "title of spoiler (...)",
                id="spoiler_with_title",
            ),
            case(
                "\n".join(
                    [
                        '<div class="spoiler-block"><div class="spoiler-header">'
                        '</div><div class="spoiler-content" aria-hidden="true">'
                        "<p>content of spoiler</p>"
                        "</div></div>"
                    ]
                ),
                "(...)",
                id="spoiler_no_title",
            ),
        ],
    )
    def test_notify_user_transformed_content(
        self, mocker, model, message_fixture, content, expected_notification_text
    ):
        mocker.patch(MODEL + ".is_visual_notifications_enabled", lambda s, id: True)
        notify = mocker.patch(MODULE + ".notify")
        message_fixture["content"] = content

        model.notify_user(message_fixture)

        notify.assert_called_once_with(mocker.ANY, expected_notification_text)

    @pytest.mark.parametrize(
        "notify_enabled, is_notify_called",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_notify_users_enabled(
        self, mocker, model, message_fixture, notify_enabled, is_notify_called
    ):
        message_fixture.update({"sender_id": 2, "flags": ["mentioned"]})
        model.controller.notify_enabled = notify_enabled
        model.user_id = 1
        notify = mocker.patch(MODULE + ".notify")
        model.notify_user(message_fixture)
        assert notify.called == is_notify_called

    @pytest.mark.parametrize(
        "hide_content, expected_content",
        [(True, "New direct message from Foo Foo"), (False, "private content here.")],
    )
    def test_notify_users_hides_PM_content_based_on_user_setting(
        self, mocker, model, private_message_fixture, hide_content, expected_content
    ):
        notify = mocker.patch(MODULE + ".notify")
        model._user_settings["pm_content_in_desktop_notifications"] = not hide_content

        message = private_message_fixture
        message["user_id"] = 5179
        message["flags"] = []

        model.notify_user(message)

        others = ", Boo Boo, Bar Bar" if len(message["display_recipient"]) > 2 else ""
        notify.assert_called_once_with(
            f"Test Organization Name:\nFoo Foo (to you{others})", expected_content
        )

    @pytest.mark.parametrize(
        "event, expected_times_messages_rerendered, expected_index, topic_view_enabled",
        [
            case(
                {  # Only subject of 1 message is updated.
                    "message_id": 1,
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [1],
                },
                1,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "new subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {1}, "old subject": {2}},
                    },
                    "edited_messages": {1},
                    "topics": {10: []},
                },
                False,
                id="Only subject of 1 message is updated",
            ),
            case(
                {  # Subject of 2 messages is updated
                    "message_id": 1,
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [1, 2],
                },
                2,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "new subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "new subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {1, 2}, "old subject": set()},
                    },
                    "edited_messages": {1},
                    "topics": {10: []},
                },
                False,
                id="Subject of 2 messages is updated",
            ),
            case(
                {  # Message content is updated
                    "message_id": 1,
                    "stream_id": 10,
                    "rendered_content": "<p>new content</p>",
                },
                1,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "<p>new content</p>",
                            "subject": "old subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": set(), "old subject": {1, 2}},
                    },
                    "edited_messages": {1},
                    "topics": {10: ["new subject", "old subject"]},
                },
                False,
                id="Message content is updated",
            ),
            case(
                {  # Both message content and subject is updated.
                    "message_id": 1,
                    "rendered_content": "<p>new content</p>",
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [1],
                },
                2,
                {  # 2=update of subject & content
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "<p>new content</p>",
                            "subject": "new subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {1}, "old subject": {2}},
                    },
                    "edited_messages": {1},
                    "topics": {10: []},
                },
                False,
                id="Both message content and subject is updated",
            ),
            case(
                {  # Some new type of update which we don't handle yet.
                    "message_id": 1,
                    "foo": "boo",
                },
                0,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": set(), "old subject": {1, 2}},
                    },
                    "edited_messages": {1},
                    "topics": {10: ["new subject", "old subject"]},
                },
                False,
                id="Some new type of update which we don't handle yet",
            ),
            case(
                {  # message_id not present in index, topic view closed.
                    "message_id": 3,
                    "rendered_content": "<p>new content</p>",
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [3],
                },
                0,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {3}, "old subject": {1, 2}},
                    },
                    "edited_messages": set(),
                    "topics": {10: []},  # This resets the cache
                },
                False,
                id="message_id not present in index, topic view closed",
            ),
            case(
                {  # message_id not present in index, topic view is enabled.
                    "message_id": 3,
                    "rendered_content": "<p>new content</p>",
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [3],
                },
                0,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {3}, "old subject": {1, 2}},
                    },
                    "edited_messages": set(),
                    "topics": {10: ["new subject", "old subject"]},
                },
                True,
                id="message_id not present in index, topic view is enabled",
            ),
            case(
                {  # Message content is updated and topic view is enabled.
                    "message_id": 1,
                    "rendered_content": "<p>new content</p>",
                    "orig_subject": "old subject",
                    "subject": "new subject",
                    "stream_id": 10,
                    "message_ids": [1],
                },
                2,
                {
                    "messages": {
                        1: {
                            "id": 1,
                            "stream_id": 10,
                            "content": "<p>new content</p>",
                            "subject": "new subject",
                        },
                        2: {
                            "id": 2,
                            "stream_id": 10,
                            "content": "old content",
                            "subject": "old subject",
                        },
                    },
                    "topic_msg_ids": {
                        10: {"new subject": {1}, "old subject": {2}},
                    },
                    "edited_messages": {1},
                    "topics": {10: ["new subject", "old subject"]},
                },
                True,
                id="Message content is updated and topic view is enabled",
            ),
        ],
    )
    def test__handle_update_message_event(
        self,
        mocker,
        model,
        event,
        expected_index,
        expected_times_messages_rerendered,
        topic_view_enabled,
    ):
        event["type"] = "update_message"

        model.index = {
            "messages": {
                message_id: {
                    "id": message_id,
                    "stream_id": 10,
                    "content": "old content",
                    "subject": "old subject",
                }
                for message_id in [1, 2]
            },
            "topic_msg_ids": {  # FIXME? consider test for eg. absence of empty set
                10: {"new subject": set(), "old subject": {1, 2}},
            },
            "edited_messages": set(),
            "topics": {10: ["new subject", "old subject"]},
        }
        mocker.patch(MODEL + "._update_rendered_view")

        def _set_topics_to_old_and_new(event):
            model.index["topics"][10] = ["new subject", "old subject"]

        fetch_topics = mocker.patch(
            MODEL + "._fetch_topics_in_streams", side_effect=_set_topics_to_old_and_new
        )

        view = model.controller.view
        view.left_panel.is_in_topic_view_with_stream_id.return_value = (
            topic_view_enabled
        )

        model._handle_update_message_event(event)

        assert model.index == expected_index

        calls_to_update_messages = model._update_rendered_view.call_count
        assert calls_to_update_messages == expected_times_messages_rerendered

        if topic_view_enabled:
            fetch_topics.assert_called_once_with([event["stream_id"]])
            stream_button = view.topic_w.stream_button
            view.left_panel.show_topic_view.assert_called_once_with(stream_button)
            model.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize(
        "subject, narrow, new_log_len",
        [
            ("foo", [["stream", "boo"], ["topic", "foo"]], 2),
            ("foo", [["stream", "boo"], ["topic", "not foo"]], 1),
            ("foo", [], 2),
        ],
        ids=[
            "msgbox_updated_in_topic_narrow",
            "msgbox_removed_due_to_topic_narrow_mismatch",
            "msgbox_updated_in_all_messages_narrow",
        ],
    )
    def test__update_rendered_view(
        self, mocker, model, subject, narrow, new_log_len, msg_id=1
    ):
        msg_w = mocker.Mock()
        other_msg_w = mocker.Mock()
        msg_w.original_widget.message = {"id": msg_id, "subject": subject}
        model.narrow = narrow
        other_msg_w.original_widget.message = {"id": 2}
        self.controller.view.message_view = mocker.Mock(log=[msg_w, other_msg_w])
        # New msg widget generated after updating index.
        new_msg_w = mocker.Mock()
        mocker.patch(MODULE + ".create_msg_box_list", return_value=[new_msg_w])

        model._update_rendered_view(msg_id)

        # If there are 2 msgs and first one is updated, next one is updated too
        if new_log_len == 2:
            other_msg_w = new_msg_w
        assert (
            self.controller.view.message_view.log
            == [new_msg_w, other_msg_w][-new_log_len:]
        )
        assert model.controller.update_screen.called

    @pytest.mark.parametrize(
        "subject, narrow, narrow_changed",
        [
            ("foo", [["stream", "boo"], ["topic", "foo"]], False),
            ("foo", [["stream", "boo"], ["topic", "not foo"]], True),
            ("foo", [], False),
        ],
        ids=[
            "same_topic_narrow",
            "previous_topic_narrow_empty_so_change_narrow",
            "same_all_messages_narrow",
        ],
    )
    def test__update_rendered_view_change_narrow(
        self, mocker, model, subject, narrow, narrow_changed, msg_id=1
    ):
        msg_w = mocker.Mock()
        msg_w.original_widget.message = {"id": msg_id, "subject": subject}
        model.narrow = narrow
        self.controller.view.message_view = mocker.Mock(log=[msg_w])
        # New msg widget generated after updating index.
        original_widget = mocker.Mock(message=dict(id=2))  # FIXME: id matters?
        new_msg_w = mocker.Mock(original_widget=original_widget)
        mocker.patch(MODULE + ".create_msg_box_list", return_value=[new_msg_w])

        model._update_rendered_view(msg_id)

        assert model.controller.narrow_to_topic.called == narrow_changed
        assert model.controller.update_screen.called

    @pytest.fixture
    def reaction_event_factory(self):
        def _factory(*, op: str, message_id: int):
            return {
                "emoji_code": "1f44d",
                "id": 2,
                "user": {
                    "email": "Foo@zulip.com",
                    "user_id": 5140,
                    "full_name": "Foo Boo",
                },
                "reaction_type": "unicode_emoji",
                "message_id": message_id,
                "emoji_name": "thumbs_up",
                "type": "reaction",
                "op": op,
            }

        return _factory

    @pytest.fixture
    def reaction_event_index_factory(self):
        """
        Generate index for reaction tests based on minimal specification

        Input is a list of pairs, of a message-id and a list of reaction tuples
        NOTE: reactions as None indicate not indexed, [] indicates no reaction
        """
        MsgsType = List[Tuple[int, Optional[List[Tuple[int, str, str, str]]]]]

        def _factory(msgs: MsgsType):
            return {
                "messages": {
                    message_id: {
                        "id": message_id,
                        "content": f"message content {message_id}",
                        "reactions": [
                            {
                                "user": {
                                    "email": f"User email #{user_id}",
                                    "full_name": f"User #{user_id}",
                                    "user_id": user_id,
                                },
                                "reaction_type": type,
                                "emoji_code": code,
                                "emoji_name": name,
                            }
                            for user_id, type, code, name in reactions
                        ],
                    }
                    for message_id, reactions in msgs
                    if reactions is not None
                }
            }

        return _factory

    @pytest.mark.parametrize("op", ["add", "remove"])
    def test__handle_reaction_event_not_in_index(
        self,
        mocker,
        model,
        reaction_event_factory,
        reaction_event_index_factory,
        op,
        unindexed_message_id=1,
    ):
        reaction_event = reaction_event_factory(
            op=op,
            message_id=unindexed_message_id,
        )
        model.index = reaction_event_index_factory(
            [
                (unindexed_message_id, None),  # explicitly exclude
                (2, [(1, "unicode_emoji", "1232", "thumbs_up")]),
                (3, []),
            ]
        )
        model._update_rendered_view = mocker.Mock()
        previous_index = deepcopy(model.index)

        model._handle_reaction_event(reaction_event)

        # If there was no message earlier then don't update
        assert model.index == previous_index
        assert not model._update_rendered_view.called

    @pytest.mark.parametrize(
        "op, expected_number_after",
        [
            ("add", 2),
            ("remove", 1),  # Removed emoji doesn't match, so length remains 1
        ],
    )
    def test__handle_reaction_event_for_msg_in_index(
        self,
        mocker,
        model,
        reaction_event_factory,
        reaction_event_index_factory,
        op,
        expected_number_after,
        event_message_id=1,
    ):
        reaction_event = reaction_event_factory(
            op=op,
            message_id=event_message_id,
        )
        model.index = reaction_event_index_factory(
            [
                (1, [(1, "unicode_emoji", "1232", "thumbs_up")]),
                (2, []),
            ]
        )
        model._update_rendered_view = mocker.Mock()

        model._handle_reaction_event(reaction_event)

        end_reactions = model.index["messages"][event_message_id]["reactions"]
        assert len(end_reactions) == expected_number_after

        model._update_rendered_view.assert_called_once_with(event_message_id)

    @pytest.fixture(
        params=[
            ("op", 32),  # At server feature level 32, event uses standard field
            ("operation", 31),
            ("operation", None),
        ]
    )
    def update_message_flags_operation(self, request):
        return request.param

    def test_update_star_status_no_index(
        self, mocker, model, update_message_flags_operation
    ):
        operation, model.server_feature_level = update_message_flags_operation

        model.index = dict(messages={})  # Not indexed
        event = {
            "type": "update_message_flags",
            "messages": [1],
            "flag": "starred",
            "all": False,
            operation: "add",
        }
        mocker.patch(MODEL + "._update_rendered_view")
        set_count = mocker.patch(MODULE + ".set_count")

        model._handle_update_message_flags_event(event)

        assert model.index == dict(messages={})
        model._update_rendered_view.assert_not_called()
        set_count.assert_not_called()
        self.controller.view.starred_button.update_count.assert_called()

    def test_update_star_status_invalid_operation(
        self,
        mocker,
        model,
        update_message_flags_operation,
    ):
        operation, model.server_feature_level = update_message_flags_operation

        model.index = dict(messages={1: {"flags": None}})  # Minimal
        event = {
            "type": "update_message_flags",
            "messages": [1],
            "flag": "starred",
            operation: "OTHER",  # not 'add' or 'remove'
            "all": False,
        }
        mocker.patch(MODEL + "._update_rendered_view")
        set_count = mocker.patch(MODULE + ".set_count")
        with pytest.raises(RuntimeError):
            model._handle_update_message_flags_event(event)
        model._update_rendered_view.assert_not_called()
        set_count.assert_not_called()
        self.controller.view.starred_button.update_count.assert_not_called()

    @pytest.mark.parametrize(
        "event_message_ids, indexed_ids",
        [
            ([1], [1]),
            ([1, 2], [1]),
            ([1, 2], [1, 2]),
            ([1], [1, 2]),
            ([], [1, 2]),
            ([1, 2], []),
        ],
    )
    @pytest.mark.parametrize(
        "event_op, scaling, flags_before, flags_after",
        [
            ("add", 1, [], ["starred"]),
            ("add", 1, ["read"], ["read", "starred"]),
            ("add", 1, ["starred"], ["starred"]),
            ("add", 1, ["read", "starred"], ["read", "starred"]),
            ("remove", -1, [], []),
            ("remove", -1, ["read"], ["read"]),
            ("remove", -1, ["starred"], []),
            ("remove", -1, ["read", "starred"], ["read"]),
            ("remove", -1, ["starred", "read"], ["read"]),
        ],
    )
    def test_update_star_status(
        self,
        mocker,
        model,
        event_op,
        event_message_ids,
        indexed_ids,
        scaling,
        flags_before,
        flags_after,
        update_message_flags_operation,
    ):
        operation, model.server_feature_level = update_message_flags_operation

        model.index = dict(
            messages={msg_id: {"flags": flags_before} for msg_id in indexed_ids},
            starred_msg_ids={
                msg_id for msg_id in indexed_ids if "starred" in flags_before
            },
        )
        event = {
            "type": "update_message_flags",
            "messages": event_message_ids,
            "flag": "starred",
            operation: event_op,
            "all": False,
        }
        self.controller.view.starred_button.count = 0
        mocker.patch(MODEL + "._update_rendered_view")
        set_count = mocker.patch(MODULE + ".set_count")
        update_star_count = self.controller.view.starred_button.update_count

        model._handle_update_message_flags_event(event)

        assert model.index["starred_msg_ids"] == {
            message_id
            for message_id, details in model.index["messages"].items()
            if "starred" in details["flags"]
        }
        changed_ids = set(indexed_ids) & set(event_message_ids)
        for changed_id in changed_ids:
            assert model.index["messages"][changed_id]["flags"] == flags_after
        model._update_rendered_view.assert_has_calls(
            [mocker.call(changed_id) for changed_id in changed_ids]
        )

        for unchanged_id in set(indexed_ids) - set(event_message_ids):
            assert model.index["messages"][unchanged_id]["flags"] == flags_before

        count = len(event_message_ids) * scaling
        update_star_count.assert_called_with(
            self.controller.view.starred_button.count + count
        )

        set_count.assert_not_called()

    @pytest.mark.parametrize(
        "event_message_ids, indexed_ids",
        [
            ([1], [1]),
            ([1, 2], [1]),
            ([1, 2], [1, 2]),
            ([1], [1, 2]),
            ([], [1, 2]),
            ([1, 2], []),
        ],
    )
    @pytest.mark.parametrize(
        "event_op, flags_before, flags_after",
        [
            ("add", [], ["read"]),
            ("add", ["read"], ["read"]),
            ("add", ["starred"], ["starred", "read"]),
            ("add", ["read", "starred"], ["read", "starred"]),
            ("remove", [], []),
            ("remove", ["read"], ["read"]),  # msg cannot be marked 'unread'
            ("remove", ["starred"], ["starred"]),
            ("remove", ["starred", "read"], ["starred", "read"]),
            ("remove", ["read", "starred"], ["read", "starred"]),
        ],
    )
    def test_update_read_status(
        self,
        mocker,
        model,
        event_op,
        event_message_ids,
        indexed_ids,
        flags_before,
        flags_after,
        update_message_flags_operation,
    ):
        operation, model.server_feature_level = update_message_flags_operation

        model.index = dict(
            messages={msg_id: {"flags": flags_before} for msg_id in indexed_ids},
            starred_msg_ids={
                msg_id for msg_id in indexed_ids if "starred" in flags_before
            },
        )
        event = {
            "type": "update_message_flags",
            "messages": event_message_ids,
            "flag": "read",
            operation: event_op,
            "all": False,
        }

        mocker.patch(MODEL + "._update_rendered_view")
        set_count = mocker.patch(MODULE + ".set_count")

        model._handle_update_message_flags_event(event)

        changed_ids = set(indexed_ids) & set(event_message_ids)
        for changed_id in changed_ids:
            assert model.index["messages"][changed_id]["flags"] == flags_after

            if event_op == "add":
                model._update_rendered_view.assert_has_calls([mocker.call(changed_id)])
            elif event_op == "remove":
                model._update_rendered_view.assert_not_called()

        for unchanged_id in set(indexed_ids) - set(event_message_ids):
            assert model.index["messages"][unchanged_id]["flags"] == flags_before

        if event_op == "add":
            set_count.assert_called_once_with(list(changed_ids), self.controller, -1)
        elif event_op == "remove":
            set_count.assert_not_called()

    @pytest.mark.parametrize(
        "pinned_streams, pin_to_top",
        [
            ([{"name": "all", "id": 2}], True),
            ([{"name": "design", "id": 1}, {"name": "all", "id": 2}], False),
            ([], True),
            ([{"name": "design", "id": 1}], False),
        ],
        ids=["pinning", "unpinning", "first_pinned", "last_unpinned"],
    )
    def test_toggle_stream_pinned_status(
        self, mocker, model, pinned_streams, pin_to_top, stream_id=1
    ):
        model.pinned_streams = deepcopy(pinned_streams)
        model.client.update_subscription_settings.return_value = {"result": "success"}

        model.toggle_stream_pinned_status(stream_id)

        request = [
            {"stream_id": stream_id, "property": "pin_to_top", "value": pin_to_top}
        ]
        model.client.update_subscription_settings.assert_called_once_with(request)

    @pytest.mark.parametrize(
        "initial_visual_notified_streams, expected_new_value",
        [
            ({315}, True),
            ({205, 315}, False),
            (set(), True),
            ({205}, False),
        ],
        ids=[
            "visual_notification_enable_205",
            "visual_notification_disable_205",
            "first_notification_enable_205",
            "last_notification_disable_205",
        ],
    )
    def test_toggle_stream_visual_notifications(
        self,
        model,
        initial_visual_notified_streams,
        expected_new_value,
        response={"result": "success"},
        stream_id=205,
    ):
        model.visual_notified_streams = initial_visual_notified_streams
        model.client.update_subscription_settings.return_value = response

        model.toggle_stream_visual_notifications(stream_id)

        request = [
            {
                "stream_id": stream_id,
                "property": "desktop_notifications",
                "value": expected_new_value,
            }
        ]
        model.client.update_subscription_settings.assert_called_once_with(request)
        self.display_error_if_present.assert_called_once_with(response, self.controller)

    @pytest.mark.parametrize(
        (
            "narrow, event, is_notification_in_progress,"
            "expected_active_conversation_info, expected_show_typing_notification,"
        ),
        [
            case(
                [["stream", "narrow"]],
                {
                    "op": "start",
                    "sender": {"user_id": 4, "email": "hamlet@zulip.com"},
                    "id": 0,
                },
                False,
                {},
                False,
                id="not_in_pm_narrow",
            ),
            case(
                [["pm-with", "othello@zulip.com"]],
                {
                    "op": "start",
                    "sender": {"user_id": 4, "email": "hamlet@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                False,
                {},
                False,
                id="not_in_pm_narrow_with_sender",
            ),
            case(
                [["pm-with", "hamlet@zulip.com"]],
                {
                    "op": "start",
                    "sender": {"user_id": 4, "email": "hamlet@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                False,
                {"sender_name": "hamlet"},
                True,
                id="in_pm_narrow_with_sender_typing:start",
            ),
            case(
                [["pm-with", "hamlet@zulip.com"]],
                {
                    "op": "start",
                    "sender": {"user_id": 4, "email": "hamlet@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                True,
                {"sender_name": "hamlet"},
                False,
                id="in_pm_narrow_with_sender_typing:start_while_animation_in_progress",
            ),
            case(
                [["pm-with", "hamlet@zulip.com"]],
                {
                    "op": "stop",
                    "sender": {"user_id": 4, "email": "hamlet@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                True,
                {},
                False,
                id="in_pm_narrow_with_sender_typing:stop",
            ),
            case(
                [["pm-with", "hamlet@zulip.com"]],
                {
                    "op": "start",
                    "sender": {"user_id": 5, "email": "iago@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                False,
                {},
                False,
                id="in_pm_narrow_with_other_myself_typing:start",
            ),
            case(
                [["pm-with", "hamlet@zulip.com"]],
                {
                    "op": "stop",
                    "sender": {"user_id": 5, "email": "iago@zulip.com"},
                    "recipients": [
                        {"user_id": 4, "email": "hamlet@zulip.com"},
                        {"user_id": 5, "email": "iago@zulip.com"},
                    ],
                    "id": 0,
                },
                False,
                {},
                False,
                id="in_pm_narrow_with_other_myself_typing:stop",
            ),
            case(
                [["pm-with", "iago@zulip.com"]],
                {
                    "op": "start",
                    "sender": {"user_id": 5, "email": "iago@zulip.com"},
                    "recipients": [{"user_id": 5, "email": "iago@zulip.com"}],
                    "id": 0,
                },
                False,
                {},
                False,
                id="in_pm_narrow_with_oneself:start",
            ),
            case(
                [["pm-with", "iago@zulip.com"]],
                {
                    "op": "stop",
                    "sender": {"user_id": 5, "email": "iago@zulip.com"},
                    "recipients": [{"user_id": 5, "email": "iago@zulip.com"}],
                    "id": 0,
                },
                False,
                {},
                False,
                id="in_pm_narrow_with_oneself:stop",
            ),
        ],
    )
    def test__handle_typing_event(
        self,
        mocker,
        model,
        narrow,
        event,
        is_notification_in_progress,
        expected_active_conversation_info,
        expected_show_typing_notification,
    ):
        event["type"] = "typing"

        model.narrow = narrow
        model.user_dict = {"hamlet@zulip.com": {"full_name": "hamlet"}}
        model.user_id = 5  # Iago's user_id
        model.controller.active_conversation_info = {}
        model.controller.is_typing_notification_in_progress = (
            is_notification_in_progress
        )
        show_typing_notification = mocker.patch(
            CONTROLLER + ".show_typing_notification"
        )

        model._handle_typing_event(event)

        if expected_active_conversation_info:
            assert (
                model.controller.active_conversation_info["sender_name"]
                == expected_active_conversation_info["sender_name"]
            )
        assert show_typing_notification.called == expected_show_typing_notification

    @pytest.mark.parametrize(
        "event, final_muted_streams, ",
        [
            (
                {
                    "property": "in_home_view",
                    "op": "update",
                    "stream_id": 18,
                    "value": True,
                },
                {15, 19},
            ),
            (
                {
                    "property": "in_home_view",
                    "op": "update",
                    "stream_id": 19,
                    "value": True,
                },
                {15},
            ),
            (
                {
                    "property": "in_home_view",
                    "op": "update",
                    "stream_id": 19,
                    "value": False,
                },
                {15, 19},
            ),
            (
                {
                    "property": "in_home_view",
                    "op": "update",
                    "stream_id": 30,
                    "value": False,
                },
                {15, 19, 30},
            ),
            (
                {
                    "property": "is_muted",
                    "op": "update",
                    "stream_id": 30,
                    "value": False,
                },
                {15, 19},
            ),
            (
                {
                    "property": "is_muted",
                    "op": "update",
                    "stream_id": 19,
                    "value": False,
                },
                {15},
            ),
            (
                {
                    "property": "is_muted",
                    "op": "update",
                    "stream_id": 15,
                    "value": True,
                },
                {15, 19},
            ),
            (
                {
                    "property": "is_muted",
                    "op": "update",
                    "stream_id": 30,
                    "value": True,
                },
                {15, 19, 30},
            ),
        ],
        ids=[
            "remove_18_in_home_view:already_unmuted:ZFLNone",
            "remove_19_in_home_view:muted:ZFLNone",
            "add_19_in_home_view:already_muted:ZFLNone",
            "add_30_in_home_view:unmuted:ZFLNone",
            "remove_30_is_muted:already_unmutedZFL139",
            "remove_19_is_muted:muted:ZFL139",
            "add_15_is_muted:already_muted:ZFL139",
            "add_30_is_muted:unmuted:ZFL139",
        ],
    )
    def test__handle_subscription_event_mute_streams(
        self, model, mocker, stream_button, event, final_muted_streams
    ):
        event["type"] = "subscription"

        model.muted_streams = {15, 19}
        model.unread_counts = {"all_msg": 300, "streams": {event["stream_id"]: 99}}
        model.controller.view.stream_id_to_button = {
            event["stream_id"]: stream_button  # stream id is known
        }
        mark_muted = mocker.patch(
            "zulipterminal.ui_tools.buttons.StreamButton.mark_muted"
        )
        mark_unmuted = mocker.patch(
            "zulipterminal.ui_tools.buttons.StreamButton.mark_unmuted"
        )

        model._handle_subscription_event(event)

        assert model.muted_streams == final_muted_streams

        if model.muted_streams != {15, 19}:
            # This condition is to check if the stream is unmuted or not
            if (event["value"] and event["property"] == "in_home_view") or (
                not event["value"] and event["property"] == "is_muted"
            ):
                mark_unmuted.assert_called_once_with(99)
                assert model.unread_counts["all_msg"] == 399
            else:
                mark_muted.assert_called_once_with()
                assert model.unread_counts["all_msg"] == 201
            model.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize(
        "event, expected_pinned_streams, expected_unpinned_streams",
        [
            (
                {
                    "property": "pin_to_top",
                    "op": "update",
                    "stream_id": 6,
                    "value": True,
                },
                [{"name": "design", "id": 8}, {"name": "all", "id": 6}],
                [],
            ),
            (
                {
                    "property": "pin_to_top",
                    "op": "update",
                    "stream_id": 8,
                    "value": False,
                },
                [],
                [{"name": "design", "id": 8}, {"name": "all", "id": 6}],
            ),
        ],
        ids=[
            "pin_stream",
            "unpin_stream",
        ],
    )
    def test__handle_subscription_event_pin_streams(
        self,
        model,
        mocker,
        stream_button,
        event,
        expected_pinned_streams,
        expected_unpinned_streams,
        initial_pinned_streams=[{"name": "design", "id": 8}],
        initial_unpinned_streams=[{"name": "all", "id": 6}],
    ):
        def set_from_list_of_dict(data):
            return {tuple(sorted(d.items())) for d in data}

        event["type"] = "subscription"

        model.controller.view.stream_id_to_button = {event["stream_id"]: stream_button}
        model.pinned_streams = deepcopy(initial_pinned_streams)
        model.unpinned_streams = deepcopy(initial_unpinned_streams)

        model._handle_subscription_event(event)

        assert set_from_list_of_dict(model.pinned_streams) == set_from_list_of_dict(
            expected_pinned_streams
        )
        assert set_from_list_of_dict(model.unpinned_streams) == set_from_list_of_dict(
            expected_unpinned_streams
        )
        update_left_panel = model.controller.view.left_panel.update_stream_view
        update_left_panel.assert_called_once_with()
        model.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize(
        "initial_visual_notified_streams, event, final_visual_notified_streams",
        [
            case(
                {15, 19},
                {
                    "property": "desktop_notifications",
                    "op": "update",
                    "stream_id": 15,
                    "value": False,
                },
                {19},
                id="remove_visual_notified_stream_15:present",
            ),
            case(
                {15, 30},
                {
                    "property": "desktop_notifications",
                    "op": "update",
                    "stream_id": 19,
                    "value": True,
                },
                {15, 19, 30},
                id="add_visual_notified_stream_19:not_present",
            ),
            case(
                {19},
                {
                    "property": "desktop_notifications",
                    "op": "update",
                    "stream_id": 15,
                    "value": False,
                },
                {19},
                id="remove_visual_notified_stream_15:not_present",
            ),
            case(
                {15, 19, 30},
                {
                    "property": "desktop_notifications",
                    "op": "update",
                    "stream_id": 19,
                    "value": True,
                },
                {15, 19, 30},
                id="add_visual_notified_stream_19:present",
            ),
        ],
    )
    def test__handle_subscription_event_visual_notifications(
        self,
        model,
        initial_visual_notified_streams,
        event,
        final_visual_notified_streams,
    ):
        event["type"] = "subscription"
        model.visual_notified_streams = initial_visual_notified_streams

        model._handle_subscription_event(event)

        assert model.visual_notified_streams == final_visual_notified_streams

    @pytest.mark.parametrize(
        "event, feature_level, stream_id, expected_subscribers",
        [
            (
                {"op": "peer_add", "stream_id": 99, "user_id": 12},
                None,
                99,
                [1001, 11, 12],
            ),
            (
                {"op": "peer_add", "stream_id": 99, "user_id": 12},
                34,
                99,
                [1001, 11, 12],
            ),
            (
                {"op": "peer_add", "stream_ids": [99], "user_ids": [12]},
                34,
                99,
                [1001, 11, 12],
            ),
            (
                {"op": "peer_add", "stream_ids": [99], "user_ids": [12]},
                35,
                99,
                [1001, 11, 12],
            ),
            ({"op": "peer_remove", "stream_id": 2, "user_id": 12}, None, 2, [1001, 11]),
            ({"op": "peer_remove", "stream_id": 2, "user_id": 12}, 34, 2, [1001, 11]),
            (
                {"op": "peer_remove", "stream_ids": [2], "user_ids": [12]},
                34,
                2,
                [1001, 11],
            ),
            (
                {"op": "peer_remove", "stream_ids": [2], "user_ids": [12]},
                35,
                2,
                [1001, 11],
            ),
        ],
        ids=[
            "user_subscribed_to_stream:ZFLNone",
            "user_subscribed_to_stream:ZFL34",
            "user_subscribed_to_stream:ZFL34_should_be_35",
            "user_subscribed_to_stream:ZFL35",
            "user_unsubscribed_from_stream:ZFLNone",
            "user_unsubscribed_from_stream:ZFL34",
            "user_unsubscribed_from_stream:ZFL34_should_be_35",
            "user_unsubscribed_from_stream:ZFL35",
        ],
    )
    def test__handle_subscription_event_subscribers(
        self,
        model,
        mocker,
        stream_dict,
        event,
        feature_level,
        stream_id,
        expected_subscribers,
    ):
        event["type"] = "subscription"

        model.stream_dict = stream_dict
        model.server_feature_level = feature_level

        model._handle_subscription_event(event)

        new_subscribers = model.stream_dict[stream_id]["subscribers"]
        assert new_subscribers == expected_subscribers

    @pytest.mark.parametrize(
        "event, feature_level",
        [
            ({"op": "peer_add", "stream_id": 462, "user_id": 12}, 34),
            ({"op": "peer_add", "stream_ids": [462], "user_ids": [12]}, 35),
            ({"op": "peer_remove", "stream_id": 462, "user_id": 12}, 34),
            ({"op": "peer_remove", "stream_ids": [462], "user_ids": [12]}, 35),
        ],
        ids=[
            "peer_subscribed_to_stream_that_user_is_unsubscribed_to",
            "peer_subscribed_to_stream_that_user_is_unsubscribed_to:ZFL35+",
            "peer_unsubscribed_from_stream_that_user_is_unsubscribed_to",
            "peer_unsubscribed_from_stream_that_user_is_unsubscribed_to:ZFL35+",
        ],
    )
    def test__handle_subscription_event_subscribers_to_unsubscribed_streams(
        self, model, mocker, stream_dict, event, feature_level
    ):
        event["type"] = "subscription"

        model.stream_dict = deepcopy(stream_dict)
        model.server_feature_level = feature_level

        model._handle_subscription_event(event)

        assert model.stream_dict == stream_dict

    # NOTE: This only applies to feature level 34/35+
    @pytest.mark.parametrize(
        "event, feature_level, expected_subscribers",
        [
            ({"op": "peer_add", "user_ids": [13, 14]}, 34, [1001, 11, 12, 13, 14]),
            ({"op": "peer_add", "user_ids": [13, 14]}, 35, [1001, 11, 12, 13, 14]),
            ({"op": "peer_remove", "user_ids": [12, 11]}, 34, [1001]),
            ({"op": "peer_remove", "user_ids": [12, 11]}, 35, [1001]),
        ],
        ids=[
            "users_subscribed_to_stream:ZFL34_should_be_35",
            "users_subscribed_to_stream:ZFL35",
            "users_unsubscribed_from_stream:ZFL34_should_be_35",
            "users_unsubscribed_from_stream:ZFL35",
        ],
    )
    def test__handle_subscription_event_subscribers_multiple_users_one_stream(
        self, model, mocker, stream_dict, event, feature_level, expected_subscribers
    ):
        event["type"] = "subscription"
        event["stream_ids"] = stream_ids = [2]

        model.stream_dict = stream_dict
        model.server_feature_level = feature_level

        model._handle_subscription_event(event)

        new_subscribers = model.stream_dict[stream_ids[0]]["subscribers"]
        assert new_subscribers == expected_subscribers

    # NOTE: This only applies to feature level 34/35+
    @pytest.mark.parametrize(
        "event, feature_level, expected_subscribers",
        [
            ({"op": "peer_add", "user_ids": [13]}, 34, [1001, 11, 12, 13]),
            ({"op": "peer_add", "user_ids": [13]}, 35, [1001, 11, 12, 13]),
            ({"op": "peer_remove", "user_ids": [12]}, 34, [1001, 11]),
            ({"op": "peer_remove", "user_ids": [12]}, 35, [1001, 11]),
        ],
        ids=[
            "user_subscribed_to_streams:ZFL34_should_be_35",
            "user_subscribed_to_streams:ZFL35",
            "user_unsubscribed_from_streams:ZFL34_should_be_35",
            "user_unsubscribed_from_streams:ZFL35",
        ],
    )
    def test__handle_subscription_event_subscribers_one_user_multiple_streams(
        self, model, mocker, stream_dict, event, feature_level, expected_subscribers
    ):
        event["type"] = "subscription"
        event["stream_ids"] = stream_ids = [1, 2]

        model.stream_dict = stream_dict
        model.server_feature_level = feature_level

        model._handle_subscription_event(event)

        for stream_id in stream_ids:
            new_subscribers = model.stream_dict[stream_id]["subscribers"]
            assert new_subscribers == expected_subscribers

    @pytest.mark.parametrize(
        "person, event_field, updated_field_if_different",
        [
            (
                {"full_name": "New Full Name"},
                "full_name",
                None,
            ),
            ({"timezone": "New Timezone"}, "timezone", None),
            ({"is_billing_admin": False}, "is_billing_admin", None),
            ({"role": 10}, "role", None),
            (
                {"avatar_url": "new_avatar_url", "avatar_version": 21},
                "avatar_url",
                None,
            ),
            ({"new_email": "new_display@email.com"}, "new_email", "email"),
            (
                {"delivery_email": "new_delivery@email.com"},
                "delivery_email",
                None,
            ),
        ],
        ids=[
            "full_name",
            "timezone",
            "billing_admin_role",
            "role",
            "avatar",
            "display_email",
            "delivery_email",
        ],
    )
    def test__handle_realm_user_event(
        self, person, event_field, updated_field_if_different, model, initial_data
    ):
        # id 11 matches initial_data["realm_users"][1] in the initial_data fixture
        person["user_id"] = 11
        event = {"type": "realm_user", "op": "update", "id": 1000, "person": person}

        model._handle_realm_user_event(event)

        if updated_field_if_different is not None:
            new_data_field = updated_field_if_different
        else:
            new_data_field = event_field
        assert (
            initial_data["realm_users"][1][new_data_field]
            == event["person"][event_field]
        )

    @pytest.mark.parametrize("value", [True, False])
    def test__handle_user_settings_event(self, mocker, model, value):
        setting = "send_private_typing_notifications"
        event = {
            "type": "user_settings",
            "op": "update",
            "property": setting,
            "value": value,
        }
        model._handle_user_settings_event(event)
        assert model.user_settings()[setting] == value

    @pytest.mark.parametrize("setting", [True, False])
    def test_update_pm_content_in_desktop_notifications(self, mocker, model, setting):
        setting_name = "pm_content_in_desktop_notifications"
        event = {
            "type": "update_global_notifications",
            "notification_name": setting_name,
            "setting": setting,
        }
        model._user_settings[setting_name] = not setting

        model._handle_update_global_notifications_event(event)

        assert model.user_settings()[setting_name] == setting

    @pytest.mark.parametrize("setting", [True, False])
    def test_update_twenty_four_hour_format(self, mocker, model, setting):
        event = {
            "type": "update_display_settings",
            "setting_name": "twenty_four_hour_time",
            "setting": setting,
        }
        first_msg_w = mocker.Mock()
        second_msg_w = mocker.Mock()
        first_msg_w.original_widget.message = {"id": 1}
        second_msg_w.original_widget.message = {"id": 2}
        self.controller.view.message_view = mocker.Mock(log=[first_msg_w, second_msg_w])
        create_msg_box_list = mocker.patch(MODULE + ".create_msg_box_list")
        model._user_settings["twenty_four_hour_format"] = not setting

        model._handle_update_display_settings_event(event)

        assert model.user_settings()["twenty_four_hour_time"] == event["setting"]
        assert create_msg_box_list.call_count == len(
            self.controller.view.message_view.log
        )
        assert model.controller.update_screen.called

    @pytest.mark.parametrize(
        "muted_streams, stream_id, is_muted",
        [
            ({1}, 1, True),
            ({1}, 2, False),
            (set(), 1, False),
        ],
        ids=["muted_stream", "unmuted_stream", "unmuted_stream_nostreamsmuted"],
    )
    def test_is_muted_stream(
        self, muted_streams, stream_id, is_muted, stream_dict, model
    ):
        model.stream_dict = stream_dict
        model.muted_streams = muted_streams
        assert model.is_muted_stream(stream_id) == is_muted

    @pytest.mark.parametrize(
        "visual_notified_streams, stream_id, is_enabled",
        [
            ({1}, 1, True),
            ({1, 3, 7}, 2, False),
            (set(), 1, False),
        ],
        ids=[
            "notifications_enabled",
            "notifications_disabled",
            "notifications_disabled_no_streams_to_notify",
        ],
    )
    def test_is_visual_notifications_enabled(
        self, visual_notified_streams, stream_id, is_enabled, stream_dict, model
    ):
        model.stream_dict = stream_dict
        model.visual_notified_streams = visual_notified_streams

        assert model.is_visual_notifications_enabled(stream_id) == is_enabled

    @pytest.mark.parametrize(
        "topic, is_muted",
        [
            ((1, "stream muted & unmuted topic"), False),
            ((2, "muted topic"), True),
            ((1, "muted stream muted topic"), True),
            ((2, "unmuted topic"), False),
        ],
    )
    def test_is_muted_topic(
        self, topic, is_muted, stream_dict, model, processed_muted_topics
    ):
        model.stream_dict = stream_dict
        model._muted_topics = processed_muted_topics

        return_value = model.is_muted_topic(stream_id=topic[0], topic=topic[1])

        assert return_value == is_muted

    @pytest.mark.parametrize(
        "unread_topics, last_unread_topic, next_unread_topic",
        [
            case(
                {(1, "topic"), (2, "topic2")},
                None,
                (1, "topic"),
                id="unread_present_after_no_state",
            ),
            case(
                {(1, "topic"), (2, "topic2")},
                (1, "topic"),
                (2, "topic2"),
                id="unread_present_after_previous_topic",
            ),
            case(
                {(1, "topic"), (2, "topic2")},
                (2, "topic2"),
                (1, "topic"),
                id="unread_present_before_previous_topic",
            ),
            case(  # TODO Should be None? (2 other cases)
                {(1, "topic")},
                (1, "topic"),
                (1, "topic"),
                id="unread_still_present_in_topic",
            ),
            case(
                {},
                (1, "topic"),
                None,
                id="no_unreads_with_previous_topic_state",
            ),
            case({}, None, None, id="no_unreads_with_no_previous_topic_state"),
            case(
                {(1, "topic"), (2, "topic2"), (3, "topic3")},
                (2, "topic2"),
                (1, "topic"),
                id="unread_present_before_previous_topic_skipping_muted_stream",
            ),
            case(
                {(1, "topic"), (2, "topic2"), (3, "topic3"), (4, "topic4")},
                (2, "topic2"),
                (4, "topic4"),
                id="unread_present_after_previous_topic_skipping_muted_stream",
            ),
            case(
                {(3, "topic3")},
                (2, "topic2"),
                None,
                id="unread_present_only_in_muted_stream",
            ),
            case(
                {(3, "topic3")},
                (3, "topic3"),
                None,
                id="unread_present_starting_in_muted_stream",  # TODO See other 2 cases
            ),
            case(
                {(3, "topic3"), (4, "topic4")},
                None,
                (4, "topic4"),
                id="unread_present_skipping_first_muted_stream_unread",
            ),
            case(
                {(2, "topic2 muted")},
                None,
                None,
                id="unread_present_only_in_muted_topic",
            ),
            case(
                {(2, "topic2 muted")},
                (2, "topic2 muted"),
                None,
                id="unread_present_starting_in_muted_topic",  # TODO See other 2 cases
            ),
            case(
                {(3, "topic3 muted")},
                None,
                None,
                id="unread_present_only_in_muted_topic_in_muted_stream",
            ),
            case(
                {(2, "topic2"), (2, "topic2 muted"), (4, "topic4")},
                (2, "topic2"),
                (4, "topic4"),
                id="unread_present_after_previous_topic_skipping_muted_topic",
            ),
            case(
                {(2, "topic2"), (2, "muted topic2")},
                (2, "muted topic2"),
                (2, "topic2"),
                id="unread_present_after_previous_topic_muted",
            ),
        ],
    )
    def test_get_next_unread_topic(
        self, model, unread_topics, last_unread_topic, next_unread_topic
    ):
        # NOTE Not important how many unreads per topic, so just use '1'
        model.unread_counts = {
            "unread_topics": {stream_topic: 1 for stream_topic in unread_topics}
        }
        model._last_unread_topic = last_unread_topic

        # Minimal extra streams for muted stream testing (should not exist otherwise)
        assert {3, 4} & set(model.stream_dict) == set()
        model.stream_dict[3] = {"name": "Stream 3"}
        model.stream_dict[4] = {"name": "Stream 4"}
        model.muted_streams = {3}

        # date data unimportant (if present)
        model._muted_topics = {
            stream_topic: None
            for stream_topic in [
                ("Stream 2", "muted topic2"),
                ("Stream 2", "topic2 muted"),
                ("Stream 3", "topic3 muted"),
            ]
        }

        unread_topic = model.get_next_unread_topic()

        assert unread_topic == next_unread_topic

    @pytest.mark.parametrize(
        "stream_id, expected_response",
        [
            (1, True),
            (462, False),
        ],
        ids=[
            "subscribed_stream",
            "unsubscribed_stream",
        ],
    )
    def test_is_user_subscribed_to_stream(
        self, model, stream_dict, stream_id, expected_response
    ):
        model.stream_dict = stream_dict

        return_value = model.is_user_subscribed_to_stream(stream_id)

        assert return_value == expected_response

    @pytest.mark.parametrize(
        "response",
        [
            {
                "result": "success",
                "msg": "",
            }
        ],
    )
    def test_fetch_message_history_success(
        self, mocker, model, message_history, response, message_id=1
    ):
        response["message_history"] = message_history
        expected_return_value = message_history
        self.client.get_message_history.return_value = response

        return_value = model.fetch_message_history(message_id)

        self.client.get_message_history.assert_called_once_with(message_id)
        assert not self.display_error_if_present.called
        assert return_value == expected_return_value

    @pytest.mark.parametrize(
        "response",
        [
            {
                "result": "error",
                "msg": "Invalid message(s)",
            }
        ],
    )
    def test_fetch_message_history_error(
        self, mocker, model, response, message_id=1, expected_return_value=list()
    ):
        self.client.get_message_history.return_value = response

        return_value = model.fetch_message_history(message_id)

        self.client.get_message_history.assert_called_once_with(message_id)
        assert self.display_error_if_present.called
        assert return_value == expected_return_value

    @pytest.mark.parametrize("user_id, full_name", [(1001, "Human Myself")])
    def test_user_name_from_id_valid(self, model, user_dict, user_id, full_name):
        model.user_id_email_dict = {1001: "FOOBOO@gmail.com"}
        model.user_dict = user_dict

        return_value = model.user_name_from_id(user_id)

        assert return_value == full_name

    @pytest.mark.parametrize("user_id", [-1])
    def test_user_name_from_id_invalid(self, model, user_id):
        model.user_id_email_dict = {1001: "FOOBOO@gmail.com"}

        with pytest.raises(RuntimeError, match="Invalid user ID."):
            model.user_name_from_id(user_id)

    def test_generate_all_emoji_data(
        self,
        mocker,
        model,
        zulip_emoji,
        unicode_emojis,
        realm_emojis_data,
        realm_emojis,
    ):
        all_emoji_data, all_emoji_names = model.generate_all_emoji_data(realm_emojis)

        assert all_emoji_data == OrderedDict(
            sorted(
                {**unicode_emojis, **realm_emojis_data, **zulip_emoji}.items(),
                key=lambda e: e[0],
            )
        )
        assert model.all_emoji_names == sorted(
            [
                name
                for emoji in {
                    **unicode_emojis,
                    **realm_emojis_data,
                    **zulip_emoji,
                }.items()
                for name in [emoji[0], *emoji[1]["aliases"]]
            ]
        )
        # custom emoji added to active_emoji_data
        assert all_emoji_data["singing"]["type"] == "realm_emoji"
        # Deactivated custom emoji is removed from active emojis set
        assert "green_tick" not in all_emoji_data
        # deactivated custom emoji which replaced unicode emoji with same name
        assert all_emoji_data["joy_cat"]["type"] == "unicode_emoji"
        # Custom emoji replaces unicode emoji with same name.
        assert all_emoji_data["joker"]["type"] == "realm_emoji"
        # zulip_extra_emoji replaces all other emoji types for 'zulip' emoji.
        assert all_emoji_data["zulip"]["type"] == "zulip_extra_emoji"

    @pytest.mark.parametrize(
        "to_vary_in_realm_emoji, expected_emoji_type, emoji_should_be_active",
        [
            (
                {"deactivated": False, "id": "20", "name": "joy_cat"},
                "realm_emoji",
                True,
            ),
            (
                {"deactivated": True, "id": "202020", "name": "joker"},
                "unicode_emoji",
                True,
            ),
            (
                {"deactivated": False, "id": "22", "name": "zulip"},
                "zulip_extra_emoji",
                True,
            ),
            (
                {"deactivated": True, "id": "4", "name": "zulip"},
                "zulip_extra_emoji",
                True,
            ),
            (
                {"deactivated": False, "id": "23", "name": "new_emoji"},
                "realm_emoji",
                True,
            ),
            ({"deactivated": True, "id": "3", "name": "singing"}, "", False),
        ],
        ids=[
            "realm_emoji_with_same_name_as_unicode_emoji_added",
            "realm_emoji_with_same_name_as_unicode_emoji_removed",
            "realm_emoji_with_name_as_zulip_added",
            "realm_emoji_with_name_as_zulip_removed",
            "realm_emoji_added",
            "realm_emoji_removed",
        ],
    )
    def test__handle_update_emoji_event(
        self,
        mocker,
        model,
        realm_emojis,
        emoji_should_be_active,
        expected_emoji_type,
        to_vary_in_realm_emoji,
    ):
        emoji_name = to_vary_in_realm_emoji["name"]
        realm_emojis[to_vary_in_realm_emoji["id"]] = to_vary_in_realm_emoji
        event = {"type": "realm_emoji", "realm_emoji": realm_emojis}

        model._handle_update_emoji_event(event)

        if emoji_should_be_active:
            assert emoji_name in model.active_emoji_data
            assert model.active_emoji_data[emoji_name]["type"] == expected_emoji_type
        else:
            assert emoji_name not in model.active_emoji_data

    # Use LoopEnder with raising_event to cause the event loop to end without
    # processing the event
    class LoopEnder(Exception):
        pass

    @pytest.fixture
    def raising_event(self, mocker):
        def raiser(*args):
            raise TestModel.LoopEnder

        return mocker.MagicMock(__getitem__=raiser)

    def test_poll_for_events__no_disconnect(self, mocker, model, raising_event):
        mocker.patch(MODEL + "._register_desired_events")
        sleep = mocker.patch(MODULE + ".time.sleep")

        self.client.get_events.side_effect = [
            {
                "events": [raising_event],
                "result": "success",
            }
        ]

        with pytest.raises(self.LoopEnder):
            model.poll_for_events()

        assert not model._register_desired_events.called
        assert self.client.get_events.called
        assert not sleep.called

    @pytest.mark.parametrize(
        "register_return_value",
        [
            pytest.param([""], id="reconnect_on_1st_attempt"),
            pytest.param(["error", ""], id="reconnect_on_2nd_attempt"),
            pytest.param(["error", "error", ""], id="reconnect_on_3rd_attempt"),
        ],
    )
    def test_poll_for_events__reconnect_ok(
        self, mocker, model, raising_event, register_return_value
    ):
        mocker.patch(
            MODEL + "._register_desired_events", side_effect=register_return_value
        )
        sleep = mocker.patch(MODULE + ".time.sleep")

        self.client.get_events.side_effect = [
            {
                "events": [raising_event],
                "result": "success",
            }
        ]

        model.queue_id = None  # Initial trigger for reconnecting

        with pytest.raises(self.LoopEnder):
            model.poll_for_events()

        registers = [mocker.call() for _ in range(len(register_return_value))]
        model._register_desired_events.assert_has_calls(registers)
        assert self.client.get_events.called
        assert sleep.call_count == len(registers) - 1
