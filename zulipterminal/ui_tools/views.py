import urwid
from typing import Any, List, Tuple
import itertools

from zulipterminal.helper import update_flag, async

from zulipterminal.ui_tools.boxes import MessageBox
from zulipterminal.ui_tools.utils import create_msg_box_list


class MessageView(urwid.ListBox):
    def __init__(self, messages: str, model: Any) -> None:
        self.model = model
        self.messages = messages
        self.focus_msg = None  # type: int
        self.log = urwid.SimpleFocusListWalker(self.main_view())
        urwid.connect_signal(self.log, 'modified', self.read_message)
        # This Function completely controls the messages
        # shown in the MessageView
        self.model.msg_view = self.log

        super(MessageView, self).__init__(self.log)

        # Set Focus to the last message
        self.set_focus(self.focus_msg)
        # if loading new/old messages - True
        self.old_loading = False
        self.new_loading = False

    def main_view(self) -> List[Any]:
        msg_btn_list, focus_msg = create_msg_box_list(self.messages,
                                                      self.model)
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
        new_messages = self.model.load_old_messages(False)
        new_messages = itertools.chain.from_iterable(new_messages.values())
        new_messages = sorted(new_messages, key=lambda msg: msg['time'],
                              reverse=True)
        # Skip the first message as we don't want to display
        # the focused message again
        for msg in new_messages[1:]:
            self.log.insert(0, urwid.AttrMap(MessageBox(msg, self.model),
                            msg['color'], 'msg_selected'))
        self.old_loading = False

    @async
    def load_new_messages(self, anchor: int, focus_position: int) -> None:
        self.new_loading = True
        self.model.anchor = anchor
        self.model.num_before = 0
        self.model.num_after = 30
        new_messages = self.model.load_old_messages(False)
        msg_list = list(itertools.chain.from_iterable(new_messages.values()))
        if len(msg_list) < 31:
            self.model.update = True
        new_messages = msg_list
        new_messages = sorted(new_messages, key=lambda msg: msg['time'],
                              reverse=True)
        # Skip the first message as we don't want to display the
        # focused message again
        for msg in new_messages[:-1]:
            self.log.insert(
                self.focus_position + 1,
                urwid.AttrMap(
                    MessageBox(msg, self.model),
                    msg['color'],
                    'msg_selected'
                )
            )
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
        if key == 'down' and not self.new_loading:
            try:
                position = self.log.next_position(self.focus_position)
                self.set_focus(position, 'above')
                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message['id']
                    self.load_new_messages(id, self.focus_position)
                return key

        if key == 'up' and not self.old_loading:
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
        key = super(MessageView, self).keypress(size, key)
        return key

    def read_message(self):
        # Message currently in focus
        msg_w, curr_pos = self.body.get_focus()
        if msg_w is None:
            return
        # msg ids that have been read
        read_msg_ids = list()  # type: List[int]
        # until we find a read message above the current message
        while msg_w.original_widget.message['color'] == 'unread':
            read_msg_ids.append(msg_w.original_widget.message['id'])
            msg_w.set_attr_map({None: None})
            msg_w, curr_pos = self.body.get_prev(curr_pos)
            if msg_w is None:
                break
        update_flag(read_msg_ids, self.model.controller.client)


class StreamsView(urwid.ListBox):
    def __init__(self, streams_btn_list: List[Any]) -> None:
        self.log = urwid.SimpleFocusListWalker(streams_btn_list)
        super(StreamsView, self).__init__(self.log)

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            if button == 5:
                self.keypress(size, 'down')
                return True
        return super(StreamsView, self).mouse_event(size, event, button, col,
                                                    row, focus)


class UsersView(urwid.ListBox):
    def __init__(self, users_btn_list: List[Any]) -> None:
        self.log = urwid.SimpleFocusListWalker(users_btn_list)
        super(UsersView, self).__init__(self.log)

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            if button == 4:
                for _ in range(5):
                    self.keypress(size, 'up')
                return True
            if button == 5:
                for _ in range(5):
                    self.keypress(size, 'down')
        return super(UsersView, self).mouse_event(size, event, button, col,
                                                  row, focus)


class MiddleColumnView(urwid.Frame):
    def __init__(self, messages: Any, model: Any, write_box: Any) -> None:
        msg_list = MessageView(messages, model)
        model.msg_list = msg_list
        super(MiddleColumnView, self).__init__(msg_list, footer=write_box)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'r':
            if not self.focus_position == 'footer':
                self.body.keypress(size, 'enter')
                self.set_focus('footer')
                self.footer.focus_position = 1
                return key
        if key == 'esc':
            self.footer.keypress(size, 'esc')
            self.set_focus('body')
        if key == 'c':
            if not self.focus_position == 'footer':
                self.body.keypress(size, 'c')
                self.set_focus('footer')
                self.footer.focus_position = 0
                return key
        return super(MiddleColumnView, self).keypress(size, key)
