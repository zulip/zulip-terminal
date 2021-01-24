import json
import time
from collections import OrderedDict, defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, wait
from copy import deepcopy
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
from typing_extensions import Literal, TypedDict

from zulipterminal import unicode_emojis
from zulipterminal.config.keys import primary_key_for_command
from zulipterminal.helper import (
    Message,
    NamedEmojiData,
    StreamData,
    asynch,
    canonicalize_color,
    classify_unread_counts,
    display_error_if_present,
    index_messages,
    initial_index,
    notify,
    set_count,
)
from zulipterminal.ui_tools.utils import create_msg_box_list


Event = TypedDict('Event', {
    'type': str,
    # typing:
    'sender': Dict[str, Any],  # 'email', ...
    # typing & reaction:
    'op': str,
    # reaction:
    'user': Dict[str, Any],  # 'email', 'user_id', 'full_name'
    'reaction_type': str,
    'emoji_code': str,
    'emoji_name': str,
    # reaction & update_message:
    'message_id': int,
    # update_message:
    'rendered_content': str,
    # update_message_flags:
    'messages': List[int],
    'operation': str,  # NOTE: deprecated in Zulip 4.0 / ZFL 32 -> 'op'
    'flag': str,
    'all': bool,
    # message:
    'message': Message,
    'flags': List[str],
    'subject': str,
    # subscription:
    'property': str,
    'user_id': int,  # Present when a streams subscribers are updated.
    'user_ids': List[int],  # NOTE: replaces 'user_id' in ZFL 35
    'stream_id': int,
    'stream_ids': List[int],  # NOTE: replaces 'stream_id' in ZFL 35 for peer*
    'value': bool,
    'message_ids': List[int]  # Present when subject of msg(s) is updated
}, total=False)  # Each Event will only have a subset of these

EditPropagateMode = Literal['change_one', 'change_all', 'change_later']

OFFLINE_THRESHOLD_SECS = 140


class ServerConnectionFailure(Exception):
    pass


def sort_streams(streams: List[StreamData]) -> None:
    """
    Used for sorting model.pinned_streams and model.unpinned_streams.
    """
    streams.sort(key=lambda s: s['name'].lower())


class Model:
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client

        self.narrow = []  # type: List[Any]
        self._have_last_message = {}  # type: Dict[str, bool]
        self.stream_id = -1
        self.recipients = frozenset()  # type: FrozenSet[Any]
        self.index = initial_index

        self.user_id = -1
        self.user_email = ""
        self.user_full_name = ""
        self.server_url = '{uri.scheme}://{uri.netloc}/'.format(
                          uri=urlparse(self.client.base_url))
        self.server_name = ""

        self._notified_user_of_notification_failure = False

        self.event_actions = OrderedDict([
            ('message', self._handle_message_event),
            ('update_message', self._handle_update_message_event),
            ('reaction', self._handle_reaction_event),
            ('subscription', self._handle_subscription_event),
            ('typing', self._handle_typing_event),
            ('update_message_flags', self._handle_update_message_flags_event),
        ])  # type: OrderedDict[str, Callable[[Event], None]]

        self.initial_data = {}  # type: Dict[str, Any]

        # Register to the queue before initializing further so that we don't
        # lose any updates while messages are being fetched.
        self._update_initial_data()

        self.server_version = self.initial_data['zulip_version']
        self.server_feature_level = (
            self.initial_data.get('zulip_feature_level')
        )

        self.users = self.get_all_users()

        subscriptions = self.initial_data['subscriptions']
        stream_data = Model._stream_info_from_subscriptions(subscriptions)
        (self.stream_dict, self.muted_streams,
         self.pinned_streams, self.unpinned_streams) = stream_data

        # NOTE: The expected response has been upgraded from
        # [stream_name, topic] to [stream_name, topic, date_muted] in
        # feature level 1, server version 3.0.
        muted_topics = self.initial_data['muted_topics']
        assert set(map(len, muted_topics)) in (set(), {2}, {3})
        self._muted_topics = {
            (stream_name, topic): (None if self.server_feature_level is None
                                   else date_muted[0])
            for stream_name, topic, *date_muted in muted_topics
        }  # type: Dict[Tuple[str, str], Optional[int]]

        groups = self.initial_data['realm_user_groups']
        self.user_group_by_id = {}  # type: Dict[int, Dict[str, Any]]
        self.user_group_names = self._group_info_from_realm_user_groups(groups)

        self.unread_counts = classify_unread_counts(self)

        self._draft = None  # type: Optional[Message]
        unicode_emoji_data = unicode_emojis.EMOJI_DATA
        for name, data in unicode_emoji_data.items():
            data['type'] = 'unicode_emoji'
        typed_unicode_emoji_data = cast(NamedEmojiData, unicode_emoji_data)
        custom_emoji_data = self.fetch_custom_emojis()
        zulip_extra_emoji = {
                'zulip': {'code': 'zulip', 'type': 'zulip_extra_emoji'}
        }  # type: NamedEmojiData
        all_emoji_data = {**typed_unicode_emoji_data,
                          **custom_emoji_data,
                          **zulip_extra_emoji}.items()
        self.active_emoji_data = OrderedDict(sorted(all_emoji_data,
                                                    key=lambda e: e[0]))

        self.new_user_input = True
        self._start_presence_updates()

    def get_focus_in_current_narrow(self) -> Union[int, Set[None]]:
        """
        Returns the focus in the current narrow.
        For no existing focus this returns {}, otherwise the message ID.
        """
        return self.index['pointer'][repr(self.narrow)]

    def set_focus_in_current_narrow(self, focus_message: int) -> None:
        self.index['pointer'][repr(self.narrow)] = focus_message

    def is_search_narrow(self) -> bool:
        """
        Checks if the current narrow is a result of a previous search for
        a messages in a different narrow.
        """
        return 'search' in [subnarrow[0] for subnarrow in self.narrow]

    def set_narrow(self, *,
                   stream: Optional[str]=None,
                   topic: Optional[str]=None,
                   pms: bool=False,
                   pm_with: Optional[str]=None,
                   starred: bool=False,
                   mentioned: bool=False) -> bool:
        selected_params = {k for k, v in locals().items() if k != 'self' and v}
        valid_narrows = {
            frozenset(): [],
            frozenset(['stream']): [['stream', stream]],
            frozenset(['stream', 'topic']): [['stream', stream],
                                             ['topic', topic]],
            frozenset(['pms']): [['is', 'private']],
            frozenset(['pm_with']): [['pm_with', pm_with]],
            frozenset(['starred']): [['is', 'starred']],
            frozenset(['mentioned']): [['is', 'mentioned']],
        }  # type: Dict[FrozenSet[str], List[Any]]
        for narrow_param, narrow in valid_narrows.items():
            if narrow_param == selected_params:
                new_narrow = narrow
                break
        else:
            raise RuntimeError("Model.set_narrow parameters used incorrectly.")

        if new_narrow != self.narrow:
            self.narrow = new_narrow

            if pm_with is not None and new_narrow[0][0] == 'pm_with':
                users = pm_with.split(', ')
                self.recipients = frozenset(
                    [self.user_dict[user]['user_id'] for user in users]
                    + [self.user_id]
                )
            else:
                self.recipients = frozenset()
            return False
        else:
            return True

    def set_search_narrow(self, search_query: str) -> None:
        self.unset_search_narrow()
        self.narrow.append(['search', search_query])

    def unset_search_narrow(self) -> None:
        # If current narrow is a result of a previous started search,
        # we pop the ['search', 'text'] term in the narrow, before
        # setting a new narrow.
        if self.is_search_narrow():
            self.narrow = [item for item in self.narrow
                           if item[0] != 'search']

    def get_message_ids_in_current_narrow(self) -> Set[int]:
        narrow = self.narrow
        index = self.index
        if narrow == []:
            ids = index['all_msg_ids']
        elif self.is_search_narrow():  # Check searches first
            ids = index['search']
        elif narrow[0][0] == 'stream':
            stream_id = self.stream_id
            if len(narrow) == 1:
                ids = index['stream_msg_ids_by_stream_id'][stream_id]
            elif len(narrow) == 2:
                topic = narrow[1][1]
                ids = index['topic_msg_ids'][stream_id].get(topic, set())
        elif narrow[0][1] == 'private':
            ids = index['private_msg_ids']
        elif narrow[0][0] == 'pm_with':
            recipients = self.recipients
            ids = index['private_msg_ids_by_user_ids'].get(recipients, set())
        elif narrow[0][1] == 'starred':
            ids = index['starred_msg_ids']
        elif narrow[0][1] == 'mentioned':
            ids = index['mentioned_msg_ids']
        return ids.copy()

    def _notify_server_of_presence(self) -> Dict[str, Any]:
        response = self.client.update_presence(
                request={
                    # TODO: Determine `status` from terminal tab focus.
                    'status': 'active' if self.new_user_input else 'idle',
                    'new_user_input': self.new_user_input,
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
            if response['result'] == 'success':
                self.initial_data['presences'] = response['presences']
                self.users = self.get_all_users()
                if hasattr(self.controller, 'view'):
                    self.controller.view.users_view.update_user_list(
                        user_list=self.users)
            time.sleep(60)

    @asynch
    def react_to_message(self,
                         message: Message,
                         reaction_to_toggle: str) -> None:
        # FIXME Only support thumbs_up for now
        assert reaction_to_toggle == 'thumbs_up'

        reaction_to_toggle_spec = dict(
            emoji_name='thumbs_up',
            emoji_code='1f44d',
            reaction_type='unicode_emoji',
            message_id=str(message['id']))
        existing_reactions = [
            reaction['emoji_code']
            for reaction in message['reactions']
            if (reaction['user'].get('user_id', None) == self.user_id
                or reaction['user'].get('id', None) == self.user_id)
        ]
        if reaction_to_toggle_spec['emoji_code'] in existing_reactions:
            response = self.client.remove_reaction(reaction_to_toggle_spec)
        else:
            response = self.client.add_reaction(reaction_to_toggle_spec)
        display_error_if_present(response, self.controller)

    def session_draft_message(self) -> Optional[Message]:
        return deepcopy(self._draft)

    def save_draft(self, message: Message) -> None:
        self._draft = deepcopy(message)
        self.controller.view.set_footer_text("Saved message as draft", 3)

    @asynch
    def toggle_message_star_status(self, message: Message) -> None:
        base_request = dict(flag='starred', messages=[message['id']])
        if 'starred' in message['flags']:
            request = dict(base_request, op='remove')
        else:
            request = dict(base_request, op='add')
        response = self.client.update_message_flags(request)
        display_error_if_present(response, self.controller)

    @asynch
    def mark_message_ids_as_read(self, id_list: List[int]) -> None:
        if not id_list:
            return
        response = self.client.update_message_flags({
            'messages': id_list,
            'flag': 'read',
            'op': 'add',
        })
        display_error_if_present(response, self.controller)

    @asynch
    def send_typing_status_by_user_ids(self, recipient_user_ids: List[int],
                                       *, status: Literal['start', 'stop']
                                       ) -> None:
        if recipient_user_ids:
            request = {
                'to': recipient_user_ids,
                'op': status
            }
            response = self.client.set_typing_status(request)
            display_error_if_present(response, self.controller)
        else:
            raise RuntimeError('Empty recipient list.')

    def send_private_message(self, recipients: List[str],
                             content: str) -> bool:
        if recipients:
            request = {
                'type': 'private',
                'to': recipients,
                'content': content,
            }
            response = self.client.send_message(request)
            display_error_if_present(response, self.controller)
            return response['result'] == 'success'
        else:
            raise RuntimeError('Empty recipients list.')

    def send_stream_message(self, stream: str, topic: str,
                            content: str) -> bool:
        request = {
            'type': 'stream',
            'to': stream,
            'subject': topic,
            'content': content,
        }
        response = self.client.send_message(request)
        display_error_if_present(response, self.controller)
        return response['result'] == 'success'

    def update_private_message(self, msg_id: int, content: str) -> bool:
        request = {
            "message_id": msg_id,
            "content": content,
        }
        response = self.client.update_message(request)
        display_error_if_present(response, self.controller)
        return response['result'] == 'success'

    def update_stream_message(self, topic: str, message_id: int,
                              propagate_mode: EditPropagateMode,
                              content: Optional[str]=None) -> bool:
        request = {
            "message_id": message_id,
            "propagate_mode": propagate_mode,
            "topic": topic,
        }
        if content is not None:
            request['content'] = content

        response = self.client.update_message(request)
        display_error_if_present(response, self.controller)
        return response['result'] == 'success'

    def fetch_custom_emojis(self) -> NamedEmojiData:
        response = self.client.get_realm_emoji()
        custom_emojis = {emoji['name']: {'code': emoji_code,
                                         'type': 'realm_emoji'}
                         for emoji_code, emoji in response['emoji'].items()
                         if not emoji['deactivated']}  # type: NamedEmojiData
        display_error_if_present(response, self.controller)
        return custom_emojis

    def get_messages(self, *,
                     num_after: int, num_before: int,
                     anchor: Optional[int]) -> str:
        # anchor value may be specific message (int) or next unread (None)
        first_anchor = anchor is None
        anchor_value = anchor if anchor is not None else 0

        request = {
            'anchor': anchor_value,
            'num_before': num_before,
            'num_after': num_after,
            'apply_markdown': True,
            'use_first_unread_anchor': first_anchor,
            'client_gravatar': True,
            'narrow': json.dumps(self.narrow),
        }
        response = self.client.get_messages(message_filters=request)
        if response['result'] == 'success':
            self.index = index_messages(response['messages'], self, self.index)
            narrow_str = repr(self.narrow)
            if first_anchor and response['anchor'] != 10000000000000000:
                self.index['pointer'][narrow_str] = response['anchor']
            if 'found_newest' in response:
                self._have_last_message[narrow_str] = response['found_newest']
            else:
                # Older versions of the server does not contain the
                # 'found_newest' flag. Instead, we use this logic:
                query_range = num_after + num_before + 1
                self._have_last_message[narrow_str] = (
                    len(response['messages']) < query_range)
            return ""
        display_error_if_present(response, self.controller)
        return response['msg']

    def fetch_message_history(self, message_id: int,
                              ) -> List[Dict[str, Union[int, str]]]:
        """
        Fetches message edit history for a message using its ID.
        """
        response = self.client.get_message_history(message_id)
        if response['result'] == 'success':
            return response['message_history']
        display_error_if_present(response, self.controller)
        return list()

    def _fetch_topics_in_streams(self, stream_list: Iterable[int]) -> str:
        """
        Fetch all topics with specified stream_id's and
        index their names (Version 1)
        """
        # FIXME: Version 2: Fetch last 'n' recent topics for each stream.
        for stream_id in stream_list:
            response = self.client.get_stream_topics(stream_id)
            if response['result'] == 'success':
                self.index['topics'][stream_id] = [topic['name'] for
                                                   topic in response['topics']]
            else:
                display_error_if_present(response, self.controller)
                return response['msg']
        return ""

    def topics_in_stream(self, stream_id: int) -> List[str]:
        """
        Returns a list of topic names for stream_id from the index.
        """
        if not self.index['topics'][stream_id]:
            self._fetch_topics_in_streams([stream_id])

        return list(self.index['topics'][stream_id])

    @staticmethod
    def exception_safe_result(future: 'Future[str]') -> str:
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
        stream_name = self.stream_dict[stream_id]['name']
        topic_to_search = (stream_name, topic)
        return topic_to_search in self._muted_topics.keys()

    def _update_initial_data(self) -> None:
        # Thread Processes to reduce start time.
        # NOTE: Exceptions do not work well with threads
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {
                'get_messages': executor.submit(self.get_messages,
                                                num_after=10,
                                                num_before=30,
                                                anchor=None),
                'register': executor.submit(self._register_desired_events,
                                            fetch_data=True),
            }  # type: Dict[str, Future[str]]

            # Wait for threads to complete
            wait(futures.values())

        results = {
            name: self.exception_safe_result(future)
            for name, future in futures.items()
        }  # type: Dict[str, str]
        if not any(results.values()):
            self.user_id = self.initial_data['user_id']
            self.user_email = self.initial_data['email']
            self.user_full_name = self.initial_data['full_name']
            self.server_name = self.initial_data['realm_name']
        else:
            failures = defaultdict(list)  # type: DefaultDict[str, List[str]]
            for name, result in results.items():
                if result:
                    failures[result].append(name)
            failure_text = [
                "{} ({})".format(error, ", ".join(sorted(calls)))
                for error, calls in failures.items()
            ]
            raise ServerConnectionFailure(", ".join(failure_text))

    def get_other_subscribers_in_stream(self, stream_id: Optional[int]=None,
                                        stream_name: Optional[str]=None,
                                        ) -> List[int]:
        assert stream_id is not None or stream_name is not None

        if stream_id:
            assert self.is_user_subscribed_to_stream(stream_id)

            return [sub
                    for sub in self.stream_dict[stream_id]['subscribers']
                    if sub != self.user_id]
        else:
            return [sub
                    for _, stream in self.stream_dict.items()
                    for sub in stream['subscribers']
                    if stream['name'] == stream_name
                    if sub != self.user_id]

    def get_all_users(self) -> List[Dict[str, Any]]:
        # Dict which stores the active/idle status of users (by email)
        presences = self.initial_data['presences']

        # Construct a dict of each user in the realm to look up by email
        # and a user-id to email mapping
        self.user_dict = dict()  # type: Dict[str, Dict[str, Any]]
        self.user_id_email_dict = dict()  # type: Dict[int, str]
        for user in self.initial_data['realm_users']:
            if self.user_id == user['user_id']:
                current_user = {
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'user_id': user['user_id'],
                    'status': 'active',
                }
                continue
            email = user['email']
            if email in presences:  # presences currently subset of all users
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
                aggregate_status = 'offline'
                for client in presences[email].items():
                    client_name = client[0]
                    status = client[1]['status']
                    timestamp = client[1]['timestamp']
                    if client_name == 'aggregated':
                        continue
                    elif (time.time() - timestamp) < OFFLINE_THRESHOLD_SECS:
                        if status == 'active':
                            aggregate_status = 'active'
                        if status == 'idle':
                            if aggregate_status != 'active':
                                aggregate_status = status
                        if status == 'offline':
                            if (aggregate_status != 'active'
                                    and aggregate_status != 'idle'):
                                aggregate_status = status

                status = aggregate_status
            else:
                # Set status of users not in the  `presence` list
                # as 'inactive'. They will not be displayed in the
                # user's list by default (only in the search list).
                status = 'inactive'
            self.user_dict[email] = {
                'full_name': user['full_name'],
                'email': email,
                'user_id': user['user_id'],
                'status': status,
            }
            self.user_id_email_dict[user['user_id']] = email

        # Add internal (cross-realm) bots to dicts
        for bot in self.initial_data['cross_realm_bots']:
            email = bot['email']
            self.user_dict[email] = {
                'full_name': bot['full_name'],
                'email': email,
                'user_id': bot['user_id'],
                'status': 'inactive',
            }
            self.user_id_email_dict[bot['user_id']] = email

        # Generate filtered lists for active & idle users
        active = [properties for properties in self.user_dict.values()
                  if properties['status'] == 'active']
        idle = [properties for properties in self.user_dict.values()
                if properties['status'] == 'idle']
        offline = [properties for properties in self.user_dict.values()
                   if properties['status'] == 'offline']
        inactive = [properties for properties in self.user_dict.values()
                    if properties['status'] == 'inactive']

        # Construct user_list from sorted components of each list
        user_list = sorted(active, key=lambda u: u['full_name'].casefold())
        user_list += sorted(idle, key=lambda u: u['full_name'].casefold())
        user_list += sorted(offline, key=lambda u: u['full_name'].casefold())
        user_list += sorted(inactive, key=lambda u: u['full_name'].casefold())
        # Add current user to the top of the list
        user_list.insert(0, current_user)
        self.user_dict[current_user['email']] = current_user
        self.user_id_email_dict[self.user_id] = current_user['email']

        return user_list

    def user_name_from_id(self, user_id: int) -> str:
        """
        Returns user's full name given their ID.
        """
        user_email = self.user_id_email_dict.get(user_id)

        if not user_email:
            raise RuntimeError('Invalid user ID.')

        return self.user_dict[user_email]['full_name']

    @staticmethod
    def _stream_info_from_subscriptions(
            subscriptions: List[Dict[str, Any]]
    ) -> Tuple[Dict[int, Any], Set[int], List[StreamData], List[StreamData]]:

        def make_reduced_stream_data(stream: Dict[str, Any]) -> StreamData:
            # stream_id has been changed to id.
            return StreamData({'name': stream['name'],
                               'id': stream['stream_id'],
                               'color': stream['color'],
                               'invite_only': stream['invite_only'],
                               'description': stream['description']})
        # Canonicalize color formats, since zulip server versions may use
        # different formats
        for subscription in subscriptions:
            subscription['color'] = canonicalize_color(subscription['color'])

        pinned_streams = [make_reduced_stream_data(stream)
                          for stream in subscriptions if stream['pin_to_top']]
        unpinned_streams = [make_reduced_stream_data(stream)
                            for stream in subscriptions
                            if not stream['pin_to_top']]
        sort_streams(pinned_streams)
        sort_streams(unpinned_streams)
        # Mapping of stream-id to all available stream info
        # Stream IDs for muted streams
        # Limited stream info sorted by name (used in display)
        return (
            {stream['stream_id']: stream for stream in subscriptions},
            {stream['stream_id'] for stream in subscriptions
             if stream['in_home_view'] is False},
            pinned_streams,
            unpinned_streams,
        )

    def _group_info_from_realm_user_groups(self,
                                           groups: List[Dict[str, Any]]
                                           ) -> List[str]:
        """
        Stores group information in the model and returns a list of
        group_names which helps in group typeahead. (Eg: @*terminal*)
        """
        for sub_group in groups:
            self.user_group_by_id[sub_group['id']] = {
                key: sub_group[key] for key in sub_group if key != 'id'}
        user_group_names = [self.user_group_by_id[group_id]['name']
                            for group_id in self.user_group_by_id]
        # Sort groups for typeahead to work alphabetically (case-insensitive)
        user_group_names.sort(key=str.lower)
        return user_group_names

    def toggle_stream_muted_status(self, stream_id: int) -> None:
        request = [{
            'stream_id': stream_id,
            'property': 'is_muted',
            'value': not self.is_muted_stream(stream_id)
            # True for muting and False for unmuting.
        }]
        response = self.client.update_subscription_settings(request)
        display_error_if_present(response, self.controller)

    def stream_id_from_name(self, stream_name: str) -> int:
        for stream_id, stream in self.stream_dict.items():
            if stream['name'] == stream_name:
                return stream_id
        raise RuntimeError("Invalid stream name.")

    def is_pinned_stream(self, stream_id: int) -> bool:
        return stream_id in [stream['id'] for stream in self.pinned_streams]

    def toggle_stream_pinned_status(self, stream_id: int) -> bool:
        request = [{
            'stream_id': stream_id,
            'property': 'pin_to_top',
            'value': not self.is_pinned_stream(stream_id)
        }]
        response = self.client.update_subscription_settings(request)
        return response['result'] == 'success'

    def is_user_subscribed_to_stream(self, stream_id: int) -> bool:
        return stream_id in self.stream_dict

    def _handle_subscription_event(self, event: Event) -> None:
        """
        Handle changes in subscription (eg. muting/unmuting,
                                        pinning/unpinning streams)
        """
        def get_stream_by_id(streams: List[StreamData], stream_id: int
                             ) -> StreamData:
            for stream in streams:
                if stream['id'] == stream_id:
                    return stream
            raise RuntimeError("Invalid stream id.")

        if event['op'] == 'update':
            if hasattr(self.controller, 'view'):
                if event.get('property', None) == 'in_home_view':
                    stream_id = event['stream_id']

                    # FIXME: Does this always contain the stream_id?
                    stream_button = (
                        self.controller.view.stream_id_to_button[stream_id]
                    )

                    unread_count = self.unread_counts['streams'][stream_id]
                    if event['value']:  # Unmuting streams
                        self.muted_streams.remove(stream_id)
                        self.unread_counts['all_msg'] += unread_count
                        stream_button.mark_unmuted(unread_count)
                    else:  # Muting streams
                        self.muted_streams.add(stream_id)
                        self.unread_counts['all_msg'] -= unread_count
                        stream_button.mark_muted()
                    self.controller.update_screen()
                elif event.get('property', None) == 'pin_to_top':
                    stream_id = event['stream_id']

                    # FIXME: Does this always contain the stream_id?
                    stream_button = (
                        self.controller.view.stream_id_to_button[stream_id]
                    )

                    if event['value']:
                        stream = get_stream_by_id(self.unpinned_streams,
                                                  stream_id)
                        if stream:
                            self.unpinned_streams.remove(stream)
                            self.pinned_streams.append(stream)
                    else:
                        stream = get_stream_by_id(self.pinned_streams,
                                                  stream_id)
                        if stream:
                            self.pinned_streams.remove(stream)
                            self.unpinned_streams.append(stream)
                    sort_streams(self.unpinned_streams)
                    sort_streams(self.pinned_streams)
                    self.controller.view.left_panel.update_stream_view()
                    self.controller.update_screen()
        elif event['op'] in ('peer_add', 'peer_remove'):
            # NOTE: ZFL 35 commit was not atomic with API change
            #       (ZFL >=35 can use new plural style)
            if 'stream_ids' not in event or 'user_ids' not in event:
                stream_ids = [event['stream_id']]
                user_ids = [event['user_id']]
            else:
                stream_ids = event['stream_ids']
                user_ids = event['user_ids']

            for stream_id in stream_ids:
                if self.is_user_subscribed_to_stream(stream_id):
                    subscribers = self.stream_dict[stream_id]['subscribers']
                    if event['op'] == 'peer_add':
                        subscribers.extend(user_ids)
                    else:
                        for user_id in user_ids:
                            subscribers.remove(user_id)

    def _handle_typing_event(self, event: Event) -> None:
        """
        Handle typing notifications (in private messages)
        """
        if hasattr(self.controller, 'view'):
            # If the user is in pm narrow with the person typing
            narrow = self.narrow
            if (len(narrow) == 1 and narrow[0][0] == 'pm_with'
                    and event['sender']['email'] in narrow[0][1].split(',')):
                if event['op'] == 'start':
                    user = self.user_dict[event['sender']['email']]
                    self.controller.view.set_footer_text([
                        ' ',
                        ('code', user['full_name']),
                        ' is typing...'
                    ])
                elif event['op'] == 'stop':
                    self.controller.view.set_footer_text()
                else:
                    raise RuntimeError("Unknown typing event operation")

    def get_invalid_recipient_emails(self, recipient_emails: List[str]
                                     ) -> List[str]:

        return [email for email in recipient_emails
                if email not in self.user_dict]

    def is_valid_stream(self, stream_name: str) -> bool:
        for stream in self.stream_dict.values():
            if stream['name'] == stream_name:
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
        if message['sender_id'] == self.user_id:
            return ""

        recipient = ''
        if message['type'] == 'private':
            target = 'you'
            if len(message['display_recipient']) > 2:
                extra_targets = [target] + [
                    recip['full_name']
                    for recip in message['display_recipient']
                    if recip['id'] not in (self.user_id, message['sender_id'])
                ]
                target = ', '.join(extra_targets)
            recipient = ' (to {})'.format(target)
        elif message['type'] == 'stream' and (
            {'mentioned', 'wildcard_mentioned'}.intersection(
                set(message['flags'])
            )
            or self.stream_dict[message['stream_id']]['desktop_notifications']
        ):
            recipient = ' (to {} -> {})'.format(message['display_recipient'],
                                                message['subject'])

        if recipient:
            return notify((self.server_name + ":\n"
                           + message['sender_full_name'] + recipient),
                          message['content'])
        return ""

    def _handle_message_event(self, event: Event) -> None:
        """
        Handle new messages (eg. add message to the end of the view)
        """
        message = event['message']
        # sometimes `flags` are missing in `event` so initialize
        # an empty list of flags in that case.
        message['flags'] = event.get('flags', [])
        # We need to update the topic order in index, unconditionally.
        if message['type'] == 'stream':
            # NOTE: The subsequent helper only updates the topic index based
            # on the message event not the UI (the UI is updated in a
            # consecutive block independently). However, it is critical to keep
            # the topics index synchronized as it used whenever the topics list
            # view is reconstructed later.
            self._update_topic_index(message['stream_id'],
                                     message['subject'])
            # If the topic view is toggled for incoming message's
            # recipient stream, then we re-arrange topic buttons
            # with most recent at the top.
            if hasattr(self.controller, 'view'):
                view = self.controller.view
                if (view.left_panel.is_in_topic_view_with_stream_id(
                        message['stream_id'])):
                    view.topic_w.update_topics_list(
                        message['stream_id'], message['subject'],
                        message['sender_id'])
                    self.controller.update_screen()

        # We can notify user regardless of whether UI is rendered or not,
        # but depend upon the UI to indicate failures.
        failed_command = self.notify_user(message)
        if (failed_command
                and hasattr(self.controller, 'view')
                and not self._notified_user_of_notification_failure):
            notice_template = (
                "You have enabled notifications, but your notification "
                "command '{}' could not be found."
                "\n\n"
                "The application will continue attempting to run this command "
                "in this session, but will not notify you again."
                "\n\n"
                "Press '{}' to close this window."
            )
            notice = notice_template.format(failed_command,
                                            primary_key_for_command("GO_BACK"))
            self.controller.popup_with_message(notice, width=50)
            self.controller.update_screen()
            self._notified_user_of_notification_failure = True

        # Index messages before calling set_count.
        self.index = index_messages([message], self, self.index)
        if 'read' not in message['flags']:
            set_count([message['id']], self.controller, 1)

        if (hasattr(self.controller, 'view')
                and self._have_last_message[repr(self.narrow)]):
            msg_log = self.controller.view.message_view.log
            if msg_log:
                last_message = msg_log[-1].original_widget.message
            else:
                last_message = None
            msg_w_list = create_msg_box_list(self, [message['id']],
                                             last_message=last_message)
            if not msg_w_list:
                return
            else:
                msg_w = msg_w_list[0]

            if not self.narrow:
                msg_log.append(msg_w)

            elif (self.narrow[0][1] == 'mentioned'
                    and 'mentioned' in message['flags']):
                msg_log.append(msg_w)

            elif (self.narrow[0][1] == message['type']
                    and len(self.narrow) == 1):
                msg_log.append(msg_w)

            elif (message['type'] == 'stream'
                    and self.narrow[0][0] == "stream"):
                recipient_stream = message['display_recipient']
                narrow_stream = self.narrow[0][1]
                append_to_stream = recipient_stream == narrow_stream

                if (append_to_stream
                    and (len(self.narrow) == 1
                         or (len(self.narrow) == 2
                             and self.narrow[1][1] == message['subject']))):
                    msg_log.append(msg_w)

            elif (message['type'] == 'private' and len(self.narrow) == 1
                    and self.narrow[0][0] == "pm_with"):
                narrow_recipients = self.recipients
                message_recipients = frozenset(
                    [user['id'] for user in message['display_recipient']])
                if narrow_recipients == message_recipients:
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
        self.index['topics'][stream_id] = topic_list

    def _handle_update_message_event(self, event: Event) -> None:
        """
        Handle updated (edited) messages (changed content/subject)
        """
        # Update edited message status from single message id
        # NOTE: If all messages in topic have topic edited,
        #       they are not all marked as edited, as per server optimization
        message_id = event['message_id']
        indexed_message = self.index['messages'].get(message_id, None)

        if indexed_message:
            self.index['edited_messages'].add(message_id)

        # Update the rendered content, if the message is indexed
        if 'rendered_content' in event and indexed_message:
            indexed_message['content'] = event['rendered_content']
            self.index['messages'][message_id] = indexed_message
            self._update_rendered_view(message_id)

        # NOTE: This is independent of messages being indexed
        # Previous assertion:
        # * 'subject' is not present in update event if
        #   the event didn't have a 'subject' update.
        if 'subject' in event:
            new_subject = event['subject']
            stream_id = event['stream_id']

            # Update any indexed messages & re-render them
            for msg_id in event['message_ids']:
                indexed_msg = self.index['messages'].get(msg_id)
                if indexed_msg:
                    indexed_msg['subject'] = new_subject
                    self._update_rendered_view(msg_id)

            # If topic view is open, reload list else reset cache.
            if stream_id in self.index['topics']:
                if hasattr(self.controller, 'view'):
                    view = self.controller.view
                    if (view.left_panel.is_in_topic_view_with_stream_id(
                            stream_id)):
                        self._fetch_topics_in_streams([stream_id])
                        view.left_panel.show_topic_view(
                            view.topic_w.stream_button)
                        self.controller.update_screen()
                    else:
                        self.index['topics'][stream_id] = []

    def _handle_reaction_event(self, event: Event) -> None:
        """
        Handle change to reactions on a message
        """
        message_id = event['message_id']
        # If the message is indexed
        if self.index['messages'][message_id] != {}:

            message = self.index['messages'][message_id]
            if event['op'] == 'add':
                message['reactions'].append(
                    {
                        'user': event['user'],
                        'reaction_type': event['reaction_type'],
                        'emoji_code': event['emoji_code'],
                        'emoji_name': event['emoji_name'],
                    }
                )
            else:
                emoji_code = event['emoji_code']
                for reaction in message['reactions']:
                    # Since Who reacted is not displayed,
                    # remove the first one encountered
                    if reaction['emoji_code'] == emoji_code:
                        message['reactions'].remove(reaction)

            self.index['messages'][message_id] = message
            self._update_rendered_view(message_id)

    def _handle_update_message_flags_event(self, event: Event) -> None:
        """
        Handle change to message flags (eg. starred, read)
        """
        if (self.server_feature_level is None
                or self.server_feature_level < 32):
            operation = event['operation']
        else:
            operation = event['op']

        if event['all']:  # FIXME Should handle eventually
            return

        flag_to_change = event['flag']
        if flag_to_change not in {'starred', 'read'}:
            return

        if flag_to_change == 'read' and operation == 'remove':
            return

        indexed_message_ids = set(self.index['messages'])
        message_ids_to_mark = set(event['messages'])

        for message_id in message_ids_to_mark & indexed_message_ids:
            msg = self.index['messages'][message_id]
            if operation == 'add':
                if flag_to_change not in msg['flags']:
                    msg['flags'].append(flag_to_change)
            elif operation == 'remove':
                if flag_to_change in msg['flags']:
                    msg['flags'].remove(flag_to_change)
            else:
                raise RuntimeError(event, msg['flags'])

            self.index['messages'][message_id] = msg
            self._update_rendered_view(message_id)

        if operation == 'add' and flag_to_change == 'read':
            set_count(list(message_ids_to_mark & indexed_message_ids),
                      self.controller, -1)

    def _update_rendered_view(self, msg_id: int) -> None:
        """
        Helper method called by various _handle_* methods
        """
        # Update new content in the rendered view
        view = self.controller.view
        for msg_w in view.message_view.log:
            msg_box = msg_w.original_widget
            if msg_box.message['id'] == msg_id:
                # Remove the message if it no longer belongs in the current
                # narrow.
                if (len(self.narrow) == 2
                        and msg_box.message['subject'] != self.narrow[1][1]):
                    view.message_view.log.remove(msg_w)
                    # Change narrow if there are no messages left in the
                    # current narrow.
                    if not view.message_view.log:
                        msg_w_list = create_msg_box_list(
                                        self, [msg_id],
                                        last_message=msg_box.last_message)
                        if msg_w_list:
                            self.controller.narrow_to_topic(
                                msg_w_list[0].original_widget)
                    self.controller.update_screen()
                    return

                msg_w_list = create_msg_box_list(
                                self, [msg_id],
                                last_message=msg_box.last_message)
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
                            self, [next_msg_w.original_widget.message['id']],
                            last_message=new_msg_w.original_widget.message)
                        view.message_view.log[msg_pos + 1] = msg_w_list[0]
                    self.controller.update_screen()
                    return

    def _register_desired_events(self, *, fetch_data: bool=False) -> str:
        fetch_types = None if not fetch_data else [
            'realm',
            'presence',
            'subscription',
            'message',
            'update_message_flags',
            'muted_topics',
            'realm_user',  # Enables cross_realm_bots
            'realm_user_groups',
            # zulip_version and zulip_feature_level are always returned in
            # POST /register from Feature level 3.
            'zulip_version',
        ]
        event_types = list(self.event_actions)
        try:
            response = self.client.register(event_types=event_types,
                                            fetch_event_types=fetch_types,
                                            client_gravatar=True,
                                            apply_markdown=True,
                                            include_subscribers=True)
        except zulip.ZulipError as e:
            return str(e)

        if response['result'] == 'success':
            if fetch_data:
                self.initial_data.update(response)
            self.max_message_id = response['max_message_id']
            self.queue_id = response['queue_id']
            self.last_event_id = response['last_event_id']
            return ""
        return response['msg']

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
                queue_id=queue_id,
                last_event_id=last_event_id
            )

            if 'error' in response['result']:
                if response["msg"].startswith("Bad event queue id:"):
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

            for event in response['events']:
                last_event_id = max(last_event_id, int(event['id']))
                if event['type'] in self.event_actions:
                    try:
                        self.event_actions[event['type']](event)
                    except Exception:
                        import sys
                        (self.controller.
                         raise_exception_in_main_thread(sys.exc_info(),
                                                        critical=False))
