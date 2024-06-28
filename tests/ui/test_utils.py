from typing import Any, Iterable, List, Optional

import pytest
from pytest_mock import MockerFixture

from zulipterminal.api_types import Message
from zulipterminal.ui_tools.utils import create_msg_box_list, is_muted


MODULE = "zulipterminal.ui_tools.utils"


@pytest.mark.parametrize(
    "msg, narrow, muted_streams, is_muted_topic_return_value, muted",
    [
        (  # PM TEST
            {
                "type": "private",
                # ...
            },
            [],
            [1, 2],
            False,
            False,
        ),
        (
            {
                "type": "stream",
                # ...
            },
            [["stream", "foo"], ["topic", "boo"]],
            [1, 2],
            False,
            False,
        ),
        (
            {
                "type": "stream",
                "stream_id": 1,
                # ...
            },
            [["stream", "foo"]],
            [1, 2],
            False,
            True,
        ),
        (
            {
                "type": "stream",
                "stream_id": 2,
                # ...
            },
            [],
            [1, 2],
            True,
            True,
        ),
        (
            {
                "type": "stream",
                "stream_id": 3,
                "subject": "foo koo",
                # ...
            },
            [],
            [1, 2],
            False,
            False,
        ),
    ],
)
def test_is_muted(
    mocker: MockerFixture,
    msg: Message,
    narrow: List[Any],
    muted_streams: List[int],
    is_muted_topic_return_value: bool,
    muted: bool,
) -> None:
    model = mocker.Mock()
    model.is_muted_stream = mocker.Mock(
        return_value=(msg.get("stream_id", "") in muted_streams)
    )
    model.narrow = narrow
    model.is_muted_topic.return_value = is_muted_topic_return_value
    return_value = is_muted(msg, model)
    assert return_value is muted


@pytest.mark.parametrize(
    "narrow, messages, focus_msg_id, muted, unsubscribed, len_w_list",
    [
        (
            # No muted messages
            [],
            None,
            None,
            False,
            False,
            2,
        ),
        (
            # No muted messages
            [["stream", "foo"]],
            [1],
            None,
            False,
            False,
            1,
        ),
        (
            # No muted messages
            [["stream", "foo"]],
            [1],
            None,
            True,
            False,
            1,
        ),
        (
            # Don't show in 'All messages'
            [],
            [1],
            None,
            True,
            False,
            0,
        ),
        (
            # Unsubscribed messages
            [],
            [1],
            None,
            False,
            True,
            0,
        ),
    ],
)
def test_create_msg_box_list(
    mocker: MockerFixture,
    narrow: List[Any],
    messages: Optional[Iterable[Any]],
    focus_msg_id: Optional[int],
    muted: bool,
    unsubscribed: bool,
    len_w_list: int,
) -> None:
    model = mocker.Mock()
    model.narrow = narrow
    model.index = {
        "all_msg_ids": {1, 2},
        "messages": {
            1: {
                "id": 1,
                "flags": ["read"],
                "timestamp": 10,
            },
            2: {
                "id": 2,
                "flags": [],
                "timestamp": 10,
            },
        },
        "pointer": {},
        "muted_messages": {},
    }
    mocker.patch(MODULE + ".MessageBox")
    mocker.patch(MODULE + ".urwid.AttrMap", return_value="MSG")
    mock_muted = mocker.patch(MODULE + ".is_muted", return_value=muted)
    mocker.patch(
        MODULE + ".is_unsubscribed_message",
        return_value=unsubscribed,
    )

    return_value = create_msg_box_list(model, messages, focus_msg_id=focus_msg_id)

    assert len(return_value) == len_w_list
    assert mock_muted.called is not unsubscribed
