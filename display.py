#!/usr/bin/env python3

import urwid


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
        stream_title = urwid.Text(stream_title)
        time = urwid.Text(('custom', self.message['time']), align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        content = urwid.Text(self.message['content'])
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

class ZulipModel(object):
    """
    A class responsible for storing the data to be displayed.
    """

    def __init__(self):
        self.menu = [
            u'All messages',
            u'Private messages',
        ]

        self.users = [
            u'Tim Abbott',
            u'Steve Howell',
            u'Eeshan Garg',
            u'Alena Volkova',
            u'Tarun Kumar',
            u'Rishi Gupta',
            u'David Johnson',
            u'Vishnu Ks',
            u'Aman Agrawal',
        ]

        self.streams = [
            u'general',
            u'integrations',
            u'announce',
            u'design',
            u'frontend',
            u'backend',
            u'commits',
            u'documentation',
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
        ]

    def __init__(self, controller):
        self.model = controller.model
        self.users = self.model.users
        self.menu = self.model.menu
        self.messages = self.model.messages
        self.streams = self.model.streams
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

        msg_write_box = urwid.Edit(u" ")
        stream_write_box = urwid.Edit(caption=u"Stream :  ")
        title_write_box = urwid.Edit(caption=u"Title :  ")
        header_write_box = urwid.Columns([
            urwid.LineBox(stream_write_box),
            urwid.LineBox(title_write_box),
        ])
        write_box = urwid.Pile([
            header_write_box,
            msg_write_box
        ])
        write_box = urwid.LineBox(write_box, title=u"New Message")

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
            ('weight', 29, right_column),
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
        self.model = ZulipModel()
        self.view = ZulipView( self )

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.loop.run()


def main():
    ZulipController().main()

if '__main__'==__name__:
    main()
