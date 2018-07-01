import platform
import re
from urllib.parse import urlparse
from typing import Any, Tuple

import urwid

from zulipterminal.config import get_key
from zulipterminal.ui_tools.boxes import WriteBox, SearchBox
from zulipterminal.ui_tools.views import (
    RightColumnView,
    MiddleColumnView,
    StreamsView,
    LeftColumnView,
)


class View(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """
    palette = {
        'default': [
            (None,           'light gray',    'black'),
            ('selected',     'light magenta', 'dark blue'),
            ('msg_selected', 'light red',     'black'),
            ('header',       'dark cyan',     'dark blue',  'bold'),
            ('custom',       'white',         'dark blue',  'underline'),
            ('content',      'white',         'black',      'standout'),
            ('name',         'yellow',        'black'),
            ('unread',       'black',         'light gray'),
            ('active',       'white',         'black'),
            ('idle',         'yellow',        'black')
        ],
        'light': [
            (None,           'black',        'white'),
            ('selected',     'white',        'dark blue'),
            ('msg_selected', 'dark blue',    'light gray'),
            ('header',       'white',        'dark blue',  'bold'),
            ('custom',       'white',        'dark blue',  'underline'),
            ('content',      'black',        'light gray', 'standout'),
            ('name',         'dark magenta', 'light gray', 'bold'),
        ],
        'blue': [
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
        self.users = self.model.users
        self.streams = self.model.streams
        self.write_box = WriteBox(self)
        self.search_box = SearchBox(self.controller)
        super(View, self).__init__(self.main_window())

    def left_column_view(self) -> Any:
        self.left_col_w = LeftColumnView(self)
        return self.left_col_w

    def message_view(self) -> Any:
        self.middle_column = MiddleColumnView(self.model, self.write_box,
                                              self.search_box)
        w = urwid.LineBox(self.middle_column)
        return w

    def right_column_view(self) -> Any:
        self.users_view = RightColumnView(self)
        w = urwid.LineBox(self.users_view, title=u"Users")
        return w

    def main_window(self) -> Any:
        left_column = self.left_column_view()
        center_column = self.message_view()
        right_column = self.right_column_view()
        body = [
            (25, left_column),
            ('weight', 10, center_column),
            (25, right_column),
        ]
        self.body = urwid.Columns(body, focus_column=1)

        div_char = '═'
        profile = self.controller.client.get_profile()

        base_url = '{uri.scheme}://{uri.netloc}/'.format(
                uri=urlparse(self.controller.client.base_url))

        title_text = " {full_name} ({email}) - {server} ".format(
                server=base_url, **profile)
        title_bar = urwid.Columns([
            urwid.Divider(div_char=div_char),
            (len(title_text), urwid.Text([title_text])),
            urwid.Divider(div_char=div_char),
        ])

        w = urwid.Frame(self.body, title_bar, footer=urwid.Text(""),
                        focus_part='body')
        return w

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if self.controller.editor_mode:
            return self.controller.editor.keypress((size[1],), key)
        elif key == "w":
            # Start User Search if not in editor_mode
            self.users_view.keypress(size, 'w')
            self.body.focus_col = 2
            self.user_search.set_edit_text("")
            self.controller.editor_mode = True
            self.controller.editor = self.user_search
            return key
        elif key == "q":
            # jump stream search
            self.left_col_w.keypress(size, 'q')
            self.body.focus_col = 0
            self.stream_w.search_box.set_edit_text("")
            self.controller.editor_mode = True
            self.controller.editor = self.stream_w.search_box
            return key
        else:
            return super(View, self).keypress(size, get_key(key))


class Screen(urwid.raw_display.Screen):

    def write(self, data: Any) -> None:
        if "Microsoft" in platform.platform():
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)
