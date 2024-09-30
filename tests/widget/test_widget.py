from typing import Any

import pytest
from pytest import param as case

from zulipterminal.widget import find_widget_type


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
