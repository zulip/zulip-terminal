from typing import Any

import pytest

import zulipterminal.helper
from zulipterminal.helper import (
    canonicalize_color, classify_unread_counts, index_messages, notify,
    powerset,
)


def test_index_messages_narrow_all_messages(mocker,
                                            messages_successful_response,
                                            index_all_messages,
                                            initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = []
    assert index_messages(messages, model, model.index) == index_all_messages


def test_index_messages_narrow_stream(mocker,
                                      messages_successful_response,
                                      index_stream,
                                      initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['stream', 'PTEST']]
    model.is_search_narrow.return_value = False
    model.stream_id = 205
    assert index_messages(messages, model, model.index) == index_stream


def test_index_messages_narrow_topic(mocker,
                                     messages_successful_response,
                                     index_topic,
                                     initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['stream', '7'],
                    ['topic', 'Test']]
    model.is_search_narrow.return_value = False
    model.stream_id = 205
    assert index_messages(messages, model, model.index) == index_topic


def test_index_messages_narrow_user(mocker,
                                    messages_successful_response,
                                    index_user,
                                    initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['pm_with', 'boo@zulip.com']]
    model.is_search_narrow.return_value = False
    model.user_id = 5140
    model.user_dict = {
        'boo@zulip.com': {
            'user_id': 5179,
        }
    }
    assert index_messages(messages, model, model.index) == index_user


def test_index_messages_narrow_user_multiple(mocker,
                                             messages_successful_response,
                                             index_user_multiple,
                                             initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['pm_with', 'boo@zulip.com, bar@zulip.com']]
    model.is_search_narrow.return_value = False
    model.user_id = 5140
    model.user_dict = {
        'boo@zulip.com': {
            'user_id': 5179,
        },
        'bar@zulip.com': {
            'user_id': 5180
        }
    }
    assert index_messages(messages, model, model.index) == index_user_multiple


@pytest.mark.parametrize('edited_msgs', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_edited_message(mocker,
                              messages_successful_response,
                              empty_index,
                              edited_msgs,
                              initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in edited_msgs:
            msg['edit_history'] = []
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = []

    expected_index = dict(empty_index, edited_messages=edited_msgs,
                          all_msg_ids={537286, 537287, 537288})
    for msg_id, msg in expected_index['messages'].items():
        if msg_id in edited_msgs:
            msg['edit_history'] = []

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('msgs_with_stars', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_starred(mocker,
                       messages_successful_response,
                       empty_index,
                       msgs_with_stars,
                       initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')

    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['is', 'starred']]
    model.is_search_narrow.return_value = False
    expected_index = dict(empty_index, private_msg_ids={537287, 537288},
                          starred_msg_ids=msgs_with_stars)
    for msg_id, msg in expected_index['messages'].items():
        if msg_id in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('mentioned_messages', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_mentioned_messages(mocker,
                                  messages_successful_response,
                                  empty_index,
                                  mentioned_messages,
                                  initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in mentioned_messages and 'mentioned' not in msg['flags']:
            msg['flags'].append('mentioned')

    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['is', 'mentioned']]
    model.is_search_narrow.return_value = False
    expected_index = dict(empty_index, private_msg_ids={537287, 537288},
                          mentioned_msg_ids=mentioned_messages)

    for msg_id, msg in expected_index['messages'].items():
        if msg_id in mentioned_messages and 'mentioned' not in msg['flags']:
            msg['flags'].append('mentioned')

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('iterable, map_func, expected_powerset', [
    ([], set, [set()]),
    ([1], set, [set(), {1}]),
    ([1, 2], set, [set(), {1}, {2}, {1, 2}]),
    ([1, 2, 3], set,
     [set(), {1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}]),
    ([1, 2], tuple, [(), (1,), (2,), (1, 2)]),
])
def test_powerset(iterable, map_func, expected_powerset):
    assert powerset(iterable, map_func) == expected_powerset


@pytest.mark.parametrize('muted_streams, muted_topics, vary_in_unreads', [
    ([99], [['Some general stream', 'Some general unread topic']], {
        'all_msg': 9,
        'streams': {99: 1},
        'unread_topics': {(99, 'Some private unread topic'): 1},
        'all_mentions': 0,
    }),
    ([1000], [['Secret stream', 'Some private unread topic']], {
        'all_msg': 11,
        'streams': {1000: 3},
        'unread_topics': {(1000, 'Some general unread topic'): 3},
        'all_mentions': 0,
    }),
    ([1], [], {'all_mentions': 0})
], ids=['mute_private_stream_mute_general_stream_topic',
        'mute_general_stream_mute_private_stream_topic',
        'no_mute_some_other_stream_muted']
)
def test_classify_unread_counts(mocker, initial_data, stream_dict,
                                classified_unread_counts, muted_topics,
                                muted_streams, vary_in_unreads):
    model = mocker.Mock()
    model.stream_dict = stream_dict
    model.initial_data = initial_data
    model.muted_topics = muted_topics
    model.muted_streams = muted_streams
    assert classify_unread_counts(model) == dict(classified_unread_counts,
                                                 **vary_in_unreads)


@pytest.mark.parametrize('color', [
    '#ffffff', '#f0f0f0', '#f0f1f2', '#fff', '#FFF', '#F3F5FA'
])
def test_color_formats(mocker, color):
    canon = canonicalize_color(color)
    assert canon == '#fff'


@pytest.mark.parametrize('color', [
    '#', '#f', '#ff', '#ffff', '#fffff', '#fffffff', '#abj', '#398a0s'
])
def test_invalid_color_format(mocker, color):
    with pytest.raises(ValueError) as e:
        canon = canonicalize_color(color)
    assert str(e.value) == 'Unknown format for color "{}"'.format(color)


@pytest.mark.parametrize('OS, is_notification_sent', [
    ([True, False, False], True),  # OS: [WSL, MACOS, LINUX]
    ([False, True, False], True),
    ([False, False, True], True),
    ([False, False, False], False),  # Unsupported OS
])
def test_notify(mocker, OS, is_notification_sent):
    title = "Author"
    text = "Hello!"
    mocker.patch('zulipterminal.helper.WSL', OS[0])
    mocker.patch('zulipterminal.helper.MACOS', OS[1])
    mocker.patch('zulipterminal.helper.LINUX', OS[2])
    subprocess = mocker.patch('zulipterminal.helper.subprocess')
    notify(title, text)
    assert subprocess.run.called == is_notification_sent


@pytest.mark.parametrize('text', [
    "x", "Spaced text.", "'", '"'
], ids=["x", "spaced_text", "single", "double"])
@pytest.mark.parametrize('title', [
    "X", 'Spaced title', "'", '"'
], ids=["X", "spaced_title", "single", "double"])
@pytest.mark.parametrize('OS, cmd_length', [
    ('LINUX', 3),
    ('MACOS', 3),
    ('WSL', 2)
])
def test_notify_quotes(monkeypatch, mocker,
                       OS, cmd_length, title, text):
    subprocess = mocker.patch('zulipterminal.helper.subprocess')

    for os in ('LINUX', 'MACOS', 'WSL'):
        if os != OS:
            monkeypatch.setattr(zulipterminal.helper, os, False)
        else:
            monkeypatch.setattr(zulipterminal.helper, os, True)

    notify(title, text)

    params = subprocess.run.call_args_list
    assert len(params) == 1  # One external run call
    assert len(params[0][0][0]) == cmd_length

    # NOTE: If there is a quoting error, we may get a ValueError too
