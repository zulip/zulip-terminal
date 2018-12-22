import json
from threading import Thread
import time
from typing import Any, Dict, List, FrozenSet, Set, Union, Optional, Tuple
from mypy_extensions import TypedDict

import urwid

from zulipterminal.helper import (
    asynch,
    classify_unread_counts,
    index_messages,
    set_count,
    initial_index,
)
from zulipterminal.ui_tools.utils import create_msg_box_list

GetMessagesArgs = TypedDict('GetMessagesArgs', {
     'num_before': int,
     'num_after': int,
     'anchor': Optional[int]
    })


class Model:
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client
        # Get message after registering to the queue.
        self.msg_view = None  # type: Any
        self.msg_list = None  # type: Any
        self.narrow = []  # type: List[Any]
        self.update = False
        self.stream_id = -1
        self.recipients = frozenset()  # type: FrozenSet[Any]
        self.index = initial_index
        self.user_id = -1  # type: int
        self.initial_data = {}  # type: Dict[str, Any]
        self._update_user_id()
        self._update_initial_data()
        self.users = self.get_all_users()

        subscriptions = self.initial_data['subscriptions']
        stream_data = Model._stream_info_from_subscriptions(subscriptions)
        (self.stream_dict, self.muted_streams,
         self.pinned_streams, self.unpinned_streams) = stream_data

        self.muted_topics = self.initial_data['muted_topics']
        self.unread_counts = classify_unread_counts(self)
        self.new_user_input = True
        self.update_presence()

    @asynch
    def _update_user_id(self) -> None:
        self.user_id = self.client.get_profile()['user_id']

    def _update_realm_users(self) -> None:
        self.initial_data['realm_users'] = self.client.get_members(
            request={
                'client_gravatar': True,
            }
        )['members']

    def get_focus_in_current_narrow(self) -> Union[int, Set[None]]:
        """
        Returns the focus in the current narrow.
        For no existing focus this returns {}, otherwise the message ID.
        """
        return self.index['pointer'][str(self.narrow)]

    def set_focus_in_current_narrow(self, focus_message: int) -> None:
        self.index['pointer'][str(self.narrow)] = focus_message

    def set_narrow(self, *,
                   stream: Optional[str]=None,
                   topic: Optional[str]=None,
                   search: Optional[str]=None,
                   pms: bool=False,
                   pm_with: Optional[str]=None,
                   starred: bool=False) -> bool:
        selected_params = {k for k, v in locals().items() if k != 'self' and v}
        valid_narrows = {
            frozenset(): [],
            frozenset(['search']): [['search', search]],
            frozenset(['stream']): [['stream', stream]],
            frozenset(['stream', 'topic']): [['stream', stream],
                                             ['topic', topic]],
            frozenset(['pms']): [['is', 'private']],
            frozenset(['pm_with']): [['pm_with', pm_with]],
            frozenset(['starred']): [['is', 'starred']],
        }  # type: Dict[FrozenSet[str], List[Any]]
        for narrow_param, narrow in valid_narrows.items():
            if narrow_param == selected_params:
                new_narrow = narrow
                break
        else:
            raise RuntimeError("Model.set_narrow parameters used incorrectly.")

        if new_narrow != self.narrow:
            self.narrow = new_narrow
            return False
        else:
            return True

    def get_message_ids_in_current_narrow(self) -> Set[int]:
        narrow = self.narrow
        if narrow == []:
            current_ids = self.index['all_messages']
        elif narrow[0][0] == 'stream':
            stream_id = self.stream_id
            if len(narrow) == 1:
                current_ids = self.index['all_stream'][stream_id]
            elif len(narrow) == 2:
                topic = narrow[1][1]
                current_ids = self.index['stream'][stream_id].get(topic, set())
        elif narrow[0][1] == 'private':
            current_ids = self.index['all_private']
        elif narrow[0][0] == 'pm_with':
            recipients = self.recipients
            current_ids = self.index['private'].get(recipients, set())
        elif narrow[0][0] == 'search':
            current_ids = self.index['search']
        elif narrow[0][1] == 'starred':
            current_ids = self.index['all_starred']
        return current_ids.copy()

    @asynch
    def update_presence(self) -> None:
        # TODO: update response in user list.
        response = self.client.call_endpoint(
            url='users/me/presence',
            request={
                'status': 'active',
                'new_user_input': self.new_user_input,
            }
        )
        self.new_user_input = False
        time.sleep(60)
        self.update_presence()

    @asynch
    def react_to_message(self,
                         message: Dict[str, Any],
                         reaction_to_toggle: str) -> None:
        # FIXME Only support thumbs_up for now
        assert reaction_to_toggle == 'thumbs_up'

        endpoint = 'messages/{}/reactions'.format(message['id'])
        reaction_to_toggle_spec = dict(
            emoji_name='thumbs_up',
            reaction_type='unicode_emoji',
            emoji_code='1f44d')
        existing_reactions = [reaction['emoji_code']
                              for reaction in message['reactions']
                              if ('user_id' in reaction['user'] and
                                  reaction['user']['user_id'] == self.user_id)]
        if reaction_to_toggle_spec['emoji_code'] in existing_reactions:
            method = 'DELETE'
        else:
            method = 'POST'
        response = self.client.call_endpoint(url=endpoint,
                                             method=method,
                                             request=reaction_to_toggle_spec)

    @asynch
    def toggle_message_star_status(self, message: Dict[str, Any]) -> None:
        base_request = dict(flag='starred', messages=[message['id']])
        if 'starred' in message['flags']:
            request = dict(base_request, op='remove')
        else:
            request = dict(base_request, op='add')
        response = self.client.call_endpoint(url='messages/flags',
                                             method='POST',
                                             request=request)

    def get_messages(self, *,
                     num_after: int, num_before: int,
                     anchor: Optional[int]) -> None:
        # anchor value may be specific message (int) or next unread (None)
        first_anchor = anchor is None
        anchor_value = anchor if anchor is not None else 0

        request = {
            'anchor': anchor_value,
            'num_before': num_before,
            'num_after': num_after,
            'apply_markdown': True,
            'use_first_unread_anchor': first_anchor,
            'client_gravatar': False,
            'narrow': json.dumps(self.narrow),
        }
        response = self.client.do_api_query(request, '/json/messages',
                                            method="GET")
        if response['result'] == 'success':
            self.index = index_messages(response['messages'], self, self.index)
            if first_anchor and response['anchor'] != 10000000000000000:
                self.index['pointer'][str(self.narrow)] = response['anchor']
            query_range = num_after + num_before + 1
            if len(response['messages']) < (query_range):
                self.update = True

    def _update_initial_data(self) -> None:
        try:
            # Thread Processes to reduces start time.
            # NOTE: first_anchor is True, so anchor value is ignored
            get_messages = Thread(target=self.get_messages,
                                  kwargs={'num_after': 10,
                                          'num_before': 30,
                                          'anchor': None})
            get_messages.start()
            update_realm_users = Thread(target=self._update_realm_users)
            update_realm_users.start()
            result = self.client.register(
                fetch_event_types=[
                    'presence',
                    'subscription',
                    'message',
                    'update_message_flags',
                    'muted_topics',
                    'realm_user',  # Enables cross_realm_bots
                ],
                client_gravatar=True,
            )
            self.initial_data.update(result)
            # Join process to ensure they are completed
            update_realm_users.join()
            get_messages.join()

        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def get_all_users(self) -> List[Dict[str, Any]]:
        # Dict which stores the active/idle status of users (by email)
        presences = self.initial_data['presences']

        # Construct a dict of each user in the realm to look up by email
        # and a user-id to email mapping
        self.user_dict = dict()  # type: Dict[str, Dict[str, Any]]
        self.user_id_email_dict = dict()  # type: Dict[int, str]
        for user in self.initial_data['realm_users']:
            email = user['email']
            if email in presences:  # presences currently subset of all users
                status = presences[email]['aggregated']['status']
            else:
                # TODO: Consider if bots & other no-presence results should
                # also really be treated as 'idle' and adjust accordingly
                status = 'idle'
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
                'status': 'idle',
            }
            self.user_id_email_dict[bot['user_id']] = email

        # Generate filtered lists for active & idle users
        active = [properties for properties in self.user_dict.values()
                  if properties['status'] == 'active']
        idle = [properties for properties in self.user_dict.values()
                if properties['status'] == 'idle']

        # Construct user_list from sorted components of each list
        user_list = sorted(active, key=lambda u: u['full_name'])
        user_list += sorted(idle, key=lambda u: u['full_name'])

        return user_list

    @staticmethod
    def _stream_info_from_subscriptions(
            subscriptions: List[Dict[str, Any]]
    ) -> Tuple[Dict[int, Any], Set[int], List[List[str]], List[List[str]]]:
        stream_keys = ('name', 'stream_id', 'color', 'invite_only')
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

    def append_message(self, response: Dict[str, Any]) -> None:
        """
        Adds message to the end of the view.
        """
        response['flags'] = []
        if hasattr(self.controller, 'view') and self.update:
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

            elif self.narrow[0][1] == response['type'] and\
                    len(self.narrow) == 1:
                self.msg_list.log.append(msg_w)

            elif response['type'] == 'stream' and len(self.narrow) == 2 and\
                    self.narrow[1][1] == response['subject']:
                self.msg_list.log.append(msg_w)

            elif response['type'] == 'private' and len(self.narrow) == 1 and\
                    self.narrow[0][0] == "pm_with":
                recipients = self.recipients
                msg_recipients = frozenset([
                    self.user_id,
                    self.user_dict[self.narrow[0][1]]['user_id']
                ])
                if recipients == msg_recipients:
                    self.msg_list.log.append(msg_w)

            set_count([response['id']], self.controller, 1)
            self.controller.update_screen()

    def update_message(self, response: Dict[str, Any]) -> None:
        """
        Updates previously rendered message.
        """
        message_id = response['message_id']
        content = response['content']
        # If the message is indexed
        if self.index['messages'][message_id] != {}:
            message = self.index['messages'][message_id]
            message['content'] = content
            self.index['messages'][message_id] = message
            self.update_rendered_view(message_id)

    def update_reaction(self, response: Dict[str, Any]) -> None:
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

    def update_star_status(self, event: Dict[str, Any]) -> None:
        assert len(event['messages']) == 1  # FIXME: Can be multiple?
        message_id = event['messages'][0]

        if self.index['messages'][message_id] != {}:
            msg = self.index['messages'][message_id]
            if event['operation'] == 'add':
                if 'starred' not in msg['flags']:
                    msg['flags'].append('starred')
            elif event['operation'] == 'remove':
                if 'starred' in msg['flags']:
                    msg['flags'].remove('starred')
            else:
                raise RuntimeError(event, msg['flags'])

            self.index['messages'][message_id] = msg
            self.update_rendered_view(message_id)

    def update_rendered_view(self, msg_id: int) -> None:
        # Update new content in the rendered view
        for msg_w in self.msg_list.log:
            msg_box = msg_w.original_widget
            if msg_box.message['id'] == msg_id:
                msg_w_list = create_msg_box_list(
                                self, [msg_id],
                                last_message=msg_box.last_message)
                if not msg_w_list:
                    return
                else:
                    new_msg_w = msg_w_list[0]
                msg_pos = self.msg_list.log.index(msg_w)
                self.msg_list.log[msg_pos] = new_msg_w
                self.controller.update_screen()

    @asynch
    def poll_for_events(self) -> None:
        queue_id = self.controller.queue_id
        last_event_id = self.controller.last_event_id
        while True:
            if queue_id is None:
                self.controller.register_initial_desired_events()
                queue_id = self.controller.queue_id
                last_event_id = self.controller.last_event_id

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
                if event['type'] == 'message':
                    self.append_message(event['message'])
                elif event['type'] == 'update_message':
                    # FIXME: Support Topic Editing
                    if 'subject' in event.keys():
                        continue
                    else:
                        self.update_message(event)
                elif event['type'] == 'reaction':
                    self.update_reaction(event)
                elif event['type'] == 'typing':
                    if hasattr(self.controller, 'view'):
                        self.controller.view.handle_typing_event(event)
                elif event['type'] == 'update_message_flags':
                    # TODO: Should also support 'read' flag changes?
                    if event['flag'] == 'starred':
                        self.update_star_status(event)
