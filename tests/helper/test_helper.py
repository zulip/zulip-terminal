from zulipterminal.helper import classify_message


def test_classify_message(user_email, messages_successful_response,
                          classified_message):
    result = classify_message(user_email,
                              messages_successful_response['messages'])
    assert result == classified_message
