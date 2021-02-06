import random
import re
import time
from typing import Any, List, Optional, Tuple

import urwid

from zulipterminal.config.keys import commands_for_random_tips, is_command_key
from zulipterminal.config.symbols import (
    APPLICATION_TITLE_BAR_LINE,
    LIST_TITLE_BAR_LINE,
)
from zulipterminal.helper import WSL, asynch
from zulipterminal.ui_tools.boxes import SearchBox, WriteBox
from zulipterminal.ui_tools.views import (
    LeftColumnView,
    MiddleColumnView,
    RightColumnView,
)


class View(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """

    LEFT_WIDTH = 27
    RIGHT_WIDTH = 23

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.palette = controller.theme
        self.model = controller.model
        self.users = self.model.users
        self.pinned_streams = self.model.pinned_streams
        self.unpinned_streams = self.model.unpinned_streams
        self.write_box = WriteBox(self)
        self.search_box = SearchBox(self.controller)

        self.message_view: Any = None

        super().__init__(self.main_window())

    def left_column_view(self) -> Any:
        return LeftColumnView(View.LEFT_WIDTH, self)

    def middle_column_view(self) -> Any:
        self.middle_column = MiddleColumnView(self, self.model, self.write_box,
                                              self.search_box)
        return urwid.LineBox(self.middle_column, title='Messages',
                             tline=LIST_TITLE_BAR_LINE,
                             bline='', trcorner='│', tlcorner='│')

    def right_column_view(self) -> Any:
        self.users_view = RightColumnView(View.RIGHT_WIDTH, self)
        return urwid.LineBox(
            self.users_view, title="Users",
            tlcorner=LIST_TITLE_BAR_LINE,
            tline=LIST_TITLE_BAR_LINE,
            trcorner=LIST_TITLE_BAR_LINE,
            lline='', blcorner='─', rline='',
            bline='', brcorner=''
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

    @asynch
    def set_footer_text(self, text_list: Optional[List[Any]]=None,
                        duration: Optional[float]=None) -> None:
        if text_list is None:
            text = self.get_random_help()
        else:
            text = text_list
        self._w.footer.set_text(text)
        self.controller.update_screen()
        if duration is not None:
            assert duration > 0
            time.sleep(duration)
            self.set_footer_text()

    @asynch
    def set_typeahead_footer(self, suggestions: List[str],
                             state: Optional[int],
                             is_truncated: bool) -> None:
        if suggestions:
            # Wrap by space.
            footer_text: List[Any] = [' ' + s + ' ' for s in suggestions]
            if state is not None:
                footer_text[state] = ('code', footer_text[state])
            if is_truncated:
                footer_text += [' [more] ']
            footer_text.insert(0, [' '])  # Add leading space.
        else:
            footer_text = [' [No matches found]']

        self.set_footer_text(footer_text)

    def footer_view(self) -> Any:
        text_header = self.get_random_help()
        return urwid.AttrWrap(urwid.Text(text_header), 'footer')

    def main_window(self) -> Any:
        self.left_panel = self.left_column_view()
        self.center_panel = self.middle_column_view()
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

        # NOTE: message_view is None, but middle_column_view is called above
        # and sets it.
        assert self.message_view is not None
        # NOTE: set_focus_changed_callback is actually called before the
        # focus is set, so the message is not read yet, it will be read when
        # the focus is changed again either vertically or horizontally.
        self.body._contents.set_focus_changed_callback(
            self.message_view.read_message)

        title_text = " {full_name} ({email}) - {server_name} ({url}) ".format(
                     full_name=self.model.user_full_name,
                     email=self.model.user_email,
                     server_name=self.model.server_name,
                     url=self.model.server_url)

        title_bar = urwid.Columns([
            urwid.Divider(div_char=APPLICATION_TITLE_BAR_LINE),
            (len(title_text), urwid.Text([title_text])),
            urwid.Divider(div_char=APPLICATION_TITLE_BAR_LINE),
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
            self.body.focus_position = 0

    def show_right_panel(self, *, visible: bool) -> None:
        if not self.controller.autohide:
            return
        width = View.RIGHT_WIDTH if visible else 0
        self.body.contents[2] = (
            self.right_panel,
            self.body.options(width_type='given', width_amount=width),
        )
        if visible:
            self.body.focus_position = 2

    # FIXME: The type of size should be urwid_Size; this needs checking
    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        self.model.new_user_input = True
        if self.controller.is_in_editor_mode():
            return self.controller.current_editor().keypress((size[1],), key)
        # Redirect commands to message_view.
        elif (is_command_key('SEARCH_MESSAGES', key)
                or is_command_key('NEXT_UNREAD_TOPIC', key)
                or is_command_key('NEXT_UNREAD_PM', key)
                or is_command_key('PRIVATE_MESSAGE', key)):
            self.body.focus_col = 1
            self.middle_column.keypress(size, key)
            return key
        elif is_command_key('ALL_PM', key):
            self.model.controller.show_all_pm(self)
            self.body.focus_col = 1
        elif is_command_key('ALL_STARRED', key):
            self.model.controller.show_all_starred(self)
            self.body.focus_col = 1
        elif is_command_key('ALL_MENTIONS', key):
            self.model.controller.show_all_mentions(self)
            self.body.focus_col = 1
        elif is_command_key('SEARCH_PEOPLE', key):
            # Start User Search if not in editor_mode
            self.body.focus_position = 2
            self.users_view.keypress(size, 'w')
            self.show_left_panel(visible=False)
            self.show_right_panel(visible=True)
            self.user_search.set_edit_text("")
            self.controller.enter_editor_mode_with(self.user_search)
            return key
        elif (is_command_key('SEARCH_STREAMS', key)
              or is_command_key('SEARCH_TOPICS', key)):
            # jump stream search
            self.body.focus_position = 0
            self.left_panel.keypress(size, 'q')
            self.show_right_panel(visible=False)
            self.show_left_panel(visible=True)
            if self.left_panel.is_in_topic_view:
                search_box = self.topic_w.topic_search_box
            else:
                search_box = self.stream_w.stream_search_box
            search_box.set_edit_text("")
            self.controller.enter_editor_mode_with(search_box)
            return key
        elif is_command_key('OPEN_DRAFT', key):
            saved_draft = self.model.session_draft_message()
            if saved_draft:
                if saved_draft['type'] == 'stream':
                    self.write_box.stream_box_view(
                        caption=saved_draft['display_recipient'],
                        title=saved_draft['subject'],
                        stream_id=saved_draft['stream_id'],
                    )
                elif saved_draft['type'] == 'private':
                    email_list = saved_draft['display_recipient']
                    recipient_user_ids = [
                        self.model.user_dict[email.strip()]['user_id']
                        for email in email_list
                    ]
                    self.write_box.private_box_view(
                        emails=email_list,
                        recipient_user_ids=recipient_user_ids,
                    )
                content = saved_draft['content']
                self.write_box.msg_write_box.edit_text = content
                self.write_box.msg_write_box.edit_pos = len(content)
                self.middle_column.set_focus('footer')
            else:
                self.set_footer_text('No draft message was saved in'
                                     ' this session.', 3)
            return key
        elif is_command_key('ABOUT', key):
            self.controller.show_about()
            return key
        elif is_command_key('HELP', key):
            # Show help menu
            self.controller.show_help()
            return key
        # replace alternate keys with arrow/functional keys
        # This is needed for navigating in widgets
        # other than message_view.
        elif is_command_key('GO_UP', key):
            key = 'up'
        elif is_command_key('GO_DOWN', key):
            key = 'down'
        elif is_command_key('GO_LEFT', key):
            key = 'left'
        elif is_command_key('GO_RIGHT', key):
            key = 'right'
        elif is_command_key('SCROLL_UP', key):
            key = 'page up'
        elif is_command_key('SCROLL_DOWN', key):
            key = 'page down'
        elif is_command_key('GO_TO_BOTTOM', key):
            key = 'end'
        return super().keypress(size, key)


class Screen(urwid.raw_display.Screen):

    def write(self, data: Any) -> None:
        if WSL:
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)
