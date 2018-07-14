from typing import Any, Dict, List, Tuple

import urwid

from zulipterminal.config import is_command_key


class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='') -> None:
        self.caption = caption  # str
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [self.caption], 0), None, 'selected')


class HomeButton(urwid.Button):
    def __init__(self, controller: Any, count: int=0) -> None:
        self.caption = 'All messages'
        self.count = count
        super(HomeButton, self).__init__("")
        self._w = self.widget(count)
        urwid.connect_signal(self, 'click', controller.show_all_messages)

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        return urwid.AttrMap(urwid.SelectableIcon(
            [u' \N{BULLET} ', self.caption,
             ('idle', '' if count <= 0 else ' ' + str(count))],
            len(self.caption) + 4),
            None,
            'selected')


class PMButton(urwid.Button):
    def __init__(self, controller: Any, count: int=0) -> None:
        self.caption = 'Private messages'
        super(PMButton, self).__init__("")
        self.count = count
        self._w = self.widget(count)
        urwid.connect_signal(self, 'click', controller.show_all_pm)

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        return urwid.AttrMap(urwid.SelectableIcon(
            [u' \N{BULLET} ', self.caption,
             ('idle', '' if count <= 0 else ' ' + str(count))],
            len(self.caption) + 4),
            None,
            'selected')


class StreamButton(urwid.Button):
    def __init__(self, properties: List[Any],
                 controller: Any, view: Any, count: int=0) -> None:
        self.caption = properties[0]
        self.stream_id = properties[1]
        color = properties[2]
        self.color = color[:2] + color[3] + color[5]
        view.palette['default'].append((self.color, '', '', '', self.color,
                                       'black'))
        view.palette['default'].append(('s' + self.color, '', '', '',
                                       'black', self.color))
        self.count = count
        super(StreamButton, self).__init__("")
        self._w = self.widget(count)
        urwid.connect_signal(self, 'click', controller.narrow_to_stream)

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        return urwid.AttrMap(urwid.SelectableIcon(
            [(self.color, u' # '), self.caption,
             ('idle', '' if count <= 0 else ' ' + str(count))],
            len(self.caption) + 2),
            None,
            'selected')


class UserButton(urwid.Button):
    def __init__(self, user: Dict[str, Any], controller: Any,
                 view: Any, color: str=None, count: int=0) -> None:
        self.caption = user['full_name']  # str
        self.email = user['email']
        self.user_id = user['user_id']
        self.color = color
        self.count = count
        self.recipients = frozenset({
            self.user_id, view.model.user_id})
        super(UserButton, self).__init__("")
        self._w = self.widget(count)
        self.controller = controller
        self.view = view

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        return urwid.AttrMap(urwid.SelectableIcon(
            [u'\N{BULLET} ', self.caption,
             ('idle', '' if count <= 0 else ' ' + str(count))],
            len(self.caption) + 2),
            self.color,
            'selected')

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            self.controller.narrow_to_user(self)
            self.view.body.focus_col = 1
            self.view.body.focus.original_widget.set_focus('footer')
            self.view.write_box.private_box_view(self)
            return key
        return super(UserButton, self).keypress(size, key)


class TopicButton(urwid.Button):
    def __init__(self, stream_id: str, topic: str, model: Any) -> None:
        self.caption = model.stream_dict[int(stream_id)]['name']  # stream name
        self.title = topic
        self.stream_id = int(stream_id)


class UnreadPMButton(urwid.Button):
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email
