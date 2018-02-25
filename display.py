#!/usr/bin/env python3

import urwid
import zulip


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
        body = urwid.SimpleFocusListWalker(self.main_view())
        super(MessageView, self).__init__(body)

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
    def __init__(self, caption):
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  # ', caption], 0), None, 'selected')


class WriteBox(urwid.Pile):
    def __init__(self, view):
        super(WriteBox, self).__init__(self.main_view(True))
        self.client = view.client
        self.stream = ''
        self.title = ''
        self.msg = ''
        self.to = ''

    def set_stream(self, edit, new_text):
        self.stream = new_text

    def set_title(self, edit, new_text):
        self.title = new_text

    def set_msg(self, edit, new_text):
        self.msg = new_text

    def set_to(self, edit, new_text):
        self.to = new_text

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
        to_write_box = urwid.Edit(u"To: ")
        urwid.connect_signal(to_write_box, 'change', self.set_to)
        msg_write_box = urwid.Edit(u"> ")
        urwid.connect_signal(msg_write_box, 'change', self.set_msg)
        self.contents = [
            (urwid.LineBox(to_write_box), self.options()),
            (msg_write_box, self.options()),
        ]

    def stream_box_view(self, button):
        msg_write_box = urwid.Edit(u"> ")
        urwid.connect_signal(msg_write_box, 'change', self.set_msg)

        stream_write_box = urwid.Edit(caption=u"Stream:  ")
        urwid.connect_signal(stream_write_box, 'change', self.set_stream)

        title_write_box = urwid.Edit(caption=u"Title:  ")
        urwid.connect_signal(title_write_box, 'change', self.set_title)

        header_write_box = urwid.Columns([
            urwid.LineBox(stream_write_box),
            urwid.LineBox(title_write_box),
        ])
        write_box = [
            (header_write_box, self.options()),
            (msg_write_box, self.options()),
        ]
        self.contents = write_box

    def keypress(self, size, key):
        if key == 'enter':
            if self.to == '':
                request = {
                    'type' : 'stream',
                    'to' : self.stream,
                    'subject' : self.title,
                    'content' : self.msg,
                }
                self.client.send_message(request)
            request = {
                'type' : 'private',
                'to' : self.to,
                'content' : self.msg,
            }
            self.client.send_message(request)

        if key == 'esc':
            self.main_view(False)

        return super(WriteBox, self).keypress(size, key)


class ZulipModel(object):
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self, client):
        self.client = client
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
            user_names = [user['full_name'] for user in users_list]
            return user_names
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
        urwid.WidgetWrap.__init__(self, self.main_window())

    def menu_view(self):
        menu_btn_list = [MenuButton(item) for item in self.menu]

        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self):
        streams_btn_list = [MenuButton(item) for item in self.streams]

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
        msg_list = MessageView(self.messages)
        write_box = WriteBox(self)
        w = urwid.Frame(msg_list, footer=write_box)
        w = urwid.LineBox(w)
        return w

    def users_view(self):
        users_btn_list = [MenuButton(item) for item in self.users]

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
            ('weight', 35, right_column),
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
        self.model = ZulipModel(self.client)
        self.view = ZulipView(self)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.loop.run()


def main():
    ZulipController().main()

if '__main__'==__name__:
    main()
