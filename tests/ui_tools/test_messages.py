from collections import OrderedDict, defaultdict
from datetime import date

import pytest
import pytz
from bs4 import BeautifulSoup
from pytest import param as case
from urwid import Columns, Divider, Padding, Text

from zulipterminal.config.keys import keys_for_command
from zulipterminal.config.symbols import (
    QUOTED_TEXT_MARKER,
    STATUS_INACTIVE,
    STREAM_TOPIC_SEPARATOR,
    TIME_MENTION_MARKER,
)
from zulipterminal.ui_tools.messages import MessageBox


MODULE = "zulipterminal.ui_tools.messages"


SERVER_URL = "https://chat.zulip.zulip"


class TestMessageBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.model = mocker.MagicMock()
        self.model.index = initial_index

    @pytest.mark.parametrize(
        "message_type, set_fields",
        [
            ("stream", [("stream_name", ""), ("stream_id", None), ("topic_name", "")]),
            ("private", [("email", ""), ("user_id", None)]),
        ],
    )
    def test_init(self, mocker, message_type, set_fields):
        mocker.patch.object(MessageBox, "main_view")
        message = dict(
            id=3,
            display_recipient=[
                {"id": 7, "email": "boo@zulip.com", "full_name": "Boo is awesome"}
            ],
            stream_id=5,
            subject="hi",
            sender_email="foo@zulip.com",
            sender_id=4209,
            type=message_type,
        )

        msg_box = MessageBox(message, self.model, None)

        assert msg_box.last_message == defaultdict(dict)
        for field, invalid_default in set_fields:
            assert getattr(msg_box, field) != invalid_default
        if message_type == "stream":
            assert msg_box.topic_links == OrderedDict()
        assert msg_box.message_links == OrderedDict()
        assert msg_box.time_mentions == list()

    def test_init_fails_with_bad_message_type(self):
        message = dict(type="BLAH")

        with pytest.raises(RuntimeError):
            MessageBox(message, self.model, None)

    def test_private_message_to_self(self, mocker):
        message = dict(
            type="private",
            display_recipient=[
                {"full_name": "Foo Foo", "email": "foo@zulip.com", "id": None}
            ],
            sender_id=9,
            content="<p> self message. </p>",
            sender_full_name="Foo Foo",
            sender_email="foo@zulip.com",
            timestamp=150989984,
        )
        self.model.user_email = "foo@zulip.com"
        mocker.patch(
            MODULE + ".MessageBox._is_private_message_to_self", return_value=True
        )
        mocker.patch.object(MessageBox, "main_view")
        msg_box = MessageBox(message, self.model, None)

        assert msg_box.recipient_emails == ["foo@zulip.com"]
        msg_box._is_private_message_to_self.assert_called_once_with()

    @pytest.mark.parametrize(
        "content, expected_markup",
        [
            case("", [], id="empty"),
            case("<p>hi</p>", ["", "hi"], id="p"),
            case(
                '<span class="user-mention">@Bob Smith',
                [("msg_mention", "@Bob Smith")],
                id="user-mention",
            ),
            case("<h1>heading1</h1>", [("msg_heading", "heading1")], id="h1"),
            case("<h2>heading2</h2>", [("msg_heading", "heading2")], id="h2"),
            case("<h3>heading3</h3>", [("msg_heading", "heading3")], id="h3"),
            case("<h4>heading4</h4>", [("msg_heading", "heading4")], id="h4"),
            case("<h5>heading5</h5>", [("msg_heading", "heading5")], id="h5"),
            case("<h6>heading6</h6>", [("msg_heading", "heading6")], id="h6"),
            case(
                '<span class="user-group-mention">@A Group',
                [("msg_mention", "@A Group")],
                id="group-mention",
            ),
            case("<code>some code", [("pygments:w", "some code")], id="inline-code"),
            case(
                '<div class="codehilite" data-code-language="python">'
                "<pre><span></span>"
                "<code><span>def</span> <span>func</span><span>():</span>\n"
                '    <span class="pg">print</span><span>()</span><span></span>\n'
                "\n"
                "<span>class</span> <span>New</span><span>:</span>\n"
                '    <span>name</span> <span>=</span> <span>"name"</span>\n'
                "</code></pre></div>",
                [
                    ("pygments:w", "def"),
                    ("pygments:w", " "),
                    ("pygments:w", "func"),
                    ("pygments:w", "():"),
                    ("pygments:w", "\n" "    "),
                    ("pygments:pg", "print"),
                    ("pygments:w", "()"),
                    ("pygments:w", "\n" "\n"),
                    ("pygments:w", "class"),
                    ("pygments:w", " "),
                    ("pygments:w", "New"),
                    ("pygments:w", ":"),
                    ("pygments:w", "\n" "    "),
                    ("pygments:w", "name"),
                    ("pygments:w", " "),
                    ("pygments:w", "="),
                    ("pygments:w", " "),
                    ("pygments:w", '"name"'),
                    ("pygments:w", "\n"),
                ],
                id="codehilite-code",
            ),
            case(
                '<div class="codehilite" data-code-language="python">'
                "<pre><span></span>"
                "<span>def</span> <span>func</span><span>():</span>\n"
                '    <span class="pg">print</span><span>()</span>\n'
                "\n"
                "<span>class</span> <span>New</span><span>:</span>\n"
                '    <span>name</span> <span>=</span> <span>"name"</span>\n'
                "</pre></div>",
                [
                    ("pygments:w", "def"),
                    ("pygments:w", " "),
                    ("pygments:w", "func"),
                    ("pygments:w", "():"),
                    ("pygments:w", "\n" "    "),
                    ("pygments:pg", "print"),
                    ("pygments:w", "()"),
                    ("pygments:w", "\n" "\n"),
                    ("pygments:w", "class"),
                    ("pygments:w", " "),
                    ("pygments:w", "New"),
                    ("pygments:w", ":"),
                    ("pygments:w", "\n" "    "),
                    ("pygments:w", "name"),
                    ("pygments:w", " "),
                    ("pygments:w", "="),
                    ("pygments:w", " "),
                    ("pygments:w", '"name"'),
                    ("pygments:w", "\n"),
                ],
                id="codehilite-code-old",
            ),
            case(
                '<div class="codehilite">'
                "<pre><span></span>"
                "<code>This is a\n"
                "    Plain\n"
                "\n"
                "    Codeblock\n"
                "</code></pre></div>",
                [
                    ("pygments:w", "This is a\n    Plain\n\n    Codeblock\n"),
                ],
                id="codehilite-plain-text-codeblock",
            ),
            case(
                '<div class="codehilite">'
                "<pre><span></span>"
                "This is a\n"
                "    Plain\n"
                "\n"
                "    Codeblock\n"
                "</pre></div>",
                [
                    ("pygments:w", "This is a\n    Plain\n\n    Codeblock\n"),
                ],
                id="codehilite-plain-text-codeblock-old",
            ),
            case("<strong>Something", [("msg_bold", "Something")], id="strong"),
            case("<em>Something", [("msg_bold", "Something")], id="em"),
            case("<blockquote>stuff", [("msg_quote", ["", "stuff"])], id="blockquote"),
            # FIXME Unsupported:
            case(
                '<div class="message_embed">',
                ["[EMBEDDED CONTENT NOT RENDERED]"],
                id="embedded_content",
            ),
            # TODO: Generate test cases to work with both soup2markup and
            # footlinks_view.
            case(
                '<a href="http://foo">Foo</a><a href="https://bar.org">Bar</a>',
                [
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "Bar"),
                    " ",
                    ("msg_link_index", "[2]"),
                ],
                id="link_two",
            ),
            case(
                '<a href="http://foo">Foo</a><a href="http://foo">Another foo</a>',
                [
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "Another foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                ],
                id="link_samelinkdifferentname",
            ),
            case(
                '<a href="http://foo">Foo</a><a href="https://bar.org">Bar</a>'
                '<a href="http://foo">Foo</a><a href="https://bar.org">Bar</a>',
                [
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "Bar"),
                    " ",
                    ("msg_link_index", "[2]"),
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "Bar"),
                    " ",
                    ("msg_link_index", "[2]"),
                ],
                id="link_duplicatelink",
            ),
            case(
                '<a href="http://baz.com/">http://baz.com/</a>',
                [("msg_link", "http://baz.com"), " ", ("msg_link_index", "[1]")],
                id="link_trailingslash",
            ),
            case(
                '<a href="http://foo.com/">Foo</a><a href="http://foo.com">Foo</a>',
                [
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "Foo"),
                    " ",
                    ("msg_link_index", "[1]"),
                ],
                id="link_trailingslashduplicatelink",
            ),
            case(
                '<a href="http://foo">http://foo</a>',
                [("msg_link", "http://foo"), " ", ("msg_link_index", "[1]")],
                id="link_sametext",
            ),
            case(
                '<a href="http://foo/bar.png">http://foo/bar.png</a>',
                [("msg_link", "bar.png"), " ", ("msg_link_index", "[1]")],
                id="link_sameimage",
            ),
            case(
                '<a href="http://foo">bar</a>',
                [("msg_link", "bar"), " ", ("msg_link_index", "[1]")],
                id="link_differenttext",
            ),
            case(
                '<a href="/user_uploads/blah.gif"',
                [("msg_link", "blah.gif"), " ", ("msg_link_index", "[1]")],
                id="link_userupload",
            ),
            case(
                '<a href="/api"',
                [("msg_link", "/api"), " ", ("msg_link_index", "[1]")],
                id="link_api",
            ),
            case(
                f'<a href="some/relative_url">{SERVER_URL}/some/relative_url</a>',
                [("msg_link", "/some/relative_url"), " ", ("msg_link_index", "[1]")],
                id="link_serverrelative_same",
            ),
            case(
                '<a href="http://foo.com/bar">foo.com/bar</a>',
                [("msg_link", "foo.com"), " ", ("msg_link_index", "[1]")],
                id="link_textwithoutscheme",
            ),
            case(
                '<a href="http://foo.com">foo.com</a>'
                '<a href="http://foo.com">http://foo.com</a>'
                '<a href="https://foo.com">https://foo.com</a>'
                '<a href="http://foo.com">Text</a>',
                [
                    ("msg_link", "foo.com"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "http://foo.com"),
                    " ",
                    ("msg_link_index", "[1]"),
                    ("msg_link", "https://foo.com"),
                    " ",
                    ("msg_link_index", "[2]"),
                    ("msg_link", "Text"),
                    " ",
                    ("msg_link_index", "[1]"),
                ],
                id="link_differentscheme",
            ),
            case("<li>Something", ["\n", "  \N{BULLET} ", "", "Something"], id="li"),
            case("<li></li>", ["\n", "  \N{BULLET} ", ""], id="empty_li"),
            case(
                "<li>\n<p>Something",
                ["\n", "  \N{BULLET} ", "", "", "", "Something"],
                id="li_with_li_p_newline",
            ),
            case(
                "<li>Something<li>else",
                [
                    "\n",
                    "  \N{BULLET} ",
                    "",
                    "Something",
                    "\n",
                    "  \N{BULLET} ",
                    "",
                    "else",
                ],
                id="two_li",
            ),
            case(
                "<li>\n<p>Something</p>\n</li><li>else",
                [
                    "\n",
                    "  \N{BULLET} ",
                    "",
                    "",
                    "",
                    "Something",
                    "",
                    "\n",
                    "  \N{BULLET} ",
                    "",
                    "else",
                ],
                id="two_li_with_li_p_newlines",
            ),
            case(
                "<ul><li>Something<ul><li>nested",
                [
                    "",
                    "  \N{BULLET} ",
                    "",
                    "Something",
                    "",
                    "\n",
                    "    \N{RING OPERATOR} ",
                    "",
                    "nested",
                ],
                id="li_nested",
            ),
            case(
                "<ul><li>Something<ul><li>nested<ul><li>a<ul><li>lot",
                [
                    "",
                    "  \N{BULLET} ",
                    "",
                    "Something",
                    "",
                    "\n",
                    "    \N{RING OPERATOR} ",
                    "",
                    "nested",
                    "",
                    "\n",
                    "      \N{HYPHEN} ",
                    "",
                    "a",
                    "",
                    "\n",
                    "        \N{BULLET} ",
                    "",
                    "lot",
                ],
                id="li_heavily_nested",
            ),
            case("<br>", [], id="br"),
            case("<br/>", [], id="br2"),
            case("<hr>", ["[RULER NOT RENDERED]"], id="hr"),
            case("<hr/>", ["[RULER NOT RENDERED]"], id="hr2"),
            case("<img>", ["[IMAGE NOT RENDERED]"], id="img"),
            case("<img/>", ["[IMAGE NOT RENDERED]"], id="img2"),
            case(
                "<table><thead><tr><th>Firstname</th><th>Lastname</th></tr></thead>"
                "<tbody><tr><td>John</td><td>Doe</td></tr><tr><td>Mary</td><td>Moe"
                "</td></tr></tbody></table>",
                [
                    "┌─",
                    "─────────",
                    "─┬─",
                    "────────",
                    "─┐\n",
                    "│ ",
                    ("table_head", "Firstname"),
                    " │ ",
                    ("table_head", "Lastname"),
                    " │\n",
                    "├─",
                    "─────────",
                    "─┼─",
                    "────────",
                    "─┤\n",
                    "│ ",
                    (None, "John     "),
                    " │ ",
                    (None, "Doe     "),
                    " │\n",
                    "│ ",
                    (None, "Mary     "),
                    " │ ",
                    (None, "Moe     "),
                    " │\n",
                    "└─",
                    "─────────",
                    "─┴─",
                    "────────",
                    "─┘",
                ],
                id="table_default",
            ),
            case(
                '<table><thead><tr><th align="left">Name</th><th align="right">Id'
                '</th></tr></thead><tbody><tr><td align="left">Robert</td>'
                '<td align="right">1</td></tr><tr><td align="left">Mary</td>'
                '<td align="right">100</td></tr></tbody></table>',
                [
                    "┌─",
                    "──────",
                    "─┬─",
                    "───",
                    "─┐\n",
                    "│ ",
                    ("table_head", "Name  "),
                    " │ ",
                    ("table_head", " Id"),
                    " │\n",
                    "├─",
                    "──────",
                    "─┼─",
                    "───",
                    "─┤\n",
                    "│ ",
                    (None, "Robert"),
                    " │ ",
                    (None, "  1"),
                    " │\n",
                    "│ ",
                    (None, "Mary  "),
                    " │ ",
                    (None, "100"),
                    " │\n",
                    "└─",
                    "──────",
                    "─┴─",
                    "───",
                    "─┘",
                ],
                id="table_with_left_and_right_alignments",
            ),
            case(
                '<table><thead><tr><th align="center">Name</th><th align="right">Id'
                '</th></tr></thead><tbody><tr><td align="center">Robert</td>'
                '<td align="right">1</td></tr><tr><td align="center">Mary</td>'
                '<td align="right">100</td></tr></tbody></table>',
                [
                    "┌─",
                    "──────",
                    "─┬─",
                    "───",
                    "─┐\n",
                    "│ ",
                    ("table_head", " Name "),
                    " │ ",
                    ("table_head", " Id"),
                    " │\n",
                    "├─",
                    "──────",
                    "─┼─",
                    "───",
                    "─┤\n",
                    "│ ",
                    (None, "Robert"),
                    " │ ",
                    (None, "  1"),
                    " │\n",
                    "│ ",
                    (None, " Mary "),
                    " │ ",
                    (None, "100"),
                    " │\n",
                    "└─",
                    "──────",
                    "─┴─",
                    "───",
                    "─┘",
                ],
                id="table_with_center_and_right_alignments",
            ),
            case(
                "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Foo</td>"
                "</tr><tr><td>Bar</td></tr><tr><td>Baz</td></tr></tbody></table>",
                [
                    "┌─",
                    "────",
                    "─┐\n",
                    "│ ",
                    ("table_head", "Name"),
                    " │\n",
                    "├─",
                    "────",
                    "─┤\n",
                    "│ ",
                    (None, "Foo "),
                    " │\n",
                    "│ ",
                    (None, "Bar "),
                    " │\n",
                    "│ ",
                    (None, "Baz "),
                    " │\n",
                    "└─",
                    "────",
                    "─┘",
                ],
                id="table_with_single_column",
            ),
            case(
                "<table><thead><tr><th>Column1</th></tr></thead><tbody><tr><td></td>"
                "</tr></tbody></table>",
                [
                    "┌─",
                    "───────",
                    "─┐\n",
                    "│ ",
                    ("table_head", "Column1"),
                    " │\n",
                    "├─",
                    "───────",
                    "─┤\n",
                    "│ ",
                    (None, "       "),
                    " │\n",
                    "└─",
                    "───────",
                    "─┘",
                ],
                id="table_with_the_bare_minimum",
            ),
            case(
                '<time datetime="2020-08-07T04:30:00Z"> Fri, Aug 7 2020, 10:00AM IST'
                "</time>",
                [("msg_time", f" {TIME_MENTION_MARKER} Fri, Aug 7 2020, 10:00 (IST) ")],
                id="time_human_readable_input",
            ),
            case(
                '<time datetime="2020-08-11T16:32:58Z"> 1597163578</time>',
                [
                    (
                        "msg_time",
                        f" {TIME_MENTION_MARKER} Tue, Aug 11 2020, 22:02 (IST) ",
                    )
                ],
                id="time_UNIX_timestamp_input",
            ),
            case(
                # Markdown:
                # ```math
                # some-math
                # ```
                '<span class="katex-display"><span class="katex"><semantics>'
                "<annotation>some-math</annotation></semantics></span></span>",
                [("msg_math", "some-math")],
                id="katex_HTML_response_math_fenced_markdown",
            ),
            case(
                # Markdown:
                # $$ some-math $$
                '<span class="katex"><semantics><annotation>some-math</annotation>'
                "</semantics></span>",
                [("msg_math", "some-math")],
                id="katex_HTML_response_double_$_fenced_markdown",
            ),
            case("<ul><li>text</li></ul>", ["", "  \N{BULLET} ", "", "text"], id="ul"),
            case(
                "<ul>\n<li>text</li>\n</ul>",
                ["", "", "  \N{BULLET} ", "", "text", ""],
                id="ul_with_ul_li_newlines",
            ),
            case("<ol><li>text</li></ol>", ["", "  1. ", "", "text"], id="ol"),
            case(
                "<ol>\n<li>text</li>\n</ol>",
                ["", "", "  1. ", "", "text", ""],
                id="ol_with_ol_li_newlines",
            ),
            case(
                '<ol start="5"><li>text</li></ol>',
                ["", "  5. ", "", "text"],
                id="ol_starting_at_5",
            ),
            # FIXME Strikethrough
            case("<del>text</del>", ["", "text"], id="strikethrough_del"),
            # FIXME inline image?
            case(
                '<div class="message_inline_image">'
                '<a href="x"><img src="x"></a></div>',
                [],
                id="inline_image",
            ),
            # FIXME inline ref?
            case('<div class="message_inline_ref">blah</div>', [], id="inline_ref"),
            case(
                '<span class="emoji">:smile:</span>',
                [("msg_emoji", ":smile:")],
                id="emoji",
            ),
            case(
                '<div class="inline-preview-twitter"',
                ["[TWITTER PREVIEW NOT RENDERED]"],
                id="preview-twitter",
            ),
            case(
                '<img class="emoji" title="zulip"/>',
                [("msg_emoji", ":zulip:")],
                id="zulip_extra_emoji",
            ),
            case(
                '<img class="emoji" title="github"/>',
                [("msg_emoji", ":github:")],
                id="custom_emoji",
            ),
        ],
    )
    def test_soup2markup(self, content, expected_markup, mocker):
        mocker.patch(
            MODULE + ".get_localzone", return_value=pytz.timezone("Asia/Kolkata")
        )
        soup = BeautifulSoup(content, "lxml").find(name="body")
        metadata = dict(
            server_url=SERVER_URL,
            message_links=OrderedDict(),
            time_mentions=list(),
            bq_len=0,
        )

        markup, *_ = MessageBox.soup2markup(soup, metadata)

        assert markup == [""] + expected_markup

    @pytest.mark.parametrize(
        "message, last_message",
        [
            (
                {
                    "sender_id": 1,
                    "display_recipient": "Verona",
                    "sender_full_name": "aaron",
                    "submessages": [],
                    "stream_id": 5,
                    "subject": "Verona2",
                    "id": 37,
                    "subject_links": [],
                    "content": (
                        "<p>It's nice and it feels more modern, but I think"
                        " this will take some time to get used to</p>"
                    ),
                    "timestamp": 1531716583,
                    "sender_realm_str": "zulip",
                    "client": "populate_db",
                    "content_type": "text/html",
                    "reactions": [],
                    "type": "stream",
                    "is_me_message": False,
                    "flags": ["read"],
                    "sender_email": "AARON@zulip.com",
                },
                None,
            ),
            (
                {
                    "sender_id": 5,
                    "display_recipient": [
                        {
                            "is_mirror_dummy": False,
                            "email": "AARON@zulip.com",
                            "id": 1,
                            "full_name": "aaron",
                        },
                        {
                            "is_mirror_dummy": False,
                            "email": "iago@zulip.com",
                            "id": 5,
                            "full_name": "Iago",
                        },
                    ],
                    "sender_full_name": "Iago",
                    "submessages": [],
                    "subject": "",
                    "id": 107,
                    "subject_links": [],
                    "content": "<p>what are you planning to do this week</p>",
                    "timestamp": 1532103879,
                    "sender_realm_str": "zulip",
                    "client": "ZulipTerminal",
                    "content_type": "text/html",
                    "reactions": [],
                    "type": "private",
                    "is_me_message": False,
                    "flags": ["read"],
                    "sender_email": "iago@zulip.com",
                },
                None,
            ),
        ],
    )
    def test_main_view(self, mocker, message, last_message):
        self.model.stream_dict = {
            5: {
                "color": "#bd6",
            },
        }
        MessageBox(message, self.model, last_message)

    @pytest.mark.parametrize(
        "message",
        [
            {
                "id": 4,
                "type": "stream",
                "display_recipient": "Verona",
                "stream_id": 5,
                "subject": "Test topic",
                "is_me_message": True,  # will be overridden by test function.
                "flags": [],
                "content": "",  # will be overridden by test function.
                "reactions": [],
                "sender_full_name": "Alice",
                "timestamp": 1532103879,
            }
        ],
    )
    @pytest.mark.parametrize(
        "content, is_me_message",
        [
            ("<p>/me is excited!</p>", True),
            ("<p>/me is excited! /me is not excited.</p>", True),
            ("<p>This is /me not.</p>", False),
            ("<p>/me is excited!</p>", False),
        ],
    )
    def test_main_view_renders_slash_me(self, mocker, message, content, is_me_message):
        mocker.patch(MODULE + ".urwid.Text")
        message["content"] = content
        message["is_me_message"] = is_me_message
        msg_box = MessageBox(message, self.model, message)
        msg_box.main_view()
        name_index = 11 if is_me_message else -1  # 11 = len(<str><strong>)
        assert (
            msg_box.message["content"].find(message["sender_full_name"]) == name_index
        )

    @pytest.mark.parametrize(
        "message",
        [
            {
                "id": 4,
                "type": "stream",
                "display_recipient": "Verona",
                "stream_id": 5,
                "subject": "Test topic",
                "flags": [],
                "is_me_message": False,
                "content": "<p>what are you planning to do this week</p>",
                "reactions": [],
                "sender_full_name": "Alice",
                "timestamp": 1532103879,
            }
        ],
    )
    @pytest.mark.parametrize(
        "to_vary_in_last_message",
        [
            {"display_recipient": "Verona offtopic"},
            {"subject": "Test topic (previous)"},
            {"type": "private"},
        ],
        ids=[
            "different_stream_before",
            "different_topic_before",
            "PM_before",
        ],
    )
    def test_main_view_generates_stream_header(
        self, mocker, message, to_vary_in_last_message
    ):
        self.model.stream_dict = {
            5: {
                "color": "#bd6",
            },
        }
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3

        assert isinstance(view_components[0], Columns)

        assert isinstance(view_components[0][0], Text)
        assert isinstance(view_components[0][1], Text)
        assert isinstance(view_components[0][2], Divider)

    @pytest.mark.parametrize(
        "message",
        [
            {
                "id": 4,
                "type": "private",
                "sender_email": "iago@zulip.com",
                "sender_id": 5,
                "display_recipient": [
                    {"email": "AARON@zulip.com", "id": 1, "full_name": "aaron"},
                    {"email": "iago@zulip.com", "id": 5, "full_name": "Iago"},
                ],
                "flags": [],
                "is_me_message": False,
                "content": "<p>what are you planning to do this week</p>",
                "reactions": [],
                "sender_full_name": "Alice",
                "timestamp": 1532103879,
            },
        ],
    )
    @pytest.mark.parametrize(
        "to_vary_in_last_message",
        [
            {
                "display_recipient": [
                    {"email": "AARON@zulip.com", "id": 1, "full_name": "aaron"},
                    {"email": "iago@zulip.com", "id": 5, "full_name": "Iago"},
                    {"email": "SE@zulip.com", "id": 6, "full_name": "Someone Else"},
                ],
            },
            {"type": "stream"},
        ],
        ids=[
            "larger_pm_group",
            "stream_before",
        ],
    )
    def test_main_view_generates_PM_header(
        self, mocker, message, to_vary_in_last_message
    ):
        last_message = dict(message, **to_vary_in_last_message)
        msg_box = MessageBox(message, self.model, last_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 3

        assert isinstance(view_components[0], Columns)

        assert isinstance(view_components[0][0], Text)
        assert isinstance(view_components[0][1], Text)
        assert isinstance(view_components[0][2], Divider)

    @pytest.mark.parametrize(
        "msg_narrow, msg_type, assert_header_bar, assert_search_bar",
        [
            ([], 0, f"PTEST {STREAM_TOPIC_SEPARATOR} ", "All messages"),
            ([], 1, "You and ", "All messages"),
            ([], 2, "You and ", "All messages"),
            (
                [["stream", "PTEST"]],
                0,
                f"PTEST {STREAM_TOPIC_SEPARATOR} ",
                ("bar", [("s#bd6", "PTEST")]),
            ),
            (
                [["stream", "PTEST"], ["topic", "b"]],
                0,
                f"PTEST {STREAM_TOPIC_SEPARATOR}",
                ("bar", [("s#bd6", "PTEST"), ("s#bd6", ": topic narrow")]),
            ),
            ([["is", "private"]], 1, "You and ", "All direct messages"),
            ([["is", "private"]], 2, "You and ", "All direct messages"),
            (
                [["pm-with", "boo@zulip.com"]],
                1,
                "You and ",
                "Direct message conversation",
            ),
            (
                [["pm-with", "boo@zulip.com, bar@zulip.com"]],
                2,
                "You and ",
                "Group direct message conversation",
            ),
            (
                [["is", "starred"]],
                0,
                f"PTEST {STREAM_TOPIC_SEPARATOR} ",
                "Starred messages",
            ),
            ([["is", "starred"]], 1, "You and ", "Starred messages"),
            ([["is", "starred"]], 2, "You and ", "Starred messages"),
            ([["is", "starred"], ["search", "FOO"]], 1, "You and ", "Starred messages"),
            (
                [["search", "FOO"]],
                0,
                f"PTEST {STREAM_TOPIC_SEPARATOR} ",
                "All messages",
            ),
            ([["is", "mentioned"]], 0, f"PTEST {STREAM_TOPIC_SEPARATOR} ", "Mentions"),
            ([["is", "mentioned"]], 1, "You and ", "Mentions"),
            ([["is", "mentioned"]], 2, "You and ", "Mentions"),
            ([["is", "mentioned"], ["search", "FOO"]], 1, "You and ", "Mentions"),
        ],
    )
    def test_msg_generates_search_and_header_bar(
        self,
        mocker,
        messages_successful_response,
        msg_type,
        msg_narrow,
        assert_header_bar,
        assert_search_bar,
    ):
        self.model.stream_dict = {
            205: {
                "color": "#bd6",
            },
        }
        self.model.narrow = msg_narrow
        messages = messages_successful_response["messages"]
        current_message = messages[msg_type]
        msg_box = MessageBox(current_message, self.model, messages[0])
        search_bar = msg_box.top_search_bar()
        header_bar = msg_box.recipient_header()

        assert header_bar[0].text.startswith(assert_header_bar)
        assert search_bar.text_to_fill == assert_search_bar

    # Assume recipient (PM/stream/topic) header is unchanged below
    @pytest.mark.parametrize(
        "message",
        [
            {
                "id": 4,
                "type": "stream",
                "display_recipient": "Verona",
                "stream_id": 5,
                "subject": "Test topic",
                "flags": [],
                "is_me_message": False,
                "content": "<p>what are you planning to do this week</p>",
                "reactions": [],
                "sender_full_name": "alice",
                "timestamp": 1532103879,
            }
        ],
    )
    @pytest.mark.parametrize(
        "current_year", [2018, 2019, 2050], ids=["now_2018", "now_2019", "now_2050"]
    )
    @pytest.mark.parametrize(
        "starred_msg",
        ["this", "last", "neither"],
        ids=["this_starred", "last_starred", "no_stars"],
    )
    @pytest.mark.parametrize(
        "expected_header, to_vary_in_last_message",
        [
            (
                [STATUS_INACTIVE, "alice", " ", "DAYDATETIME"],
                {"sender_full_name": "bob"},
            ),
            ([" ", " ", " ", "DAYDATETIME"], {"timestamp": 1532103779}),
            ([STATUS_INACTIVE, "alice", " ", "DAYDATETIME"], {"timestamp": 0}),
        ],
        ids=[
            "show_author_as_authors_different",
            "merge_messages_as_only_slightly_earlier_message",
            "dont_merge_messages_as_much_earlier_message",
        ],
    )
    def test_main_view_content_header_without_header(
        self,
        mocker,
        message,
        expected_header,
        current_year,
        starred_msg,
        to_vary_in_last_message,
    ):
        mocked_date = mocker.patch(MODULE + ".date")
        mocked_date.today.return_value = date(current_year, 1, 1)
        mocked_date.side_effect = lambda *args, **kw: date(*args, **kw)

        output_date_time = "Fri Jul 20 21:54"  # corresponding to timestamp

        self.model.formatted_local_time.side_effect = [  # for this- and last-message
            output_date_time,
            " ",
        ] * 2  # called once in __init__ and then in main_view explicitly

        # The empty dict is responsible for INACTIVE status of test user.
        self.model.user_dict = {}  # called once in main_view explicitly

        stars = {
            msg: ({"flags": ["starred"]} if msg == starred_msg else {})
            for msg in ("this", "last")
        }
        this_msg = dict(message, **stars["this"])
        all_to_vary = dict(to_vary_in_last_message, **stars["last"])
        last_msg = dict(message, **all_to_vary)

        msg_box = MessageBox(this_msg, self.model, last_msg)

        expected_header[2] = output_date_time
        if current_year > 2018:
            expected_header[2] = "2018 - " + expected_header[2]
        expected_header[3] = "*" if starred_msg == "this" else " "

        view_components = msg_box.main_view()

        assert len(view_components) == 2
        assert isinstance(view_components[0], Columns)
        assert [w.text for w in view_components[0].widget_list] == expected_header
        assert isinstance(view_components[1], Padding)

    @pytest.mark.parametrize(
        "to_vary_in_each_message",
        [
            {"sender_full_name": "bob"},
            {"timestamp": 1532103779},
            {"timestamp": 0},
            {},
            {"flags": ["starred"]},
        ],
        ids=[
            "common_author",
            "common_timestamp",
            "common_early_timestamp",
            "common_unchanged_message",
            "both_starred",
        ],
    )
    def test_main_view_compact_output(
        self, mocker, message_fixture, to_vary_in_each_message
    ):
        message_fixture.update({"id": 4})
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, varied_message)
        view_components = msg_box.main_view()
        assert len(view_components) == 1
        assert isinstance(view_components[0], Padding)

    def test_main_view_generates_EDITED_label(
        self, mocker, messages_successful_response
    ):
        messages = messages_successful_response["messages"]
        for message in messages:
            self.model.index["edited_messages"].add(message["id"])
            msg_box = MessageBox(message, self.model, message)
            view_components = msg_box.main_view()

            label = view_components[0].original_widget.contents[0]
            assert label[0].text == "EDITED"
            assert label[1][1] == 7

    @pytest.mark.parametrize(
        "to_vary_in_last_message, update_required",
        [
            ({"sender_full_name": "Unique name (won't be in next message)"}, True),
            ({}, False),
        ],
        ids=[
            "author_field_present",
            "author_field_not_present",
        ],
    )
    def test_update_message_author_status(
        self,
        message_fixture,
        update_required,
        to_vary_in_last_message,
    ):
        message = message_fixture
        last_msg = dict(message, **to_vary_in_last_message)

        msg_box = MessageBox(message, self.model, last_msg)

        assert msg_box.update_message_author_status() == update_required

    @pytest.mark.parametrize("key", keys_for_command("STREAM_MESSAGE"))
    @pytest.mark.parametrize(
        "narrow, expect_to_prefill",
        [
            ([], False),
            ([["stream", "general"]], True),
            ([["stream", "general"], ["topic", "Test"]], True),
            ([["is", "starred"]], False),
            ([["is", "mentioned"]], False),
            ([["is", "private"]], False),
            ([["pm-with", "notification-bot@zulip.com"]], False),
        ],
        ids=[
            "all_messages_narrow",
            "stream_narrow",
            "topic_narrow",
            "private_conversation_narrow",
            "starred_messages_narrow",
            "mentions_narrow",
            "private_messages_narrow",
        ],
    )
    def test_keypress_STREAM_MESSAGE(
        self, mocker, msg_box, widget_size, narrow, expect_to_prefill, key
    ):
        write_box = msg_box.model.controller.view.write_box
        msg_box.model.narrow = narrow
        size = widget_size(msg_box)

        msg_box.keypress(size, key)

        if expect_to_prefill:
            write_box.stream_box_view.assert_called_once_with(
                caption="PTEST",
                stream_id=205,
            )
        else:
            write_box.stream_box_view.assert_called_once_with(0)

    @pytest.mark.parametrize("key", keys_for_command("EDIT_MESSAGE"))
    @pytest.mark.parametrize(
        [
            "to_vary_in_each_message",
            "realm_editing_allowed",
            "msg_body_edit_limit",
            "expect_msg_body_edit_enabled",
            "expect_editing_to_succeed",
            "expect_footer_text",
        ],
        [
            case(
                {"sender_id": 2, "timestamp": 45, "subject": "test"},
                True,
                60,
                {"stream": False, "private": False},
                {"stream": False, "private": False},
                {
                    "stream": (
                        " You can't edit messages sent by other users"
                        " that already have a topic."
                    ),
                    "private": " You can't edit direct messages sent by other users.",
                },
                id="msg_sent_by_other_user_with_topic",
            ),
            case(
                {"sender_id": 1, "timestamp": 1, "subject": "test"},
                True,
                60,
                {"stream": False, "private": False},
                {"stream": True, "private": False},
                {
                    "stream": (
                        " Only topic editing allowed."
                        " Time Limit for editing the message body has been exceeded."
                    ),
                    "private": " Time Limit for editing the message has been exceeded.",
                },
                id="topic_edit_only_after_time_limit",
            ),
            case(
                {"sender_id": 1, "timestamp": 45, "subject": "test"},
                False,
                60,
                {"stream": False, "private": False},
                {"stream": False, "private": False},
                {
                    "stream": " Editing sent message is disabled.",
                    "private": " Editing sent message is disabled.",
                },
                id="realm_editing_not_allowed",
            ),
            case(
                {"sender_id": 1, "timestamp": 45, "subject": "test"},
                True,
                60,
                {"stream": True, "private": True},
                {"stream": True, "private": True},
                {"stream": None, "private": None},
                id="realm_editing_allowed_and_within_time_limit",
            ),
            case(
                {"sender_id": 1, "timestamp": 1, "subject": "test"},
                True,
                0,
                {"stream": True, "private": True},
                {"stream": True, "private": True},
                {"stream": None, "private": None},
                id="no_msg_body_edit_limit",
            ),
            case(
                {"sender_id": 1, "timestamp": 1, "subject": "(no topic)"},
                True,
                60,
                {"stream": False, "private": False},
                {"stream": True, "private": False},
                {
                    "stream": (
                        " Only topic editing allowed."
                        " Time Limit for editing the message body has been exceeded."
                    ),
                    "private": " Time Limit for editing the message has been exceeded.",
                },
                id="msg_sent_by_me_with_no_topic",
            ),
            case(
                {"sender_id": 2, "timestamp": 1, "subject": "(no topic)"},
                True,
                60,
                {"stream": False, "private": False},
                {"stream": True, "private": False},
                {
                    "stream": (
                        " Only topic editing is allowed."
                        " This is someone else's message but with (no topic)."
                    ),
                    "private": " You can't edit direct messages sent by other users.",
                },
                id="msg_sent_by_other_with_no_topic",
            ),
            case(
                {"sender_id": 1, "timestamp": 1, "subject": "(no topic)"},
                False,
                60,
                {"stream": False, "private": False},
                {"stream": False, "private": False},
                {
                    "stream": " Editing sent message is disabled.",
                    "private": " Editing sent message is disabled.",
                },
                id="realm_editing_not_allowed_for_no_topic",
            ),
            case(
                {"sender_id": 1, "timestamp": 45, "subject": "(no topic)"},
                True,
                0,
                {"stream": True, "private": True},
                {"stream": True, "private": True},
                {"stream": None, "private": None},
                id="no_msg_body_edit_limit_with_no_topic",
            ),
        ],
    )
    def test_keypress_EDIT_MESSAGE(
        self,
        mocker,
        message_fixture,
        widget_size,
        to_vary_in_each_message,
        realm_editing_allowed,
        msg_body_edit_limit,
        expect_msg_body_edit_enabled,
        expect_editing_to_succeed,
        expect_footer_text,
        key,
    ):
        if message_fixture["type"] == "private":
            to_vary_in_each_message["subject"] = ""
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        message_type = varied_message["type"]
        msg_box = MessageBox(varied_message, self.model, message_fixture)
        size = widget_size(msg_box)
        msg_box.model.user_id = 1
        msg_box.model.initial_data = {
            "realm_allow_message_editing": realm_editing_allowed,
            "realm_message_content_edit_limit_seconds": msg_body_edit_limit,
        }
        msg_box.model.fetch_raw_message_content.return_value = "Edit this message"
        write_box = msg_box.model.controller.view.write_box
        write_box.msg_edit_state = None
        write_box.msg_body_edit_enabled = None
        report_error = msg_box.model.controller.report_error
        report_warning = msg_box.model.controller.report_warning
        mocker.patch(MODULE + ".time", return_value=100)

        msg_box.keypress(size, key)

        if expect_editing_to_succeed[message_type]:
            assert write_box.msg_edit_state.message_id == varied_message["id"]
            assert write_box.msg_edit_state.old_topic == varied_message["subject"]
            write_box.msg_write_box.set_edit_text.assert_called_once_with(
                "Edit this message"
            )
            assert (
                write_box.msg_body_edit_enabled
                == expect_msg_body_edit_enabled[message_type]
            )
        else:
            assert write_box.msg_edit_state is None
            write_box.msg_write_box.set_edit_text.assert_not_called()
        if expect_footer_text[message_type]:
            if expect_editing_to_succeed[message_type]:
                report_warning.assert_called_once_with(
                    [expect_footer_text[message_type]]
                )
            else:
                report_error.assert_called_once_with([expect_footer_text[message_type]])

    @pytest.mark.parametrize(
        "raw_html, expected_content",
        [
            # Avoid reformatting to preserve quote result readability
            # fmt: off
            case("""<blockquote>
                        <p>A</p>
                    </blockquote>
                    <p>B</p>""",
                 ("{} A\n\n"
                  "B"),
                 id="quoted level 1"),
            case("""<blockquote>
                        <blockquote>
                            <p>A</p>
                        </blockquote>
                        <p>B</p>
                    </blockquote>
                    <p>C</p>""",
                 ("{} {} A\n\n"
                  "{} B\n\n"
                  "C"),
                 id="quoted level 2"),
            case("""<blockquote>
                        <blockquote>
                            <blockquote>
                                <p>A</p>
                            </blockquote>
                            <p>B</p>
                        </blockquote>
                        <p>C</p>
                    </blockquote>
                    <p>D</p>""",
                 ("{} {} {} A\n\n"
                  "{} {} B\n\n"
                  "{} C\n\n"
                  "D"),
                 id="quoted level 3"),
            case("""<blockquote>
                        <p>A<br>
                        B</p>
                    </blockquote>
                    <p>C</p>""",
                 ("{} A\n"
                  "{} B\n\n"
                  "C"),
                 id="multi-line quoting"),
            case("""<blockquote>
                        <p><a href='https://chat.zulip.org/'>czo</a></p>
                    </blockquote>""",
                 ("{} czo [1]\n"),
                 id="quoting with links"),
            case("""<blockquote>
                        <blockquote>
                            <p>A<br>
                            B</p>
                        </blockquote>
                    </blockquote>""",
                 ("{} {} A\n"
                  "{} {} B\n\n"),
                 id="multi-line level 2"),
            case("""<blockquote>
                        <blockquote>
                            <p>A</p>
                        </blockquote>
                        <p>B</p>
                        <blockquote>
                            <p>C</p>
                        </blockquote>
                    </blockquote>""",
                 ("{} {} A\n"
                  "{} B\n"
                  "{} \n"
                  "{} {} C\n\n"),
                 id="quoted level 2-1-2"),
            case("""<p><a href='https://chat.zulip.org/1'>czo</a></p>
                    <blockquote>
                        <p><a href='https://chat.zulip.org/2'>czo</a></p>
                        <blockquote>
                            <p>A<br>
                            B</p>
                        </blockquote>
                        <p>C</p>
                    </blockquote>
                    <p>D</p>""",
                 ("czo [1]\n"
                  "{} czo [2]\n"
                  "{} \n"
                  "{} {} A\n"
                  "{} {} B\n\n"
                  "{} C\n\n"
                  "D"),
                 id="quoted with links level 2"),
            case("""<blockquote>
                        <blockquote>
                            <blockquote>
                                <p>A</p>
                            </blockquote>
                            <p>B</p>
                            <blockquote>
                                <p>C</p>
                            </blockquote>
                            <p>D</p>
                        </blockquote>
                        <p>E</p>
                    </blockquote>
                    <p>F</p>""",
                 ("{} {} {} A\n"
                  "{} {} B\n"
                  "{} {} \n"
                  "{} {} {} C\n\n"
                  "{} {} D\n\n"
                  "{} E\n\n"
                  "F"),
                 id="quoted level 3-2-3"),
            case("""<blockquote>
                        <p>A</p>
                        <blockquote>
                            <blockquote>
                                <blockquote>
                                    <p>B<br>
                                    C</p>
                                </blockquote>
                            </blockquote>
                        </blockquote>
                    </blockquote>""",
                 ("{} A\n"
                  "{} {} {} B\n"
                  "{} {} {} C\n"),
                 id="quoted level 1-3",
                 marks=pytest.mark.xfail(reason="rendered_bug")),
            case("""<blockquote>
                        <p><a href="https://chat.zulip.org/1">czo</a></p>
                        <blockquote>
                            <p><a href="https://chat.zulip.org/2">czo</a></p>
                            <blockquote>
                                <p>A<br>
                                B</p>
                            </blockquote>
                            <p>C</p>
                        </blockquote>
                        <p>D<br>
                        E</p>
                    </blockquote>""",
                 ("{} czo [1]\n"
                  "{} {} czo [2]\n"
                  "{} {} {} A\n"
                  "{} {} {} B\n"
                  "{} {} C\n"
                  "{} D\n"
                  "{} E\n"),
                 id="quoted with links level 1-3-1",
                 marks=pytest.mark.xfail(reason="rendered_bug")),
            # fmt: on
        ],
    )
    def test_transform_content(self, mocker, raw_html, expected_content):
        expected_content = expected_content.replace("{}", QUOTED_TEXT_MARKER)

        content, *_ = MessageBox.transform_content(raw_html, SERVER_URL)

        rendered_text = Text(content)
        assert rendered_text.text == expected_content

    # FIXME This is the same parametrize as MsgInfoView:test_height_reactions
    @pytest.mark.parametrize(
        "to_vary_in_each_message, expected_text, expected_attributes",
        [
            case(
                {
                    "reactions": [
                        {
                            "emoji_name": "thumbs_up",
                            "emoji_code": "1f44d",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "AARON@zulip.com",
                                "full_name": "aaron",
                                "id": 1,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "heart",
                            "emoji_code": "2764",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                    ],
                },
                " :thumbs_up: 1   :zulip: 2   :heart: 1  ",
                [
                    ("reaction", 15),
                    (None, 1),
                    ("reaction_mine", 11),
                    (None, 1),
                    ("reaction", 11),
                ],
            ),
            case(
                {
                    "reactions": [
                        {
                            "emoji_name": "thumbs_up",
                            "emoji_code": "1f44d",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "AARON@zulip.com",
                                "full_name": "aaron",
                                "id": 1,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "heart",
                            "emoji_code": "2764",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                    ],
                },
                " :thumbs_up: Iago   :zulip: You   :heart: Iago  ",
                [
                    ("reaction", 18),
                    (None, 1),
                    ("reaction_mine", 13),
                    (None, 1),
                    ("reaction", 14),
                ],
            ),
            case(
                {
                    "reactions": [
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "AARON@zulip.com",
                                "full_name": "aaron",
                                "id": 1,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "shivam@zulip.com",
                                "full_name": "Shivam",
                                "id": 6,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                    ],
                },
                " :zulip: Iago, Shivam, You  ",
                [
                    ("reaction_mine", 27),
                ],
            ),
            case(
                {
                    "reactions": [
                        {
                            "emoji_name": "heart",
                            "emoji_code": "2764",
                            "user": {
                                "email": "iago@zulip.com",
                                "full_name": "Iago",
                                "id": 5,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "AARON@zulip.com",
                                "full_name": "aaron",
                                "id": 1,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "shivam@zulip.com",
                                "full_name": "Shivam",
                                "id": 6,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                    ],
                },
                " :heart: Iago   :zulip: Shivam, You  ",
                [
                    ("reaction", 14),
                    (None, 1),
                    ("reaction_mine", 21),
                ],
            ),
            case(
                {
                    "reactions": [
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "AARON@zulip.com",
                                "full_name": "aaron",
                                "id": 1,
                            },
                            "reaction_type": "zulip_extra_emoji",
                        },
                        {
                            "emoji_name": "zulip",
                            "emoji_code": "zulip",
                            "user": {
                                "email": "shivam@zulip.com",
                                "full_name": "Shivam",
                                "id": 6,
                            },
                            "reaction_type": "unicode_emoji",
                        },
                    ],
                },
                " :zulip: Shivam, You  ",
                [
                    ("reaction_mine", 21),
                ],
            ),
        ],
    )
    def test_reactions_view(
        self,
        message_fixture,
        to_vary_in_each_message,
        expected_text,
        expected_attributes,
    ):
        self.model.user_id = 1
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, None)
        reactions = to_vary_in_each_message["reactions"]

        reactions_view = msg_box.reactions_view(reactions)

        assert reactions_view.original_widget.text == expected_text
        assert reactions_view.original_widget.attrib == expected_attributes

    @pytest.mark.parametrize(
        "message_links, expected_text, expected_attrib, expected_footlinks_width",
        [
            case(
                OrderedDict(
                    [
                        (
                            "https://github.com/zulip/zulip-terminal/pull/1",
                            ("#T1", 1, True),
                        ),
                    ]
                ),
                "1: https://github.com/zulip/zulip-terminal/pull/1",
                [("msg_link_index", 2), (None, 1), ("msg_link", 46)],
                49,
                id="one_footlink",
            ),
            case(
                OrderedDict(
                    [
                        ("https://foo.com", ("Foo!", 1, True)),
                        ("https://bar.com", ("Bar!", 2, True)),
                    ]
                ),
                "1: https://foo.com\n2: https://bar.com",
                [
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                    (None, 1),
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                ],
                18,
                id="more_than_one_footlink",
            ),
            case(
                OrderedDict(
                    [
                        ("https://example.com", ("https://example.com", 1, False)),
                        ("http://example.com", ("http://example.com", 2, False)),
                    ]
                ),
                None,
                None,
                0,
                id="similar_link_and_text",
            ),
            case(
                OrderedDict(
                    [
                        ("https://foo.com", ("https://foo.com, Text", 1, True)),
                        ("https://bar.com", ("Text, https://bar.com", 2, True)),
                    ]
                ),
                "1: https://foo.com\n2: https://bar.com",
                [
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                    (None, 1),
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                ],
                18,
                id="different_link_and_text",
            ),
            case(
                OrderedDict(
                    [
                        ("https://foo.com", ("Foo!", 1, True)),
                        ("http://example.com", ("example.com", 2, False)),
                        ("https://bar.com", ("Bar!", 3, True)),
                    ]
                ),
                "1: https://foo.com\n3: https://bar.com",
                [
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                    (None, 1),
                    ("msg_link_index", 2),
                    (None, 1),
                    ("msg_link", 15),
                ],
                18,
                id="http_default_scheme",
            ),
        ],
    )
    def test_footlinks_view(
        self, message_links, expected_text, expected_attrib, expected_footlinks_width
    ):
        footlinks, footlinks_width = MessageBox.footlinks_view(
            message_links,
            maximum_footlinks=3,
            padded=True,
            wrap="ellipsis",
        )

        if expected_text:
            assert footlinks.original_widget.text == expected_text
            assert footlinks.original_widget.attrib == expected_attrib
            assert footlinks_width == expected_footlinks_width
        else:
            assert footlinks is None
            assert not hasattr(footlinks, "original_widget")

    @pytest.mark.parametrize(
        "maximum_footlinks, expected_instance",
        [
            (0, type(None)),
            (1, Padding),
            (3, Padding),
        ],
    )
    def test_footlinks_limit(self, maximum_footlinks, expected_instance):
        message_links = OrderedDict(
            [
                ("https://github.com/zulip/zulip-terminal", ("ZT", 1, True)),
            ]
        )

        footlinks, _ = MessageBox.footlinks_view(
            message_links,
            maximum_footlinks=maximum_footlinks,
            padded=True,
            wrap="ellipsis",
        )

        assert isinstance(footlinks, expected_instance)

    @pytest.mark.parametrize(
        "key", keys_for_command("ENTER"), ids=lambda param: f"left_click-key:{param}"
    )
    def test_mouse_event_left_click(
        self, mocker, msg_box, key, widget_size, compose_box_is_open
    ):
        size = widget_size(msg_box)
        col = 1
        row = 1
        focus = mocker.Mock()
        mocker.patch.object(msg_box, "keypress")
        msg_box.model = mocker.Mock()
        msg_box.model.controller.is_in_editor_mode.return_value = compose_box_is_open

        msg_box.mouse_event(size, "mouse press", 1, col, row, focus)

        if compose_box_is_open:
            msg_box.keypress.assert_not_called()
        else:
            msg_box.keypress.assert_called_once_with(size, key)
