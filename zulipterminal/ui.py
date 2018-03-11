import itertools
from typing import List, Any, Tuple, Dict
import urwid

from zulipterminal.ui_tools import (
    WriteBox,
    MenuButton,
    MessageView,
    MiddleColumnView,
    StreamsView,
    UsersView,
)

class ZulipView(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """
    palette = {'default':[
                (None,           'light gray',   'black'),
                ('selected',     'white',        'dark blue'),
                ('msg_selected', 'light red',    'black'),
                ('header',       'dark cyan',    'dark blue',  'bold'),
                ('custom',       'white',        'dark blue',  'underline'),
                ('content',      'white',        'black',      'standout'),
                ('name',         'yellow',       'black'),
                ('unread',       'black',        'light gray'),
                ],
                'light':[
                (None,           'black',        'white'),
                ('selected',     'white',        'dark blue'),
                ('msg_selected', 'dark blue',    'light gray'),
                ('header',       'white',        'dark blue',  'bold'),
                ('custom',       'white',        'dark blue',  'underline'),
                ('content',      'black',        'light gray', 'standout'),
                ('name',         'dark magenta', 'light gray', 'bold'),
                ],
                'blue':[
                (None,           'black',        'light blue'),
                ('selected',     'white',        'dark blue'),
                ('msg_selected', 'black',        'light gray'),
                ('header',       'black',        'dark blue',  'bold'),
                ('custom',       'white',        'dark blue',  'underline'),
                ('content',      'black',        'light gray', 'standout'),
                ('name',         'dark red',     'light gray', 'bold'),
                ]
            }

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.model = controller.model
        self.client = controller.client
        self.users = self.model.get_all_users()
        self.menu = self.model.menu
        self.messages = list(itertools.chain.from_iterable(self.model.messages.values()))
        self.streams = self.model.get_subscribed_streams()
        self.write_box = WriteBox(self)
        urwid.WidgetWrap.__init__(self, self.main_window())

    def menu_view(self) -> None:
        menu_btn_list = [MenuButton(item, controller=self.controller) for item in self.menu]
        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self) -> Any:
        streams_btn_list = [MenuButton(item, controller=self.controller, view=self, stream=True) for item in self.streams]
        w = StreamsView(streams_btn_list)
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
        w = MiddleColumnView(self.messages, self.model, self.write_box)
        w = urwid.LineBox(w)
        return w

    def users_view(self) -> Any:
        users_btn_list = [MenuButton(item[0], item[1], controller=self.controller, view=self, user=True) for item in self.users]
        w = UsersView(urwid.SimpleFocusListWalker(users_btn_list))
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
            ('weight', 3, left_column),
            ('weight', 10, center_column),
            ('weight', 3, right_column),
        ]
        self.body = urwid.Columns(body, focus_column=1)
        w = urwid.LineBox(self.body, title=u"Zulip")
        return w
