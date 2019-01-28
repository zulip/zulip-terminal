from typing import Any, Dict, List, Tuple, Callable, Optional, Union

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
                 show_function: Callable[..., Any], width: int,
                 prefix_character: Union[str, Tuple[Any, str]]='\N{BULLET}',
                 text_color: Optional[str]=None,
                 count: int=0) -> None:
        self.caption = caption
        self.prefix_character = prefix_character
        self.count = count
        self.width_for_text_space_count = width - 4
        self.text_color = text_color
        self.show_function = show_function
        super().__init__("")
        self._w = self.widget(count)
        self.controller = controller
        urwid.connect_signal(self, 'click', self.activate)

    def update_count(self, count: int) -> None:
        self.count = count
        self._w = self.widget(count)

    def widget(self, count: int) -> Any:
        if count < 0:
            count_text = 'M'  # Muted
        elif count == 0:
            count_text = ''
        else:
            count_text = str(count)

        # Shrink text, but always require at least one space
        max_caption_length = (self.width_for_text_space_count -
                              len(str(count_text)) - 1)
        if len(self.caption) > max_caption_length:
            caption = self.caption[:max_caption_length-2] + '..'
        else:
            caption = self.caption
        num_spaces = max_caption_length - len(caption) + 1

        return urwid.AttrMap(urwid.SelectableIcon(
            [' ', self.prefix_character,
             ' {}{}'.format(caption, num_spaces*' '),
             ('idle',  count_text)],
            self.width_for_text_space_count+4),  # cursor location
            self.text_color,
            'selected')

    def activate(self, key: Any) -> None:
        self.controller.view.show_left_panel(visible=False)
        self.controller.view.show_right_panel(visible=False)
        self.controller.view.body.focus_col = 1
        self.show_function(self)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            self.activate(key)
        return super().keypress(size, key)


class HomeButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        super().__init__(controller, 'All messages',
                         controller.show_all_messages, count=count,
                         width=width)


class PMButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        super().__init__(controller, 'Private messages',
                         controller.show_all_pm, count=count,
                         width=width)


class StarredButton(TopButton):
    def __init__(self, controller: Any, width: int) -> None:
        super().__init__(controller, 'Starred messages',
                         controller.show_all_starred,
                         width=width,
                         count=0)  # Starred messages are already marked read


class StreamButton(TopButton):
    def __init__(self, properties: List[Any],
                 controller: Any, view: Any, width: int,
                 count: int=0) -> None:
        # FIXME Is having self.stream_id the best way to do this?
        # (self.stream_id is used elsewhere)
        caption, self.stream_id, orig_color, is_private = properties

        # Simplify the color from the original version & add to palette
        # TODO Should this occur elsewhere and more intelligently?
        color = ''.join(orig_color[i] for i in (0, 1, 3, 5))  # 0 -> '#'
        for entry in view.palette:
            if entry[0] is None:
                background = entry[5] if len(entry) > 4 else entry[2]
                break
        view.palette.append((color, '', '', '', color+', bold', background))
        view.palette.append(('s' + color, '', '', '', background, color))

        super().__init__(controller,
                         caption=caption,
                         show_function=controller.narrow_to_stream,
                         prefix_character=(color, 'P' if is_private else '#'),
                         width=width,
                         count=count)


class UserButton(TopButton):
    def __init__(self, user: Dict[str, Any], controller: Any,
                 view: Any, width: int,
                 color: Optional[str]=None, count: int=0) -> None:
        # Properties accessed externally
        self.email = user['email']
        self.user_id = user['user_id']

        self._view = view  # Used in _narrow_with_compose

        # FIXME Is this still needed?
        self.recipients = frozenset({self.user_id, view.model.user_id})

        caption = user['full_name']
        super().__init__(controller,
                         caption=caption,
                         show_function=self._narrow_with_compose,
                         prefix_character=(color, '\N{BULLET}'),
                         text_color=color,
                         width=width,
                         count=count)

    def _narrow_with_compose(self, button: Any) -> None:
        # Switches directly to composing with user
        # FIXME should we just narrow?
        self.controller.narrow_to_user(self)
        self._view.body.focus.original_widget.set_focus('footer')
        self._view.write_box.private_box_view(self)


class TopicButton(urwid.Button):
    def __init__(self, stream_id: str, topic: str, model: Any) -> None:
        self.caption = model.stream_dict[int(stream_id)]['name']  # stream name
        self.title = topic
        self.stream_id = int(stream_id)


class UnreadPMButton(urwid.Button):
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email
