from typing import Any, Dict, List, Union

from typing_extensions import Literal, TypedDict


EditPropagateMode = Literal['change_one', 'change_all', 'change_later']


class PrivateComposition(TypedDict):
    type: Literal['private']
    content: str
    to: List[str]  # emails  # TODO: Migrate to using List[int] (user ids)


class StreamComposition(TypedDict):
    type: Literal['stream']
    content: str
    to: str  # stream name  # TODO: Migrate to using int (stream id)
    subject: str  # TODO: Migrate to using topic


Composition = Union[PrivateComposition, StreamComposition]


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


class MessageEvent(TypedDict):
    type: Literal['message']
    message: Message
    flags: List[str]


class UpdateMessageEvent(TypedDict):
    type: Literal['update_message']
    message_id: int
    # FIXME: These groups of types are not always present
    # A: Content needs re-rendering
    rendered_content: str
    # B: Subject of these message ids needs updating?
    message_ids: List[int]
    subject: str
    stream_id: int


class ReactionEvent(TypedDict):
    type: Literal['reaction']
    op: str
    user: Dict[str, Any]  # 'email', 'user_id', 'full_name'
    reaction_type: str
    emoji_code: str
    emoji_name: str
    message_id: int


class SubscriptionEvent(TypedDict):
    type: Literal['subscription']
    op: str
    property: str

    user_id: int  # Present when a streams subscribers are updated.
    user_ids: List[int]  # NOTE: replaces 'user_id' in ZFL 35

    stream_id: int
    stream_ids: List[int]  # NOTE: replaces 'stream_id' in ZFL 35 for peer*

    value: bool
    message_ids: List[int]  # Present when subject of msg(s) is updated


class TypingEvent(TypedDict):
    type: Literal['typing']
    sender: Dict[str, Any]  # 'email', ...
    op: str


class UpdateMessageFlagsEvent(TypedDict):
    type: Literal['update_message_flags']
    messages: List[int]
    operation: str  # NOTE: deprecated in Zulip 4.0 / ZFL 32 -> 'op'
    op: str
    flag: str
    all: bool


class UpdateDisplaySettings(TypedDict):
    type: Literal['update_display_settings']
    setting_name: str
    setting: bool


Event = Union[
    MessageEvent,
    UpdateMessageEvent,
    ReactionEvent,
    SubscriptionEvent,
    TypingEvent,
    UpdateMessageFlagsEvent,
    UpdateDisplaySettings,
]
