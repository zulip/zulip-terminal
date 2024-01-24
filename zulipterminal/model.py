"""
Defines the `Model`, fetching and storing data retrieved from the Zulip server
"""

import itertools
import json
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, wait
from copy import deepcopy
from datetime import datetime
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)
from urllib.parse import urlparse

import zulip
from bs4 import BeautifulSoup
from typing_extensions import TypedDict

from zulipterminal import unicode_emojis
from zulipterminal.api_types import (
    MAX_MESSAGE_LENGTH,
    MAX_STREAM_NAME_LENGTH,
    MAX_TOPIC_NAME_LENGTH,
    Composition,
    CustomFieldValue,
    DirectTypingNotification,
    EditPropagateMode,
    Event,
    Message,
    MessagesFlagChange,
    PrivateComposition,
    PrivateMessageUpdateRequest,
    RealmEmojiData,
    RealmUser,
    Stream,
    StreamComposition,
    StreamMessageUpdateRequest,
    Subscription,
    SubscriptionSettingChange,
    TypingStatusChange,
    UpdateMessageContentEvent,
    UpdateMessagesLocationEvent,
)
from zulipterminal.config.keys import primary_key_for_command
from zulipterminal.config.symbols import STREAM_TOPIC_SEPARATOR
from zulipterminal.config.ui_mappings import EDIT_TOPIC_POLICY, ROLE_BY_ID, STATE_ICON
from zulipterminal.helper import (
    CustomProfileData,
    MinimalUserData,
    NamedEmojiData,
    StreamAccessType,
    StreamData,
    TidiedUserInfo,
    UserStatus,
    asynch,
    canonicalize_color,
    classify_unread_counts,
    display_error_if_present,
    index_messages,
    initial_index,
    notify_if_message_sent_outside_narrow,
    set_count,
    sort_unread_topics,
)
from zulipterminal.platform_code import notify
from zulipterminal.ui_tools.utils import create_msg_box_list


OFFLINE_THRESHOLD_SECS = 140


class ServerConnectionFailure(Exception):
    pass


def sort_streams(streams: List[StreamData]) -> None:
    """
    Used for sorting model.pinned_streams and model.unpinned_streams.
    """
    streams.sort(key=lambda s: s["name"].lower())


class UserSettings(TypedDict):
    send_private_typing_notifications: bool
    twenty_four_hour_time: bool
    pm_content_in_desktop_notifications: bool


class Model:
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client

        self.narrow: List[Any] = []
        self._have_last_message: Dict[str, bool] = {}
        self.stream_id: Optional[int] = None
        self.recipients: FrozenSet[Any] = frozenset()
        self.index = initial_index
        self.last_unread_pm = None

        self.user_id = -1
        self.user_email = ""
        self.user_full_name = ""
        self.server_url = "{uri.scheme}://{uri.netloc}/".format(
            uri=urlparse(self.client.base_url)
        )
        self.server_name = ""

        self._notified_user_of_notification_failure = False

        # Events fetched once at startup
        self.initial_data_to_fetch: List[str] = [
            "realm",
            "presence",
            "subscription",
            "message",
            "starred_messages",
            "update_message_flags",
            "muted_topics",
            "realm_user",  # Enables cross_realm_bots
            "realm_user_groups",
            "update_global_notifications",
            "update_display_settings",
            "user_settings",
            "realm_emoji",
            "custom_profile_fields",
            # zulip_version and zulip_feature_level are always returned in
            # POST /register from Feature level 3.
            "zulip_version",
        ]

        # Events desired with their corresponding callback
        self.event_actions: Dict[str, Callable[[Event], None]] = {
            "message": self._handle_message_event,
            "update_message": self._handle_update_message_event,
            "reaction": self._handle_reaction_event,
            "subscription": self._handle_subscription_event,
            "typing": self._handle_typing_event,
            "update_message_flags": self._handle_update_message_flags_event,
            "update_global_notifications": self._handle_update_global_notifications_event,  # noqa: E501
            "update_display_settings": self._handle_update_display_settings_event,
            "user_settings": self._handle_user_settings_event,
            "realm_emoji": self._handle_update_emoji_event,
            "realm_user": self._handle_realm_user_event,
        }

        self.initial_data: Dict[str, Any] = {}

        # Register to the queue before initializing further so that we don't
        # lose any updates while messages are being fetched.
        self._fetch_initial_data()

        self.server_version = self.initial_data["zulip_version"]
        self.server_feature_level = self.initial_data.get("zulip_feature_level")

        self.user_dict: Dict[str, MinimalUserData] = {}
        self.user_id_email_dict: Dict[int, str] = {}
        self._all_users_by_id: Dict[int, RealmUser] = {}
        self._cross_realm_bots_by_id: Dict[int, RealmUser] = {}
        self.users: List[MinimalUserData] = []
        self._update_users_data_from_initial_data()

        self.stream_dict: Dict[int, Subscription] = {}
        self._unsubscribed_streams: Dict[int, Subscription] = {}
        self._never_subscribed_streams: Dict[int, Stream] = {}
        self.muted_streams: Set[int] = set()
        self.pinned_streams: List[StreamData] = []
        self.unpinned_streams: List[StreamData] = []
        self.visual_notified_streams: Set[int] = set()

        self._register_non_subscribed_streams(
            unsubscribed_streams=self.initial_data["unsubscribed"],
            never_subscribed_streams=self.initial_data["never_subscribed"],
        )

        self._subscribe_to_streams(self.initial_data["subscriptions"])

        # NOTE: The date_created field of stream has been added in feature
        # level 30, server version 4. For consistency we add this field
        # on server iterations even before this with value of None.
        if self.server_feature_level is None or self.server_feature_level < 30:
            for stream in self.stream_dict.values():
                stream["date_created"] = None

        self.normalize_and_cache_message_retention_text()

        # NOTE: The expected response has been upgraded from
        # [stream_name, topic] to [stream_name, topic, date_muted] in
        # feature level 1, server version 3.0.
        muted_topics = self.initial_data["muted_topics"]
        assert set(map(len, muted_topics)) in (set(), {2}, {3})
        self._muted_topics: Dict[Tuple[str, str], Optional[int]] = {
            (stream_name, topic): (
                None if self.server_feature_level is None else date_muted[0]
            )
            for stream_name, topic, *date_muted in muted_topics
        }

        groups = self.initial_data["realm_user_groups"]
        self.user_group_by_id: Dict[int, Dict[str, Any]] = {}
        self.user_group_names = self._group_info_from_realm_user_groups(groups)

        self.unread_counts = classify_unread_counts(self)

        self._draft: Optional[Composition] = None

        self._store_content_length_restrictions()

        self.active_emoji_data, self.all_emoji_names = self.generate_all_emoji_data(
            self.initial_data["realm_emoji"]
        )

        # "user_settings" only present in ZFl 89+ (v5.0)
        user_settings = self.initial_data.get("user_settings", None)
        # TODO: Support multiple settings locations via settings migration #1108
        self._user_settings = UserSettings(
            send_private_typing_notifications=(
                True
                if user_settings is None
                else user_settings["send_private_typing_notifications"]
            ),  # ZFL 105, Zulip 5.0
            twenty_four_hour_time=self.initial_data["twenty_four_hour_time"],
            pm_content_in_desktop_notifications=self.initial_data[
                "pm_content_in_desktop_notifications"
            ],
        )

        self.new_user_input = True
        self._start_presence_updates()

    def user_settings(self) -> UserSettings:
        return deepcopy(self._user_settings)

    def message_retention_days_response(self, days: int, org_default: bool) -> str:
        suffix = " [Organization default]" if org_default else ""
        return ("Indefinite" if (days == -1 or days is None) else str(days)) + suffix

    def normalize_and_cache_message_retention_text(self) -> None:
        # NOTE: The "message_retention_days" field was added in server v3.0, ZFL 17.
        # For consistency, we add this field on server iterations even before this
        # assigning it the value of "realm_message_retention_days" from /register.
        # The server defines two special values for this field:
        # • None: Inherits organization-level setting i.e. realm_message_retention_days
        # • -1: Messages in this stream are stored indefinitely
        # We store the abstracted message retention text for each stream mapped to its
        # sream_id in model.cached_retention_text. This will be displayed in the UI.
        self.cached_retention_text: Dict[int, str] = {}
        realm_message_retention_days = self.initial_data["realm_message_retention_days"]
        if self.server_feature_level is None or self.server_feature_level < 17:
            for stream in self.stream_dict.values():
                stream["message_retention_days"] = None

        for stream in self.stream_dict.values():
            message_retention_days = stream["message_retention_days"]
            is_organization_default = message_retention_days is None
            final_msg_retention_days = (
                realm_message_retention_days
                if is_organization_default
                else message_retention_days
            )
            message_retention_response = self.message_retention_days_response(
                final_msg_retention_days, is_organization_default
            )
            self.cached_retention_text[stream["stream_id"]] = message_retention_response

    def get_focus_in_current_narrow(self) -> Optional[int]:
        """
        Returns the focus in the current narrow.
        For no existing focus this returns None, otherwise the message ID.
        """
        return self.index["pointer"].get(repr(self.narrow), None)

    def set_focus_in_current_narrow(self, focus_message: int) -> None:
        self.index["pointer"][repr(self.narrow)] = focus_message

    def is_search_narrow(self) -> bool:
        """
        Checks if the current narrow is a result of a previous search for
        a messages in a different narrow.
        """
        return "search" in [subnarrow[0] for subnarrow in self.narrow]

    def set_narrow(
        self,
        *,
        stream: Optional[str] = None,
        topic: Optional[str] = None,
        pms: bool = False,
        pm_with: Optional[str] = None,
        starred: bool = False,
        mentioned: bool = False,
    ) -> bool:
        selected_params = {k for k, v in locals().items() if k != "self" and v}
        valid_narrows: Dict[FrozenSet[str], List[Any]] = {
            frozenset(): [],
            frozenset(["stream"]): [["stream", stream]],
            frozenset(["stream", "topic"]): [["stream", stream], ["topic", topic]],
            frozenset(["pms"]): [["is", "private"]],
            frozenset(["pm_with"]): [["pm-with", pm_with]],
            frozenset(["starred"]): [["is", "starred"]],
            frozenset(["mentioned"]): [["is", "mentioned"]],
        }
        for narrow_param, narrow in valid_narrows.items():
            if narrow_param == selected_params:
                new_narrow = narrow
                break
        else:
            raise RuntimeError("Model.set_narrow parameters used incorrectly.")

        if new_narrow != self.narrow:
            self.narrow = new_narrow

            if pm_with is not None and new_narrow[0][0] == "pm-with":
                users = pm_with.split(", ")
                self.recipients = frozenset(
                    [self.user_dict[user]["user_id"] for user in users] + [self.user_id]
                )
            else:
                self.recipients = frozenset()

            if stream is not None:
                # FIXME?: Set up a mapping for this if we plan to use it a lot
                self.stream_id = self.stream_id_from_name(stream)
            else:
                self.stream_id = None

            return False
        else:
            return True

    def set_search_narrow(self, search_query: str) -> None:
        self.unset_search_narrow()
        self.narrow.append(["search", search_query])

    def unset_search_narrow(self) -> None:
        # If current narrow is a result of a previous started search,
        # we pop the ['search', 'text'] term in the narrow, before
        # setting a new narrow.
        if self.is_search_narrow():
            self.narrow = [item for item in self.narrow if item[0] != "search"]

    def get_message_ids_in_current_narrow(self) -> Set[int]:
        narrow = self.narrow
        index = self.index
        if narrow == []:
            ids = index["all_msg_ids"]
        elif self.is_search_narrow():  # Check searches first
            ids = index["search"]
        elif narrow[0][0] == "stream":
            assert self.stream_id is not None
            stream_id = self.stream_id
            if len(narrow) == 1:
                ids = index["stream_msg_ids_by_stream_id"][stream_id]
            elif len(narrow) == 2:
                topic = narrow[1][1]
                ids = index["topic_msg_ids"][stream_id].get(topic, set())
        elif narrow[0][1] == "private":
            ids = index["private_msg_ids"]
        elif narrow[0][0] == "pm-with":
            recipients = self.recipients
            ids = index["private_msg_ids_by_user_ids"].get(recipients, set())
        elif narrow[0][1] == "starred":
            ids = index["starred_msg_ids"]
        elif narrow[0][1] == "mentioned":
            ids = index["mentioned_msg_ids"]
        return ids.copy()

    def current_narrow_contains_message(self, message: Message) -> bool:
        """
        Determine if a message conceptually belongs to a narrow
        FIXME?: stars are not handled right now
        """
        return (
            # all messages contains all messages
            not self.narrow
            # mentions
            or (
                self.narrow[0][1] == "mentioned"
                and bool({"mentioned", "wildcard_mentioned"} & set(message["flags"]))
            )
            # All-PMs
            # FIXME Buggy condition?
            or (self.narrow[0][1] == message["type"] and len(self.narrow) == 1)
            # stream or stream+topic
            or (
                self.narrow[0][0] == "stream"
                and message["type"] == "stream"
                and message["display_recipient"] == self.narrow[0][1]
                and (
                    len(self.narrow) == 1  # stream
                    or (
                        len(self.narrow) == 2  # stream+topic
                        and self.narrow[1][1] == message["subject"]
                    )
                )
            )
            # PM-with
            or (
                self.narrow[0][0] == "pm-with"
                and message["type"] == "private"
                and len(self.narrow) == 1
                and self.recipients
                == frozenset([user["id"] for user in message["display_recipient"]])
            )
        )

    def _notify_server_of_presence(self) -> Dict[str, Any]:
        response = self.client.update_presence(
            request={
                # TODO: Determine `status` from terminal tab focus.
                "status": "active" if self.new_user_input else "idle",
                "new_user_input": self.new_user_input,
            }
        )
        self.new_user_input = False
        return response

    @asynch
    def _start_presence_updates(self) -> None:
        """
        Call `_notify_server_of_presence` every minute (version 1a).
        Use 'response' to update user list (version 1b).
        """
        # FIXME: Version 2: call endpoint with ping_only=True only when
        #        needed, and rely on presence events to update
        while True:
            response = self._notify_server_of_presence()
            if response["result"] == "success":
                self.initial_data["presences"] = response["presences"]
                self._update_users_data_from_initial_data()
                if hasattr(self.controller, "view"):
                    view = self.controller.view
                    view.users_view.update_user_list(user_list=self.users)
                    view.middle_column.update_message_list_status_markers()
            time.sleep(60)

    @asynch
    def toggle_message_reaction(
        self, message: Message, reaction_to_toggle: str
    ) -> None:
        # Check if reaction_to_toggle is a valid original/alias
        assert reaction_to_toggle in self.all_emoji_names

        for emoji_name, emoji_data in self.active_emoji_data.items():
            if (
                reaction_to_toggle == emoji_name
                or reaction_to_toggle in emoji_data["aliases"]
            ):
                # Found the emoji to toggle. Store its code/type and dont check further
                emoji_code = emoji_data["code"]
                emoji_type = emoji_data["type"]
                break

        reaction_to_toggle_spec = dict(
            emoji_name=reaction_to_toggle,
            emoji_code=emoji_code,
            reaction_type=emoji_type,
            message_id=str(message["id"]),
        )
        has_user_reacted = self.has_user_reacted_to_message(
            message, emoji_code=emoji_code
        )
        if has_user_reacted:
            response = self.client.remove_reaction(reaction_to_toggle_spec)
        else:
            response = self.client.add_reaction(reaction_to_toggle_spec)
        display_error_if_present(response, self.controller)

    def has_user_reacted_to_message(self, message: Message, *, emoji_code: str) -> bool:
        for reaction in message["reactions"]:
            if reaction["emoji_code"] != emoji_code:
                continue
            # The reaction.user_id field was added in Zulip v3.0, ZFL 2 so we need to
            # check both the reaction.user.{user_id/id} fields too for pre v3 support.
            user = reaction.get("user", {})
            has_user_reacted = (
                user.get("user_id", None) == self.user_id
                or user.get("id", None) == self.user_id
                or reaction.get("user_id", None) == self.user_id
            )
            if has_user_reacted:
                return True
        return False

    def session_draft_message(self) -> Optional[Composition]:
        return deepcopy(self._draft)

    def save_draft(self, draft: Composition) -> None:
        self._draft = deepcopy(draft)
        self.controller.report_success(["Saved message as draft"])

    @asynch
    def toggle_message_star_status(self, message: Message) -> None:
        messages = [message["id"]]
        if "starred" in message["flags"]:
            request = MessagesFlagChange(messages=messages, flag="starred", op="remove")
        else:
            request = MessagesFlagChange(messages=messages, flag="starred", op="add")
        response = self.client.update_message_flags(request)
        display_error_if_present(response, self.controller)

    @asynch
    def mark_message_ids_as_read(self, id_list: List[int]) -> None:
        if not id_list:
            return
        response = self.client.update_message_flags(
            MessagesFlagChange(messages=id_list, flag="read", op="add")
        )
        display_error_if_present(response, self.controller)

    @asynch
    def send_typing_status_by_user_ids(
        self, recipient_user_ids: List[int], *, status: TypingStatusChange
    ) -> None:
        if not self.user_settings()["send_private_typing_notifications"]:
            return
        if recipient_user_ids:
            request: DirectTypingNotification = {"to": recipient_user_ids, "op": status}
            response = self.client.set_typing_status(request)
            display_error_if_present(response, self.controller)
        else:
            raise RuntimeError("Empty recipient list.")

    def send_private_message(self, recipients: List[int], content: str) -> bool:
        if recipients:
            composition = PrivateComposition(
                type="private",
                to=recipients,
                content=content,
            )
            response = self.client.send_message(composition)
            display_error_if_present(response, self.controller)
            message_was_sent = response["result"] == "success"
            if message_was_sent:
                notify_if_message_sent_outside_narrow(composition, self.controller)
            return message_was_sent
        else:
            raise RuntimeError("Empty recipients list.")

    def send_stream_message(self, stream: str, topic: str, content: str) -> bool:
        composition = StreamComposition(
            type="stream",
            to=stream,
            subject=topic,
            content=content,
        )
        response = self.client.send_message(composition)
        display_error_if_present(response, self.controller)
        message_was_sent = response["result"] == "success"
        if message_was_sent:
            notify_if_message_sent_outside_narrow(composition, self.controller)
        return message_was_sent

    def update_private_message(self, msg_id: int, content: str) -> bool:
        request: PrivateMessageUpdateRequest = {
            "message_id": msg_id,
            "content": content,
        }
        response = self.client.update_message(request)
        display_error_if_present(response, self.controller)
        return response["result"] == "success"

    def update_stream_message(
        self,
        topic: str,
        message_id: int,
        propagate_mode: EditPropagateMode,
        content: Optional[str] = None,
        notify_old: bool = False,
        notify_new: bool = False,
    ) -> bool:
        request: StreamMessageUpdateRequest = {
            "message_id": message_id,
            "propagate_mode": propagate_mode,
            "topic": topic,
        }
        if content is not None:
            request["content"] = content

        if self.server_feature_level is not None and self.server_feature_level >= 9:
            request["send_notification_to_old_thread"] = notify_old
            request["send_notification_to_new_thread"] = notify_new

        response = self.client.update_message(request)
        display_error_if_present(response, self.controller)
        if response["result"] == "success":
            message = self.index["messages"][message_id]
            stream_name = message.get("display_recipient", None)
            old_topic = message.get("subject", None)
            new_topic = request["topic"]
            stream_name_markup = (
                "footer_contrast",
                f" {stream_name} {STREAM_TOPIC_SEPARATOR} ",
            )
            old_topic_markup = ("footer_contrast", f" {old_topic} ")
            new_topic_markup = ("footer_contrast", f" {new_topic} ")
            if old_topic != new_topic:
                if propagate_mode == "change_one":
                    messages_changed = "one message's"
                elif propagate_mode == "change_all":
                    messages_changed = "all messages'"
                else:  # propagate_mode == "change_later":
                    messages_changed = "some messages'"
                self.controller.report_success(
                    [
                        f"You changed {messages_changed} topic from ",
                        stream_name_markup,
                        old_topic_markup,
                        " to ",
                        stream_name_markup,
                        new_topic_markup,
                        " .",
                    ],
                    duration=6,
                )

        return response["result"] == "success"

    def get_latest_message_in_topic(
        self, stream_id: int, topic_name: str
    ) -> Optional[Message]:
        request: Dict[str, Any] = {
            "anchor": 10000000000000000,
            "num_before": 1,
            "num_after": 0,
            "narrow": [
                {
                    "operator": "stream",
                    "operand": stream_id,
                },
                {"operator": "topic", "operand": topic_name},
            ],
        }
        response = self.client.get_messages(request)
        display_error_if_present(response, self.controller)
        if response["messages"] != [] and len(response["messages"]) == 1:
            return response["messages"][0]
        else:
            return None

    def can_user_edit_topic(self) -> bool:
        user_info = self.get_user_info(self.user_id)
        if user_info is not None:
            if not self.initial_data.get("realm_allow_message_editing"):
                self.controller.report_error("Editing messages is disabled")
                return False
            role = user_info["role"]
            if role <= 200:
                return True
            # ZFL >= 75, realm/ allow_community_topic_editing was replaced with
            # edit_topic_policy
            allow_community_topic_editing = self.initial_data.get(
                "realm_allow_community_topic_editing", None
            )
            if allow_community_topic_editing is True:
                return True
            elif allow_community_topic_editing is False:
                self.controller.report_error("Editing topic is disabled")
                return False
            else:
                edit_topic_policy = self.initial_data.get("realm_edit_topic_policy")
                if edit_topic_policy == 2:
                    # For admins and owners only (not using user role)
                    if role <= 200:
                        return True
                    else:
                        self.controller.report_error(EDIT_TOPIC_POLICY[2])
                        return False
                elif edit_topic_policy == 4:
                    # Check for moderators
                    if role <= 300:
                        return True
                    else:
                        self.controller.report_error(EDIT_TOPIC_POLICY[4])
                        return False
                elif edit_topic_policy == 3:
                    # Check for 'full members'
                    if role <= 400:
                        return True
                    else:
                        self.controller.report_error(EDIT_TOPIC_POLICY[3])
                        return False
                elif edit_topic_policy == 1:
                    # Check for members
                    if role <= 400:
                        return True
                    else:
                        self.controller.report_error(EDIT_TOPIC_POLICY[1])
                        return False
                else:  # edit_topic_policy == 5 (or None)
                    # All users including guests
                    return True
        self.controller.report_error("User not found")
        return False

    def generate_all_emoji_data(
        self, custom_emoji: Dict[str, RealmEmojiData]
    ) -> Tuple[NamedEmojiData, List[str]]:
        unicode_emoji_data = unicode_emojis.EMOJI_DATA
        for name, data in unicode_emoji_data.items():
            data["type"] = "unicode_emoji"
        typed_unicode_emoji_data = cast(NamedEmojiData, unicode_emoji_data)
        custom_emoji_data: NamedEmojiData = {
            emoji["name"]: {
                "code": emoji_code,
                "aliases": [],
                "type": "realm_emoji",
            }
            for emoji_code, emoji in custom_emoji.items()
            if not emoji["deactivated"]
        }
        zulip_extra_emoji: NamedEmojiData = {
            "zulip": {"code": "zulip", "aliases": [], "type": "zulip_extra_emoji"}
        }
        all_emoji_data = {
            **typed_unicode_emoji_data,
            **custom_emoji_data,
            **zulip_extra_emoji,
        }
        all_emoji_names = []
        for emoji_name, emoji_data in all_emoji_data.items():
            all_emoji_names.append(emoji_name)
            all_emoji_names.extend(emoji_data["aliases"])
        all_emoji_names = sorted(all_emoji_names)
        active_emoji_data = dict(sorted(all_emoji_data.items()))
        return active_emoji_data, all_emoji_names

    def get_messages(
        self, *, num_after: int, num_before: int, anchor: Optional[int]
    ) -> str:
        # anchor value may be specific message (int) or next unread (None)
        first_anchor = anchor is None
        anchor_value = anchor if anchor is not None else 0

        request = {
            "anchor": anchor_value,
            "num_before": num_before,
            "num_after": num_after,
            "apply_markdown": True,
            "use_first_unread_anchor": first_anchor,
            "client_gravatar": True,
            "narrow": json.dumps(self.narrow),
        }
        response = self.client.get_messages(message_filters=request)
        if response["result"] == "success":
            response["messages"] = [
                self.modernize_message_response(msg) for msg in response["messages"]
            ]

            self.index = index_messages(response["messages"], self, self.index)
            narrow_str = repr(self.narrow)
            if first_anchor and response["anchor"] != 10000000000000000:
                self.index["pointer"][narrow_str] = response["anchor"]
            if "found_newest" in response:
                just_found_last_msg = response["found_newest"]
            else:
                # Older versions of the server does not contain the
                # 'found_newest' flag. Instead, we use this logic:
                query_range = num_after + num_before + 1
                just_found_last_msg = len(response["messages"]) < query_range

            had_last_msg = self._have_last_message.get(narrow_str, False)
            self._have_last_message[narrow_str] = had_last_msg or just_found_last_msg

            return ""
        display_error_if_present(response, self.controller)
        return response["msg"]

    def _store_content_length_restrictions(self) -> None:
        """
        Stores content length restriction fields for compose box in
        Model, if received from server, else use pre-defined values.
        These fields were added in server version 4.0, ZFL 53.
        """
        self.max_stream_name_length = self.initial_data.get(
            "max_stream_name_length", MAX_STREAM_NAME_LENGTH
        )
        self.max_topic_length = self.initial_data.get(
            "max_topic_length", MAX_TOPIC_NAME_LENGTH
        )
        self.max_message_length = self.initial_data.get(
            "max_message_length", MAX_MESSAGE_LENGTH
        )

    @staticmethod
    def modernize_message_response(message: Message) -> Message:
        """
        Converts received message into the modern message response format.

        This provides a good single place to handle support for older server
        releases params, and making them compatible with recent releases.

        TODO: This could be extended for other message params in future.
        """
        # (1) `subject_links` param is changed to `topic_links` from
        # feature level 1, server version 3.0
        if "subject_links" in message:
            message["topic_links"] = message.pop("subject_links")

        # (2) Modernize `topic_links` old response (List[str]) to new response
        # (List[Dict[str, str]])
        if "topic_links" in message:
            topic_links = [
                {"url": link, "text": ""}
                for link in message["topic_links"]
                if type(link) == str
            ]
            if topic_links:
                message["topic_links"] = topic_links

        return message

    def fetch_message_history(
        self, message_id: int
    ) -> List[Dict[str, Union[int, str]]]:
        """
        Fetches message edit history for a message using its ID.
        """
        response = self.client.get_message_history(message_id)
        if response["result"] == "success":
            return response["message_history"]
        display_error_if_present(response, self.controller)
        return list()

    def fetch_raw_message_content(self, message_id: int) -> Optional[str]:
        """
        Fetches raw message content of a message using its ID.
        """
        response = self.client.get_raw_message(message_id)
        if response["result"] == "success":
            return response["raw_content"]
        display_error_if_present(response, self.controller)

        return None

    def _fetch_topics_in_streams(self, stream_list: Iterable[int]) -> str:
        """
        Fetch all topics with specified stream_id's and
        index their names (Version 1)
        """
        # FIXME: Version 2: Fetch last 'n' recent topics for each stream.
        for stream_id in stream_list:
            response = self.client.get_stream_topics(stream_id)
            if response["result"] == "success":
                self.index["topics"][stream_id] = [
                    topic["name"] for topic in response["topics"]
                ]
            else:
                display_error_if_present(response, self.controller)
                return response["msg"]
        return ""

    def topics_in_stream(self, stream_id: int) -> List[str]:
        """
        Returns a list of topic names for stream_id from the index.
        """
        if not self.index["topics"][stream_id]:
            self._fetch_topics_in_streams([stream_id])

        return list(self.index["topics"][stream_id])

    @staticmethod
    def exception_safe_result(future: "Future[str]") -> str:
        try:
            return future.result()
        except zulip.ZulipError as e:
            return str(e)

    def is_muted_stream(self, stream_id: int) -> bool:
        return stream_id in self.muted_streams

    def is_muted_topic(self, stream_id: int, topic: str) -> bool:
        """
        Returns True if topic is muted via muted_topics.
        """
        stream_name = self.stream_name_from_id(stream_id)
        topic_to_search = (stream_name, topic)
        return topic_to_search in self._muted_topics

    def stream_topic_from_message_id(
        self, message_id: int
    ) -> Optional[Tuple[int, str]]:
        """
        Returns the stream and topic of a message of a given message id.
        If the message is not a stream message or if it is not present in the index,
        None is returned.
        """
        message = self.index["messages"].get(message_id, None)
        if message is not None and message["type"] == "stream":
            stream_id = message["stream_id"]
            topic = message["subject"]
            return (stream_id, topic)
        return None

    def next_unread_topic_from_message_id(
        self, current_message: Optional[int]
    ) -> Optional[Tuple[int, str]]:
        if current_message:
            current_topic = self.stream_topic_from_message_id(current_message)
        else:
            current_topic = (
                self.stream_id_from_name(self.narrow[0][1]),
                self.narrow[1][1],
            )
        left_panel_stream_list = [
            stream["id"] for stream in (self.pinned_streams + self.unpinned_streams)
        ]
        unread_topics = sort_unread_topics(
            self.unread_counts["unread_topics"],
            left_panel_stream_list,
        )
        next_topic = False
        stream_start: Optional[Tuple[int, str]] = None
        if current_topic is None:
            next_topic = True
        elif current_topic not in unread_topics:
            # insert current_topic in list of unread_topics for the case where
            # current_topic is not in unread_topics, and the next unmuted topic
            # is to be returned. This does not modify the original unread topics
            # data, and is just used to compute the next unmuted topic to be returned.
            unread_topics = sort_unread_topics(
                {**self.unread_counts["unread_topics"], current_topic: 0},
                left_panel_stream_list,
            )
        # loop over unread_topics list twice for the case that last_unread_topic was
        # the last valid unread_topic in unread_topics list.
        for unread_topic in unread_topics * 2:
            stream_id, topic_name = unread_topic
            if not self.is_muted_topic(
                stream_id, topic_name
            ) and not self.is_muted_stream(stream_id):
                if next_topic:
                    if unread_topic == current_topic:
                        return None
                    if (
                        current_topic is not None
                        and unread_topic[0] != current_topic[0]
                        and stream_start != current_topic
                    ):
                        return stream_start
                    return unread_topic

                if (
                    stream_start is None
                    and current_topic is not None
                    and unread_topic[0] == current_topic[0]
                ):
                    stream_start = unread_topic
            if unread_topic == current_topic:
                next_topic = True
        return None

    def get_next_unread_pm(self) -> Optional[int]:
        pms = list(self.unread_counts["unread_pms"].keys())
        next_pm = False
        for pm in pms:
            if next_pm is True:
                self.last_unread_pm = pm
                return pm
            if pm == self.last_unread_pm:
                next_pm = True
        if len(pms) > 0:
            pm = pms[0]
            self.last_unread_pm = pm
            return pm
        return None

    def _fetch_initial_data(self) -> None:
        # Thread Processes to reduce start time.
        # NOTE: Exceptions do not work well with threads
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures: Dict[str, Future[str]] = {
                "get_messages": executor.submit(
                    self.get_messages, num_after=10, num_before=30, anchor=None
                ),
                "register": executor.submit(
                    self._register_desired_events, fetch_data=True
                ),
            }

            # Wait for threads to complete
            wait(futures.values())

        results: Dict[str, str] = {
            name: self.exception_safe_result(future) for name, future in futures.items()
        }
        if not any(results.values()):
            self.user_id = self.initial_data["user_id"]
            self.user_email = self.initial_data["email"]
            self.user_full_name = self.initial_data["full_name"]
            self.server_name = self.initial_data["realm_name"]
        else:
            failures: DefaultDict[str, List[str]] = defaultdict(list)
            for name, result in results.items():
                if result:
                    failures[result].append(name)
            failure_text = [
                "{} ({})".format(error, ", ".join(sorted(calls)))
                for error, calls in failures.items()
            ]
            raise ServerConnectionFailure(", ".join(failure_text))

    def get_other_subscribers_in_stream(
        self, stream_id: Optional[int] = None, stream_name: Optional[str] = None
    ) -> List[int]:
        assert stream_id is not None or stream_name is not None

        if stream_id:
            assert self.is_user_subscribed_to_stream(stream_id)

            return [
                sub
                for sub in self.stream_dict[stream_id]["subscribers"]
                if sub != self.user_id
            ]
        else:
            return [
                sub
                for _, stream in self.stream_dict.items()
                for sub in stream["subscribers"]
                if stream["name"] == stream_name
                if sub != self.user_id
            ]

    def _clean_and_order_custom_profile_data(
        self, custom_profile_data: Dict[str, CustomFieldValue]
    ) -> List[CustomProfileData]:
        # Get custom profile fields
        profile_fields = {
            str(field["id"]): field
            for field in self.initial_data["custom_profile_fields"]
        }

        cleaned_profile_data = []
        for field_id in custom_profile_data:
            field = profile_fields[field_id]
            raw_value = custom_profile_data[field_id]["value"]

            if field["type"] == 3:  # List of options
                field_options = json.loads(field["field_data"])
                field_value = field_options[raw_value]["text"]

            elif field["type"] == 6:  # Person picker
                field_value = list(
                    map(
                        int,
                        raw_value.strip("][").split(","),
                    )
                )

            elif field["type"] == 7:  # External Account
                field_options = json.loads(field["field_data"])
                field_subtype = field_options["subtype"]
                if field_subtype == "github":
                    url_pattern = "https://github.com/%(username)s"
                elif field_subtype == "twitter":
                    url_pattern = "https://twitter.com/%(username)s"
                else:
                    url_pattern = field_options["url_pattern"]
                field_value = url_pattern % {"username": raw_value}
            else:
                field_value = raw_value

            data: CustomProfileData = {
                "label": field["name"],
                "value": field_value,
                "type": field["type"],
                "order": field["order"],
            }
            cleaned_profile_data.append(data)

        cleaned_profile_data.sort(key=lambda field: field["order"])
        return cleaned_profile_data

    def get_user_info(self, user_id: int) -> Optional[TidiedUserInfo]:
        api_user_data: Optional[RealmUser] = self._all_users_by_id.get(user_id, None)

        if not api_user_data:
            return None

        # Role `None` for triggering servers < Zulip 4.1 (ZFL 59)
        raw_user_role = api_user_data.get("role", None)
        if raw_user_role is None:
            user_role = 400  # Default role is member

            # Ensure backwards compatibility for role parameters (e.g., `is_admin`)
            for role_id, role in ROLE_BY_ID.items():
                if api_user_data.get(role["bool"], None):
                    user_role = role_id
                    break
        else:
            user_role = raw_user_role

        custom_profile_data = api_user_data.get("profile_data", {})
        cleaned_custom_profile_data = self._clean_and_order_custom_profile_data(
            custom_profile_data
        )
        # TODO: Add custom fields later as an enhancement
        user_info: TidiedUserInfo = dict(
            full_name=api_user_data.get("full_name", "(No name)"),
            email=api_user_data.get("email", ""),
            date_joined=api_user_data.get("date_joined", ""),
            timezone=api_user_data.get("timezone", ""),
            is_bot=api_user_data.get("is_bot", False),
            role=user_role,
            custom_profile_data=cleaned_custom_profile_data,
            bot_type=api_user_data.get("bot_type", None),
            bot_owner_name="",  # Can be non-empty only if is_bot == True
            last_active="",
        )

        bot_owner: Optional[Union[RealmUser, MinimalUserData]] = None

        if api_user_data.get("bot_owner_id", None):
            bot_owner = self._all_users_by_id.get(api_user_data["bot_owner_id"], None)
        # Ensure backwards compatibility for `bot_owner` (which is email of owner)
        elif api_user_data.get("bot_owner", None):
            bot_owner = self.user_dict.get(api_user_data["bot_owner"], None)

        user_info["bot_owner_name"] = bot_owner["full_name"] if bot_owner else ""

        if self.initial_data["presences"].get(user_info["email"], None):
            timestamp = self.initial_data["presences"][user_info["email"]][
                "aggregated"
            ]["timestamp"]

            # Take 24h vs AM/PM format into consideration
            user_info["last_active"] = self.formatted_local_time(
                timestamp, show_seconds=True
            )

        return user_info

    def _update_users_data_from_initial_data(self) -> None:
        # Dict which stores the active/idle status of users (by email)
        presences = self.initial_data["presences"]

        # Construct a dict of each user in the realm to look up by email
        # and a user-id to email mapping
        self.user_dict = dict()
        self.user_id_email_dict = dict()
        for user in self.initial_data["realm_users"]:
            if self.user_id == user["user_id"]:
                self._all_users_by_id[self.user_id] = user
                current_user: MinimalUserData = {
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "user_id": user["user_id"],
                    "status": "active",
                }
                continue
            email = user["email"]

            status: UserStatus
            if user["is_bot"]:
                # Bot has no dynamic status, so avoid presence lookup
                status = "bot"
            elif email in presences:  # presences currently subset of all users
                """
                * Aggregate our information on a user's presence across their
                * clients.
                *
                * For an explanation of the Zulip presence model this helps
                * implement, see the subsystem doc:
                https://zulip.readthedocs.io/en/latest/subsystems/presence.html
                *
                * This logic should match `status_from_timestamp` in the web
                * app's
                * `static/js/presence.js`.
                *
                * Out of the ClientPresence objects found in `presence`, we
                * consider only those with a timestamp newer than
                * OFFLINE_THRESHOLD_SECS; then of
                * those, return the one that has the greatest UserStatus, where
                * `active` > `idle` > `offline`.
                *
                * If there are several ClientPresence objects with the greatest
                * UserStatus, an arbitrary one is chosen.
                """
                aggregate_status: UserStatus = "offline"
                for client in presences[email].items():
                    client_name = client[0]
                    status = client[1]["status"]
                    timestamp = client[1]["timestamp"]
                    if client_name == "aggregated":
                        continue
                    elif (time.time() - timestamp) < OFFLINE_THRESHOLD_SECS:
                        if status == "active":
                            aggregate_status = "active"
                        if status == "idle" and aggregate_status != "active":
                            aggregate_status = status
                        if status == "offline" and (
                            aggregate_status != "active" and aggregate_status != "idle"
                        ):
                            aggregate_status = status

                status = aggregate_status
            else:
                # Set status of users not in the  `presence` list
                # as 'inactive'. They will not be displayed in the
                # user's list by default (only in the search list).
                status = "inactive"
            self.user_dict[email] = {
                "full_name": user["full_name"],
                "email": email,
                "user_id": user["user_id"],
                "status": status,
            }

            self._all_users_by_id[user["user_id"]] = user
            self.user_id_email_dict[user["user_id"]] = email

        # Add internal (cross-realm) bots to dicts
        for bot in self.initial_data["cross_realm_bots"]:
            email = bot["email"]
            self.user_dict[email] = {
                "full_name": bot["full_name"],
                "email": email,
                "user_id": bot["user_id"],
                "status": "bot",
            }
            self._cross_realm_bots_by_id[bot["user_id"]] = bot
            self._all_users_by_id[bot["user_id"]] = bot
            self.user_id_email_dict[bot["user_id"]] = email

        # Generate filtered lists for each status
        ordered_statuses = list(STATE_ICON.keys())
        presences_by_status = {
            status: sorted(
                [
                    properties
                    for properties in self.user_dict.values()
                    if properties["status"] == status
                ],
                key=lambda user: user["full_name"].casefold(),
            )
            for status in ordered_statuses
        }
        user_list = list(
            itertools.chain.from_iterable(
                presences_by_status[status] for status in ordered_statuses
            )
        )
        user_list.insert(0, current_user)  # Add current user to the top of the list

        # NOTE: Do this after generating user_list to avoid current_user duplication
        self.user_dict[current_user["email"]] = current_user
        self.user_id_email_dict[self.user_id] = current_user["email"]

        self.users = user_list

    def user_name_from_id(self, user_id: int) -> str:
        """
        Returns user's full name given their ID.
        """
        user_email = self.user_id_email_dict.get(user_id)

        if not user_email:
            raise RuntimeError("Invalid user ID.")

        return self.user_dict[user_email]["full_name"]

    def _register_non_subscribed_streams(
        self,
        unsubscribed_streams: List[Subscription],
        never_subscribed_streams: List[Stream],
    ) -> None:
        self._unsubscribed_streams = {
            subscription["stream_id"]: subscription
            for subscription in unsubscribed_streams
        }
        self._never_subscribed_streams = {
            stream["stream_id"]: stream for stream in never_subscribed_streams
        }

    def _get_stream_from_id(self, stream_id: int) -> Stream:
        if stream_id in self.stream_dict:
            return cast(Stream, self.stream_dict[stream_id])
        elif stream_id in self._unsubscribed_streams:
            return cast(Stream, self._unsubscribed_streams[stream_id])
        elif stream_id in self._never_subscribed_streams:
            return self._never_subscribed_streams[stream_id]
        else:
            raise RuntimeError(f"Stream with id {stream_id} does not exist!")

    def _get_subscription_from_id(self, subscription_id: int) -> Subscription:
        if subscription_id in self.stream_dict:
            return self.stream_dict[subscription_id]
        elif subscription_id in self._unsubscribed_streams:
            return self._unsubscribed_streams[subscription_id]
        else:
            raise RuntimeError(
                f"Stream with id {subscription_id} does not exist or never subscribed to!"  # noqa: E501
            )

    def get_all_stream_ids(self) -> List[int]:
        id_list = list(self.stream_dict)
        id_list.extend(stream_id for stream_id in self._unsubscribed_streams)
        id_list.extend(stream_id for stream_id in self._never_subscribed_streams)
        return id_list

    def stream_name_from_id(self, stream_id: int) -> str:
        stream = self._get_stream_from_id(stream_id)
        return stream["name"]

    def subscription_color_from_id(self, subscription_id: int) -> str:
        subscription = self._get_subscription_from_id(subscription_id)
        return canonicalize_color(subscription["color"])

    def _subscribe_to_streams(self, subscriptions: List[Subscription]) -> None:
        def make_reduced_stream_data(stream: Subscription) -> StreamData:
            # stream_id has been changed to id.
            return StreamData(
                {
                    "name": stream["name"],
                    "id": stream["stream_id"],
                    "color": stream["color"],
                    "stream_access_type": self.stream_access_type(stream["stream_id"]),
                    "description": stream["description"],
                }
            )

        new_pinned_streams = []
        new_unpinned_streams = []
        new_muted_streams = set()
        new_visual_notified_streams = set()

        for subscription in subscriptions:
            # Canonicalize color formats, since zulip server versions may use
            # different formats
            subscription["color"] = canonicalize_color(subscription["color"])

            self.stream_dict[subscription["stream_id"]] = subscription
            stream_data = make_reduced_stream_data(subscription)
            if subscription["pin_to_top"]:
                new_pinned_streams.append(stream_data)
            else:
                new_unpinned_streams.append(stream_data)
            if subscription["is_muted"]:
                new_muted_streams.add(subscription["stream_id"])
            if subscription["desktop_notifications"]:
                new_visual_notified_streams.add(subscription["stream_id"])

        if new_pinned_streams:
            self.pinned_streams.extend(new_pinned_streams)
            sort_streams(self.pinned_streams)
        if new_unpinned_streams:
            self.unpinned_streams.extend(new_unpinned_streams)
            sort_streams(self.unpinned_streams)

        self.muted_streams = self.muted_streams.union(new_muted_streams)
        self.visual_notified_streams = self.visual_notified_streams.union(
            new_visual_notified_streams
        )

    def _group_info_from_realm_user_groups(
        self, groups: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Stores group information in the model and returns a list of
        group_names which helps in group typeahead. (Eg: @*terminal*)
        """
        for sub_group in groups:
            self.user_group_by_id[sub_group["id"]] = {
                key: sub_group[key] for key in sub_group if key != "id"
            }
        user_group_names = [
            self.user_group_by_id[group_id]["name"]
            for group_id in self.user_group_by_id
        ]
        # Sort groups for typeahead to work alphabetically (case-insensitive)
        user_group_names.sort(key=str.lower)
        return user_group_names

    def toggle_stream_muted_status(self, stream_id: int) -> None:
        request = [
            SubscriptionSettingChange(
                stream_id=stream_id,
                property="is_muted",
                value=not self.is_muted_stream(stream_id)
                # True for muting and False for unmuting.
            )
        ]
        response = self.client.update_subscription_settings(request)
        display_error_if_present(response, self.controller)

    def stream_id_from_name(self, stream_name: str) -> int:
        for stream_id, stream in self.stream_dict.items():
            if stream["name"] == stream_name:
                return stream_id
        raise RuntimeError("Invalid stream name.")

    def stream_access_type(self, stream_id: int) -> StreamAccessType:
        if stream_id not in self.stream_dict:
            raise RuntimeError("Invalid stream id.")
        stream = self.stream_dict[stream_id]
        if stream.get("is_web_public", False):
            return "web-public"
        if stream["invite_only"]:
            return "private"
        return "public"

    def is_pinned_stream(self, stream_id: int) -> bool:
        return stream_id in [stream["id"] for stream in self.pinned_streams]

    def toggle_stream_pinned_status(self, stream_id: int) -> bool:
        request = [
            SubscriptionSettingChange(
                stream_id=stream_id,
                property="pin_to_top",
                value=not self.is_pinned_stream(stream_id),
            )
        ]
        response = self.client.update_subscription_settings(request)
        return response["result"] == "success"

    def is_visual_notifications_enabled(self, stream_id: int) -> bool:
        """
        Returns true if the stream had "desktop_notifications" enabled
        """
        return stream_id in self.visual_notified_streams

    def toggle_stream_visual_notifications(self, stream_id: int) -> None:
        request = [
            SubscriptionSettingChange(
                stream_id=stream_id,
                property="desktop_notifications",
                value=not self.is_visual_notifications_enabled(stream_id),
            )
        ]
        response = self.client.update_subscription_settings(request)
        display_error_if_present(response, self.controller)

    def is_user_subscribed_to_stream(self, stream_id: int) -> bool:
        return stream_id in self.stream_dict

    def _handle_subscription_event(self, event: Event) -> None:
        """
        Handle changes in subscription (eg. muting/unmuting,
                                        pinning/unpinning streams)
        """
        assert event["type"] == "subscription"

        def get_stream_by_id(streams: List[StreamData], stream_id: int) -> StreamData:
            for stream in streams:
                if stream["id"] == stream_id:
                    return stream
            raise RuntimeError("Invalid stream id.")

        if event["op"] == "update":
            if hasattr(self.controller, "view"):
                # NOTE: As per ZFL 139, is_muted is supported now, but the server
                # also sends event with in_home_view to support older versions
                if (
                    event.get("property", None) == "in_home_view"
                    or event.get("property", None) == "is_muted"
                ):
                    # in_home_view and is_muted have opposite boolean values
                    event_stream_muted_value: bool
                    if event.get("property", None) == "in_home_view":
                        event_stream_muted_value = not event["value"]
                    else:
                        event_stream_muted_value = event["value"]

                    stream_id = event["stream_id"]

                    # FIXME: Does this always contain the stream_id?
                    stream_button = self.controller.view.stream_id_to_button[stream_id]

                    unread_count = self.unread_counts["streams"][stream_id]
                    if not event_stream_muted_value:  # Unmuting streams
                        if stream_id in self.muted_streams:
                            self.muted_streams.remove(stream_id)
                            self.unread_counts["all_msg"] += unread_count
                            stream_button.mark_unmuted(unread_count)
                    else:  # Muting streams
                        if stream_id not in self.muted_streams:
                            self.muted_streams.add(stream_id)
                            self.unread_counts["all_msg"] -= unread_count
                            stream_button.mark_muted()
                    self.controller.update_screen()
                elif event.get("property", None) == "pin_to_top":
                    stream_id = event["stream_id"]

                    # FIXME: Does this always contain the stream_id?
                    stream_button = self.controller.view.stream_id_to_button[stream_id]

                    if event["value"]:
                        stream = get_stream_by_id(self.unpinned_streams, stream_id)
                        if stream:
                            self.unpinned_streams.remove(stream)
                            self.pinned_streams.append(stream)
                    else:
                        stream = get_stream_by_id(self.pinned_streams, stream_id)
                        if stream:
                            self.pinned_streams.remove(stream)
                            self.unpinned_streams.append(stream)
                    sort_streams(self.unpinned_streams)
                    sort_streams(self.pinned_streams)
                    self.controller.view.left_panel.update_stream_view()
                    self.controller.update_screen()
                elif event.get("property", None) == "desktop_notifications":
                    stream_id = event["stream_id"]

                    if event["value"]:
                        self.visual_notified_streams.add(stream_id)
                    else:
                        self.visual_notified_streams.discard(stream_id)
        elif event["op"] in ("peer_add", "peer_remove"):
            # NOTE: ZFL 35 commit was not atomic with API change
            #       (ZFL >=35 can use new plural style)
            if "stream_ids" not in event or "user_ids" not in event:
                stream_ids = [event["stream_id"]]
                user_ids = [event["user_id"]]
            else:
                stream_ids = event["stream_ids"]
                user_ids = event["user_ids"]

            for stream_id in stream_ids:
                if self.is_user_subscribed_to_stream(stream_id):
                    subscribers = self.stream_dict[stream_id]["subscribers"]
                    if event["op"] == "peer_add":
                        subscribers.extend(user_ids)
                    else:
                        for user_id in user_ids:
                            subscribers.remove(user_id)

    def _handle_typing_event(self, event: Event) -> None:
        """
        Handle typing notifications (in private messages)
        """
        assert event["type"] == "typing"

        if not hasattr(self.controller, "view"):
            return

        narrow = self.narrow
        controller = self.controller
        active_conversation_info = controller.active_conversation_info
        sender_email = event["sender"]["email"]
        sender_id = event["sender"]["user_id"]

        # If the user is in pm narrow with the person typing
        # and the person typing isn't the user themselves
        if (
            len(narrow) == 1
            and narrow[0][0] == "pm-with"
            and sender_email in narrow[0][1].split(",")
            and sender_id != self.user_id
        ):
            if event["op"] == "start":
                sender_name = self.user_dict[sender_email]["full_name"]
                active_conversation_info["sender_name"] = sender_name

                if not controller.is_typing_notification_in_progress:
                    controller.show_typing_notification()

            elif event["op"] == "stop":
                controller.active_conversation_info = {}

            else:
                raise RuntimeError("Unknown typing event operation")

    def is_valid_private_recipient(
        self,
        recipient_email: str,
        recipient_name: str,
    ) -> bool:
        return (
            recipient_email in self.user_dict
            and self.user_dict[recipient_email]["full_name"] == recipient_name
        )

    def is_valid_stream(self, stream_name: str) -> bool:
        for stream in self.stream_dict.values():
            if stream["name"] == stream_name:
                return True
        return False

    def notify_user(self, message: Message) -> str:
        """
        return value signifies if notification failed, if it should occur
        """
        # Check if notifications are enabled by the user.
        # It is disabled by default.
        if not self.controller.notify_enabled:
            return ""
        if message["sender_id"] == self.user_id:
            return ""

        recipient = ""
        content = message["content"]
        hidden_content = False
        if message["type"] == "private":
            recipient = "you"
            if len(message["display_recipient"]) > 2:
                extra_targets = [recipient] + [
                    recip["full_name"]
                    for recip in message["display_recipient"]
                    if recip["id"] not in (self.user_id, message["sender_id"])
                ]
                recipient = ", ".join(extra_targets)
            if not self.user_settings()["pm_content_in_desktop_notifications"]:
                content = f"New direct message from {message['sender_full_name']}"
                hidden_content = True
        elif message["type"] == "stream":
            stream_id = message["stream_id"]
            if {"mentioned", "wildcard_mentioned"}.intersection(
                set(message["flags"])
            ) or self.is_visual_notifications_enabled(stream_id):
                recipient = "{display_recipient} -> {subject}".format(**message)

        if recipient:
            if hidden_content:
                text = content
            else:
                soup = BeautifulSoup(content, "lxml")
                for spoiler_tag in soup.find_all(
                    "div", attrs={"class": "spoiler-block"}
                ):
                    header = spoiler_tag.find("div", attrs={"class": "spoiler-header"})
                    header.contents = [ele for ele in header.contents if ele != "\n"]
                    empty_header = len(header.contents) == 0
                    header.unwrap()

                    to_hide = spoiler_tag.find(
                        "div", attrs={"class": "spoiler-content"}
                    )
                    to_hide.string = "(...)" if empty_header else " (...)"

                    spoiler_tag.unwrap()
                text = soup.text

            return notify(
                f"{self.server_name}:\n"
                f"{message['sender_full_name']} (to {recipient})",
                text,
            )
        return ""

    def _handle_message_event(self, event: Event) -> None:
        """
        Handle new messages (eg. add message to the end of the view)
        """
        assert event["type"] == "message"
        message = self.modernize_message_response(event["message"])
        # sometimes `flags` are missing in `event` so initialize
        # an empty list of flags in that case.
        message["flags"] = event.get("flags", [])
        # We need to update the topic order in index, unconditionally.
        if message["type"] == "stream":
            # NOTE: The subsequent helper only updates the topic index based
            # on the message event not the UI (the UI is updated in a
            # consecutive block independently). However, it is critical to keep
            # the topics index synchronized as it used whenever the topics list
            # view is reconstructed later.
            self._update_topic_index(message["stream_id"], message["subject"])
            # If the topic view is toggled for incoming message's
            # recipient stream, then we re-arrange topic buttons
            # with most recent at the top.
            if hasattr(self.controller, "view"):
                view = self.controller.view
                if view.left_panel.is_in_topic_view_with_stream_id(
                    message["stream_id"]
                ):
                    view.topic_w.update_topics_list(
                        message["stream_id"], message["subject"], message["sender_id"]
                    )
                    self.controller.update_screen()

        # We can notify user regardless of whether UI is rendered or not,
        # but depend upon the UI to indicate failures.
        failed_command = self.notify_user(message)
        if (
            failed_command
            and hasattr(self.controller, "view")
            and not self._notified_user_of_notification_failure
        ):
            notice_template = (
                "You have enabled notifications, but your notification "
                "command '{}' could not be found."
                "\n\n"
                "The application will continue attempting to run this command "
                "in this session, but will not notify you again."
                "\n\n"
                "Press '{}' to close this window."
            )
            notice = notice_template.format(
                failed_command, primary_key_for_command("GO_BACK")
            )
            self.controller.popup_with_message(notice, width=50)
            self.controller.update_screen()
            self._notified_user_of_notification_failure = True

        # Index messages before calling set_count.
        self.index = index_messages([message], self, self.index)
        if "read" not in message["flags"]:
            set_count([message["id"]], self.controller, 1)

        if hasattr(self.controller, "view") and self._have_last_message.get(
            repr(self.narrow), False
        ):
            msg_log = self.controller.view.message_view.log
            if msg_log:
                last_message = msg_log[-1].original_widget.message
            else:
                last_message = None
            msg_w_list = create_msg_box_list(
                self, [message["id"]], last_message=last_message
            )
            if not msg_w_list:
                return
            else:
                msg_w = msg_w_list[0]

            if self.current_narrow_contains_message(message):
                msg_log.append(msg_w)

            self.controller.update_screen()

    def _update_topic_index(self, stream_id: int, topic_name: str) -> None:
        """
        Update topic order in index based on incoming message.
        Helper method called by _handle_message_event
        """
        topic_list = self.topics_in_stream(stream_id)
        for topic_iterator, topic in enumerate(topic_list):
            if topic == topic_name:
                topic_list.insert(0, topic_list.pop(topic_iterator))
                break
        else:
            # No previous topics with same topic names are found
            # hence, it must be a new topic.
            topic_list.insert(0, topic_name)

        # Update the index.
        self.index["topics"][stream_id] = topic_list

    def _handle_update_message_event(self, event: Event) -> None:
        """
        Handle updated (edited) messages (changed content/subject)
        """
        assert event["type"] == "update_message"

        # Update edited message status from single message id
        # NOTE: If all messages in topic have topic edited,
        #       they are not all marked as edited, as per server optimization
        message_id = event["message_id"]
        indexed_message = self.index["messages"].get(message_id, None)

        if indexed_message:
            self.index["edited_messages"].add(message_id)

        # Update the rendered content, if the message is indexed
        if "rendered_content" in event and indexed_message:
            content_event = cast(UpdateMessageContentEvent, event)
            indexed_message["content"] = content_event["rendered_content"]
            indexed_message["is_me_message"] = content_event["is_me_message"]
            self.index["messages"][message_id] = indexed_message
            self._update_rendered_view(message_id)

        # NOTE: This is independent of messages being indexed
        # Previous assertion:
        # * 'subject' is not present in update event if
        #   the event didn't have a 'subject' update.
        if "subject" in event:
            location_event = cast(UpdateMessagesLocationEvent, event)
            new_subject = location_event["subject"]
            stream_id = location_event["stream_id"]
            old_subject = location_event["orig_subject"]
            msg_ids_by_topic = self.index["topic_msg_ids"][stream_id]

            # Remove each message_id from the old topic's `topic_msg_ids` set
            # if it exists, and update & re-render the message if it is indexed.
            for msg_id in location_event["message_ids"]:
                # Ensure that the new topic is not the same as the old one
                # (no-op topic edit).
                if new_subject != old_subject:
                    # Remove the msg_id from the relevant `topic_msg_ids` set,
                    # if that topic's set has already been initiated.
                    if old_subject in msg_ids_by_topic:
                        msg_ids_by_topic[old_subject].discard(msg_id)

                    # Add the msg_id to the new topic's set, if the set has
                    # already been initiated.
                    if new_subject in msg_ids_by_topic:
                        msg_ids_by_topic[new_subject].add(msg_id)

                # Update and re-render indexed messages.
                indexed_msg = self.index["messages"].get(msg_id)
                if indexed_msg:
                    indexed_msg["subject"] = new_subject
                    self._update_rendered_view(msg_id)

            # If topic view is open, reload list else reset cache.
            if stream_id in self.index["topics"]:  # noqa: SIM102
                if hasattr(self.controller, "view"):
                    view = self.controller.view
                    if view.left_panel.is_in_topic_view_with_stream_id(stream_id):
                        self._fetch_topics_in_streams([stream_id])
                        view.left_panel.show_topic_view(view.topic_w.stream_button)
                        self.controller.update_screen()
                    else:
                        self.index["topics"][stream_id] = []

    def _handle_reaction_event(self, event: Event) -> None:
        """
        Handle change to reactions on a message
        """
        assert event["type"] == "reaction"
        message_id = event["message_id"]
        # If the message is indexed
        if message_id in self.index["messages"]:
            message = self.index["messages"][message_id]
            if event["op"] == "add":
                message["reactions"].append(
                    {
                        "user": event["user"],
                        "reaction_type": event["reaction_type"],
                        "emoji_code": event["emoji_code"],
                        "emoji_name": event["emoji_name"],
                    }
                )
            else:
                emoji_code = event["emoji_code"]
                for reaction in message["reactions"]:
                    # Since Who reacted is not displayed,
                    # remove the first one encountered
                    if reaction["emoji_code"] == emoji_code:
                        message["reactions"].remove(reaction)

            self.index["messages"][message_id] = message
            self._update_rendered_view(message_id)

    def _handle_update_message_flags_event(self, event: Event) -> None:
        """
        Handle change to message flags (eg. starred, read)
        """
        assert event["type"] == "update_message_flags"
        if self.server_feature_level is None or self.server_feature_level < 32:
            operation = event["operation"]
        else:
            operation = event["op"]

        if event["all"]:  # FIXME Should handle eventually
            return

        flag_to_change = event["flag"]
        if flag_to_change not in {"starred", "read"}:
            return

        if flag_to_change == "read" and operation == "remove":
            return

        indexed_message_ids = set(self.index["messages"])
        message_ids_to_mark = set(event["messages"])

        for message_id in message_ids_to_mark & indexed_message_ids:
            msg = self.index["messages"][message_id]
            if operation == "add":
                if flag_to_change not in msg["flags"]:
                    msg["flags"].append(flag_to_change)
                if flag_to_change == "starred":
                    self.index["starred_msg_ids"].add(message_id)
            elif operation == "remove":
                if flag_to_change in msg["flags"]:
                    msg["flags"].remove(flag_to_change)
                if (
                    message_id in self.index["starred_msg_ids"]
                    and flag_to_change == "starred"
                ):
                    self.index["starred_msg_ids"].remove(message_id)
            else:
                raise RuntimeError(event, msg["flags"])

            self.index["messages"][message_id] = msg
            self._update_rendered_view(message_id)

        if operation == "add" and flag_to_change == "read":
            set_count(
                list(message_ids_to_mark & indexed_message_ids), self.controller, -1
            )

        if flag_to_change == "starred" and operation in ["add", "remove"]:
            # update starred count in view
            len_ids = len(message_ids_to_mark)
            count = -len_ids if operation == "remove" else len_ids
            self.controller.view.starred_button.update_count(
                self.controller.view.starred_button.count + count
            )
            self.controller.update_screen()

    def formatted_local_time(
        self, timestamp: int, *, show_seconds: bool, show_year: bool = False
    ) -> str:
        local_time = datetime.fromtimestamp(timestamp)
        use_24h_format = self.user_settings()["twenty_four_hour_time"]
        format_codes = (
            "%a %b %d "
            f"{'%Y ' if show_year else ''}"
            f"{'%H:' if use_24h_format else '%I:'}"
            "%M"
            f"{':%S' if show_seconds else ''}"
            f"{'' if use_24h_format else ' %p'}"
        )
        return local_time.strftime(format_codes)

    def _handle_update_emoji_event(self, event: Event) -> None:
        """
        Handle update of emoji
        """
        # Here, the event contains information of all realm emojis added
        # by the users in the organisation along with a boolean value
        # representing the active state of each emoji.
        assert event["type"] == "realm_emoji"
        self.active_emoji_data, self.all_emoji_names = self.generate_all_emoji_data(
            event["realm_emoji"]
        )

    def _update_rendered_view(self, msg_id: int) -> None:
        """
        Helper method called by various _handle_* methods
        """
        # Update new content in the rendered view
        view = self.controller.view
        for msg_w in view.message_view.log:
            msg_box = msg_w.original_widget
            if msg_box.message["id"] == msg_id:
                # Remove the message if it no longer belongs in the current
                # narrow.
                if (
                    len(self.narrow) == 2
                    and msg_box.message["subject"] != self.narrow[1][1]
                ):
                    view.message_view.log.remove(msg_w)
                    # Change narrow if there are no messages left in the
                    # current narrow.
                    if not view.message_view.log:
                        msg_w_list = create_msg_box_list(
                            self, [msg_id], last_message=msg_box.last_message
                        )
                        if msg_w_list:
                            # FIXME Still depends on widget
                            widget = msg_w_list[0].original_widget
                            self.controller.narrow_to_topic(
                                stream_name=widget.stream_name,
                                topic_name=widget.topic_name,
                                contextual_message_id=widget.message["id"],
                            )
                    self.controller.update_screen()
                    return

                msg_w_list = create_msg_box_list(
                    self, [msg_id], last_message=msg_box.last_message
                )
                if not msg_w_list:
                    return
                else:
                    new_msg_w = msg_w_list[0]
                    msg_pos = view.message_view.log.index(msg_w)
                    view.message_view.log[msg_pos] = new_msg_w

                    # If this is not the last message in the view
                    # update the next message's last_message too.
                    if len(view.message_view.log) != (msg_pos + 1):
                        next_msg_w = view.message_view.log[msg_pos + 1]
                        msg_w_list = create_msg_box_list(
                            self,
                            [next_msg_w.original_widget.message["id"]],
                            last_message=new_msg_w.original_widget.message,
                        )
                        view.message_view.log[msg_pos + 1] = msg_w_list[0]
                    self.controller.update_screen()
                    return

    def _handle_user_settings_event(self, event: Event) -> None:
        """
        Event when user settings have changed - from ZFL 89, v5.0
        (previously "update_display_settings" and "update_global_notifications")
        """
        assert event["type"] == "user_settings"
        # We only expect these to be "update" event operations
        assert event["op"] == "update"
        # Update the setting (property) to the value, but only if already initialized
        if event["property"] in self._user_settings:
            setting = event["property"]
            self._user_settings[setting] = event["value"]

    def _handle_update_global_notifications_event(self, event: Event) -> None:
        assert event["type"] == "update_global_notifications"
        to_update = event["notification_name"]
        if to_update == "pm_content_in_desktop_notifications":
            self._user_settings[to_update] = event["setting"]

    def _handle_update_display_settings_event(self, event: Event) -> None:
        """
        Handle change to user display setting (Eg: Time format)
        """
        assert event["type"] == "update_display_settings"
        view = self.controller.view
        if event["setting_name"] == "twenty_four_hour_time":
            self._user_settings["twenty_four_hour_time"] = event["setting"]
            for msg_w in view.message_view.log:
                msg_box = msg_w.original_widget
                msg_id = msg_box.message["id"]
                last_msg = msg_box.last_message
                msg_pos = view.message_view.log.index(msg_w)
                msg_w_list = create_msg_box_list(self, [msg_id], last_message=last_msg)
                view.message_view.log[msg_pos] = msg_w_list[0]
        self.controller.update_screen()

    def _handle_realm_user_event(self, event: Event) -> None:
        """
        Handle change to user(s) metadata (Eg: full_name, timezone, etc.)
        """
        assert event["type"] == "realm_user"
        if event["op"] == "update":
            updated_details = event["person"]
            for realm_user in self.initial_data["realm_users"]:
                if realm_user["user_id"] == updated_details["user_id"]:
                    # realm_users has 'email' attribute and not 'new_email'
                    if "new_email" in updated_details:
                        realm_user["email"] = updated_details["new_email"]

                    elif "custom_profile_field" in updated_details:
                        profile_field_data = updated_details["custom_profile_field"]
                        profile_field_id = str(profile_field_data["id"])

                        if profile_field_data["value"] is None:
                            # Ignore if field does not exist
                            realm_user["profile_data"].pop(profile_field_id, None)
                        else:
                            updated_data = {
                                key: value
                                for key, value in profile_field_data.items()
                                if key != "id"
                            }
                            realm_user["profile_data"][profile_field_id] = updated_data
                    else:
                        realm_user.update(updated_details)
                    break

    def _register_desired_events(self, *, fetch_data: bool = False) -> str:
        fetch_types = None if not fetch_data else self.initial_data_to_fetch
        event_types = list(self.event_actions)
        try:
            response = self.client.register(
                event_types=event_types,
                fetch_event_types=fetch_types,
                client_gravatar=True,
                apply_markdown=True,
                include_subscribers=True,
            )
        except zulip.ZulipError as e:
            return str(e)

        if response["result"] == "success":
            if fetch_data:
                # FIXME: Improve methods to avoid updating `realm_users` on
                # every cycle. Add support for `realm_users` events too.
                self.initial_data.update(response)
            self.max_message_id = response["max_message_id"]
            self.queue_id = response["queue_id"]
            self.last_event_id = response["last_event_id"]
            return ""
        return response["msg"]

    @asynch
    def poll_for_events(self) -> None:
        reregister_timeout = 10
        queue_id = self.queue_id
        last_event_id = self.last_event_id
        while True:
            if queue_id is None:
                while True:
                    if not self._register_desired_events():
                        queue_id = self.queue_id
                        last_event_id = self.last_event_id
                        break
                    time.sleep(reregister_timeout)

            response = self.client.get_events(
                queue_id=queue_id, last_event_id=last_event_id
            )

            if "error" in response["result"]:
                if response.get("code") == "BAD_EVENT_QUEUE_ID":
                    # Our event queue went away, probably because
                    # we were asleep or the server restarted
                    # abnormally.  We may have missed some
                    # events while the network was down or
                    # something, but there's not really anything
                    # we can do about it other than resuming
                    # getting new ones.
                    #
                    # Reset queue_id to register a new event queue.
                    queue_id = None
                time.sleep(1)
                continue

            for event in response["events"]:
                last_event_id = max(last_event_id, int(event["id"]))
                if event["type"] in self.event_actions:
                    try:
                        self.event_actions[event["type"]](event)
                    except Exception:
                        import sys

                        self.controller.raise_exception_in_main_thread(
                            sys.exc_info(), critical=False
                        )
