import pytest
from collections import defaultdict
from bs4 import BeautifulSoup

from zulipterminal.ui_tools.boxes import MessageBox

from urwid import AttrWrap, Columns, Padding, Text

VIEWS = "zulipterminal.ui_tools.views"
MESSAGEBOX = "zulipterminal.ui_tools.boxes.MessageBox"


class TestMessageBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.model = mocker.MagicMock()
        self.model.index = initial_index

    @pytest.mark.parametrize('message_type, set_fields', [
        ('stream', [('caption', ''), ('stream_id', None), ('title', '')]),
        ('private', [('email', ''), ('user_id', None)]),
    ])
    def test_init(self, mocker, message_type, set_fields):
        mocker.patch.object(MessageBox, 'main_view')
        message = dict(display_recipient=[
            {
                'id': 7,
                'email': 'boo@zulip.com',
                'full_name': 'Boo is awesome'
            }],
            stream_id=5,
            subject='hi',
            sender_email='foo@zulip.com',
            sender_id=4209,
            type=message_type)

        msg_box = MessageBox(message, self.model, None)

        assert msg_box.last_message == defaultdict(dict)
        for field, invalid_default in set_fields:
            assert getattr(msg_box, field) != invalid_default

    def test_init_fails_with_bad_message_type(self):
        message = dict(type='BLAH')

        with pytest.raises(RuntimeError):
            msg_box = MessageBox(message, self.model, None)

    def test_private_message_to_self(self, mocker):
        message = dict(
            type='private',
            display_recipient=[{'full_name': 'Foo Foo',
                                'email': 'foo@zulip.com',
                                'id': None}],
            sender_id=9,
            content="<p> self message. </p>",
            sender_full_name='Foo Foo',
            sender_email='foo@zulip.com',
            timestamp=150989984,
        )
        self.model.user_email = 'foo@zulip.com'
        mocker.patch(MESSAGEBOX + '._is_private_message_to_self',
                     return_value=True)
        mocker.patch.object(MessageBox, 'main_view')
        msg_box = MessageBox(message, self.model, None)

        assert msg_box.recipients_emails == 'foo@zulip.com'
        msg_box._is_private_message_to_self.assert_called_once_with()

    @pytest.mark.parametrize('content, markup', [
        ('', []),
        ('<p>hi</p>', ['', 'hi']),
        ('<span class="user-mention">@Bob Smith', [('span', '@Bob Smith')]),
        ('<span class="user-group-mention">@A Group', [('span', '@A Group')]),
        ('<code>some code', [('code', 'some code')]),
        ('<div class="codehilite">some code', [('code', 'some code')]),
        ('<strong>Something', [('bold', 'Something')]),
        ('<em>Something', [('bold', 'Something')]),
        ('<blockquote>stuff', [('blockquote', ['', 'stuff'])]),
        ('<div class="message_embed">',
            ['[EMBEDDED CONTENT NOT RENDERED]']),  # FIXME Unsupported
        ('<a href="foo">foo</a>', ['foo']),  # FIXME? Render with link style?
        ('<a href="foo">bar</a>', [('link', '[bar](foo)')]),
        ('<a href="/user_uploads/blah"',
            [('link', '[](SOME_BASE_URL/user_uploads/blah)')]),
        ('<li>Something', ['  * ', '', 'Something']),
        ('<li>Something<li>else',  # NOTE Real items are newline-separated?
            ['  * ', '', 'Something', '  * ', '', 'else']),
        ('<br>', []), ('<br/>', []),
        ('<hr>', ['[RULER NOT RENDERED]']),
        ('<hr/>', ['[RULER NOT RENDERED]']),
        ('<img>', ['[IMAGE NOT RENDERED]']),
        ('<img/>', ['[IMAGE NOT RENDERED]']),
        ('<table>stuff</table>', ['[TABLE NOT RENDERED]']),
        ('<span class="katex-display">some-math</span>', ['some-math']),
        ('<span class="katex">some-math</span>', ['some-math']),
        ('<ul><li>text</li></ul>', ['', '  * ', '', 'text']),
        ('<del>text</del>', ['', 'text']),  # FIXME Strikethrough
        ('<div class="message_inline_image">'
         '<a href="x"><img src="x"></a></div>', ['', 'x']),
        ('<div class="message_inline_ref">blah</div>',
            ['[MESSAGE INLINE REF NOT RENDERED]']),
        ('<span class="emoji">:smile:</span>', [':smile:']),
        ('<div class="inline-preview-twitter"',
            ['[TWITTER PREVIEW NOT RENDERED]']),
        ('<img class="emoji" title="zulip"/>', [':zulip:']),
        ('<img class="emoji" title="github"/>', [':github:']),
    ], ids=[
        'empty', 'p', 'user-mention', 'group-mention', 'code', 'codehilite',
        'strong', 'em', 'blockquote',
        'embedded_content', 'link_sametext', 'link_differenttext',
        'link_userupload', 'listitem', 'listitems',
        'br', 'br2', 'hr', 'hr2', 'img', 'img2', 'table', 'math', 'math2',
        'ul', 'strikethrough_del', 'inline_image', 'inline_ref',
        'emoji', 'preview-twitter', 'zulip_extra_emoji', 'custom_emoji'
    ])
    def test_soup2markup(self, content, markup):
        message = dict(display_recipient=['x'], stream_id=5, subject='hi',
                       sender_email='foo@zulip.com', id=4, sender_id=4209,
                       type='stream',  # NOTE Output should not vary with PM
                       flags=[], content=content, sender_full_name='bob smith',
                       timestamp=99, reactions=[])
        self.model.stream_dict = {
            5: {  # matches stream_id above
                'color': '#bfd56f',
            },
        }
        self.model.server_url = "SOME_BASE_URL"
        # NOTE Absence of previous (last) message should not affect markup
        msg_box = MessageBox(message, self.model, None)

        soup = BeautifulSoup(message['content'], 'lxml').find(name='body')
        assert msg_box.soup2markup(soup) == [''] + markup

    @pytest.mark.parametrize('message, last_message', [
        ({
            'sender_id': 1,
            'display_recipient': 'Verona',
            'sender_full_name': 'aaron',
            'submessages': [],
            'stream_id': 5,
            'subject': 'Verona2',
            'id': 37,
            'subject_links': [],
            'recipient_id': 20,
            'content': "<p>It's nice and it feels more modern, but I think"
                       " this will take some time to get used to</p>",
            'timestamp': 1531716583,
            'sender_realm_str': 'zulip',
            'client': 'populate_db',
            'content_type': 'text/html',
            'reactions': [],
            'type': 'stream',
            'is_me_message': False,
            'sender_short_name': 'aaron',
            'flags': ['read'],
            'sender_email': 'AARON@zulip.com'
        }, None),
        ({
            'sender_id': 5,
            'display_recipient': [{
                'is_mirror_dummy': False,
                'short_name': 'aaron',
                'email': 'AARON@zulip.com',
                'id': 1,
                'full_name': 'aaron'
            }, {
                'is_mirror_dummy': False,
                'short_name': 'iago',
                'email': 'iago@zulip.com',
                'id': 5,
                'full_name': 'Iago'
            }],
            'sender_full_name': 'Iago',
            'submessages': [],
            'subject': '',
            'id': 107,
            'subject_links': [],
            'recipient_id': 1,
            'content': '<p>what are you planning to do this week</p>',
            'timestamp': 1532103879,
            'sender_realm_str': 'zulip',
            'client': 'ZulipTerminal',
            'content_type': 'text/html',
            'reactions': [],
            'type': 'private',
            'is_me_message': False,
            'sender_short_name': 'iago',
            'flags': ['read'],
            'sender_email': 'iago@zulip.com'
        }, None)
    ])
    def test_main_view(self, mocker, message, last_message):
        self.model.stream_dict = {
            5: {
                'color': '#bfd56f',
            },
        }
        msg_box = MessageBox(message, self.model, last_message)

    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('to_vary_in_last_message', [
            {'display_recipient': 'Verona offtopic'},
            {'subject': 'Test topic (previous)'},
            {'type': 'private'},
    ], ids=['different_stream_before', 'different_topic_before', 'PM_before'])
    def test_main_view_generates_stream_header(self, mocker, message,
                                               to_vary_in_last_message):
        mocker.patch(VIEWS + ".urwid.Text")
        self.model.stream_dict = {
            5: {
                'color': '#bfd56f',
            },
        }
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3
        assert isinstance(view_components[0], AttrWrap)
        assert view_components[0].get_attr() == 'bar'
        assert isinstance(view_components[1], Columns)
        assert isinstance(view_components[2], Padding)

    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'private',
            'sender_email': 'iago@zulip.com',
            'sender_id': 5,
            'display_recipient': [{
                'email': 'AARON@zulip.com',
                'id': 1,
                'full_name': 'aaron'
            }, {
                'email': 'iago@zulip.com',
                'id': 5,
                'full_name': 'Iago'
            }],
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'Alice',
            'timestamp': 1532103879,
        },
    ])
    @pytest.mark.parametrize('to_vary_in_last_message', [
            {
                'display_recipient': [{
                    'email': 'AARON@zulip.com',
                    'id': 1,
                    'full_name': 'aaron'
                }, {
                    'email': 'iago@zulip.com',
                    'id': 5,
                    'full_name': 'Iago'
                }, {
                    'email': 'SE@zulip.com',
                    'id': 6,
                    'full_name': 'Someone Else'
                }],
            },
            {'type': 'stream'},
    ], ids=['larger_pm_group', 'stream_before'])
    def test_main_view_generates_PM_header(self, mocker, message,
                                           to_vary_in_last_message):
        mocker.patch(VIEWS + ".urwid.Text")
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3
        assert isinstance(view_components[0], AttrWrap)
        assert view_components[0].get_attr() == 'bar'
        assert isinstance(view_components[1], Columns)
        assert isinstance(view_components[2], Padding)

    @pytest.mark.parametrize('msg_narrow, msg_type, assert_header_bar,\
                              assert_search_bar', [
        ([], 0, 'PTEST >', 'All messages'),
        ([], 1, 'You and ', 'All messages'),
        ([], 2, 'You and ', 'All messages'),
        ([['stream', 'PTEST']], 0, 'PTEST >', ('bar', [('s#bd6', 'PTEST')])),
        ([['stream', 'PTEST'], ['topic', 'b']], 0, 'PTEST >',
         ('bar', [('s#bd6', 'PTEST'), ('s#bd6', ': topic narrow')])),
        ([['is', 'private']], 1, 'You and ', 'All private messages'),
        ([['is', 'private']], 2, 'You and ', 'All private messages'),
        ([['pm_with', 'boo@zulip.com']], 1, 'You and ',
         'Private conversation'),
        ([['pm_with', 'boo@zulip.com, bar@zulip.com']], 2, 'You and ',
         'Group private conversation'),
        ([['is', 'starred']], 0, 'PTEST >', 'Starred messages'),
        ([['is', 'starred']], 1, 'You and ', 'Starred messages'),
        ([['is', 'starred']], 2, 'You and ', 'Starred messages'),
    ])
    def test_msg_generates_search_and_header_bar(self, mocker,
                                                 messages_successful_response,
                                                 msg_type, msg_narrow,
                                                 assert_header_bar,
                                                 assert_search_bar):
        self.model.stream_dict = {
            205: {
                'color': '#bfd56f',
            },
        }
        self.model.narrow = msg_narrow
        messages = messages_successful_response['messages']
        current_message = messages[msg_type]
        msg_box = MessageBox(current_message, self.model, messages[0])
        search_bar = msg_box.top_search_bar()
        header_bar = msg_box.top_header_bar(msg_box)

        assert header_bar.text.startswith(assert_header_bar)
        assert search_bar.text_to_fill == assert_search_bar

    # Assume recipient (PM/stream/topic) header is unchanged below
    @pytest.mark.parametrize('message', [
        {
            'id': 4,
            'type': 'stream',
            'display_recipient': 'Verona',
            'stream_id': 5,
            'subject': 'Test topic',
            'flags': [],
            'content': '<p>what are you planning to do this week</p>',
            'reactions': [],
            'sender_full_name': 'alice',
            'timestamp': 1532103879,
        }
    ])
    @pytest.mark.parametrize('starred_msg', ['this', 'last', 'neither'],
                             ids=['this_starred', 'last_starred', 'no_stars'])
    @pytest.mark.parametrize('expected_header, to_vary_in_last_message', [
        (['alice', ' ', 'DAYDATETIME'], {'sender_full_name': 'bob'}),
        ([' ', ' ', 'DAYDATETIME'], {'timestamp': 1532103779}),  # 100 earlier
        (['alice', ' ', 'DAYDATETIME'], {'timestamp': 0}),  # much earlier!
    ], ids=['author_different', 'earlier_message', 'much_earlier_message'])
    def test_main_view_content_header_without_header(self, mocker, message,
                                                     expected_header,
                                                     starred_msg,
                                                     to_vary_in_last_message):
        stars = {msg: ({'flags': ['starred']} if msg == starred_msg else {})
                 for msg in ('this', 'last')}
        this_msg = dict(message, **stars['this'])
        all_to_vary = dict(to_vary_in_last_message, **stars['last'])
        last_msg = dict(message, **all_to_vary)
        msg_box = MessageBox(this_msg, self.model, last_msg)
        expected_header[1] = '*' if starred_msg == 'this' else ' '
        expected_header[2] = msg_box._time_for_message(message)

        view_components = msg_box.main_view()
        assert len(view_components) == 2
        assert isinstance(view_components[0], Columns)
        assert ([w.text for w in view_components[0].widget_list] ==
                expected_header)
        assert isinstance(view_components[1], Padding)

    @pytest.mark.parametrize('to_vary_in_each_message', [
        {'sender_full_name': 'bob'},
        {'timestamp': 1532103779},
        {'timestamp': 0},
        {},
        {'flags': ['starred']},
    ], ids=['common_author', 'common_timestamp', 'common_early_timestamp',
            'common_unchanged_message', 'both_starred'])
    def test_main_view_compact_output(self, mocker, message_fixture,
                                      to_vary_in_each_message):
        message_fixture.update({'id': 4})
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, varied_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 1
        assert isinstance(view_components[0], Padding)

    def test_main_view_generates_EDITED_label(self, mocker,
                                              messages_successful_response):
        messages = messages_successful_response['messages']
        for message in messages:
            self.model.index['edited_messages'].add(message['id'])
            msg_box = MessageBox(message, self.model, message)
            view_components = msg_box.main_view()

            label = view_components[0].original_widget.contents[0]
            assert label[0].text == 'EDITED'
            assert label[1][1] == 7

    @pytest.mark.parametrize('to_vary_in_each_message, realm_editing_allowed,\
                             expect_editing_to_succeed', [
        ({'sender_id': 2, 'timestamp': 45}, True, False),
        ({'sender_id': 1, 'timestamp': 1}, True, False),
        ({'sender_id': 1, 'timestamp': 45}, False, False),
        ({'sender_id': 1, 'timestamp': 45}, True, True),
    ], ids=['msg_sent_by_other_user',
            'time_limit_esceeded',
            'editing_not_allowed',
            'all_conditions_met'])
    def test_keypress_edit_message(self, mocker, message_fixture,
                                   expect_editing_to_succeed,
                                   to_vary_in_each_message,
                                   realm_editing_allowed):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        key = 'e'
        size = (20,)
        msg_box = MessageBox(varied_message, self.model, message_fixture)
        msg_box.model.user_id = 1
        msg_box.model.initial_data = {
            'realm_allow_message_editing': realm_editing_allowed,
            'realm_message_content_edit_limit_seconds': 60,
        }
        msg_box.model.client.get_raw_message.return_value = {
            'raw_content': "Edit this message"
        }
        write_box = msg_box.model.controller.view.write_box
        write_box.msg_edit_id = None
        mocker.patch("zulipterminal.ui_tools.boxes.time", return_value=100)
        msg_box.keypress(size, key)

        if expect_editing_to_succeed:
            assert write_box.msg_edit_id == varied_message['id']
            write_box.msg_write_box.set_edit_text.assert_called_once_with(
                "Edit this message")
        else:
            assert write_box.msg_edit_id is None
            write_box.msg_write_box.set_edit_text.assert_not_called()

    @pytest.mark.parametrize('raw_html, expected_content', [
        ("""<blockquote>
                <p>A</p>
            </blockquote>
            <p>B</p>""", "░ A\n\nB"),
        ("""<blockquote>
                <blockquote>
                    <p>A</p>
                </blockquote>
                <p>B</p>
            </blockquote>
            <p>C</p>""", "░ ░ A\n\n░ B\n\nC"),
        ("""<blockquote>
                <blockquote>
                    <blockquote>
                        <p>A</p>
                    </blockquote>
                    <p>B</p>
                </blockquote>
                <p>C</p>
            </blockquote>
            <p>D</p>""", "░ ░ ░ A\n\n░ ░ B\n\n░ C\n\nD"),
        ("""<blockquote>
                <p>A<br/>B</p>
            </blockquote>
            <p>C</p>""", "░ A\n░ B\n\nC"),
        ("""<blockquote>
                <p><a href='https://chat.zulip.org/'</a>czo</p>
            </blockquote>""", "░ [czo](https://chat.zulip.org/)\n"),
        pytest.param("""<blockquote>
                            <blockquote>
                                <p>A<br>
                                B</p>
                            </blockquote>
                        </blockquote>
            """, "░ ░ A\n░ ░ B",
                     marks=pytest.mark.xfail(reason="rendered_bug")),
        pytest.param("""<blockquote>
                            <blockquote>
                                <p>A</p>
                            </blockquote>
                            <p>B</p>
                            <blockquote>
                                <p>C</p>
                            </blockquote>
                        </blockquote>
        """, "░ ░ A\n░ B\n░ ░ C",
                     marks=pytest.mark.xfail(reason="rendered_bug")),
    ], ids=[
        "quoted level 1",
        "quoted level 2",
        "quoted level 3",
        "multi-line quoting",
        "quoting with links",
        "multi-line level 2",
        "quoted level 2-1-2",
    ])
    def test_transform_content(self, mocker, raw_html, expected_content,
                               messages_successful_response):
        message = messages_successful_response['messages'][0]
        msg_box = MessageBox(message, self.model, message)
        msg_box.message['content'] = raw_html
        content = msg_box.transform_content()
        rendered_text = Text(content)
        assert rendered_text.text == expected_content
