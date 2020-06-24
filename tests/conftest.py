from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict

import pytest

from zulipterminal.ui_tools.boxes import MessageBox
from zulipterminal.ui_tools.buttons import StreamButton, UserButton
from zulipterminal.helper import initial_index as helper_initial_index


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
        properties=['PTEST', 205, '#bfd56f', False],
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
def logged_on_user():
    return {
        'user_id': 1001,
        'full_name': 'Human Myself',
        'email': 'FOOBOO@gmail.com',
        'short_name': 'Human',
    }

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
    'avatar_url': '/user_avatars/2/foo.png?x=x&version=2',
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
    'avatar_url': '/user_avatars/2/foo.png?x=x&version=2',
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
    'avatar_url': '/user_avatars/2/foo.png?x=x&version=2',
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
def initial_data(logged_on_user):
    """
    Response from /register API request.
    """
    return {
        'full_name': logged_on_user['full_name'],
        'email': logged_on_user['email'],
        'user_id': logged_on_user['user_id'],
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
        'realm_users': [{
            'bot_type': None,
            'is_bot': False,
            'is_admin': False,
            'email': logged_on_user['email'],
            'full_name': logged_on_user['full_name'],
            'user_id': logged_on_user['user_id'],
            'avatar_url': None,
            'is_active': True
        }, {
            'full_name': 'Jari Winberg',
            'user_id': 6086,
            'avatar_url': None,
            'is_active': True,
            'bot_type': None,
            'is_bot': False,
            'is_admin': False,
            'email': 'nyan.salmon+sns@gmail.com',
        }, {
            'bot_type': None,
            'is_bot': False,
            'is_admin': False,
            'email': 'cloudserver2@hotmail.de',
            'full_name': 'Test Account',
            'user_id': 6085,
            'is_active': True
        }],
        'cross_realm_bots': [{
            'full_name': 'Notification Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.035543+00:00',
            'email': 'notification-bot@zulip.com',
            'user_id': 5,
            'is_admin': False,
            'avatar_url': 'https://secure.gravatar.com/avatar/'
                          '0fc5476bdf03fe8640cc8fbc27a47549'
                          '?d=identicon&version=1'
        }, {
            'full_name': 'Email Gateway',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.037658+00:00',
            'email': 'emailgateway@zulip.com',
            'user_id': 6,
            'is_admin': False,
            'avatar_url': 'https://secure.gravatar.com/avatar/'
                          '99ac4226a594fca879bb598c1b36fb42'
                          '?d=identicon&version=1'
        }, {
            'full_name': 'Welcome Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:29.033231+00:00',
            'email': 'welcome-bot@zulip.com',
            'user_id': 4,
            'is_admin': False,
            'avatar_url': 'https://secure.gravatar.com/avatar/'
                          '6a4e22d220487fb7ceb295fa706f39d5'
                          '?d=identicon&version=1'
        }, {
            'full_name': 'Zulip Feedback Bot',
            'timezone': '',
            'is_bot': True,
            'date_joined': '2015-12-28T19:58:28.972281+00:00',
            'email': 'feedback@zulip.com',
            'user_id': 1,
            'is_admin': False,
            'avatar_url': 'https://secure.gravatar.com/avatar/'
                          '78eecc367eedd27e6ac9292dc966beb6'
                          '?d=identicon&version=1'
        }],
        'subscriptions': [{
            'audible_notifications': False,
            'description': '',
            'stream_id': 86,
            'is_old_stream': True,
            'desktop_notifications': False,
            'pin_to_top': False,
            'stream_weekly_traffic': 0,
            'invite_only': False,
            'name': 'Django',
            'push_notifications': False,
            'email_address': '',
            'color': '#94c849',
            'in_home_view': True
        }, {
            'audible_notifications': False,
            'description': 'The Google Summer of Code',
            'stream_id': 14,
            'is_old_stream': True,
            'desktop_notifications': False,
            'pin_to_top': False,
            'stream_weekly_traffic': 53,
            'invite_only': False,
            'name': 'GSoC',
            'push_notifications': False,
            'email_address': '',
            'color': '#c2c2c2',
            'in_home_view': True
        }, {
            # This is a private stream;
            # only description/stream_id/invite_only/name/color vary from above
            'audible_notifications': False,
            'description': 'Some private stream',
            'stream_id': 99,
            'is_old_stream': True,
            'desktop_notifications': False,
            'pin_to_top': False,
            'stream_weekly_traffic': 53,
            'invite_only': True,
            'name': 'Secret stream',
            'push_notifications': False,
            'email_address': '',
            'color': '#c3c3c3',
            'in_home_view': True
        }],
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
            'pms': [],
            'count': 0,
            'mentions': [],
            'streams': [],
            'huddles': []
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
        'nyan.salmon+sns@gmail.com': {
            'full_name': 'Jari Winberg',
            'email': 'nyan.salmon+sns@gmail.com',
            'status': 'offline',
            'user_id': 6086
        },
        'cloudserver2@hotmail.de': {
            'full_name': 'Test Account',
            'email': 'cloudserver2@hotmail.de',
            'status': 'inactive',
            'user_id': 6085
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
        'full_name': 'Jari Winberg',
        'email': 'nyan.salmon+sns@gmail.com',
        'status': 'offline',
        'user_id': 6086
    }, {
        'email': 'emailgateway@zulip.com',
        'full_name': 'Email Gateway',
        'status': 'inactive',
        'user_id': 6
    }, {
        'email': 'notification-bot@zulip.com',
        'full_name': 'Notification Bot',
        'status': 'inactive',
        'user_id': 5
    }, {
        'full_name': 'Test Account',
        'email': 'cloudserver2@hotmail.de',
        'status': 'inactive',
        'user_id': 6085
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
    return [
        ['Django', 86, '#94c849', False],
        ['GSoC', 14, '#c2c2c2', False],
        ['Secret stream', 99, '#c3c3c3', True],
    ]


@pytest.fixture
def user_id(logged_on_user):
    """
    Default User id of the current
    user, i.e., Tomás Farías
    according to current Fixtures.
    """
    return logged_on_user['user_id']
