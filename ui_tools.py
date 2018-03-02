from typing import Any, List, Tuple, Dict
import urwid
from time import ctime
import itertools

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
        return super(StreamsView, self).mouse_event(size, event, button, col, row, focus)

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
        return super(UsersView, self).mouse_event(size, event, button, col, row, focus)

class MiddleColumnView(urwid.Frame):
    def __init__(self, messages: Any, model: Any, write_box: Any) -> None:
        msg_list = MessageView(messages, model)
        model.msg_list = msg_list
        super(MiddleColumnView, self).__init__(msg_list, footer=write_box)


class MessageBox(urwid.Pile):
    def __init__(self, message: str, model: Any) -> None:
        self.model = model
        self.message = message
        super(MessageBox, self).__init__(self.main_view())

    def stream_view(self) -> Any:
        stream_title = ('header', [
        ('custom', self.message['stream']), 
        ('selected', ">"),
        ('custom', self.message['title'])
        ])
        stream_title = urwid.Text(stream_title)
        time = urwid.Text(('custom', ctime(self.message['time'])), align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def private_view(self) -> Any:
        title = ('header', [('custom', 'Private Message')])
        title = urwid.Text(title)
        time = urwid.Text(('custom', ctime(self.message['time'])), align='right')
        header = urwid.Columns([
            title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def main_view(self) -> List[Any]:
        if self.message['type'] == 'stream':
            header = self.stream_view()
        else:
            header = self.private_view()
        content = [('name', self.message['sender']), "\n" + self.message['content']]
        content = urwid.Text(content)
        return [header, content]

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            if button == 1:
                self.keypress(size, 'enter')
                return True
        return super(MessageBox, self).mouse_event(size, event, button, col, row, focus)

    def keypress(self, size, key):
        if key == 'enter':
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(email=self.message['sender_email'])
            if self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(caption=self.message['stream'], title=self.message['title'])
        return key


class MessageView(urwid.ListBox):
    def __init__(self, messages: str, model: Any) -> None:
        self.model = model
        self.messages = messages
        self.log = urwid.SimpleFocusListWalker(self.main_view())

        # This Function completely controls the messages shown in the MessageView
        self.model.msg_view = self.log

        super(MessageView, self).__init__(self.log)

        # Set Focus to the last message
        self.set_focus(len(self.body) - 1)

    def main_view(self) -> List[Any]:
        msg_btn_list = create_msg_box_list(self.messages, self.model)
        return msg_btn_list

    def load_old_messages(self, anchor: int=10000000000) -> None:
        # Use the currently focused image as anchor
        self.model.anchor = anchor
        # We don't want message after the current message
        self.model.num_after = 0
        self.model.num_before = 30
        new_messages = self.model.load_old_messages(False)
        new_messages = itertools.chain.from_iterable(new_messages.values())
        new_messages = sorted(new_messages, key=lambda msg: msg['time'], reverse=True)
        # Skip the first message as we don't want to display the focused message again
        for msg in new_messages[1:]:
            self.log.insert(0, urwid.AttrMap(MessageBox(msg, self.model), None, 'msg_selected'))

    def load_new_messages(self, anchor: int) -> None:
        self.model.anchor = anchor
        self.model.num_before = 0
        self.model.num_after = 30
        new_messages = self.model.load_old_messages(False)
        new_messages = itertools.chain.from_iterable(new_messages.values())
        new_messages = sorted(new_messages, key=lambda msg: msg['time'], reverse=True)
        # Skip the first message as we don't want to display the focused message again
        for msg in new_messages[:-1]:
            self.log.insert(self.focus_position + 1, urwid.AttrMap(MessageBox(msg, self.model), None, 'msg_selected'))

    def mouse_event(self, size: Any, event: str, button: int, col: int, row: int, focus: Any) -> Any:
        if event == 'mouse press':
            if button == 4:
                self.keypress(size, 'up')
                return True
            if button == 5:
                self.keypress(size, 'down')
                return True
        return super(MessageView, self).mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'down':
            try:
                self.focus_position = self.log.next_position(self.focus_position)
                return key
            except Exception:
                if self.focus:
                    self.load_new_messages(self.focus.original_widget.message['id'])
                return key

        if key == 'up':
            try:
                self.focus_position = self.log.prev_position(self.focus_position)
                return key
            except Exception:
                if self.focus:
                    self.load_old_messages(self.focus.original_widget.message['id'])
                else:
                    self.load_old_messages()
                return key
        key = super(MessageView, self).keypress(size, key)
        return key

class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='', controller: Any=None, view: Any=None, user: str=False, stream: bool=False) -> None:
        self.caption = caption  # str
        if stream:  # caption = [stream_name, stream_id]
            self.caption = caption[0]
            self.stream_id = caption[1]
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  # ', self.caption], 0), None, 'selected')
        if stream:
            urwid.connect_signal(self, 'click', controller.narrow_to_stream)
            urwid.connect_signal(self, 'click', view.write_box.stream_box_view)
        if user:
            urwid.connect_signal(self, 'click', controller.narrow_to_user)
            urwid.connect_signal(self, 'click', view.write_box.private_box_view)
        if self.caption == u'All messages':
            urwid.connect_signal(self, 'click', controller.show_all_messages)


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super(WriteBox, self).__init__(self.main_view(True))
        self.client = view.client
        self.to_write_box=None
        self.stream_write_box=None

    def main_view(self, new: bool) -> Any:
        private_button = MenuButton(u"New Private Message")
        urwid.connect_signal(private_button, 'click', self.private_box_view)
        stream_button = MenuButton(u"New Topic")
        urwid.connect_signal(stream_button, 'click', self.stream_box_view)
        w = urwid.Columns([
            urwid.LineBox(private_button),
            urwid.LineBox(stream_button),
        ])
        if new:
            return [w]
        else:
            self.contents = [(w, self.options())]

    def private_box_view(self, button: Any=None, email: str='') -> None:
        if email=='':
            email = button.email
        self.to_write_box = urwid.Edit(u"To: ", edit_text=email)
        self.msg_write_box = urwid.Edit(u"> ")
        self.contents = [
            (urwid.LineBox(self.to_write_box), self.options()),
            (self.msg_write_box, self.options()),
        ]

    def stream_box_view(self, button: Any=None, caption: str='', title: str='') -> None:
        if caption == '':
            caption = button.caption
        self.msg_write_box = urwid.Edit(u"> ")
        self.stream_write_box = urwid.Edit(caption=u"Stream:  ", edit_text=caption)
        self.title_write_box = urwid.Edit(caption=u"Title:  ", edit_text=title)

        header_write_box = urwid.Columns([
            urwid.LineBox(self.stream_write_box),
            urwid.LineBox(self.title_write_box),
        ])
        write_box = [
            (header_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'enter':
            if not self.to_write_box:
                request = {
                    'type' : 'stream',
                    'to' : self.stream_write_box.edit_text,
                    'subject' : self.title_write_box.edit_text,
                    'content' : self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)
            else:
                request = {
                    'type' : 'private',
                    'to' : self.to_write_box.edit_text,
                    'content' : self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)
            if response['result'] == 'success':
                self.msg_write_box.edit_text = ''
        if key == 'esc':
            self.main_view(False)
        key = super(WriteBox, self).keypress(size, key)
        return key

def create_msg_box_list(messages: List[Dict[str, Any]], model: Any) -> List[Any]:
    messages = sorted(messages, key=lambda msg: msg['time'])
    return [urwid.AttrMap(MessageBox(item, model), None, 'msg_selected') for item in messages]
