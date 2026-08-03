#!/usr/bin/env python3
import logging
import sys
from typing import Any, Dict, List

import click

import zulip

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("zulip-cli")

client = zulip.Client(config_file="~/zuliprc")


@click.group()
def cli() -> None:
    pass


def exit_on_result(result: str) -> None:
    if result == "success":
        sys.exit(0)
    sys.exit(1)


def log_exit(response: Dict[str, Any]) -> None:
    result = response["result"]
    if result == "success":
        log.info(response)
    else:
        log.error(response)
    exit_on_result(result)


# Messages API


@cli.command()
@click.argument("recipients", type=str, nargs=-1)
@click.option(
    "--stream",
    "-s",
    default="",
    help="Allows the user to specify a stream for the message.",
)
@click.option(
    "--subject",
    "-S",
    default="",
    help="Allows the user to specify a subject for the message.",
)
@click.option("--message", "-m", required=True)
def send_message(recipients: List[str], stream: str, subject: str, message: str) -> None:
    """Sends a message and optionally prints status about the same."""

    # Sanity check user data
    has_stream = stream != ""
    has_subject = subject != ""
    if len(recipients) != 0 and has_stream:
        click.echo("You cannot specify both a username and a stream/subject.")
        raise SystemExit(1)
    if len(recipients) == 0 and (has_stream != has_subject):
        click.echo("Stream messages must have a subject")
        raise SystemExit(1)
    if len(recipients) == 0 and not has_stream:
        click.echo("You must specify a stream/subject or at least one recipient.")
        raise SystemExit(1)

    message_data: Dict[str, Any]
    if has_stream:
        message_data = {
            "type": "stream",
            "content": message,
            "subject": subject,
            "to": stream,
        }
    else:
        message_data = {
            "type": "private",
            "content": message,
            "to": recipients,
        }

    if message_data["type"] == "stream":
        log.info(
            'Sending message to stream "%s", subject "%s"... '
            % (message_data["to"], message_data["subject"])
        )
    else:
        log.info("Sending message to %s... " % message_data["to"])
    response = client.send_message(message_data)
    log_exit(response)


@cli.command()
def upload_file() -> None:
    """Upload a single file and get the corresponding URI."""
    # TODO


@cli.command()
@click.argument("message_id", type=int)
@click.option("--message", "-m", required=True)
def update_message(message_id: int, message: str) -> None:
    """Edit/update the content or topic of a message."""
    request = {
        "message_id": message_id,
        "content": message,
    }
    response = client.update_message(request)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
def delete_message(message_id: int) -> None:
    """Permanently delete a message."""
    response = client.delete_message(message_id)
    log_exit(response)


# TODO
# https://zulip.com/api/get-messages
# https://zulip.com/api/construct-narrow


@cli.command()
@click.argument("message_id", type=int)
@click.argument("emoji_name")
def add_reaction(message_id: int, emoji_name: str) -> None:
    """Add an emoji reaction to a message."""
    request = {
        "message_id": message_id,
        "emoji_name": emoji_name,
    }

    response = client.add_reaction(request)
    log_exit(response)


@cli.command()
@click.argument("message_id", type=int)
@click.argument("emoji_name")
def remove_reaction(message_id: int, emoji_name: str) -> None:
    """Remove an emoji reaction from a message."""
    request = {
        "message_id": message_id,
        "emoji_name": emoji_name,
    }

    response = client.remove_reaction(request)
    log_exit(response)


# TODO
# https://zulip.com/api/render-message
# https://zulip.com/api/get-raw-message
# https://zulip.com/api/check-narrow-matches


@cli.command()
@click.argument("message_id", type=int)
def get_message_history(message_id: int) -> None:
    """Fetch the message edit history of a previously edited message.
    Note that edit history may be disabled in some organizations; see https://zulip.com/help/view-a-messages-edit-history.
    """
    response = client.get_message_history(message_id)
    log_exit(response)


# TODO
# https://zulip.com/api/update-message-flags


@cli.command()
def mark_all_as_read() -> None:
    """Marks all of the current user's unread messages as read."""
    response = client.mark_all_as_read()
    log_exit(response)


# Streams API


@cli.command()
def get_subscriptions() -> None:
    """Get all streams that the user is subscribed to."""
    response = client.get_subscriptions()
    log_exit(response)


if __name__ == "__main__":
    cli()
