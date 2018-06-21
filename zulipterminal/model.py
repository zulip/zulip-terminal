import json
import time
from typing import Any, Dict, List, FrozenSet, Set, Union

import urwid

from zulipterminal.helper import (
    async,
    classify_unread_counts,
    index_messages,
    set_count
)
from zulipterminal.ui_tools.utils import create_msg_box_list


class Model:
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client
        # Get message after registering to the queue.
        self.msg_view = None  # type: Any
        self.anchor = 0
        self.num_before = 30
        self.num_after = 10
        self.msg_list = None  # type: Any
        self.narrow = []  # type: List[Any]
        self.update = False
        self.stream_id = -1
        self.stream_dict = {}  # type: Dict[int, Any]
        self.recipients = frozenset()  # type: FrozenSet[Any]
        self.index = None  # type: Any
        self.get_messages(first_anchor=True)
        self.initial_data = self.fetch_initial_data()
        self.user_id = self.client.get_profile()['user_id']
        self.users = self.get_all_users()
        self.muted_streams = list()  # type: List[int]
        self.streams = self.get_subscribed_streams()
        self.muted_topics = self.initial_data['muted_topics']
        self.unread_counts = classify_unread_counts(self)

    def get_focus_in_current_narrow(self) -> Union[int, Set[None]]:
        """
        Returns the focus in the current narrow.
        For no existing focus this returns {}, otherwise the message ID.
        """
        return self.index['pointer'][str(self.narrow)]

    def get_messages(self, first_anchor: bool) -> Any:
        request = {
            'anchor': self.anchor,
            'num_before': self.num_before,
            'num_after': self.num_after,
            'apply_markdown': False,
            'use_first_unread_anchor': first_anchor,
            'client_gravatar': False,
            'narrow': json.dumps(self.narrow),
        }
        response = self.client.do_api_query(request, '/json/messages',
                                            method="GET")
        if response['result'] == 'success':
            self.index = index_messages(response['messages'], self, self.index)
            if first_anchor:
                self.index[str(self.narrow)] = response['anchor']
            query_range = self.num_after + self.num_before + 1
            if len(response['messages']) < (query_range):
                self.update = True
            return self.index

    def fetch_initial_data(self) -> Dict[str, Any]:
        try:
            result = self.client.register(
                fetch_event_types=[
                    'presence',
                    'subscription',
                    'message',
                    'update_message_flags',
                    'muted_topics',
                ],
                client_gravatar=True,
            )
            result['realm_users'] = self.client.get_members(
                request={
                    'client_gravatar': True,
                }
            )['members']
            return result
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

        # Generate filtered lists for active & idle users
        active = [properties for properties in self.user_dict.values()
                  if properties['status'] == 'active']
        idle = [properties for properties in self.user_dict.values()
                if properties['status'] == 'idle']

        # Construct user_list from sorted components of each list
        user_list = sorted(active, key=lambda u: u['full_name'])
        user_list += sorted(idle, key=lambda u: u['full_name'])

        return user_list

    def get_subscribed_streams(self) -> List[List[str]]:
        subscriptions = self.initial_data['subscriptions']
        # Store streams in id->Stream format
        for stream in subscriptions:
            self.stream_dict[stream['stream_id']] = stream
            # Add if stream is muted.
            if stream['in_home_view'] is False:
                self.muted_streams.append(stream['stream_id'])

        stream_names = [[
            stream['name'],
            stream['stream_id'],
            stream['color'],
        ] for stream in subscriptions
        ]
        return sorted(stream_names, key=lambda s: s[0].lower())

    def append_message(self, response: Dict[str, Any]) -> None:
        """
        Adds message to the end of the view.
        """
        response['flags'] = []
        if hasattr(self.controller, 'view') and self.update:
            self.index = index_messages([response], self, self.index)
            msg_w_list = create_msg_box_list(self, [response['id']])
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
            self.controller.loop.draw_screen()

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

    def update_rendered_view(self, msg_id: int) -> None:
        # Update new content in the rendered view
        for msg_w in self.msg_list.log:
            if msg_w.original_widget.message['id'] == msg_id:
                msg_w_list = create_msg_box_list(self, [msg_id])
                if not msg_w_list:
                    return
                else:
                    new_msg_w = msg_w_list[0]
                msg_pos = self.msg_list.log.index(msg_w)
                self.msg_list.log[msg_pos] = new_msg_w
                self.controller.loop.draw_screen()

    @async
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
                if event['type'] == 'update_message':
                    # FIXME: Support Topic Editing
                    if 'subject' in event.keys():
                        continue
                    else:
                        self.update_message(event)
                if event['type'] == 'reaction':
                    self.update_reaction(event)
