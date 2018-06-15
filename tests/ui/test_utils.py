import pytest
from zulipterminal.ui_tools.utils import is_muted


@pytest.mark.parametrize('msg, narrow, muted_streams, muted_topics,\
                         muted', [
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
    model.narrow = narrow
    model.muted_streams = muted_streams
    model.muted_topics = muted_topics
    return_value = is_muted(msg, model)
    assert return_value is muted
