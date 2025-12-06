#!/usr/bin/env python3

import hashlib
import json
import logging
import optparse
import os
import re
import select
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from types import FrameType
from typing import IO, Any, Dict, List, NoReturn, Optional, Set, Tuple, Union

from typing_extensions import Literal, TypedDict

from zulip import RandomExponentialBackoff

DEFAULT_SITE = "https://api.zulip.com"


class States:
    Startup, ZulipToZephyr, ZephyrToZulip, ChildSending = list(range(4))


CURRENT_STATE = States.Startup

logger: logging.Logger


def to_zulip_username(zephyr_username: str) -> str:
    if "@" in zephyr_username:
        (user, realm) = zephyr_username.split("@")
    else:
        (user, realm) = (zephyr_username, "ATHENA.MIT.EDU")
    if realm.upper() == "ATHENA.MIT.EDU":
        # Hack to make ctl's fake username setup work :)
        if user.lower() == "golem":
            user = "ctl"
        return user.lower() + "@mit.edu"
    return user.lower() + "|" + realm.upper() + "@mit.edu"


def to_zephyr_username(zulip_username: str) -> str:
    (user, realm) = zulip_username.split("@")
    if "|" not in user:
        # Hack to make ctl's fake username setup work :)
        if user.lower() == "ctl":
            user = "golem"
        return user.lower() + "@ATHENA.MIT.EDU"
    match_user = re.match(r"([a-zA-Z0-9_]+)\|(.+)", user)
    if not match_user:
        raise Exception(f"Could not parse Zephyr realm for cross-realm user {zulip_username}")
    return match_user.group(1).lower() + "@" + match_user.group(2).upper()


# Checks whether the pair of adjacent lines would have been
# linewrapped together, had they been intended to be parts of the same
# paragraph.  Our check is whether if you move the first word on the
# 2nd line onto the first line, the resulting line is either (1)
# significantly shorter than the following line (which, if they were
# in the same paragraph, should have been wrapped in a way consistent
# with how the previous line was wrapped) or (2) shorter than 60
# characters (our assumed minimum linewrapping threshold for Zephyr)
# or (3) the first word of the next line is longer than this entire
# line.
def different_paragraph(line: str, next_line: str) -> bool:
    words = next_line.split()
    return (
        len(line + " " + words[0]) < len(next_line) * 0.8
        or len(line + " " + words[0]) < 50
        or len(line) < len(words[0])
    )


# Linewrapping algorithm based on:
# http://gcbenison.wordpress.com/2011/07/03/a-program-to-intelligently-remove-carriage-returns-so-you-can-paste-text-without-having-it-look-awful/ #ignorelongline
def unwrap_lines(body: str) -> str:
    lines = body.split("\n")
    result = ""
    previous_line = lines[0]
    for line in lines[1:]:
        line = line.rstrip()
        if re.match(r"^\W", line, flags=re.UNICODE) and re.match(
            r"^\W", previous_line, flags=re.UNICODE
        ):
            result += previous_line + "\n"
        elif (
            line == ""
            or previous_line == ""
            or re.match(r"^\W", line, flags=re.UNICODE)
            or different_paragraph(previous_line, line)
        ):
            # Use 2 newlines to separate sections so that we
            # trigger proper Markdown processing on things like
            # bulleted lists
            result += previous_line + "\n\n"
        else:
            result += previous_line + " "
        previous_line = line
    result += previous_line
    return result


class ZephyrDict(TypedDict, total=False):
    type: Literal["private", "stream"]
    time: str
    sender: str
    stream: str
    subject: str
    recipient: Union[str, List[str]]
    content: str
    zsig: str


def send_zulip(zeph: ZephyrDict) -> Dict[str, Any]:
    message: Dict[str, Any]
    message = {}
    if options.forward_class_messages:
        message["forged"] = "yes"
    message["type"] = zeph["type"]
    message["time"] = zeph["time"]
    message["sender"] = to_zulip_username(zeph["sender"])
    if "subject" in zeph:
        # Truncate the subject to the current limit in Zulip.  No
        # need to do this for stream names, since we're only
        # subscribed to valid stream names.
        message["subject"] = zeph["subject"][:60]
    if zeph["type"] == "stream":
        # Forward messages sent to -c foo -i bar to stream bar subject "instance"
        if zeph["stream"] == "message":
            message["to"] = zeph["subject"].lower()
            message["subject"] = "instance {}".format(zeph["subject"])
        elif zeph["stream"] == "tabbott-test5":
            message["to"] = zeph["subject"].lower()
            message["subject"] = "test instance {}".format(zeph["subject"])
        else:
            message["to"] = zeph["stream"]
    else:
        message["to"] = zeph["recipient"]
    message["content"] = unwrap_lines(zeph["content"])

    if options.test_mode and options.site == DEFAULT_SITE:
        logger.debug(f"Message is: {str(message)}")
        return {"result": "success"}

    return zulip_client.send_message(message)


def send_error_zulip(error_msg: str) -> None:
    message = {
        "type": "private",
        "sender": zulip_account_email,
        "to": zulip_account_email,
        "content": error_msg,
    }
    zulip_client.send_message(message)


current_zephyr_subs = set()


def zephyr_bulk_subscribe(subs: List[Tuple[str, str, str]]) -> None:
    try:
        zephyr._z.subAll(subs)
    except OSError:
        # Since we haven't added the subscription to
        # current_zephyr_subs yet, we can just return (so that we'll
        # continue processing normal messages) and we'll end up
        # retrying the next time the bot checks its subscriptions are
        # up to date.
        logger.exception("Error subscribing to streams (will retry automatically):")
        logger.warning(f"Streams were: {[cls for cls, instance, recipient in subs]}")
        return
    try:
        actual_zephyr_subs = [cls for (cls, _, _) in zephyr._z.getSubscriptions()]
    except OSError:
        logger.exception("Error getting current Zephyr subscriptions")
        # Don't add anything to current_zephyr_subs so that we'll
        # retry the next time we check for streams to subscribe to
        # (within 15 seconds).
        return
    for (cls, instance, recipient) in subs:
        if cls not in actual_zephyr_subs:
            logger.error(f"Zephyr failed to subscribe us to {cls}; will retry")
            try:
                # We'll retry automatically when we next check for
                # streams to subscribe to (within 15 seconds), but
                # it's worth doing 1 retry immediately to avoid
                # missing 15 seconds of messages on the affected
                # classes
                zephyr._z.sub(cls, instance, recipient)
            except OSError:
                pass
        else:
            current_zephyr_subs.add(cls)


def update_subscriptions() -> None:
    try:
        f = open(options.stream_file_path)
        public_streams: List[str] = json.loads(f.read())
        f.close()
    except Exception:
        logger.exception("Error reading public streams:")
        return

    classes_to_subscribe = set()
    for stream in public_streams:
        zephyr_class = stream
        if options.shard is not None and not hashlib.sha1(
            zephyr_class.encode("utf-8")
        ).hexdigest().startswith(options.shard):
            # This stream is being handled by a different zephyr_mirror job.
            continue
        if zephyr_class in current_zephyr_subs:
            continue
        classes_to_subscribe.add((zephyr_class, "*", "*"))

    if len(classes_to_subscribe) > 0:
        zephyr_bulk_subscribe(list(classes_to_subscribe))


def maybe_kill_child() -> None:
    try:
        if child_pid is not None:
            os.kill(child_pid, signal.SIGTERM)
    except OSError:
        # We don't care if the child process no longer exists, so just log the error
        logger.exception("")


def maybe_restart_mirroring_script() -> None:
    if os.stat(
        os.path.join(options.stamp_path, "stamps", "restart_stamp")
    ).st_mtime > start_time or (
        (options.user == "tabbott" or options.user == "tabbott/extra")
        and os.stat(os.path.join(options.stamp_path, "stamps", "tabbott_stamp")).st_mtime
        > start_time
    ):
        logger.warning("")
        logger.warning("zephyr mirroring script has been updated; restarting...")
        maybe_kill_child()
        try:
            zephyr._z.cancelSubs()
        except OSError:
            # We don't care whether we failed to cancel subs properly, but we should log it
            logger.exception("")
        backoff = RandomExponentialBackoff(
            maximum_retries=3,
        )
        while backoff.keep_going():
            try:
                os.execvp(os.path.abspath(__file__), sys.argv)
                # No need for backoff.succeed, since this can't be reached
            except Exception:
                logger.exception("Error restarting mirroring script; trying again... Traceback:")
                backoff.fail()
        raise Exception("Failed to reload too many times, aborting!")


def process_loop(log: Optional[IO[str]]) -> NoReturn:
    restart_check_count = 0
    last_check_time = time.time()
    recieve_backoff = RandomExponentialBackoff()
    while True:
        select.select([zephyr._z.getFD()], [], [], 15)
        try:
            process_backoff = RandomExponentialBackoff()
            # Fetch notices from the queue until its empty
            while True:
                notice = zephyr.receive(block=False)
                recieve_backoff.succeed()
                if notice is None:
                    break
                try:
                    process_notice(notice, log)
                    process_backoff.succeed()
                except Exception:
                    logger.exception("Error relaying zephyr:")
                    process_backoff.fail()
        except Exception:
            logger.exception("Error checking for new zephyrs:")
            recieve_backoff.fail()
            continue

        if time.time() - last_check_time > 15:
            last_check_time = time.time()
            try:
                maybe_restart_mirroring_script()
                if restart_check_count > 0:
                    logger.info("Stopped getting errors checking whether restart is required.")
                    restart_check_count = 0
            except Exception:
                if restart_check_count < 5:
                    logger.exception("Error checking whether restart is required:")
                    restart_check_count += 1

            if options.forward_class_messages:
                try:
                    update_subscriptions()
                except Exception:
                    logger.exception("Error updating subscriptions from Zulip:")


def parse_zephyr_body(zephyr_data: str, notice_format: str) -> Tuple[str, str]:
    try:
        (zsig, body) = zephyr_data.split("\x00", 1)
        if (
            notice_format == "New transaction [$1] entered in $2\nFrom: $3 ($5)\nSubject: $4"
            or notice_format == "New transaction [$1] entered in $2\nFrom: $3\nSubject: $4"
        ):
            # Logic based off of owl_zephyr_get_message in barnowl
            fields = body.split("\x00")
            if len(fields) == 5:
                body = "New transaction [{}] entered in {}\nFrom: {} ({})\nSubject: {}".format(
                    fields[0],
                    fields[1],
                    fields[2],
                    fields[4],
                    fields[3],
                )
    except ValueError:
        (zsig, body) = ("", zephyr_data)
    # Clean body of any null characters, since they're invalid in our protocol.
    body = body.replace("\x00", "")
    return (zsig, body)


def parse_crypt_table(zephyr_class: str, instance: str) -> Optional[str]:
    try:
        crypt_table = open(os.path.join(os.environ["HOME"], ".crypt-table"))
    except OSError:
        return None

    for line in crypt_table.readlines():
        if line.strip() == "":
            # Ignore blank lines
            continue
        match = re.match(
            r"^crypt-(?P<class>\S+):\s+((?P<algorithm>(AES|DES)):\s+)?(?P<keypath>\S+)$", line
        )
        if match is None:
            # Malformed crypt_table line
            logger.debug("Invalid crypt_table line!")
            continue
        groups = match.groupdict()
        if (
            groups["class"].lower() == zephyr_class
            and "keypath" in groups
            and groups.get("algorithm") == "AES"
        ):
            return groups["keypath"]
    return None


def decrypt_zephyr(zephyr_class: str, instance: str, body: str) -> str:
    keypath = parse_crypt_table(zephyr_class, instance)
    if keypath is None:
        # We can't decrypt it, so we just return the original body
        return body

    # Enable handling SIGCHLD briefly while we call into
    # subprocess to avoid http://bugs.python.org/issue9127
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    # decrypt the message!
    p = subprocess.Popen(
        [
            "gpg",
            "--decrypt",
            "--no-options",
            "--no-default-keyring",
            "--keyring=/dev/null",
            "--secret-keyring=/dev/null",
            "--batch",
            "--quiet",
            "--no-use-agent",
            "--passphrase-file",
            keypath,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        errors="replace",
    )
    decrypted, _ = p.communicate(input=body)
    # Restore our ignoring signals
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    return decrypted


def process_notice(notice: "zephyr.ZNotice", log: Optional[IO[str]]) -> None:
    assert notice.sender is not None
    (zsig, body) = parse_zephyr_body(notice.message, notice.format)
    is_personal = False
    is_huddle = False

    if notice.opcode == "PING":
        # skip PING messages
        return

    zephyr_class = notice.cls.lower()

    if zephyr_class == options.nagios_class:
        # Mark that we got the message and proceed
        with open(options.nagios_path, "w") as f:
            f.write("0\n")
        return

    if notice.recipient != "":
        is_personal = True
    # Drop messages not to the listed subscriptions
    if is_personal and not options.forward_personals:
        return
    if (zephyr_class not in current_zephyr_subs) and not is_personal:
        logger.debug(f"Skipping ... {zephyr_class}/{notice.instance}/{is_personal}")
        return
    if notice.format.startswith("Zephyr error: See") or notice.format.endswith("@(@color(blue))"):
        logger.debug("Skipping message we got from Zulip!")
        return
    if (
        zephyr_class == "mail"
        and notice.instance.lower() == "inbox"
        and is_personal
        and not options.forward_mail_zephyrs
    ):
        # Only forward mail zephyrs if forwarding them is enabled.
        return

    if is_personal:
        if body.startswith("CC:"):
            is_huddle = True
            # Map "CC: user1 user2" => "user1@mit.edu, user2@mit.edu"
            huddle_recipients = [
                to_zulip_username(x.strip()) for x in body.split("\n")[0][4:].split()
            ]
            if notice.sender not in huddle_recipients:
                huddle_recipients.append(to_zulip_username(notice.sender))
            body = body.split("\n", 1)[1]

    if (
        options.forward_class_messages
        and notice.opcode is not None
        and notice.opcode.lower() == "crypt"
    ):
        body = decrypt_zephyr(zephyr_class, notice.instance.lower(), body)

    zeph: ZephyrDict
    zeph = {
        "time": str(notice.time),
        "sender": notice.sender,
        "zsig": zsig,  # logged here but not used by app
        "content": body,
    }
    if is_huddle:
        zeph["type"] = "private"
        zeph["recipient"] = huddle_recipients
    elif is_personal:
        assert notice.recipient is not None
        zeph["type"] = "private"
        zeph["recipient"] = to_zulip_username(notice.recipient)
    else:
        zeph["type"] = "stream"
        zeph["stream"] = zephyr_class
        if notice.instance.strip() != "":
            zeph["subject"] = notice.instance
        else:
            zeph["subject"] = f'(instance "{notice.instance}")'

    # Add instances in for instanced personals
    if is_personal:
        if notice.cls.lower() != "message" and notice.instance.lower() != "personal":
            heading = f"[-c {notice.cls} -i {notice.instance}]\n"
        elif notice.cls.lower() != "message":
            heading = f"[-c {notice.cls}]\n"
        elif notice.instance.lower() != "personal":
            heading = f"[-i {notice.instance}]\n"
        else:
            heading = ""
        zeph["content"] = heading + zeph["content"]

    logger.info(f"Received a message on {zephyr_class}/{notice.instance} from {notice.sender}...")
    if log is not None:
        log.write(json.dumps(zeph) + "\n")
        log.flush()

    if os.fork() == 0:
        global CURRENT_STATE
        CURRENT_STATE = States.ChildSending
        # Actually send the message in a child process, to avoid blocking.
        try:
            res = send_zulip(zeph)
            if res.get("result") != "success":
                logger.error(f"Error relaying zephyr:\n{zeph}\n{res}")
        except Exception:
            logger.exception("Error relaying zephyr:")
        finally:
            os._exit(0)


def quit_failed_initialization(message: str) -> str:
    logger.error(message)
    maybe_kill_child()
    sys.exit(1)


def zephyr_init_autoretry() -> None:
    backoff = zulip.RandomExponentialBackoff()
    while backoff.keep_going():
        try:
            # zephyr.init() tries to clear old subscriptions, and thus
            # sometimes gets a SERVNAK from the server
            zephyr.init()
            backoff.succeed()
            return
        except OSError:
            logger.exception("Error initializing Zephyr library (retrying).  Traceback:")
            backoff.fail()

    quit_failed_initialization("Could not initialize Zephyr library, quitting!")


def zephyr_load_session_autoretry(session_path: str) -> None:
    backoff = zulip.RandomExponentialBackoff()
    while backoff.keep_going():
        try:
            with open(session_path, "rb") as f:
                session = f.read()
            zephyr._z.initialize()
            zephyr._z.load_session(session)
            zephyr.__inited = True
            return
        except OSError:
            logger.exception("Error loading saved Zephyr session (retrying).  Traceback:")
            backoff.fail()

    quit_failed_initialization("Could not load saved Zephyr session, quitting!")


def zephyr_subscribe_autoretry(sub: Tuple[str, str, str]) -> None:
    backoff = zulip.RandomExponentialBackoff()
    while backoff.keep_going():
        try:
            zephyr.Subscriptions().add(sub)
            backoff.succeed()
            return
        except OSError:
            # Probably a SERVNAK from the zephyr server, but log the
            # traceback just in case it's something else
            logger.exception("Error subscribing to personals (retrying).  Traceback:")
            backoff.fail()

    quit_failed_initialization("Could not subscribe to personals, quitting!")


def zephyr_to_zulip(options: optparse.Values) -> None:
    if options.use_sessions and os.path.exists(options.session_path):
        logger.info("Loading old session")
        zephyr_load_session_autoretry(options.session_path)
    else:
        zephyr_init_autoretry()
        if options.forward_class_messages:
            update_subscriptions()
        if options.forward_personals:
            # Subscribe to personals; we really can't operate without
            # those subscriptions, so just retry until it works.
            zephyr_subscribe_autoretry(("message", "*", "%me%"))
            zephyr_subscribe_autoretry(("mail", "inbox", "%me%"))
        if options.nagios_class:
            zephyr_subscribe_autoretry((options.nagios_class, "*", "*"))
        if options.use_sessions:
            with open(options.session_path, "wb") as f:
                f.write(zephyr._z.dump_session())

    if options.logs_to_resend is not None:
        with open(options.logs_to_resend) as log:
            for ln in log:
                try:
                    zeph = json.loads(ln)
                    # Handle importing older zephyrs in the logs
                    # where it isn't called a "stream" yet
                    if "class" in zeph:
                        zeph["stream"] = zeph["class"]
                    if "instance" in zeph:
                        zeph["subject"] = zeph["instance"]
                    logger.info(
                        "sending saved message to %s from %s..."
                        % (zeph.get("stream", zeph.get("recipient")), zeph["sender"])
                    )
                    send_zulip(zeph)
                except Exception:
                    logger.exception("Could not send saved zephyr:")
                    time.sleep(2)

    logger.info("Successfully initialized; Starting receive loop.")

    if options.resend_log_path is not None:
        with open(options.resend_log_path, "a") as log:
            process_loop(log)
    else:
        process_loop(None)


def send_zephyr(zwrite_args: List[str], content: str) -> Tuple[int, str]:
    p = subprocess.Popen(
        zwrite_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = p.communicate(input=content)
    if p.returncode:
        logger.error(
            "zwrite command '%s' failed with return code %d:"
            % (
                " ".join(zwrite_args),
                p.returncode,
            )
        )
        if stdout:
            logger.info("stdout: " + stdout)
    elif stderr:
        logger.warning(
            "zwrite command '{}' printed the following warning:".format(" ".join(zwrite_args))
        )
    if stderr:
        logger.warning("stderr: " + stderr)
    return (p.returncode, stderr)


def send_authed_zephyr(zwrite_args: List[str], content: str) -> Tuple[int, str]:
    return send_zephyr(zwrite_args, content)


def send_unauthed_zephyr(zwrite_args: List[str], content: str) -> Tuple[int, str]:
    return send_zephyr(zwrite_args + ["-d"], content)


def zcrypt_encrypt_content(zephyr_class: str, instance: str, content: str) -> Optional[str]:
    keypath = parse_crypt_table(zephyr_class, instance)
    if keypath is None:
        return None

    # encrypt the message!
    p = subprocess.Popen(
        [
            "gpg",
            "--symmetric",
            "--no-options",
            "--no-default-keyring",
            "--keyring=/dev/null",
            "--secret-keyring=/dev/null",
            "--batch",
            "--quiet",
            "--no-use-agent",
            "--armor",
            "--cipher-algo",
            "AES",
            "--passphrase-file",
            keypath,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    encrypted, _ = p.communicate(input=content)
    return encrypted


def forward_to_zephyr(message: Dict[str, Any]) -> None:
    # 'Any' can be of any type of text
    support_heading = "Hi there! This is an automated message from Zulip."
    support_closing = """If you have any questions, please be in touch through the \
Feedback button or at support@zulip.com."""

    wrapper = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
    wrapped_content = "\n".join(
        "\n".join(wrapper.wrap(line)) for line in message["content"].replace("@", "@@").split("\n")
    )

    zwrite_args = [
        "zwrite",
        "-n",
        "-s",
        message["sender_full_name"],
        "-F",
        "Zephyr error: See http://zephyr.1ts.org/wiki/df",
        "-x",
        "UTF-8",
    ]

    # Hack to make ctl's fake username setup work :)
    if message["type"] == "stream" and zulip_account_email == "ctl@mit.edu":
        zwrite_args.extend(["-S", "ctl"])

    if message["type"] == "stream":
        zephyr_class = message["display_recipient"]
        instance = message["subject"]

        match_whitespace_instance = re.match(r'^\(instance "(\s*)"\)$', instance)
        if match_whitespace_instance:
            # Forward messages sent to '(instance "WHITESPACE")' back to the
            # appropriate WHITESPACE instance for bidirectional mirroring
            instance = match_whitespace_instance.group(1)
        elif instance == f"instance {zephyr_class}" or instance == "test instance {}".format(
            zephyr_class,
        ):
            # Forward messages to e.g. -c -i white-magic back from the
            # place we forward them to
            if instance.startswith("test"):
                instance = zephyr_class
                zephyr_class = "tabbott-test5"
            else:
                instance = zephyr_class
                zephyr_class = "message"
        zwrite_args.extend(["-c", zephyr_class, "-i", instance])
        logger.info(f"Forwarding message to class {zephyr_class}, instance {instance}")
    elif message["type"] == "private":
        if len(message["display_recipient"]) == 1:
            recipient = to_zephyr_username(message["display_recipient"][0]["email"])
            recipients = [recipient]
        elif len(message["display_recipient"]) == 2:
            recipient = ""
            for r in message["display_recipient"]:
                if r["email"].lower() != zulip_account_email.lower():
                    recipient = to_zephyr_username(r["email"])
                    break
            recipients = [recipient]
        else:
            zwrite_args.extend(["-C"])
            # We drop the @ATHENA.MIT.EDU here because otherwise the
            # "CC: user1 user2 ..." output will be unnecessarily verbose.
            recipients = [
                to_zephyr_username(user["email"]).replace("@ATHENA.MIT.EDU", "")
                for user in message["display_recipient"]
            ]
        logger.info(f"Forwarding message to {recipients}")
        zwrite_args.extend(recipients)

    if message.get("invite_only_stream"):
        result = zcrypt_encrypt_content(zephyr_class, instance, wrapped_content)
        if result is None:
            send_error_zulip(
                """%s

Your Zulip-Zephyr mirror bot was unable to forward that last message \
from Zulip to Zephyr because you were sending to a zcrypted Zephyr \
class and your mirroring bot does not have access to the relevant \
key (perhaps because your AFS tokens expired). That means that while \
Zulip users (like you) received it, Zephyr users did not.

%s"""
                % (support_heading, support_closing)
            )
            return

        # Proceed with sending a zcrypted message
        wrapped_content = result
        zwrite_args.extend(["-O", "crypt"])

    if options.test_mode:
        logger.debug(f"Would have forwarded: {zwrite_args}\n{wrapped_content}")
        return

    (code, stderr) = send_authed_zephyr(zwrite_args, wrapped_content)
    if code == 0 and stderr == "":
        return
    elif code == 0:
        send_error_zulip(
            """%s

Your last message was successfully mirrored to zephyr, but zwrite \
returned the following warning:

%s

%s"""
            % (support_heading, stderr, support_closing)
        )
        return
    elif code != 0 and (
        stderr.startswith("zwrite: Ticket expired while sending notice to ")
        or stderr.startswith("zwrite: No credentials cache found while sending notice to ")
    ):
        # Retry sending the message unauthenticated; if that works,
        # just notify the user that they need to renew their tickets
        (code, stderr) = send_unauthed_zephyr(zwrite_args, wrapped_content)
        if code == 0:
            if options.ignore_expired_tickets:
                return
            send_error_zulip(
                """%s

Your last message was forwarded from Zulip to Zephyr unauthenticated, \
because your Kerberos tickets have expired. It was sent successfully, \
but please renew your Kerberos tickets in the screen session where you \
are running the Zulip-Zephyr mirroring bot, so we can send \
authenticated Zephyr messages for you again.

%s"""
                % (support_heading, support_closing)
            )
            return

    # zwrite failed and it wasn't because of expired tickets: This is
    # probably because the recipient isn't subscribed to personals,
    # but regardless, we should just notify the user.
    send_error_zulip(
        """%s

Your Zulip-Zephyr mirror bot was unable to forward that last message \
from Zulip to Zephyr. That means that while Zulip users (like you) \
received it, Zephyr users did not.  The error message from zwrite was:

%s

%s"""
        % (support_heading, stderr, support_closing)
    )
    return


def maybe_forward_to_zephyr(message: Dict[str, Any]) -> None:
    # The key string can be used to direct any type of text.
    if message["sender_email"] == zulip_account_email:
        if not (
            (message["type"] == "stream")
            or (
                message["type"] == "private"
                and False
                not in [
                    u["email"].lower().endswith("mit.edu") for u in message["display_recipient"]
                ]
            )
        ):
            # Don't try forward private messages with non-MIT users
            # to MIT Zephyr.
            return
        timestamp_now = int(time.time())
        if float(message["timestamp"]) < timestamp_now - 15:
            logger.warning(
                "Skipping out of order message: {} < {}".format(message["timestamp"], timestamp_now)
            )
            return
        try:
            forward_to_zephyr(message)
        except Exception:
            # Don't let an exception forwarding one message crash the
            # whole process
            logger.exception("Error forwarding message:")


def zulip_to_zephyr(options: optparse.Values) -> NoReturn:
    # Sync messages from zulip to zephyr
    logger.info("Starting syncing messages.")
    backoff = RandomExponentialBackoff(timeout_success_equivalent=120)
    while True:
        try:
            zulip_client.call_on_each_message(maybe_forward_to_zephyr)
        except Exception:
            logger.exception("Error syncing messages:")
            backoff.fail()


def subscribed_to_mail_messages() -> bool:
    # In case we have lost our AFS tokens and those won't be able to
    # parse the Zephyr subs file, first try reading in result of this
    # query from the environment so we can avoid the filesystem read.
    stored_result = os.environ.get("HUMBUG_FORWARD_MAIL_ZEPHYRS")
    if stored_result is not None:
        return stored_result == "True"
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=False):
        if cls.lower() == "mail" and instance.lower() == "inbox":
            os.environ["HUMBUG_FORWARD_MAIL_ZEPHYRS"] = "True"
            return True
    os.environ["HUMBUG_FORWARD_MAIL_ZEPHYRS"] = "False"
    return False


def add_zulip_subscriptions(verbose: bool) -> None:
    zephyr_subscriptions = set()
    skipped = set()
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=verbose):
        if cls.lower() == "message":
            if recipient != "*":
                # We already have a (message, *, you) subscription, so
                # these are redundant
                continue
            # We don't support subscribing to (message, *)
            if instance == "*":
                if recipient == "*":
                    skipped.add(
                        (
                            cls,
                            instance,
                            recipient,
                            "subscribing to all of class message is not supported.",
                        )
                    )
                continue
            # If you're on -i white-magic on zephyr, get on stream white-magic on zulip
            # instead of subscribing to stream "message" on zulip
            zephyr_subscriptions.add(instance)
            continue
        elif cls.lower() == "mail" and instance.lower() == "inbox":
            # We forward mail zephyrs, so no need to log a warning.
            continue
        elif len(cls) > 60:
            skipped.add((cls, instance, recipient, "Class longer than 60 characters"))
            continue
        elif instance != "*":
            skipped.add((cls, instance, recipient, "Unsupported non-* instance"))
            continue
        elif recipient != "*":
            skipped.add((cls, instance, recipient, "Unsupported non-* recipient."))
            continue
        zephyr_subscriptions.add(cls)

    if len(zephyr_subscriptions) != 0:
        res = zulip_client.add_subscriptions(
            list({"name": stream} for stream in zephyr_subscriptions),
            authorization_errors_fatal=False,
        )
        if res.get("result") != "success":
            logger.error("Error subscribing to streams:\n{}".format(res["msg"]))
            return

        already = res.get("already_subscribed")
        new = res.get("subscribed")
        unauthorized = res.get("unauthorized")
        if verbose:
            if already is not None and len(already) > 0:
                logger.info(
                    "\nAlready subscribed to: {}".format(", ".join(list(already.values())[0]))
                )
            if new is not None and len(new) > 0:
                logger.info(
                    "\nSuccessfully subscribed to: {}".format(", ".join(list(new.values())[0]))
                )
            if unauthorized is not None and len(unauthorized) > 0:
                logger.info(
                    "\n"
                    + "\n".join(
                        textwrap.wrap(
                            """\
The following streams you have NOT been subscribed to,
because they have been configured in Zulip as invitation-only streams.
This was done at the request of users of these Zephyr classes, usually
because traffic to those streams is sent within the Zephyr world encrypted
via zcrypt (in Zulip, we achieve the same privacy goals through invitation-only streams).
If you wish to read these streams in Zulip, you need to contact the people who are
on these streams and already use Zulip.  They can subscribe you to them via the
"streams" page in the Zulip web interface:
"""
                        )
                    )
                    + "\n\n  {}".format(", ".join(unauthorized))
                )

    if len(skipped) > 0:
        if verbose:
            logger.info(
                "\n"
                + "\n".join(
                    textwrap.wrap(
                        """\
You have some lines in ~/.zephyr.subs that could not be
synced to your Zulip subscriptions because they do not
use "*" as both the instance and recipient and not one of
the special cases (e.g. personals and mail zephyrs) that
Zulip has a mechanism for forwarding.  Zulip does not
allow subscribing to only some subjects on a Zulip
stream, so this tool has not created a corresponding
Zulip subscription to these lines in ~/.zephyr.subs:
"""
                    )
                )
                + "\n"
            )

    for (cls, instance, recipient, reason) in skipped:
        if verbose:
            if reason != "":
                logger.info(f"  [{cls},{instance},{recipient}] ({reason})")
            else:
                logger.info(f"  [{cls},{instance},{recipient}]")
    if len(skipped) > 0:
        if verbose:
            logger.info(
                "\n"
                + "\n".join(
                    textwrap.wrap(
                        """\
If you wish to be subscribed to any Zulip streams related
to these .zephyrs.subs lines, please do so via the Zulip
web interface.
"""
                    )
                )
                + "\n"
            )


def valid_stream_name(name: str) -> bool:
    return name != ""


def parse_zephyr_subs(verbose: bool = False) -> Set[Tuple[str, str, str]]:
    zephyr_subscriptions = set()  # type: Set[Tuple[str, str, str]]
    subs_file = os.path.join(os.environ["HOME"], ".zephyr.subs")
    if not os.path.exists(subs_file):
        if verbose:
            logger.error("Couldn't find ~/.zephyr.subs!")
        return zephyr_subscriptions

    for line in open(subs_file).readlines():
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            (cls, instance, recipient) = line.split(",")
            cls = cls.replace("%me%", options.user)
            instance = instance.replace("%me%", options.user)
            recipient = recipient.replace("%me%", options.user)
            if not valid_stream_name(cls):
                if verbose:
                    logger.error(f"Skipping subscription to unsupported class name: [{line}]")
                continue
        except Exception:
            if verbose:
                logger.error(f"Couldn't parse ~/.zephyr.subs line: [{line}]")
            continue
        zephyr_subscriptions.add((cls.strip(), instance.strip(), recipient.strip()))
    return zephyr_subscriptions


def open_logger() -> logging.Logger:
    if options.log_path is not None:
        log_file = options.log_path
    elif options.forward_class_messages:
        if options.test_mode:
            log_file = "/var/log/zulip/test-mirror-log"
        else:
            log_file = "/var/log/zulip/mirror-log"
    else:
        f = tempfile.NamedTemporaryFile(prefix=f"zulip-log.{options.user}.", delete=False)
        log_file = f.name
        # Close the file descriptor, since the logging system will
        # reopen it anyway.
        f.close()
    logger = logging.getLogger(__name__)
    log_format = "%(asctime)s <initial>: %(message)s"
    formatter = logging.Formatter(log_format)
    logging.basicConfig(format=log_format)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def configure_logger(logger: logging.Logger, direction_name: Optional[str]) -> None:
    if direction_name is None:
        log_format = "%(message)s"
    else:
        log_format = "%(asctime)s [" + direction_name + "] %(message)s"
    formatter = logging.Formatter(log_format)

    # Replace the formatters for the file and stdout loggers
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


def parse_args() -> Tuple[optparse.Values, List[str]]:
    parser = optparse.OptionParser()
    parser.add_option(
        "--forward-class-messages", default=False, help=optparse.SUPPRESS_HELP, action="store_true"
    )
    parser.add_option("--shard", help=optparse.SUPPRESS_HELP)
    parser.add_option("--noshard", default=False, help=optparse.SUPPRESS_HELP, action="store_true")
    parser.add_option("--resend-log", dest="logs_to_resend", help=optparse.SUPPRESS_HELP)
    parser.add_option("--enable-resend-log", dest="resend_log_path", help=optparse.SUPPRESS_HELP)
    parser.add_option("--log-path", dest="log_path", help=optparse.SUPPRESS_HELP)
    parser.add_option(
        "--stream-file-path",
        dest="stream_file_path",
        default="/home/zulip/public_streams",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option(
        "--no-forward-personals",
        dest="forward_personals",
        help=optparse.SUPPRESS_HELP,
        default=True,
        action="store_false",
    )
    parser.add_option(
        "--forward-mail-zephyrs",
        dest="forward_mail_zephyrs",
        help=optparse.SUPPRESS_HELP,
        default=False,
        action="store_true",
    )
    parser.add_option(
        "--no-forward-from-zulip",
        default=True,
        dest="forward_from_zulip",
        help=optparse.SUPPRESS_HELP,
        action="store_false",
    )
    parser.add_option("--verbose", default=False, help=optparse.SUPPRESS_HELP, action="store_true")
    parser.add_option("--sync-subscriptions", default=False, action="store_true")
    parser.add_option("--ignore-expired-tickets", default=False, action="store_true")
    parser.add_option("--site", default=DEFAULT_SITE, help=optparse.SUPPRESS_HELP)
    parser.add_option("--on-startup-command", default=None, help=optparse.SUPPRESS_HELP)
    parser.add_option("--user", default=os.environ["USER"], help=optparse.SUPPRESS_HELP)
    parser.add_option(
        "--stamp-path",
        default="/afs/athena.mit.edu/user/t/a/tabbott/for_friends",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option("--session-path", default=None, help=optparse.SUPPRESS_HELP)
    parser.add_option("--nagios-class", default=None, help=optparse.SUPPRESS_HELP)
    parser.add_option("--nagios-path", default=None, help=optparse.SUPPRESS_HELP)
    parser.add_option(
        "--use-sessions", default=False, action="store_true", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "--test-mode", default=False, help=optparse.SUPPRESS_HELP, action="store_true"
    )
    parser.add_option(
        "--api-key-file", default=os.path.join(os.environ["HOME"], "Private", ".humbug-api-key")
    )
    return parser.parse_args()


def die_gracefully(signal: int, frame: FrameType) -> None:
    if CURRENT_STATE == States.ZulipToZephyr or CURRENT_STATE == States.ChildSending:
        # this is a child process, so we want os._exit (no clean-up necessary)
        os._exit(1)

    if CURRENT_STATE == States.ZephyrToZulip and not options.use_sessions:
        try:
            # zephyr=>zulip processes may have added subs, so run cancelSubs
            zephyr._z.cancelSubs()
        except OSError:
            # We don't care whether we failed to cancel subs properly, but we should log it
            logger.exception("")

    sys.exit(1)


if __name__ == "__main__":
    # Set the SIGCHLD handler back to SIG_DFL to prevent these errors
    # when importing the "requests" module after being restarted using
    # the restart_stamp functionality:
    #
    # close failed in file object destructor:
    # IOError: [Errno 10] No child processes
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    signal.signal(signal.SIGINT, die_gracefully)

    (options, args) = parse_args()

    logger = open_logger()
    configure_logger(logger, "parent")

    # In case this is an automated restart of the mirroring script,
    # and we have lost AFS tokens, first try reading the API key from
    # the environment so that we can skip doing a filesystem read.
    if os.environ.get("HUMBUG_API_KEY") is not None:
        api_key = os.environ.get("HUMBUG_API_KEY")
    else:
        if not os.path.exists(options.api_key_file):
            logger.error(
                "\n"
                + "\n".join(
                    textwrap.wrap(
                        """\
Could not find API key file.
You need to either place your api key file at %s,
or specify the --api-key-file option."""
                        % (options.api_key_file,)
                    )
                )
            )
            sys.exit(1)
        api_key = open(options.api_key_file).read().strip()
        # Store the API key in the environment so that our children
        # don't need to read it in
        os.environ["HUMBUG_API_KEY"] = api_key

    if options.nagios_path is None and options.nagios_class is not None:
        logger.error("\n" + "nagios_path is required with nagios_class\n")
        sys.exit(1)

    zulip_account_email = options.user + "@mit.edu"
    import zulip

    zulip_client = zulip.Client(
        email=zulip_account_email,
        api_key=api_key,
        verbose=True,
        client="zephyr_mirror",
        site=options.site,
    )

    start_time = time.time()

    if options.sync_subscriptions:
        configure_logger(logger, None)  # make the output cleaner
        logger.info("Syncing your ~/.zephyr.subs to your Zulip Subscriptions!")
        add_zulip_subscriptions(True)
        sys.exit(0)

    # Kill all zephyr_mirror processes other than this one and its parent.
    if not options.test_mode:
        pgrep_query = "python.*zephyr_mirror"
        if options.shard is not None:
            # sharded class mirror
            pgrep_query = f"{pgrep_query}.*--shard={options.shard}"
        elif options.user is not None:
            # Personals mirror on behalf of another user.
            pgrep_query = f"{pgrep_query}.*--user={options.user}"
        proc = subprocess.Popen(
            ["pgrep", "-U", os.environ["USER"], "-f", pgrep_query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, _err_unused = proc.communicate()
        for pid in map(int, out.split()):
            if pid == os.getpid() or pid == os.getppid():
                continue

            # Another copy of zephyr_mirror.py!  Kill it.
            logger.info(f"Killing duplicate zephyr_mirror process {pid}")
            try:
                os.kill(pid, signal.SIGINT)
            except OSError:
                # We don't care if the target process no longer exists, so just log the error
                logger.exception("")

    if options.shard is not None and set(options.shard) != set("a"):
        # The shard that is all "a"s is the one that handles personals
        # forwarding and zulip => zephyr forwarding
        options.forward_personals = False
        options.forward_from_zulip = False
    if options.forward_mail_zephyrs is None:
        options.forward_mail_zephyrs = subscribed_to_mail_messages()

    if options.session_path is None:
        options.session_path = f"/var/tmp/{options.user}"

    if options.forward_from_zulip:
        child_pid = os.fork()  # type: Optional[int]
        if child_pid == 0:
            CURRENT_STATE = States.ZulipToZephyr
            # Run the zulip => zephyr mirror in the child
            configure_logger(logger, "zulip=>zephyr")
            zulip_to_zephyr(options)
    else:
        child_pid = None
    CURRENT_STATE = States.ZephyrToZulip

    import zephyr

    logger_name = "zephyr=>zulip"
    if options.shard is not None:
        logger_name += f"({options.shard})"
    configure_logger(logger, logger_name)
    # Have the kernel reap children for when we fork off processes to send Zulips
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    zephyr_to_zulip(options)
