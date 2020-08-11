import re
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from sys import platform
from time import ctime, time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import dateutil.parser
import urwid
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from tzlocal import get_localzone
from urwid_readline import ReadlineEdit

from zulipterminal import emoji_names
from zulipterminal.config.keys import is_command_key, keys_for_command
from zulipterminal.config.symbols import (
    MESSAGE_CONTENT_MARKER, MESSAGE_HEADER_DIVIDER, QUOTED_TEXT_MARKER,
    STREAM_TOPIC_SEPARATOR, TIME_MENTION_MARKER,
)
from zulipterminal.helper import (
    Message, format_string, match_emoji, match_group, match_stream, match_user,
)
from zulipterminal.ui_tools.tables import render_table
from zulipterminal.urwid_types import urwid_Size


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super().__init__(self.main_view(True))
        self.model = view.model
        self.view = view
        self.msg_edit_id = None  # type: Optional[int]
        self.is_in_typeahead_mode = False
        self.recipient_user_ids = []  # type: List[int]

    def main_view(self, new: bool) -> Any:
        if new:
            return []
        else:
            self.contents.clear()

    def set_editor_mode(self) -> None:
        self.view.controller.enter_editor_mode_with(self)

    def private_box_view(self, button: Any=None, email: str='',
                         recipient_user_ids: Optional[List[int]]=None) -> None:
        self.set_editor_mode()
        if recipient_user_ids:
            self.recipient_user_ids = recipient_user_ids
        if email == '' and button is not None:
            email = button.email
        self.to_write_box = ReadlineEdit("To: ", edit_text=email)
        self.msg_write_box = ReadlineEdit(multiline=True)
        self.msg_write_box.enable_autocomplete(
            func=self.generic_autocomplete,
            key=keys_for_command('AUTOCOMPLETE').pop(),
            key_reverse=keys_for_command('AUTOCOMPLETE_REVERSE').pop()
        )
        to_write_box = urwid.LineBox(
            self.to_write_box, tlcorner='─', tline='─', lline='',
            trcorner='─', blcorner='─', rline='',
            bline='─', brcorner='─'
        )
        self.contents = [
            (to_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.focus_position = 1

    def stream_box_view(self, stream_id: int, caption: str='', title: str='',
                        ) -> None:
        self.set_editor_mode()
        self.recipient_user_ids = self.model.get_other_subscribers_in_stream(
                                            stream_id=stream_id)
        self.to_write_box = None
        self.msg_write_box = ReadlineEdit(multiline=True)
        self.msg_write_box.enable_autocomplete(
            func=self.generic_autocomplete,
            key=keys_for_command('AUTOCOMPLETE').pop(),
            key_reverse=keys_for_command('AUTOCOMPLETE_REVERSE').pop()
        )
        self.stream_write_box = ReadlineEdit(
            caption="Stream:  ",
            edit_text=caption
        )
        self.title_write_box = ReadlineEdit(caption="Topic:  ",
                                            edit_text=title)

        header_write_box = urwid.Columns([
            urwid.LineBox(
                self.stream_write_box, tlcorner='─', tline='─', lline='',
                trcorner='┬', blcorner='─', rline='│',
                bline='─', brcorner='┴'
            ),
            urwid.LineBox(
                self.title_write_box, tlcorner='─', tline='─', lline='',
                trcorner='─', blcorner='─', rline='',
                bline='─', brcorner='─'
            ),
        ])
        write_box = [
            (header_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def generic_autocomplete(self, text: str, state: Optional[int]
                             ) -> Optional[str]:
        num_suggestions = 10
        autocomplete_map = OrderedDict([
                ('@_', self.autocomplete_mentions),
                ('@', self.autocomplete_mentions),
                ('#', self.autocomplete_streams),
                (':', self.autocomplete_emojis),
            ])

        # Look in a reverse order to find the last autocomplete prefix used in
        # the text. For instance, if text='@#example', use '#' as the prefix.
        reversed_text = text[::-1]
        for reverse_index, char in enumerate(reversed_text):
            # Patch for silent mentions.
            if (char == '_' and reverse_index + 1 < len(reversed_text)
                    and reversed_text[reverse_index + 1] == '@'):
                char = '@_'

            if char in autocomplete_map:
                prefix = char
                autocomplete_func = autocomplete_map[prefix]
                prefix_index = max(text.rfind(prefix), 0)
                break
        else:
            # Return text if it doesn't have any of the autocomplete prefixes.
            return text

        # NOTE: The following block only executes if any of the autocomplete
        # prefixes exist.
        self.is_in_typeahead_mode = True
        typeaheads, suggestions = (
            autocomplete_func(text[prefix_index:], prefix)
        )
        fewer_typeaheads = typeaheads[:num_suggestions]
        reduced_suggestions = suggestions[:num_suggestions]
        is_truncated = len(fewer_typeaheads) != len(typeaheads)

        if (state is not None and state < len(fewer_typeaheads)
                and state >= -len(fewer_typeaheads)):
            typeahead = fewer_typeaheads[state]  # type: Optional[str]
            if typeahead:
                typeahead = text[:prefix_index] + typeahead
        else:
            typeahead = None
            state = None
        self.view.set_typeahead_footer(reduced_suggestions,
                                       state, is_truncated)
        return typeahead

    def autocomplete_mentions(self, text: str, prefix_string: str
                              ) -> Tuple[List[str], List[str]]:
        # Handles user mentions (@ mentions and silent mentions)
        # and group mentions.
        groups = [group_name
                  for group_name in self.model.user_group_names
                  if match_group(group_name, text[1:])]
        group_typeahead = format_string(groups, '@*{}*')

        users_list = self.view.users
        matching_users = [user
                          for user in users_list
                          if match_user(user, text[len(prefix_string):])]
        matching_ids = set([user['user_id'] for user in matching_users])
        matching_recipient_ids = (set(self.recipient_user_ids)
                                  & set(matching_ids))
        # Display subscribed users/recipients first.
        sorted_matching_users = sorted(matching_users,
                                       key=lambda user: user['user_id']
                                       in matching_recipient_ids,
                                       reverse=True)

        user_names = [user['full_name'] for user in sorted_matching_users]
        user_typeahead = format_string(user_names, prefix_string + '**{}**')

        combined_typeahead = user_typeahead + group_typeahead
        combined_names = user_names + groups

        return combined_typeahead, combined_names

    def autocomplete_streams(self, text: str, prefix_string: str
                             ) -> Tuple[List[str], List[str]]:
        streams_list = self.view.pinned_streams + self.view.unpinned_streams
        streams = [stream[0]
                   for stream in streams_list]
        stream_typeahead = format_string(streams, '#**{}**')
        stream_data = list(zip(stream_typeahead, streams))

        matched_data = match_stream(stream_data, text[1:],
                                    self.view.pinned_streams)
        return matched_data

    def autocomplete_emojis(self, text: str, prefix_string: str
                            ) -> Tuple[List[str], List[str]]:
        emoji_list = emoji_names.EMOJI_NAMES
        emojis = [emoji
                  for emoji in emoji_list
                  if match_emoji(emoji, text[1:])]
        emoji_typeahead = format_string(emojis, ':{}:')

        return emoji_typeahead, emojis

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if self.is_in_typeahead_mode:
            if not (is_command_key('AUTOCOMPLETE', key)
                    or is_command_key('AUTOCOMPLETE_REVERSE', key)):
                # set default footer when done with autocomplete
                self.is_in_typeahead_mode = False
                self.view.set_footer_text()

        if is_command_key('SEND_MESSAGE', key):
            if not self.to_write_box:
                if re.fullmatch(r'\s*', self.title_write_box.edit_text):
                    topic = '(no topic)'
                else:
                    topic = self.title_write_box.edit_text

                if self.msg_edit_id:
                    success = self.model.update_stream_message(
                        topic=topic,
                        content=self.msg_write_box.edit_text,
                        msg_id=self.msg_edit_id,
                    )
                else:
                    success = self.model.send_stream_message(
                        stream=self.stream_write_box.edit_text,
                        topic=topic,
                        content=self.msg_write_box.edit_text
                    )
            else:
                if self.msg_edit_id:
                    success = self.model.update_private_message(
                        content=self.msg_write_box.edit_text,
                        msg_id=self.msg_edit_id,
                    )
                else:
                    success = self.model.send_private_message(
                        recipients=self.to_write_box.edit_text,
                        content=self.msg_write_box.edit_text
                    )
            if success:
                self.msg_write_box.edit_text = ''
                if self.msg_edit_id:
                    self.msg_edit_id = None
                    self.keypress(size, 'esc')
        elif is_command_key('GO_BACK', key):
            self.msg_edit_id = None
            self.view.controller.exit_editor_mode()
            self.main_view(False)
            self.view.middle_column.set_focus('body')
        elif is_command_key('TAB', key):
            if len(self.contents) == 0:
                return key
            header = self.contents[0][0]
            # toggle focus position
            if self.focus_position == 0:
                if self.to_write_box is None:
                    if header.focus_col == 0:
                        stream_name = header[0].edit_text
                        if not self.model.is_valid_stream(stream_name):
                            self.view.set_footer_text("Invalid stream name", 3)
                            return key
                        user_ids = self.model.get_other_subscribers_in_stream(
                                                    stream_name=stream_name)
                        self.recipient_user_ids = user_ids

                        header.focus_col = 1
                        return key
                    else:
                        header.focus_col = 0
                else:
                    recipient_box = header.original_widget
                    recipient_emails = [email.strip() for email in
                                        recipient_box.edit_text.split(',')]
                    invalid_emails = self.model.get_invalid_recipient_emails(
                                                              recipient_emails)
                    if invalid_emails:
                        invalid_emails_error = ('Invalid recipient(s) - '
                                                + ', '.join(invalid_emails))
                        self.view.set_footer_text(invalid_emails_error, 3)
                        return key
                    users = self.model.user_dict
                    self.recipient_user_ids = [users[email]['user_id']
                                               for email in recipient_emails]

            self.focus_position = self.focus_position == 0
            header.focus_col = 0

        key = super().keypress(size, key)
        return key


class MessageBox(urwid.Pile):
    # type of last_message is Optional[Message], but needs refactoring
    def __init__(self, message: Message, model: Any,
                 last_message: Any) -> None:
        self.model = model
        self.message = message
        self.stream_name = ''
        self.stream_id = None  # type: Union[int, None]
        self.topic_name = ''
        self.email = ''
        self.user_id = None  # type: Union[int, None]
        self.message_links = (
            OrderedDict()
        )   # type: OrderedDict[str, Tuple[str, int, bool]]
        self.last_message = last_message
        # if this is the first message
        if self.last_message is None:
            self.last_message = defaultdict(dict)

        if self.message['type'] == 'stream':
            self.stream_name = self.message['display_recipient']
            self.stream_id = self.message['stream_id']
            self.topic_name = self.message['subject']
        elif self.message['type'] == 'private':
            self.email = self.message['sender_email']
            self.user_id = self.message['sender_id']
        else:
            raise RuntimeError("Invalid message type")

        if self.message['type'] == 'private':
            if self._is_private_message_to_self():
                recipient = self.message['display_recipient'][0]
                self.recipients_names = recipient['full_name']
                self.recipients_emails = self.model.user_email
                self.recipient_ids = self.model.user_id
            else:
                self.recipients_names = ', '.join(list(
                            recipient['full_name']
                            for recipient in self.message['display_recipient']
                            if recipient['email'] != self.model.user_email
                        ))
                self.recipients_emails = ', '.join(list(
                            recipient['email']
                            for recipient in self.message['display_recipient']
                            if recipient['email'] != self.model.user_email
                        ))
                self.recipient_ids = [recipient['id'] for recipient
                                      in self.message['display_recipient']
                                      if recipient['id'] != self.model.user_id]

        # mouse_event helper variable
        self.displaying_selection_hint = False

        super().__init__(self.main_view())

    def _time_for_message(self, message: Message) -> str:
        return ctime(message['timestamp'])[:-8]

    def need_recipient_header(self) -> bool:
        # Prevent redundant information in recipient bar
        if (len(self.model.narrow) == 1
                and self.model.narrow[0][0] == 'pm_with'):
            return False
        if (len(self.model.narrow) == 2
                and self.model.narrow[1][0] == 'topic'):
            return False

        last_msg = self.last_message
        if self.message['type'] == 'stream':
            return not (
                last_msg['type'] == 'stream'
                and self.topic_name == last_msg['subject']
                and self.stream_name == last_msg['display_recipient']
            )
        elif self.message['type'] == 'private':
            recipient_ids = [{recipient['id']
                              for recipient in message['display_recipient']
                              if 'id' in recipient}
                             for message in (self.message, last_msg)
                             if 'display_recipient' in message]
            return not (
                len(recipient_ids) == 2
                and recipient_ids[0] == recipient_ids[1]
                and last_msg['type'] == 'private'
            )
        else:
            raise RuntimeError("Invalid message type")

    def _is_private_message_to_self(self) -> bool:
        recipient_list = self.message['display_recipient']
        return (len(recipient_list) == 1
                and recipient_list[0]['email'] == self.model.user_email)

    def stream_header(self) -> Any:
        color = self.model.stream_dict[self.stream_id]['color']
        bar_color = 's' + color
        stream_title_markup = ('bar', [
            (bar_color, '{} {} '.format(self.stream_name,
                                        STREAM_TOPIC_SEPARATOR)),
            ('title', ' {}'.format(self.topic_name))
        ])
        stream_title = urwid.Text(stream_title_markup)
        header = urwid.Columns([
            ('pack', stream_title),
            (1, urwid.Text((color, ' '))),
            urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER),
                           color),
        ])
        header.markup = stream_title_markup
        return header

    def private_header(self) -> Any:
        title_markup = ('header', [
            ('general_narrow', 'You and '),
            ('general_narrow', self.recipients_names)
        ])
        title = urwid.Text(title_markup)
        header = urwid.Columns([
            ('pack', title),
            (1, urwid.Text(('general_bar', ' '))),
            urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER),
                           'general_bar'),
        ])
        header.markup = title_markup
        return header

    def top_header_bar(self, message_view: Any) -> Any:
        if self.message['type'] == 'stream':
            return message_view.stream_header()
        else:
            return message_view.private_header()

    def top_search_bar(self) -> Any:
        curr_narrow = self.model.narrow
        is_search_narrow = self.model.is_search_narrow()
        if is_search_narrow:
            curr_narrow = [sub_narrow for sub_narrow in curr_narrow
                           if sub_narrow[0] != 'search']
        else:
            self.model.controller.view.search_box.text_box.set_edit_text("")
        if curr_narrow == []:
            text_to_fill = 'All messages'
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == 'private':
            text_to_fill = 'All private messages'
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == 'starred':
            text_to_fill = 'Starred messages'
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == 'mentioned':
            text_to_fill = 'Mentions'
        elif self.message['type'] == 'stream':
            bar_color = self.model.stream_dict[self.stream_id]['color']
            bar_color = 's' + bar_color
            if len(curr_narrow) == 2 and curr_narrow[1][0] == 'topic':
                text_to_fill = ('bar', [  # type: ignore
                    (bar_color, '{}'.format(self.stream_name)),
                    (bar_color, ': topic narrow')
                ])
            else:
                text_to_fill = ('bar', [  # type: ignore
                    (bar_color, '{}'.format(self.stream_name))
                ])
        elif len(curr_narrow) == 1 and len(curr_narrow[0][1].split(",")) > 1:
            text_to_fill = 'Group private conversation'
        else:
            text_to_fill = 'Private conversation'

        if is_search_narrow:
            title_markup = ('header', [
                ('general_narrow', text_to_fill),
                (None, ' '),
                ('filter_results', 'Search Results')
            ])
        else:
            title_markup = ('header', [
                ('general_narrow', text_to_fill)
            ])
        title = urwid.Text(title_markup)
        header = urwid.AttrWrap(title, 'bar')
        header.text_to_fill = text_to_fill
        header.markup = title_markup
        return header

    def reactions_view(self, reactions: List[Dict[str, Any]]) -> Any:
        if not reactions:
            return ''
        try:
            reaction_stats = defaultdict(set)
            for reaction in reactions:
                user_id = int(reaction['user'].get('id', -1))
                if user_id == -1:
                    user_id = int(reaction['user']['user_id'])
                reaction_stats[reaction['emoji_name']].add(user_id)

            sorted_stats = sorted(
                (reaction, count)
                for reaction, count in reaction_stats.items()
            )

            my_user_id = self.model.user_id
            reaction_texts = [
                ('reaction_mine' if my_user_id in ids else 'reaction',
                 ':{}: {}'.format(reaction, len(ids)))
                for reaction, ids in sorted_stats
            ]

            spaced_reaction_texts = [
                entry
                for pair in zip(reaction_texts,
                                ' ' * len(reaction_texts))
                for entry in pair
            ]
            return urwid.Padding(
                urwid.Text(spaced_reaction_texts),
                align='left', width=('relative', 90), left=25, min_width=50)
        except Exception:
            return ''

    # Use quotes as a workaround for OrderedDict typing issue.
    # See https://github.com/python/mypy/issues/6904.
    def footlinks_view(
        self, message_links: 'OrderedDict[str, Tuple[str, int, bool]]',
    ) -> Any:
        # Return if footlinks are disabled by the user.
        if not self.model.controller.footlinks_enabled:
            return None

        footlinks = []
        for link, (text, index, show_footlink) in message_links.items():
            if not show_footlink:
                continue

            footlinks.extend([
                ('msg_link_index', '{}:'.format(index)),
                ' ',
                ('msg_link', link),
                '\n',
            ])

        if not footlinks:
            return None

        footlinks[-1] = footlinks[-1][:-1]  # Remove the last newline.
        return urwid.Padding(urwid.Text(footlinks, wrap='ellipsis'),
                             align='left', left=8, width=('relative', 100),
                             min_width=10, right=2)

    def soup2markup(self, soup: Any, **state: Any) -> List[Any]:
        # Ensure a string is provided, in case the soup finds none
        # This could occur if eg. an image is removed or not shown
        markup = ['']  # type: List[Union[str, Tuple[Optional[str], Any]]]
        if soup is None:  # This is not iterable, so return promptly
            return markup
        unrendered_tags = {  # In pairs of 'tag_name': 'text'
            # TODO: Some of these could be implemented
            'br': '',  # No indicator of absence
            'hr': 'RULER',
            'img': 'IMAGE',
        }
        unrendered_div_classes = {  # In pairs of 'div_class': 'text'
            # TODO: Support embedded content & twitter preview?
            'message_embed': 'EMBEDDED CONTENT',
            'inline-preview-twitter': 'TWITTER PREVIEW',
            'message_inline_ref': '',  # Duplicate of other content
            'message_inline_image': '',  # Duplicate of other content
        }
        unrendered_template = '[{} NOT RENDERED]'
        for element in soup:
            if isinstance(element, NavigableString):
                # NORMAL STRINGS
                if (hasattr(self, 'bq_len') and element == '\n'
                        and self.bq_len > 0):
                    self.bq_len -= 1
                    continue
                markup.append(element)
            elif (element.name == 'div' and element.attrs
                  and any(cls in element.attrs.get('class', [])
                          for cls in unrendered_div_classes)):
                # UNRENDERED DIV CLASSES
                matching_class = (set(unrendered_div_classes)
                                  & set(element.attrs.get('class')))
                text = unrendered_div_classes[matching_class.pop()]
                if text:
                    markup.append(unrendered_template.format(text))
            elif (element.name == 'img'
                  and element.attrs.get('class', []) == ['emoji']):
                # CUSTOM EMOJIS AND ZULIP_EXTRA_EMOJI
                emoji_name = element.attrs.get('title', [])
                markup.append(('msg_emoji', ":" + emoji_name + ":"))
            elif element.name in unrendered_tags:
                # UNRENDERED SIMPLE TAGS
                text = unrendered_tags[element.name]
                if text:
                    markup.append(unrendered_template.format(text))
            elif element.name in ('p', 'del'):
                # PARAGRAPH, STRIKE-THROUGH
                markup.extend(self.soup2markup(element))
            elif (element.name == 'span' and element.attrs
                  and 'emoji' in element.attrs.get('class', [])):
                # EMOJI
                markup.append(('msg_emoji', element.text))
            elif (element.name == 'span' and element.attrs
                  and ('katex-display' in element.attrs.get('class', [])
                       or 'katex' in element.attrs.get('class', []))):
                # MATH TEXT
                markup.append(element.text)
            elif (element.name == 'span' and element.attrs
                  and ('user-group-mention' in element.attrs.get('class', [])
                       or 'user-mention' in element.attrs.get('class', []))):
                # USER MENTIONS & USER-GROUP MENTIONS
                markup.append(('msg_mention', element.text))
            elif element.name == 'a':
                # LINKS
                # Use rstrip to avoid anomalies and edge cases like
                # https://google.com vs https://google.com/.
                link = element.attrs['href'].rstrip('/')
                text = element.img['src'] if element.img else element.text
                text = text.rstrip('/')

                parsed_link = urlparse(link)
                if not parsed_link.scheme:  # => relative link
                    # Prepend org url to convert it to an absolute link
                    link = urljoin(self.model.server_url, link)

                text = text if text else link

                show_footlink = True
                # Only use the last segment if the text is redundant.
                # NOTE: The 'without scheme' excerpt is to deal with the case
                # where a user puts a link without any scheme and the server
                # uses http as the default scheme but keeps the text as-is.
                # For instance, see how example.com/some/path becomes
                # <a href="http://example.com">example.com/some/path</a>.
                link_without_scheme, text_without_scheme = [
                    data.split('://')[1] if '://' in data else data
                    for data in [link, text]
                ]   # Split on '://' is for cases where text == link.
                if link_without_scheme == text_without_scheme:
                    last_segment = text.split('/')[-1]
                    if '.' in last_segment:
                        new_text = last_segment  # Filename.
                    elif text.startswith(self.model.server_url):
                        # Relative URL.
                        new_text = text.split(self.model.server_url)[-1]
                    else:
                        new_text = (
                            parsed_link.netloc if parsed_link.netloc
                            else text.split('/')[0]
                        )  # Domain name.
                    if new_text != text_without_scheme:
                        text = new_text
                    else:
                        # Do not show as a footlink as the text is sufficient
                        # to represent the link.
                        show_footlink = False

                # Detect duplicate links to save screen real estate.
                if link not in self.message_links:
                    self.message_links[link] = (
                        text, len(self.message_links) + 1, show_footlink
                    )
                else:
                    # Append the text if its link already exist with a
                    # different text.
                    saved_text, saved_link_index, saved_footlink_status = (
                        self.message_links[link]
                    )
                    if saved_text != text:
                        self.message_links[link] = (
                            '{}, {}'.format(saved_text, text),
                            saved_link_index,
                            show_footlink or saved_footlink_status,
                        )

                markup.extend([
                    ('msg_link', text),
                    ' ',
                    ('msg_link_index',
                     '[{}]'.format(self.message_links[link][1])),
                ])
            elif element.name == 'blockquote':
                # BLOCKQUOTE TEXT
                markup.append((
                    'msg_quote', self.soup2markup(element)
                ))
            elif element.name == 'code':
                # CODE (INLINE?)
                markup.append((
                    'msg_code', element.text
                ))
            elif (element.name == 'div' and element.attrs
                    and 'codehilite' in element.attrs.get('class', [])):
                # CODE (BLOCK?)
                markup.append((
                    'msg_code', element.text
                ))
            elif element.name in ('strong', 'em'):
                # BOLD & ITALIC
                markup.append(('msg_bold', element.text))
            elif element.name in ('ul', 'ol'):
                # LISTS (UL & OL)
                for part in element.contents:
                    if part == '\n':
                        part.replace_with('')

                if 'indent_level' not in state:
                    state['indent_level'] = 1
                    state['list_start'] = True
                else:
                    state['indent_level'] += 1
                    state['list_start'] = False
                if element.name == 'ol':
                    start_number = int(element.attrs.get('start', 1))
                    state['list_index'] = start_number
                    markup.extend(self.soup2markup(element, **state))
                    del state['list_index']  # reset at end of this list
                else:
                    if 'list_index' in state:
                        del state['list_index']  # this is unordered
                    markup.extend(self.soup2markup(element, **state))
                del state['indent_level']  # reset indents after any list
            elif element.name == 'li':
                # LIST ITEMS (LI)
                for part in element.contents:
                    if part == '\n':
                        part.replace_with('')
                if not state.get('list_start', False):
                    markup.append('\n')

                indent = state.get('indent_level', 1)
                if 'list_index' in state:
                    markup.append('{}{}. '.format('  ' * indent,
                                                  state['list_index']))
                    state['list_index'] += 1
                else:
                    chars = [
                            '\N{BULLET}',
                            '\N{RING OPERATOR}',    # small hollow
                            '\N{HYPHEN}',
                    ]
                    markup.append('{}{} '.format('  ' * indent,
                                                 chars[(indent - 1) % 3]))
                state['list_start'] = False
                markup.extend(self.soup2markup(element, **state))
            elif element.name == 'table':
                markup.extend(render_table(element))
            elif element.name == 'time':
                # New in feature level 16, server version 3.0.
                # Render time in current user's local time zone.
                timestamp = element.get('datetime')

                # This should not happen. Regardless, we are interested in
                # debugging and reporting it to zulip/zulip if it does.
                assert timestamp is not None, 'Could not find datetime attr'

                utc_time = dateutil.parser.parse(timestamp)
                local_time = utc_time.astimezone(get_localzone())
                # TODO: Address 12-hour format support with application-wide
                # support for different formats.
                time_string = local_time.strftime('%a, %b %-d %Y, %-H:%M (%Z)')
                markup.append((
                    'msg_time',
                    ' {} {} '.format(TIME_MENTION_MARKER, time_string)
                ))
            else:
                markup.extend(self.soup2markup(element))
        return markup

    def main_view(self) -> List[Any]:

        # Recipient Header
        if self.need_recipient_header():
            if self.message['type'] == 'stream':
                recipient_header = self.stream_header()
            else:
                recipient_header = self.private_header()
        else:
            recipient_header = None

        # Content Header
        message = {
            key: {
                'is_starred': 'starred' in msg['flags'],
                'author': (msg['sender_full_name']
                           if 'sender_full_name' in msg else None),
                'time': (self._time_for_message(msg)
                         if 'timestamp' in msg else None),
                'datetime': (datetime.fromtimestamp(msg['timestamp'])
                             if 'timestamp' in msg else None),
            }
            for key, msg in dict(this=self.message,
                                 last=self.last_message).items()
        }
        different = {  # How this message differs from the previous one
            'recipients': recipient_header is not None,
            'author': message['this']['author'] != message['last']['author'],
            '24h': (message['last']['datetime'] is not None
                    and ((message['this']['datetime']
                          - message['last']['datetime'])
                         .days)),
            'timestamp': (
                message['last']['time'] is not None
                and message['this']['time'] != message['last']['time']
            ),
            'star_status': (
                message['this']['is_starred'] != message['last']['is_starred']
            ),
        }
        any_differences = any(different.values())

        if any_differences:  # Construct content_header, if needed
            TextType = Dict[str, Tuple[Optional[str], str]]
            text_keys = ('author', 'star', 'time')
            text = {key: (None, ' ') for key in text_keys}  # type: TextType

            if any(different[key] for key in ('recipients', 'author', '24h')):
                text['author'] = ('name', message['this']['author'])
            if message['this']['is_starred']:
                text['star'] = ('starred', "*")
            if any(different[key]
                   for key in ('recipients', 'author', 'timestamp')):
                this_year = date.today().year
                msg_year = message['this']['datetime'].year
                if this_year != msg_year:
                    text['time'] = (
                        'time',
                        '{} - {}'.format(msg_year, message['this']['time'])
                    )
                else:
                    text['time'] = ('time', message['this']['time'])

            content_header = urwid.Columns([
                ('weight', 10, urwid.Text(text['author'])),
                (23, urwid.Text(text['time'], align='right')),
                (1, urwid.Text(text['star'], align='right')),
                ], dividechars=1)
        else:
            content_header = None

        # If the message contains '/me' emote then replace it with
        # sender's full name and show it in bold.
        if self.message['is_me_message']:
            self.message['content'] = self.message['content'].replace(
                '/me',
                '<strong>' + self.message['sender_full_name'] + '</strong>', 1)

        # Transform raw message content into markup (As needed by urwid.Text)
        content = self.transform_content()

        if self.message['id'] in self.model.index['edited_messages']:
            edited_label_size = 7
            left_padding = 1
        else:
            edited_label_size = 0
            left_padding = 8

        content = urwid.Padding(
            urwid.Columns([
                (edited_label_size,
                 urwid.Text('EDITED')),
                urwid.LineBox(
                    urwid.Columns([
                        (1, urwid.Text('')),
                        urwid.Text(content),
                    ]), tline='', bline='', rline='',
                    lline=MESSAGE_CONTENT_MARKER
                )
            ]),
            align='left', left=left_padding,
            width=('relative', 100), min_width=10, right=5)

        # Reactions
        reactions = self.reactions_view(self.message['reactions'])

        # Footlinks.
        footlinks = self.footlinks_view(self.message_links)

        # Build parts together and return
        parts = [
            (recipient_header, recipient_header is not None),
            (content_header, any_differences),
            (content, True),
            (footlinks, footlinks is not None),
            (reactions, reactions != ''),
        ]
        return [part for part, condition in parts if condition]

    def transform_content(self) -> Tuple[None, Any]:
        soup = BeautifulSoup(self.message['content'], 'lxml')
        body = soup.find(name='body')
        if body and body.find(name='blockquote'):
            self.indent_quoted_content(soup, QUOTED_TEXT_MARKER)

        return (None, self.soup2markup(body))

    def indent_quoted_content(self, soup: Any, padding_char: str) -> None:
        """
        We indent quoted text by padding them.
        The extent of indentation depends on their level of quoting.
        For example:
        [Before Padding]               [After Padding]

        <blockquote>                    <blockquote>
        <blockquote>                    <blockquote>
        <p>Foo</p>                      <p>▒ ▒ </p><p>Foo</p>
        </blockquote>       --->        </blockquote>
        <p>Boo</p>                      <p>▒ </p><p>Boo</p>
        </blockquote>                   </blockquote>
        """
        pad_count = 1
        blockquote_list = soup.find_all('blockquote')
        self.bq_len = len(blockquote_list)
        for tag in blockquote_list:
            child_list = tag.findChildren(recursive=False)
            actual_padding = (padding_char + ' ') * pad_count
            if len(child_list) == 1:
                pad_count = 0
                child_iterator = child_list
            else:
                child_iterator = child_list[1:]
            for child in child_iterator:
                new_tag = soup.new_tag('p')
                new_tag.string = actual_padding
                # If the quoted message is multi-line message
                # we deconstruct it and pad it at break-points (<br/>)
                if child.findAll('br'):
                    for br in child.findAll('br'):
                        next_s = br.nextSibling
                        text = str(next_s).strip()
                        if text:
                            insert_tag = soup.new_tag('p')
                            insert_tag.string = '\n' + actual_padding + text
                            next_s.replace_with(insert_tag)
                child.insert_before(new_tag)
            pad_count += 1

    def selectable(self) -> bool:
        # Returning True, indicates that this widget
        # is designed to take focus.
        return True

    def mouse_event(self, size: urwid_Size, event: str, button: int,
                    col: int, row: int, focus: bool) -> bool:
        if event == 'mouse press':
            if button == 1:
                if self.model.controller.is_in_editor_mode():
                    return True
                self.keypress(size, keys_for_command('ENTER').pop())
                return True
        elif event == 'mouse drag':
            selection_key = "Fn + Alt" if platform == "darwin" else "Shift"
            self.model.controller.view.set_footer_text([
                'Try pressing ',
                ('code', ' ' + selection_key + ' '),
                ' and dragging to select text.'
            ])
            self.displaying_selection_hint = True
        elif event == 'mouse release' and self.displaying_selection_hint:
            self.model.controller.view.set_footer_text()
            self.displaying_selection_hint = False

        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key('ENTER', key):
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.recipients_emails,
                    recipient_user_ids=self.recipient_ids,
                )
            elif self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['display_recipient'],
                    title=self.message['subject'],
                    stream_id=self.stream_id,
                )
        elif is_command_key('STREAM_MESSAGE', key):
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.recipients_emails,
                    recipient_user_ids=self.recipient_ids,
                )
            elif self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['display_recipient'],
                    stream_id=self.stream_id,
                )
        elif is_command_key('STREAM_NARROW', key):
            if self.message['type'] == 'private':
                self.model.controller.narrow_to_user(self)
            elif self.message['type'] == 'stream':
                self.model.controller.narrow_to_stream(self)
        elif is_command_key('TOGGLE_NARROW', key):
            self.model.unset_search_narrow()
            if self.message['type'] == 'private':
                if (
                    len(self.model.narrow) == 1
                    and self.model.narrow[0][0] == 'pm_with'
                   ):
                    self.model.controller.show_all_pm(self)
                else:
                    self.model.controller.narrow_to_user(self)
            elif self.message['type'] == 'stream':
                if len(self.model.narrow) > 1:  # in a topic
                    self.model.controller.narrow_to_stream(self)
                else:
                    self.model.controller.narrow_to_topic(self)
        elif is_command_key('TOPIC_NARROW', key):
            if self.message['type'] == 'private':
                self.model.controller.narrow_to_user(self)
            elif self.message['type'] == 'stream':
                self.model.controller.narrow_to_topic(self)
        elif is_command_key('GO_BACK', key):
            self.model.controller.show_all_messages(self)
        elif is_command_key('REPLY_AUTHOR', key):
            # All subscribers from recipient_ids are not needed here.
            self.model.controller.view.write_box.private_box_view(
                email=self.message['sender_email'],
                recipient_user_ids=[self.message['sender_id']],
            )
        elif is_command_key('MENTION_REPLY', key):
            self.keypress(size, 'enter')
            mention = '@**' + self.message['sender_full_name'] + '** '
            self.model.controller.view.write_box.msg_write_box.set_edit_text(
                mention)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(
                len(mention))
            self.model.controller.view.middle_column.set_focus('footer')
        elif is_command_key('QUOTE_REPLY', key):
            self.keypress(size, 'enter')
            quote = '```quote\n' + self.model.client.get_raw_message(
                self.message['id'])['raw_content'] + '\n```\n'
            self.model.controller.view.write_box.msg_write_box.set_edit_text(
                quote)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(
                len(quote))
            self.model.controller.view.middle_column.set_focus('footer')
        elif is_command_key('EDIT_MESSAGE', key):
            if self.message['sender_id'] != self.model.user_id:
                self.model.controller.view.set_footer_text(
                        " You can't edit messages sent by other users.", 3)
                return key
            # Check if editing is allowed in the realm
            elif not self.model.initial_data['realm_allow_message_editing']:
                self.model.controller.view.set_footer_text(
                    " Editing sent message is disabled.", 3)
                return key
            # Check if message is still editable, i.e. within
            # the time limit.
            time_since_msg_sent = time() - self.message['timestamp']
            edit_time_limit = self.model.initial_data[
                    'realm_message_content_edit_limit_seconds']
            if time_since_msg_sent >= edit_time_limit:
                self.model.controller.view.set_footer_text(
                        " Time Limit for editing the message has"
                        " been exceeded.", 3)
                return key
            self.keypress(size, 'enter')
            msg_id = self.message['id']
            msg = self.model.client.get_raw_message(msg_id)['raw_content']
            write_box = self.model.controller.view.write_box
            write_box.msg_edit_id = msg_id
            write_box.msg_write_box.set_edit_text(msg)
            write_box.msg_write_box.set_edit_pos(len(msg))
            self.model.controller.view.middle_column.set_focus('footer')
        elif is_command_key('MSG_INFO', key):
            self.model.controller.show_msg_info(self.message,
                                                self.message_links)
        return key


class SearchBox(urwid.Pile):
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        super().__init__(self.main_view())

    def main_view(self) -> Any:
        search_text = ("Search ["
                       + ", ".join(keys_for_command("SEARCH_MESSAGES"))
                       + "]: ")
        self.text_box = ReadlineEdit(search_text + " ")
        # Add some text so that when packing,
        # urwid doesn't hide the widget.
        self.conversation_focus = urwid.Text(" ")
        self.search_bar = urwid.Columns([
            ('pack', self.conversation_focus),
            ('pack', urwid.Text("  ")),
            self.text_box,
        ])
        self.msg_narrow = urwid.Text("DONT HIDE")
        self.recipient_bar = urwid.LineBox(
            self.msg_narrow, title="Current message recipients",
            tline='─', lline='', trcorner='─', tlcorner='─',
            blcorner='─', rline='', bline='─', brcorner='─')
        return [self.search_bar, self.recipient_bar]

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if ((is_command_key('ENTER', key) and self.text_box.edit_text == '')
                or is_command_key('GO_BACK', key)):
            self.text_box.set_edit_text("")
            self.controller.exit_editor_mode()
            self.controller.view.middle_column.set_focus('body')
            return key

        elif is_command_key('ENTER', key):
            self.controller.exit_editor_mode()
            self.controller.search_messages(self.text_box.edit_text)
            self.controller.view.middle_column.set_focus('body')
            return key

        key = super().keypress(size, key)
        return key


class PanelSearchBox(urwid.Edit):
    """
    Search Box to search panel views in real-time.
    """
    def __init__(self, panel_view: Any, search_command: str,
                 update_function: Callable[..., None]) -> None:
        self.panel_view = panel_view
        self.search_command = search_command
        self.search_text = ("Search ["
                            + ", ".join(keys_for_command(search_command))
                            + "]: ")
        urwid.connect_signal(self, 'change', update_function)
        super().__init__(caption='', edit_text=self.search_text)

    def reset_search_text(self) -> None:
        self.set_caption('')
        self.set_edit_text(self.search_text)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if ((is_command_key('ENTER', key) and self.get_edit_text() == '')
                or is_command_key('GO_BACK', key)):
            self.panel_view.view.controller.exit_editor_mode()
            self.reset_search_text()
            self.panel_view.set_focus("body")
            self.panel_view.keypress(size, 'esc')
        elif is_command_key('ENTER', key):
            self.panel_view.view.controller.exit_editor_mode()
            self.set_caption([('filter_results', 'Search Results'), ' '])
            self.panel_view.set_focus("body")
            if hasattr(self.panel_view, 'log') and len(self.panel_view.log):
                self.panel_view.body.set_focus(0)
        return super().keypress(size, key)
