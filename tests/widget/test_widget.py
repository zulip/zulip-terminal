from typing import Any, Dict

import pytest
from pytest import param as case

from zulipterminal.widget import find_widget_type, process_todo_widget


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
    "submessage, expected_title, expected_tasks",
    [
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
            "Today's Tasks",
            {
                "0,canned": {"task": "Write code", "desc": "", "completed": False},
                "1,canned": {"task": "Sleep", "desc": "", "completed": False},
                "2,27294": {"task": "Eat", "desc": "", "completed": False},
            },
            id="todo_with_title_and_unfinished_tasks",
        ),
        case(
            [
                {
                    "id": 11912,
                    "message_id": 1954626,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "todo", "extra_data": '
                    '{"task_list_title": "", "tasks": [{"task": "Hey", "desc": ""}, '
                    '{"task": "Hi", "desc": ""}]}}',
                }
            ],
            "Task list",
            {
                "0,canned": {"task": "Hey", "desc": "", "completed": False},
                "1,canned": {"task": "Hi", "desc": "", "completed": False},
            },
            id="todo_without_title_and_unfinished_tasks",
        ),
        case(
            [
                {
                    "id": 11919,
                    "message_id": 1954843,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "todo", "extra_data": '
                    '{"task_list_title": "", "tasks": []}}',
                }
            ],
            "Task list",
            {},
            id="todo_without_title_or_tasks",
        ),
        case(
            [
                {
                    "id": 11932,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "todo", "extra_data": '
                    '{"task_list_title": "", "tasks": []}}',
                },
                {
                    "id": 11933,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task","key":2,"task":"Write code",'
                    '"desc":"Make the todo ZT PR!","completed":false}',
                },
                {
                    "id": 11934,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task","key":4,"task":"Sleep",'
                    '"desc":"at least 8 hours a day","completed":false}',
                },
                {
                    "id": 11935,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task","key":6,"task":"Eat",'
                    '"desc":"3 meals a day","completed":false}',
                },
                {
                    "id": 11936,
                    "message_id": 1954847,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task","key":8,"task":"Exercise",'
                    '"desc":"an hour a day","completed":false}',
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
            id="todo_with_title_and_description_and_some_tasks_completed",
        ),
        case(
            [
                {
                    "id": 12143,
                    "message_id": 1958318,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"widget_type": "todo", "extra_data": {'
                    '"task_list_title": "Today\'s Work", "tasks": [{"task": '
                    '"Update todo titles on ZT", "desc": ""}, '
                    '{"task": "Push todo update", "desc": ""}]}}',
                },
                {
                    "id": 12144,
                    "message_id": 1958318,
                    "sender_id": 27294,
                    "msg_type": "widget",
                    "content": '{"type":"new_task_list_title",'
                    '"title":"Today\'s Work [Updated]"}',
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
            id="todo_with_updated_title_and_some_tasks_completed",
        ),
    ],
)
def test_process_todo_widget(
    submessage: Any, expected_title: str, expected_tasks: Dict[str, Dict[str, Any]]
) -> None:
    title, tasks = process_todo_widget(submessage)

    assert title == expected_title
    assert tasks == expected_tasks
