from zulipterminal.helper import (
    update_flag,
    index_messages,
)
from typing import Any


def test_update_flag(mocker: Any) -> None:
    mock_controller = mocker.patch('zulipterminal.core.Controller')
    mock_api_query = mocker.patch('zulipterminal.core.Controller'
                                  '.client.do_api_query')
    update_flag([1, 2], mock_controller)
    mock_api_query.assert_called_once_with(
        {'flag': 'read', 'messages': [1, 2], 'op': 'add'},
        '/json/messages/flags',
        method='POST'
    )


def test_update_flag_empty_msg_list(mocker: Any) -> None:
    assert update_flag([], mocker.patch('zulip.Client')) is None


def test_index_messages_narrow_all_messages(mocker,
                                            messages_successful_response,
                                            index_all_messages) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.narrow = []
    assert index_messages(messages, model) == index_all_messages


def test_index_messages_narrow_stream(mocker,
                                      messages_successful_response,
                                      index_stream) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.narrow = [['stream', 'PTEST']]
    model.stream_id = 205
    assert index_messages(messages, model) == index_stream


def test_index_messages_narrow_topic(mocker,
                                     messages_successful_response,
                                     index_topic) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.narrow = [['stream', '7'],
                    ['topic', 'Test']]
    model.stream_id = 205
    assert index_messages(messages, model) == index_topic


def test_index_messages_narrow_user(mocker,
                                    messages_successful_response,
                                    index_user):
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.narrow = [['pm_with', 'boo@zulip.com']]
    model.user_id = 5140
    model.user_dict = {
        'boo@zulip.com': {
            'user_id': 5179,
        }
    }
    assert index_messages(messages, model) == index_user
