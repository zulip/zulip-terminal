from typing import Any, Dict, List

import pytest
from pytest import param as case

from zulipterminal.widget import find_widget_type, process_poll_widget


@pytest.mark.parametrize(
    "submessage, expected_widget_type",
    [
        case(
            [
                {
                    "id": 11897,
                    "message_id": 1954461,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": '
                    '{"question": "Sample Question?", "options": ["Yes", "No"]}}',
                },
                {
                    "id": 11898,
                    "message_id": 1954461,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_option","idx":1,"option":"Maybe"}',
                },
            ],
            "poll",
        ),
        case(
            [
                {
                    "id": 11899,
                    "message_id": 1954463,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "todo", "extra_data": '
                    '{"task_list_title": "Today\'s Tasks", "tasks": [{"task": '
                    '"Write code", "desc": ""}, {"task": "Sleep", "desc": ""}]}}',
                },
                {
                    "id": 11900,
                    "message_id": 1954463,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task","key":2,"task":"Eat","desc":"",'
                    '"completed":false}',
                },
            ],
            "todo",
        ),
        case([{}], "unknown"),
    ],
)
def test_find_widget_type(submessage: Any, expected_widget_type: str) -> None:
    widget_type = find_widget_type(submessage)

    assert widget_type == expected_widget_type


@pytest.mark.parametrize(
    "submessage, expected_poll_question, expected_options",
    [
        case(
            [
                {
                    "id": 12082,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": '
                    '{"question": "Do polls work on ZT?", "options": ["Yes", "No"]}}',
                },
                {
                    "id": 12083,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
                {
                    "id": 12084,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":-1}',
                },
                {
                    "id": 12085,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":1}',
                },
                {
                    "id": 12086,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
                {
                    "id": 12087,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":-1}',
                },
            ],
            "Do polls work on ZT?",
            {
                "canned,0": {"option": "Yes", "votes": [27294]},
                "canned,1": {"option": "No", "votes": []},
            },
            id="poll_widget_with_votes",
        ),
        case(
            [
                {
                    "id": 12089,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {"question": "Is '
                    'this a poll with options added later?", '
                    '"options": ["Yes", "No"]}}',
                },
                {
                    "id": 12090,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_option","idx":1,"option":"Maybe"}',
                },
                {
                    "id": 12091,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":1}',
                },
                {
                    "id": 12092,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":-1}',
                },
                {
                    "id": 12093,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"27294,1","vote":1}',
                },
                {
                    "id": 12094,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
            ],
            "Is this a poll with options added later?",
            {
                "canned,0": {"option": "Yes", "votes": [27294]},
                "canned,1": {"option": "No", "votes": []},
                "27294,1": {"option": "Maybe", "votes": [27294]},
            },
            id="poll_widget_with_new_option_and_votes",
        ),
        case(
            [
                {
                    "id": 12095,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {"question": '
                    '"Let\'s change this question later?", "options": ["Yes"]}}',
                },
                {
                    "id": 12096,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
                {
                    "id": 12097,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_option","idx":1,"option":"No"}',
                },
                {
                    "id": 12098,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":-1}',
                },
                {
                    "id": 12099,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"question",'
                    '"question":"Has this question stayed the same?"}',
                },
                {
                    "id": 12100,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"27294,1","vote":1}',
                },
            ],
            "Has this question stayed the same?",
            {
                "canned,0": {"option": "Yes", "votes": []},
                "27294,1": {"option": "No", "votes": [27294]},
            },
            id="poll_widget_with_new_question_and_votes",
        ),
        case(
            [
                {
                    "id": 12101,
                    "message_id": 1957693,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {"question": "",'
                    ' "options": ["Yes", "No"]}}',
                }
            ],
            "",
            {
                "canned,0": {"option": "Yes", "votes": []},
                "canned,1": {"option": "No", "votes": []},
            },
            id="poll_widget_with_empty_question",
        ),
        case(
            [
                {
                    "id": 12102,
                    "message_id": 1957700,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {'
                    '"question": "Does this poll have options?", "options": []}}',
                }
            ],
            "Does this poll have options?",
            {},
            id="poll_widget_with_empty_options",
        ),
        case(
            [
                {
                    "id": 12112,
                    "message_id": 1957722,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {"question": "",'
                    ' "options": []}}',
                }
            ],
            "",
            {},
            id="poll_widget_with_empty_question_and_options",
        ),
        case(
            [
                {
                    "id": 12103,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "poll", "extra_data": {"question": "'
                    'Does this poll have multiple voters?", "options": ["Yes", "No"]}}',
                },
                {
                    "id": 12104,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
                {
                    "id": 12105,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":1}',
                },
                {
                    "id": 12106,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":-1}',
                },
                {
                    "id": 12107,
                    "message_id": 1957719,
                    "sender_id": 32159,
                    "msg_type": "widget",
                    "content": '{"type":"new_option","idx":1,"option":"Maybe"}',
                },
                {
                    "id": 12108,
                    "message_id": 1957719,
                    "sender_id": 32159,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"32159,1","vote":1}',
                },
                {
                    "id": 12109,
                    "message_id": 1957719,
                    "sender_id": 32159,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
                {
                    "id": 12110,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,1","vote":-1}',
                },
                {
                    "id": 12111,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"vote","key":"canned,0","vote":1}',
                },
            ],
            "Does this poll have multiple voters?",
            {
                "canned,0": {"option": "Yes", "votes": [32159, 27294]},
                "canned,1": {"option": "No", "votes": []},
                "32159,1": {"option": "Maybe", "votes": [32159]},
            },
            id="poll_widget_with_multiple_voters",
        ),
    ],
)
def test_process_poll_widget(
    submessage: List[Dict[str, Any]],
    expected_poll_question: str,
    expected_options: Dict[str, Dict[str, Any]],
) -> None:
    poll_question, options = process_poll_widget(submessage)

    assert poll_question == expected_poll_question
    assert options == expected_options
