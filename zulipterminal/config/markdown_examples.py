from typing import List

from typing_extensions import TypedDict


class MarkdownElements(TypedDict):
    name: str
    raw_text: str
    html_element: str


MARKDOWN_ELEMENTS: List[MarkdownElements] = [
    {
        # BOLD TEXT
        "name": "Bold text",
        "raw_text": "**bold**",
        "html_element": "<strong>bold</strong>",
    },
    {
        # EMOJI
        "name": "Emoji",
        "raw_text": ":heart:",
        "html_element": '<span class="emoji">:heart:</span>',
    },
    {
        # MESSAGE LINKS
        "name": "Message links",
        "raw_text": "[Zulip website]\n(https://zulip.org)",
        "html_element": '<a href="https://zulip.org">Zulip website</a>',
    },
    {
        # BULLET LISTS
        "name": "Bullet lists",
        "raw_text": "* Milk\n* Tea\n  * Green tea\n  * Black tea\n"
        "  * Oolong tea\n* Coffee",
        "html_element": "<ul><li>Milk</li><li>Tea<ul><li>Green tea</li>"
        "<li>Black tea</li><li>Oolong tea</li></ul>"
        "</li><li>Coffee</li>",
    },
    {
        # NUMBERED LISTS
        "name": "Numbered lists",
        "raw_text": "1. Milk\n2. Tea\n3. Coffee",
        "html_element": "<ol><li>Milk</li><li>Tea</li><li>Coffee</li></ol>",
    },
    {
        # USER MENTIONS
        "name": "User mentions",
        "raw_text": "@**King Hamlet**",
        "html_element": '<span class="user-mention">@King Hamlet</span>',
    },
    {
        # USER SILENT MENTIONS
        "name": "User silent mentions",
        "raw_text": "@_**King Hamlet**",
        "html_element": '<span class="user-mention silent">King Hamlet</span>',
    },
    {
        # NOTIFY ALL RECIPIENTS
        "name": "Notify all recipients",
        "raw_text": "@**all**",
        "html_element": '<span class="user-mention">@all</span>',
    },
    {
        # LINK TO A STREAM
        "name": "Link to a stream",
        "raw_text": "#**announce**",
        "html_element": '<a class="stream" data-stream-id="6" '
        'href="/#narrow/stream/6-announce">#announce</a>',
    },
    {
        # STATUS MESSAGE
        "name": "Status message",
        "raw_text": "/me is busy writing code.",
        "html_element": "<strong>{user}</strong> is busy writing code.",
    },
    {
        # INLINE CODE
        "name": "Inline code",
        "raw_text": "Some inline `code`",
        "html_element": "Some inline <code>code</code>",
    },
    {
        # CODE BLOCK
        "name": "Code block",
        "raw_text": "```\ndef zulip():\n    print 'Zulip'\n```",
        "html_element": '<div class="codehilite"><pre><span></span><code>\n'
        "def zulip():\n    print 'Zulip'</code></pre></div>",
    },
    {
        # QUOTED TEXT
        "name": "Quoted text",
        "raw_text": ">Quoted",
        "html_element": "<blockquote>░ Quoted</blockquote>",
    },
    {
        # QUOTED BLOCK
        "name": "Quoted block",
        "raw_text": "```quote\nQuoted block\n```",
        "html_element": "<blockquote>\n░ Quoted block</blockquote>",
    },
    {
        # TABLE RENDERING
        "name": "Table rendering",
        "raw_text": "|Name|Id|\n|--|--:|\n|Robert|1|\n|Mary|100|",
        "html_element": (
            "<table>"
            "<thead>"
            '<tr><th align="left">Name</th><th align="right">Id</th></tr>'
            "</thead>"
            "<tbody>"
            '<tr><td align="left">Robert</td><td align="right">1</td></tr>'
            '<tr><td align="left">Mary</td><td align="right">100</td></tr>'
            "</tbody>"
            "</table>"
        ),
    },
]
