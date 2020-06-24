from collections import defaultdict
from time import ctime, time
from datetime import datetime
from sys import platform
from typing import Any, Dict, List, Tuple, Union, Optional

import emoji
import urwid
from urwid_readline import ReadlineEdit
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from zulipterminal.config.keys import is_command_key


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super(WriteBox, self).__init__(self.main_view(True))
        self.model = view.model
        self.view = view
        self.msg_edit_id = None  # type: Optional[int]

    def main_view(self, new: bool) -> Any:
        if new:
            return []
        else:
            self.contents.clear()

    def set_editor_mode(self) -> None:
        # if not in the editor mode already set editor_mode to True.
        if not self.view.controller.editor_mode:
            self.view.controller.editor_mode = True
            self.view.controller.editor = self

    def private_box_view(self, button: Any=None, email: str='') -> None:
        self.set_editor_mode()
        if email == '' and button is not None:
            email = button.email
        self.to_write_box = ReadlineEdit(u"To: ", edit_text=email)
        self.msg_write_box = ReadlineEdit(multiline=True)
        to_write_box = urwid.LineBox(
            self.to_write_box, tlcorner=u'─', tline=u'─', lline=u'',
            trcorner=u'─', blcorner=u'─', rline=u'',
            bline=u'─', brcorner=u'─'
        )
        self.contents = [
            (to_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.focus_position = 1

    def stream_box_view(self, button: Any=None, caption: str='',
                        title: str='') -> None:
        self.set_editor_mode()
        self.to_write_box = None
        if caption == '' and button is not None:
            caption = button.caption
        self.msg_write_box = ReadlineEdit(multiline=True)
        self.stream_write_box = ReadlineEdit(
            caption=u"Stream:  ",
            edit_text=caption
        )
        self.title_write_box = ReadlineEdit(caption=u"Topic:  ",
                                            edit_text=title)

        header_write_box = urwid.Columns([
            urwid.LineBox(
                self.stream_write_box, tlcorner=u'─', tline=u'─', lline=u'',
                trcorner=u'┬', blcorner=u'─', rline=u'│',
                bline=u'─', brcorner=u'┴'
            ),
            urwid.LineBox(
                self.title_write_box, tlcorner=u'─', tline=u'─', lline=u'',
                trcorner=u'─', blcorner=u'─', rline=u'',
                bline=u'─', brcorner=u'─'
            ),
        ])
        write_box = [
            (header_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('SEND_MESSAGE', key):
            if self.msg_edit_id:
                if not self.to_write_box:
                    success = self.model.update_stream_message(
                        topic=self.title_write_box.edit_text,
                        content=self.msg_write_box.edit_text,
                        msg_id=self.msg_edit_id,
                    )
                else:
                    success = self.model.update_private_message(
                        content=self.msg_write_box.edit_text,
                        msg_id=self.msg_edit_id,
                    )
            else:
                if not self.to_write_box:
                    success = self.model.send_stream_message(
                        stream=self.stream_write_box.edit_text,
                        topic=self.title_write_box.edit_text,
                        content=self.msg_write_box.edit_text
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
            self.view.controller.editor_mode = False
            self.main_view(False)
            self.view.middle_column.set_focus('body')
        elif is_command_key('TAB', key):
            if len(self.contents) == 0:
                return key
            # toggle focus position
            if self.focus_position == 0 and self.to_write_box is None:
                if self.contents[0][0].focus_col == 0:
                    self.contents[0][0].focus_col = 1
                    return key
                else:
                    self.contents[0][0].focus_col = 0
            self.focus_position = self.focus_position == 0
            self.contents[0][0].focus_col = 0

        key = super(WriteBox, self).keypress(size, key)
        return key


class MessageBox(urwid.Pile):
    def __init__(self, message: Dict[str, Any], model: Any,
                 last_message: Any) -> None:
        self.model = model
        self.message = message
        self.caption = ''
        self.stream_id = None  # type: Union[int, None]
        self.title = ''
        self.email = ''
        self.user_id = None  # type: Union[int, None]
        self.last_message = last_message
        # if this is the first message
        if self.last_message is None:
            self.last_message = defaultdict(dict)

        if self.message['type'] == 'stream':
            self.caption = self.message['display_recipient']
            self.stream_id = self.message['stream_id']
            self.title = self.message['subject']
        elif self.message['type'] == 'private':
            self.email = self.message['sender_email']
            self.user_id = self.message['sender_id']
        else:
            raise RuntimeError("Invalid message type")

        if self.message['type'] == 'private':
            if self._is_private_message_to_self():
                self.recipients_names = \
                    self.message['display_recipient'][0]['full_name']
                self.recipients_emails = self.model.user_email
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

        # mouse_event helper variable
        self.displaying_selection_hint = False

        super(MessageBox, self).__init__(self.main_view())

    def _time_for_message(self, message: Dict[str, Any]) -> str:
        return ctime(message['timestamp'])[:-8]

    def need_recipient_header(self) -> bool:
        # Prevent redundant information in recipient bar
        if len(self.model.narrow) == 1 and \
                self.model.narrow[0][0] == 'pm_with':
            return False
        if len(self.model.narrow) == 2 and \
                self.model.narrow[1][0] == 'topic':
            return False

        last_msg = self.last_message
        if self.message['type'] == 'stream':
            if (last_msg['type'] == 'stream' and
                    self.title == last_msg['subject'] and
                    self.caption == last_msg['display_recipient']):
                return False
            return True
        elif self.message['type'] == 'private':
            recipient_ids = [{recipient['id']
                              for recipient in message['display_recipient']
                              if 'id' in recipient}
                             for message in (self.message, last_msg)
                             if 'display_recipient' in message]
            if (len(recipient_ids) == 2 and
                    recipient_ids[0] == recipient_ids[1] and
                    last_msg['type'] == 'private'):
                return False
            return True
        else:
            raise RuntimeError("Invalid message type")

    def _is_private_message_to_self(self) -> bool:
        recipient_list = self.message['display_recipient']
        return len(recipient_list) == 1 and \
            recipient_list[0]['email'] == self.model.user_email

    def stream_header(self) -> Any:
        bar_color = self.model.stream_dict[self.stream_id]['color']
        bar_color = 's' + bar_color[:2] + bar_color[3] + bar_color[5]
        stream_title_markup = ('bar', [
            (bar_color, '{} >'.format(self.caption)),
            ('title', ' {} '.format(self.title))
        ])
        stream_title = urwid.Text(stream_title_markup)
        header = urwid.AttrWrap(stream_title, 'bar')
        header.markup = stream_title_markup
        return header

    def private_header(self) -> Any:
        if self._is_private_message_to_self():
            self.recipients_names = \
                self.message['display_recipient'][0]['full_name']
        title_markup = ('header', [
            ('custom', 'You and '),
            ('custom', self.recipients_names)
        ])
        title = urwid.Text(title_markup)
        header = urwid.AttrWrap(title, 'bar')
        header.markup = title_markup
        return header

    def top_header_bar(self, message_view: Any) -> Any:
        if self.message['type'] == 'stream':
            return message_view.stream_header()
        else:
            return message_view.private_header()

    def top_search_bar(self) -> Any:
        curr_narrow = self.model.narrow
        if curr_narrow == []:
            text_to_fill = 'All messages'
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == 'private':
            text_to_fill = 'All private messages'
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == 'starred':
            text_to_fill = 'Starred messages'
        elif self.message['type'] == 'stream':
            bar_color = self.model.stream_dict[self.stream_id]['color']
            bar_color = 's' + bar_color[:2] + bar_color[3] + bar_color[5]
            if len(curr_narrow) == 2 and curr_narrow[1][0] == 'topic':
                text_to_fill = ('bar', [  # type: ignore
                    (bar_color, '{}'.format(self.caption)),
                    (bar_color, ': topic narrow')
                ])
            else:
                text_to_fill = ('bar', [  # type: ignore
                    (bar_color, '{}'.format(self.caption))
                ])
        elif len(curr_narrow) == 1 and len(curr_narrow[0][1].split(",")) > 1:
            text_to_fill = 'Group private conversation'
        else:
            text_to_fill = 'Private conversation'
        title_markup = ('header', [
            ('custom', text_to_fill)
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
            reacts = defaultdict(int)  # type: Dict[str, int]
            custom_reacts = defaultdict(int)  # type: Dict[str, int]
            for reaction in reactions:
                if reaction['reaction_type'] == 'unicode_emoji':
                    reacts[reaction['emoji_code']] += 1
                else:
                    # Includes realm_emoji and zulip_extra_emoji
                    custom_reacts[":"+reaction['emoji_name']+":"] += 1
            dis = [
                '\\U' + '0'*(8-len(emoji)) + emoji + ' ' + str(reacts[emoji]) +
                ' ' for emoji in reacts]
            emojis = ''.join(e.encode().decode('unicode-escape') for e in dis)
            custom_emojis = ''.join(
                ['{} {} '.format(r, custom_reacts[r]) for r in custom_reacts])
            return urwid.Padding(
                urwid.Text(([
                    ('emoji', emoji.demojize(emojis + custom_emojis))
                ])), align='left', width=('relative', 90), left=25,
                min_width=50)
        except Exception:
            return ''

    def soup2markup(self, soup: Any) -> List[Any]:
        # Ensure a string is provided, in case the soup finds none
        # This could occur if eg. an image is removed or not shown
        markup = ['']
        if soup is None:  # This is not iterable, so return promptly
            return markup
        unrendered_tags = {  # In pairs of 'tag_name': 'text'
            # TODO: Some of these could be implemented
            'br': '',  # No indicator of absence
            'hr': 'RULER',
            'img': 'IMAGE',
            'table': 'TABLE'
        }
        unrendered_div_classes = {  # In pairs of 'div_class': 'text'
            # TODO: Support embedded content & twitter preview?
            'message_embed': 'EMBEDDED CONTENT',
            'inline-preview-twitter': 'TWITTER PREVIEW',
            'message_inline_ref': 'MESSAGE INLINE REF',
        }
        unrendered_template = '[{} NOT RENDERED]'
        for element in soup:
            if isinstance(element, NavigableString):
                # NORMAL STRINGS
                if hasattr(self, 'bq_len') and element == '\n' and \
                        self.bq_len > 0:
                    self.bq_len -= 1
                    continue
                markup.append(element)
            elif (element.name == 'div' and element.attrs and
                    any(cls in element.attrs.get('class', [])
                        for cls in unrendered_div_classes)):
                # UNRENDERED DIV CLASSES
                matching_class = (set(unrendered_div_classes) &
                                  set(element.attrs.get('class')))
                text = unrendered_div_classes[matching_class.pop()]
                if text:
                    markup.append(unrendered_template.format(text))
            elif (element.name == 'img' and
                    element.attrs.get('class', []) == ['emoji']):
                # CUSTOM EMOJIS AND ZULIP_EXTRA_EMOJI
                emoji_name = element.attrs.get('title', [])
                markup.append(":"+emoji_name+":")
            elif element.name in unrendered_tags:
                # UNRENDERED SIMPLE TAGS
                text = unrendered_tags[element.name]
                if text:
                    markup.append(unrendered_template.format(text))
            elif element.name in ('p', 'ul', 'del'):
                # PARAGRAPH, LISTS, STRIKE-THROUGH
                markup.extend(self.soup2markup(element))
            elif (element.name == 'span' and element.attrs and
                  'emoji' in element.attrs.get('class', [])):
                # EMOJI
                markup.append(element.text)
            elif (element.name == 'span' and element.attrs and
                  ('katex-display' in element.attrs.get('class', []) or
                   'katex' in element.attrs.get('class', []))):
                # MATH TEXT
                markup.append(element.text)
            elif element.name == 'span' and element.attrs and\
                    ('user-mention' in element.attrs.get('class', []) or
                     'user-group-mention' in element.attrs.get('class', [])):
                # USER MENTIONS & USER-GROUP MENTIONS
                markup.append(('span', element.text))
            elif element.name == 'a':
                # LINKS
                link = element.attrs['href']
                text = element.img['src'] if element.img else element.text
                if link == text:
                    # If the link and text are same
                    # usually the case when user just pastes
                    # a link then just display the link
                    markup.append(text)
                else:
                    if link.startswith('/user_uploads/'):
                        # Append org url to before user_uploads to convert it
                        # into a link.
                        link = self.model.server_url + link
                    markup.append(
                        ('link', '[' + text + ']' + '(' + link + ')'))
            elif element.name == 'blockquote':
                # BLOCKQUOTE TEXT
                markup.append((
                    'blockquote', self.soup2markup(element)
                ))
            elif element.name == 'code':
                # CODE (INLINE?)
                markup.append((
                    'code', element.text
                ))
            elif element.name == 'div' and element.attrs and\
                    'codehilite' in element.attrs.get('class', []):
                # CODE (BLOCK?)
                markup.append((
                    'code', element.text
                ))
            elif element.name in ('strong', 'em'):
                # BOLD & ITALIC
                markup.append(('bold', element.text))
            elif element.name == 'li':
                # LISTS
                # TODO: Support nested lists
                markup.append('  * ')
                markup.extend(self.soup2markup(element))
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
            'author': message['last']['author'] != message['this']['author'],
            '24h': (message['last']['datetime'] is not None and
                    ((message['this']['datetime'] -
                      message['last']['datetime'])
                     .days)),
            'timestamp': (message['last']['time'] is not None and
                          message['this']['time'] != message['last']['time']),
            'star_status': (message['this']['is_starred'] !=
                            message['last']['is_starred']),
        }
        any_differences = any(different.values())

        if any_differences:  # Construct content_header, if needed
            TextType = Dict[str, Tuple[Optional[str], str]]
            text = {key: (None, ' ')
                    for key in ('author', 'star', 'time')}  # type: TextType
            if any(different[key] for key in ('recipients', 'author', '24h')):
                text['author'] = ('name', message['this']['author'])
            if message['this']['is_starred']:
                text['star'] = ('starred', "*")
            if any(different[key]
                   for key in ('recipients', 'author', 'timestamp')):
                text['time'] = ('time', message['this']['time'])

            content_header = urwid.Columns([
                ('weight', 10, urwid.Text(text['author'])),
                (1, urwid.Text(text['star'], align='right')),
                (16, urwid.Text(text['time'], align='right')),
                ], dividechars=1)
        else:
            content_header = None

        # Transform raw message content into markup (As needed by urwid.Text)
        active_char = '▒'  # Options are '█', '▓', '▒', '░'
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
                    ]), tline='', bline='', rline='', lline=active_char
                )
            ]),
            align='left', left=left_padding,
            width=('relative', 100), min_width=10, right=5)

        # Reactions
        reactions = self.reactions_view(self.message['reactions'])

        # Build parts together and return
        parts = [
            (recipient_header, recipient_header is not None),
            (content_header, any_differences),
            (content, True),
            (reactions, reactions != ''),
        ]
        return [part for part, condition in parts if condition]

    def transform_content(self) -> Tuple[None, Any]:
        soup = BeautifulSoup(self.message['content'], 'lxml')
        body = soup.find(name='body')
        if body and body.find(name='blockquote'):
            padding_char = '░'
            self.indent_quoted_content(soup, padding_char)

        return (None, self.soup2markup(body))

    def indent_quoted_content(self, soup: Any, padding_char: str) -> None:
        '''
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
        '''
        pad_count = 1
        blockquote_list = soup.find_all('blockquote')
        self.bq_len = len(blockquote_list)
        for tag in blockquote_list:
            child_list = tag.findChildren(recursive=False)
            actual_padding = (padding_char + ' ')*pad_count
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
        return True

    def mouse_event(self, size: Tuple[int, int], event: Any, button: Any,
                    col: int, row: int, focus: int) -> Union[bool, Any]:
        if event == 'mouse press':
            if button == 1:
                self.keypress(size, 'enter')
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

        return super(MessageBox, self).mouse_event(size, event, button, col,
                                                   row, focus)

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.recipients_emails
                )
            elif self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['display_recipient'],
                    title=self.message['subject']
                )
        elif is_command_key('STREAM_MESSAGE', key):
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.recipients_emails
                )
            elif self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['display_recipient']
                )
        elif is_command_key('STREAM_NARROW', key):
            if self.message['type'] == 'private':
                self.model.controller.narrow_to_user(self)
            elif self.message['type'] == 'stream':
                self.model.controller.narrow_to_stream(self)
        elif is_command_key('TOGGLE_NARROW', key):
            if self.message['type'] == 'private':
                if (len(self.model.narrow) == 1 and
                        self.model.narrow[0][0] == 'pm_with'):
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
            self.model.controller.view.write_box.private_box_view(
                email=self.message['sender_email']
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
        return key


class SearchBox(urwid.Pile):
    def __init__(self, controller: Any) -> None:
        self.controller = controller
        super(SearchBox, self).__init__(self.main_view())

    def main_view(self) -> Any:
        self.text_box = ReadlineEdit(u"Search: ")
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
            self.msg_narrow, title=u"Current message recipients",
            tline=u'─', lline=u'', trcorner=u'─', tlcorner=u'─',
            blcorner=u'─', rline=u'', bline=u'─', brcorner=u'─')
        return [self.search_bar, self.recipient_bar]

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('GO_BACK', key):
            self.text_box.set_edit_text("")
            self.controller.editor_mode = False
            self.controller.view.middle_column.set_focus('body')
            return key

        elif is_command_key('ENTER', key):
            self.controller.editor_mode = False
            self.controller.search_messages(self.text_box.edit_text)
            self.controller.view.middle_column.set_focus('body')
            return key

        key = super(SearchBox, self).keypress(size, key)
        return key


class UserSearchBox(urwid.Edit):
    """
    Search Box to search users in real-time.
    """

    def __init__(self, user_view: Any) -> None:
        self.user_view = user_view
        super(UserSearchBox, self).__init__(edit_text="Search people")

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key):
            self.user_view.view.controller.editor_mode = False
            self.user_view.set_focus("body")
        if is_command_key('GO_BACK', key):
            self.user_view.view.controller.editor_mode = False
            self.set_edit_text("Search people")
            self.user_view.set_focus("body")
            self.user_view.keypress(size, 'esc')

        return super(UserSearchBox, self).keypress(size, key)


class StreamSearchBox(urwid.Edit):
    """
    Search Box to search streams in real-time.urwid
    """

    def __init__(self, stream_view: Any) -> None:
        self.stream_view = stream_view
        super(StreamSearchBox, self).__init__(edit_text="Search streams")

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if is_command_key('ENTER', key) and len(self.stream_view.log):
            self.stream_view.view.controller.editor_mode = False
            self.stream_view.set_focus("body")
            self.stream_view.body.set_focus(0)
        if is_command_key('GO_BACK', key):
            self.stream_view.view.controller.editor_mode = False
            self.set_edit_text("Search streams")
            self.stream_view.set_focus("body")
            self.stream_view.keypress(size, 'esc')

        return super(StreamSearchBox, self).keypress(size, key)
