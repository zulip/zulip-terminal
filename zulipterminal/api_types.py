from typing import Any, Dict, List, Optional, Union

from typing_extensions import Literal, TypedDict

# These are documented in the zulip package (python-zulip-api repo)
from zulip import EditPropagateMode  # one/all/later
from zulip import EmojiType  # [unicode/realm/zulip_extra + _emoji]
from zulip import MessageFlag  # superset of below, may only be changed indirectly
from zulip import ModifiableMessageFlag  # directly modifiable read/starred/collapsed


RESOLVED_TOPIC_PREFIX = "✔ "


class PrivateComposition(TypedDict):
    type: Literal["private"]
    content: str
    to: List[int]  # User ids


class StreamComposition(TypedDict):
    type: Literal["stream"]
    content: str
    to: str  # stream name  # TODO: Migrate to using int (stream id)
    subject: str  # TODO: Migrate to using topic


Composition = Union[PrivateComposition, StreamComposition]


class Message(TypedDict, total=False):
    id: int
    sender_id: int
    content: str
    timestamp: int
    client: str
    subject: str  # Only for stream msgs.
    # NOTE: new in Zulip 3.0 / ZFL 1, replacing `subject_links`
    # NOTE: API response format of `topic_links` changed in Zulip 4.0 / ZFL 46
    topic_links: List[Any]
    # NOTE: `subject_links` in Zulip 2.1; deprecated from Zulip 3.0 / ZFL 1
    subject_links: List[str]
    is_me_message: bool
    reactions: List[Dict[str, Any]]
    submessages: List[Dict[str, Any]]
    flags: List[MessageFlag]
    sender_full_name: str
    sender_email: str
    sender_realm_str: str
    display_recipient: Any
    type: str
    stream_id: int  # Only for stream msgs.
    avatar_url: str
    content_type: str
    match_content: str  # If keyword search specified in narrow params.
    match_subject: str  # If keyword search specified in narrow params.

    # Unused/Unsupported fields
    # NOTE: Deprecated; a server implementation detail not useful in a client.
    # recipient_id: int
    # NOTE: Removed from Zulip 3.1 / ZFL 26; unused before that.
    # sender_short_name: str


# Elements and types taken from https://zulip.com/api/get-events
class Subscription(TypedDict):
    stream_id: int
    name: str
    description: str
    rendered_description: str
    date_created: int  # NOTE: new in Zulip 4.0 / ZFL 30
    invite_only: bool
    subscribers: List[int]
    desktop_notifications: Optional[bool]
    email_notifications: Optional[bool]
    wildcard_mentions_notify: Optional[bool]
    push_notifications: Optional[bool]
    audible_notifications: Optional[bool]
    pin_to_top: bool
    email_address: str

    is_muted: bool  # NOTE: new in Zulip 2.1 (in_home_view still present)
    in_home_view: bool  # TODO: Migrate to is_muted (note inversion)

    is_announcement_only: bool  # Deprecated in Zulip 3.0 -> stream_post_policy
    stream_post_policy: int  # NOTE: new in Zulip 3.0 / ZFL 1

    is_web_public: bool
    role: int  # NOTE: new in Zulip 4.0 / ZFL 31
    color: str
    message_retention_days: Optional[int]  # NOTE: new in Zulip 3.0 / ZFL 17
    history_public_to_subscribers: bool
    first_message_id: Optional[int]
    stream_weekly_traffic: Optional[int]


class RealmUser(TypedDict):
    user_id: int
    full_name: str
    email: str

    # Present in most cases, but these only in /users/me from Zulip 3.0 (ZFL 10):
    timezone: str
    date_joined: str

    avatar_url: str  # Absent depending on server/capability-field (Zulip 3.0/ZFL 18+)
    avatar_version: int  # NOTE: new in Zulip 3.0 [(ZFL 6) (ZFL 10)]

    is_bot: bool
    # These are only meaningfully (or literally) present for bots (ie. is_bot==True)
    bot_type: Optional[int]
    bot_owner_id: int  # NOTE: new in Zulip 3.0 (ZFL 1) - None for old bots
    bot_owner: str  # (before ZFL 1; containing email field of owner instead)

    is_billing_admin: bool  # NOTE: new in Zulip 5.0 (ZFL 73)

    # If role is present, prefer it to the other is_* fields below
    role: int  # NOTE: new in Zulip 4.0 (ZFL 59)
    is_owner: bool  # NOTE: new in Zulip 3.0 [/users/* (ZFL 8); /register (ZFL 11)]
    is_admin: bool
    is_guest: bool  # NOTE: added /users/me ZFL 10; other changes before that

    # To support in future:
    # profile_data: Dict  # NOTE: Only if requested
    # is_active: bool  # NOTE: Dependent upon realm_users vs realm_non_active_users
    # delivery_email: str  # NOTE: Only available if admin, and email visibility limited

    # Occasionally present or deprecated fields
    # is_moderator: bool  # NOTE: new in Zulip 4.0 (ZFL 60) - ONLY IN REGISTER RESPONSE
    # is_cross_realm_bot: bool  # NOTE: Only for cross-realm bots
    # max_message_id: int  # NOTE: DEPRECATED & only for /users/me


class MessageEvent(TypedDict):
    type: Literal["message"]
    message: Message
    flags: List[MessageFlag]


class UpdateMessageEvent(TypedDict):
    type: Literal["update_message"]
    message_id: int
    # FIXME: These groups of types are not always present
    # A: Content needs re-rendering
    rendered_content: str
    # B: Subject of these message ids needs updating?
    message_ids: List[int]
    orig_subject: str
    subject: str
    propagate_mode: EditPropagateMode
    stream_id: int


class ReactionEvent(TypedDict):
    type: Literal["reaction"]
    op: str
    user: Dict[str, Any]  # 'email', 'user_id', 'full_name'
    reaction_type: EmojiType
    emoji_code: str
    emoji_name: str
    message_id: int


class SubscriptionEvent(TypedDict):
    type: Literal["subscription"]
    op: str
    property: str

    user_id: int  # Present when a streams subscribers are updated.
    user_ids: List[int]  # NOTE: replaces 'user_id' in ZFL 35

    stream_id: int
    stream_ids: List[int]  # NOTE: replaces 'stream_id' in ZFL 35 for peer*

    value: bool
    message_ids: List[int]  # Present when subject of msg(s) is updated


class TypingEvent(TypedDict):
    type: Literal["typing"]
    sender: Dict[str, Any]  # 'email', ...
    op: str


class UpdateMessageFlagsEvent(TypedDict):
    type: Literal["update_message_flags"]
    messages: List[int]
    operation: str  # NOTE: deprecated in Zulip 4.0 / ZFL 32 -> 'op'
    op: str
    flag: ModifiableMessageFlag
    all: bool


class UpdateDisplaySettings(TypedDict):
    type: Literal["update_display_settings"]
    setting_name: str
    setting: bool


class RealmEmojiData(TypedDict):
    id: str
    name: str
    source_url: str
    deactivated: bool
    # Previous versions had an author object with an id field.
    author_id: int  # NOTE: new in Zulip 3.0 / ZFL 7.


class UpdateRealmEmojiEvent(TypedDict):
    type: Literal["realm_emoji"]
    realm_emoji: Dict[str, RealmEmojiData]


# This is specifically only those supported by ZT
SupportedUserSettings = Literal["send_private_typing_notifications"]


class UpdateUserSettingsEvent(TypedDict):
    type: Literal["user_settings"]
    op: Literal["update"]
    property: SupportedUserSettings
    value: Any


# This is specifically only those supported by ZT
SupportedGlobalNotificationSettings = Literal["pm_content_in_desktop_notifications"]


class UpdateGlobalNotificationsEvent(TypedDict):
    type: Literal["update_global_notifications"]
    notification_name: SupportedGlobalNotificationSettings
    setting: Any


Event = Union[
    MessageEvent,
    UpdateMessageEvent,
    ReactionEvent,
    SubscriptionEvent,
    TypingEvent,
    UpdateMessageFlagsEvent,
    UpdateDisplaySettings,
    UpdateRealmEmojiEvent,
    UpdateUserSettingsEvent,
    UpdateGlobalNotificationsEvent,
]
