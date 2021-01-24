import re
from typing import Any, Callable, Dict, Optional, Tuple, Union, cast
from urllib.parse import urljoin, urlparse

import urwid
from typing_extensions import TypedDict

from zulipterminal.config.keys import is_command_key, primary_key_for_command
from zulipterminal.config.symbols import (
    MUTE_MARKER,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
)
from zulipterminal.helper import (
    StreamData,
    edit_mode_captions,
    hash_util_decode,
)
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

        self.original_color = text_color
        self.show_function = show_function
        super().__init__("")
        self.update_count(count, text_color)
        self.controller = controller
        urwid.connect_signal(self, 'click', self.activate)

    def update_count(self, count: int, text_color: Optional[str]=None) -> None:
        new_color = self.original_color if text_color is None else text_color

        self.count = count
        if count == 0:
            count_text = ''
        else:
            count_text = str(count)
        self.update_widget(('unread_count', count_text), new_color)

    def update_widget(self, count_text: Tuple[str, str],
                      text_color: Optional[str]) -> Any:
        # Note that we don't modify self._caption
        max_caption_length = (self.width_for_text_and_count
                              - len(count_text[1]))
        if len(self._caption) > max_caption_length:
            caption = (self._caption[:max_caption_length - 1]
                       + '\N{HORIZONTAL ELLIPSIS}')
        else:
            caption = self._caption
        num_extra_spaces = (
            self.width_for_text_and_count - len(count_text[1]) - len(caption)
        )

        # NOTE: Generated text does not include space at end
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [' ', self.prefix_character, self.post_prefix_spacing,
             '{}{}'.format(caption, num_extra_spaces * ' '),
             ' ', count_text],
            self.width_for_text_and_count + 5),  # cursor location
            text_color,
            'selected')

    def activate(self, key: Any) -> None:
        self.controller.view.show_left_panel(visible=False)
        self.controller.view.show_right_panel(visible=False)
        self.controller.view.body.focus_col = 1
        self.show_function(self)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('ENTER', key):
            self.activate(key)
            return None
        else:  # This is in the else clause, to avoid multiple activation
            return super().keypress(size, key)


class HomeButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("All messages     ["
                       + primary_key_for_command("ALL_MESSAGES")
                       + "]")
        super().__init__(controller, button_text,
                         controller.show_all_messages, count=count,
                         prefix_character='',
                         width=width)


class PMButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("Private messages ["
                       + primary_key_for_command("ALL_PM")
                       + "]")
        super().__init__(controller, button_text,
                         controller.show_all_pm, count=count,
                         prefix_character='',
                         width=width)


class MentionedButton(TopButton):
    def __init__(self, controller: Any, width: int, count: int=0) -> None:
        button_text = ("Mentions         ["
                       + primary_key_for_command("ALL_MENTIONS")
                       + "]")
        super().__init__(controller, button_text,
                         controller.show_all_mentions,
                         width=width,
                         count=count,
                         prefix_character='')


class StarredButton(TopButton):
    def __init__(self, controller: Any, width: int) -> None:
        button_text = ("Starred messages ["
                       + primary_key_for_command("ALL_STARRED")
                       + "]")
        super().__init__(controller, button_text,
                         controller.show_all_starred,
                         width=width,
                         prefix_character='',
                         count=0)  # Starred messages are already marked read


class StreamButton(TopButton):
    def __init__(self, properties: StreamData,
                 controller: Any, view: Any, width: int,
                 count: int=0) -> None:
        # FIXME Is having self.stream_id the best way to do this?
        # (self.stream_id is used elsewhere)
        self.stream_name = properties['name']
        self.stream_id = properties['id']
        self.color = properties['color']
        is_private = properties['invite_only']
        self.description = properties['description']

        self.model = controller.model
        self.count = count
        self.view = view

        for entry in view.palette:
            if entry[0] is None:
                background = entry[5] if len(entry) > 4 else entry[2]
                inverse_text = background if background else 'black'
                break
        view.palette.append((
            self.color, '', '', 'bold', self.color + ', bold', background))
        view.palette.append((
            's' + self.color, '', '', 'standout', inverse_text, self.color))

        stream_marker = (STREAM_MARKER_PRIVATE if is_private
                         else STREAM_MARKER_PUBLIC)
        super().__init__(controller,
                         caption=self.stream_name,
                         show_function=controller.narrow_to_stream,
                         prefix_character=(self.color, stream_marker),
                         width=width,
                         count=count)

        # Mark muted streams 'M' during button creation.
        if self.model.is_muted_stream(self.stream_id):
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget(('muted', MUTE_MARKER), 'muted')
        self.view.home_button.update_count(
            self.model.unread_counts['all_msg'])

    def mark_unmuted(self, unread_count: int) -> None:
        self.update_count(unread_count)
        self.view.home_button.update_count(
            self.model.unread_counts['all_msg'])

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('TOGGLE_TOPIC', key):
            self.view.left_panel.show_topic_view(self)
        elif is_command_key('TOGGLE_MUTE_STREAM', key):
            self.controller.stream_muting_confirmation_popup(self)
        elif is_command_key('STREAM_DESC', key):
            self.model.controller.show_stream_info(self.stream_id)
        return super().keypress(size, key)


class UserButton(TopButton):
    def __init__(self, user: Dict[str, Any], controller: Any,
                 view: Any, width: int,
                 state_marker: str,
                 color: Optional[str]=None, count: int=0,
                 is_current_user: bool=False) -> None:
        # Properties accessed externally
        self.email = user['email']
        self.user_id = user['user_id']

        self._view = view  # Used in _narrow_with_compose

        # FIXME Is this still needed?
        self.recipients = frozenset({self.user_id, view.model.user_id})

        super().__init__(controller,
                         caption=user['full_name'],
                         show_function=self._narrow_with_compose,
                         prefix_character=(color, state_marker),
                         text_color=color,
                         width=width,
                         count=count)
        if is_current_user:
            self.update_widget(('current_user', '(you)'), color)

    def _narrow_with_compose(self, button: Any) -> None:
        # Switches directly to composing with user
        # FIXME should we just narrow?
        self.controller.narrow_to_user(self)
        self._view.body.focus.original_widget.set_focus('footer')
        self._view.write_box.private_box_view(
            email=self.email,
            recipient_user_ids=[self.user_id]
        )


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

        if controller.model.is_muted_topic(self.stream_id, self.topic_name):
            self.mark_muted()

    def mark_muted(self) -> None:
        self.update_widget(('muted',  MUTE_MARKER), 'muted')
    # TODO: Handle event-based approach for topic-muting.


class UnreadPMButton(urwid.Button):
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email


DecodedStream = TypedDict('DecodedStream', {
    'stream_id': Optional[int],
    'stream_name': Optional[str],
})

ParsedNarrowLink = TypedDict('ParsedNarrowLink', {
    'narrow': str,
    'stream': DecodedStream,
    'topic_name': str,
    'message_id': Optional[int],
}, total=False)


class MessageLinkButton(urwid.Button):
    def __init__(self, controller: Any, caption: str, link: str,
                 display_attr: Optional[str]) -> None:
        self.controller = controller
        self.model = self.controller.model
        self.view = self.controller.view
        self.link = link

        super().__init__('')
        self.update_widget(caption, display_attr)
        urwid.connect_signal(self, 'click', callback=self.handle_link)

    def update_widget(self, caption: str,
                      display_attr: Optional[str]=None) -> None:
        """
        Overrides the existing button widget for custom styling.
        """
        # Set cursor position next to len(caption) to avoid the cursor.
        icon = urwid.SelectableIcon(caption, cursor_position=len(caption) + 1)
        self._w = urwid.AttrMap(icon, display_attr, focus_map='selected')

    def handle_link(self, *_: Any) -> None:
        """
        Classifies and handles link.
        """
        server_url = self.model.server_url
        if self.link.startswith(urljoin(server_url, '/#narrow/')):
            self.handle_narrow_link()

    @staticmethod
    def _decode_stream_data(encoded_stream_data: str) -> DecodedStream:
        """
        Returns a dict with optional stream ID and stream name.
        """
        # Modern links come patched with the stream ID and '-' as delimiters.
        if re.match('^[0-9]+-', encoded_stream_data):
            stream_id, *_ = encoded_stream_data.split('-')
            # Given how encode_stream() in zerver/lib/url_encoding.py
            # replaces ' ' with '-' in the stream name, skip extracting the
            # stream name to avoid any ambiguity.
            return DecodedStream(stream_id=int(stream_id), stream_name=None)
        else:
            # Deprecated links did not start with the stream ID.
            stream_name = hash_util_decode(encoded_stream_data)
            return DecodedStream(stream_id=None, stream_name=stream_name)

    @staticmethod
    def _decode_message_id(message_id: str) -> Optional[int]:
        """
        Returns either the compatible near message ID or None.
        """
        try:
            return int(message_id)
        except ValueError:
            return None

    @classmethod
    def _parse_narrow_link(cls, link: str) -> ParsedNarrowLink:
        """
        Returns either a dict with narrow parameters for supported links or an
        empty dict.
        """
        # NOTE: The optional stream_id link version is deprecated. The extended
        # support is for old messages.
        # We expect the fragment to be one of the following types:
        # a. narrow/stream/[{stream_id}-]{stream-name}
        # b. narrow/stream/[{stream_id}-]{stream-name}/near/{message_id}
        # c. narrow/stream/[{stream_id}-]{stream-name}/topic/
        #    {encoded.20topic.20name}
        # d. narrow/stream/[{stream_id}-]{stream-name}/topic/
        #    {encoded.20topic.20name}/near/{message_id}
        fragments = urlparse(link.rstrip('/')).fragment.split('/')
        len_fragments = len(fragments)
        parsed_link = ParsedNarrowLink()

        if len_fragments == 3 and fragments[1] == 'stream':
            stream_data = cls._decode_stream_data(fragments[2])
            parsed_link = dict(narrow='stream', stream=stream_data)

        elif (len_fragments == 5 and fragments[1] == 'stream'
                and fragments[3] == 'topic'):
            stream_data = cls._decode_stream_data(fragments[2])
            topic_name = hash_util_decode(fragments[4])
            parsed_link = dict(narrow='stream:topic', stream=stream_data,
                               topic_name=topic_name)

        elif (len_fragments == 5 and fragments[1] == 'stream'
                and fragments[3] == 'near'):
            stream_data = cls._decode_stream_data(fragments[2])
            message_id = cls._decode_message_id(fragments[4])
            parsed_link = dict(narrow='stream:near', stream=stream_data,
                               message_id=message_id)

        elif (len_fragments == 7 and fragments[1] == 'stream'
                and fragments[3] == 'topic' and fragments[5] == 'near'):
            stream_data = cls._decode_stream_data(fragments[2])
            topic_name = hash_util_decode(fragments[4])
            message_id = cls._decode_message_id(fragments[6])
            parsed_link = dict(narrow='stream:topic:near', stream=stream_data,
                               topic_name=topic_name, message_id=message_id)

        return parsed_link

    def _validate_and_patch_stream_data(self,
                                        parsed_link: ParsedNarrowLink) -> str:
        """
        Validates stream data and patches the optional value in the nested
        DecodedStream dict.
        """
        stream_id = parsed_link['stream']['stream_id']
        stream_name = parsed_link['stream']['stream_name']
        assert (
            (stream_id is None and stream_name is not None)
            or (stream_id is not None and stream_name is None)
        )

        model = self.model
        # Validate stream ID and name.
        if ((stream_id and not model.is_user_subscribed_to_stream(stream_id))
                or (stream_name and not model.is_valid_stream(stream_name))):
            # TODO: Narrow to the concerned stream in a 'preview' mode or
            # report whether the stream id is invalid instead.
            return 'The stream seems to be either unknown or unsubscribed'

        # Patch the optional value.
        if not stream_id:
            stream_id = cast(int, model.stream_id_from_name(stream_name))
            parsed_link['stream']['stream_id'] = stream_id
        else:
            stream_name = cast(str, model.stream_dict[stream_id]['name'])
            parsed_link['stream']['stream_name'] = stream_name

        return ''

    def _validate_narrow_link(self, parsed_link: ParsedNarrowLink) -> str:
        """
        Returns either an empty string for a successful validation or an
        appropriate validation error.
        """
        if not parsed_link:
            return 'The narrow link seems to be either broken or unsupported'

        # Validate stream data.
        if 'stream' in parsed_link:
            error = self._validate_and_patch_stream_data(parsed_link)
            if error:
                return error

        # Validate topic name.
        if 'topic_name' in parsed_link:
            topic_name = parsed_link['topic_name']
            stream_id = parsed_link['stream']['stream_id']

            if topic_name not in self.model.topics_in_stream(stream_id):
                return 'Invalid topic name'

        # Validate message ID for near.
        if 'near' in parsed_link['narrow']:
            message_id = parsed_link.get('message_id')

            if message_id is None:
                return 'Invalid message ID'

        return ''

    def _switch_narrow_to(self, parsed_link: ParsedNarrowLink) -> None:
        """
        Switches narrow via narrow_to_* methods.
        """
        narrow = parsed_link['narrow']
        if 'stream' == narrow:
            self.stream_id = parsed_link['stream']['stream_id']
            self.stream_name = parsed_link['stream']['stream_name']
            self.controller.narrow_to_stream(self)
        elif 'stream:near' == narrow:
            self.stream_id = parsed_link['stream']['stream_id']
            self.stream_name = parsed_link['stream']['stream_name']
            self.message = dict(id=parsed_link['message_id'])
            self.controller.narrow_to_stream(self)
        elif 'stream:topic' == narrow:
            self.stream_id = parsed_link['stream']['stream_id']
            self.stream_name = parsed_link['stream']['stream_name']
            self.topic_name = parsed_link['topic_name']
            self.controller.narrow_to_topic(self)
        elif 'stream:topic:near' == narrow:
            self.stream_id = parsed_link['stream']['stream_id']
            self.stream_name = parsed_link['stream']['stream_name']
            self.topic_name = parsed_link['topic_name']
            self.message = dict(id=parsed_link['message_id'])
            self.controller.narrow_to_topic(self)

    def handle_narrow_link(self) -> None:
        """
        Narrows to the respective narrow if the narrow link is valid or updates
        the footer with an appropriate validation error message.
        """
        parsed_link = self._parse_narrow_link(self.link)
        error = self._validate_narrow_link(parsed_link)

        if error:
            self.view.set_footer_text(' {}'.format(error), duration=3)
        else:
            self._switch_narrow_to(parsed_link)

            # Exit pop-up if MessageLinkButton exists in one.
            if isinstance(self.controller.loop.widget, urwid.Overlay):
                self.controller.exit_popup()


class EditModeButton(urwid.Button):
    def __init__(self, controller: Any, width: int) -> None:
        self.controller = controller
        self.width = width
        super().__init__(label="",
                         on_press=controller.show_topic_edit_mode)
        self.set_selected_mode('change_later')  # set default mode

    def set_selected_mode(self, mode: str) -> None:
        self.mode = mode
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            edit_mode_captions[self.mode], self.width), None, 'selected')
