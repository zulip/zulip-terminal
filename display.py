import time
from functools import wraps
from threading import Thread
from typing import List, Any, Tuple, Dict

import urwid
import zulip

def async(func: Any) -> Any:
    """
    Decorator for executing a function in a separate :class:`threading.Thread`.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        return thread.start()
    return wrapper


class MessageBox(urwid.Pile):
    def __init__(self, message: str, model: Any) -> None:
        self.model = model
        self.message = message
        super(MessageBox, self).__init__(self.main_view())

    def stream_view(self) -> Any:
        stream_title = ('header', [
        ('custom', self.message['stream']), 
        ('selected', ">"),
        ('custom', self.message['title'])
        ])
        stream_title = urwid.Text(stream_title)
        time = urwid.Text(('custom', self.message['time']), align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def private_view(self) -> Any:
        title = ('header', [('custom', 'Private Message')])
        title = urwid.Text(title)
        time = urwid.Text(('custom', self.message['time']), align='right')
        header = urwid.Columns([
            title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def main_view(self) -> List[Any]:
        if self.message['type'] == 'stream':
            header = self.stream_view()
        else:
            header = self.private_view()

        content = self.message['sender'] + " : " + self.message['content']
        content = urwid.Text(content.encode('utf-8'))
        return [header, content]


class MessageView(urwid.ListBox):
    def __init__(self, messages: str, model: Any) -> None:
        self.model = model
        self.messages = messages
        self.log = urwid.SimpleFocusListWalker(self.main_view())
        super(MessageView, self).__init__(self.log)
        self.focus_position = 50

    def main_view(self) -> List[Any]:
        msg_btn_list = [urwid.AttrMap(MessageBox(item, self.model), None, 'msg_selected') for item in self.messages]
        return msg_btn_list

    def load_old_messages(self) -> None:
        self.model.num_before += 50
        self.model.messages = self.model.load_old_messages(False)
        new_messages = self.model.messages[:50]
        new_messages.reverse()
        for msg in new_messages:
            self.log.insert(0, urwid.AttrMap(MessageBox(msg, self), None, 'msg_selected'))

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'down':
            try:
                self.focus_position = self.log.next_position(self.focus_position)
                return key
            except Exception:
                return key

        if key == 'up':
            try:
                self.focus_position = self.log.prev_position(self.focus_position)
                return key
            except Exception:
                self.load_old_messages()
                return key
        key = super(MessageView, self).keypress(size, key)
        return key


class MenuButton(urwid.Button):
    def __init__(self, caption: str, email: str='', view: Any=None, user: str=False, stream: bool=False) -> None:
        self.caption = caption
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  # ', caption], 0), None, 'selected')
        if stream:
            urwid.connect_signal(self, 'click', view.write_box.stream_box_view)
        if user:
            urwid.connect_signal(self, 'click', view.write_box.private_box_view)


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super(WriteBox, self).__init__(self.main_view(True))
        self.client = view.client
        self.to_write_box=None
        self.stream_write_box=None

    def main_view(self, new: bool) -> Any:
        private_button = MenuButton(u"New Private Message")
        urwid.connect_signal(private_button, 'click', self.private_box_view)
        stream_button = MenuButton(u"New Topic")
        urwid.connect_signal(stream_button, 'click', self.stream_box_view)
        w = urwid.Columns([
            urwid.LineBox(private_button),
            urwid.LineBox(stream_button),
        ])
        if new:
            return [w]
        else:
            self.contents = [(w, self.options())]

    def private_box_view(self, button: Any) -> None:
        self.to_write_box = urwid.Edit(u"To: ", edit_text=button.email)
        self.msg_write_box = urwid.Edit(u"> ")
        self.contents = [
            (urwid.LineBox(self.to_write_box), self.options()),
            (self.msg_write_box, self.options()),
        ]

    def stream_box_view(self, button: Any) -> None:
        self.msg_write_box = urwid.Edit(u"> ")
        self.stream_write_box = urwid.Edit(caption=u"Stream:  ", edit_text=button.caption)
        self.title_write_box = urwid.Edit(caption=u"Title:  ")

        header_write_box = urwid.Columns([
            urwid.LineBox(self.stream_write_box),
            urwid.LineBox(self.title_write_box),
        ])
        write_box = [
            (header_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'enter':
            if not self.to_write_box:
                request = {
                    'type' : 'stream',
                    'to' : self.stream_write_box.edit_text,
                    'subject' : self.title_write_box.edit_text,
                    'content' : self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)

            else:
                request = {
                    'type' : 'private',
                    'to' : self.to_write_box.edit_text,
                    'content' : self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)

            if response['result'] == 'success':
                self.msg_write_box.edit_text = ''

        if key == 'esc':
            self.main_view(False)

        return super(WriteBox, self).keypress(size, key)


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


class ZulipView(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """
    palette = [
        (None,  'light gray', 'black'),
        ('selected', 'white', 'dark blue'),
        ('msg_selected', 'light gray', 'dark red','bold'),
        ('header','dark cyan', 'dark blue', 'bold'),
        ('custom','light cyan', 'dark blue', 'underline'),
        ('content', 'white', 'black', 'standout'),
        ]

    def __init__(self, controller: Any) -> None:
        self.model = controller.model
        self.client = controller.client
        self.users = self.model.get_all_users()
        self.menu = self.model.menu
        self.messages = self.model.messages
        self.streams = self.model.get_subscribed_streams()
        self.write_box = WriteBox(self)
        urwid.WidgetWrap.__init__(self, self.main_window())

    def menu_view(self) -> None:
        menu_btn_list = [MenuButton(item) for item in self.menu]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self) -> Any:
        streams_btn_list = [MenuButton(item, view=self, stream=True) for item in self.streams]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(streams_btn_list))
        w = urwid.LineBox(w, title="Streams")
        return w

    def left_column_view(self) -> Any:
        left_column_structure = [
            (4, self.menu_view()),
            self.streams_view(),
        ]

        w = urwid.Pile(left_column_structure)
        return w

    def message_view(self) -> Any:
        self.msg_list = MessageView(self.messages, self.model)
        w = urwid.Frame(self.msg_list, footer=self.write_box)
        w = urwid.LineBox(w)
        return w

    def users_view(self) -> Any:
        users_btn_list = [MenuButton(item[0], item[1], view=self, user=True) for item in self.users]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(users_btn_list))
        return w

    def right_column_view(self) -> Any:
        w = urwid.Frame(self.users_view())
        w = urwid.LineBox(w, title=u"Users")
        return w

    def main_window(self) -> Any:
        left_column = self.left_column_view()
        center_column = self.message_view()
        right_column = self.right_column_view()

        body = [
            ('weight', 30, left_column),
            ('weight', 100, center_column),
            ('weight', 30, right_column),
        ]

        w = urwid.Columns(body, focus_column=1)
        w = urwid.LineBox(w, title=u"Zulip")
        return w


class ZulipController:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str) -> None:
        self.client = zulip.Client(config_file=config_file)
        self.model = ZulipModel(self)
        self.view = ZulipView(self)

    @async
    def update(self) -> None:
        self.client.call_on_each_message(self.model.update_messages)

    def main(self) -> None:
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.update()
        self.loop.run()
