from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict

import pytest

from zulipterminal.config.keys import keys_for_command
from zulipterminal.helper import UnreadCounts
from zulipterminal.helper import initial_index as helper_initial_index
from zulipterminal.ui_tools.boxes import MessageBox
from zulipterminal.ui_tools.buttons import (
    StreamButton, TopicButton, UserButton,
)


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """
    Forces all the tests to work offline.
    """
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(autouse=True)
def no_asynch(mocker):
    """
    Make all function calls synchronous.
    """
    mocker.patch('zulipterminal.helper.asynch')

# --------------- Controller Fixtures -----------------------------------------


@pytest.fixture
def stream_button(mocker):
    """
    Mocked stream button.
    """
    view_mock = mocker.Mock()
    view_mock.palette = [(None, 'black', 'white')]
    button = StreamButton(
        properties=['PTEST', 205, '#bfd56f', False, "Test stream description"],
        controller=mocker.patch('zulipterminal.core.Controller'),
        width=40,
        view=view_mock,
        count=30
    )
    return button


@pytest.fixture
def user_button(mocker, width=38):
    """
    Mocked User Button.
    """
    return UserButton(
        user={
            'user_id': 5179,
            'full_name': 'Boo Boo',
            'email': 'boo@zulip.com',
        },
        width=width,
        controller=mocker.patch('zulipterminal.core.Controller'),
        view=mocker.patch('zulipterminal.ui.View')
    )


@pytest.fixture
def msg_box(mocker, messages_successful_response):
    """
    Mocked MessageBox with stream message
    """
    return MessageBox(
        messages_successful_response['messages'][0],
        mocker.patch('zulipterminal.model.Model'),
        None,
    )


# --------------- Model Fixtures ----------------------------------------------

@pytest.fixture
def users_fixture(logged_on_user):
    users = [logged_on_user]
    for i in range(1, 3):
        users.append({
            'user_id': 10 + i,
            'full_name': 'Human {}'.format(i),
            'email': 'person{}@example.com'.format(i),
            'avatar_url': None,
            'is_active': True,
            'bot_type': None,
            'is_bot': False,
            'is_admin': False,
        })
    return users


@pytest.fixture
def user_groups_fixture():
    user_groups = []
    members = [[1001, 11], [11, 12], [12], []]
    for i in range(1, 5):
        user_groups.append({
            'id': 10 + i,
            'name': 'Group {}'.format(i),
            'description': 'Core developers of Group {}'.format(i),
            'members': members[i-1],
        })
    return user_groups


@pytest.fixture
def logged_on_user():
    return {
        'user_id': 1001,
        'full_name': 'Human Myself',
        'email': 'FOOBOO@gmail.com',
        'short_name': 'Human',
    }


general_stream = {
    'name': 'Some general stream',
    'invite_only': False,
    'color': '#b0a5fd',                   # Color in '#xxxxxx' format
    'pin_to_top': False,
    'stream_id': 1000,
    'in_home_view': True,
    'audible_notifications': False,
    'description': 'General Stream',
    'is_old_stream': True,
    'desktop_notifications': False,
    'stream_weekly_traffic': 0,
    'push_notifications': False,
    'email_address': 'general@example.comm',
}

# This is a private stream;
# only description/stream_id/invite_only/name/color vary from above
secret_stream = {
    'description': 'Some private stream',
    'stream_id': 99,
    'pin_to_top': False,
    'invite_only': True,
    'name': 'Secret stream',
    'email_address': 'secret@example.com',
    'color': '#ccc',                      # Color in '#xxx' format
    'in_home_view': True,
    'audible_notifications': False,
    'is_old_stream': True,
    'desktop_notifications': False,
    'stream_weekly_traffic': 0,
    'push_notifications': False,
}


@pytest.fixture
def streams_fixture():
    streams = [general_stream, secret_stream]
    for i in range(1, 3):
        streams.append({
            'name': 'Stream {}'.format(i),
            'invite_only': False,
            'color': '#b0a5fd',
            'pin_to_top': False,
            'stream_id': i,
            'in_home_view': True,
            'audible_notifications': False,
            'description': 'A description of stream {}'.format(i),
            'is_old_stream': True,
            'desktop_notifications': False,
            'stream_weekly_traffic': 0,
            'push_notifications': False,
            'email_address': 'stream{}@example.com'.format(i),
        })
    return deepcopy(streams)


@pytest.fixture
def emojis_fixture():
    return [
        'happy',
        'joker',
        'joy_cat',
        'rock_on',
        'smile',
        'smiley',
        'smirk',
        ]


stream_msg_template = {
    'id': 537286,
    'sender_full_name': 'Foo Foo',
    'timestamp': 1520918722,
    'client': 'website',
    'recipient_id': 6076,
    'sender_email': 'foo@zulip.com',
    'type': 'stream',
    'sender_realm_str': '',
    'flags': ['read'],
    'sender_id': 5140,
    'content_type': 'text/x-markdown',
    'stream_id': 205,
    'subject': 'Test',
    'reactions': [],
    'subject_links': [],
    'avatar_url': 'dummy_avatar_url',
    'is_me_message': False,
    'sender_short_name': 'foo',
    'content': 'Stream content here.',
    'display_recipient': 'PTEST',
}

pm_template = {
    'id': 537287,
    'sender_full_name': 'Foo Foo',
    'timestamp': 1520918736,
    'client': 'website',
    'recipient_id': 5780,
    'is_me_message': False,
    'sender_email': 'foo@zulip.com',
    'flags': ['read'],
    'sender_id': 5140,
    'content_type': 'text/x-markdown',
    'sender_realm_str': '',
    'subject': '',
    'reactions': [],
    'type': 'private',
    'avatar_url': 'dummy_avatar_url',
    'subject_links': [],
    'sender_short_name': 'foo',
    'content': 'Hey PM content here.',
    'display_recipient': [{
        'id': 5179,
        'is_mirror_dummy': False,
        'full_name': 'Boo Boo',
        'short_name': 'boo',
        'email': 'boo@zulip.com',
    }, {
        'short_name': 'foo',
        'id': 5140,
        'is_mirror_dummy': False,
        'full_name': 'Foo Foo',
        'email': 'foo@zulip.com',
    }],
}

group_pm_template = {
    'id': 537288,
    'sender_full_name': 'Foo Foo',
    'timestamp': 1520918737,
    'client': 'website',
    'recipient_id': 5780,  # FIXME Unsure
    'is_me_message': False,
    'sender_email': 'foo@zulip.com',
    'flags': ['read'],
    'sender_id': 5140,
    'content_type': 'text/x-markdown',
    'sender_realm_str': '',
    'subject': '',
    'reactions': [],
    'type': 'private',
    'avatar_url': 'dummy_avatar_url',
    'subject_links': [],
    'sender_short_name': 'foo',
    'content': 'Hey PM content here again.',
    'display_recipient': [{
        'id': 5179,
        'is_mirror_dummy': False,
        'full_name': 'Boo Boo',
        'short_name': 'boo',
        'email': 'boo@zulip.com',
    }, {
        'short_name': 'foo',
        'id': 5140,
        'is_mirror_dummy': False,
        'full_name': 'Foo Foo',
        'email': 'foo@zulip.com',
    }, {
        'short_name': 'bar',
        'id': 5180,
        'is_mirror_dummy': False,
        'full_name': 'Bar Bar',
        'email': 'bar@zulip.com',
    }],
}


@pytest.fixture(params=[
    stream_msg_template, pm_template, group_pm_template
], ids=["stream_message", "pm_message", "group_pm_message"])
def message_fixture(request):
    """
    Acts as a parametrize fixture for stream msg, pms and group_pms.
    """
    return deepcopy(request.param)


@pytest.fixture
def messages_successful_response() -> Dict[str, Any]:
    """
    A successful response from a /messages API query.
    """
    return deepcopy({
        'anchor': 10000000000000000,
        'messages': [
            stream_msg_template,
            pm_template,
            group_pm_template,
        ],
        'result': 'success',
        'msg': '',
    })


@pytest.fixture
def initial_data(logged_on_user, users_fixture, streams_fixture):
    """
    Response from /register API request.
    """
    return {
        'full_name': logged_on_user['full_name'],
        'email': logged_on_user['email'],
        'user_id': logged_on_user['user_id'],
        'realm_name': 'Test Organization Name',
        'unsubscribed': [{
            'audible_notifications': False,
            'description': 'announce',
            'stream_id': 7,
            'is_old_stream': True,
            'desktop_notifications': False,
            'pin_to_top': False,
            'stream_weekly_traffic': 0,
            'invite_only': False,
            'name': 'announce',
            'push_notifications': False,
            'email_address': '',
            'color': '#bfd56f',
            'in_home_view': True
        }],
        'result': 'success',
        'queue_id': '1522420755:786',
        'realm_users': users_fixture,
        'cross_realm_bots': [{
            'full_name': 'Notification Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.035543+00:00',
            'email': 'notification-bot@zulip.com',
            'user_id': 5,
            'is_admin': False,
            'avatar_url': 'dummy_avatar_url'
        }, {
            'full_name': 'Email Gateway',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.037658+00:00',
            'email': 'emailgateway@zulip.com',
            'user_id': 6,
            'is_admin': False,
            'avatar_url': 'dummy_avatar_url'
        }, {
            'full_name': 'Welcome Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.033231+00:00',
            'email': 'welcome-bot@zulip.com',
            'user_id': 4,
            'is_admin': False,
            'avatar_url': 'dummy_avatar_url'
        }, {
            'full_name': 'Zulip Feedback Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:28.972281+00:00',
            'email': 'feedback@zulip.com',
            'user_id': 1,
            'is_admin': False,
            'avatar_url': 'dummy_avatar_url'
        }],
        'subscriptions': streams_fixture,
        'msg': '',
        'max_message_id': 552761,
        'never_subscribed': [{
            'invite_only': False,
            'description': 'Announcements from the Zulip GCI Mentors',
            'stream_id': 87,
            'name': 'GCI announce',
            'is_old_stream': True,
            'stream_weekly_traffic': 0
        }, {
            'invite_only': False,
            'description': 'General discussion',
            'stream_id': 74,
            'name': 'GCI general',
            'is_old_stream': True,
            'stream_weekly_traffic': 0
        }],
        'unread_msgs': {
            'pms': [{
                'sender_id': 1,
                'unread_message_ids': [1, 2]
            }, {
                'sender_id': 2,
                'unread_message_ids': [3]
            }],
            'count': 0,
            'mentions': [],
            'streams': [{
                'stream_id': 1000,
                'topic': 'Some general unread topic',
                'unread_message_ids': [4, 5, 6],
                'sender_ids': [1, 2]
            }, {
                'stream_id': 99,
                'topic': 'Some private unread topic',
                'unread_message_ids': [7],
                'sender_ids': [1, 2]
            }],
            'huddles': [{
              'user_ids_string': '1001,11,12',
              'unread_message_ids': [11, 12, 13]
                }, {
              'user_ids_string': '1001,11,12,13',
              'unread_message_ids': [101, 102],
            }]
        },
        'presences': {
            'nyan.salmon+sns@gmail.com': {
                'ZulipElectron': {
                    'pushable': False,
                    'client': 'ZulipElectron',
                    'status': 'idle',
                    'timestamp': 1522484059
                },
                'ZulipMobile': {
                    'pushable': False,
                    'client': 'ZulipMobile',
                    'status': 'idle',
                    'timestamp': 1522384165
                },
                'aggregated': {
                    'timestamp': 1522484059,
                    'client': 'ZulipElectron',
                    'status': 'idle'
                }
            },
            logged_on_user['email']: {
                'website': {
                    'pushable': True,
                    'client': 'website',
                    'status': 'active',
                    'timestamp': 1522458138
                },
                'ZulipMobile': {
                    'pushable': True,
                    'client': 'ZulipMobile',
                    'status': 'active',
                    'timestamp': 1522480103
                },
                'aggregated': {
                    'timestamp': 1522480103,
                    'client': 'ZulipMobile',
                    'status': 'active'
                }
            }
        },
        'last_event_id': -1,
        'muted_topics': [],
        'realm_user_groups': [],
    }


@pytest.fixture
def initial_index():
    return deepcopy(helper_initial_index)


@pytest.fixture
def empty_index():
    return deepcopy({
        'pointer': defaultdict(set, {}),
        'all_msg_ids':  set(),
        'starred_msg_ids': set(),
        'mentioned_msg_ids': set(),
        'private_msg_ids': set(),
        'private_msg_ids_by_user_ids': defaultdict(set, {}),
        'stream_msg_ids_by_stream_id': defaultdict(set, {}),
        'topic_msg_ids': defaultdict(dict, {}),
        'edited_messages': set(),
        'topics': defaultdict(list),
        'search': set(),
        'messages': defaultdict(dict, {
            stream_msg_template['id']: stream_msg_template,
            pm_template['id']: pm_template,
            group_pm_template['id']: group_pm_template,
        })
    })


@pytest.fixture
def index_all_messages(empty_index):
    """
    Expected index of `initial_data` fixture when model.narrow = []
    """
    return dict(empty_index, **{'all_msg_ids': {537286, 537287, 537288}})


@pytest.fixture
def index_stream(empty_index):
    """
    Expected index of initial_data when model.narrow = [['stream', '7']]
    """
    diff = {'stream_msg_ids_by_stream_id': defaultdict(set, {205: {537286}}),
            'private_msg_ids': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture
def index_topic(empty_index):
    """
    Expected index of initial_data when model.narrow = [['stream', '7'],
                                                        ['topic', 'Test']]
    """
    diff = {'topic_msg_ids': defaultdict(dict, {205: {'Test': {537286}}})}
    return dict(empty_index, **diff)


@pytest.fixture
def index_user(empty_index):
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                                         'boo@zulip.com'],
    """
    user_ids = frozenset({5179, 5140})
    diff = {'private_msg_ids_by_user_ids': defaultdict(set,
                                                       {user_ids: {537287}}),
            'private_msg_ids': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture
def index_user_multiple(empty_index):
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                            'boo@zulip.com, bar@zulip.com'],
    """
    user_ids = frozenset({5179, 5140, 5180})
    diff = {'private_msg_ids_by_user_ids': defaultdict(set,
                                                       {user_ids: {537288}}),
            'private_msg_ids': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture(params=[
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def index_all_starred(empty_index, request):
    msgs_with_stars = request.param
    index = dict(empty_index, starred_msg_ids=msgs_with_stars,
                 private_msg_ids={537287, 537288})
    for msg_id, msg in index['messages'].items():
        if msg_id in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')
    return index


@pytest.fixture(params=[
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def index_all_mentions(empty_index, request):
    mentioned_messages = request.param
    index = dict(empty_index, mentioned_msg_ids=mentioned_messages,
                 private_msg_ids={537287, 537288})
    for msg_id, msg in index['messages'].items():
        if msg_id in mentioned_messages and 'mentioned' not in msg['flags']:
            msg['flags'].append('mentioned')
    return index


@pytest.fixture
def user_profile(logged_on_user):
    return {  # FIXME These should all be self-consistent with others?
        'max_message_id': 589270,
        'short_name': logged_on_user['short_name'],
        'full_name': logged_on_user['full_name'],
        'email': logged_on_user['email'],
        'is_bot': False,
        'user_id': logged_on_user['user_id'],
        'result': 'success',
        'client_id': 'abcd',
        'msg': '',
        'is_admin': False,
        'pointer': 589234
    }


@pytest.fixture
def error_response():
    return {
        "msg": "Invalid API key",
        "result": "error"
    }


@pytest.fixture
def user_dict(logged_on_user):
    """
    User_dict created according to `initial_data` fixture.
    """
    return {
        logged_on_user['email']: {
            'full_name': logged_on_user['full_name'],
            'email': logged_on_user['email'],
            'status': 'active',
            'user_id': logged_on_user['user_id'],
        },
        'person1@example.com': {
            'full_name': 'Human 1',
            'email': 'person1@example.com',
            'user_id': 11,
            'status': 'inactive'
        },
        'person2@example.com': {
            'full_name': 'Human 2',
            'email': 'person2@example.com',
            'user_id': 12,
            'status': 'inactive'
        },
        'emailgateway@zulip.com': {
            'email': 'emailgateway@zulip.com',
            'full_name': 'Email Gateway',
            'status': 'inactive',
            'user_id': 6
        },
        'feedback@zulip.com': {
            'email': 'feedback@zulip.com',
            'full_name': 'Zulip Feedback Bot',
            'status': 'inactive',
            'user_id': 1
        },
        'notification-bot@zulip.com': {
            'email': 'notification-bot@zulip.com',
            'full_name': 'Notification Bot',
            'status': 'inactive',
            'user_id': 5
        },
        'welcome-bot@zulip.com': {
            'email': 'welcome-bot@zulip.com',
            'full_name': 'Welcome Bot',
            'status': 'inactive',
            'user_id': 4
        },
    }


@pytest.fixture
def user_list(logged_on_user):
    """
    List of users created corresponding to
    `initial_data` fixture.
    """
    # NOTE These are sorted active > idle, then according to full_name
    return [{
        'full_name': logged_on_user['full_name'],
        'email': logged_on_user['email'],
        'status': 'active',
        'user_id': logged_on_user['user_id'],
    }, {
        'email': 'emailgateway@zulip.com',
        'full_name': 'Email Gateway',
        'status': 'inactive',
        'user_id': 6
    }, {
        'full_name': 'Human 1',
        'email': 'person1@example.com',
        'user_id': 11,
        'status': 'inactive'
    }, {
        'full_name': 'Human 2',
        'email': 'person2@example.com',
        'user_id': 12,
        'status': 'inactive'
    }, {
        'email': 'notification-bot@zulip.com',
        'full_name': 'Notification Bot',
        'status': 'inactive',
        'user_id': 5
    }, {
        'email': 'welcome-bot@zulip.com',
        'full_name': 'Welcome Bot',
        'status': 'inactive',
        'user_id': 4
    }, {
        'email': 'feedback@zulip.com',
        'full_name': 'Zulip Feedback Bot',
        'status': 'inactive',
        'user_id': 1
    }]


@pytest.fixture
def streams():
    """
    List of streams created corresponding to
    `initial_data` fixture.
    """
    return [['Secret stream', 99, '#ccc', True, 'Some private stream'],
            ['Some general stream', 1000, '#baf', False, 'General Stream'],
            ['Stream 1', 1, '#baf', False, 'A description of stream 1'],
            ['Stream 2', 2, '#baf', False, 'A description of stream 2']]


@pytest.fixture
def user_id(logged_on_user):
    """
    Default User id of the current
    user, i.e., Tomás Farías
    according to current Fixtures.
    """
    return logged_on_user['user_id']


@pytest.fixture
def stream_dict(streams_fixture):
    return {stream['stream_id']: stream for stream in streams_fixture}


@pytest.fixture
def classified_unread_counts():
    """
    Unread counts return by
    helper.classify_unread_counts function.
    """
    return {
        'all_msg': 12,
        'all_pms': 8,
        'unread_topics': {
            (1000, 'Some general unread topic'): 3,
            (99, 'Some private unread topic'): 1
        },
        'unread_pms': {
            1: 2,
            2: 1,
        },
        'unread_huddles': {
            frozenset({1001, 11, 12}): 3,
            frozenset({1001, 11, 12, 13}): 2
        },
        'streams': {
            1000: 3,
            99: 1
        }
    }


@pytest.fixture
def initial_unread_counts():
    return UnreadCounts(all_msg=0, all_pms=0,
                        unread_topics=dict(), unread_pms=dict(),
                        unread_huddles=dict(), streams=dict())


@pytest.fixture
def index_multiple_messages():
    """
    Index fixture filled with multiple entries for messages.
    Private messages have minimal data required to test `set_count`.
    More can be added if and when required.
    """
    return dict(helper_initial_index, **{'messages': {
        1: {'id': 1, 'type': 'stream', 'subject': 'Topic 1', 'sender_id': 99,
            'stream_id': 1001, 'display_recipient': 'stream 1', 'flags': []},
        2: {'id': 2, 'type': 'stream', 'subject': 'Topic 1', 'sender_id': 100,
            'stream_id': 1001, 'display_recipient': 'stream 1', 'flags': []},
        3: {'id': 3, 'type': 'stream', 'subject': 'Topic 2', 'sender_id': 98,
            'stream_id': 1002, 'display_recipient': 'stream 2', 'flags': []},
        4: {'id': 4, 'type': 'stream', 'subject': 'Topic 3', 'sender_id': 101,
            'stream_id': 1002, 'display_recipient': 'stream 3', 'flags': []},
        5: {'id': 5, 'type': 'stream', 'subject': 'Topic 3', 'sender_id': 101,
            'stream_id': 1002, 'display_recipient': 'stream 3', 'flags': []},
        6: {'id': 6, 'type': 'stream', 'subject': 'Topic 1', 'sender_id': 101,
            'stream_id': 1001, 'display_recipient': 'stream 1', 'flags': []},
        7: {'id': 7, 'type': 'stream', 'subject': 'Topic 1', 'sender_id': 101,
            'stream_id': 1001, 'display_recipient': 'stream 1', 'flags': []},
        8: {'id': 8, 'type': 'stream', 'subject': 'Topic 10', 'sender_id': 101,
            'stream_id': 1003, 'display_recipient': 'stream 10', 'flags': []},
        9: {'id': 9, 'type': 'stream', 'subject': 'Topic 10', 'sender_id': 101,
            'stream_id': 1003, 'display_recipient': 'stream 10', 'flags': []},
        # pms
        10: {'id': 10, 'type': 'private', 'sender_id': 200,
             'display_recipient': [{'id': 202}, {'id': 200}], 'flags': []},
        11: {'id': 11, 'type': 'private', 'sender_id': 201,
             'display_recipient': [{'id': 202}, {'id': 201}], 'flags': []},
        12: {'id': 12, 'type': 'private', 'sender_id': 202,
             'display_recipient': [{'id': 202}, {'id': 201}], 'flags': []},
        13: {'id': 13, 'type': 'private', 'sender_id': 200,
             'display_recipient': [{'id': 202}, {'id': 200}], 'flags': []},
        14: {'id': 14, 'type': 'private', 'sender_id': 201,
             'display_recipient': [{'id': 202}, {'id': 201}], 'flags': []},
        15: {'id': 15, 'type': 'private', 'sender_id': 202,
             'display_recipient': [{'id': 202}], 'flags': []},
        16: {'id': 16, 'type': 'private', 'sender_id': 200,
             'display_recipient': [{'id': 202}, {'id': 200}], 'flags': []},
        }})

# --------------- UI Fixtures -----------------------------------------


@pytest.fixture(params=[
        (key, expected_key)
        for keys, expected_key in [
            (keys_for_command('GO_UP'), 'up'),
            (keys_for_command('GO_DOWN'), 'down'),
            (keys_for_command('SCROLL_UP'), 'page up'),
            (keys_for_command('SCROLL_DOWN'), 'page down'),
            (keys_for_command('GO_TO_BOTTOM'), 'end'),
        ]
        for key in keys
    ],
    ids=lambda param: 'key:{}-expected_key:{}'.format(*param)
)
def navigation_key_expected_key_pair(request):
    """
    Fixture to generate pairs of navigation keys with their respective
    expected key.
    The expected key is the one which is passed to the super `keypress` calls.
    """
    return request.param
