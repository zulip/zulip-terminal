from typing import Any, List, Tuple
import urwid

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
        time = urwid.Text(('custom', self.message['time']), align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def private_view(self) -> Any:
        title = ('header', [('custom', 'Private Message')])
        title = urwid.Text(title)
        time = urwid.Text(('custom', self.message['time']), align='right')
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
        content = self.message['sender'] + " : " + self.message['content']
        content = urwid.Text(content.encode('utf-8'))
        return [header, content]


class MessageView(urwid.ListBox):
    def __init__(self, messages: str, model: Any) -> None:
        self.model = model
        self.messages = messages
        self.log = urwid.SimpleFocusListWalker(self.main_view())
        super(MessageView, self).__init__(self.log)
        self.focus_position = 50

    def main_view(self) -> List[Any]:
        msg_btn_list = [urwid.AttrMap(MessageBox(item, self.model), None, 'msg_selected') for item in self.messages]
        return msg_btn_list

    def load_old_messages(self) -> None:
        self.model.num_before += 50
        self.model.messages = self.model.load_old_messages(False)
        new_messages = self.model.messages[:50]
        new_messages.reverse()
        for msg in new_messages:
            self.log.insert(0, urwid.AttrMap(MessageBox(msg, self), None, 'msg_selected'))

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'down':
            try:
                self.focus_position = self.log.next_position(self.focus_position)
                return key
            except Exception:
                return key

        if key == 'up':
            try:
                self.focus_position = self.log.prev_position(self.focus_position)
                return key
            except Exception:
                self.load_old_messages()
                return key
        key = super(MessageView, self).keypress(size, key)
        return key


class MenuButton(urwid.Button):
    def __init__(self, caption: str, email: str='', view: Any=None, user: str=False, stream: bool=False) -> None:
        self.caption = caption
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  # ', caption], 0), None, 'selected')
        if stream:
            urwid.connect_signal(self, 'click', view.write_box.stream_box_view)
        if user:
            urwid.connect_signal(self, 'click', view.write_box.private_box_view)


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

    def private_box_view(self, button: Any) -> None:
        self.to_write_box = urwid.Edit(u"To: ", edit_text=button.email)
        self.msg_write_box = urwid.Edit(u"> ")
        self.contents = [
            (urwid.LineBox(self.to_write_box), self.options()),
            (self.msg_write_box, self.options()),
        ]

    def stream_box_view(self, button: Any) -> None:
        self.msg_write_box = urwid.Edit(u"> ")
        self.stream_write_box = urwid.Edit(caption=u"Stream:  ", edit_text=button.caption)
        self.title_write_box = urwid.Edit(caption=u"Title:  ")

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
