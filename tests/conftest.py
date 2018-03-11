import pytest

@pytest.fixture(scope='module')
def messages_successful_response():
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
            'avatar_url': '/user_avatars/2/82af23cd4daa74c904fe3352c8b5a3dc07a62853.png?x=x&version=2'
                ,
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
            'avatar_url': '/user_avatars/2/82af23cd4daa74c904fe3352c8b5a3dc07a62853.png?x=x&version=2'
                ,
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
def classified_message():
    """
    Classified messages for `messages_successful_response` fixture.
    """
    return {
        205: [{
        'type': 'stream',
        'title': 'Test',
        'content': 'Stream content here.',
        'color': None,
        'sender_email': 'foo@zulip.com',
        'stream': 'PTEST',
        'time': 1520918722,
        'sender': 'Foo Foo',
        'id': 537286,
        }],
        'boo@zulip.com': [{
        'type': 'private',
        'title': '',
        'content': 'Hey PM content here.',
        'color': None,
        'sender_email': 'foo@zulip.com',
        'stream': [{
            'email': 'boo@zulip.com',
            'full_name': 'Boo Boo',
            'id': 5179,
            'is_mirror_dummy': False,
            'short_name': 'boo',
            }, {
            'email': 'foo@zulip.com',
            'full_name': 'Foo Foo',
            'id': 5140,
            'is_mirror_dummy': False,
            'short_name': 'foo',
            }],
        'time': 1520918736,
        'sender': 'You and Boo Boo',
        'id': 537287,
        }]
    }

@pytest.fixture(scope='module')
def user_email():
    """
    Email of the user running zulip-terminal.
    """
    return 'foo@zulip.com'
