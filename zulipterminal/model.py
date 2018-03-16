import time
import urwid
import json
from collections import defaultdict
from typing import Any, List, Tuple, Dict

from zulipterminal.ui_tools import MessageBox
from zulipterminal.helper import classify_message, async


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
        # ID of the message to select when viewing all messages.
        self.focus_all_msg = -1
        # ID of the message to select when in a narrow.
        self.focus_narrow = -1
        self.menu = [
            u'All messages',
            u'Private messages',
        ]

        '''
        Stores all the messages, type: Dict[str, Dict[Dict[str, Any]]]
            Example:
            {
                'hamelet@example.com' : [ # Store other user's id in PM
                                          # (regardless of sender)
                    # List of Messages
                    {
                        'sender' : 'Aman Agrawal',
                        'time' : '8 AM',
                        'stream':[ # Actually recipient
                            {
                                'full_name':'Hamlet of Denmark',
                                'email':'hamlet@example.com',
                                'short_name':'hamlet',
                                'id':31572
                            },
                            {
                                'full_name': 'Aman Agrawal',
                                'email' : 'aman@zulip.com',
                                'short_name' : 'aman',
                                'id' : '123',
                            }
                        ],
                        'title' : '',
                        'content' : 'HI',
                        'type' : 'private',
                        'sender_email' : 'aman@zulip.com',
                    },
                    ...
                ],
                '89' : [ # Stream ID
                    {
                        'sender' : 'aman',
                        'time' : '8 AM',
                        'stream' : 'integrations',
                        'title' : 'zulip-terminal',
                        'content' : 'HI',
                        'type' : 'stream',
                        'sender_email' : 'aman@zulip.com',
                    },
                    ...
                ],
                ...
            }
        '''
        # TODO: make initial fetch async so that no message is lost
        #       when the messages are being fetched.
        self.initial_update = list()
        self.update_new_message()
        self.messages = self.load_old_messages(first_anchor=True)
        self.messages = classify_message(self.client.email,
                                         self.initial_update, self.messages)
        self.initial_data = self.fetch_initial_data()

    @async
    def update_new_message(self) -> None:
        self.client.call_on_each_message(self.update_messages)

    def load_old_messages(self, first_anchor: bool) -> List[Dict[str, str]]:
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

            if first_anchor:
                self.focus_narrow = response['anchor']
                if self.narrow == []:
                    self.focus_all_msg = response['anchor']

                if (len(response['messages']) < 41):
                    self.update = True

            return classify_message(self.client.email, response['messages'])

    def fetch_initial_data(self):
        try:
            result = self.client.register(
                fetch_event_types=[
                    'presence',
                    'subscription',
                    'realm_user',
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
                'full_name' : user['full_name'],
                'email' : user['email'],
                'status' : 'idle',
            }
        # The to display
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
        if hasattr(self.controller, 'view'):
            cmsg = classify_message(self.client.email, [response])
            key = list(cmsg.keys())[0]
            if ((self.narrow == []) or (self.narrow[0][1] == key)) and\
                    self.update:
                self.msg_list.log.append(
                    urwid.AttrMap(
                        MessageBox(
                            cmsg[key][0], self
                            ),
                        cmsg[key][0]['color'],
                        'msg_selected')
                    )
            self.controller.loop.draw_screen()
        else:
            if hasattr(self, 'messages'):
                self.messages = classify_message(self.client.email, [response],
                                                 self.messages)
            else:
                self.initial_update.append(response)
