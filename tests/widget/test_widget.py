from typing import Dict, List, Union, cast

import pytest
from pytest import param as case

from zulipterminal.api_types import PollOption, Submessage
from zulipterminal.widget import (
    find_widget_type,
    process_poll_widget,
    process_todo_widget,
)


@pytest.mark.parametrize(
    "submessages, expected_widget_type",
    [
        case(
            [
                {
                    "id": 11897,
                    "message_id": 1954461,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": '
                        '{"question": "Sample Question?", "options": ["Yes", "No"]}}'
                    ),
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
                    "content": (
                        '{"widget_type": "todo", "extra_data": '
                        '{"task_list_title": "Today\'s Tasks", "tasks": [{"task": '
                        '"Write code", "desc": ""}, {"task": "Sleep", "desc": ""}]}}'
                    ),
                },
                {
                    "id": 11900,
                    "message_id": 1954463,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":2,"task":"Eat","desc":"",'
                        '"completed":false}'
                    ),
                },
            ],
            "todo",
        ),
        case([{}], "unknown"),
    ],
)
def test_find_widget_type(
    submessages: List[Submessage], expected_widget_type: str
) -> None:
    widget_type = find_widget_type(submessages)

    assert widget_type == expected_widget_type


@pytest.mark.parametrize(
    "submessages, expected_title, expected_tasks",
    [
        case(
            [
                {
                    "id": 11899,
                    "message_id": 1954463,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "todo", "extra_data": '
                        '{"task_list_title": "Today\'s Tasks", "tasks": [{"task": '
                        '"Write code", "desc": ""}, {"task": "Sleep", "desc": ""}]}}'
                    ),
                },
                {
                    "id": 11900,
                    "message_id": 1954463,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":2,"task":"Eat","desc":"",'
                        '"completed":false}'
                    ),
                },
            ],
            "Today's Tasks",
            {
                "0,canned": {"task": "Write code", "desc": "", "completed": False},
                "1,canned": {"task": "Sleep", "desc": "", "completed": False},
                "2,27294": {"task": "Eat", "desc": "", "completed": False},
            },
            id="title_and_unfinished_tasks",
        ),
        case(
            [
                {
                    "id": 11912,
                    "message_id": 1954626,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "todo", "extra_data": '
                        '{"task_list_title": "", "tasks": [{"task": "Hey", "desc": ""},'
                        ' {"task": "Hi", "desc": ""}]}}'
                    ),
                }
            ],
            "Task list",
            {
                "0,canned": {"task": "Hey", "desc": "", "completed": False},
                "1,canned": {"task": "Hi", "desc": "", "completed": False},
            },
            id="no_title_and_unfinished_tasks",
        ),
        case(
            [
                {
                    "id": 11919,
                    "message_id": 1954843,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "todo", "extra_data": '
                        '{"task_list_title": "", "tasks": []}}'
                    ),
                }
            ],
            "Task list",
            {},
            id="no_title_or_tasks",
        ),
        case(
            [
                {
                    "id": 11932,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "todo", "extra_data": '
                        '{"task_list_title": "", "tasks": []}}'
                    ),
                },
                {
                    "id": 11933,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":2,"task":"Write code",'
                        '"desc":"Make the todo ZT PR!","completed":false}'
                    ),
                },
                {
                    "id": 11934,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":4,"task":"Sleep",'
                        '"desc":"at least 8 hours a day","completed":false}'
                    ),
                },
                {
                    "id": 11935,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":6,"task":"Eat",'
                        '"desc":"3 meals a day","completed":false}'
                    ),
                },
                {
                    "id": 11936,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task","key":8,"task":"Exercise",'
                        '"desc":"an hour a day","completed":false}'
                    ),
                },
                {
                    "id": 11937,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"2,27294"}',
                },
                {
                    "id": 11938,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"2,27294"}',
                },
                {
                    "id": 11939,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"4,27294"}',
                },
                {
                    "id": 11940,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"6,27294"}',
                },
                {
                    "id": 11941,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"8,27294"}',
                },
                {
                    "id": 11942,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"2,27294"}',
                },
                {
                    "id": 11943,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"4,27294"}',
                },
                {
                    "id": 11944,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"6,27294"}',
                },
                {
                    "id": 11945,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"4,27294"}',
                },
                {
                    "id": 11946,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"8,27294"}',
                },
            ],
            "Task list",
            {
                "2,27294": {
                    "task": "Write code",
                    "desc": "Make the todo ZT PR!",
                    "completed": True,
                },
                "4,27294": {
                    "task": "Sleep",
                    "desc": "at least 8 hours a day",
                    "completed": True,
                },
                "6,27294": {"task": "Eat", "desc": "3 meals a day", "completed": False},
                "8,27294": {
                    "task": "Exercise",
                    "desc": "an hour a day",
                    "completed": False,
                },
            },
            id="title_and_description_and_finished_tasks",
        ),
        case(
            [
                {
                    "id": 12143,
                    "message_id": 1958318,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "todo", "extra_data": {'
                        '"task_list_title": "Today\'s Work", "tasks": [{"task": '
                        '"Update todo titles on ZT", "desc": ""}, '
                        '{"task": "Push todo update", "desc": ""}]}}'
                    ),
                },
                {
                    "id": 12144,
                    "message_id": 1958318,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"type":"new_task_list_title",'
                        '"title":"Today\'s Work [Updated]"}'
                    ),
                },
                {
                    "id": 12145,
                    "message_id": 1958318,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"strike","key":"0,canned"}',
                },
            ],
            "Today's Work [Updated]",
            {
                "0,canned": {
                    "task": "Update todo titles on ZT",
                    "desc": "",
                    "completed": True,
                },
                "1,canned": {
                    "task": "Push todo update",
                    "desc": "",
                    "completed": False,
                },
            },
            id="updated_title_and_finished_tasks",
        ),
    ],
)
def test_process_todo_widget(
    submessages: List[Submessage],
    expected_title: str,
    expected_tasks: Dict[str, Dict[str, Union[str, bool]]],
) -> None:
    result = process_todo_widget(submessages)

    assert result["title"] == expected_title
    assert result["tasks"] == expected_tasks


@pytest.mark.parametrize(
    "submessages, expected_poll_question, expected_options",
    [
        case(
            [
                {
                    "id": 12082,
                    "message_id": 1957499,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {'
                        '"question": "Do polls work on ZT?", "options": ["Yes", "No"]}}'
                    ),
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
            id="multiple_vote_events",
        ),
        case(
            [
                {
                    "id": 12089,
                    "message_id": 1957662,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {"question": "Is '
                        'this a poll with options added later?", '
                        '"options": ["Yes", "No"]}}'
                    ),
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
            id="new_option_and_votes",
        ),
        case(
            [
                {
                    "id": 12095,
                    "message_id": 1957682,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {"question": '
                        '"Let\'s change this question later?", "options": ["Yes"]}}'
                    ),
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
            id="new_question_and_votes",
        ),
        case(
            [
                {
                    "id": 12101,
                    "message_id": 1957693,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {"question": "",'
                        ' "options": ["Yes", "No"]}}'
                    ),
                }
            ],
            "",
            {
                "canned,0": {"option": "Yes", "votes": []},
                "canned,1": {"option": "No", "votes": []},
            },
            id="empty_question",
        ),
        case(
            [
                {
                    "id": 12102,
                    "message_id": 1957700,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {'
                        '"question": "Does this poll have options?", "options": []}}'
                    ),
                }
            ],
            "Does this poll have options?",
            {},
            id="empty_options",
        ),
        case(
            [
                {
                    "id": 12112,
                    "message_id": 1957722,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {"question": "",'
                        ' "options": []}}'
                    ),
                }
            ],
            "",
            {},
            id="empty_question_and_options",
        ),
        case(
            [
                {
                    "id": 12103,
                    "message_id": 1957719,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": (
                        '{"widget_type": "poll", "extra_data": {"question": "Does'
                        ' this poll have multiple voters?", "options": ["Yes", "No"]}}'
                    ),
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
            id="multiple_voters",
        ),
    ],
)
def test_process_poll_widget(
    submessages: List[Submessage],
    expected_poll_question: str,
    expected_options: Dict[str, Dict[str, Union[str, List[str]]]],
) -> None:
    result = process_poll_widget(submessages)

    assert result["question"] == expected_poll_question
    assert result["options"] == cast(Dict[str, PollOption], expected_options)
