#!/usr/bin/env python3
# zulip-send -- Sends a message to the specified recipients.

import argparse
import logging
import sys
from typing import Any, Dict

import zulip

logging.basicConfig()

log = logging.getLogger("zulip-send")


def do_send_message(client: zulip.Client, message_data: Dict[str, Any]) -> bool:
    """Sends a message and optionally prints status about the same."""

    if message_data["type"] == "stream":
        log.info(
            'Sending message to stream "%s", subject "%s"... '
            % (message_data["to"], message_data["subject"])
        )
    else:
        log.info("Sending message to {}... ".format(message_data["to"]))
    response = client.send_message(message_data)
    if response["result"] == "success":
        log.info("Message sent.")
        return True
    else:
        log.error(response["msg"])
        return False


def main() -> int:
    usage = """zulip-send [options] [recipient...]

    Sends a message to specified recipients.

    Examples: zulip-send --stream denmark --subject castle -m "Something is rotten in the state of Denmark."
              zulip-send hamlet@example.com cordelia@example.com -m "Conscience doth make cowards of us all."

    Specify your Zulip API credentials and server in a ~/.zuliprc file or using the options.
    """

    parser = zulip.add_default_arguments(argparse.ArgumentParser(usage=usage))

    parser.add_argument(
        "recipients", nargs="*", help="email addresses of the recipients of the message"
    )

    parser.add_argument(
        "-m", "--message", help="Specifies the message to send, prevents interactive prompting."
    )

    group = parser.add_argument_group("Stream parameters")
    group.add_argument(
        "-s",
        "--stream",
        dest="stream",
        action="store",
        help="Allows the user to specify a stream for the message.",
    )
    group.add_argument(
        "-S",
        "--subject",
        dest="subject",
        action="store",
        help="Allows the user to specify a subject for the message.",
    )

    options = parser.parse_args()

    if options.verbose:
        logging.getLogger().setLevel(logging.INFO)
    # Sanity check user data
    if len(options.recipients) != 0 and (options.stream or options.subject):
        parser.error("You cannot specify both a username and a stream/subject.")
    if len(options.recipients) == 0 and (bool(options.stream) != bool(options.subject)):
        parser.error("Stream messages must have a subject")
    if len(options.recipients) == 0 and not (options.stream and options.subject):
        parser.error("You must specify a stream/subject or at least one recipient.")

    client = zulip.init_from_options(options)

    if not options.message:
        options.message = sys.stdin.read()

    if options.stream:
        message_data = {
            "type": "stream",
            "content": options.message,
            "subject": options.subject,
            "to": options.stream,
        }
    else:
        message_data = {
            "type": "private",
            "content": options.message,
            "to": options.recipients,
        }

    if not do_send_message(client, message_data):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
