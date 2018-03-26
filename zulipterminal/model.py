import urwid
import json
from typing import Any, List, Tuple, Dict

from zulipterminal.helper import (
    async,
    index_messages,
    classify_unread_counts,
)
from zulipterminal.ui_tools.utils import create_msg_box_list


class ZulipModel(object):
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client
        self.msg_view = None  # List Walker of urwid
        self.anchor = 0
        self.num_before = 30
        self.num_after = 10
        self.msg_list = None  # Updated by MiddleColumnView (ListBox)
        self.narrow = []
        self.update = False
        self.stream_id = -1
        self.initial_update = list()
        self.update_new_message()
        self.initial_data = self.fetch_initial_data()
        self.index = None
        self.get_messages(first_anchor=True)
        self.user_id = self.client.get_profile()['user_id']
        self.users = self.get_all_users()
        self.streams = self.get_subscribed_streams()
        self.unread_counts = classify_unread_counts(
            self.initial_data['unread_msgs']
            )

    @async
    def update_new_message(self) -> None:
        self.client.call_on_each_message(self.update_messages)

    def get_messages(self, first_anchor: bool) -> List[Dict[str, str]]:
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

    def fetch_initial_data(self):
        try:
            result = self.client.register(
                fetch_event_types=[
                    'presence',
                    'subscription',
                    'realm_user',
                    'message',
                    'update_message_flags',
                    ],
            )
            return result
        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def get_all_users(self) -> List[Tuple[Any, Any]]:
        # All the users in the realm
        users = self.initial_data['realm_users']
        user_dict = dict()
        # store the relevant info for a user in Dict[Dict[str, Any]] format.
        for user in users:
            user_dict[user['email']] = {
                'full_name': user['full_name'],
                'email': user['email'],
                'status': 'idle',
                'user_id': user['user_id']
            }
        self.user_dict = user_dict.copy()
        # List to display
        user_list = list()
        # List which stores the active/idle status of users
        presences = self.initial_data['presences']
        # sort the list according to the full name of users.
        presence_list = sorted(
            presences.keys(),
            key=lambda p: user_dict[p]['full_name'].lower()
            )
        for user in presence_list:
            # if the user is active append it to the list
            if presences[user]['aggregated']['status'] == 'active':
                user_dict[user]['status'] = 'active'
                user_list.append(user_dict[user])
                # remove the user from dictionary
                user_dict.pop(user)
        # add the remaining users to the list.
        user_list += sorted(user_dict.values(),
                            key=lambda u: u['full_name'].lower(),
                            )
        return user_list

    def get_subscribed_streams(self) -> List[List[str]]:
        subscriptions = self.initial_data['subscriptions']
        stream_names = [[
            stream['name'],
            stream['stream_id'],
            stream['color'],
            ] for stream in subscriptions
        ]
        return sorted(stream_names, key=lambda s: s[0].lower())

    def update_messages(self, response: Dict[str, str]) -> None:
        response['flags'] = []
        if len(self.initial_update) > 0 and hasattr(self.controller, 'view'):

            for msg in self.initial_update:
                self.index = index_messages([msg], self, self.index)
                msg_w = create_msg_box_list(self, [msg['id']])[0]
                self.msg_list.log.append(msg_w)

            self.initial_update = []
        elif not hasattr(self.controller, 'view'):
            self.initial_update.append(response)

        if hasattr(self.controller, 'view') and self.update:
            self.index = index_messages([response], self, self.index)
            msg_w = create_msg_box_list(self, [response['id']])[0]

            if self.narrow == []:
                self.msg_list.log.append(msg_w)

            elif self.narrow[0][1] == response['type'] and\
                    len(self.narrow) == 1:
                self.msg_list.log.append(msg_w)

            elif response['type'] == 'stream' and len(self.narrow) == 2 and\
                    self.narrow[1][1] == response['subject']:
                self.msg_list.log.append(msg_w)

            self.controller.loop.draw_screen()
