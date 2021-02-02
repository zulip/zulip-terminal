from typing import Any, Dict, List

from typing_extensions import Literal, TypedDict


EditPropagateMode = Literal['change_one', 'change_all', 'change_later']


class Message(TypedDict, total=False):
    id: int
    sender_id: int
    content: str
    recipient_id: int
    timestamp: int
    client: str
    subject: str  # Only for stream msgs.
    topic_links: List[str]
    is_me_message: bool
    reactions: List[Dict[str, Any]]
    submessages: List[Dict[str, Any]]
    flags: List[str]
    sender_full_name: str
    sender_short_name: str
    sender_email: str
    sender_realm_str: str
    display_recipient: Any
    type: str
    stream_id: int  # Only for stream msgs.
    avatar_url: str
    content_type: str
    match_content: str  # If keyword search specified in narrow params.
    match_subject: str  # If keyword search specified in narrow params.


class Event(TypedDict, total=False):  # Each Event will only have a subset
    type: str
    # typing:
    sender: Dict[str, Any]  # 'email', ...
    # typing & reaction:
    op: str
    # reaction:
    user: Dict[str, Any]  # 'email', 'user_id', 'full_name'
    reaction_type: str
    emoji_code: str
    emoji_name: str
    # reaction & update_message:
    message_id: int
    # update_message:
    rendered_content: str
    # update_message_flags:
    messages: List[int]
    operation: str  # NOTE: deprecated in Zulip 4.0 / ZFL 32 -> 'op'
    flag: str
    all: bool
    # message:
    message: Message
    flags: List[str]
    subject: str
    # subscription:
    property: str
    user_id: int  # Present when a streams subscribers are updated.
    user_ids: List[int]  # NOTE: replaces 'user_id' in ZFL 35
    stream_id: int
    stream_ids: List[int]  # NOTE: replaces 'stream_id' in ZFL 35 for peer*
    value: bool
    message_ids: List[int]  # Present when subject of msg(s) is updated
