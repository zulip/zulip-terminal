import pytest

from zulipterminal.helper import (
    index_messages,
)
from typing import Any


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
                          all_messages={537286, 537287, 537288})
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

    expected_index = dict(empty_index, all_private={537287, 537288},
                          all_starred=msgs_with_stars)
    for msg_id, msg in expected_index['messages'].items():
        if msg_id in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')

    assert index_messages(messages, model, model.index) == expected_index
