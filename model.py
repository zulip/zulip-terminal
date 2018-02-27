from typing import Any, List, Tuple, Dict
import time
import urwid
import ujson

from ui_tools import MessageBox
from helper import classify_message

class ZulipModel(object):
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client
        self.msg_view = None  # List Walker of urwid
        self.anchor = 0
        self.num_before = 50
        self.num_after = 0
        self.msg_list = None # Updated by MiddleColumnView
        self.menu = [
            u'All messages',
            u'Private messages',
        ]

        ''' 
        Stores all the messages, type: Dict[str, Dict[Dict[str, Any]]]
            Example:
            {
                'aman@zulip.com' : [
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
                            }
                        ],
                        'title' : '',
                        'content' : 'HI',
                        'type' : 'private',
                        'sender_email' : 'aman@zulip.com',
                    },
                    ...
                ],
                'integrations' : [
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
        self.messages = self.load_old_messages(first_anchor=True)

    def load_old_messages(self, first_anchor: bool) -> List[Dict[str, str]]:
        if first_anchor:
            narrow =  '[]'
        else:
            narrow = self.controller.view.narrow
        request = {
            'anchor' : self.anchor,
            'num_before': self.num_before,
            'num_after': self.num_after,
            'apply_markdown': False,
            'use_first_unread_anchor': True,
            'client_gravatar': False,
            'narrow': narrow,
        }
        response = self.client.do_api_query(request, '/json/messages', method="GET")
        if response['result'] == 'success':
            if first_anchor:
                self.anchor = response['anchor']
            return classify_message(self.client.email, response['messages'])

    def get_all_users(self) -> List[Tuple[Any, Any]]:
        try:
            users = self.client.get_members()
            users_list = [user for user in users['members'] if user['is_active']]
            users_list.sort(key=lambda x: x['full_name'].lower())
            return [(user['full_name'][:20], user['email']) for user in users_list]
        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def get_subscribed_streams(self) -> List[str]:
        try :
            streams = self.client.get_streams(include_subscribed=True, include_public=False)
            stream_names = [stream['name'] for stream in streams['streams']]
            return sorted(stream_names, key=str.lower)
        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def update_messages(self, response: Dict[str, str]) -> None:
        cmsg = classify_message(self.client.email, [response])
        view = self.controller.view
        key = list(cmsg.keys())[0]
        self.messages[key] += cmsg[key]
        if view.narrow == ujson.dumps([]) or ujson.loads(view.narrow)[0][1] == key:
            self.msg_list.log.append(urwid.AttrMap(MessageBox(cmsg[key][0], self), None, 'msg_selected'))
