from collections import OrderedDict, defaultdict
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import pytest
from pytest_mock import MockerFixture
from urwid import Widget

from zulipterminal.api_types import (
    CustomFieldValue,
    CustomProfileField,
    Message,
    MessageType,
)
from zulipterminal.config.keys import (
    ZT_TO_URWID_CMD_MAPPING,
    keys_for_command,
    primary_key_for_command,
)
from zulipterminal.helper import CustomProfileData, Index, TidiedUserInfo
from zulipterminal.helper import initial_index as helper_initial_index
from zulipterminal.ui_tools.buttons import StreamButton, TopicButton, UserButton
from zulipterminal.ui_tools.messages import MessageBox
from zulipterminal.urwid_types import urwid_Size
from zulipterminal.version import (
    MINIMUM_SUPPORTED_SERVER_VERSION,
    SUPPORTED_SERVER_VERSIONS,
)


# --------------- Autouse Fixtures -----------------------------------------


@pytest.fixture(autouse=True)
def no_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Forces all the tests to work offline.
    """
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(autouse=True)
def no_asynch(mocker: MockerFixture) -> None:
    """
    Make all function calls synchronous.
    """
    mocker.patch("zulipterminal.helper.asynch")


# --------------- Controller Fixtures -----------------------------------------


@pytest.fixture
def stream_button(mocker: MockerFixture) -> StreamButton:
    """
    Mocked stream button.
    """
    view_mock = mocker.Mock()
    view_mock.palette = [(None, "black", "white")]
    button = StreamButton(
        properties={
            "name": "PTEST",
            "id": 205,
            "color": "#bfd56f",
            "stream_access_type": "public",
            "description": "Test stream description",
        },
        controller=mocker.patch("zulipterminal.core.Controller"),
        view=view_mock,
        count=30,
    )
    return button


@pytest.fixture
def topic_button(mocker: MockerFixture) -> TopicButton:
    """
    Mocked topic button.
    """
    view_mock = mocker.Mock()
    view_mock.palette = [(None, "black", "white")]
    button = TopicButton(
        stream_id=100,
        topic="PTEST",
        controller=mocker.patch("zulipterminal.core.Controller"),
        view=view_mock,
        count=30,
    )
    return button


@pytest.fixture
def user_button(mocker: MockerFixture) -> UserButton:
    """
    Mocked User Button.
    """
    return UserButton(
        user={
            "user_id": 5179,
            "full_name": "Boo Boo",
            "email": "boo@zulip.com",
        },
        controller=mocker.patch("zulipterminal.core.Controller"),
        view=mocker.patch("zulipterminal.ui.View"),
        state_marker="*",
        count=0,
    )


@pytest.fixture
def msg_box(
    mocker: MockerFixture, messages_successful_response: Dict[str, Any]
) -> MessageBox:
    """
    Mocked MessageBox with stream message
    """
    return MessageBox(
        messages_successful_response["messages"][0],
        mocker.patch("zulipterminal.model.Model"),
        None,
    )


# --------------- Model Fixtures ----------------------------------------------


@pytest.fixture
def users_fixture(
    logged_on_user: Dict[str, Any],
    custom_profile_data_fixture: Dict[str, CustomFieldValue],
) -> List[Dict[str, Any]]:
    users = [logged_on_user]
    for i in range(1, 3):
        users.append(
            {
                "user_id": 10 + i,
                "full_name": f"Human {i}",
                "email": f"person{i}@example.com",
                "avatar_url": None,
                "is_active": True,
                "bot_type": None,
                "is_bot": False,
                "is_admin": False,
            }
        )
    # Also add two users with the same name.
    for i in range(1, 3):
        users.append(
            {
                "user_id": 12 + i,
                "full_name": "Human Duplicate",
                "email": f"personduplicate{i}@example.com",
                "avatar_url": None,
                "is_active": True,
                "bot_type": None,
                "is_bot": False,
                "is_admin": False,
            }
        )
    # Add custom profile data to user 12
    for user in users:
        if user["user_id"] == 12:
            user["profile_data"] = custom_profile_data_fixture
        else:
            user["profile_data"] = {}
    return users


@pytest.fixture
def tidied_user_info_response(
    clean_custom_profile_data_fixture: List[CustomProfileData],
) -> TidiedUserInfo:
    # FIXME: Refactor this to use a more generic user?
    return {
        "full_name": "Human 2",
        "email": "person2@example.com",
        "date_joined": "",
        "timezone": "",
        "is_bot": False,
        "role": 400,
        "bot_type": None,
        "bot_owner_name": "",
        "last_active": "",
        "custom_profile_data": clean_custom_profile_data_fixture,
    }


@pytest.fixture
def _all_users_by_id(initial_data: Dict[str, Any]) -> Dict[int, Any]:
    return {
        user["user_id"]: user
        for user in (initial_data["realm_users"] + initial_data["cross_realm_bots"])
    }


@pytest.fixture
def _cross_realm_bots_by_id(initial_data: Dict[str, Any]) -> Dict[int, Any]:
    return {user["user_id"]: user for user in initial_data["cross_realm_bots"]}


@pytest.fixture
def user_groups_fixture() -> List[Dict[str, Any]]:
    user_groups = []
    members = [[1001, 11], [11, 12], [12], []]
    for i in range(1, 5):
        user_groups.append(
            {
                "id": 10 + i,
                "name": f"Group {i}",
                "description": f"Core developers of Group {i}",
                "members": members[i - 1],
            }
        )
    return user_groups


@pytest.fixture
def logged_on_user() -> Dict[str, Any]:
    return {
        "user_id": 1001,
        "full_name": "Human Myself",
        "email": "FOOBOO@gmail.com",
    }


@pytest.fixture
def general_stream() -> Dict[str, Any]:
    return {
        "name": "Some general stream",
        "date_created": 1472091253,
        "invite_only": False,
        "color": "#b0a5fd",  # Color in '#xxxxxx' format
        "pin_to_top": False,
        "stream_id": 1000,
        "is_muted": False,
        "audible_notifications": False,
        "description": "General Stream",
        "rendered_description": "General Stream",
        "is_old_stream": True,
        "desktop_notifications": False,
        "stream_weekly_traffic": 0,
        "push_notifications": False,
        "email_address": "general@example.comm",
        "message_retention_days": 10,
        "subscribers": [1001, 11, 12],
        "history_public_to_subscribers": True,
    }


# This is a private stream;
# only description/stream_id/invite_only/name/color vary from above
@pytest.fixture
def secret_stream() -> Dict[str, Any]:
    return {
        "description": "Some private stream",
        "stream_id": 99,
        "pin_to_top": False,
        "invite_only": True,
        "name": "Secret stream",
        "date_created": 1472047124,
        "email_address": "secret@example.com",
        "rendered_description": "Some private stream",
        "color": "#ccc",  # Color in '#xxx' format
        "is_muted": False,
        "audible_notifications": False,
        "is_old_stream": True,
        "desktop_notifications": False,
        "stream_weekly_traffic": 0,
        "message_retention_days": -1,
        "push_notifications": False,
        "subscribers": [1001, 11],
        "history_public_to_subscribers": False,
    }


# Like public stream but with is_web_public=True
@pytest.fixture
def web_public_stream() -> Dict[str, Any]:
    return {
        "description": "Some web public stream",
        "stream_id": 999,
        "pin_to_top": False,
        "invite_only": False,
        "name": "Web public stream",
        "date_created": 1472047124,
        "email_address": "web_public@example.com",
        "rendered_description": "Some web public stream",
        "color": "#ddd",  # Color in '#xxx' format
        "is_muted": False,
        "audible_notifications": False,
        "is_old_stream": True,
        "desktop_notifications": False,
        "stream_weekly_traffic": 0,
        "message_retention_days": -1,
        "push_notifications": False,
        "subscribers": [1001, 11],
        "history_public_to_subscribers": False,
        "is_web_public": True,
    }


@pytest.fixture
def streams_fixture(
    general_stream: Dict[str, Any],
    secret_stream: Dict[str, Any],
    web_public_stream: Dict[str, Any],
) -> List[Dict[str, Any]]:
    streams = [general_stream, secret_stream, web_public_stream]
    for i in range(1, 3):
        streams.append(
            {
                "name": f"Stream {i}",
                "date_created": 1472047124 + i,
                "invite_only": False,
                "color": "#b0a5fd",
                "pin_to_top": False,
                "stream_id": i,
                "is_muted": False,
                "audible_notifications": False,
                "description": f"A description of stream {i}",
                "rendered_description": f"A description of stream {i}",
                "is_old_stream": True,
                "desktop_notifications": False,
                "stream_weekly_traffic": 0,
                "push_notifications": False,
                "message_retention_days": i + 30,
                "email_address": f"stream{i}@example.com",
                "subscribers": [1001, 11, 12],
                "history_public_to_subscribers": True,
            }
        )
    return deepcopy(streams)


@pytest.fixture
def realm_emojis() -> Dict[str, Dict[str, Any]]:
    # Omitting source_url, author_id (server version 3.0),
    # author (server version < 3.0) since they are not used.
    return {
        "1": {
            "deactivated": True,
            "id": "1",
            "name": "green_tick",
        },
        "202020": {
            "deactivated": False,
            "id": "202020",
            "name": "joker",
        },
        "2": {
            "deactivated": True,
            "id": "2",
            "name": "joy_cat",
        },
        "3": {
            "deactivated": False,
            "id": "3",
            "name": "singing",
        },
        "4": {
            "deactivated": False,
            "id": "4",
            "name": "zulip",
        },
    }


@pytest.fixture
def realm_emojis_data() -> "OrderedDict[str, Dict[str, Any]]":
    return OrderedDict(
        [
            ("joker", {"code": "202020", "aliases": [], "type": "realm_emoji"}),
            ("singing", {"code": "3", "aliases": [], "type": "realm_emoji"}),
            ("zulip", {"code": "4", "aliases": [], "type": "realm_emoji"}),
        ]
    )


@pytest.fixture
def unicode_emojis() -> "OrderedDict[str, Dict[str, Any]]":
    return OrderedDict(
        [
            (
                "happy",
                {"code": "1f600", "aliases": ["grinning"], "type": "unicode_emoji"},
            ),
            ("joker", {"code": "1f0cf", "aliases": [], "type": "unicode_emoji"}),
            ("joy_cat", {"code": "1f639", "aliases": [], "type": "unicode_emoji"}),
            (
                "rock_on",
                {
                    "code": "1f918",
                    "aliases": ["sign_of_the_horns"],
                    "type": "unicode_emoji",
                },
            ),
            ("smile", {"code": "263a", "aliases": [], "type": "unicode_emoji"}),
            ("smiley", {"code": "1f603", "aliases": [], "type": "unicode_emoji"}),
            ("smirk", {"code": "1f60f", "aliases": ["smug"], "type": "unicode_emoji"}),
            ("thumbs_up", {"code": "1f44d", "aliases": [], "type": "unicode_emoji"}),
        ]
    )


@pytest.fixture
def zulip_emoji() -> "OrderedDict[str, Dict[str, Any]]":
    return OrderedDict(
        [
            (
                "zulip",
                {"code": "zulip", "aliases": [], "type": "zulip_extra_emoji"},
            )
        ]
    )


def display_recipient_factory(
    recipient_details_list: List[Tuple[int, str]]
) -> List[Dict[str, Any]]:
    """
    Generate display_recipient field for (PM/group) messages
    """
    return [
        {
            "id": _id,
            "is_mirror_dummy": False,
            "full_name": _name,
            "email": f"{_name.split()[0]}@example.com",
        }
        for _id, _name in recipient_details_list
    ]


def msg_template_factory(
    msg_id: int,
    msg_type: MessageType,
    timestamp: int,
    *,
    subject: str = "",
    stream_id: Optional[int] = None,
    recipients: Union[str, List[Dict[str, Any]]] = "PTEST",
) -> Message:
    """
    Generate message template for all types of messages(stream/PM/group)
    """
    # TODO: Separate Message into distinct types for stream and private messages.
    message = Message(
        id=msg_id,
        sender_full_name="Foo Foo",
        timestamp=timestamp,
        client="website",
        sender_email="foo@zulip.com",
        type=msg_type,
        sender_realm_str="",
        flags=["read"],
        sender_id=5140,
        content_type="text/x-markdown",
        subject=subject,
        reactions=[],
        subject_links=[],
        avatar_url="dummy_avatar_url",
        is_me_message=False,
        content=f"{msg_type} content here.",
        display_recipient=recipients,
    )

    if msg_type == "stream":
        assert isinstance(stream_id, int)
        assert isinstance(recipients, str)
        message["stream_id"] = stream_id
    else:
        assert isinstance(recipients, list)
        for _val in recipients:
            assert isinstance(_val, dict)

    return message


@pytest.fixture
def stream_msg_template() -> Message:
    msg_template = msg_template_factory(
        537286, "stream", 1520918722, subject="Test", stream_id=205
    )
    return msg_template


@pytest.fixture
def extra_stream_msg_template() -> Message:
    msg_template = msg_template_factory(
        537289, "stream", 1520918740, subject="Test", stream_id=205
    )
    return msg_template


@pytest.fixture
def pm_template() -> Message:
    recipients = display_recipient_factory([(5179, "Boo Boo"), (5140, "Foo Foo")])
    return msg_template_factory(537287, "private", 1520918736, recipients=recipients)


@pytest.fixture
def group_pm_template() -> Message:
    recipients = display_recipient_factory(
        [(5179, "Boo Boo"), (5140, "Foo Foo"), (5180, "Bar Bar")]
    )
    return msg_template_factory(537288, "private", 1520918737, recipients=recipients)


@pytest.fixture(params=["pm_template", "group_pm_template"])
def private_message_fixture(request: Any) -> Message:
    return request.getfixturevalue(request.param)


@pytest.fixture(
    params=["stream_msg_template", "pm_template", "group_pm_template"],
    ids=["stream_message", "pm_message", "group_pm_message"],
)
def message_fixture(request: Any) -> Message:
    """
    Acts as a parametrize fixture for stream msg, pms and group_pms.
    """
    # `request` currently does not have an exported Pytest type.
    # TODO: Use the exported type when it's made available.
    template = request.getfixturevalue(request.param)
    return template


@pytest.fixture
def messages_successful_response(
    stream_msg_template: Message,
    pm_template: Message,
    group_pm_template: Message,
) -> Dict[str, Any]:
    """
    A successful response from a /messages API query.
    """
    return deepcopy(
        {
            "anchor": 10000000000000000,
            "messages": [
                stream_msg_template,
                pm_template,
                group_pm_template,
            ],
            "result": "success",
            "msg": "",
        }
    )


@pytest.fixture(
    params=SUPPORTED_SERVER_VERSIONS,
    ids=(lambda param: "server_version:{}-server_feature_level:{}".format(*param)),
)
def zulip_version(request: Any) -> Tuple[str, Optional[int]]:
    """
    Fixture to test different components based on the server version and the
    feature level.
    """
    return request.param


@pytest.fixture(
    params=[
        [
            {
                "content": "Hello!",
                "timestamp": 1530129122,
                "topic": "hello world",
                "user_id": 1001,
                # ...
            }
        ],
        [
            {
                "content": "Hello!",
                "timestamp": 1530129122,
                "topic": "party at my houz",
                "user_id": 1001,
                # ...
            },
            {
                "content": "Howdy!",
                "prev_content": "Hello!",
                "prev_topic": "party at my houz",
                "timestamp": 1530129134,
                "topic": "party at my house",
                "user_id": 1001,
                # ...
            },
        ],
    ],
    ids=[
        "unedited_message",
        "edited_message",
    ],
)
def message_history(request: Any) -> List[Dict[str, Any]]:
    """
    Returns message edit history for a message.
    """
    return request.param


@pytest.fixture
def topics() -> List[str]:
    return [
        "Topic 1",
        "This is a topic",
        "Hello there!",
        "He-llo there!",
        "Hello t/here!",
        "Hello from out-er_space!",
    ]


@pytest.fixture(
    params=[
        ({537286}, {537286}),
        ({537286, 537287}, set()),
        (set(), {537286, 537287}),
        ({537286, 537288}, {537287}),
        ({537287}, {537286, 537288}),
        ({537288}, {537286, 537287, 537288}),
        ({537286, 537287, 537288}, {537286}),
        ({537286, 537288}, {537286, 537288}),
    ],
    ids=[
        "stream_mention__stream_wildcard",
        "stream+pm_mention__no_wildcard",
        "no_mention__stream+pm_wildcard",
        "stream+group_mention__pm_wildcard",
        "pm_mention__stream+group_wildcard",
        "group_mention__all_wildcard",
        "all_mention__stream_wildcard",
        "stream+group_mention__wildcard",
    ],
)
def mentioned_messages_combination(request: Any) -> Tuple[Set[int], Set[int]]:
    """
    Returns a combination of mentioned and wildcard_mentioned messages
    """
    return deepcopy(request.param)


@pytest.fixture
def custom_profile_fields_fixture() -> List[CustomProfileField]:
    return [
        {
            # Short text: For one line responses, like "Job title".
            # Responses are limited to 50 characters.
            "id": 1,
            "name": "Phone number",
            "type": 1,
            "hint": "",
            "field_data": "",
            "order": 1,
        },
        {
            # Long text: For multiline responses, like "Biography".
            "id": 2,
            "name": "Biography",
            "type": 2,
            "hint": "What are you known for?",
            "field_data": "",
            "order": 2,
        },
        {
            # Another example of Short text field.
            "id": 3,
            "name": "Favorite food",
            "type": 1,
            "hint": "Or drink, if you'd prefer",
            "field_data": "",
            "order": 3,
        },
        {
            # List of options: Creates a dropdown with a list of options.
            "id": 4,
            "name": "Favorite editor",
            "type": 3,
            "hint": "",
            "field_data": (
                '{"0":{"text":"Vim","order":"1"},"1":{"text":"Emacs","order":"2"}}'
            ),
            "order": 4,
        },
        {
            # Date picker: For dates, like "Birthday".
            "id": 5,
            "name": "Birthday",
            "type": 4,
            "hint": "",
            "field_data": "",
            "order": 5,
        },
        {
            # Link: For links to websites.
            "id": 6,
            "name": "Favorite website",
            "type": 5,
            "hint": "Or your personal blog's URL",
            "field_data": "",
            "order": 6,
        },
        {
            # Person picker: For selecting one or more users,
            # like "Manager" or "Direct reports".
            "id": 7,
            "name": "Manager",
            "type": 6,
            "hint": "Only one person",
            "field_data": "",
            "order": 7,
        },
        {
            # Another person picker: Use case with multiple users.
            "id": 8,
            "name": "Mentor",
            "type": 6,
            "hint": "",
            "field_data": "",
            "order": 8,
        },
        {
            # External account: For linking to GitHub, Twitter, etc.
            # GitHub example
            "id": 9,
            "name": "GitHub username",
            "type": 7,
            "hint": "",
            "field_data": '{"subtype":"github"}',
            "order": 9,
        },
        {
            # Twitter example
            "id": 10,
            "name": "Twitter username",
            "type": 7,
            "hint": "",
            "field_data": '{"subtype":"twitter"}',
            "order": 10,
        },
        {
            # Custom example
            "id": 11,
            "name": "Reddit username",
            "type": 7,
            "hint": "",
            "field_data": '{"subtype":"custom", "url_pattern":"https://www.reddit.com/u/%(username)s"}',
            "order": 11,
        },
        {
            # Pronouns: What pronouns should people use to refer to the user?
            "id": 12,
            "name": "Pronouns",
            "type": 8,
            "hint": "What pronouns should people use to refer to you?",
            "field_data": "",
            "order": 12,
        },
    ]


@pytest.fixture
def custom_profile_data_fixture() -> Dict[str, CustomFieldValue]:
    return {
        "1": {"value": "6352813452", "rendered_value": "<p>6352813452</p>"},
        "2": {
            "value": "Simplicity\nThis is a multiline field",
            "rendered_value": "<p>Simplicity\nThis is a multiline field</p>",
        },
        "3": {"value": "cola", "rendered_value": "<p>cola</p>"},
        "4": {"value": "0"},
        "5": {"value": "2023-04-22"},
        "6": {"value": "https://www.google.com"},
        "7": {"value": "[11]"},
        "8": {"value": "[11, 13]"},
        "9": {"value": "gitmaster"},
        "10": {"value": "twittermaster"},
        "11": {"value": "redditmaster"},
        "12": {"value": "he/him"},
    }


@pytest.fixture
def clean_custom_profile_data_fixture() -> List[CustomProfileData]:
    return [
        {
            "label": "Phone number",
            "value": "6352813452",
            "type": 1,
            "order": 1,
        },
        {
            "label": "Biography",
            "value": "Simplicity\nThis is a multiline field",
            "type": 2,
            "order": 2,
        },
        {
            "label": "Favorite food",
            "value": "cola",
            "type": 1,
            "order": 3,
        },
        {
            "label": "Favorite editor",
            "value": "Vim",
            "type": 3,
            "order": 4,
        },
        {
            "label": "Birthday",
            "value": "2023-04-22",
            "type": 4,
            "order": 5,
        },
        {
            "label": "Favorite website",
            "value": "https://www.google.com",
            "type": 5,
            "order": 6,
        },
        {
            "label": "Manager",
            "value": [11],
            "type": 6,
            "order": 7,
        },
        {
            "label": "Mentor",
            "value": [11, 13],
            "type": 6,
            "order": 8,
        },
        {
            "label": "GitHub username",
            "value": "https://github.com/gitmaster",
            "type": 7,
            "order": 9,
        },
        {
            "label": "Twitter username",
            "value": "https://twitter.com/twittermaster",
            "type": 7,
            "order": 10,
        },
        {
            "label": "Reddit username",
            "value": "https://www.reddit.com/u/redditmaster",
            "type": 7,
            "order": 11,
        },
        {
            "label": "Pronouns",
            "value": "he/him",
            "type": 8,
            "order": 12,
        },
    ]


@pytest.fixture
def initial_data(
    logged_on_user: Dict[str, Any],
    users_fixture: List[Dict[str, Any]],
    streams_fixture: List[Dict[str, Any]],
    realm_emojis: Dict[str, Dict[str, Any]],
    custom_profile_fields_fixture: List[Dict[str, Union[str, int]]],
) -> Dict[str, Any]:
    """
    Response from /register API request.
    """
    return {
        "full_name": logged_on_user["full_name"],
        "email": logged_on_user["email"],
        "user_id": logged_on_user["user_id"],
        "realm_name": "Test Organization Name",
        "unsubscribed": [
            {
                "audible_notifications": False,
                "description": "announce",
                "stream_id": 7,
                "is_old_stream": True,
                "desktop_notifications": False,
                "pin_to_top": False,
                "stream_weekly_traffic": 0,
                "invite_only": False,
                "name": "announce",
                "push_notifications": False,
                "email_address": "",
                "color": "#bfd56f",
                "is_muted": False,
                "history_public_to_subscribers": True,
            }
        ],
        "result": "success",
        "muted_users": {},
        "queue_id": "1522420755:786",
        "realm_users": users_fixture,
        "cross_realm_bots": [
            {
                "full_name": "Notification Bot",
                "timezone": "",
                "is_bot": True,
                "date_joined": "2015-12-28T19:58:29.035543+00:00",
                "email": "notification-bot@zulip.com",
                "user_id": 5,
                "is_admin": False,
                "avatar_url": "dummy_avatar_url",
            },
            {
                "full_name": "Email Gateway",
                "timezone": "",
                "is_bot": True,
                "date_joined": "2015-12-28T19:58:29.037658+00:00",
                "email": "emailgateway@zulip.com",
                "user_id": 6,
                "is_admin": False,
                "avatar_url": "dummy_avatar_url",
            },
            {
                "full_name": "Welcome Bot",
                "timezone": "",
                "is_bot": True,
                "date_joined": "2015-12-28T19:58:29.033231+00:00",
                "email": "welcome-bot@zulip.com",
                "user_id": 4,
                "is_admin": False,
                "avatar_url": "dummy_avatar_url",
            },
            {
                "full_name": "Zulip Feedback Bot",
                "timezone": "",
                "is_bot": True,
                "date_joined": "2015-12-28T19:58:28.972281+00:00",
                "email": "feedback@zulip.com",
                "user_id": 1,
                "is_admin": False,
                "avatar_url": "dummy_avatar_url",
            },
        ],
        "subscriptions": streams_fixture,
        "msg": "",
        "max_message_id": 552761,
        "never_subscribed": [
            {
                "invite_only": False,
                "description": "Announcements from the Zulip GCI Mentors",
                "stream_id": 87,
                "name": "GCI announce",
                "is_old_stream": True,
                "stream_weekly_traffic": 0,
            },
            {
                "invite_only": False,
                "description": "General discussion",
                "stream_id": 74,
                "name": "GCI general",
                "is_old_stream": True,
                "stream_weekly_traffic": 0,
            },
        ],
        "unread_msgs": {
            "pms": [
                {"sender_id": 1, "unread_message_ids": [1, 2]},
                {"sender_id": 2, "unread_message_ids": [3]},
            ],
            "count": 0,
            "mentions": [],
            "streams": [
                {
                    "stream_id": 1000,
                    "topic": "Some general unread topic",
                    "unread_message_ids": [4, 5, 6],
                    "sender_ids": [1, 2],
                },
                {
                    "stream_id": 99,
                    "topic": "Some private unread topic",
                    "unread_message_ids": [7],
                    "sender_ids": [1, 2],
                },
            ],
            "huddles": [
                {"user_ids_string": "1001,11,12", "unread_message_ids": [11, 12, 13]},
                {
                    "user_ids_string": "1001,11,12,13",
                    "unread_message_ids": [101, 102],
                },
            ],
        },
        "presences": {
            "nyan.salmon+sns@gmail.com": {
                "ZulipElectron": {
                    "pushable": False,
                    "client": "ZulipElectron",
                    "status": "idle",
                    "timestamp": 1522484059,
                },
                "ZulipMobile": {
                    "pushable": False,
                    "client": "ZulipMobile",
                    "status": "idle",
                    "timestamp": 1522384165,
                },
                "aggregated": {
                    "timestamp": 1522484059,
                    "client": "ZulipElectron",
                    "status": "idle",
                },
            },
            logged_on_user["email"]: {
                "website": {
                    "pushable": True,
                    "client": "website",
                    "status": "active",
                    "timestamp": 1522458138,
                },
                "ZulipMobile": {
                    "pushable": True,
                    "client": "ZulipMobile",
                    "status": "active",
                    "timestamp": 1522480103,
                },
                "aggregated": {
                    "timestamp": 1522480103,
                    "client": "ZulipMobile",
                    "status": "active",
                },
            },
        },
        "twenty_four_hour_time": True,
        "pm_content_in_desktop_notifications": True,
        "realm_emoji": realm_emojis,
        "realm_message_retention_days": 74,
        "last_event_id": -1,
        "muted_topics": [],
        "realm_user_groups": [],
        # Deliberately use hard-coded zulip version and feature level to avoid
        # adding extra tests unnecessarily.
        "zulip_version": MINIMUM_SUPPORTED_SERVER_VERSION[0],
        "zulip_feature_level": MINIMUM_SUPPORTED_SERVER_VERSION[1],
        "starred_messages": [1117554, 1117558, 1117574],
        "custom_profile_fields": custom_profile_fields_fixture,
    }


@pytest.fixture
def initial_index() -> Index:
    return deepcopy(helper_initial_index)


@pytest.fixture
def empty_index(
    stream_msg_template: Message, pm_template: Message, group_pm_template: Message
) -> Index:
    return deepcopy(
        Index(
            pointer=dict(),
            all_msg_ids=set(),
            starred_msg_ids=set(),
            mentioned_msg_ids=set(),
            private_msg_ids=set(),
            private_msg_ids_by_user_ids=defaultdict(set, {}),
            stream_msg_ids_by_stream_id=defaultdict(set, {}),
            topic_msg_ids=defaultdict(dict, {}),
            edited_messages=set(),
            muted_messages=set(),
            topics=defaultdict(list),
            search=set(),
            messages=defaultdict(
                lambda: {},
                {
                    stream_msg_template["id"]: stream_msg_template,
                    pm_template["id"]: pm_template,
                    group_pm_template["id"]: group_pm_template,
                },
            ),
        )
    )


@pytest.fixture
def index_all_messages(empty_index: Index) -> Index:
    """
    Expected index of `initial_data` fixture when model.narrow = []
    """
    index = empty_index
    index["all_msg_ids"] = {537286, 537287, 537288}
    return index


@pytest.fixture
def index_stream(empty_index: Index) -> Index:
    """
    Expected index of initial_data when model.narrow = [['stream', '7']]
    """
    index = empty_index
    index["stream_msg_ids_by_stream_id"] = defaultdict(set, {205: {537286}})
    index["private_msg_ids"] = {537287, 537288}
    return index


@pytest.fixture
def index_topic(empty_index: Index) -> Index:
    """
    Expected index of initial_data when model.narrow = [['stream', '7'],
                                                        ['topic', 'Test']]
    """
    index = empty_index
    index["topic_msg_ids"] = defaultdict(dict, {205: {"Test": {537286}}})
    return index


@pytest.fixture
def index_multiple_topic_msg(
    empty_index: Index, extra_stream_msg_template: Message
) -> Index:
    """
    Index of initial_data with multiple message when model.narrow = [['stream, '7'],
                                                                     ['topic', 'Test']]
    """
    empty_index_with_multiple_topic_msg = empty_index
    empty_index_with_multiple_topic_msg["messages"].update(
        {extra_stream_msg_template["id"]: extra_stream_msg_template}
    )
    empty_index_with_multiple_topic_msg["topic_msg_ids"] = defaultdict(
        dict, {205: {"Test": {537286, 537289}}}
    )
    return empty_index_with_multiple_topic_msg


@pytest.fixture
def index_user(empty_index: Index) -> Index:
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                                         'boo@zulip.com'],
    """
    user_ids = frozenset({5179, 5140})
    index = empty_index
    index["private_msg_ids_by_user_ids"] = defaultdict(set, {user_ids: {537287}})
    index["private_msg_ids"] = {537287, 537288}
    return index


@pytest.fixture
def index_user_multiple(empty_index: Index) -> Index:
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                            'boo@zulip.com, bar@zulip.com'],
    """
    user_ids = frozenset({5179, 5140, 5180})
    index = empty_index
    index["private_msg_ids_by_user_ids"] = defaultdict(set, {user_ids: {537288}})
    index["private_msg_ids"] = {537287, 537288}
    return index


@pytest.fixture(
    params=[
        {537286, 537287, 537288},
        {537286},
        {537287},
        {537288},
        {537286, 537287},
        {537286, 537288},
        {537287, 537288},
    ]
)
def index_all_starred(empty_index: Index, request: Any) -> Index:
    msgs_with_stars = request.param
    index = empty_index
    index["starred_msg_ids"] = msgs_with_stars
    index["private_msg_ids"] = {537287, 537288}
    for msg_id, msg in index["messages"].items():
        if msg_id in msgs_with_stars and "starred" not in msg["flags"]:
            msg["flags"].append("starred")
    return index


@pytest.fixture()
def index_all_mentions(
    empty_index: Index, mentioned_messages_combination: Tuple[Set[int], Set[int]]
) -> Index:
    mentioned_messages, wildcard_mentioned_messages = mentioned_messages_combination
    index = empty_index
    index["mentioned_msg_ids"] = mentioned_messages | wildcard_mentioned_messages
    index["private_msg_ids"] = {537287, 537288}
    for msg_id, msg in index["messages"].items():
        if msg_id in mentioned_messages and "mentioned" not in msg["flags"]:
            msg["flags"].append("mentioned")
        if (
            msg_id in wildcard_mentioned_messages
            and "wildcard_mentioned" not in msg["flags"]
        ):
            msg["flags"].append("wildcard_mentioned")
    return index


@pytest.fixture()
def index_search_messages(empty_index: Index) -> Index:
    """Expected initial index when search contains the message_id 500."""
    index = empty_index
    index["search"] = {500}
    return index


@pytest.fixture
def user_profile(logged_on_user: Dict[str, Any]) -> Dict[str, Any]:
    return {  # FIXME These should all be self-consistent with others?
        "max_message_id": 589270,
        "full_name": logged_on_user["full_name"],
        "email": logged_on_user["email"],
        "is_bot": False,
        "user_id": logged_on_user["user_id"],
        "result": "success",
        "client_id": "abcd",
        "msg": "",
        "is_admin": False,
        "pointer": 589234,
    }


@pytest.fixture
def error_response() -> Dict[str, str]:
    return {"msg": "Invalid API key", "result": "error"}


@pytest.fixture
def user_dict(logged_on_user: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    User_dict created according to `initial_data` fixture.
    """
    return {
        logged_on_user["email"]: {
            "full_name": logged_on_user["full_name"],
            "email": logged_on_user["email"],
            "status": "active",
            "user_id": logged_on_user["user_id"],
        },
        "person1@example.com": {
            "full_name": "Human 1",
            "email": "person1@example.com",
            "user_id": 11,
            "status": "inactive",
        },
        "person2@example.com": {
            "full_name": "Human 2",
            "email": "person2@example.com",
            "user_id": 12,
            "status": "inactive",
        },
        "personduplicate1@example.com": {
            "full_name": "Human Duplicate",
            "email": "personduplicate1@example.com",
            "user_id": 13,
            "status": "inactive",
        },
        "personduplicate2@example.com": {
            "full_name": "Human Duplicate",
            "email": "personduplicate2@example.com",
            "user_id": 14,
            "status": "inactive",
        },
        "emailgateway@zulip.com": {
            "email": "emailgateway@zulip.com",
            "full_name": "Email Gateway",
            "status": "bot",
            "user_id": 6,
        },
        "feedback@zulip.com": {
            "email": "feedback@zulip.com",
            "full_name": "Zulip Feedback Bot",
            "status": "bot",
            "user_id": 1,
        },
        "notification-bot@zulip.com": {
            "email": "notification-bot@zulip.com",
            "full_name": "Notification Bot",
            "status": "bot",
            "user_id": 5,
        },
        "welcome-bot@zulip.com": {
            "email": "welcome-bot@zulip.com",
            "full_name": "Welcome Bot",
            "status": "bot",
            "user_id": 4,
        },
    }


@pytest.fixture
def user_id_email_dict(logged_on_user: Dict[str, Any]) -> Dict[int, str]:
    """
    User_id_email_dict created according to `initial_data` fixture.
    """
    return {
        logged_on_user["user_id"]: logged_on_user["email"],
        11: "person1@example.com",
        12: "person2@example.com",
        6: "emailgateway@zulip.com",
        1: "feedback@zulip.com",
        5: "notification-bot@zulip.com",
        4: "welcome-bot@zulip.com",
    }


@pytest.fixture
def user_list(logged_on_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    List of users created corresponding to
    `initial_data` fixture.
    """
    # NOTE These are sorted active > idle, then according to full_name
    return [
        {
            "full_name": logged_on_user["full_name"],
            "email": logged_on_user["email"],
            "status": "active",
            "user_id": logged_on_user["user_id"],
        },
        {
            "full_name": "Human 1",
            "email": "person1@example.com",
            "user_id": 11,
            "status": "inactive",
        },
        {
            "full_name": "Human 2",
            "email": "person2@example.com",
            "user_id": 12,
            "status": "inactive",
        },
        {
            "full_name": "Human Duplicate",
            "email": "personduplicate1@example.com",
            "user_id": 13,
            "status": "inactive",
        },
        {
            "full_name": "Human Duplicate",
            "email": "personduplicate2@example.com",
            "user_id": 14,
            "status": "inactive",
        },
        {
            "email": "emailgateway@zulip.com",
            "full_name": "Email Gateway",
            "status": "bot",
            "user_id": 6,
        },
        {
            "email": "notification-bot@zulip.com",
            "full_name": "Notification Bot",
            "status": "bot",
            "user_id": 5,
        },
        {
            "email": "welcome-bot@zulip.com",
            "full_name": "Welcome Bot",
            "status": "bot",
            "user_id": 4,
        },
        {
            "email": "feedback@zulip.com",
            "full_name": "Zulip Feedback Bot",
            "status": "bot",
            "user_id": 1,
        },
    ]


@pytest.fixture
def streams() -> List[Dict[str, Any]]:
    """
    List of streams created corresponding to
    `initial_data` fixture.
    """
    return [
        {
            "name": "Secret stream",
            "id": 99,
            "color": "#ccc",
            "invite_only": True,
            "description": "Some private stream",
        },
        {
            "name": "Some general stream",
            "id": 1000,
            "color": "#baf",
            "invite_only": False,
            "description": "General Stream",
        },
        {
            "name": "Stream 1",
            "id": 1,
            "color": "#baf",
            "invite_only": False,
            "description": "A description of stream 1",
        },
        {
            "name": "Stream 2",
            "id": 2,
            "color": "#baf",
            "invite_only": False,
            "description": "A description of stream 2",
        },
        {
            "name": "Web public stream",
            "id": 999,
            "color": "#ddd",
            "invite_only": False,
            "description": "Some web public stream",
        },
    ]


@pytest.fixture
def user_id(logged_on_user: Dict[str, Any]) -> int:
    """
    Default User id of the current
    user, i.e., Tomás Farías
    according to current Fixtures.
    """
    return logged_on_user["user_id"]


@pytest.fixture
def stream_dict(streams_fixture: List[Dict[str, Any]]) -> Dict[int, Any]:
    return {stream["stream_id"]: stream for stream in streams_fixture}


@pytest.fixture(
    params=[
        {
            ("Stream 1", "muted stream muted topic"): None,
            ("Stream 2", "muted topic"): None,
        },
        {
            ("Stream 1", "muted stream muted topic"): 1530129122,
            ("Stream 2", "muted topic"): 1530129122,
        },
    ],
    ids=[
        "zulip_feature_level:None",
        "zulip_feature_level:1",
    ],
)
def processed_muted_topics(request: Any) -> Dict[Tuple[str], Optional[int]]:
    """
    Locally processed muted topics data (see _muted_topics in Model.__init__).
    """
    return request.param


@pytest.fixture
def classified_unread_counts() -> Dict[str, Any]:
    """
    Unread counts return by
    helper.classify_unread_counts function.
    """
    return {
        "all_msg": 12,
        "all_pms": 8,
        "unread_topics": {
            (1000, "Some general unread topic"): 3,
            (99, "Some private unread topic"): 1,
        },
        "unread_pms": {
            1: 2,
            2: 1,
        },
        "unread_huddles": {
            frozenset({1001, 11, 12}): 3,
            frozenset({1001, 11, 12, 13}): 2,
        },
        "streams": {1000: 3, 99: 1},
    }


# --------------- UI Fixtures -----------------------------------------


@pytest.fixture(params=[True, False], ids=["ignore_mouse_click", "handle_mouse_click"])
def compose_box_is_open(request: Any) -> bool:
    return request.param


@pytest.fixture(
    params=[
        ("mouse press", 4, primary_key_for_command("GO_UP")),
        ("mouse press", 5, primary_key_for_command("GO_DOWN")),
    ],
    ids=[
        "mouse_scroll_up",
        "mouse_scroll_down",
    ],
)
def mouse_scroll_event(request: Any) -> Tuple[Any]:
    """
    Returns required parameters for mouse_event keypress
    """
    return request.param


@pytest.fixture(
    params=[key for cmd in ZT_TO_URWID_CMD_MAPPING for key in keys_for_command(cmd)],
    ids=lambda param: "nav-key:{}".format(*param),
)
def navigation_key(request: Any) -> str:
    """
    Fixture to generate navigation keys.
    This key is passed to the super `keypress` calls as is.
    """
    return request.param


@pytest.fixture
def widget_size() -> Callable[[Widget], urwid_Size]:
    """
    Returns widget size for any widget.
    """

    def _widget_size(widget: Widget) -> urwid_Size:
        widget_type, *_ = widget.sizing()
        if widget_type == "box":
            return (200, 20)
        elif widget_type == "flow":
            return (20,)
        else:
            return ()

    return _widget_size
