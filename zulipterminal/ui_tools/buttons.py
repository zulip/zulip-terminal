import urwid
from typing import Any, List


class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='') -> None:
        self.caption = caption  # str
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'    ', self.caption], 0), None, 'selected')


class HomeButton(urwid.Button):
    def __init__(self, controller: Any=None) -> None:
        self.caption = 'All messages'
        super(HomeButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \u26FA  ', self.caption], 0), None, 'selected')
        urwid.connect_signal(self, 'click', controller.show_all_messages)


class PMButton(urwid.Button):
    def __init__(self, controller: Any=None) -> None:
        self.caption = 'Private messages'
        super(PMButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \u260F  ', self.caption], 0), None, 'selected')
        urwid.connect_signal(self, 'click', controller.show_all_pm)


class StreamButton(urwid.Button):
    def __init__(self, properties: List[Any], email: str='',
                 controller: Any=None, view: Any=None) -> None:
        self.caption = properties[0]
        self.stream_id = properties[1]
        color = properties[2]
        color = color[:2] + color[3] + color[5]
        view.palette['default'].append((color, '', '', '', color, 'black'))
        self.email = email
        super(StreamButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [(color, u'  # '), self.caption],
            len(self.caption) + 4),
            None,
            'selected')
        urwid.connect_signal(self, 'click', controller.narrow_to_stream)
        urwid.connect_signal(self, 'click', view.write_box.stream_box_view)


class UserButton(urwid.Button):
    def __init__(self, caption: Any, email: str='', controller: Any=None,
                 view: Any=None, color: str=None) -> None:
        self.caption = caption  # str
        self.email = email
        super(UserButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', self.caption], 0), color, 'selected')
        urwid.connect_signal(self, 'click', controller.narrow_to_user)
        urwid.connect_signal(self, 'click',
                             view.write_box.private_box_view)
