"""
Types from the Zulip API, translated into python, to improve type checking
"""
# NOTE: Only modify this file if it leads to a better match to the types used
#       in the API at http://zulip.com/api

from typing import Any, Dict, List, Optional, Union

from typing_extensions import Final, Literal, NotRequired, TypedDict, final

# These are documented in the zulip package (python-zulip-api repo)
from zulip import EditPropagateMode  # one/all/later
from zulip import EmojiType  # [unicode/realm/zulip_extra + _emoji]
from zulip import MessageFlag  # superset of below, may only be changed indirectly
from zulip import ModifiableMessageFlag  # directly modifiable read/starred/collapsed


RESOLVED_TOPIC_PREFIX = "✔ "

###############################################################################
# These values are in the register response from ZFL 53
# Before this feature level, they had the listed default (fixed) values
# (strictly, the stream value was available, under a different name)

MAX_STREAM_NAME_LENGTH: Final = 60
MAX_TOPIC_NAME_LENGTH: Final = 60
MAX_MESSAGE_LENGTH: Final = 10000


###############################################################################
# Core message types (used in Composition and Message below)

DirectMessageString = Literal["private"]
StreamMessageString = Literal["stream"]

MessageType = Union[DirectMessageString, StreamMessageString]


###############################################################################
# Parameters to pass in request to:
#   https://zulip.com/api/set-typing-status
# Refer to the top of that page for the expected protocol clients should observe
#
# NOTE: `to` field could be email until ZFL 11/3.0; ids were possible from 2.0+

# Timing parameters for when notifications should occur
TYPING_STARTED_WAIT_PERIOD: Final = 10
TYPING_STOPPED_WAIT_PERIOD: Final = 5
TYPING_STARTED_EXPIRY_PERIOD: Final = 15  # TODO: Needs implementation in ZT

TypingStatusChange = Literal["start", "stop"]


class DirectTypingNotification(TypedDict):
    # The type field was added in ZFL 58, Zulip 4.0, so don't require it yet
    ## type: DirectMessageString
    op: TypingStatusChange
    to: List[int]


# NOTE: Not yet implemented in ZT
# New in ZFL 58, Zulip 4.0
class StreamTypingNotification(TypedDict):
    type: StreamMessageString
    op: TypingStatusChange
    to: List[int]  # NOTE: Length 1, stream id
    topic: str


###############################################################################
# Parameter to pass in request to:
#   https://zulip.com/api/send-message


class PrivateComposition(TypedDict):
    type: DirectMessageString
    content: str
    to: List[int]  # User ids


class StreamComposition(TypedDict):
    type: StreamMessageString
    content: str
    to: str  # stream name  # TODO: Migrate to using int (stream id)
    subject: str  # TODO: Migrate to using topic


Composition = Union[PrivateComposition, StreamComposition]

###############################################################################
# Parameters to pass in request to:
#   https://zulip.com/api/update-message-flags

MessageFlagStatusChange = Literal["add", "remove"]


class MessagesFlagChange(TypedDict):
    messages: List[int]
    op: MessageFlagStatusChange
    flag: ModifiableMessageFlag


###############################################################################
# Parameter to pass in request to:
#   https://zulip.com/api/update-message


class PrivateMessageUpdateRequest(TypedDict):
    message_id: int
    content: str


class StreamMessageUpdateRequest(TypedDict):
    message_id: int

    # May update combination of content for specified message
    # ...and/or topic of that message and potentially others (via mode)
    # ...but content and stream may not be changed together
    content: NotRequired[str]
    topic: NotRequired[str]
    propagate_mode: NotRequired[EditPropagateMode]

    # Supported for stream moves in ZFL 9 (Zulip 3)
    # Default values if not passed in ZFL 152 (Zulip 6)
    send_notification_to_old_thread: NotRequired[bool]
    send_notification_to_new_thread: NotRequired[bool]

    # TODO: Implement message moves between streams
    # stream_id: int


MessageUpdateRequest = Union[PrivateMessageUpdateRequest, StreamMessageUpdateRequest]

###############################################################################
# Parameter to pass in request to:
#   https://zulip.com/api/update-subscription-settings

PersonalSubscriptionSetting = Literal[
    "in_home_view", "is_muted", "pin_to_top", "desktop_notifications"
]
# Currently unsupported in ZT:
# - color  # TODO: Add support (value is str not bool)
# - audible_notifications
# - push_notifications
# - email_notifications
# - wildcard_mentions_notify  # TODO: Add support


class SubscriptionSettingChange(TypedDict):
    stream_id: int
    property: PersonalSubscriptionSetting
    value: bool


###############################################################################
# In "messages" response from:
#   https://zulip.com/api/get-messages
# In "message" response from:
#   https://zulip.com/api/get-events#message
#   https://zulip.com/api/get-message  (unused)

## TODO: Improve this typing to split private and stream message data


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
    type: MessageType
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


###############################################################################
# In "subscriptions" response from:
#   https://zulip.com/api/register-queue
# Also directly from:
#   https://zulip.com/api/get-events#subscription-add
#   https://zulip.com/api/get-subscriptions (unused)


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

    is_muted: bool

    is_announcement_only: bool  # Deprecated in Zulip 3.0 -> stream_post_policy
    stream_post_policy: int  # NOTE: new in Zulip 3.0 / ZFL 1

    is_web_public: bool
    role: int  # NOTE: new in Zulip 4.0 / ZFL 31
    color: str
    message_retention_days: Optional[int]  # NOTE: new in Zulip 3.0 / ZFL 17
    history_public_to_subscribers: bool
    first_message_id: Optional[int]
    stream_weekly_traffic: Optional[int]

    # Deprecated fields
    # in_home_view: bool  # Replaced by is_muted in Zulip 2.1; still present in updates


###############################################################################
# In "custom_profile_fields" response from:
#   https://zulip.com/api/register-queue
# Also directly from:
#   https://zulip.com/api/get-events#custom_profile_fields
#   NOTE: This data structure is currently used in conftest.py to improve
#   typing of fixtures, and can be used when initial_data is refactored to have
#   better typing.


class CustomProfileField(TypedDict):
    id: int
    name: str
    type: Literal[1, 2, 3, 4, 5, 6, 7, 8]  # Field types range from 1 to 8.
    hint: str
    field_data: str
    order: int


###############################################################################
# In "realm_user" response from:
#   https://zulip.com/api/register-queue
# Also directly from:
#   https://zulip.com/api/get-events#realm_user-add
#   https://zulip.com/api/get-users     (unused)
#   https://zulip.com/api/get-own-user  (unused)
#   https://zulip.com/api/get-user      (unused)
# NOTE: Responses between versions & endpoints vary


class CustomFieldValue(TypedDict):
    value: str
    rendered_value: NotRequired[str]


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

    profile_data: Dict[str, CustomFieldValue]

    # To support in future:
    # is_active: bool  # NOTE: Dependent upon realm_users vs realm_non_active_users
    # delivery_email: str  # NOTE: Only available if admin, and email visibility limited

    # Occasionally present or deprecated fields
    # is_moderator: bool  # NOTE: new in Zulip 4.0 (ZFL 60) - ONLY IN REGISTER RESPONSE
    # is_cross_realm_bot: bool  # NOTE: Only for cross-realm bots
    # max_message_id: int  # NOTE: DEPRECATED & only for /users/me


###############################################################################
# Events possible in "events" from:
#   https://zulip.com/api/get-events
# (also helper data structures not used elsewhere)


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#message
class MessageEvent(TypedDict):
    type: Literal["message"]
    message: Message
    flags: List[MessageFlag]


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#update_message
# NOTE: A single "update_message" event can be both derived event classes


class BaseUpdateMessageEvent(TypedDict):
    type: Literal["update_message"]

    # Present in both cases:
    # - specific message content being updated
    # - move one message (change_one) or this message and those later (change_later)
    message_id: int
    # Present in both cases; message_id may change read/mention/alert status
    # flags: List[MessageFlag]

    # Omitted before Zulip 5.0 / ZFL 114 for rendering-only updates
    # Subsequently always present (and None for rendering_only==True)
    # user_id: NotRequired[Optional[int]]  # sender
    # edit_timestamp: NotRequired[int]

    # When True, does not relate to user-generated edit or message history
    # Prior to Zulip 5.0 / ZFL 114, detect via presence/absence of user_id
    # rendering_only: NotRequired[bool]  # New in Zulip 5.0 / ZFL 114


class UpdateMessageContentEvent(BaseUpdateMessageEvent):
    # stream_name: str  # Not recommended; prefer stream_id
    # stream_id: NotRequired[int]  # Only if a stream message

    # orig_rendered_content: str
    rendered_content: str

    # Not used since we parse the rendered_content only
    # orig_content: str
    # content: str

    is_me_message: bool


class UpdateMessagesLocationEvent(BaseUpdateMessageEvent):
    # All previously sent to stream_id with topic orig_subject
    message_ids: List[int]

    # Old location of messages
    # stream_name: str  # Not recommended; prefer stream_id
    stream_id: int
    orig_subject: str

    propagate_mode: EditPropagateMode

    # Only present if messages are moved to a different topic
    # eg. if subject unchanged, but stream does change, these will be absent
    subject: NotRequired[str]
    # subject_links: NotRequired[List[Any]]
    # topic_links: NotRequired[List[Any]]

    # Only present if messages are moved to a different stream
    # new_stream_id: NotRequired[int]


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#reaction-add and -remove
class ReactionEvent(TypedDict):
    type: Literal["reaction"]
    op: str
    user: Dict[str, Any]  # 'email', 'user_id', 'full_name'
    reaction_type: EmojiType
    emoji_code: str
    emoji_name: str
    message_id: int


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#realm_user-add and -remove


class UpdateCustomFieldValue(TypedDict):
    id: int
    value: Optional[str]
    rendered_value: NotRequired[str]


@final
class RealmUserUpdateName(TypedDict):
    user_id: int
    full_name: str


@final
class RealmUserUpdateAvatar(TypedDict):
    user_id: int
    avatar_url: str
    avatar_source: str
    avatar_url_medium: str
    avatar_version: int


@final
class RealmUserUpdateTimeZone(TypedDict):
    user_id: int
    # NOTE: This field will be removed in future as it is redundant with the user_id
    # email: str
    timezone: str


@final
class RealmUserUpdateBotOwner(TypedDict):
    user_id: int
    bot_owner_id: int


@final
class RealmUserUpdateRole(TypedDict):
    user_id: int
    role: int


@final
class RealmUserUpdateBillingRole(TypedDict):
    user_id: int
    is_billing_admin: bool  # New in ZFL 73 (Zulip 5.0)


@final
class RealmUserUpdateDeliveryEmail(TypedDict):
    user_id: int
    delivery_email: str  # NOTE: Only sent to admins


@final
class RealmUserUpdateCustomProfileField(TypedDict):
    user_id: int
    custom_profile_field: UpdateCustomFieldValue


@final
class RealmUserUpdateEmail(TypedDict):
    user_id: int
    new_email: str


RealmUserEventPerson = Union[
    RealmUserUpdateName,
    RealmUserUpdateAvatar,
    RealmUserUpdateTimeZone,
    RealmUserUpdateBotOwner,
    RealmUserUpdateRole,
    RealmUserUpdateBillingRole,
    RealmUserUpdateDeliveryEmail,
    RealmUserUpdateCustomProfileField,
    RealmUserUpdateEmail,
]


class RealmUserEvent(TypedDict):
    type: Literal["realm_user"]
    op: Literal["update"]
    person: RealmUserEventPerson


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#subscription-update
# (also -peer_add and -peer_remove; FIXME: -add & -remove are not yet supported)


# Update of personal properties
class SubscriptionUpdateEvent(SubscriptionSettingChange):
    type: Literal["subscription"]
    op: Literal["update"]


# User(s) have been (un)subscribed from stream(s)
class SubscriptionPeerAddRemoveEvent(TypedDict):
    type: Literal["subscription"]
    op: Literal["peer_add", "peer_remove"]

    stream_id: int
    stream_ids: List[int]  # NOTE: replaces 'stream_id' in ZFL 35

    user_id: int
    user_ids: List[int]  # NOTE: replaces 'user_id' in ZFL 35


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#typing-start and -stop
class _TypingEventUser(TypedDict):
    user_id: int
    email: str


class TypingEvent(TypedDict):
    type: Literal["typing"]
    op: TypingStatusChange
    sender: _TypingEventUser

    # Unused as yet
    # Pre Zulip 4.0, always present; now only present if message_type == "private"
    # recipients: List[_TypingEventUser]
    # NOTE: These fields are all new in Zulip 4.0 / ZFL 58, if client capability sent
    # message_type: NotRequired[MessageType]
    # stream_id: NotRequired[int]  # Only present if message_type == "stream"
    # topic: NotRequired[str]  # Only present if message_type == "stream"


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#update_message_flags-add and -remove


class UpdateMessageFlagsEvent(TypedDict):
    type: Literal["update_message_flags"]
    messages: List[int]
    operation: MessageFlagStatusChange  # NOTE: deprecated in Zulip 4.0 / ZFL 32 -> 'op'
    op: MessageFlagStatusChange
    flag: ModifiableMessageFlag
    all: bool


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#realm_emoji-update
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


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#user_settings-update
# This is specifically only those supported by ZT
SupportedUserSettings = Literal["send_private_typing_notifications"]


class UpdateUserSettingsEvent(TypedDict):
    type: Literal["user_settings"]
    op: Literal["update"]
    property: SupportedUserSettings
    value: Any


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#update_global_notifications
# This is specifically only those supported by ZT
SupportedGlobalNotificationSettings = Literal["pm_content_in_desktop_notifications"]


class UpdateGlobalNotificationsEvent(TypedDict):
    type: Literal["update_global_notifications"]
    notification_name: SupportedGlobalNotificationSettings
    setting: Any


# -----------------------------------------------------------------------------
# See https://zulip.com/api/get-events#update_display_settings
# This is specifically only those supported by ZT
SupportedDisplaySettings = Literal["twenty_four_hour_time"]


class UpdateDisplaySettingsEvent(TypedDict):
    type: Literal["update_display_settings"]
    setting_name: SupportedDisplaySettings
    setting: bool


class MutedUserEvent(TypedDict):
    type: Literal["muted_users"]
    muted_users: List[Dict[str, int]]


# -----------------------------------------------------------------------------
Event = Union[
    MessageEvent,
    UpdateMessageContentEvent,
    UpdateMessagesLocationEvent,
    ReactionEvent,
    SubscriptionUpdateEvent,
    SubscriptionPeerAddRemoveEvent,
    TypingEvent,
    UpdateMessageFlagsEvent,
    UpdateDisplaySettingsEvent,
    UpdateRealmEmojiEvent,
    UpdateUserSettingsEvent,
    UpdateGlobalNotificationsEvent,
    RealmUserEvent,
    MutedUserEvent,
]

###############################################################################
# In response from:
#   https://zulip.com/api/get-server-settings

AuthenticationMethod = Literal[
    "password",
    "dev",
    "email",
    "ldap",
    "remoteuser",
    "github",
    "azuread",
    "gitlab",  # New in Zulip 3.0, ZFL 1
    "apple",
    "google",
    "saml",
    "openid_connect",
]


class ExternalAuthenticationMethod(TypedDict):
    name: str
    display_name: str
    display_icon: Optional[str]
    login_url: str
    signup_url: str


# As of ZFL 121
class ServerSettings(TypedDict):
    # authentication_methods is deprecated in favor of external_authentication_methods
    authentication_methods: Dict[AuthenticationMethod, bool]
    # Added in Zulip 2.1.0
    external_authentication_methods: List[ExternalAuthenticationMethod]

    # TODO Refactor ZFL to default to zero
    zulip_feature_level: NotRequired[int]  # New in Zulip 3.0, ZFL 1
    zulip_version: str
    zulip_merge_base: NotRequired[str]  # New in Zulip 5.0, ZFL 88

    push_notifications_enabled: bool
    is_incompatible: bool
    email_auth_enabled: bool
    require_email_format_usernames: bool

    # This appears to be present for all Zulip servers, even for no organization,
    # which makes it useful to determine a 'preferred' URL for the server/organization
    realm_uri: str

    # These may only be present if it's an organization, not just a Zulip server
    # Re realm_name discussion, See #api document > /server_settings: `realm_name`, etc.
    realm_name: NotRequired[str]  # Absence indicates root Zulip server but no realm
    realm_icon: str
    realm_description: str
    realm_web_public_access_enabled: NotRequired[bool]  # New in Zulip 5.0, ZFL 116
