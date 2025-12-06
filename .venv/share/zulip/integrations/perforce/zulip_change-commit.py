#!/usr/bin/env python3

"""Zulip notification change-commit hook.

In Perforce, The "change-commit" trigger is fired after a metadata has been
created, files have been transferred, and the changelist committed to the depot
database.

This specific trigger expects command-line arguments in the form:
  %change% %changeroot%

For example:
  1234 //depot/security/src/

"""

import os
import os.path
import sys

import git_p4

__version__ = "0.1"

sys.path.insert(0, os.path.dirname(__file__))
from typing import Any, Dict, Optional

import zulip_perforce_config as config

if config.ZULIP_API_PATH is not None:
    sys.path.append(config.ZULIP_API_PATH)

import zulip

client = zulip.Client(
    email=config.ZULIP_USER,
    site=config.ZULIP_SITE,
    api_key=config.ZULIP_API_KEY,
    client="ZulipPerforce/" + __version__,
)  # type: zulip.Client

try:
    changelist = int(sys.argv[1])  # type: int
    changeroot = sys.argv[2]  # type: str
except IndexError:
    print("Wrong number of arguments.\n\n", end=" ", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(-1)
except ValueError:
    print("First argument must be an integer.\n\n", end=" ", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(-1)

metadata = git_p4.p4_describe(changelist)  # type: Dict[str, str]

destination = config.commit_notice_destination(
    changeroot, changelist
)  # type: Optional[Dict[str, str]]

if destination is None:
    # Don't forward the notice anywhere
    sys.exit(0)

ignore_missing_stream = None
if hasattr(config, "ZULIP_IGNORE_MISSING_STREAM"):
    ignore_missing_stream = config.ZULIP_IGNORE_MISSING_STREAM

if ignore_missing_stream:
    # Check if the destination stream exists yet
    stream_state = client.get_stream_id(destination["stream"])
    if stream_state["result"] == "error":
        # Silently discard the message
        sys.exit(0)

change = metadata["change"]
p4web = None
if hasattr(config, "P4_WEB"):
    p4web = config.P4_WEB

if p4web is not None:
    # linkify the change number
    change = "[{change}]({p4web}/{change}?ac=10)".format(p4web=p4web, change=change)

message = """**{user}** committed revision @{change} to `{path}`.

```quote
{desc}
```
""".format(
    user=metadata["user"], change=change, path=changeroot, desc=metadata["desc"]
)  # type: str

message_data = {
    "type": "stream",
    "to": destination["stream"],
    "subject": destination["subject"],
    "content": message,
}  # type: Dict[str, Any]
client.send_message(message_data)
