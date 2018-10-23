from typing import Any, Dict, List, Tuple, Callable, Optional

import urwid

from zulipterminal.config.keys import is_command_key


class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='') -> None:
        self.caption = caption  # str
        self.email = email
        super(MenuButton, self).__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [self.caption], 0), None, 'selected')


class TopButton(urwid.Button):
    def __init__(self, controller: Any, caption: str,
                 show_function: Callable[..., Any], count: int=0) -> None:
        self.caption = caption
        self.count = count
        super().__init__("")
        self._w = self.widget(count)
        self.controller = controller
        urwid.connect_signal(self, 'click', show_function)

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

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            self.controller.view.show_left_panel(visible=False)
            self.controller.view.body.focus_col = 1
        return super().keypress(size, key)


class HomeButton(TopButton):
    def __init__(self, controller: Any, count: int=0) -> None:
        super().__init__(controller, 'All messages',
                         controller.show_all_messages, count=count)


class PMButton(TopButton):
    def __init__(self, controller: Any, count: int=0) -> None:
        super().__init__(controller, 'Private messages',
                         controller.show_all_pm, count=count)


class StarredButton(TopButton):
    def __init__(self, controller: Any) -> None:
        super().__init__(controller, 'Starred messages',
                         controller.show_all_starred,
                         count=0)  # Starred messages are already marked read


class StreamButton(urwid.Button):
    def __init__(self, properties: List[Any],
                 controller: Any, view: Any, count: int=0) -> None:
        self.caption = properties[0]
        self.stream_id = properties[1]
        color = properties[2]
        self.color = color[:2] + color[3] + color[5]
        view.palette.append((self.color, '', '', '', self.color, 'black'))
        view.palette.append(('s' + self.color, '', '', '', 'black',
                             self.color))
        self.is_private = properties[3]
        self.count = count
        super(StreamButton, self).__init__("")
        self._w = self.widget(count)
        self.controller = controller
        urwid.connect_signal(self, 'click', controller.narrow_to_stream)

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        stream_prefix = 'P' if self.is_private else '#'
        if count < 0:
            count_text = ' M'  # Muted
        elif count == 0:
            count_text = ''
        else:
            count_text = ' ' + str(count)
        return urwid.AttrMap(urwid.SelectableIcon(
            [' ', (self.color, stream_prefix), ' ', self.caption,
             ('idle', count_text)],
            len(self.caption) + 2),
            None,
            'selected')

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            self.controller.view.show_left_panel(visible=False)
            self.controller.view.body.focus_col = 1
        return super(StreamButton, self).keypress(size, key)


class UserButton(urwid.Button):
    def __init__(self, user: Dict[str, Any], controller: Any,
                 view: Any, color: Optional[str]=None, count: int=0) -> None:
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
