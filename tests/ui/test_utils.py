import pytest

from zulipterminal.ui_tools.utils import create_msg_box_list, is_muted


@pytest.mark.parametrize(['msg', 'narrow', 'muted_streams', 'muted_topics',
                          'muted'], [
    (   # PM TEST
        {
            'type': 'private',
            # ...
        },
        [],
        [1, 2],
        [
            ['foo', 'boo foo'],
            ['boo', 'foo boo'],
        ],
        False
    ),
    (
        {
            'type': 'stream',
            # ...
        },
        [['stream', 'foo'], ['topic', 'boo']],
        [1, 2],
        [
            ['foo', 'boo foo'],
            ['boo', 'foo boo'],
        ],
        False
    ),
    (
        {
            'type': 'stream',
            'stream_id': 1,
            # ...
        },
        [['stream', 'foo']],
        [1, 2],
        [
            ['foo', 'boo foo'],
            ['boo', 'foo boo'],
        ],
        True
    ),
    (
        {
            'type': 'stream',
            'stream_id': 2,
            'display_recipient': 'boo',
            'subject': 'foo boo',
            # ...
        },
        [],
        [1, 2],
        [
            ['foo', 'boo foo'],
            ['boo', 'foo boo'],
        ],
        True
    ),
    (
        {
            'type': 'stream',
            'stream_id': 3,
            'display_recipient': 'zoo',
            'subject': 'foo koo',
            # ...
        },
        [],
        [1, 2],
        [
            ['foo', 'boo foo'],
            ['boo', 'foo boo'],
        ],
        False
    ),
])
def test_is_muted(mocker, msg, narrow, muted_streams, muted_topics, muted):
    model = mocker.Mock()
    model.is_muted_stream = (
        mocker.Mock(return_value=(msg.get('stream_id', '') in muted_streams))
    )
    model.narrow = narrow
    model.muted_topics = muted_topics
    return_value = is_muted(msg, model)
    assert return_value is muted


@pytest.mark.parametrize(['narrow', 'messages', 'focus_msg_id', 'muted',
                          'unsubscribed', 'len_w_list'], [
    (
        # No muted messages
        [],
        None,
        None,
        False,
        False,
        2,
    ),
    (
        # No muted messages
        [['stream', 'foo']],
        [1],
        None,
        False,
        False,
        1,
    ),
    (
        # No muted messages
        [['stream', 'foo']],
        [1],
        None,
        True,
        False,
        1,
    ),
    (
        # Don't show in 'All messages'
        [],
        [1],
        None,
        True,
        False,
        0,
    ),
    (
        # Unsubscribed messages
        [],
        [1],
        None,
        False,
        True,
        0,
    ),

])
def test_create_msg_box_list(mocker, narrow, messages, focus_msg_id,
                             muted, unsubscribed, len_w_list):
    model = mocker.Mock()
    model.narrow = narrow
    model.index = {
        'all_msg_ids': {1, 2},
        'messages': {
            1: {
                'id': 1,
                'flags': ['read'],
                'timestamp': 10,
            },
            2: {
                'id': 2,
                'flags': [],
                'timestamp': 10,
            }
        },
        'pointer': {},
        }
    msg_box = mocker.patch('zulipterminal.ui_tools.utils.MessageBox')
    mocker.patch('zulipterminal.ui_tools.utils.urwid.AttrMap',
                 return_value='MSG')
    mocker.patch('zulipterminal.ui_tools.utils.is_muted', return_value=muted)
    mocker.patch('zulipterminal.ui_tools.utils.is_unsubscribed_message',
                 return_value=unsubscribed)
    return_value = create_msg_box_list(model, messages,
                                       focus_msg_id=focus_msg_id)
    assert len(return_value) == len_w_list
