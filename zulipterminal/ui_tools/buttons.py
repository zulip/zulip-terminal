from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import urwid

from zulipterminal.config.keys import is_command_key, keys_for_command
from zulipterminal.urwid_types import urwid_Size


class MenuButton(urwid.Button):
    def __init__(self, caption: Any, email: str='') -> None:
        self.caption = caption  # str
        self.email = email
        super().__init__("")
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [self.caption], 0), None, 'selected')


class TopButton(urwid.Button):
    def __init__(self, controller: Any, caption: str,
                 show_function: Callable[..., Any], width: int,
                 prefix_character: Union[str, Tuple[Any, str]]='\N{BULLET}',
                 text_color: Optional[str]=None,
                 count: int=0) -> None:
        if isinstance(prefix_character, tuple):
            prefix = prefix_character[1]
        else:
            prefix = prefix_character
        assert len(prefix) in (0, 1)
        self._caption = caption
        self.prefix_character = prefix_character
        self.post_prefix_spacing = ' ' if prefix else ''
        self.count = count

        prefix_length = 0 if prefix == '' else 2
        # Space either side, at least one space between
        self.width_for_text_and_count = width - 3 - prefix_length

        self.text_color = text_color
        self.show_function = show_function
        super().__init__("")
        self.update_count(count)
        self.controller = controller
        urwid.connect_signal(self, 'click', self.activate)

    def update_count(self, count: int) -> None:
        self.count = count
        if count == 0:
            count_text = ''
        else:
            count_text = str(count)
        self.update_widget(count_text)

    def update_widget(self, count_text: str) -> Any:
        # Note that we don't modify self._caption
        max_caption_length = (self.width_for_text_and_count -
                              len(count_text))
        if len(self._caption) > max_caption_length:
            caption = (self._caption[:max_caption_length-1] +
                       '\N{HORIZONTAL ELLIPSIS}')
        else:
            caption = self._caption
        num_extra_spaces = (
            self.width_for_text_and_count - len(count_text) - len(caption)
        )

        # NOTE: Generated text does not include space at end
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [' ', self.prefix_character, self.post_prefix_spacing,
             '{}{}'.format(caption, num_extra_spaces*' '),
             ' ', ('unread_count',  count_text)],
            self.width_for_text_and_count+5),  # cursor location
            self.text_color,
            'selected')

    def activate(self, key: Any) -> None:
        self.controller.view.show_left_panel(visible=False)
        self.controller.view.show_right_panel(visible=False)
        self.controller.view.body.focus_col = 1
        self.show_function(self)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('ENTER', key):
            self.activate(key)
        return super().keypress(size, key)


class HomeButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("All messages   [" +
                       keys_for_command("GO_BACK").pop() +  # FIXME
                       "]")
        super().__init__(controller, button_text,
                         controller.show_all_messages, count=count,
                         prefix_character='',
                         width=width)


class PMButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("Private messages [" +
                       keys_for_command("ALL_PM").pop() +
                       "]")
        super().__init__(controller, button_text,
                         controller.show_all_pm, count=count,
                         prefix_character='',
                         width=width)


class MentionedButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("Mentions         [" +
                       keys_for_command("ALL_MENTIONS").pop() +
                       "]")
        super().__init__(controller, button_text,
                         controller.show_all_mentions,
                         width=width,
                         count=count,
                         prefix_character='')


class StarredButton(TopButton):
    def __init__(self, controller: Any, width: int) -> None:
        button_text = ("Starred messages [" +
                       keys_for_command("ALL_STARRED").pop() +
                       "]")
        super().__init__(controller, button_text,
                         controller.show_all_starred,
                         width=width,
                         prefix_character='',
                         count=0)  # Starred messages are already marked read


class StreamButton(TopButton):
    def __init__(self, properties: List[Any],
                 controller: Any, view: Any, width: int,
                 count: int=0) -> None:
        # FIXME Is having self.stream_id the best way to do this?
        # (self.stream_id is used elsewhere)
        self.stream_name, self.stream_id, self.color, is_private, \
            self.description = properties
        self.model = controller.model
        self.count = count
        self.view = view

        for entry in view.palette:
            if entry[0] is None:
                background = entry[5] if len(entry) > 4 else entry[2]
                inverse_text = background if background else 'black'
                break
        view.palette.append((
            self.color, '', '', '', self.color+', bold', background))
        view.palette.append((
            's' + self.color, '', '', '', inverse_text, self.color))

        super().__init__(controller,
                         caption=self.stream_name,
                         show_function=controller.narrow_to_stream,
                         prefix_character=(
                            self.color, 'P' if is_private else '#'),
                         width=width,
                         count=count)

        # Mark muted streams 'M' during button creation.
        if self.model.is_muted_stream(self.stream_id):
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget('M')
        self.model.unread_counts['all_msg'] -= self.count
        self.view.home_button.update_count(
            self.model.unread_counts['all_msg'])

    def mark_unmuted(self) -> None:
        if self.stream_id in self.model.unread_counts['streams']:
            unmuted_count = self.model.unread_counts['streams'][self.stream_id]
            self.update_count(unmuted_count)
            self.model.unread_counts['all_msg'] += self.count
            self.view.home_button.update_count(
                self.model.unread_counts['all_msg'])
        else:
            # All messages in this stream are read.
            self.update_count(0)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('TOGGLE_TOPIC', key):
            topic_view = self.view.left_panel.topics_view(self)
            self.view.left_panel.is_in_topic_view = True
            self.view.left_panel.contents[1] = (
                topic_view,
                self.view.left_panel.options(height_type="weight")
                )
        elif is_command_key('TOGGLE_MUTE_STREAM', key):
            self.controller.stream_muting_confirmation_popup(self)
        elif is_command_key('STREAM_DESC', key):
            self.model.controller.show_stream_info(
                self.color, self.stream_name, self.description)
        return super().keypress(size, key)


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

        super().__init__(controller,
                         caption=user['full_name'],
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


class TopicButton(TopButton):
    def __init__(self, stream_id: int, topic: str,
                 controller: Any, width: int=0, count: int=0) -> None:
        self.stream_name = controller.model.stream_dict[stream_id]['name']
        self.topic_name = topic
        self.stream_id = stream_id
        self.model = controller.model

        super().__init__(controller=controller,
                         caption=self.topic_name,
                         prefix_character='',
                         show_function=controller.narrow_to_topic,
                         width=width,
                         count=count)

        if [self.stream_name, self.topic_name] in \
                controller.model.muted_topics:
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget('M')
    # TODO: Handle event-based approach for topic-muting.


class UnreadPMButton(urwid.Button):
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email
