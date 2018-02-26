from typing import List, Any, Tuple, Dict
import urwid

from ui_tools import (
    WriteBox,
    MenuButton,
    MessageView,
)

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
