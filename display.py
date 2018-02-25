#!/usr/bin/env python3

import time
from functools import wraps
from threading import Thread

import urwid
import zulip

def async(func):
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
    def __init__(self, message):
        self.message = message
        super(MessageBox, self).__init__(self.main_view())

    def main_view(self):
        stream_title = ('header', [
        ('custom', self.message['stream']), 
        ('selected', ">"),
        ('custom', self.message['title'])
        ])
        content = self.message['sender'] + " : " + self.message['content']
        stream_title = urwid.Text(stream_title)
        time = urwid.Text(('custom', self.message['time']), align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        content = urwid.Text(content.encode('utf-8'))
        return [header, content]


class MessageView(urwid.ListBox):
    def __init__(self, messages):
        self.messages = messages
        self.log = urwid.SimpleFocusListWalker(self.main_view())
        super(MessageView, self).__init__(self.log)

    def main_view(self):
        msg_btn_list = [urwid.AttrMap(MessageBox(item), None, 'msg_selected') for item in self.messages]
        return msg_btn_list

    def keypress(self, size, key):
        key = super(MessageView, self).keypress(size, key)

        if key == 'down':
            try:
                self.focus_position += 1
                return key
            except Exception:
                return key

        if key == 'up':
            try:
                self.focus_position -= 1
                return key
            except Exception:
                return key

        return key


class MenuButton(urwid.Button):
    def __init__(self, caption, email='', view=None, user=False, stream=False):
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
    def __init__(self, view):
        super(WriteBox, self).__init__(self.main_view(True))
        self.client = view.client
        self.to_write_box=None
        self.stream_write_box=None

    def main_view(self, new):
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

    def private_box_view(self, button):
        self.to_write_box = urwid.Edit(u"To: ", edit_text=button.email)
        self.msg_write_box = urwid.Edit(u"> ")
        self.contents = [
            (urwid.LineBox(self.to_write_box), self.options()),
            (self.msg_write_box, self.options()),
        ]

    def stream_box_view(self, button):
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

    def keypress(self, size, key):
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

    def __init__(self, controller):
        self.controller = controller
        self.client = controller.client
        self.menu = [
            u'All messages',
            u'Private messages',
        ]

        self.messages = [
            {
                'sender' : 'Aman Agrawal',
                'time' : '8:56 AM',
                'stream' : 'integrations',
                'title' : 'Zulip Terminal',
                'content' : 'Hi Eeshan',
            },
            {
                'sender' : 'Eeshan Garg',
                'time' : '8:57 AM',
                'stream' : 'integrations',
                'title' : 'Zulip Terminal',
                'content' : 'Hi Aman',
            },
        ]

    def get_all_users(self):
        try:
            users = self.client.get_members()
            users_list = [user for user in users['members'] if user['is_active']]
            users_list.sort(key=lambda x: x['full_name'].lower())
            return [(user['full_name'][:20], user['email']) for user in users_list]

        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def get_subscribed_streams(self):
        try :
            streams = self.client.get_streams(include_subscribed=True, include_public=False)
            stream_names = [stream['name'] for stream in streams['streams']]
            return sorted(stream_names, key=str.lower)
        except Exception:
            print("Invalid API key")
            raise urwid.ExitMainLoop()

    def update_messages(self, response):
        msg = {
            'sender' : response['sender_full_name'],
            'time' : time.ctime(int(response['timestamp'])),
            'stream' : response['display_recipient'],
            'title' : response['subject'],
            'content' : response['content'],
        }
        self.controller.view.msg_list.log.append(urwid.AttrMap(MessageBox(msg), None, 'msg_selected'))


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

    def __init__(self, controller):
        self.model = controller.model
        self.client = controller.client
        self.users = self.model.get_all_users()
        self.menu = self.model.menu
        self.messages = self.model.messages
        self.streams = self.model.get_subscribed_streams()
        self.write_box = WriteBox(self)
        urwid.WidgetWrap.__init__(self, self.main_window())

    def menu_view(self):
        menu_btn_list = [MenuButton(item) for item in self.menu]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self):
        streams_btn_list = [MenuButton(item, view=self, stream=True) for item in self.streams]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(streams_btn_list))
        w = urwid.LineBox(w, title="Streams")
        return w

    def left_column_view(self):
        left_column_structure = [
            (4, self.menu_view()),
            self.streams_view(),
        ]

        w = urwid.Pile(left_column_structure)
        return w

    def message_view(self):
        self.msg_list = MessageView(self.messages)
        w = urwid.Frame(self.msg_list, footer=self.write_box)
        w = urwid.LineBox(w)
        return w

    def users_view(self):
        users_btn_list = [MenuButton(item[0], item[1], view=self, user=True) for item in self.users]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(users_btn_list))
        return w

    def right_column_view(self):
        w = urwid.Frame(self.users_view())
        w = urwid.LineBox(w, title=u"Users")
        return w

    def main_window(self):
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

    def __init__(self):
        self.client = zulip.Client(config_file="./zit")
        self.model = ZulipModel(self)
        self.view = ZulipView(self)

    @async
    def update(self):
        self.client.call_on_each_message(self.model.update_messages)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.update()
        self.loop.run()


def main():
    ZulipController().main()

if '__main__'==__name__:
    main()
