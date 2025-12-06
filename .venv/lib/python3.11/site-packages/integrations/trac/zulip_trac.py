# Zulip trac plugin -- sends zulips when tickets change.
#
# Install by copying this file and zulip_trac_config.py to the trac
# plugins/ subdirectory, customizing the constants in
# zulip_trac_config.py, and then adding "zulip_trac" to the
# components section of the conf/trac.ini file, like so:
#
# [components]
# zulip_trac = enabled
#
# You may then need to restart trac (or restart Apache) for the bot
# (or changes to the bot) to actually be loaded by trac.

import os.path
import sys

from trac.core import Component, implements
from trac.ticket import ITicketChangeListener

sys.path.insert(0, os.path.dirname(__file__))
import zulip_trac_config as config

VERSION = "0.9"

from typing import Any, Dict

if config.ZULIP_API_PATH is not None:
    sys.path.append(config.ZULIP_API_PATH)

import zulip

client = zulip.Client(
    email=config.ZULIP_USER,
    site=config.ZULIP_SITE,
    api_key=config.ZULIP_API_KEY,
    client="ZulipTrac/" + VERSION,
)


def markdown_ticket_url(ticket: Any, heading: str = "ticket") -> str:
    return f"[{heading} #{ticket.id}]({config.TRAC_BASE_TICKET_URL}/{ticket.id})"


def markdown_block(desc: str) -> str:
    return "\n\n>" + "\n> ".join(desc.split("\n")) + "\n"


def truncate(string: str, length: int) -> str:
    if len(string) <= length:
        return string
    return string[: length - 3] + "..."


def trac_subject(ticket: Any) -> str:
    return truncate("#{}: {}".format(ticket.id, ticket.values.get("summary")), 60)


def send_update(ticket: Any, content: str) -> None:
    client.send_message(
        {
            "type": "stream",
            "to": config.STREAM_FOR_NOTIFICATIONS,
            "content": content,
            "subject": trac_subject(ticket),
        }
    )


class ZulipPlugin(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket: Any) -> None:
        """Called when a ticket is created."""
        content = "{} created {} in component **{}**, priority **{}**:\n".format(
            ticket.values.get("reporter"),
            markdown_ticket_url(ticket),
            ticket.values.get("component"),
            ticket.values.get("priority"),
        )
        # Include the full subject if it will be truncated
        if len(ticket.values.get("summary")) > 60:
            content += "**{}**\n".format(ticket.values.get("summary"))
        if ticket.values.get("description") != "":
            content += "{}".format(markdown_block(ticket.values.get("description")))
        send_update(ticket, content)

    def ticket_changed(
        self, ticket: Any, comment: str, author: str, old_values: Dict[str, Any]
    ) -> None:
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        if not (
            set(old_values.keys()).intersection(set(config.TRAC_NOTIFY_FIELDS))
            or (comment and "comment" in set(config.TRAC_NOTIFY_FIELDS))
        ):
            return

        content = f"{author} updated {markdown_ticket_url(ticket)}"
        if comment:
            content += f" with comment: {markdown_block(comment)}\n\n"
        else:
            content += ":\n\n"
        field_changes = []
        for key, value in old_values.items():
            if key == "description":
                content += "- Changed {} from {}\n\nto {}".format(
                    key,
                    markdown_block(value),
                    markdown_block(ticket.values.get(key)),
                )
            elif old_values.get(key) == "":
                field_changes.append(f"{key}: => **{ticket.values.get(key)}**")
            elif ticket.values.get(key) == "":
                field_changes.append(f'{key}: **{old_values.get(key)}** => ""')
            else:
                field_changes.append(
                    f"{key}: **{old_values.get(key)}** => **{ticket.values.get(key)}**"
                )
        content += ", ".join(field_changes)

        send_update(ticket, content)

    def ticket_deleted(self, ticket: Any) -> None:
        """Called when a ticket is deleted."""
        content = "{} was deleted.".format(markdown_ticket_url(ticket, heading="Ticket"))
        send_update(ticket, content)
