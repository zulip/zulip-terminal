from typing import Any, List, Tuple, Dict
import time
import urwid

from ui_tools import MessageBox

class ZulipModel(object):
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.client = controller.client
        self.anchor = 10000000000000000
        self.num_before = 50
        self.num_after = 0
        self.menu = [
            u'All messages',
            u'Private messages',
        ]
        self.messages = self.load_old_messages(first_anchor=True)

    def load_old_messages(self, first_anchor: bool) -> List[Dict[str, str]]:
        request = {
            'anchor' : self.anchor,
            'num_before': self.num_before,
            'num_after': self.num_after,
            'apply_markdown': False,
            'use_first_unread_anchor': first_anchor,
            'client_gravatar': False,
        }
        response = self.client.do_api_query(request, '/json/messages', method="GET")
        messages = []
        if response['result'] == 'success':
            for msg in response['messages']:
                messages.append({
                    'sender' : msg['sender_full_name'],
                    'time' : time.ctime(int(msg['timestamp'])),
                    'stream' : msg['display_recipient'],
                    'title' : msg['subject'],
                    'content' : msg['content'],
                    'type' : msg['type'],
                })
        return messages

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
        msg = {
            'sender' : response['sender_full_name'],
            'time' : time.ctime(int(response['timestamp'])),
            'stream' : response['display_recipient'],
            'title' : response['subject'],
            'content' : response['content'],
            'type' : response['type'],
        }
        self.controller.view.msg_list.log.append(urwid.AttrMap(MessageBox(msg, self), None, 'msg_selected'))
