import json
import time
from collections import OrderedDict, defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, wait
from threading import Thread
from typing import (
    Any, Callable, DefaultDict, Dict, FrozenSet, Iterable, List, Optional, Set,
    Tuple, Union,
)
from urllib.parse import urlparse

import zulip
from mypy_extensions import TypedDict

from zulipterminal.helper import (
    Message, asynch, canonicalize_color, classify_unread_counts,
    index_messages, initial_index, notify, set_count,
)
from zulipterminal.ui_tools.utils import create_msg_box_list


GetMessagesArgs = TypedDict('GetMessagesArgs', {
     'num_before': int,
     'num_after': int,
     'anchor': Optional[int]
    })

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
    'operation': str,
    'flag': str,
    'all': bool,
    # message:
    'message': Message,
    'flags': List[str],
    'subject': str,
    # subscription:
    'property': str,
    'stream_id': int,
    'value': bool,
    'message_ids': List[int]  # Present when subject of msg(s) is updated
}, total=False)  # Each Event will only have a subset of these

OFFLINE_THRESHOLD_SECS = 140


class ServerConnectionFailure(Exception):
    pass


class Model:
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client

        self.msg_view = None  # type: Any
        self.msg_list = None  # type: Any
        self.narrow = []  # type: List[Any]
        self.found_newest = False
        self.stream_id = -1
        self.recipients = frozenset()  # type: FrozenSet[Any]
        self.index = initial_index

        self.user_id = -1  # type: int
        self.user_email = ""
        self.user_full_name = ""
        self.server_url = '{uri.scheme}://{uri.netloc}/'.format(
                          uri=urlparse(self.client.base_url))
        self.server_name = ""

        self.event_actions = OrderedDict([
            ('message', self.append_message),
            ('update_message', self.update_message),
            ('reaction', self.update_reaction),
            ('subscription', self.update_subscription),
            ('typing', self.handle_typing_event),
            ('update_message_flags', self.update_message_flag_status),
        ])  # type: OrderedDict[str, Callable[[Event], None]]

        self.initial_data = {}  # type: Dict[str, Any]

        # Register to the queue before initializing further so that we don't
        # lose any updates while messages are being fetched.
        self._update_initial_data()

        self.users = self.get_all_users()

        subscriptions = self.initial_data['subscriptions']
        stream_data = Model._stream_info_from_subscriptions(subscriptions)
        (self.stream_dict, self.muted_streams,
         self.pinned_streams, self.unpinned_streams) = stream_data

        self.muted_topics = (
            self.initial_data['muted_topics'])  # type: List[List[str]]

        groups = self.initial_data['realm_user_groups']
        self.user_group_by_id = {}  # type: Dict[int, Dict[str, Any]]
        self.user_group_names = self._group_info_from_realm_user_groups(groups)

        self.unread_counts = classify_unread_counts(self)

        self.fetch_all_topics(workers=5)

        self.new_user_input = True
        self._start_presence_updates()

    def get_focus_in_current_narrow(self) -> Union[int, Set[None]]:
        """
        Returns the focus in the current narrow.
        For no existing focus this returns {}, otherwise the message ID.
        """
        return self.index['pointer'][str(self.narrow)]

    def set_focus_in_current_narrow(self, focus_message: int) -> None:
        self.index['pointer'][str(self.narrow)] = focus_message

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
                    [self.user_dict[user]['user_id'] for user in users] +
                    [self.user_id]
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
            if (('user_id' in reaction['user'] and
                reaction['user']['user_id'] == self.user_id)) or
               (('id' in reaction['user'] and
                reaction['user']['id'] == self.user_id))
        ]
        if reaction_to_toggle_spec['emoji_code'] in existing_reactions:
            response = self.client.remove_reaction(reaction_to_toggle_spec)
        else:
            response = self.client.add_reaction(reaction_to_toggle_spec)

    @asynch
    def toggle_message_star_status(self, message: Message) -> None:
        base_request = dict(flag='starred', messages=[message['id']])
        if 'starred' in message['flags']:
            request = dict(base_request, op='remove')
        else:
            request = dict(base_request, op='add')
        response = self.client.update_message_flags(request)

    @asynch
    def mark_message_ids_as_read(self, id_list: List[int]) -> None:
        if not id_list:
            return
        self.client.update_message_flags({
            'messages': id_list,
            'flag': 'read',
            'op': 'add',
        })

    def send_private_message(self, recipients: str,
                             content: str) -> bool:
        request = {
            'type': 'private',
            'to': recipients,
            'content': content,
        }
        response = self.client.send_message(request)
        return response['result'] == 'success'

    def send_stream_message(self, stream: str, topic: str,
                            content: str) -> bool:
        request = {
            'type': 'stream',
            'to': stream,
            'subject': topic,
            'content': content,
        }
        response = self.client.send_message(request)
        return response['result'] == 'success'

    def update_private_message(self, msg_id: int, content: str) -> bool:
        request = {
            "message_id": msg_id,
            "content": content,
        }
        response = self.client.update_message(request)
        return response['result'] == 'success'

    def update_stream_message(self, topic: str, msg_id: int,
                              content: str) -> bool:
        request = {
            "message_id": msg_id,
            "content": content,
            # TODO: Add support for "change_later" & "change_all"
            "propagate_mode": "change_one",
            "subject": topic,
        }
        response = self.client.update_message(request)
        return response['result'] == 'success'

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
            if first_anchor and response['anchor'] != 10000000000000000:
                self.index['pointer'][str(self.narrow)] = response['anchor']
            if 'found_newest' in response:
                self.found_newest = response['found_newest']
            else:
                # Older versions of the server does not contain the
                # 'found_newest' flag. Instead, we use this logic:
                query_range = num_after + num_before + 1
                self.found_newest = len(response['messages']) < query_range
            return ""
        return response['msg']

    def get_topics_in_stream(self, stream_list: Iterable[int]) -> str:
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
                return response['msg']
        return ""

    @staticmethod
    def exception_safe_result(future: 'Future[str]') -> str:
        try:
            return future.result()
        except zulip.ZulipError as e:
            return str(e)

    def fetch_all_topics(self, workers: int) -> None:
        """
        Distribute stream ids across threads in order to fetch
        topics concurrently.
        """
        with ThreadPoolExecutor(max_workers=workers) as executor:
            list_of_streams = list(self.stream_dict.keys())
            thread_objects = {
                i: executor.submit(self.get_topics_in_stream,
                                   list_of_streams[i::workers])
                for i in range(workers)
            }  # type: Dict[int, Future[str]]
            wait(thread_objects.values())

        results = {
            str(name): self.exception_safe_result(thread_object)
            for name, thread_object in thread_objects.items()
        }  # type: Dict[str, str]
        if any(results.values()):
            failures = ['fetch_topics[{}]'.format(name)
                        for name, result in results.items()
                        if result]
            raise ServerConnectionFailure(", ".join(failures))

    def is_muted_stream(self, stream_id: int) -> bool:
        return stream_id in self.muted_streams

    def is_muted_topic(self, stream_id: int, topic: str) -> bool:
        if stream_id in self.muted_streams:
            return True
        stream_name = self.stream_dict[stream_id]['name']
        topic_to_search = [stream_name, topic]  # type: List[str]
        return topic_to_search in self.muted_topics

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
                            if aggregate_status != 'active' and\
                                    aggregate_status != 'idle':
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

    @staticmethod
    def _stream_info_from_subscriptions(
            subscriptions: List[Dict[str, Any]]
    ) -> Tuple[Dict[int, Any], Set[int], List[List[str]], List[List[str]]]:
        stream_keys = ('name', 'stream_id', 'color',
                       'invite_only', 'description')

        # Canonicalize color formats, since zulip server versions may use
        # different formats
        for subscription in subscriptions:
            subscription['color'] = canonicalize_color(subscription['color'])

        # Mapping of stream-id to all available stream info
        # Stream IDs for muted streams
        # Limited stream info sorted by name (used in display)
        return (
            {stream['stream_id']: stream for stream in subscriptions},
            {stream['stream_id'] for stream in subscriptions
             if stream['in_home_view'] is False},
            sorted([[stream[key] for key in stream_keys]
                    for stream in subscriptions if stream['pin_to_top']],
                   key=lambda s: s[0].lower()),
            sorted([[stream[key] for key in stream_keys]
                    for stream in subscriptions if not stream['pin_to_top']],
                   key=lambda s: s[0].lower())
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

    def update_subscription(self, event: Event) -> None:
        """
        Handle changes in subscription (Eg: muting/unmuting streams)
        """
        if hasattr(self.controller, 'view'):
            if ('property' in event and
                    event['property'] == 'in_home_view'):
                stream_id = event['stream_id']

                # FIXME: Does this always contain the stream_id?
                stream_button = self.controller.view.\
                    stream_id_to_button[stream_id]

                if event['value']:  # Unmuting streams
                    self.muted_streams.remove(stream_id)
                    stream_button.mark_unmuted()
                else:  # Muting streams
                    self.muted_streams.add(stream_id)
                    stream_button.mark_muted()

                self.controller.update_screen()

    def toggle_stream_muted_status(self, stream_id: int) -> bool:
        request = [{
            'stream_id': stream_id,
            'property': 'is_muted',
            'value': not self.is_muted_stream(stream_id)
            # True for muting and False for unmuting.
        }]
        response = self.client.update_subscription_settings(request)
        return response['result'] == 'success'

    def handle_typing_event(self, event: Event) -> None:
        if hasattr(self.controller, 'view'):
            # If the user is in pm narrow with the person typing
            if len(self.narrow) == 1 and self.narrow[0][0] == 'pm_with' and\
                    event['sender']['email'] in self.narrow[0][1].split(','):
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

    def notify_user(self, message: Message) -> None:
        # Check if notifications are enabled by the user.
        # It is disabled by default.
        if not self.controller.notify_enabled:
            return
        if message['sender_id'] == self.user_id:
            return

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
        elif {'mentioned', 'wildcard_mentioned'}.intersection(
                set(message['flags'])) and message['type'] == 'stream':
            recipient = ' (to {} -> {})'.format(message['display_recipient'],
                                                message['subject'])

        if recipient:
            notify((self.server_name + ":\n" +
                    message['sender_full_name'] + recipient),
                   message['content'])

    def append_message(self, event: Event) -> None:
        """
        Adds message to the end of the view.
        """
        response = event['message']
        # sometimes `flags` are missing in `event` so initialize
        # an empty list of flags in that case.
        response['flags'] = event.get('flags', [])
        # We need to update the topic order in index, unconditionally.
        if response['type'] == 'stream':
            self.update_topic_index(response['stream_id'], response['subject'])
            # If the topic view is toggled for incoming message's
            # recipient stream, then we re-arrange topic buttons
            # with most recent at the top.
            if (hasattr(self.controller, 'view') and
                self.controller.view.left_panel.is_in_topic_view and
                response['stream_id'] == self.controller.view.
                    topic_w.stream_button.stream_id):
                self.controller.view.topic_w.update_topics_list(
                    response['stream_id'], response['subject'],
                    response['sender_id'])
                self.controller.update_screen()

        # We can notify user regardless of whether UI is rendered or not.
        self.notify_user(response)
        if hasattr(self.controller, 'view') and self.found_newest:
            self.index = index_messages([response], self, self.index)
            if self.msg_list.log:
                last_message = self.msg_list.log[-1].original_widget.message
            else:
                last_message = None
            msg_w_list = create_msg_box_list(self, [response['id']],
                                             last_message=last_message)
            if not msg_w_list:
                return
            else:
                msg_w = msg_w_list[0]

            if not self.narrow:
                self.msg_list.log.append(msg_w)

            elif self.narrow[0][1] == 'mentioned' and \
                    'mentioned' in response['flags']:
                self.msg_list.log.append(msg_w)

            elif self.narrow[0][1] == response['type'] and\
                    len(self.narrow) == 1:
                self.msg_list.log.append(msg_w)

            elif response['type'] == 'stream' and \
                    self.narrow[0][0] == "stream":
                recipient_stream = response['display_recipient']
                narrow_stream = self.narrow[0][1]
                append_to_stream = recipient_stream == narrow_stream

                if append_to_stream and (len(self.narrow) == 1 or
                                         (len(self.narrow) == 2 and
                                          self.narrow[1][1] ==
                                          response['subject'])):
                    self.msg_list.log.append(msg_w)

            elif response['type'] == 'private' and len(self.narrow) == 1 and\
                    self.narrow[0][0] == "pm_with":
                narrow_recipients = self.recipients
                message_recipients = frozenset(
                    [user['id'] for user in response['display_recipient']])
                if narrow_recipients == message_recipients:
                    self.msg_list.log.append(msg_w)
            if 'read' not in response['flags']:
                set_count([response['id']], self.controller, 1)
            self.controller.update_screen()

    def update_topic_index(self, stream_id: int, topic_name: str) -> None:
        """
        Update topic order in index based on incoming message.
        """
        topic_index = self.index['topics'][stream_id]
        for topic_iterator, topic in enumerate(topic_index):
            if topic == topic_name:
                topic_index.insert(0, topic_index.pop(topic_iterator))
                return
        # No previous topics with same topic names are found
        # hence, it must be a new topic.
        topic_index.insert(0, topic_name)

    def update_message(self, response: Event) -> None:
        """
        Updates previously rendered message.
        """
        message_id = response['message_id']
        # If the message is indexed
        if self.index['messages'].get(message_id):
            message = self.index['messages'][message_id]
            self.index['edited_messages'].add(message_id)

            if 'rendered_content' in response:
                message['content'] = response['rendered_content']
                self.index['messages'][message_id] = message
                self.update_rendered_view(message_id)

            # 'subject' is not present in update event if
            # the response didn't have a 'subject' update.
            if 'subject' in response:
                for msg_id in response['message_ids']:
                    self.index['messages'][msg_id]['subject']\
                        = response['subject']
                    self.update_rendered_view(msg_id)

    def update_reaction(self, response: Event) -> None:
        message_id = response['message_id']
        # If the message is indexed
        if self.index['messages'][message_id] != {}:

            message = self.index['messages'][message_id]
            if response['op'] == 'add':
                message['reactions'].append(
                    {
                        'user': response['user'],
                        'reaction_type': response['reaction_type'],
                        'emoji_code': response['emoji_code'],
                        'emoji_name': response['emoji_name'],
                    }
                )
            else:
                emoji_code = response['emoji_code']
                for reaction in message['reactions']:
                    # Since Who reacted is not displayed,
                    # remove the first one encountered
                    if reaction['emoji_code'] == emoji_code:
                        message['reactions'].remove(reaction)

            self.index['messages'][message_id] = message
            self.update_rendered_view(message_id)

    def update_message_flag_status(self, event: Event) -> None:
        if event['all']:  # FIXME Should handle eventually
            return

        flag_to_change = event['flag']
        if flag_to_change not in {'starred', 'read'}:
            return

        if flag_to_change == 'read' and event['operation'] == 'remove':
            return

        indexed_message_ids = set(self.index['messages'])
        message_ids_to_mark = set(event['messages'])

        for message_id in message_ids_to_mark & indexed_message_ids:
            msg = self.index['messages'][message_id]
            if event['operation'] == 'add':
                if flag_to_change not in msg['flags']:
                    msg['flags'].append(flag_to_change)
            elif event['operation'] == 'remove':
                if flag_to_change in msg['flags']:
                    msg['flags'].remove(flag_to_change)
            else:
                raise RuntimeError(event, msg['flags'])

            self.index['messages'][message_id] = msg
            self.update_rendered_view(message_id)

        if event['operation'] == 'add' and flag_to_change == 'read':
            set_count(list(message_ids_to_mark & indexed_message_ids),
                      self.controller, -1)

    def update_rendered_view(self, msg_id: int) -> None:
        # Update new content in the rendered view
        for msg_w in self.msg_list.log:
            msg_box = msg_w.original_widget
            if msg_box.message['id'] == msg_id:
                # Remove the message if it no longer belongs in the current
                # narrow.
                if len(self.narrow) == 2 and\
                        msg_box.message['subject'] != self.narrow[1][1]:
                    self.msg_list.log.remove(msg_w)
                    # Change narrow if there are no messages left in the
                    # current narrow.
                    if not self.msg_list.log:
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
                    msg_pos = self.msg_list.log.index(msg_w)
                    self.msg_list.log[msg_pos] = new_msg_w

                    # If this is not the last message in the view
                    # update the next message's last_message too.
                    if len(self.msg_list.log) != (msg_pos + 1):
                        next_msg_w = self.msg_list.log[msg_pos+1]
                        msg_w_list = create_msg_box_list(
                            self, [next_msg_w.original_widget.message['id']],
                            last_message=new_msg_w.original_widget.message)
                        self.msg_list.log[msg_pos+1] = msg_w_list[0]
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
            'realm_user_groups'
        ]
        event_types = list(self.event_actions)
        try:
            response = self.client.register(event_types=event_types,
                                            fetch_event_types=fetch_types,
                                            client_gravatar=True,
                                            apply_markdown=True)
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
                    if self._register_desired_events():
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
                for event_type, do_action_for in self.event_actions.items():
                    if event_type == event['type']:
                        do_action_for(event)
