import platform
import re
from typing import Any, Tuple, List, Dict, Optional
import random

import urwid

from zulipterminal.config.keys import (
    is_command_key,
    commands_for_random_tips
)
from zulipterminal.config.themes import THEMES
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

    LEFT_WIDTH = 25
    RIGHT_WIDTH = 25

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.palette = controller.theme
        self.model = controller.model
        self.users = self.model.users
        self.pinned_streams = self.model.pinned_streams
        self.unpinned_streams = self.model.unpinned_streams
        self.write_box = WriteBox(self)
        self.search_box = SearchBox(self.controller)
        super(View, self).__init__(self.main_window())

    def left_column_view(self) -> Any:
        return LeftColumnView(View.LEFT_WIDTH, self)

    def message_view(self) -> Any:
        self.middle_column = MiddleColumnView(self, self.model, self.write_box,
                                              self.search_box)
        return urwid.LineBox(self.middle_column, bline="")

    def right_column_view(self) -> Any:
        self.users_view = RightColumnView(View.RIGHT_WIDTH, self)
        return urwid.LineBox(
            self.users_view, title=u"Users",
            tlcorner=u'─', tline=u'─', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'', brcorner=u''
        )

    def get_random_help(self) -> List[Any]:
        # Get random allowed hotkey (ie. eligible for being displayed as a tip)
        allowed_commands = commands_for_random_tips()
        if not allowed_commands:
            return ['Help(?): ', ]
        random_command = random.choice(allowed_commands)
        return [
            'Help(?): ',
            ('code', ' ' + ', '.join(random_command['keys']) + ' '),
            ' ' + random_command['help_text'],
        ]

    def set_footer_text(self, text_list: Optional[List[Any]]=None) -> None:
        if text_list is None:
            text = self.get_random_help()
        else:
            text = text_list
        self._w.footer.set_text(text)
        self.controller.update_screen()

    def footer_view(self) -> Any:
        text_header = self.get_random_help()
        return urwid.AttrWrap(urwid.Text(text_header), 'footer')

    def main_window(self) -> Any:
        self.left_panel = self.left_column_view()
        self.center_panel = self.message_view()
        self.right_panel = self.right_column_view()
        if self.controller.autohide:
            body = [
                (View.LEFT_WIDTH, self.left_panel),
                ('weight', 10, self.center_panel),
                (0, self.right_panel),
            ]
        else:
            body = [
                (View.LEFT_WIDTH, self.left_panel),
                ('weight', 10, self.center_panel),
                (View.RIGHT_WIDTH, self.right_panel),
            ]
        self.body = urwid.Columns(body, focus_column=0)

        div_char = '═'

        title_text = " {full_name} ({email}) - {server} ".format(
                     full_name=self.model.user_full_name,
                     email=self.model.user_email,
                     server=self.model.server_url)

        title_bar = urwid.Columns([
            urwid.Divider(div_char=div_char),
            (len(title_text), urwid.Text([title_text])),
            urwid.Divider(div_char=div_char),
        ])

        w = urwid.Frame(self.body, title_bar, focus_part='body',
                        footer=self.footer_view())
        return w

    def show_left_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return
        width = View.LEFT_WIDTH if visible else 0
        self.body.contents[0] = (
            self.left_panel,
            self.body.options(width_type='given', width_amount=width),
        )
        if visible:
            self.body.focus_col = 0

    def show_right_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return
        width = View.RIGHT_WIDTH if visible else 0
        self.body.contents[2] = (
            self.right_panel,
            self.body.options(width_type='given', width_amount=width),
        )
        if visible:
            self.body.focus_col = 2

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        self.model.new_user_input = True
        if self.controller.editor_mode:
            return self.controller.editor.keypress((size[1],), key)
        # Redirect commands to message_view.
        elif is_command_key('SEARCH_MESSAGES', key) or\
                is_command_key('NEXT_UNREAD_TOPIC', key) or\
                is_command_key('NEXT_UNREAD_PM', key) or\
                is_command_key('PRIVATE_MESSAGE', key):
            self.body.focus_col = 1
            self.middle_column.keypress(size, key)
            return key
        elif is_command_key('ALL_PM', key):
            self.model.controller.show_all_pm(self)
            self.body.focus_col = 1
        elif is_command_key('ALL_STARRED', key):
            self.model.controller.show_all_starred(self)
            self.body.focus_col = 1
        elif is_command_key('SEARCH_PEOPLE', key):
            # Start User Search if not in editor_mode
            self.users_view.keypress(size, 'w')
            self.show_left_panel(visible=False)
            self.show_right_panel(visible=True)
            self.user_search.set_edit_text("")
            self.controller.editor_mode = True
            self.controller.editor = self.user_search
            return key
        elif is_command_key('SEARCH_STREAMS', key):
            # jump stream search
            self.left_panel.keypress(size, 'q')
            self.show_right_panel(visible=False)
            self.show_left_panel(visible=True)
            self.stream_w.search_box.set_edit_text("")
            self.controller.editor_mode = True
            self.controller.editor = self.stream_w.search_box
            return key
        elif is_command_key('HELP', key):
            # Show help menu
            self.controller.show_help()
            return key
        # replace alternate keys with arrow/functional keys
        # This is needed for navigating in widgets
        # other than message_view.
        elif is_command_key('PREVIOUS_MESSAGE', key):
            key = 'up'
        elif is_command_key('NEXT_MESSAGE', key):
            key = 'down'
        elif is_command_key('GO_LEFT', key):
            key = 'left'
        elif is_command_key('GO_RIGHT', key):
            key = 'right'
        elif is_command_key('SCROLL_TO_TOP', key):
            key = 'page up'
        elif is_command_key('SCROLL_TO_BOTTOM', key):
            key = 'page down'
        elif is_command_key('END_MESSAGE', key):
            key = 'end'
        return super(View, self).keypress(size, key)


class Screen(urwid.raw_display.Screen):

    def write(self, data: Any) -> None:
        if "Microsoft" in platform.platform():
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)
