#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import traceback
from types import FrameType

from zulip import RandomExponentialBackoff


def die(signal: int, frame: FrameType) -> None:
    """We actually want to exit, so run os._exit (so as not to be caught and restarted)"""
    os._exit(1)


signal.signal(signal.SIGINT, die)

args = [os.path.join(os.path.dirname(sys.argv[0]), "jabber_mirror_backend.py")]
args.extend(sys.argv[1:])

backoff = RandomExponentialBackoff(timeout_success_equivalent=300)
while backoff.keep_going():
    print("Starting Jabber mirroring bot")
    try:
        ret = subprocess.call(args)
    except Exception:
        traceback.print_exc()
    else:
        if ret == 2:
            # Don't try again on initial configuration errors
            sys.exit(ret)

    backoff.fail()

print("")
print("")
print("ERROR: The Jabber mirroring bot is unable to continue mirroring Jabber.")
print("Please contact zulip-devel@googlegroups.com if you need assistance.")
print("")
sys.exit(1)
