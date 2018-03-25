from zulipterminal.helper import (
    update_flag,
)
from typing import Any


def test_update_flag(mocker: Any) -> None:
    mock_client = mocker.patch('zulip.Client')
    mock_api_query = mocker.patch('zulip.Client.do_api_query')
    update_flag([1, 2], mock_client)
    mock_api_query.assert_called_once_with(
        {'flag': 'read', 'messages': [1, 2], 'op': 'add'},
        '/json/messages/flags',
        method='POST'
    )


def test_update_flag_empty_msg_list(mocker: Any) -> None:
    assert update_flag([], mocker.patch('zulip.Client')) is None
