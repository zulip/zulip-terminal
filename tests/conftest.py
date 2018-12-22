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
    button = StreamButton(
        properties=['PTEST', 205, '#bfd56f', False],
        controller=mocker.patch('zulipterminal.core.Controller'),
        view=mocker.patch('zulipterminal.ui.View')
    )
    return button


@pytest.fixture
def user_button(mocker):
    """
    Mocked User Button.
    """
    return UserButton(
        user={
            'user_id': 5179,
            'full_name': 'Boo Boo',
            'email': 'boo@zulip.com',
        },
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
def messages_successful_response() -> Dict[str, Any]:
    """
    A successful response from a /messages API query.
    """
    response = {
        'anchor': 10000000000000000,
        'messages': [{
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
        }, {
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
        }, {
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
        }],
        'result': 'success',
        'msg': '',
    }
    return response


@pytest.fixture(scope="module")
def initial_data():
    """
    Response from /register API request.
    """
    return {
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
            'email': 'FOOBOO@gmail.com',
            'full_name': 'Tomás Farías',
            'user_id': 5827,
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
            'FOOBOO@gmail.com': {
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
    return {
        'pointer': defaultdict(set, {}),
        'private': defaultdict(set, {}),
        'all_messages':  set(),
        'all_private': set(),
        'all_stream': defaultdict(set, {}),
        'stream': defaultdict(dict, {}),
        'search': set(),
        'all_starred': set(),
        'messages': defaultdict(dict, {
            537286: {
                'type': 'stream',
                'sender_realm_str': '',
                'is_me_message': False,
                'content': 'Stream content here.',
                'recipient_id': 6076,
                'avatar_url': '/user_avatars/2/foo.png?x=x&version=2',
                'client': 'website',
                'stream_id': 205,
                'subject_links': [],
                'content_type': 'text/x-markdown',
                'display_recipient': 'PTEST',
                'reactions': [],
                'sender_short_name': 'foo',
                'id': 537286,
                'flags': ['read'],
                'sender_email': 'foo@zulip.com',
                'timestamp': 1520918722,
                'subject': 'Test',
                'sender_id': 5140,
                'sender_full_name': 'Foo Foo'
            },
            537287: {
                'type': 'private',
                'sender_realm_str': '',
                'is_me_message': False,
                'content': 'Hey PM content here.',
                'recipient_id': 5780,
                'client': 'website',
                'subject': '',
                'avatar_url': '/user_avatars/2/foo.png?x=x&version=2',
                'content_type': 'text/x-markdown',
                'display_recipient': [{
                    'id': 5179,
                    'full_name': 'Boo Boo',
                    'email': 'boo@zulip.com',
                    'short_name': 'boo',
                    'is_mirror_dummy': False
                }, {
                    'id': 5140,
                    'full_name': 'Foo Foo',
                    'email': 'foo@zulip.com',
                    'short_name': 'foo',
                    'is_mirror_dummy': False
                }],
                'sender_short_name': 'foo',
                'id': 537287,
                'flags': ['read'],
                'sender_email': 'foo@zulip.com',
                'timestamp': 1520918736,
                'reactions': [],
                'sender_id': 5140,
                'sender_full_name': 'Foo Foo',
                'subject_links': []
            },
            537288: {
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
        }),
    }


@pytest.fixture
def index_all_messages(empty_index):
    """
    Expected index of `initial_data` fixture when model.narrow = []
    """
    return dict(empty_index, **{'all_messages': {537286, 537287, 537288}})


@pytest.fixture
def index_stream(empty_index):
    """
    Expected index of initial_data when model.narrow = [['stream', '7']]
    """
    diff = {'all_stream': defaultdict(set, {205: {537286}}),
            'all_private': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture
def index_topic(empty_index):
    """
    Expected index of initial_data when model.narrow = [['stream', '7'],
                                                        ['topic', 'Test']]
    """
    diff = {'stream': defaultdict(dict, {205: {'Test': {537286}}})}
    return dict(empty_index, **diff)


@pytest.fixture
def index_user(empty_index):
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                                         'boo@zulip.com'],
    """
    diff = {'private': defaultdict(set, {frozenset({5179, 5140}): {537287}}),
            'all_private': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture
def index_user_multiple(empty_index):
    """
    Expected index of initial_data when model.narrow = [['pm_with',
                                            'boo@zulip.com, bar@zulip.com'],
    """
    diff = {'private': defaultdict(set,
                                   {frozenset({5179, 5140, 5180}): {537288}}),
            'all_private': {537287, 537288}}
    return dict(empty_index, **diff)


@pytest.fixture(params=[
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def index_all_starred(empty_index, request):
    msgs_with_stars = request.param
    index = dict(empty_index, all_starred=msgs_with_stars,
                 all_private={537287, 537288})
    for msg_id, msg in index['messages'].items():
        if msg_id in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')
    return index


@pytest.fixture(scope="module")
def user_profile():
    return {
        'max_message_id': 589270,
        'short_name': 'FOO',
        'full_name': 'FOO BOO',
        'email': 'FOO@ZULIP.COM',
        'is_bot': False,
        'user_id': 5140,
        'result': 'success',
        'client_id': 'abcd',
        'msg': '',
        'is_admin': False,
        'pointer': 589234
    }


@pytest.fixture(scope="module")
def error_response():
    return {
        "msg": "Invalid API key",
        "result": "error"
    }


@pytest.fixture(scope="module")
def user_dict():
    """
    User_dict created according to `initial_data` fixture.
    """
    return {
        'FOOBOO@gmail.com': {
            'full_name': 'Tomás Farías',
            'email': 'FOOBOO@gmail.com',
            'status': 'active',
            'user_id': 5827
        },
        'nyan.salmon+sns@gmail.com': {
            'full_name': 'Jari Winberg',
            'email': 'nyan.salmon+sns@gmail.com',
            'status': 'idle',
            'user_id': 6086
        },
        'cloudserver2@hotmail.de': {
            'full_name': 'Test Account',
            'email': 'cloudserver2@hotmail.de',
            'status': 'idle',
            'user_id': 6085
        },
        'emailgateway@zulip.com': {
            'email': 'emailgateway@zulip.com',
            'full_name': 'Email Gateway',
            'status': 'idle',
            'user_id': 6
        },
        'feedback@zulip.com': {
            'email': 'feedback@zulip.com',
            'full_name': 'Zulip Feedback Bot',
            'status': 'idle',
            'user_id': 1
        },
        'notification-bot@zulip.com': {
            'email': 'notification-bot@zulip.com',
            'full_name': 'Notification Bot',
            'status': 'idle',
            'user_id': 5
        },
        'welcome-bot@zulip.com': {
            'email': 'welcome-bot@zulip.com',
            'full_name': 'Welcome Bot',
            'status': 'idle',
            'user_id': 4
        },
    }


@pytest.fixture(scope="module")
def user_list():
    """
    List of users created corresponding to
    `initial_data` fixture.
    """
    # NOTE These are sorted active > idle, then according to full_name
    return [{
        'full_name': 'Tomás Farías',
        'email': 'FOOBOO@gmail.com',
        'status': 'active',
        'user_id': 5827
    }, {
        'email': 'emailgateway@zulip.com',
        'full_name': 'Email Gateway',
        'status': 'idle',
        'user_id': 6
    }, {
        'full_name': 'Jari Winberg',
        'email': 'nyan.salmon+sns@gmail.com',
        'status': 'idle',
        'user_id': 6086
    }, {
        'email': 'notification-bot@zulip.com',
        'full_name': 'Notification Bot',
        'status': 'idle',
        'user_id': 5
    }, {
        'full_name': 'Test Account',
        'email': 'cloudserver2@hotmail.de',
        'status': 'idle',
        'user_id': 6085
    }, {
        'email': 'welcome-bot@zulip.com',
        'full_name': 'Welcome Bot',
        'status': 'idle',
        'user_id': 4
    }, {
        'email': 'feedback@zulip.com',
        'full_name': 'Zulip Feedback Bot',
        'status': 'idle',
        'user_id': 1
    }]


@pytest.fixture(scope="module")
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
