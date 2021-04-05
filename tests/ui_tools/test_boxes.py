import datetime
from collections import OrderedDict, defaultdict

import pytest
import pytz
from bs4 import BeautifulSoup
from pytest import param as case
from urwid import Columns, Divider, Padding, Text

from zulipterminal.config.keys import keys_for_command, primary_key_for_command
from zulipterminal.config.symbols import (
    INVALID_MARKER,
    QUOTED_TEXT_MARKER,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
    STREAM_TOPIC_SEPARATOR,
    TIME_MENTION_MARKER,
)
from zulipterminal.ui_tools.boxes import MessageBox, PanelSearchBox, WriteBox


VIEWS = "zulipterminal.ui_tools.views"
MESSAGEBOX = "zulipterminal.ui_tools.boxes.MessageBox"
BOXES = "zulipterminal.ui_tools.boxes"
SERVER_URL = "https://chat.zulip.zulip"


@pytest.fixture(params=[True, False], ids=["ignore_mouse_click", "handle_mouse_click"])
def compose_box_is_open(request):
    return request.param


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
            msg_box = MessageBox(message, self.model, None)

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
        mocker.patch(MESSAGEBOX + "._is_private_message_to_self", return_value=True)
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
            case(
                '<span class="user-group-mention">@A Group',
                [("msg_mention", "@A Group")],
                id="group-mention",
            ),
            case("<code>some code", [("msg_code", "some code")], id="code"),
            case(
                '<div class="codehilite">some code',
                [("msg_code", "some code")],
                id="codehilite",
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
                '<span class="katex-display">some-math</span>', ["some-math"], id="math"
            ),
            case('<span class="katex">some-math</span>', ["some-math"], id="math2"),
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
            BOXES + ".get_localzone", return_value=pytz.timezone("Asia/Kolkata")
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
        msg_box = MessageBox(message, self.model, last_message)

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
        mocker.patch(VIEWS + ".urwid.Text")
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
            ([["is", "private"]], 1, "You and ", "All private messages"),
            ([["is", "private"]], 2, "You and ", "All private messages"),
            ([["pm_with", "boo@zulip.com"]], 1, "You and ", "Private conversation"),
            (
                [["pm_with", "boo@zulip.com, bar@zulip.com"]],
                2,
                "You and ",
                "Group private conversation",
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
        header_bar = msg_box.top_header_bar(msg_box)

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
            (["alice", " ", "DAYDATETIME"], {"sender_full_name": "bob"}),
            ([" ", " ", "DAYDATETIME"], {"timestamp": 1532103779}),
            (["alice", " ", "DAYDATETIME"], {"timestamp": 0}),
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
        date = mocker.patch("zulipterminal.ui_tools.boxes.date")
        date.today.return_value = datetime.date(current_year, 1, 1)
        date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

        output_date_time = "Fri Jul 20 21:54"  # corresponding to timestamp

        self.model.formatted_local_time.side_effect = [  # for this- and last-message
            output_date_time,
            " ",
        ] * 2  # called once in __init__ and then in main_view explicitly

        stars = {
            msg: ({"flags": ["starred"]} if msg == starred_msg else {})
            for msg in ("this", "last")
        }
        this_msg = dict(message, **stars["this"])
        all_to_vary = dict(to_vary_in_last_message, **stars["last"])
        last_msg = dict(message, **all_to_vary)

        msg_box = MessageBox(this_msg, self.model, last_msg)

        expected_header[1] = output_date_time
        if current_year > 2018:
            expected_header[1] = "2018 - " + expected_header[1]
        expected_header[2] = "*" if starred_msg == "this" else " "

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
            ([["pm_with", "notification-bot@zulip.com"]], False),
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
            "msg_body_edit_enabled",
            "msg_body_edit_limit",
            "expect_editing_to_succeed",
        ],
        [
            ({"sender_id": 2, "timestamp": 45}, True, True, 60, False),
            ({"sender_id": 1, "timestamp": 1}, True, False, 60, True),
            ({"sender_id": 1, "timestamp": 45}, False, True, 60, False),
            ({"sender_id": 1, "timestamp": 45}, True, True, 60, True),
            ({"sender_id": 1, "timestamp": 1}, True, True, 0, True),
        ],
        ids=[
            "msg_sent_by_other_user",
            "topic_edit_only_after_time_limit",
            "editing_not_allowed",
            "all_conditions_met",
            "no_msg_body_edit_limit",
        ],
    )
    def test_keypress_EDIT_MESSAGE(
        self,
        mocker,
        message_fixture,
        widget_size,
        expect_editing_to_succeed,
        to_vary_in_each_message,
        realm_editing_allowed,
        msg_body_edit_enabled,
        msg_body_edit_limit,
        key,
    ):
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, message_fixture)
        size = widget_size(msg_box)
        msg_box.model.user_id = 1
        msg_box.model.initial_data = {
            "realm_allow_message_editing": realm_editing_allowed,
            "realm_message_content_edit_limit_seconds": msg_body_edit_limit,
        }
        msg_box.model.client.get_raw_message.return_value = {
            "raw_content": "Edit this message"
        }
        write_box = msg_box.model.controller.view.write_box
        write_box.msg_edit_id = None
        write_box.msg_body_edit_enabled = None
        mocker.patch("zulipterminal.ui_tools.boxes.time", return_value=100)
        # private messages cannot be edited after time-limit, if there is one.
        if (
            varied_message["type"] == "private"
            and varied_message["timestamp"] == 1
            and msg_body_edit_limit > 0
        ):
            expect_editing_to_succeed = False

        msg_box.keypress(size, key)

        if expect_editing_to_succeed:
            assert write_box.msg_edit_id == varied_message["id"]
            write_box.msg_write_box.set_edit_text.assert_called_once_with(
                "Edit this message"
            )
            assert write_box.msg_body_edit_enabled == msg_body_edit_enabled
        else:
            assert write_box.msg_edit_id is None
            write_box.msg_write_box.set_edit_text.assert_not_called()

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
        "to_vary_in_each_message",
        [
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
                ]
            }
        ],
    )
    def test_reactions_view(self, message_fixture, to_vary_in_each_message):
        self.model.user_id = 1
        varied_message = dict(message_fixture, **to_vary_in_each_message)
        msg_box = MessageBox(varied_message, self.model, None)
        reactions = to_vary_in_each_message["reactions"]

        reactions_view = msg_box.reactions_view(reactions)

        assert reactions_view.original_widget.text == (
            ":heart: 1 :thumbs_up: 1 :zulip: 2 "
        )
        assert reactions_view.original_widget.attrib == [
            ("reaction", 9),
            (None, 1),
            ("reaction", 13),
            (None, 1),
            ("reaction_mine", 9),
        ]

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
        mocker.patch(BOXES + ".keys_for_command", return_value=[key])
        mocker.patch.object(msg_box, "keypress")
        msg_box.model = mocker.Mock()
        msg_box.model.controller.is_in_editor_mode.return_value = compose_box_is_open

        msg_box.mouse_event(size, "mouse press", 1, col, row, focus)

        if compose_box_is_open:
            msg_box.keypress.assert_not_called()
        else:
            msg_box.keypress.assert_called_once_with(size, key)


class TestWriteBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()

    @pytest.fixture()
    def write_box(
        self,
        mocker,
        users_fixture,
        user_groups_fixture,
        streams_fixture,
        unicode_emojis,
        user_dict,
    ):
        self.view.model.active_emoji_data = unicode_emojis
        write_box = WriteBox(self.view)
        write_box.view.users = users_fixture
        write_box.model.user_dict = user_dict
        write_box.model.max_stream_name_length = 60
        write_box.model.max_topic_length = 60
        write_box.model.max_message_length = 10000
        write_box.model.user_group_names = [
            groups["name"] for groups in user_groups_fixture
        ]

        write_box.view.pinned_streams = []
        write_box.view.unpinned_streams = sorted(
            [{"name": stream["name"]} for stream in streams_fixture],
            key=lambda stream: stream["name"].lower(),
        )

        return write_box

    def test_init(self, write_box):
        assert write_box.model == self.view.model
        assert write_box.view == self.view
        assert write_box.msg_edit_id is None

    def test_not_calling_typing_method_without_recipients(self, mocker, write_box):
        write_box.model.send_typing_status_by_user_ids = mocker.Mock()
        write_box.private_box_view(emails=[], recipient_user_ids=[])
        # Set idle_status_tracking to True to avoid setting off the
        # idleness tracker function.
        write_box.idle_status_tracking = True

        # Changing the edit_text triggers on_type_send_status.
        write_box.msg_write_box.edit_text = "random text"

        assert not write_box.model.send_typing_status_by_user_ids.called

    @pytest.mark.parametrize("key", keys_for_command("SEND_MESSAGE"))
    def test_not_calling_send_private_message_without_recipients(
        self, key, mocker, write_box, widget_size
    ):
        write_box.model.send_private_message = mocker.Mock()
        write_box.private_box_view(emails=[], recipient_user_ids=[])
        write_box.msg_write_box.edit_text = "random text"

        size = widget_size(write_box)
        write_box.keypress(size, key)

        assert not write_box.model.send_private_message.called

    @pytest.mark.parametrize(
        "text, state",
        [
            ("Plain Text", 0),
            ("Plain Text", 1),
        ],
    )
    def test_generic_autocomplete_no_prefix(self, mocker, write_box, text, state):
        return_val = write_box.generic_autocomplete(text, state)
        assert return_val == text
        write_box.view.set_typeahead_footer.assert_not_called()

    @pytest.mark.parametrize(
        "text, state, footer_text",
        [
            # no-text mentions
            (
                "@",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                    "Group 1",
                    "Group 2",
                    "Group 3",
                    "Group 4",
                ],
            ),
            ("@*", 0, ["Group 1", "Group 2", "Group 3", "Group 4"]),
            (
                "@**",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            # mentions
            (
                "@Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@**Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@_Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            ("@_*Human", None, []),  # NOTE: Optional single star fails
            (
                "@_**Human",
                0,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            (
                "@Human",
                None,
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
            ),
            ("@NoMatch", None, []),
            # streams
            (
                "#Stream",
                0,
                ["Stream 1", "Stream 2", "Secret stream", "Some general stream"],
            ),
            ("#*Stream", None, []),  # NOTE: Optional single star fails
            (
                "#**Stream",
                0,
                ["Stream 1", "Stream 2", "Secret stream", "Some general stream"],
            ),  # Optional 2-stars
            (
                "#Stream",
                None,
                ["Stream 1", "Stream 2", "Secret stream", "Some general stream"],
            ),
            ("#NoMatch", None, []),
            # emojis
            (":smi", 0, ["smile", "smiley", "smirk"]),
            (":smi", None, ["smile", "smiley", "smirk"]),
            (":NoMatch", None, []),
        ],
    )
    def test_generic_autocomplete_set_footer(
        self, mocker, write_box, state, footer_text, text
    ):
        write_box.view.set_typeahead_footer = mocker.patch(
            "zulipterminal.ui.View.set_typeahead_footer"
        )
        write_box.generic_autocomplete(text, state)

        write_box.view.set_typeahead_footer.assert_called_once_with(
            footer_text, state, False
        )

    @pytest.mark.parametrize(
        "text, state, required_typeahead",
        [
            ("@Human", 0, "@**Human Myself**"),
            ("@Human", 1, "@**Human 1**"),
            ("@Human", 2, "@**Human 2**"),
            ("@Human", 3, "@**Human Duplicate|13**"),
            ("@Human", 4, "@**Human Duplicate|14**"),
            ("@Human", -1, "@**Human Duplicate|14**"),
            ("@Human", -2, "@**Human Duplicate|13**"),
            ("@Human", -3, "@**Human 2**"),
            ("@Human", -4, "@**Human 1**"),
            ("@Human", -5, "@**Human Myself**"),
            ("@Human", -6, None),
            ("@_Human", 0, "@_**Human Myself**"),
            ("@_Human", 1, "@_**Human 1**"),
            ("@_Human", 2, "@_**Human 2**"),
            ("@_Human", 3, "@_**Human Duplicate|13**"),
            ("@_Human", 4, "@_**Human Duplicate|14**"),
            ("@H", 1, "@**Human 1**"),
            ("@Hu", 1, "@**Human 1**"),
            ("@Hum", 1, "@**Human 1**"),
            ("@Huma", 1, "@**Human 1**"),
            ("@Human", 1, "@**Human 1**"),
            ("@Human 1", 0, "@**Human 1**"),
            ("@_H", 1, "@_**Human 1**"),
            ("@_Hu", 1, "@_**Human 1**"),
            ("@_Hum", 1, "@_**Human 1**"),
            ("@_Huma", 1, "@_**Human 1**"),
            ("@_Human", 1, "@_**Human 1**"),
            ("@_Human 1", 0, "@_**Human 1**"),
            ("@Group", 0, "@*Group 1*"),
            ("@Group", 1, "@*Group 2*"),
            ("@G", 0, "@*Group 1*"),
            ("@Gr", 0, "@*Group 1*"),
            ("@Gro", 0, "@*Group 1*"),
            ("@Grou", 0, "@*Group 1*"),
            ("@G", 1, "@*Group 2*"),
            ("@Gr", 1, "@*Group 2*"),
            ("@Gro", 1, "@*Group 2*"),
            ("@Grou", 1, "@*Group 2*"),
            # Expected sequence of autocompletes from '@'
            ("@", 0, "@**Human Myself**"),
            ("@", 1, "@**Human 1**"),
            ("@", 2, "@**Human 2**"),
            ("@", 3, "@**Human Duplicate|13**"),
            ("@", 4, "@**Human Duplicate|14**"),
            ("@", 5, "@*Group 1*"),
            ("@", 6, "@*Group 2*"),
            ("@", 7, "@*Group 3*"),
            ("@", 8, "@*Group 4*"),
            ("@", 9, None),  # Reached last match
            ("@", 10, None),  # Beyond end
            # Expected sequence of autocompletes from '@**' (no groups)
            ("@**", 0, "@**Human Myself**"),
            ("@**", 1, "@**Human 1**"),
            ("@**", 2, "@**Human 2**"),
            ("@", 3, "@**Human Duplicate|13**"),
            ("@", 4, "@**Human Duplicate|14**"),
            ("@**", 5, None),  # Reached last match
            ("@**", 6, None),  # Beyond end
            # Expected sequence of autocompletes from '@*' (only groups)
            ("@*", 0, "@*Group 1*"),
            ("@*", 1, "@*Group 2*"),
            ("@*", 2, "@*Group 3*"),
            ("@*", 3, "@*Group 4*"),
            ("@*", 4, None),  # Reached last match
            ("@*", 5, None),  # Beyond end
            # Expected sequence of autocompletes from '@_'
            ("@_", 0, "@_**Human Myself**"),  # NOTE: No silent group mention
            ("@_", 1, "@_**Human 1**"),
            ("@_", 2, "@_**Human 2**"),
            ("@_", 3, "@_**Human Duplicate|13**"),
            ("@_", 4, "@_**Human Duplicate|14**"),
            ("@_", 5, None),  # Reached last match
            ("@_", 6, None),  # Beyond end
            ("@_", -1, "@_**Human Duplicate|14**"),
            # Complex autocomplete prefixes.
            ("(@H", 0, "(@**Human Myself**"),
            ("(@H", 1, "(@**Human 1**"),
            ("-@G", 0, "-@*Group 1*"),
            ("-@G", 1, "-@*Group 2*"),
            ("_@H", 0, "_@**Human Myself**"),
            ("_@G", 0, "_@*Group 1*"),
            ("@@H", 0, "@@**Human Myself**"),
            (":@H", 0, ":@**Human Myself**"),
            ("#@H", 0, "#@**Human Myself**"),
            ("@_@H", 0, "@_@**Human Myself**"),
            (">@_H", 0, ">@_**Human Myself**"),
            (">@_H", 1, ">@_**Human 1**"),
            ("@_@_H", 0, "@_@_**Human Myself**"),
            ("@@_H", 0, "@@_**Human Myself**"),
            (":@_H", 0, ":@_**Human Myself**"),
            ("#@_H", 0, "#@_**Human Myself**"),
            ("@@_H", 0, "@@_**Human Myself**"),
            ("@@_*H", 0, None),  # Optional single star fails
            ("@@_**H", 0, "@@_**Human Myself**"),  # Optional stars
        ],
    )
    def test_generic_autocomplete_mentions(
        self, write_box, text, required_typeahead, state
    ):
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, state, required_typeahead, recipients",
        [
            ("@", 0, "@**Human 2**", [12]),
            ("@", 1, "@**Human Myself**", [12]),
            ("@", 2, "@**Human 1**", [12]),
            ("@", -1, "@*Group 4*", [12]),
            ("@", 0, "@**Human 1**", [11, 12]),
            ("@", 1, "@**Human 2**", [11, 12]),
            ("@", 2, "@**Human Myself**", [11, 12]),
            ("@", -1, "@*Group 4*", [11, 12]),
        ],
    )
    def test_generic_autocomplete_mentions_subscribers(
        self, write_box, text, required_typeahead, state, recipients
    ):
        write_box.recipient_user_ids = recipients
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, expected_distinct_prefix",
        # Add 3 different lists of tuples, with each tuple containing a combination
        # of the text to be autocompleted and the corresponding typeahead prefix to
        # be added to the typeahead suggestions. Only the "@" case has to be ignored
        # while building the parameters, because it includes group suggestions too.
        [("@" + "Human"[: index + 1], "@") for index in range(len("Human"))]
        + [("@**" + "Human"[:index], "@") for index in range(len("Human") + 1)]
        + [("@_" + "Human"[:index], "@_") for index in range(len("Human") + 1)],
    )
    def test_generic_autocomplete_user_mentions(
        self, write_box, mocker, text, expected_distinct_prefix, state=1
    ):
        _process_typeaheads = mocker.patch(BOXES + ".WriteBox._process_typeaheads")

        write_box.generic_autocomplete(text, state)

        matching_users = [
            "Human Myself",
            "Human 1",
            "Human 2",
            "Human Duplicate",
            "Human Duplicate",
        ]
        distinct_matching_users = [
            expected_distinct_prefix + "**Human Myself**",
            expected_distinct_prefix + "**Human 1**",
            expected_distinct_prefix + "**Human 2**",
            expected_distinct_prefix + "**Human Duplicate|13**",
            expected_distinct_prefix + "**Human Duplicate|14**",
        ]
        _process_typeaheads.assert_called_once_with(
            distinct_matching_users, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, state, required_typeahead, to_pin",
        [
            # With no streams pinned.
            ("#Stream", 0, "#**Stream 1**", []),  # 1st-word startswith match.
            ("#Stream", 1, "#**Stream 2**", []),  # 1st-word startswith match.
            ("#Stream", 2, "#**Secret stream**", []),  # 2nd-word startswith match.
            ("#Stream", 3, "#**Some general stream**", []),  # 3rd-word startswith.
            ("#S", 0, "#**Secret stream**", []),  # 1st-word startswith match.
            ("#S", 1, "#**Some general stream**", []),  # 1st-word startswith.
            ("#S", 2, "#**Stream 1**", []),  # 1st-word startswith match.
            ("#S", 3, "#**Stream 2**", []),  # 1st-word startswith match.
            ("#S", -1, "#**Stream 2**", []),
            ("#S", -2, "#**Stream 1**", []),
            ("#S", -3, "#**Some general stream**", []),
            ("#S", -4, "#**Secret stream**", []),
            ("#S", -5, None, []),
            ("#So", 0, "#**Some general stream**", []),
            ("#So", 1, None, []),
            ("#Se", 0, "#**Secret stream**", []),
            ("#Se", 1, None, []),
            ("#St", 0, "#**Stream 1**", []),
            ("#St", 1, "#**Stream 2**", []),
            ("#g", 0, "#**Some general stream**", []),
            ("#g", 1, None, []),
            ("#Stream 1", 0, "#**Stream 1**", []),  # Complete match.
            ("#nomatch", 0, None, []),
            ("#ene", 0, None, []),
            # Complex autocomplete prefixes.
            ("[#Stream", 0, "[#**Stream 1**", []),
            ("(#Stream", 1, "(#**Stream 2**", []),
            ("@#Stream", 0, "@#**Stream 1**", []),
            ("@_#Stream", 0, "@_#**Stream 1**", []),
            (":#Stream", 0, ":#**Stream 1**", []),
            ("##Stream", 0, "##**Stream 1**", []),
            ("##*Stream", 0, None, []),  # NOTE: Optional single star fails
            ("##**Stream", 0, "##**Stream 1**", []),  # Optional 2-stars
            # With 'Secret stream' pinned.
            (
                "#Stream",
                0,
                "#**Secret stream**",
                ["Secret stream"],
            ),  # 2nd-word startswith match (pinned).
            (
                "#Stream",
                1,
                "#**Stream 1**",
                ["Secret stream"],
            ),  # 1st-word startswith match (unpinned).
            (
                "#Stream",
                2,
                "#**Stream 2**",
                ["Secret stream"],
            ),  # 1st-word startswith match (unpinned).
            (
                "#Stream",
                3,
                "#**Some general stream**",
                ["Secret stream"],
            ),  # 3rd-word starstwith match (unpinned).
            # With 'Stream 1' and 'Secret stream' pinned.
            ("#Stream", 0, "#**Stream 1**", ["Secret stream", "Stream 1"]),
            ("#Stream", 1, "#**Secret stream**", ["Secret stream", "Stream 1"]),
            ("#Stream", 2, "#**Stream 2**", ["Secret stream", "Stream 1"]),
            ("#Stream", 3, "#**Some general stream**", ["Secret stream", "Stream 1"]),
        ],
    )
    def test_generic_autocomplete_streams(
        self, write_box, text, state, required_typeahead, to_pin
    ):
        streams_to_pin = [{"name": stream_name} for stream_name in to_pin]
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, state, required_typeahead",
        [
            (":rock_o", 0, ":rock_on:"),
            (":rock_o", 1, None),
            (":rock_o", -1, ":rock_on:"),
            (":rock_o", -2, None),
            (":smi", 0, ":smile:"),
            (":smi", 1, ":smiley:"),
            (":smi", 2, ":smirk:"),
            (":jo", 0, ":joker:"),
            (":jo", 1, ":joy_cat:"),
            (":jok", 0, ":joker:"),
            (":", 0, ":happy:"),
            (":", 1, ":joker:"),
            (":", -2, ":smiley:"),
            (":", -1, ":smirk:"),
            (":nomatch", 0, None),
            (":nomatch", -1, None),
            # Complex autocomplete prefixes.
            ("(:smi", 0, "(:smile:"),
            ("&:smi", 1, "&:smiley:"),
            ("@:smi", 0, "@:smile:"),
            ("@_:smi", 0, "@_:smile:"),
            ("#:smi", 0, "#:smile:"),
        ],
    )
    def test_generic_autocomplete_emojis(
        self, write_box, text, mocker, state, required_typeahead
    ):
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(
        "text, matching_users, matching_users_info",
        [
            (
                "",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Human Myself <FOOBOO@gmail.com>",
                    "Human 1 <person1@example.com>",
                    "Human 2 <person2@example.com>",
                    "Human Duplicate <personduplicate1@example.com>",
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            ("My", ["Human Myself"], ["Human Myself <FOOBOO@gmail.com>"]),
        ],
        ids=[
            "no_search_text",
            "single_word_search_text",
        ],
    )
    def test__to_box_autocomplete(
        self, mocker, write_box, text, matching_users, matching_users_info, state=1
    ):
        _process_typeaheads = mocker.patch(BOXES + ".WriteBox._process_typeaheads")

        write_box._to_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_users_info, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Hu", "Human Myself <FOOBOO@gmail.com>"),
            ("Human M", "Human Myself <FOOBOO@gmail.com>"),
            ("Human Myself <FOOBOO", "Human Myself <FOOBOO@gmail.com>"),
        ],
    )
    def test__to_box_autocomplete_with_spaces(
        self, write_box, text, expected_text, widget_size
    ):
        write_box.private_box_view(
            emails=["feedback@zulip.com"], recipient_user_ids=[1]
        )
        write_box.to_write_box.set_edit_text(text)
        write_box.to_write_box.set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.to_write_box.edit_text == expected_text

    @pytest.mark.parametrize(
        "text, matching_users, matching_users_info",
        [
            (
                "Welcome Bot <welcome-bot@zulip.com>, Human",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Myself <FOOBOO@gmail.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human 1 <person1@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human 2 <person2@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Duplicate <personduplicate1@example.com>",
                    "Welcome Bot <welcome-bot@zulip.com>, "
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            (
                "Welcome Bot <welcome-bot@zulip.com>, Notification Bot "
                "<notification-bot@zulip.com>, person2",
                ["Human 2"],
                [
                    "Welcome Bot <welcome-bot@zulip.com>, Notification Bot "
                    "<notification-bot@zulip.com>, Human 2 <person2@example.com>"
                ],
            ),
            (
                "Email Gateway <emailgateway@zulip.com>,Human",
                [
                    "Human Myself",
                    "Human 1",
                    "Human 2",
                    "Human Duplicate",
                    "Human Duplicate",
                ],
                [
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Myself <FOOBOO@gmail.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human 1 <person1@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human 2 <person2@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Duplicate <personduplicate1@example.com>",
                    "Email Gateway <emailgateway@zulip.com>, "
                    "Human Duplicate <personduplicate2@example.com>",
                ],
            ),
            (
                "Human 1 <person1@example.com>, Notification Bot "
                "<notification-bot@zulip.com>,person2",
                ["Human 2"],
                [
                    "Human 1 <person1@example.com>, Notification Bot "
                    "<notification-bot@zulip.com>, Human 2 <person2@example.com>"
                ],
            ),
        ],
        ids=[
            "name_search_text_with_space_after_separator",
            "email_search_text_with_space_after_separator",
            "name_search_text_without_space_after_separator",
            "email_search_text_without_space_after_separator",
        ],
    )
    def test__to_box_autocomplete_with_multiple_recipients(
        self, mocker, write_box, text, matching_users, matching_users_info, state=1
    ):
        _process_typeaheads = mocker.patch(BOXES + ".WriteBox._process_typeaheads")

        write_box._to_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_users_info, state, matching_users
        )

    @pytest.mark.parametrize(
        "text, state, to_pin, matching_streams",
        [
            (
                "",
                1,
                [],
                ["Secret stream", "Some general stream", "Stream 1", "Stream 2"],
            ),
            (
                "",
                1,
                ["Stream 2"],
                ["Stream 2", "Secret stream", "Some general stream", "Stream 1"],
            ),
            (
                "St",
                1,
                [],
                ["Stream 1", "Stream 2", "Secret stream", "Some general stream"],
            ),
            (
                "St",
                1,
                ["Stream 2"],
                ["Stream 2", "Stream 1", "Secret stream", "Some general stream"],
            ),
        ],
        ids=[
            "no_search_text",
            "no_search_text_with_pinned_stream",
            "single_word_search_text",
            "single_word_search_text_with_pinned_stream",
        ],
    )
    def test__stream_box_autocomplete(
        self, mocker, write_box, text, state, to_pin, matching_streams
    ):
        streams_to_pin = [{"name": stream_name} for stream_name in to_pin]
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        _process_typeaheads = mocker.patch(BOXES + ".WriteBox._process_typeaheads")

        write_box._stream_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_streams, state, matching_streams
        )

    @pytest.mark.parametrize(
        "stream_name, stream_id, is_valid_stream, expected_marker, expected_color",
        [
            ("Secret stream", 99, True, STREAM_MARKER_PRIVATE, "#ccc"),
            ("Stream 1", 1, True, STREAM_MARKER_PUBLIC, "#b0a5fd"),
            ("Stream 0", 0, False, INVALID_MARKER, "general_bar"),
        ],
        ids=[
            "private_stream",
            "public_stream",
            "invalid_stream_name",
        ],
    )
    def test__set_stream_write_box_style_markers(
        self,
        write_box,
        stream_id,
        stream_name,
        is_valid_stream,
        expected_marker,
        stream_dict,
        mocker,
        expected_color,
    ):
        # FIXME: Refactor when we have ~ Model.is_private_stream
        write_box.model.stream_dict = stream_dict
        write_box.model.is_valid_stream.return_value = is_valid_stream
        write_box.model.stream_id_from_name.return_value = stream_id

        write_box.stream_box_view(stream_id)

        write_box._set_stream_write_box_style(write_box, stream_name)

        stream_marker = write_box.header_write_box[write_box.FOCUS_HEADER_PREFIX_STREAM]

        assert stream_marker.text == expected_marker
        assert stream_marker.attrib[0][0] == expected_color

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Som", "Some general stream"),
            ("Some gen", "Some general stream"),
        ],
    )
    def test__stream_box_autocomplete_with_spaces(
        self, mocker, write_box, widget_size, text, expected_text
    ):
        mocker.patch(BOXES + ".WriteBox._set_stream_write_box_style")
        write_box.stream_box_view(1000)
        stream_focus = write_box.FOCUS_HEADER_BOX_STREAM
        write_box.header_write_box[stream_focus].set_edit_text(text)
        write_box.header_write_box[stream_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = stream_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.header_write_box[stream_focus].edit_text == expected_text

    @pytest.mark.parametrize(
        "text, matching_topics",
        [
            ("", ["Topic 1", "This is a topic", "Hello there!"]),
            ("Th", ["This is a topic"]),
        ],
        ids=[
            "no_search_text",
            "single_word_search_text",
        ],
    )
    def test__topic_box_autocomplete(
        self, mocker, write_box, text, topics, matching_topics, state=1
    ):
        write_box.model.topics_in_stream.return_value = topics
        _process_typeaheads = mocker.patch(BOXES + ".WriteBox._process_typeaheads")

        write_box._topic_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(
            matching_topics, state, matching_topics
        )

    @pytest.mark.parametrize(
        "text, expected_text",
        [
            ("Th", "This is a topic"),
            ("This i", "This is a topic"),
        ],
    )
    def test__topic_box_autocomplete_with_spaces(
        self, mocker, write_box, widget_size, text, expected_text, topics
    ):
        mocker.patch(BOXES + ".WriteBox._set_stream_write_box_style")
        write_box.stream_box_view(1000)
        write_box.model.topics_in_stream.return_value = topics
        topic_focus = write_box.FOCUS_HEADER_BOX_TOPIC
        write_box.header_write_box[topic_focus].set_edit_text(text)
        write_box.header_write_box[topic_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = topic_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command("AUTOCOMPLETE"))

        assert write_box.header_write_box[topic_focus].edit_text == expected_text

    @pytest.mark.parametrize(
        "suggestions, state, expected_state, expected_typeahead, is_truncated",
        [
            (["zero", "one", "two"], 1, 1, "*one*", False),
            (["zero", "one", "two"] * 4, 1, 1, "*one*", True),
            (["zero", "one", "two"], None, None, None, False),
            (["zero", "one", "two"], 5, None, None, False),
            (["zero", "one", "two"], -5, None, None, False),
        ],
        ids=[
            "fewer_than_10_typeaheads",
            "more_than_10_typeaheads",
            "invalid_state-None",
            "invalid_state-greater_than_possible_index",
            "invalid_state-less_than_possible_index",
        ],
    )
    def test__process_typeaheads(
        self,
        write_box,
        suggestions,
        state,
        expected_state,
        expected_typeahead,
        is_truncated,
        mocker,
    ):
        write_box.view.set_typeahead_footer = mocker.patch(
            "zulipterminal.ui.View.set_typeahead_footer"
        )
        # Use an example formatting to differentiate between
        # typeaheads and suggestions.
        typeaheads = [f"*{s}*" for s in suggestions]

        typeahead = write_box._process_typeaheads(typeaheads, state, suggestions)

        assert typeahead == expected_typeahead
        write_box.view.set_typeahead_footer.assert_called_once_with(
            suggestions[:10], expected_state, is_truncated
        )

    @pytest.mark.parametrize(
        "topic_entered_by_user, topic_sent_to_server",
        [
            ("", "(no topic)"),
            ("hello", "hello"),
            ("  ", "(no topic)"),
        ],
        ids=[
            "empty_topic",
            "non_empty_topic",
            "topic_with_whitespace",
        ],
    )
    @pytest.mark.parametrize(
        "msg_edit_id", [10, None], ids=["update_message", "send_message"]
    )
    @pytest.mark.parametrize("key", keys_for_command("SEND_MESSAGE"))
    def test_keypress_SEND_MESSAGE_no_topic(
        self,
        mocker,
        write_box,
        msg_edit_id,
        topic_entered_by_user,
        topic_sent_to_server,
        key,
        widget_size,
        propagate_mode="change_one",
    ):
        write_box.stream_write_box = mocker.Mock()
        write_box.msg_write_box = mocker.Mock(edit_text="")
        write_box.title_write_box = mocker.Mock(edit_text=topic_entered_by_user)
        write_box.to_write_box = None
        size = widget_size(write_box)
        write_box.msg_edit_id = msg_edit_id
        write_box.edit_mode_button = mocker.Mock(mode=propagate_mode)

        write_box.keypress(size, key)

        if msg_edit_id:
            write_box.model.update_stream_message.assert_called_once_with(
                topic=topic_sent_to_server,
                content=write_box.msg_write_box.edit_text,
                message_id=msg_edit_id,
                propagate_mode=propagate_mode,
            )
        else:
            write_box.model.send_stream_message.assert_called_once_with(
                stream=write_box.stream_write_box.edit_text,
                topic=topic_sent_to_server,
                content=write_box.msg_write_box.edit_text,
            )

    @pytest.mark.parametrize(
        "key, current_typeahead_mode, expected_typeahead_mode, expect_footer_was_reset",
        [
            # footer does not reset
            (primary_key_for_command("AUTOCOMPLETE"), False, False, False),
            (primary_key_for_command("AUTOCOMPLETE_REVERSE"), False, False, False),
            (primary_key_for_command("AUTOCOMPLETE"), True, True, False),
            (primary_key_for_command("AUTOCOMPLETE_REVERSE"), True, True, False),
            # footer resets
            (primary_key_for_command("GO_BACK"), True, False, True),
            ("space", True, False, True),
            ("k", True, False, True),
        ],
    )
    def test_keypress_typeahead_mode_autocomplete_key(
        self,
        mocker,
        write_box,
        widget_size,
        current_typeahead_mode,
        expected_typeahead_mode,
        expect_footer_was_reset,
        key,
    ):
        write_box.is_in_typeahead_mode = current_typeahead_mode
        size = widget_size(write_box)

        write_box.keypress(size, key)

        assert write_box.is_in_typeahead_mode == expected_typeahead_mode
        if expect_footer_was_reset:
            self.view.set_footer_text.assert_called_once_with()
        else:
            self.view.set_footer_text.assert_not_called()

    @pytest.mark.parametrize(
        [
            "initial_focus_name",
            "initial_focus_col_name",
            "box_type",
            "msg_body_edit_enabled",
            "message_being_edited",
            "expected_focus_name",
            "expected_focus_col_name",
        ],
        [
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                "stream",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="stream_name_to_topic_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                True,
                False,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="topic_to_message_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                False,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                id="topic_edit_only-topic_to_edit_mode_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                "stream",
                False,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="topic_edit_only-edit_mode_to_topic_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "stream",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                id="message_to_stream_name_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                id="edit_box-stream_name_to_topic_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_TOPIC",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                id="edit_box-topic_to_edit_mode_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_EDIT",
                "stream",
                True,
                True,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="edit_box-edit_mode_to_message_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "stream",
                True,
                True,
                "CONTAINER_HEADER",
                "HEADER_BOX_STREAM",
                id="edit_box-message_to_stream_name_box",
            ),
            case(
                "CONTAINER_HEADER",
                "HEADER_BOX_RECIPIENT",
                "private",
                True,
                False,
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                id="recipient_to_message_box",
            ),
            case(
                "CONTAINER_MESSAGE",
                "MESSAGE_BOX_BODY",
                "private",
                True,
                False,
                "CONTAINER_HEADER",
                "HEADER_BOX_RECIPIENT",
                id="message_to_recipient_box",
            ),
        ],
    )
    @pytest.mark.parametrize("tab_key", keys_for_command("CYCLE_COMPOSE_FOCUS"))
    def test_keypress_CYCLE_COMPOSE_FOCUS(
        self,
        write_box,
        tab_key,
        initial_focus_name,
        expected_focus_name,
        initial_focus_col_name,
        expected_focus_col_name,
        box_type,
        msg_body_edit_enabled,
        message_being_edited,
        widget_size,
        mocker,
        stream_id=10,
    ):
        mocker.patch(BOXES + ".WriteBox._set_stream_write_box_style")

        if box_type == "stream":
            if message_being_edited:
                mocker.patch(BOXES + ".EditModeButton")
                write_box.stream_box_edit_view(stream_id)
                write_box.msg_edit_id = 10
            else:
                write_box.stream_box_view(stream_id)
        else:
            write_box.private_box_view()
        size = widget_size(write_box)

        def focus_val(x: str) -> int:
            return getattr(write_box, "FOCUS_" + x)

        write_box.focus_position = focus_val(initial_focus_name)
        write_box.msg_body_edit_enabled = msg_body_edit_enabled
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            write_box.header_write_box.focus_col = focus_val(initial_focus_col_name)
        write_box.model.get_invalid_recipient_emails.return_value = []
        write_box.model.user_dict = mocker.MagicMock()

        write_box.keypress(size, tab_key)

        assert write_box.focus_position == focus_val(expected_focus_name)
        # FIXME: Needs refactoring?
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            assert write_box.header_write_box.focus_col == focus_val(
                expected_focus_col_name
            )
        else:
            assert write_box.FOCUS_MESSAGE_BOX_BODY == focus_val(
                expected_focus_col_name
            )

    @pytest.mark.parametrize(
        "msg_type, expected_box_size",
        [
            ("private", 1),
            ("stream", 4),
            ("stream_edit", 5),
        ],
        ids=[
            "private_message",
            "stream_message",
            "stream_edit_message",
        ],
    )
    def test_write_box_header_contents(
        self, write_box, expected_box_size, mocker, msg_type
    ):
        mocker.patch(BOXES + ".WriteBox._set_stream_write_box_style")
        mocker.patch(BOXES + ".WriteBox.set_editor_mode")
        if msg_type == "stream":
            write_box.stream_box_view(1000)
        elif msg_type == "stream_edit":
            write_box.stream_box_edit_view(1000)
        else:
            write_box.private_box_view(
                emails=["feedback@zulip.com"], recipient_user_ids=[1]
            )

        assert len(write_box.header_write_box.widget_list) == expected_box_size


class TestPanelSearchBox:
    search_caption = "Search Results "

    @pytest.fixture
    def panel_search_box(self, mocker):
        # X is the return from keys_for_command("UNTESTED_TOKEN")
        mocker.patch(BOXES + ".keys_for_command", return_value="X")
        panel_view = mocker.Mock()
        update_func = mocker.Mock()
        return PanelSearchBox(panel_view, "UNTESTED_TOKEN", update_func)

    def test_init(self, panel_search_box):
        assert panel_search_box.search_text == "Search [X]: "
        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

    def test_reset_search_text(self, panel_search_box):
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_search_box.reset_search_text()

        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

    @pytest.mark.parametrize(
        "search_text, entered_string, expected_result",
        [
            # NOTE: In both backspace cases it is not validated (backspace is not
            #       shown), but still is handled during editing as normal
            # NOTE: Unicode backspace case likely doesn't get triggered
            case("", "backspace", False, id="no_text-disallow_urwid_backspace"),
            case("", "\u0008", False, id="no_text-disallow_unicode_backspace"),
            case("", "\u2003", False, id="no_text-disallow_unicode_em_space"),
            case("", "x", True, id="no_text-allow_entry_of_x"),
            case("", "\u0394", True, id="no_text-allow_entry_of_delta"),
            case("", " ", False, id="no_text-disallow_entry_of_space"),
            case("x", " ", True, id="text-allow_entry_of_space"),
            case("x", "backspace", False, id="text-disallow_urwid_backspace"),
        ],
    )
    def test_valid_char(
        self, panel_search_box, search_text, entered_string, expected_result
    ):
        panel_search_box.edit_text = search_text

        result = panel_search_box.valid_char(entered_string)

        assert result == expected_result

    @pytest.mark.parametrize(
        "log, expect_body_focus_set", [([], False), (["SOMETHING"], True)]
    )
    @pytest.mark.parametrize("enter_key", keys_for_command("ENTER"))
    def test_keypress_ENTER(
        self, panel_search_box, widget_size, enter_key, log, expect_body_focus_set
    ):
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = lambda: True
        panel_search_box.panel_view.log = log
        empty_search = False if log else True
        panel_search_box.panel_view.empty_search = empty_search
        panel_search_box.set_caption("")
        panel_search_box.edit_text = "key words"

        panel_search_box.keypress(size, enter_key)

        # Update this display
        # FIXME We can't test for the styled version?
        # We'd compare to [('filter_results', 'Search Results'), ' ']

        assert panel_search_box.edit_text == "key words"

        panel_view = panel_search_box.panel_view
        if expect_body_focus_set:
            assert panel_search_box.caption == self.search_caption
            # Leave editor mode
            panel_view.view.controller.exit_editor_mode.assert_called_once_with()
            # Switch focus to body; if have results, move to them
            panel_view.set_focus.assert_called_once_with("body")
            panel_view.body.set_focus.assert_called_once_with(0)
        else:
            assert panel_search_box.caption == ""
            panel_view.view.controller.exit_editor_mode.assert_not_called()
            panel_view.set_focus.assert_not_called()
            panel_view.body.set_focus.assert_not_called()

    @pytest.mark.parametrize("back_key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, panel_search_box, back_key, widget_size):
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = lambda: True
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_view = panel_search_box.panel_view

        panel_search_box.keypress(size, back_key)

        # Reset display
        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

        # Leave editor mode
        panel_view.view.controller.exit_editor_mode.assert_called_once_with()

        # Switch focus to body; focus should return to previous in body
        panel_view.set_focus.assert_called_once_with("body")

        # pass keypress back
        # FIXME This feels hacky to call keypress (with hardcoded 'esc' too)
        #       - should we add a second callback to update the panel?
        panel_view.keypress.assert_called_once_with(size, "esc")
