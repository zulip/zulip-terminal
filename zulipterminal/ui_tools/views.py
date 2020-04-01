import threading
import time
from collections import OrderedDict, defaultdict
from typing import Any, Callable, List, Optional, Tuple

import urwid

from zulipterminal.config.keys import (
    HELP_CATEGORIES, KEY_BINDINGS, is_command_key,
)
from zulipterminal.helper import Message, asynch, match_user
from zulipterminal.ui_tools.boxes import PanelSearchBox
from zulipterminal.ui_tools.buttons import (
    HomeButton, MentionedButton, PMButton, StarredButton, StreamButton,
    TopicButton, UnreadPMButton, UserButton,
)
from zulipterminal.ui_tools.utils import create_msg_box_list
from zulipterminal.urwid_types import urwid_Size


class ModListWalker(urwid.SimpleFocusListWalker):

    def set_focus(self, position: int) -> None:
        # When setting focus via set_focus method.
        self.focus = position
        self._modified()
        if hasattr(self, 'read_message'):
            self.read_message()

    def _set_focus(self, index: int) -> None:
        # This method is called when directly setting focus via
        # self.focus = focus_position
        if not self:
            self._focus = 0
            return
        if index < 0 or index >= len(self):
            raise IndexError('focus index is out of range: %s' % (index,))
        if index != int(index):
            raise IndexError('invalid focus index: %s' % (index,))
        index = int(index)
        if index != self._focus:
            self._focus_changed(index)
        self._focus = index
        if hasattr(self, 'read_message'):
            self.read_message()

    def extend(self, items: List[Any],
               focus_position: Optional[int]=None) -> int:
        if focus_position is None:
            focus = self._adjust_focus_on_contents_modified(
                slice(len(self), len(self)), items)
        else:
            focus = focus_position
        rval = super(urwid.MonitoredFocusList, self).extend(items)
        self._set_focus(focus)
        return rval


class MessageView(urwid.ListBox):
    def __init__(self, model: Any) -> None:
        self.model = model
        # Initialize for reference
        self.focus_msg = 0
        self.log = ModListWalker(self.main_view())
        self.log.read_message = self.read_message
        # This Function completely controls the messages
        # shown in the MessageView
        self.model.msg_view = self.log

        super().__init__(self.log)
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

    @asynch
    def load_old_messages(self, anchor: int=10000000000) -> None:
        self.old_loading = True

        ids_to_keep = self.model.get_message_ids_in_current_narrow()
        if self.log:
            top_message_id = self.log[0].original_widget.message['id']
            ids_to_keep.remove(top_message_id)  # update this id
            no_update_baseline = {top_message_id}
        else:
            no_update_baseline = set()

        self.model.get_messages(num_before=30, num_after=0, anchor=anchor)
        ids_to_process = (self.model.get_message_ids_in_current_narrow() -
                          ids_to_keep)

        # Only update if more messages are provided
        if ids_to_process != no_update_baseline:
            if self.log:
                self.log.remove(self.log[0])  # avoid duplication when updating

            message_list = create_msg_box_list(self.model, ids_to_process)
            message_list.reverse()
            for msg_w in message_list:
                self.log.insert(0, msg_w)

            self.set_focus(self.focus_msg)  # Return focus to original message

            self.model.controller.update_screen()

        self.old_loading = False

    @asynch
    def load_new_messages(self, anchor: int) -> None:
        self.new_loading = True
        current_ids = self.model.get_message_ids_in_current_narrow()
        self.model.get_messages(num_before=0, num_after=30, anchor=anchor)
        new_ids = self.model.get_message_ids_in_current_narrow() - current_ids
        if self.log:
            last_message = self.log[-1].original_widget.message
        else:
            last_message = None

        message_list = create_msg_box_list(self.model, new_ids,
                                           last_message=last_message)
        self.log.extend(message_list)

        self.model.controller.update_screen()
        self.new_loading = False

    def mouse_event(self, size: urwid_Size, event: str, button: int, col: int,
                    row: int, focus: bool) -> bool:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            if button == 5:
                self.keypress(size, 'down')
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('GO_DOWN', key) and not self.new_loading:
            try:
                position = self.log.next_position(self.focus_position)
                self.set_focus(position, 'above')
                self.set_focus_valign('middle')

                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message['id']
                    self.load_new_messages(id)
                return key

        elif is_command_key('GO_UP', key) and not self.old_loading:
            try:
                position = self.log.prev_position(self.focus_position)
                self.set_focus(position, 'below')
                self.set_focus_valign('middle')
                return key
            except Exception:
                if self.focus:
                    id = self.focus.original_widget.message['id']
                    self.load_old_messages(id)
                else:
                    self.load_old_messages()
                return key

        elif is_command_key('SCROLL_UP', key) and not self.old_loading:
            if self.focus is not None and \
               self.focus_position == 0:
                return self.keypress(size, 'up')
            else:
                return super().keypress(size, 'page up')

        elif is_command_key('SCROLL_DOWN', key) and not self.old_loading:
            if self.focus is not None and \
               self.focus_position == len(self.log) - 1:
                return self.keypress(size, 'down')
            else:
                return super().keypress(size, 'page down')

        elif is_command_key('THUMBS_UP', key):
            if self.focus is not None:
                self.model.react_to_message(
                    self.focus.original_widget.message,
                    reaction_to_toggle='thumbs_up')

        elif is_command_key('TOGGLE_STAR_STATUS', key):
            if self.focus is not None:
                message = self.focus.original_widget.message
                self.model.toggle_message_star_status(message)

        key = super().keypress(size, key)
        return key

    def update_search_box_narrow(self, message_view: Any) -> None:
        if not hasattr(self.model.controller, 'view'):
            return
        # if view is ready display current narrow
        # at the bottom of the view.
        recipient_bar = message_view.top_header_bar(message_view)
        top_header = message_view.top_search_bar()
        self.model.controller.view.search_box.conversation_focus.set_text(
            top_header.markup
            )
        self.model.controller.view.search_box.msg_narrow.set_text(
            recipient_bar.markup
            )
        self.model.controller.update_screen()

    def read_message(self, index: int=-1) -> None:
        # Message currently in focus
        if hasattr(self.model.controller, "view"):
            view = self.model.controller.view
        else:
            return
        msg_w, curr_pos = self.body.get_focus()
        if msg_w is None:
            return
        self.update_search_box_narrow(msg_w.original_widget)
        # If this the last message in the view and focus is set on this message
        # then read the message.
        last_message_focused = (curr_pos == len(self.log) - 1)
        # Only allow reading a message when middle column is
        # in focus.
        if not(view.body.focus_col == 1 or last_message_focused):
            return
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
        self.model.mark_message_ids_as_read(read_msg_ids)


class StreamsView(urwid.Frame):
    def __init__(self, streams_btn_list: List[Any], view: Any) -> None:
        self.view = view
        self.log = urwid.SimpleFocusListWalker(streams_btn_list)
        self.streams_btn_list = streams_btn_list
        self.focus_index_before_search = 0
        list_box = urwid.ListBox(self.log)
        self.stream_search_box = PanelSearchBox(self,
                                                'SEARCH_STREAMS',
                                                self.update_streams)
        super().__init__(list_box, header=urwid.LineBox(
            self.stream_search_box, tlcorner=u'─', tline=u'', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
        ))
        self.search_lock = threading.Lock()

    @asynch
    def update_streams(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.editor_mode:
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong stream list.
        with self.search_lock:
            new_text = new_text.lower()
            streams_display = [
                stream
                for stream in self.streams_btn_list.copy()
                if new_text in stream.stream_name.lower()
            ]
            self.log.clear()
            self.log.extend(streams_display)
            self.view.controller.update_screen()

    def mouse_event(self, size: urwid_Size, event: str, button: int, col: int,
                    row: int, focus: bool) -> bool:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            elif button == 5:
                self.keypress(size, 'down')
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('SEARCH_STREAMS', key):
            self.set_focus('header')
            return key
        elif is_command_key('GO_BACK', key):
            self.stream_search_box.reset_search_text()
            self.log.clear()
            self.log.extend(self.streams_btn_list)
            self.set_focus('body')
            self.log.set_focus(self.focus_index_before_search)
            self.view.controller.update_screen()
            return key
        return_value = super().keypress(size, key)
        _, self.focus_index_before_search = self.log.get_focus()
        return return_value


class TopicsView(urwid.Frame):
    def __init__(self, topics_btn_list: List[Any], view: Any,
                 stream_button: Any) -> None:
        self.view = view
        self.log = urwid.SimpleFocusListWalker(topics_btn_list)
        self.topics_btn_list = topics_btn_list
        self.stream_button = stream_button
        self.list_box = urwid.ListBox(self.log)
        self.topic_search_box = PanelSearchBox(self,
                                               'SEARCH_TOPICS',
                                               self.update_topics)
        self.header_list = urwid.Pile([self.stream_button,
                                       urwid.Divider('─'),
                                       self.topic_search_box])
        super().__init__(self.list_box, header=urwid.LineBox(
            self.header_list, tlcorner=u'─', tline=u'', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
        ))
        self.search_lock = threading.Lock()

    @asynch
    def update_topics(self, search_box: Any, new_text: str) -> None:
        if not self.view.controller.editor_mode:
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong topics list.
        with self.search_lock:
            new_text = new_text.lower()
            topics_to_display = [
                topic
                for topic in self.topics_btn_list.copy()
                if new_text in topic.topic_name.lower()
            ]
            self.log.clear()
            self.log.extend(topics_to_display)
            self.view.controller.update_screen()

    def update_topics_list(self, stream_id: int, topic_name: str,
                           sender_id: int) -> None:
        # More recent topics are found towards the beginning
        # of the list.
        for topic_iterator, topic_button in enumerate(self.log):
            if topic_button.topic_name == topic_name:
                self.log.insert(0, self.log.pop(topic_iterator))
                self.list_box.set_focus_valign('bottom')
                if sender_id == self.view.model.user_id:
                    self.list_box.set_focus(0)
                return
        # No previous topics with same topic names are found
        # hence we create a new topic button for it.
        new_topic_button = TopicButton(stream_id,
                                       topic_name,
                                       self.view.controller,
                                       self.view.LEFT_WIDTH,
                                       0)
        self.log.insert(0, new_topic_button)
        self.list_box.set_focus_valign('bottom')
        if sender_id == self.view.model.user_id:
            self.list_box.set_focus(0)

    def mouse_event(self, size: urwid_Size, event: str, button: int, col: int,
                    row: int, focus: bool) -> bool:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            elif button == 5:
                self.keypress(size, 'down')
                return True
        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('TOGGLE_TOPIC', key):
            # Exit topic view
            self.view.left_panel.contents[1] = (
                self.view.left_panel.stream_v,
                self.view.left_panel.options(height_type="weight")
                )
            self.view.left_panel.is_in_topic_view = False
        elif is_command_key('GO_RIGHT', key):
            self.view.show_left_panel(visible=False)
            self.view.body.focus_col = 1
        if is_command_key('SEARCH_TOPICS', key):
            self.header_list.set_focus(2)
            return key
        elif is_command_key('GO_BACK', key):
            self.topic_search_box.reset_search_text()
            self.log.clear()
            self.log.extend(self.topics_btn_list)
            self.set_focus('body')
            self.view.controller.update_screen()
            return key
        return super().keypress(size, key)


class UsersView(urwid.ListBox):
    def __init__(self, users_btn_list: List[Any]) -> None:
        self.log = urwid.SimpleFocusListWalker(users_btn_list)
        super().__init__(self.log)

    def mouse_event(self, size: urwid_Size, event: str, button: int, col: int,
                    row: int, focus: bool) -> bool:
        if event == 'mouse press':
            if button == 4:
                for _ in range(5):
                    self.keypress(size, 'up')
                return True
            elif button == 5:
                for _ in range(5):
                    self.keypress(size, 'down')
        return super().mouse_event(size, event, button, col, row, focus)


class MiddleColumnView(urwid.Frame):
    def __init__(self, view: Any, model: Any,
                 write_box: Any, search_box: Any) -> None:
        msg_list = MessageView(model)
        self.model = model
        self.controller = model.controller
        self.view = view
        self.last_unread_topic = None
        self.last_unread_pm = None
        self.search_box = search_box
        model.msg_list = msg_list
        super().__init__(msg_list, header=search_box, footer=write_box)

    def get_next_unread_topic(self) -> Optional[Tuple[int, str]]:
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
        return None

    def get_next_unread_pm(self) -> Optional[int]:
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
        return None

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('GO_BACK', key):
            self.header.keypress(size, 'esc')
            self.footer.keypress(size, 'esc')
            self.set_focus('body')

        elif self.focus_position in ['footer', 'header']:
            return super().keypress(size, key)

        elif is_command_key('SEARCH_MESSAGES', key):
            self.controller.editor_mode = True
            self.controller.editor = self.search_box
            self.set_focus('header')
            return key

        elif is_command_key('REPLY_MESSAGE', key):
            self.body.keypress(size, 'enter')
            if self.footer.focus is not None:
                self.set_focus('footer')
                self.footer.focus_position = 1
            return key

        elif is_command_key('STREAM_MESSAGE', key):
            self.body.keypress(size, 'c')
            # For new streams with no previous conversation.
            if self.footer.focus is None:
                stream_id = self.model.stream_id
                stream_dict = self.model.stream_dict
                self.footer.stream_box_view(
                    caption=stream_dict[stream_id]['name'])
            self.set_focus('footer')
            self.footer.focus_position = 0
            return key

        elif is_command_key('REPLY_AUTHOR', key):
            self.body.keypress(size, 'R')
            if self.footer.focus is not None:
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
                                                        self.controller))
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
        elif is_command_key('GO_LEFT', key):
            self.view.show_left_panel(visible=True)
        elif is_command_key('GO_RIGHT', key):
            self.view.show_right_panel(visible=True)
        return super().keypress(size, key)


class RightColumnView(urwid.Frame):
    """
    Displays the users list on the right side of the app.
    """

    def __init__(self, width: int, view: Any) -> None:
        self.width = width
        self.view = view
        self.user_search = PanelSearchBox(self,
                                          'SEARCH_PEOPLE',
                                          self.update_user_list)
        self.view.user_search = self.user_search
        search_box = urwid.LineBox(
            self.user_search, tlcorner=u'─', tline=u'', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
            )
        self.allow_update_user_list = True
        self.search_lock = threading.Lock()
        super().__init__(self.users_view(), header=search_box)

    @asynch
    def update_user_list(self, search_box: Any=None,
                         new_text: str="",
                         user_list: Any=None) -> None:

        assert ((user_list is None and search_box is not None) or
                (user_list is not None and search_box is None and
                 new_text == ""))

        if not self.view.controller.editor_mode and not user_list:
            return
        if not self.allow_update_user_list and new_text == "":
            return
        # wait for any previously started search to finish to avoid
        # displaying wrong user list.
        with self.search_lock:
            if user_list:
                self.view.users = user_list
            users = self.view.users.copy()
            if new_text:
                users_display = [
                    user for user in users if match_user(user, new_text)
                ]
            else:
                users_display = users
            self.body = self.users_view(users_display)
            self.set_body(self.body)
            self.view.controller.update_screen()

    def users_view(self, users: Any=None) -> Any:
        reset_default_view_users = False
        if users is None:
            users = self.view.users.copy()
            reset_default_view_users = True
        users_btn_list = list()  # type: List[Any]
        for user in users:
            # Only include `inactive` users in search result.
            if user['status'] == 'inactive' and\
                    not self.view.controller.editor_mode:
                continue
            unread_count = (self.view.model.unread_counts['unread_pms'].
                            get(user['user_id'], 0))
            users_btn_list.append(
                UserButton(
                    user,
                    controller=self.view.controller,
                    view=self.view,
                    width=self.width,
                    color='user_' + user['status'],
                    count=unread_count
                )
            )
        user_w = UsersView(users_btn_list)
        # Donot reset them while searching.
        if reset_default_view_users:
            self.users_btn_list = users_btn_list
            self.view.user_w = user_w
        return user_w

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('SEARCH_PEOPLE', key):
            self.allow_update_user_list = False
            self.set_focus('header')
            return key
        elif is_command_key('GO_BACK', key):
            self.user_search.reset_search_text()
            self.allow_update_user_list = True
            self.body = UsersView(self.users_btn_list)
            self.set_body(self.body)
            self.set_focus('body')
            self.view.controller.update_screen()
            return key
        elif is_command_key('GO_LEFT', key):
            self.view.show_right_panel(visible=False)
        return super().keypress(size, key)


class LeftColumnView(urwid.Pile):
    """
    Displays the buttons at the left column of the app.
    """

    def __init__(self, width: int, view: Any) -> None:
        self.model = view.model
        self.view = view
        self.controller = view.controller
        self.width = width
        self.menu_v = self.menu_view()
        self.stream_v = self.streams_view()

        self.is_in_topic_view = False
        self.left_column_structure = [
            (4, self.menu_v),
            self.stream_v
        ]
        super().__init__(self.left_column_structure)

    def menu_view(self) -> Any:
        count = self.model.unread_counts.get('all_msg', 0)
        self.view.home_button = HomeButton(self.controller,
                                           count=count,
                                           width=self.width)

        count = self.model.unread_counts.get('all_pms', 0)
        self.view.pm_button = PMButton(self.controller,
                                       count=count,
                                       width=self.width)

        self.view.mentioned_button = MentionedButton(
            self.controller,
            width=self.width,
            count=self.model.unread_counts['all_mentions'])

        # Starred messages are by definition read already
        self.view.starred_button = StarredButton(self.controller,
                                                 width=self.width)

        menu_btn_list = [
            self.view.home_button,
            self.view.pm_button,
            self.view.mentioned_button,
            self.view.starred_button,
        ]
        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self) -> Any:
        streams_btn_list = [
                StreamButton(
                    stream,
                    controller=self.controller,
                    view=self.view,
                    width=self.width,
                    count=self.model.unread_counts['streams'].get(stream[1], 0)
                ) for stream in self.view.pinned_streams]

        if len(streams_btn_list):
            unpinned_divider = urwid.Divider("-")

            # FIXME Necessary since the divider is treated as a StreamButton
            # NOTE: This is specifically for stream search to work correctly
            unpinned_divider.stream_id = -1
            unpinned_divider.stream_name = ''

            streams_btn_list += [unpinned_divider]

        streams_btn_list += [
                StreamButton(
                    stream,
                    controller=self.controller,
                    view=self.view,
                    width=self.width,
                    count=self.model.unread_counts['streams'].get(stream[1], 0)
                ) for stream in self.view.unpinned_streams]

        self.view.stream_id_to_button = {stream.stream_id: stream
                                         for stream in streams_btn_list
                                         if hasattr(stream, 'stream_id')}

        self.view.stream_w = StreamsView(streams_btn_list, self.view)
        w = urwid.LineBox(
            self.view.stream_w, title="Streams",
            tlcorner=u'━', tline=u'━', lline=u'',
            trcorner=u'━', blcorner=u'', rline=u'',
            bline=u'', brcorner=u'─'
            )
        return w

    def topics_view(self, stream_button: Any) -> Any:
        stream_id = stream_button.stream_id
        topics_btn_list = [
            TopicButton(
                stream_id=stream_id,
                topic=topic,
                controller=self.controller,
                width=self.width,
                count=self.model.unread_counts['unread_topics'].
                get((stream_id, topic), 0)
            ) for topic in self.model.index['topics'][stream_id]]

        self.view.topic_w = TopicsView(topics_btn_list, self.view,
                                       stream_button)
        w = urwid.LineBox(
            self.view.topic_w, title="Topics",
            tlcorner=u'━', tline=u'━', lline=u'',
            trcorner=u'━', blcorner=u'', rline=u'',
            bline=u'', brcorner=u'─'
            )
        return w

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if (is_command_key('SEARCH_STREAMS', key) or
                is_command_key('SEARCH_TOPICS', key)):
            self.focus_position = 1
            if self.is_in_topic_view:
                self.view.topic_w.keypress(size, key)
            else:
                self.view.stream_w.keypress(size, key)
            return key
        elif is_command_key('GO_RIGHT', key):
            self.view.show_left_panel(visible=False)
        return super().keypress(size, key)


class PopUpView(urwid.ListBox):
    def __init__(self, controller: Any, widgets: List[Any],
                 command: str) -> None:
        self.controller = controller
        self.command = command
        self.log = urwid.SimpleFocusListWalker(widgets)
        super().__init__(self.log)

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key('GO_BACK', key) or is_command_key(self.command, key):
            self.controller.exit_popup()
        elif is_command_key('GO_UP', key):
            key = 'up'
        elif is_command_key('GO_DOWN', key):
            key = 'down'
        elif is_command_key('SCROLL_UP', key):
            key = 'page up'
        elif is_command_key('SCROLL_DOWN', key):
            key = 'page down'
        elif is_command_key('GO_TO_BOTTOM', key):
            key = 'end'
        return super().keypress(size, key)


class HelpView(PopUpView):
    def __init__(self, controller: Any) -> None:
        widths = [(len(binding['help_text'])+4,
                   len(", ".join(binding['keys'])))
                  for binding in KEY_BINDINGS.values()]
        max_widths = [max(width) for width in zip(*widths)]
        self.width = sum(max_widths)

        help_menu_content = []  # type: List[urwid.AttrWrap]
        for category in HELP_CATEGORIES:
            if len(help_menu_content) > 0:  # Separate categories by newline
                help_menu_content.append(urwid.Text(''))

            help_menu_content.append(urwid.Text(('popup_category',
                                                 HELP_CATEGORIES[category])))

            keys_in_category = (binding for binding in KEY_BINDINGS.values()
                                if binding['key_category'] == category)
            for help_item_number, binding in enumerate(keys_in_category):
                help_menu_content.append(
                    urwid.AttrWrap(
                        urwid.Columns([
                            urwid.Text(binding['help_text']),
                            (max_widths[1],
                                urwid.Text(", ".join(binding['keys'])))
                            ], dividechars=2),
                        None if help_item_number % 2 else 'popup_contrast'
                    )
                )

        self.height = len(help_menu_content)

        super().__init__(controller, help_menu_content, 'HELP')


class PopUpConfirmationView(urwid.Overlay):
    def __init__(self, controller: Any, question: Any,
                 success_callback: Callable[[], bool]):
        self.controller = controller
        self.success_callback = success_callback
        yes = urwid.Button(u'Yes', self.exit_popup_yes)
        no = urwid.Button(u'No', self.exit_popup_no)
        yes._w = urwid.AttrMap(urwid.SelectableIcon(
            'Yes', 4), None, 'selected')
        no._w = urwid.AttrMap(urwid.SelectableIcon(
            'No', 4), None, 'selected')
        display_widget = urwid.GridFlow([yes, no], 3, 5, 1, 'center')
        wrapped_widget = urwid.WidgetWrap(display_widget)
        prompt = urwid.LineBox(
            urwid.ListBox(
                urwid.SimpleFocusListWalker(
                    [question, urwid.Divider(), wrapped_widget]
                )))
        urwid.Overlay.__init__(self, prompt, self.controller.view,
                               align="left", valign="top",
                               width=self.controller.view.LEFT_WIDTH+1,
                               height=8)

    def exit_popup_yes(self, args: Any) -> None:
        self.success_callback()
        self.controller.exit_popup()

    def exit_popup_no(self, args: Any) -> None:
        self.controller.exit_popup()

    def keypress(self, size: urwid_Size, key: str) -> str:
        if is_command_key('GO_BACK', key):
            self.controller.exit_popup()
        return super().keypress(size, key)


class StreamInfoView(PopUpView):
    def __init__(self, controller: Any, color: str,
                 name: str, desc: str) -> None:
        # TODO: Width & Height handling could be improved
        self.width = max(len(desc), len("# {}".format(name)))+2
        self.height = 2
        stream_info_content = [urwid.Text(desc, align='center')]
        super().__init__(controller, stream_info_content, 'STREAM_DESC')


class MsgInfoView(PopUpView):
    def __init__(self, controller: Any, msg: Message) -> None:
        self.msg = msg

        if msg['reactions']:
            reactions = sorted(
                        [reaction['emoji_name'] +
                            ": " +
                            reaction['user']['full_name'] +
                            "\n"
                            for reaction in msg['reactions']])
            reactions[-1] = reactions[-1].rstrip("\n")

        msg_info = OrderedDict([
            ('Date & Time', time.ctime(msg['timestamp'])[:-5]),
            ('Sender', msg['sender_full_name']),
            ('Sender\'s Email ID', msg['sender_email']),
            ('Reactions', reactions if msg['reactions'] else '---None---'),
            ])

        widths = [(len(field)+7,
                  max(len(reaction_users) for reaction_users in data)
                  if isinstance(data, list)
                  else len(data)+2)
                  for field, data in msg_info.items()]
        max_widths = [max(width) for width in zip(*widths)]
        self.width = sum(max_widths)
        self.height = len(msg_info['Reactions'])+4 if msg['reactions'] else 5

        msg_info_content = [urwid.AttrWrap(
                urwid.Columns([
                    urwid.Text(field),
                    (max_widths[1], urwid.Text(data))
                ], dividechars=2),
                None if index % 2 else 'popup_contrast')
             for index, (field, data) in enumerate(msg_info.items())]

        super().__init__(controller, msg_info_content, 'MSG_INFO')
