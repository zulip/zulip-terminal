from zulipterminal.helper import (
    classify_message,
    update_flag,
)


def test_classify_message(user_email, messages_successful_response,
                          classified_message):
    result = classify_message(user_email,
                              messages_successful_response['messages'])
    assert result == classified_message


def test_update_flag(mocker):
    mock_client = mocker.patch('zulip.Client')
    mock_api_query = mocker.patch('zulip.Client.do_api_query')
    update_flag([1, 2], mock_client)
    mock_api_query.assert_called_once_with(
        {'flag': 'read', 'messages': [1, 2], 'op': 'add'},
        '/json/messages/flags',
        method='POST'
    )


def test_update_flag_empty_msg_list(mocker):
    assert update_flag([], mocker.patch('zulip.Client')) is None
