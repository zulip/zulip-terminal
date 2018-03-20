import pytest
from typing import Any, List, Dict


@pytest.fixture(scope='module')
def messages_successful_response() -> Dict[str, List[Dict[str, Any]]]:
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
            }],
        'result': 'success',
        'msg': '',
    }
    return response


@pytest.fixture(scope='module')
def classified_message() -> Dict[Any, List[Dict[str, Any]]]:
    """
    Classified messages for `messages_successful_response` fixture.
    """
    return {
        205: [{
            'type': 'stream',
            'title': 'Test',
            'stream': 'PTEST',
            'sender': 'Foo Foo',
            'sender_email': 'foo@zulip.com',
            'id': 537286,
            'stream_id': 205,
            'time': 1520918722,
            'content': 'Stream content here.',
            'color': None
        }],
        'boo@zulip.com': [{
            'type': 'private',
            'title': '',
            'stream': [{
                'id': 5179,
                'full_name': 'Boo Boo',
                'email': 'boo@zulip.com',
                'is_mirror_dummy': False,
                'short_name': 'boo'
            }, {
                'id': 5140,
                'full_name': 'Foo Foo',
                'email': 'foo@zulip.com',
                'is_mirror_dummy': False,
                'short_name': 'foo'
            }],
            'sender': 'You and Boo Boo',
            'sender_email': 'foo@zulip.com',
            'id': 537287,
            'stream_id': 'boo@zulip.com',
            'time': 1520918736,
            'content': 'Hey PM content here.',
            'color': None
        }]
    }


@pytest.fixture(scope='module')
def user_email() -> str:
    """
    Email of the user running zulip-terminal.
    """
    return 'foo@zulip.com'
