from typing import Any, List, Tuple

import urwid
from zulipterminal.helper import async, update_flag
from zulipterminal.ui_tools.buttons import TopicButton, UnreadPMButton
from zulipterminal.ui_tools.utils import create_msg_box_list


class MessageView(urwid.ListBox):
    def __init__(self, model: Any) -> None:
        self.model = model
        self.index = model.index
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
        focus_msg = self.model.index['pointer'][str(self.model.narrow)]
        if focus_msg == set():
            focus_msg = len(msg_btn_list) - 1
        self.focus_msg = focus_msg
        return msg_btn_list

    def get_current_ids(self) -> Any:
        narrow = self.model.narrow
        if narrow == []:
            current_ids = self.index['all_messages'].copy()
        elif narrow[0][0] == 'stream':
            stream_id = self.model.stream_id
            if len(narrow) == 1:
                current_ids = self.index['all_stream'][stream_id].copy()
            elif len(narrow) == 2:
                topic = narrow[1][1]
                current_ids = self.index['stream'][stream_id][topic].copy()
        elif narrow[0][1] == 'private':
            current_ids = self.index['all_private'].copy()
        elif narrow[0][0] == 'pm_with':
            recipients = self.model.recipients
            current_ids = self.index['private'][recipients].copy()
        return current_ids

    @async
    def load_old_messages(self, anchor: int=10000000000) -> None:
        self.old_loading = True
        # Use the currently focused image as anchor
        self.model.anchor = anchor
        # We don't want message after the current message
        self.model.num_after = 0
        self.model.num_before = 30
        current_ids = self.get_current_ids()
        self.index = self.model.get_messages(False)
        msg_ids = self.get_current_ids() - current_ids
        message_list = create_msg_box_list(self.model, msg_ids)
        message_list.reverse()
        for msg_w in message_list:
            self.log.insert(0, msg_w)
        self.model.controller.loop.draw_screen()
        self.old_loading = False

    @async
    def load_new_messages(self, anchor: int, focus_position: int) -> None:
        self.new_loading = True
        self.model.anchor = anchor
        self.model.num_before = 0
        self.model.num_after = 30
        current_ids = self.get_current_ids()
        self.index = self.model.get_messages(False)
        msg_ids = self.get_current_ids() - current_ids
        message_list = create_msg_box_list(self.model, msg_ids)
        self.log.extend(message_list)
        self.model.controller.loop.draw_screen()
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

        elif key == 'up' and not self.old_loading:
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

        elif key == 'page up' and not self.old_loading:
            if self.focus_position == 0:
                return self.keypress(size, 'up')
            else:
                return super(MessageView, self).keypress(size, 'page up')

        elif key == 'page down' and not self.old_loading:
            if self.focus_position == len(self.log) - 1:
                return self.keypress(size, 'down')
            else:
                return super(MessageView, self).keypress(size, 'page down')

        key = super(MessageView, self).keypress(size, key)
        return key

    def read_message(self) -> None:
        # Message currently in focus
        msg_w, curr_pos = self.body.get_focus()
        if msg_w is None:
            return
        # save the current focus
        key = str(self.model.narrow)
        self.model.index['pointer'][key] = self.focus_position
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


class StreamsView(urwid.ListBox):
    def __init__(self, streams_btn_list: List[Any]) -> None:
        self.log = urwid.SimpleFocusListWalker(streams_btn_list)
        super(StreamsView, self).__init__(self.log)

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
    def __init__(self, model: Any, write_box: Any) -> None:
        msg_list = MessageView(model)
        self.model = model
        self.controller = model.controller
        self.last_unread_topic = None
        self.last_unread_pm = None
        model.msg_list = msg_list
        super(MiddleColumnView, self).__init__(msg_list, footer=write_box)

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
        if key == 'esc':
            self.footer.keypress(size, 'esc')
            self.set_focus('body')

        elif self.focus_position == 'footer':
            return super(MiddleColumnView, self).keypress(size, key)

        elif key == 'r':
            self.body.keypress(size, 'enter')
            self.set_focus('footer')
            self.footer.focus_position = 1
            return key

        elif key == 'c':
            self.body.keypress(size, 'c')
            self.set_focus('footer')
            self.footer.focus_position = 0
            return key

        elif key == 'R':
            self.body.keypress(size, 'R')
            self.set_focus('footer')
            self.footer.focus_position = 1
            return key

        elif key == 'n':
            # narrow to next unread topic
            stream_topic = self.get_next_unread_topic()
            if stream_topic is None:
                return key
            stream, topic = stream_topic
            self.controller.narrow_to_topic(TopicButton(stream, topic,
                                                        self.model))
            return key
        elif key == 'p':
            # narrow to next unread pm
            pm = self.get_next_unread_pm()
            if pm is None:
                return key
            email = self.model.user_id_email_dict[pm]
            self.controller.narrow_to_user(UnreadPMButton(pm, email))

        return super(MiddleColumnView, self).keypress(size, key)
