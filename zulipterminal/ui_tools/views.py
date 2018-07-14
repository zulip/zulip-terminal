from collections import defaultdict
from typing import Any, List, Tuple
import threading

import urwid

from zulipterminal.config import KEY_BINDINGS, is_command_key
from zulipterminal.helper import async, update_flag, match_user
from zulipterminal.ui_tools.buttons import (
    TopicButton,
    UnreadPMButton,
    UserButton,
    HomeButton,
    PMButton,
    StreamButton,
)
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.ui_tools.boxes import UserSearchBox, StreamSearchBox


class MessageView(urwid.ListBox):
    def __init__(self, model: Any) -> None:
        self.model = model
        self.index = model.index
        # Initialize for reference
        self.focus_msg = 0
        self.log = urwid.SimpleFocusListWalker(self.main_view())
        urwid.connect_signal(self.log, 'modified', self.read_message)
        # This Function completely controls the messages
        # shown in the MessageView
        self.model.msg_view = self.log

        super(MessageView, self).__init__(self.log)
        self.set_focus(self.focus_msg)
        # if loading new/old messages - True
        self.old_loading = False
        self.new_loading = False

    def main_view(self) -> List[Any]:
        msg_btn_list = create_msg_box_list(self.model)
        focus_msg = self.model.get_focus_in_current_narrow()
        if focus_msg == set():
            focus_msg = len(msg_btn_list) - 1
        self.focus_msg = focus_msg
        return msg_btn_list

    @async
    def load_old_messages(self, anchor: int=10000000000) -> None:
        self.old_loading = True
        # Use the currently focused image as anchor
        self.model.anchor = anchor
        # We don't want message after the current message
        self.model.num_after = 0
        self.model.num_before = 30
        current_ids = self.model.get_message_ids_in_current_narrow()
        self.index = self.model.get_messages(False)
        msg_ids = self.model.get_message_ids_in_current_narrow() - current_ids
        message_list = create_msg_box_list(self.model, msg_ids)
        message_list.reverse()
        for msg_w in message_list:
            self.log.insert(0, msg_w)
        self.model.controller.update_screen()
        self.old_loading = False

    @async
    def load_new_messages(self, anchor: int) -> None:
        self.new_loading = True
        self.model.anchor = anchor
        self.model.num_before = 0
        self.model.num_after = 30
        current_ids = self.model.get_message_ids_in_current_narrow()
        self.index = self.model.get_messages(False)
        msg_ids = self.model.get_message_ids_in_current_narrow() - current_ids
        message_list = create_msg_box_list(self.model, msg_ids)
        self.log.extend(message_list)
        self.model.controller.update_screen()
        self.new_loading = False

    def mouse_event(self, size: Any, event: str, button: int, col: int,
                    row: int, focus: Any) -> Any:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            if button == 5:
                self.keypress(size, 'down')
                return True
        return super(MessageView, self).mouse_event(size, event, button, col,
                                                    row, focus)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('NEXT_MESSAGE', key) and not self.new_loading:
            try:
                position = self.log.next_position(self.focus_position)
                self.set_focus(position, 'above')
                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message['id']
                    self.load_new_messages(id)
                return key

        elif is_command_key('PREVIOUS_MESSAGE', key) and not self.old_loading:
            try:
                position = self.log.prev_position(self.focus_position)
                self.set_focus(position, 'below')
                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message['id']
                    self.load_old_messages(id)
                else:
                    self.load_old_messages()
                return key

        elif is_command_key('SCROLL_TO_TOP', key) and not self.old_loading:
            if self.focus_position == 0:
                return self.keypress(size, 'up')
            else:
                return super(MessageView, self).keypress(size, 'page up')

        elif is_command_key('SCROLL_TO_BOTTOM', key) and not self.old_loading:
            if self.focus_position == len(self.log) - 1:
                return self.keypress(size, 'down')
            else:
                return super(MessageView, self).keypress(size, 'page down')

        key = super(MessageView, self).keypress(size, key)
        return key

    def update_current_footer(self, message_view: Any) -> None:
        if not hasattr(self.model.controller, 'view'):
            return
        # if view is ready display current narrow
        # at the bottom of the view.
        message_view.last_message = defaultdict(dict)
        is_stream = message_view.message['type'] == 'stream'
        if is_stream:
            footer = message_view.stream_view()
        else:
            footer = message_view.private_view()
        self.model.controller.view.search_box.msg_narrow.set_text(
            footer.markup
        )
        self.model.controller.update_screen()

    def read_message(self) -> None:
        # Message currently in focus
        msg_w, curr_pos = self.body.get_focus()
        if msg_w is None:
            return
        self.update_current_footer(msg_w.original_widget)
        # save the current focus
        self.model.set_focus_in_current_narrow(self.focus_position)
        # msg ids that have been read
        read_msg_ids = list()  # type: List[int]
        # until we find a read message above the current message
        while msg_w.attr_map == {None: 'unread'}:
            msg_id = msg_w.original_widget.message['id']
            read_msg_ids.append(msg_id)
            self.model.index['messages'][msg_id]['flags'].append('read')
            msg_w.set_attr_map({None: None})
            msg_w, curr_pos = self.body.get_prev(curr_pos)
            if msg_w is None:
                break
        update_flag(read_msg_ids, self.model.controller)


class StreamsView(urwid.Frame):
    def __init__(self, streams_btn_list: List[Any], view: Any) -> None:
        self.view = view
        self.log = urwid.SimpleFocusListWalker(streams_btn_list)
        self.streams_btn_list = streams_btn_list
        list_box = urwid.ListBox(self.log)
        self.search_box = StreamSearchBox(self)
        urwid.connect_signal(self.search_box, 'change', self.update_streams)
        super(StreamsView, self).__init__(list_box, header=urwid.LineBox(
            self.search_box, tlcorner=u'─', tline=u'─', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
        ))
        self.search_lock = threading.Lock()

    @async
    def update_streams(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.editor_mode:
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong stream list.
        self.search_lock.acquire()
        streams_display = self.streams_btn_list.copy()
        for stream in self.streams_btn_list:
            if not stream.caption.lower().startswith(new_text):
                streams_display.remove(stream)
        self.log.clear()
        self.log.extend(streams_display)
        self.view.controller.update_screen()
        self.search_lock.release()

    def mouse_event(self, size: Any, event: str, button: int, col: int,
                    row: int, focus: Any) -> Any:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            elif button == 5:
                self.keypress(size, 'down')
                return True
        return super(StreamsView, self).mouse_event(size, event, button, col,
                                                    row, focus)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('SEARCH_STREAMS', key):
            self.set_focus('header')
            return key
        elif is_command_key('GO_BACK', key):
            self.search_box.set_edit_text("Search streams")
            self.log.clear()
            self.log.extend(self.streams_btn_list)
            self.set_focus('body')
            self.view.controller.update_screen()
            return key
        return super(StreamsView, self).keypress(size, key)


class UsersView(urwid.ListBox):
    def __init__(self, users_btn_list: List[Any]) -> None:
        self.log = urwid.SimpleFocusListWalker(users_btn_list)
        super(UsersView, self).__init__(self.log)

    def mouse_event(self, size: Any, event: str, button: int, col: int,
                    row: int, focus: Any) -> Any:
        if event == 'mouse press':
            if button == 4:
                for _ in range(5):
                    self.keypress(size, 'up')
                return True
            elif button == 5:
                for _ in range(5):
                    self.keypress(size, 'down')
        return super(UsersView, self).mouse_event(size, event, button, col,
                                                  row, focus)


class MiddleColumnView(urwid.Frame):
    def __init__(self, model: Any, write_box: Any, search_box: Any) -> None:
        msg_list = MessageView(model)
        self.model = model
        self.controller = model.controller
        self.last_unread_topic = None
        self.last_unread_pm = None
        self.search_box = search_box
        model.msg_list = msg_list
        super(MiddleColumnView, self).__init__(msg_list, header=search_box,
                                               footer=write_box)

    def get_next_unread_topic(self) -> Any:
        topics = list(self.model.unread_counts['unread_topics'].keys())
        next_topic = False
        for topic in topics:
            if next_topic is True:
                self.last_unread_topic = topic
                return topic
            if topic == self.last_unread_topic:
                next_topic = True
        if len(topics) > 0:
            topic = topics[0]
            self.last_unread_topic = topic
            return topic
        return

    def get_next_unread_pm(self) -> Any:
        pms = list(self.model.unread_counts['unread_pms'].keys())
        next_pm = False
        for pm in pms:
            if next_pm is True:
                self.last_unread_pm = pm
                return pm
            if pm == self.last_unread_pm:
                next_pm = True
        if len(pms) > 0:
            pm = pms[0]
            self.last_unread_pm = pm
            return pm
        return

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('GO_BACK', key):
            self.header.keypress(size, 'esc')
            self.footer.keypress(size, 'esc')
            self.set_focus('body')

        elif self.focus_position in ['footer', 'header']:
            return super(MiddleColumnView, self).keypress(size, key)

        elif is_command_key('SEARCH_MESSAGES', key):
            self.controller.editor_mode = True
            self.controller.editor = self.search_box
            self.set_focus('header')
            return key

        elif is_command_key('REPLY_MESSAGE', key):
            self.body.keypress(size, 'enter')
            self.set_focus('footer')
            self.footer.focus_position = 1
            return key

        elif is_command_key('STREAM_MESSAGE', key):
            self.body.keypress(size, 'c')
            self.set_focus('footer')
            self.footer.focus_position = 0
            return key

        elif is_command_key('REPLY_AUTHOR', key):
            self.body.keypress(size, 'R')
            self.set_focus('footer')
            self.footer.focus_position = 1
            return key

        elif is_command_key('NEXT_UNREAD_TOPIC', key):
            # narrow to next unread topic
            stream_topic = self.get_next_unread_topic()
            if stream_topic is None:
                return key
            stream, topic = stream_topic
            self.controller.narrow_to_topic(TopicButton(stream, topic,
                                                        self.model))
            return key
        elif is_command_key('NEXT_UNREAD_PM', key):
            # narrow to next unread pm
            pm = self.get_next_unread_pm()
            if pm is None:
                return key
            email = self.model.user_id_email_dict[pm]
            self.controller.narrow_to_user(UnreadPMButton(pm, email))
        elif is_command_key('PRIVATE_MESSAGE', key):
            # Create new PM message
            self.footer.private_box_view()
            self.set_focus('footer')
            self.footer.focus_position = 0
            return key
        return super(MiddleColumnView, self).keypress(size, key)


class RightColumnView(urwid.Frame):
    """
    Displays the users list on the right side of the app.
    """

    def __init__(self, view: Any) -> None:
        self.view = view
        self.user_search = UserSearchBox(self)
        urwid.connect_signal(self.user_search, 'change',
                             self.update_user_list)
        self.view.user_search = self.user_search
        search_box = urwid.LineBox(
            self.user_search, tlcorner=u'─', tline=u'─', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
            )
        self.search_lock = threading.Lock()
        super(RightColumnView, self).__init__(self.users_view(),
                                              header=search_box)

    @async
    def update_user_list(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.editor_mode:
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong user list.
        self.search_lock.acquire()
        users_display = self.users_btn_list.copy()
        for user in self.users_btn_list:
            if not match_user(user, new_text):
                users_display.remove(user)
        self.body = UsersView(
            urwid.SimpleFocusListWalker(users_display))
        self.set_body(self.body)
        self.view.controller.update_screen()
        self.search_lock.release()

    def users_view(self) -> Any:
        self.users_btn_list = list()  # type: List[Any]
        for user in self.view.users:
            unread_count = self.view.model.unread_counts.get(user['user_id'],
                                                             0)
            self.users_btn_list.append(
                UserButton(
                    user,
                    controller=self.view.controller,
                    view=self.view,
                    color=user['status'],
                    count=unread_count
                )
            )
        self.user_w = UsersView(
            urwid.SimpleFocusListWalker(self.users_btn_list))
        self.view.user_w = self.user_w
        return self.user_w

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('SEARCH_PEOPLE', key):
            self.set_focus('header')
            return key
        elif is_command_key('GO_BACK', key):
            self.user_search.set_edit_text("Search People")
            self.body = UsersView(
                urwid.SimpleFocusListWalker(self.users_btn_list))
            self.set_body(self.body)
            self.set_focus('body')
            self.view.controller.update_screen()
            return key
        return super(RightColumnView, self).keypress(size, key)


class LeftColumnView(urwid.Pile):
    """
    Displays the buttons at the left column of the app.
    """

    def __init__(self, view: Any) -> None:
        self.model = view.model
        self.view = view
        self.controller = view.controller
        left_column_structure = [
            (4, self.menu_view()),
            self.streams_view(),
        ]
        super(LeftColumnView, self).__init__(left_column_structure)

    def menu_view(self) -> Any:
        count = self.model.unread_counts.get('all_msg', 0)
        self.view.home_button = HomeButton(self.controller, count=count)
        count = self.model.unread_counts.get('all_pms', 0)
        self.view.pm_button = PMButton(self.controller, count=count)
        menu_btn_list = [
            self.view.home_button,
            self.view.pm_button,
        ]
        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self) -> Any:
        streams_btn_list = list()
        for stream in self.view.streams:
            unread_count = self.model.unread_counts.get(stream[1], 0)
            streams_btn_list.append(
                StreamButton(
                    stream,
                    controller=self.controller,
                    view=self.view,
                    count=unread_count,
                )
            )
        self.view.stream_w = StreamsView(streams_btn_list, self.view)
        w = urwid.LineBox(
            self.view.stream_w, title="Streams",
            tlcorner=u'─', tline=u'─', lline=u'',
            trcorner=u'─', blcorner=u'', rline=u'',
            bline=u'', brcorner=u'─'
            )
        return w

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('SEARCH_STREAMS', key):
            self.focus_position = 1
            self.view.stream_w.keypress(size, key)
            return key
        return super(LeftColumnView, self).keypress(size, key)


class HelpView(urwid.ListBox):
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.log = urwid.SimpleFocusListWalker([
            urwid.Text("Press q to quit.", align='center')
        ])
        for _, binding in KEY_BINDINGS.items():
            commands = ", ".join(binding['keys'])
            self.log.append(
                urwid.Columns([
                    urwid.LineBox(
                        urwid.Text(binding['help_text']),
                        tlcorner=' ', tline=' ', lline=' ', trcorner=' ',
                        blcorner=' ', rline=' ', bline='-', brcorner=' '
                    ),
                    urwid.LineBox(
                        urwid.Text(commands),
                        tlcorner=' ', tline=' ', lline=' ', trcorner=' ',
                        blcorner=' ', rline=' ', bline='-', brcorner=' '
                    )
                ])
            )
        super(HelpView, self).__init__(self.log)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('QUIT_HELP', key):
            self.controller.exit_help()
        return super(HelpView, self).keypress(size, key)
