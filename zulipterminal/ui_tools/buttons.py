import urwid
from typing import Any


class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='', controller: Any=None,
                 view: Any=None, user: str=False, stream: bool=False,
                 color: str=None) -> None:
        self.caption = caption  # str
        if stream:  # caption = [stream_name, stream_id, color]
            self.caption = caption[0]
            self.stream_id = caption[1]
            color = caption[2]
            color = color[:2] + color[3] + color[5]
            view.palette['default'].append((color, '', '', '', color, 'black'))
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  # ', self.caption], 0), color, 'selected')
        if stream:
            urwid.connect_signal(self, 'click', controller.narrow_to_stream)
            urwid.connect_signal(self, 'click', view.write_box.stream_box_view)
        if user:
            urwid.connect_signal(self, 'click', controller.narrow_to_user)
            urwid.connect_signal(self, 'click',
                                 view.write_box.private_box_view)
        if self.caption == u'All messages':
            urwid.connect_signal(self, 'click', controller.show_all_messages)
        if self.caption == u'Private messages':
            urwid.connect_signal(self, 'click', controller.show_all_pm)
