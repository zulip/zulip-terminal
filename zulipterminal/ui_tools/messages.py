"""
UI to render a Zulip message for display, and respond contextually to actions
"""

import typing
from collections import defaultdict
from datetime import date, datetime
from time import time
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import dateutil.parser
import urwid
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from tzlocal import get_localzone

from zulipterminal.config.keys import is_command_key, primary_key_for_command
from zulipterminal.config.symbols import (
    MESSAGE_CONTENT_MARKER,
    MESSAGE_HEADER_DIVIDER,
    QUOTED_TEXT_MARKER,
    STREAM_TOPIC_SEPARATOR,
    TIME_MENTION_MARKER,
)
from zulipterminal.config.ui_mappings import STATE_ICON
from zulipterminal.helper import Message, get_unused_fence
from zulipterminal.server_url import near_message_url
from zulipterminal.ui_tools.tables import render_table
from zulipterminal.urwid_types import urwid_MarkupTuple, urwid_Size


if typing.TYPE_CHECKING:
    from zulipterminal.model import Model

# Usernames to show before just showing reaction counts
MAXIMUM_USERNAMES_VISIBLE = 3


class _MessageEditState(NamedTuple):
    message_id: int
    old_topic: str


class MessageBox(urwid.Pile):
    # type of last_message is Optional[Message], but needs refactoring
    def __init__(self, message: Message, model: "Model", last_message: Any) -> None:
        self.model = model
        self.message = message
        self.header: List[Any] = []
        self.content: urwid.Text = urwid.Text("")
        self.footer: List[Any] = []
        self.stream_name = ""
        self.stream_id: Optional[int] = None
        self.topic_name = ""
        self.email = ""  # FIXME: Can we remove this?
        self.user_id: Optional[int] = None
        self.message_links: Dict[str, Tuple[str, int, bool]] = dict()
        self.topic_links: Dict[str, Tuple[str, int, bool]] = dict()
        self.time_mentions: List[Tuple[str, str]] = list()
        self.last_message = last_message
        # if this is the first message
        if self.last_message is None:
            self.last_message = defaultdict(dict)

        if self.message["type"] == "stream":
            # Set `topic_links` if present
            for link in self.message.get("topic_links", []):
                # Modernized response
                self.topic_links[link["url"]] = (
                    link["text"],
                    len(self.topic_links) + 1,
                    True,
                )

            self.stream_name = self.message["display_recipient"]
            self.stream_id = self.message["stream_id"]
            self.topic_name = self.message["subject"]
        elif self.message["type"] == "private":
            self.email = self.message["sender_email"]
            self.user_id = self.message["sender_id"]
        else:
            raise RuntimeError("Invalid message type")

        if self.message["type"] == "private":
            if self._is_private_message_to_self():
                recipient = self.message["display_recipient"][0]
                self.recipients_names = recipient["full_name"]
                self.recipient_emails = [self.model.user_email]
                self.recipient_ids = [self.model.user_id]
            else:
                self.recipients_list = []
                for recipient in self.message["display_recipient"]:
                    if recipient["email"] != self.model.user_email:
                        if self.message["id"] in self.model.index["muted_messages"]:
                            self.recipients_list.append("muted_user")
                        else:
                            self.recipients_list.append(recipient["full_name"])
                self.recipients_names = ", ".join(self.recipients_list)
                self.recipient_emails = [
                    recipient["email"]
                    for recipient in self.message["display_recipient"]
                    if recipient["email"] != self.model.user_email
                ]
                self.recipient_ids = [
                    recipient["id"]
                    for recipient in self.message["display_recipient"]
                    if recipient["id"] != self.model.user_id
                ]

        super().__init__(self.main_view())

    def need_recipient_header(self) -> bool:
        # Prevent redundant information in recipient bar
        if len(self.model.narrow) == 1 and self.model.narrow[0][0] == "pm-with":
            return False
        if len(self.model.narrow) == 2 and self.model.narrow[1][0] == "topic":
            return False

        last_msg = self.last_message
        if self.message["type"] == "stream":
            return not (
                last_msg["type"] == "stream"
                and self.topic_name == last_msg["subject"]
                and self.stream_name == last_msg["display_recipient"]
            )
        elif self.message["type"] == "private":
            recipient_ids = [
                {
                    recipient["id"]
                    for recipient in message["display_recipient"]
                    if "id" in recipient
                }
                for message in (self.message, last_msg)
                if "display_recipient" in message
            ]
            return not (
                len(recipient_ids) == 2
                and recipient_ids[0] == recipient_ids[1]
                and last_msg["type"] == "private"
            )
        else:
            raise RuntimeError("Invalid message type")

    def _is_private_message_to_self(self) -> bool:
        recipient_list = self.message["display_recipient"]
        return (
            len(recipient_list) == 1
            and recipient_list[0]["email"] == self.model.user_email
        )

    def stream_header(self) -> Any:
        assert self.stream_id is not None
        color = self.model.stream_dict[self.stream_id]["color"]
        bar_color = f"s{color}"
        stream_title_markup = (
            "bar",
            [
                (bar_color, f"{self.stream_name} {STREAM_TOPIC_SEPARATOR} "),
                ("title", f" {self.topic_name}"),
            ],
        )
        stream_title = urwid.Text(stream_title_markup)
        header = urwid.Columns(
            [
                ("pack", stream_title),
                (1, urwid.Text((color, " "))),
                urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER), color),
            ]
        )
        header.markup = stream_title_markup
        return header

    def private_header(self) -> Any:
        title_markup = (
            "header",
            [("general_narrow", "You and "), ("general_narrow", self.recipients_names)],
        )
        title = urwid.Text(title_markup)
        header = urwid.Columns(
            [
                ("pack", title),
                (1, urwid.Text(("general_bar", " "))),
                urwid.AttrWrap(urwid.Divider(MESSAGE_HEADER_DIVIDER), "general_bar"),
            ]
        )
        header.markup = title_markup
        return header

    def recipient_header(self) -> Any:
        if self.message["type"] == "stream":
            return self.stream_header()
        else:
            return self.private_header()

    def top_search_bar(self) -> Any:
        curr_narrow = self.model.narrow
        is_search_narrow = self.model.is_search_narrow()
        if is_search_narrow:
            curr_narrow = [
                sub_narrow for sub_narrow in curr_narrow if sub_narrow[0] != "search"
            ]
        else:
            self.model.controller.view.search_box.text_box.set_edit_text("")
        if curr_narrow == []:
            text_to_fill = "All messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "private":
            text_to_fill = "All direct messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "starred":
            text_to_fill = "Starred messages"
        elif len(curr_narrow) == 1 and curr_narrow[0][1] == "mentioned":
            text_to_fill = "Mentions"
        elif self.message["type"] == "stream":
            assert self.stream_id is not None
            bar_color = self.model.stream_dict[self.stream_id]["color"]
            bar_color = f"s{bar_color}"
            if len(curr_narrow) == 2 and curr_narrow[1][0] == "topic":
                text_to_fill = (
                    "bar",  # type: ignore[assignment]
                    [
                        (bar_color, self.stream_name),
                        (bar_color, ": topic narrow"),
                    ],
                )
            else:
                text_to_fill = (
                    "bar",  # type: ignore[assignment]
                    [(bar_color, self.stream_name)],
                )
        elif len(curr_narrow) == 1 and len(curr_narrow[0][1].split(",")) > 1:
            text_to_fill = "Group direct message conversation"
        else:
            text_to_fill = "Direct message conversation"

        if is_search_narrow:
            title_markup = (
                "header",
                [
                    ("general_narrow", text_to_fill),
                    (None, " "),
                    ("filter_results", "Search Results"),
                ],
            )
        else:
            title_markup = ("header", [("general_narrow", text_to_fill)])
        title = urwid.Text(title_markup)
        header = urwid.AttrWrap(title, "bar")
        header.text_to_fill = text_to_fill
        header.markup = title_markup
        return header

    def reactions_view(
        self, reactions: List[Dict[str, Any]]
    ) -> Optional[urwid.Padding]:
        if not reactions:
            return None
        try:
            my_user_id = self.model.user_id
            reaction_stats = defaultdict(list)
            for reaction in reactions:
                user_id = int(reaction["user"].get("id", -1))
                if user_id == -1:
                    user_id = int(reaction["user"]["user_id"])
                user_name = reaction["user"]["full_name"]
                if user_id == my_user_id:
                    user_name = "You"
                reaction_stats[reaction["emoji_name"]].append((user_id, user_name))

            for reaction, ids in reaction_stats.items():
                if (my_user_id, "You") in ids:
                    ids.remove((my_user_id, "You"))
                    ids.append((my_user_id, "You"))

            reaction_texts = [
                (
                    "reaction_mine"
                    if my_user_id in [id[0] for id in ids]
                    else "reaction",
                    f" :{reaction}: {len(ids)} "
                    if len(reactions) > MAXIMUM_USERNAMES_VISIBLE
                    else f" :{reaction}: {', '.join([id[1] for id in ids])} ",
                )
                for reaction, ids in reaction_stats.items()
            ]

            spaced_reaction_texts = [
                entry
                for pair in zip(reaction_texts, " " * len(reaction_texts))
                for entry in pair
            ]
            return urwid.Padding(
                urwid.Text(spaced_reaction_texts),
                align="left",
                width=("relative", 90),
                left=25,
                min_width=50,
            )
        except Exception:
            return None

    @staticmethod
    def footlinks_view(
        message_links: Dict[str, Tuple[str, int, bool]],
        *,
        maximum_footlinks: int,
        padded: bool,
        wrap: str,
    ) -> Tuple[Any, int]:
        """
        Returns a Tuple that consists footlinks view (widget) and its required
        width.
        """
        # Return if footlinks are disabled by the user.
        if maximum_footlinks == 0:
            return None, 0

        footlinks = []
        counter = 0
        footlinks_width = 0
        for link, (text, index, show_footlink) in message_links.items():
            if counter == maximum_footlinks:
                break
            if not show_footlink:
                continue

            counter += 1
            styled_footlink = [
                ("msg_link_index", f"{index}:"),
                (None, " "),
                ("msg_link", link),
            ]
            footlinks_width = max(
                footlinks_width, sum([len(text) for style, text in styled_footlink])
            )
            footlinks.extend([*styled_footlink, "\n"])

        if not footlinks:
            return None, 0

        footlinks[-1] = footlinks[-1][:-1]  # Remove the last newline.

        text_widget = urwid.Text(footlinks, wrap=wrap)
        if padded:
            return (
                urwid.Padding(
                    text_widget,
                    align="left",
                    left=8,
                    width=("relative", 100),
                    min_width=10,
                    right=2,
                ),
                footlinks_width,
            )
        else:
            return text_widget, footlinks_width

    @classmethod
    def soup2markup(
        cls, soup: Any, metadata: Dict[str, Any], **state: Any
    ) -> Tuple[List[Any], Dict[str, Tuple[str, int, bool]], List[Tuple[str, str]]]:
        # Ensure a string is provided, in case the soup finds none
        # This could occur if eg. an image is removed or not shown
        markup: List[Union[str, Tuple[Optional[str], Any]]] = [""]
        if soup is None:  # This is not iterable, so return promptly
            return markup, metadata["message_links"], metadata["time_mentions"]
        unrendered_tags = {  # In pairs of 'tag_name': 'text'
            # TODO: Some of these could be implemented
            "br": "",  # No indicator of absence
            "hr": "RULER",
            "img": "IMAGE",
        }
        unrendered_div_classes = {  # In pairs of 'div_class': 'text'
            # TODO: Support embedded content & twitter preview?
            "message_embed": "EMBEDDED CONTENT",
            "inline-preview-twitter": "TWITTER PREVIEW",
            "message_inline_ref": "",  # Duplicate of other content
            "message_inline_image": "",  # Duplicate of other content
        }
        unrendered_template = "[{} NOT RENDERED]"
        for element in soup:
            if isinstance(element, Tag):
                # Caching element variables for use in the
                # if/elif/else chain below for improving legibility.
                tag = element.name
                tag_attrs = element.attrs
                tag_classes = tag_attrs.get("class", [])
                tag_text = element.text

            if isinstance(element, NavigableString):
                # NORMAL STRINGS
                if element == "\n" and metadata.get("bq_len", 0) > 0:
                    metadata["bq_len"] -= 1
                    continue
                markup.append(element)
            elif tag == "div" and (set(tag_classes) & set(unrendered_div_classes)):
                # UNRENDERED DIV CLASSES
                # NOTE: Though `matches` is generalized for multiple
                # matches it is very unlikely that there would be any.
                matches = set(unrendered_div_classes) & set(tag_classes)
                text = unrendered_div_classes[matches.pop()]
                if text:
                    markup.append(unrendered_template.format(text))
            elif tag == "img" and tag_classes == ["emoji"]:
                # CUSTOM EMOJIS AND ZULIP_EXTRA_EMOJI
                emoji_name = tag_attrs.get("title", [])
                markup.append(("msg_emoji", f":{emoji_name}:"))
            elif tag in unrendered_tags:
                # UNRENDERED SIMPLE TAGS
                text = unrendered_tags[tag]
                if text:
                    markup.append(unrendered_template.format(text))
            elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                # HEADING STYLE (h1 to h6)
                markup.append(("msg_heading", tag_text))
            elif tag in ("p", "del"):
                # PARAGRAPH, STRIKE-THROUGH
                markup.extend(cls.soup2markup(element, metadata)[0])
            elif tag == "span" and "emoji" in tag_classes:
                # EMOJI
                markup.append(("msg_emoji", tag_text))
            elif tag == "span" and ({"katex-display", "katex"} & set(tag_classes)):
                # MATH TEXT
                # FIXME: Add html -> urwid client-side logic for rendering KaTex text.
                # Avoid displaying multiple markups, and show only the source
                # as of now.
                if element.find("annotation"):
                    tag_text = element.find("annotation").text

                markup.append(("msg_math", tag_text))
            elif tag == "span" and (
                {"user-group-mention", "user-mention"} & set(tag_classes)
            ):
                # USER MENTIONS & USER-GROUP MENTIONS
                markup.append(("msg_mention", tag_text))
            elif tag == "a":
                # LINKS
                # Use rstrip to avoid anomalies and edge cases like
                # https://google.com vs https://google.com/.
                link = tag_attrs["href"].rstrip("/")
                text = element.img["src"] if element.img else tag_text
                text = text.rstrip("/")

                parsed_link = urlparse(link)
                if not parsed_link.scheme:  # => relative link
                    # Prepend org url to convert it to an absolute link
                    link = urljoin(metadata["server_url"], link)

                text = text if text else link

                show_footlink = True
                # Only use the last segment if the text is redundant.
                # NOTE: The 'without scheme' excerpt is to deal with the case
                # where a user puts a link without any scheme and the server
                # uses http as the default scheme but keeps the text as-is.
                # For instance, see how example.com/some/path becomes
                # <a href="http://example.com">example.com/some/path</a>.
                link_without_scheme, text_without_scheme = (
                    data.split("://")[1] if "://" in data else data
                    for data in [link, text]
                )  # Split on '://' is for cases where text == link.
                if link_without_scheme == text_without_scheme:
                    last_segment = text.split("/")[-1]
                    if "." in last_segment:
                        new_text = last_segment  # Filename.
                    elif text.startswith(metadata["server_url"]):
                        # Relative URL.
                        new_text = text.split(metadata["server_url"])[-1]
                    else:
                        new_text = (
                            parsed_link.netloc
                            if parsed_link.netloc
                            else text.split("/")[0]
                        )  # Domain name.
                    if new_text != text_without_scheme:
                        text = new_text
                    else:
                        # Do not show as a footlink as the text is sufficient
                        # to represent the link.
                        show_footlink = False

                # Detect duplicate links to save screen real estate.
                if link not in metadata["message_links"]:
                    metadata["message_links"][link] = (
                        text,
                        len(metadata["message_links"]) + 1,
                        show_footlink,
                    )
                else:
                    # Append the text if its link already exist with a
                    # different text.
                    saved_text, saved_link_index, saved_footlink_status = metadata[
                        "message_links"
                    ][link]
                    if saved_text != text:
                        metadata["message_links"][link] = (
                            f"{saved_text}, {text}",
                            saved_link_index,
                            show_footlink or saved_footlink_status,
                        )

                markup.extend(
                    [
                        ("msg_link", text),
                        " ",
                        ("msg_link_index", f"[{metadata['message_links'][link][1]}]"),
                    ]
                )
            elif tag == "blockquote":
                # BLOCKQUOTE TEXT
                markup.append(("msg_quote", cls.soup2markup(element, metadata)[0]))
            elif tag == "code":
                """
                CODE INLINE
                -----------
                Use the same style as plain text codeblocks
                which is the `whitespace` token of pygments.
                """
                markup.append(("pygments:w", tag_text))
            elif tag == "div" and "codehilite" in tag_classes:
                """
                CODE BLOCK
                -------------
                Structure:   # Language is optional
                    <div class="codehilite" data-code-language="python">
                      <pre>
                        <span></span>
                        <code>
                          Code HTML
                          Made of <span>'s and NavigableStrings
                        </code>
                      </pre>
                    </div>
                """
                code_soup = element.pre.code
                # NOTE: Old messages don't have the additional `code` tag.
                # Ref: https://github.com/Python-Markdown/markdown/pull/862
                if code_soup is None:
                    code_soup = element.pre

                for code_element in code_soup.contents:
                    code_text = (
                        code_element.text
                        if isinstance(code_element, Tag)
                        else code_element.string
                    )

                    if code_element.name == "span":
                        if len(code_text) == 0:
                            continue
                        css_style = code_element.attrs.get("class", ["w"])
                        markup.append((f"pygments:{css_style[0]}", code_text))
                    else:
                        markup.append(("pygments:w", code_text))
            elif tag in ("strong", "em"):
                # BOLD & ITALIC
                markup.append(("msg_bold", tag_text))
            elif tag in ("ul", "ol"):
                # LISTS (UL & OL)
                for part in element.contents:
                    if part == "\n":
                        part.replace_with("")

                if "indent_level" not in state:
                    state["indent_level"] = 1
                    state["list_start"] = True
                else:
                    state["indent_level"] += 1
                    state["list_start"] = False
                if tag == "ol":
                    start_number = int(tag_attrs.get("start", 1))
                    state["list_index"] = start_number
                    markup.extend(cls.soup2markup(element, metadata, **state)[0])
                    del state["list_index"]  # reset at end of this list
                else:
                    if "list_index" in state:
                        del state["list_index"]  # this is unordered
                    markup.extend(cls.soup2markup(element, metadata, **state)[0])
                del state["indent_level"]  # reset indents after any list
            elif tag == "li":
                # LIST ITEMS (LI)
                for part in element.contents:
                    if part == "\n":
                        part.replace_with("")
                if not state.get("list_start", False):
                    markup.append("\n")

                indent = state.get("indent_level", 1)
                if "list_index" in state:
                    markup.append(f"{'  ' * indent}{state['list_index']}. ")
                    state["list_index"] += 1
                else:
                    chars = [
                        "\N{BULLET}",
                        "\N{RING OPERATOR}",  # small hollow
                        "\N{HYPHEN}",
                    ]
                    markup.append(f"{'  ' * indent}{chars[(indent - 1) % 3]} ")
                state["list_start"] = False
                markup.extend(cls.soup2markup(element, metadata, **state)[0])
            elif tag == "table":
                markup.extend(render_table(element))
            elif tag == "time":
                # New in feature level 16, server version 3.0.
                # Render time in current user's local time zone.
                timestamp = element.get("datetime")

                # This should not happen. Regardless, we are interested in
                # debugging and reporting it to zulip/zulip if it does.
                assert timestamp is not None, "Could not find datetime attr"

                utc_time = dateutil.parser.parse(timestamp)
                local_time = utc_time.astimezone(get_localzone())
                # TODO: Address 12-hour format support with application-wide
                # support for different formats.
                time_string = local_time.strftime("%a, %b %-d %Y, %-H:%M (%Z)")
                markup.append(("msg_time", f" {TIME_MENTION_MARKER} {time_string} "))

                source_text = f"Original text was {tag_text.strip()}"
                metadata["time_mentions"].append((time_string, source_text))
            else:
                markup.extend(cls.soup2markup(element, metadata)[0])
        return markup, metadata["message_links"], metadata["time_mentions"]

    def main_view(self) -> List[Any]:
        # Recipient Header
        if self.need_recipient_header():
            recipient_header = self.recipient_header()
        else:
            recipient_header = None

        # Content Header
        message = {
            key: {
                "is_starred": "starred" in msg["flags"],
                "author": (
                    msg["sender_full_name"] if "sender_full_name" in msg else None
                ),
                "time": (
                    self.model.formatted_local_time(
                        msg["timestamp"], show_seconds=False
                    )
                    if "timestamp" in msg
                    else None
                ),
                "datetime": (
                    datetime.fromtimestamp(msg["timestamp"])
                    if "timestamp" in msg
                    else None
                ),
            }
            for key, msg in dict(this=self.message, last=self.last_message).items()
        }
        different = {  # How this message differs from the previous one
            "recipients": recipient_header is not None,
            "author": message["this"]["author"] != message["last"]["author"],
            "24h": (
                message["last"]["datetime"] is not None
                and ((message["this"]["datetime"] - message["last"]["datetime"]).days)
            ),
            "timestamp": (
                message["last"]["time"] is not None
                and message["this"]["time"] != message["last"]["time"]
            ),
            "star_status": (
                message["this"]["is_starred"] != message["last"]["is_starred"]
            ),
        }
        any_differences = any(different.values())

        if any_differences:  # Construct content_header, if needed
            text_keys = ("author", "star", "time", "status")
            text: Dict[str, urwid_MarkupTuple] = {key: (None, " ") for key in text_keys}

            if any(different[key] for key in ("recipients", "author", "24h")):
                if self.message["id"] in self.model.index["muted_messages"]:
                    text["author"] = ("msg_sender", "muted_user")
                else:
                    text["author"] = ("msg_sender", message["this"]["author"])

                # TODO: Refactor to use user ids for look up instead of emails.
                email = self.message.get("sender_email", "")
                user = self.model.user_dict.get(email, None)
                # TODO: Currently status of bots are shown as `inactive`.
                # Render bot users' status with bot marker as a follow-up
                status = user.get("status", "inactive") if user else "inactive"

                # The default text['status'] value is (None, ' ')
                if status in STATE_ICON:
                    text["status"] = (f"user_{status}", STATE_ICON[status])

            if message["this"]["is_starred"]:
                text["star"] = ("starred", "*")
            if any(different[key] for key in ("recipients", "author", "timestamp")):
                this_year = date.today().year
                msg_year = message["this"]["datetime"].year
                if this_year != msg_year:
                    text["time"] = ("time", f"{msg_year} - {message['this']['time']}")
                else:
                    text["time"] = ("time", message["this"]["time"])

            content_header = urwid.Columns(
                [
                    ("pack", urwid.Text(text["status"])),
                    ("weight", 10, urwid.Text(text["author"])),
                    (26, urwid.Text(text["time"], align="right")),
                    (1, urwid.Text(text["star"], align="right")),
                ],
                dividechars=1,
            )
        else:
            content_header = None

        # If the message contains '/me' emote then replace it with
        # sender's full name and show it in bold.
        if self.message["is_me_message"]:
            self.message["content"] = self.message["content"].replace(
                "/me", f"<strong>{self.message['sender_full_name']}</strong>", 1
            )

        muted_message_text = "This message was hidden because you have muted the sender"
        # Transform raw message content into markup (As needed by urwid.Text)
        if self.message["id"] in self.model.index["muted_messages"]:
            content, self.message_links, self.time_mentions = (
                (None, muted_message_text),
                {},
                [],
            )
        else:
            content, self.message_links, self.time_mentions = self.transform_content(
                self.message["content"], self.model.server_url
            )
        self.content.set_text(content)

        if self.message["id"] in self.model.index["edited_messages"]:
            edited_label_size = 7
            left_padding = 1
        else:
            edited_label_size = 0
            left_padding = 8

        wrapped_content = urwid.Padding(
            urwid.Columns(
                [
                    (edited_label_size, urwid.Text("EDITED")),
                    urwid.LineBox(
                        urwid.Columns(
                            [
                                (1, urwid.Text("")),
                                self.content,
                            ]
                        ),
                        tline="",
                        bline="",
                        rline="",
                        lline=MESSAGE_CONTENT_MARKER,
                    ),
                ]
            ),
            align="left",
            left=left_padding,
            width=("relative", 100),
            min_width=10,
            right=5,
        )

        # Reactions
        reactions = self.reactions_view(self.message["reactions"])

        # Footlinks.
        footlinks, _ = self.footlinks_view(
            self.message_links,
            maximum_footlinks=self.model.controller.maximum_footlinks,
            padded=True,
            wrap="ellipsis",
        )

        # Build parts together and return
        parts = [
            (recipient_header, recipient_header is not None),
            (content_header, any_differences),
            (wrapped_content, True),
            (footlinks, footlinks is not None),
            (reactions, reactions is not None),
        ]

        self.header = [part for part, condition in parts[:2] if condition]
        self.footer = [part for part, condition in parts[3:] if condition]

        return [part for part, condition in parts if condition]

    def update_message_author_status(self) -> bool:
        """
        Update the author status by resetting the entire message box
        if author field is present.
        """
        author_is_present = False
        author_column = 1  # Index of author field in content header

        if len(self.header) > 0:
            # -1 represents that content header is the last row of header field
            author_field = self.header[-1][author_column]
            author_is_present = author_field.text != " "

        if author_is_present:
            # Re initialize the message if update is required.
            # FIXME: Render specific element (here author field) instead?
            super().__init__(self.main_view())

        return author_is_present

    @classmethod
    def transform_content(
        cls, content: Any, server_url: str
    ) -> Tuple[
        Tuple[None, Any],
        Dict[str, Tuple[str, int, bool]],
        List[Tuple[str, str]],
    ]:
        soup = BeautifulSoup(content, "lxml")
        body = soup.find(name="body")

        metadata = dict(
            server_url=server_url,
            message_links=dict(),
            time_mentions=list(),
        )  # type: Dict[str, Any]

        if body and body.find(name="blockquote"):
            metadata["bq_len"] = cls.indent_quoted_content(soup, QUOTED_TEXT_MARKER)

        markup, message_links, time_mentions = cls.soup2markup(body, metadata)
        return (None, markup), message_links, time_mentions

    @staticmethod
    def indent_quoted_content(soup: Any, padding_char: str) -> int:
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
        blockquote_list = soup.find_all("blockquote")
        bq_len = len(blockquote_list)
        for tag in blockquote_list:
            child_list = tag.findChildren(recursive=False)
            child_block = tag.find_all("blockquote")
            actual_padding = f"{padding_char} " * pad_count
            if len(child_list) == 1:
                pad_count -= 1
                child_iterator = child_list
            else:
                if len(child_block) == 0:
                    child_iterator = child_list
                else:
                    # If there is some text at the beginning of a
                    # quote, we pad it separately.
                    if child_list[0].name == "p":
                        new_tag = soup.new_tag("p")
                        new_tag.string = f"\n{actual_padding}"
                        child_list[0].insert_before(new_tag)
                    child_iterator = child_list[1:]
            for child in child_iterator:
                new_tag = soup.new_tag("p")
                new_tag.string = actual_padding
                # If the quoted message is multi-line message
                # we deconstruct it and pad it at break-points (<br/>)
                for br in child.findAll("br"):
                    next_s = br.nextSibling
                    text = str(next_s.string).strip()
                    if text:
                        insert_tag = soup.new_tag("p")
                        insert_tag.string = f"\n{padding_char} {text}"
                        next_s.replace_with(insert_tag)
                child.insert_before(new_tag)
            pad_count += 1
        return bq_len

    def selectable(self) -> bool:
        # Returning True, indicates that this widget
        # is designed to take focus.
        return True

    def mouse_event(
        self, size: urwid_Size, event: str, button: int, col: int, row: int, focus: bool
    ) -> bool:
        if event == "mouse press" and button == 1:
            if self.model.controller.is_in_editor_mode():
                return True
            self.keypress(size, primary_key_for_command("ENTER"))
            return True

        return super().mouse_event(size, event, button, col, row, focus)

    def keypress(self, size: urwid_Size, key: str) -> Optional[str]:
        if is_command_key("REPLY_MESSAGE", key):
            if self.message["type"] == "private":
                self.model.controller.view.write_box.private_box_view(
                    recipient_user_ids=self.recipient_ids,
                )
            elif self.message["type"] == "stream":
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message["display_recipient"],
                    title=self.message["subject"],
                    stream_id=self.stream_id,
                )
        elif is_command_key("STREAM_MESSAGE", key):
            if len(self.model.narrow) != 0 and self.model.narrow[0][0] == "stream":
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message["display_recipient"],
                    stream_id=self.stream_id,
                )
            else:
                self.model.controller.view.write_box.stream_box_view(0)
        elif is_command_key("STREAM_NARROW", key):
            if self.message["type"] == "private":
                self.model.controller.narrow_to_user(
                    recipient_emails=self.recipient_emails,
                    contextual_message_id=self.message["id"],
                )
            elif self.message["type"] == "stream":
                self.model.controller.narrow_to_stream(
                    stream_name=self.stream_name,
                    contextual_message_id=self.message["id"],
                )
        elif is_command_key("TOGGLE_NARROW", key):
            self.model.unset_search_narrow()
            if self.message["type"] == "private":
                if len(self.model.narrow) == 1 and self.model.narrow[0][0] == "pm-with":
                    self.model.controller.narrow_to_all_pm(
                        contextual_message_id=self.message["id"],
                    )
                else:
                    self.model.controller.narrow_to_user(
                        recipient_emails=self.recipient_emails,
                        contextual_message_id=self.message["id"],
                    )
            elif self.message["type"] == "stream":
                if len(self.model.narrow) > 1:  # in a topic
                    self.model.controller.narrow_to_stream(
                        stream_name=self.stream_name,
                        contextual_message_id=self.message["id"],
                    )
                else:
                    self.model.controller.narrow_to_topic(
                        stream_name=self.stream_name,
                        topic_name=self.topic_name,
                        contextual_message_id=self.message["id"],
                    )
        elif is_command_key("TOPIC_NARROW", key):
            if self.message["type"] == "private":
                self.model.controller.narrow_to_user(
                    recipient_emails=self.recipient_emails,
                    contextual_message_id=self.message["id"],
                )
            elif self.message["type"] == "stream":
                self.model.controller.narrow_to_topic(
                    stream_name=self.stream_name,
                    topic_name=self.topic_name,
                    contextual_message_id=self.message["id"],
                )
        elif is_command_key("ALL_MESSAGES", key):
            self.model.controller.narrow_to_all_messages(
                contextual_message_id=self.message["id"]
            )
        elif is_command_key("REPLY_AUTHOR", key):
            # All subscribers from recipient_ids are not needed here.
            self.model.controller.view.write_box.private_box_view(
                recipient_user_ids=[self.message["sender_id"]],
            )
        elif is_command_key("MENTION_REPLY", key):
            self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))
            mention = f"@**{self.message['sender_full_name']}** "
            self.model.controller.view.write_box.msg_write_box.set_edit_text(mention)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(
                len(mention)
            )
            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("QUOTE_REPLY", key):
            self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))

            # To correctly quote a message that contains quote/code-blocks,
            # we need to fence quoted message containing ``` with ````,
            # ```` with ````` and so on.
            response = self.model.fetch_raw_message_content(self.message["id"])
            message_raw_content = response if response is not None else ""
            fence = get_unused_fence(message_raw_content)

            absolute_url = near_message_url(self.model.server_url[:-1], self.message)

            # Compose box should look something like this:
            #   @_**Zeeshan|514** [said](link to message):
            #   ```quote
            #   message_content
            #   ```
            quote = "@_**{0}|{1}** [said]({2}):\n{3}quote\n{4}\n{3}\n".format(
                self.message["sender_full_name"],
                self.message["sender_id"],
                absolute_url,
                fence,
                message_raw_content,
            )

            self.model.controller.view.write_box.msg_write_box.set_edit_text(quote)
            self.model.controller.view.write_box.msg_write_box.set_edit_pos(len(quote))
            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("EDIT_MESSAGE", key):
            # User can't edit messages of others that already have a subject
            # For private messages, subject = "" (empty string)
            # This also handles the realm_message_content_edit_limit_seconds == 0 case
            if (
                self.message["sender_id"] != self.model.user_id
                and self.message["subject"] != "(no topic)"
            ):
                if self.message["type"] == "stream":
                    self.model.controller.report_error(
                        [
                            " You can't edit messages sent by other users that"
                            " already have a topic."
                        ]
                    )
                else:
                    self.model.controller.report_error(
                        [" You can't edit direct messages sent by other users."]
                    )
                return key
            # Check if editing is allowed in the realm
            elif not self.model.initial_data["realm_allow_message_editing"]:
                self.model.controller.report_error(
                    [" Editing sent message is disabled."]
                )
                return key
            # Check if message is still editable, i.e. within
            # the time limit. A limit of 0 signifies no limit
            # on message body editing.
            msg_body_edit_enabled = True
            if self.model.initial_data["realm_message_content_edit_limit_seconds"] > 0:
                if self.message["sender_id"] == self.model.user_id:
                    time_since_msg_sent = time() - self.message["timestamp"]
                    edit_time_limit = self.model.initial_data[
                        "realm_message_content_edit_limit_seconds"
                    ]
                    # Don't allow editing message body if time-limit exceeded.
                    if time_since_msg_sent >= edit_time_limit:
                        if self.message["type"] == "private":
                            self.model.controller.report_error(
                                [
                                    " Time Limit for editing the message"
                                    " has been exceeded."
                                ]
                            )
                            return key
                        elif self.message["type"] == "stream":
                            self.model.controller.report_warning(
                                [
                                    " Only topic editing allowed."
                                    " Time Limit for editing the message body"
                                    " has been exceeded."
                                ]
                            )
                            msg_body_edit_enabled = False
                elif self.message["type"] == "stream":
                    # Allow editing topic if the message has "(no topic)" subject
                    if self.message["subject"] == "(no topic)":
                        self.model.controller.report_warning(
                            [
                                " Only topic editing is allowed."
                                " This is someone else's message but with (no topic)."
                            ]
                        )
                        msg_body_edit_enabled = False
                    else:
                        self.model.controller.report_error(
                            [
                                " You can't edit messages sent by other users that"
                                " already have a topic."
                            ]
                        )
                        return key
                else:
                    # The remaining case is of a private message not belonging to user.
                    # Which should be already handled by the topmost if block
                    raise RuntimeError(
                        "Reached unexpected block. This should be handled at the top."
                    )

            if self.message["type"] == "private":
                self.keypress(size, primary_key_for_command("REPLY_MESSAGE"))
            elif self.message["type"] == "stream":
                self.model.controller.view.write_box.stream_box_edit_view(
                    stream_id=self.stream_id,
                    caption=self.message["display_recipient"],
                    title=self.message["subject"],
                )
            msg_id = self.message["id"]
            response = self.model.fetch_raw_message_content(msg_id)
            msg = response if response is not None else ""
            write_box = self.model.controller.view.write_box
            write_box.msg_edit_state = _MessageEditState(
                message_id=msg_id, old_topic=self.message["subject"]
            )
            write_box.msg_write_box.set_edit_text(msg)
            write_box.msg_write_box.set_edit_pos(len(msg))
            write_box.msg_body_edit_enabled = msg_body_edit_enabled
            # Set focus to topic box if message body editing is disabled.
            if not msg_body_edit_enabled:
                write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
                write_box.header_write_box.focus_col = write_box.FOCUS_HEADER_BOX_TOPIC

            self.model.controller.view.middle_column.set_focus("footer")
        elif is_command_key("MSG_INFO", key):
            self.model.controller.show_msg_info(
                self.message, self.topic_links, self.message_links, self.time_mentions
            )
        elif is_command_key("ADD_REACTION", key):
            self.model.controller.show_emoji_picker(self.message)
        elif is_command_key("MSG_SENDER_INFO", key):
            self.model.controller.show_msg_sender_info(self.message["sender_id"])
        return key
