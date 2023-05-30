import pytest

from zulipterminal.api_types import Message
from zulipterminal.server_url import encode_stream, near_message_url


@pytest.mark.parametrize(
    "stream_id, stream_name, expected_encoded_string",
    [
        (10, "zulip terminal", "10-zulip-terminal"),
        (12, "<strong>xss</strong>", "12-.3Cstrong.3Exss.3C.2Fstrong.3E"),
        (17, "#test-here #T1 #T2 #T3", "17-.23test-here-.23T1-.23T2-.23T3"),
        (27, ":party_parrot:", "27-.3Aparty_parrot.3A"),
        (44, "(ZT) % zulip ?/; &", "44-.28ZT.29-.25-zulip-.3F.2F.3B-.26"),
        (273, "abc + de = abcde", "273-abc-.2B-de-.3D-abcde"),
        (374, "/ in a stream name ?", "374-.2F-in-a-stream-name-.3F"),
    ],
)
def test_encode_stream(
    stream_id: int, stream_name: str, expected_encoded_string: str
) -> None:
    encoded_string = encode_stream(stream_id=stream_id, stream_name=stream_name)

    assert encoded_string == expected_encoded_string


@pytest.mark.parametrize(
    "server_url, msg, expected_message_url",
    [
        (
            "https://chat.zulip.org",
            {
                "id": 17252,
                "type": "stream",
                "stream_id": 23,
                "display_recipient": "zulip terminal",
                "subject": "#test-here #T1 #T2 #T3",
            },
            (
                "https://chat.zulip.org/#narrow/stream/23-zulip-terminal"
                "/topic/.23test-here.20.23T1.20.23T2.20.23T3/near/17252"
            ),
        ),
        (
            "https://foo-bar.co.in",
            {
                "id": 5412,
                "type": "stream",
                "stream_id": 425,
                "display_recipient": "/ in a stream name ?",
                "subject": "abc + de = abcde",
            },
            (
                "https://foo-bar.co.in/#narrow/stream/425-.2F-in-a-stream-name-.3F"
                "/topic/abc.20.2B.20de.20.3D.20abcde/near/5412"
            ),
        ),
        (
            "https://foo.bar.com",
            {
                "id": 24284,
                "type": "private",
                "display_recipient": [
                    {
                        "id": 12,
                    },
                    {
                        "id": 144,
                    },
                    {
                        "id": 249,
                    },
                ],
            },
            "https://foo.bar.com/#narrow/dm-with/12,144,249-dm/near/24284",
        ),
    ],
)
def test_near_message_url(
    server_url: str, msg: Message, expected_message_url: str
) -> None:
    message_url = near_message_url(server_url=server_url, message=msg)

    assert message_url == expected_message_url
