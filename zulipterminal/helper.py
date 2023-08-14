"""
Helper functions used in multiple places
"""

import os
import subprocess
import time
from collections import defaultdict
from contextlib import contextmanager
from functools import partial, wraps
from itertools import chain, combinations
from re import ASCII, MULTILINE, findall, match
from tempfile import NamedTemporaryFile
from threading import Thread
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)
from urllib.parse import unquote

import requests
from typing_extensions import ParamSpec, TypedDict

from zulipterminal.api_types import Composition, EmojiType, Message
from zulipterminal.config.keys import primary_key_for_command
from zulipterminal.config.regexes import (
    REGEX_COLOR_3_DIGIT,
    REGEX_COLOR_6_DIGIT,
    REGEX_QUOTED_FENCE_LENGTH,
)
from zulipterminal.config.ui_mappings import StreamAccessType
from zulipterminal.platform_code import (
    PLATFORM,
    normalized_file_path,
    successful_GUI_return_code,
)


class StreamData(TypedDict):
    name: str
    id: int
    color: str
    stream_access_type: StreamAccessType
    description: str


class EmojiData(TypedDict):
    code: str
    aliases: List[str]
    type: EmojiType


NamedEmojiData = Dict[str, EmojiData]


class CustomProfileData(TypedDict):
    label: str
    value: Union[str, List[int]]
    type: int
    order: int


class TidiedUserInfo(TypedDict):
    full_name: str
    email: str
    date_joined: str
    timezone: str
    role: int
    last_active: str
    custom_profile_data: List[CustomProfileData]

    is_bot: bool
    # Below fields are only meaningful if is_bot == True
    bot_type: Optional[int]
    bot_owner_name: str


class Index(TypedDict):
    pointer: Dict[str, Optional[int]]  # narrow_str, message_id (or no data)
    # Various sets of downloaded message ids (all, starred, ...)
    all_msg_ids: Set[int]
    starred_msg_ids: Set[int]
    mentioned_msg_ids: Set[int]
    private_msg_ids: Set[int]
    private_msg_ids_by_user_ids: Dict[FrozenSet[int], Set[int]]
    stream_msg_ids_by_stream_id: Dict[int, Set[int]]
    topic_msg_ids: Dict[int, Dict[str, Set[int]]]
    # Extra cached information
    edited_messages: Set[int]  # {message_id, ...}
    topics: Dict[int, List[str]]  # {topic names, ...}
    search: Set[int]  # {message_id, ...}
    muted_messages: Set[int]
    # Downloaded message data by message id
    messages: Dict[int, Message]


initial_index = Index(
    pointer=dict(),
    all_msg_ids=set(),
    starred_msg_ids=set(),
    mentioned_msg_ids=set(),
    private_msg_ids=set(),
    private_msg_ids_by_user_ids=defaultdict(set),
    stream_msg_ids_by_stream_id=defaultdict(set),
    topic_msg_ids=defaultdict(dict),
    edited_messages=set(),
    topics=defaultdict(list),
    search=set(),
    muted_messages=set(),
    # mypy bug: https://github.com/python/mypy/issues/7217
    messages=defaultdict(lambda: Message()),
)


class UnreadCounts(TypedDict):
    all_msg: int
    all_pms: int
    all_mentions: int
    unread_topics: Dict[Tuple[int, str], int]  # stream_id, topic
    unread_pms: Dict[int, int]  # sender_id
    unread_huddles: Dict[FrozenSet[int], int]  # Group pms
    streams: Dict[int, int]  # stream_id


ParamT = ParamSpec("ParamT")


def asynch(func: Callable[ParamT, None]) -> Callable[ParamT, None]:
    """
    Decorator for executing a function in a separate :class:`threading.Thread`.
    """

    @wraps(func)
    def wrapper(*args: ParamT.args, **kwargs: ParamT.kwargs) -> None:
        # If calling when pytest is running simply return the function
        # to avoid running in asynch mode.
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return func(*args, **kwargs)

        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()

    return wrapper


def _set_count_in_model(
    new_count: int, changed_messages: List[Message], unread_counts: UnreadCounts
) -> None:
    """
    This function doesn't explicitly set counts in model,
    but updates `unread_counts` (which can update the model
    if it's passed in, but is not tied to it).
    """
    # broader unread counts (for all_*) are updated
    # later conditionally in _set_count_in_view.
    KeyT = TypeVar("KeyT")

    def update_unreads(unreads: Dict[KeyT, int], key: KeyT) -> None:
        if key in unreads:
            unreads[key] += new_count
            if unreads[key] == 0:
                unreads.pop(key)
        elif new_count == 1:
            unreads[key] = new_count

    for message in changed_messages:
        if message["type"] == "stream":
            stream_id = message["stream_id"]
            update_unreads(
                unread_counts["unread_topics"], (stream_id, message["subject"])
            )
            update_unreads(unread_counts["streams"], stream_id)
        # self-pm has only one display_recipient
        # 1-1 pms have 2 display_recipient
        elif len(message["display_recipient"]) <= 2:
            update_unreads(unread_counts["unread_pms"], message["sender_id"])
        else:  # If it's a group pm
            update_unreads(
                unread_counts["unread_huddles"],
                frozenset(
                    recipient["id"] for recipient in message["display_recipient"]
                ),
            )


def _set_count_in_view(
    controller: Any,
    new_count: int,
    changed_messages: List[Message],
    unread_counts: UnreadCounts,
) -> None:
    """
    This function for the most part contains the logic for setting the
    count in the UI buttons. The later buttons (all_msg, all_pms)
    additionally set the current count in the model and make use of the
    same in the UI.
    """
    stream_buttons_list = controller.view.stream_w.streams_btn_list
    is_open_topic_view = controller.view.left_panel.is_in_topic_view
    if is_open_topic_view:
        topic_buttons_list = controller.view.topic_w.topics_btn_list
        toggled_stream_id = controller.view.topic_w.stream_button.stream_id
    user_buttons_list = controller.view.user_w.users_btn_list
    all_msg = controller.view.home_button
    all_pm = controller.view.pm_button
    all_mentioned = controller.view.mentioned_button
    for message in changed_messages:
        user_id = message["sender_id"]

        # If we sent this message, don't increase the count
        if user_id == controller.model.user_id:
            continue

        msg_type = message["type"]
        add_to_counts = True
        if {"mentioned", "wildcard_mentioned"} & set(message["flags"]):
            unread_counts["all_mentions"] += new_count
            all_mentioned.update_count(unread_counts["all_mentions"])

        if msg_type == "stream":
            stream_id = message["stream_id"]
            msg_topic = message["subject"]
            if controller.model.is_muted_stream(stream_id):
                add_to_counts = False  # if muted, don't add to eg. all_msg
            else:
                for stream_button in stream_buttons_list:
                    if stream_button.stream_id == stream_id:
                        stream_button.update_count(stream_button.count + new_count)
                        break
            # FIXME: Update unread_counts['unread_topics']?
            if controller.model.is_muted_topic(stream_id, msg_topic):
                add_to_counts = False
            if is_open_topic_view and stream_id == toggled_stream_id:
                # If topic_view is open for incoming messages's stream,
                # We update the respective TopicButton count accordingly.
                for topic_button in topic_buttons_list:
                    if topic_button.topic_name == msg_topic:
                        topic_button.update_count(topic_button.count + new_count)
        else:
            for user_button in user_buttons_list:
                if user_button.user_id == user_id:
                    user_button.update_count(user_button.count + new_count)
                    break
            unread_counts["all_pms"] += new_count
            all_pm.update_count(unread_counts["all_pms"])

        if add_to_counts:
            unread_counts["all_msg"] += new_count
            all_msg.update_count(unread_counts["all_msg"])


def set_count(id_list: List[int], controller: Any, new_count: int) -> None:
    # This method applies new_count for 'new message' (1) or 'read' (-1)
    # (we could ensure this in a different way by a different type)
    assert new_count == 1 or new_count == -1
    messages = controller.model.index["messages"]
    unread_counts: UnreadCounts = controller.model.unread_counts
    changed_messages = [messages[id] for id in id_list]
    _set_count_in_model(new_count, changed_messages, unread_counts)

    # if view is not yet loaded. Usually the case when first message is read.
    while not hasattr(controller, "view"):
        time.sleep(0.1)

    _set_count_in_view(controller, new_count, changed_messages, unread_counts)

    while not hasattr(controller, "loop"):
        time.sleep(0.1)
    controller.update_screen()


def index_messages(messages: List[Message], model: Any, index: Index) -> Index:
    """
    STRUCTURE OF INDEX
    {
        'pointer': {
            '[]': 30  # str(ZulipModel.narrow)
            '[["stream", "verona"]]': 32,
            ...
        }
        'topic_msg_ids': {
            123: {    # stream_id
                'topic name': {
                    51234,  # message id
                    56454,
                    ...
                }
        },
        'private_msg_ids_by_user_ids': {
            (3, 7): {  # user_ids frozenset
                51234,
                56454,
                ...
            },
            (1, 2, 3, 4): {  # multiple recipients
                12345,
                32553,
            }
        },
        'topics': {
            123: [    # stread_id
                'Denmark2', # topic name
                'Verona2',
                ....
            ]
        },
        'all_msg_ids': {
            14231,
            23423,
            ...
        },
        'private_msg_ids': {
            22334,
            23423,
            ...
        },
        'mentioned_msg_ids': {
            14423,
            33234,
            ...
        },
        'stream_msg_ids_by_stream_id': {
            123: {
                53434,
                36435,
                ...
            }
            234: {
                23423,
                23423,
                ...
            }
        },
        'edited_messages':{
            51234,
            23423,
            ...
        },
        'search': {
            13242,
            23423,
            23423,
            ...
        },
        'messages': {
            # all the messages mapped to their id
            # for easy retrieval of message from id
            45645: {  # PRIVATE
                'id': 4290,
                'timestamp': 1521817473,
                'content': 'Hi @**Cordelia Lear**',
                'sender_full_name': 'Iago',
                'flags': [],
                'sender_email': 'iago@zulip.com',
                'subject': '',
                'subject_links': [],
                'sender_id': 73,
                'type': 'private',
                'reactions': [],
                'display_recipient': [
                    {
                        'email': 'ZOE@zulip.com',
                        'id': 70,
                        'full_name': 'Zoe',
                    }, {
                        'email': 'cordelia@zulip.com',
                        'id': 71,
                        'full_name': 'Cordelia Lear',
                    }, {
                        'email': 'hamlet@zulip.com',
                        'id': 72,
                        'full_name': 'King Hamlet',
                    }, {
                        'email': 'iago@zulip.com',
                        'id': 73,
                        'full_name': 'Iago',
                    }
                ]
            },
            45645: {  # STREAM
                'timestamp': 1521863062,
                'sender_id': 72,
                'sender_full_name': 'King Hamlet',
                'content': 'https://github.com/zulip/zulip-terminal',
                'type': 'stream',
                'sender_email': 'hamlet@zulip.com',
                'id': 4298,
                'display_recipient': 'Verona',
                'flags': [],
                'reactions': [],
                'subject': 'Verona2',
                'stream_id': 32,
            },
        },
    }
    """
    narrow = model.narrow
    for msg in messages:
        if msg["sender_id"] in model.muted_users:
            index["muted_messages"].add(msg["id"])
        if "edit_history" in msg:
            index["edited_messages"].add(msg["id"])

        index["messages"][msg["id"]] = msg
        if not narrow:
            index["all_msg_ids"].add(msg["id"])

        elif model.is_search_narrow():
            index["search"].add(msg["id"])
            continue

        if len(narrow) == 1:
            if narrow[0][1] == "starred" and "starred" in msg["flags"]:
                index["starred_msg_ids"].add(msg["id"])

            msg_has_mention = {"mentioned", "wildcard_mentioned"} & set(msg["flags"])
            if narrow[0][1] == "mentioned" and msg_has_mention:
                index["mentioned_msg_ids"].add(msg["id"])

            if msg["type"] == "private":
                index["private_msg_ids"].add(msg["id"])
                recipients = frozenset(
                    {recipient["id"] for recipient in msg["display_recipient"]}
                )

                if narrow[0][0] == "pm-with":
                    narrow_emails = [
                        model.user_dict[email]["user_id"]
                        for email in narrow[0][1].split(", ")
                    ] + [model.user_id]
                    if recipients == frozenset(narrow_emails):
                        index["private_msg_ids_by_user_ids"][recipients].add(msg["id"])

            if msg["type"] == "stream" and msg["stream_id"] == model.stream_id:
                index["stream_msg_ids_by_stream_id"][msg["stream_id"]].add(msg["id"])

        if (
            msg["type"] == "stream"
            and len(narrow) == 2
            and narrow[1][1] == msg["subject"]
        ):
            topics_in_stream = index["topic_msg_ids"][msg["stream_id"]]
            if not topics_in_stream.get(msg["subject"]):
                topics_in_stream[msg["subject"]] = set()
            topics_in_stream[msg["subject"]].add(msg["id"])

    return index


def classify_unread_counts(model: Any) -> UnreadCounts:
    # TODO: support group pms
    unread_msg_counts = model.initial_data["unread_msgs"]

    unread_counts = UnreadCounts(
        all_msg=0,
        all_pms=0,
        all_mentions=0,
        unread_topics=dict(),
        unread_pms=dict(),
        unread_huddles=dict(),
        streams=defaultdict(int),
    )

    mentions_count = len(unread_msg_counts["mentions"])
    unread_counts["all_mentions"] += mentions_count

    for pm in unread_msg_counts["pms"]:
        count = len(pm["unread_message_ids"])
        unread_counts["unread_pms"][pm["sender_id"]] = count
        unread_counts["all_msg"] += count
        unread_counts["all_pms"] += count

    for stream in unread_msg_counts["streams"]:
        count = len(stream["unread_message_ids"])
        stream_id = stream["stream_id"]
        # unsubscribed streams may be in raw unreads, but are not tracked
        if not model.is_user_subscribed_to_stream(stream_id):
            continue
        if model.is_muted_topic(stream_id, stream["topic"]):
            continue
        stream_topic = (stream_id, stream["topic"])
        unread_counts["unread_topics"][stream_topic] = count
        if not unread_counts["streams"].get(stream_id):
            unread_counts["streams"][stream_id] = count
        else:
            unread_counts["streams"][stream_id] += count
        if stream_id not in model.muted_streams:
            unread_counts["all_msg"] += count

    # store unread count of group pms in `unread_huddles`
    for group_pm in unread_msg_counts["huddles"]:
        count = len(group_pm["unread_message_ids"])
        user_ids = group_pm["user_ids_string"].split(",")
        user_ids = frozenset(map(int, user_ids))
        unread_counts["unread_huddles"][user_ids] = count
        unread_counts["all_msg"] += count
        unread_counts["all_pms"] += count

    return unread_counts


def match_user(user: Any, text: str) -> bool:
    """
    Matches if the user full name, last name or email matches
    with `text` or not.
    """
    full_name = user["full_name"].lower()
    keywords = full_name.split()
    # adding full_name helps in further narrowing down the right user.
    keywords.append(full_name)
    keywords.append(user["email"].lower())
    return any(keyword.startswith(text.lower()) for keyword in keywords)


def match_user_name_and_email(user: Any, text: str) -> bool:
    """
    Matches if the user's full name, last name, email or a combination
    in the form of "name <email>" matches with `text`.
    """
    full_name = user["full_name"].lower()
    email = user["email"].lower()
    keywords = full_name.split()
    keywords.append(full_name)
    keywords.append(email)
    keywords.append(f"{full_name} <{email}>")
    return any(keyword.startswith(text.lower()) for keyword in keywords)


def match_emoji(emoji: str, text: str) -> bool:
    """
    True if the emoji matches with `text` (case insensitive),
    False otherwise.
    """
    return emoji.lower().startswith(text.lower())


def match_topics(topic_names: List[str], search_text: str) -> List[str]:
    matching_topics = []
    delimiters = "-_/"
    trans = str.maketrans(delimiters, len(delimiters) * " ")
    for full_topic_name in topic_names:
        # "abc def-gh" --> ["abc def gh", "def", "gh"]
        words_to_be_matched = [full_topic_name] + full_topic_name.translate(
            trans
        ).split()[1:]

        for word in words_to_be_matched:
            if word.lower().startswith(search_text.lower()):
                matching_topics.append(full_topic_name)
                break
    return matching_topics


DataT = TypeVar("DataT")


def match_stream(
    data: List[Tuple[DataT, str]], search_text: str, pinned_streams: List[StreamData]
) -> Tuple[List[DataT], List[str]]:
    """
    Returns a list of DataT (streams) and a list of their corresponding names
    whose words match with the 'text' in the following order:
    * 1st-word startswith match > 2nd-word startswith match > ... (pinned)
    * 1st-word startswith match > 2nd-word startswith match > ... (unpinned)

    Note: This function expects `data` to be sorted, in a non-decreasing
    order, and ordered by their pinning status.
    """
    pinned_stream_names = [stream["name"] for stream in pinned_streams]

    # Assert that the data is sorted, in a non-decreasing order, and ordered by
    # their pinning status.
    assert data == sorted(  # noqa: C414 (nested sort)
        sorted(data, key=lambda data: data[1].lower()),
        key=lambda data: data[1] in pinned_stream_names,
        reverse=True,
    )

    delimiters = "-_/"
    trans = str.maketrans(delimiters, len(delimiters) * " ")
    stream_splits = [
        ((datum, [stream_name] + stream_name.translate(trans).split()[1:]))
        for datum, stream_name in data
    ]

    matches: Dict[str, DefaultDict[int, List[Tuple[DataT, str]]]] = {
        "pinned": defaultdict(list),
        "unpinned": defaultdict(list),
    }

    for datum, splits in stream_splits:
        stream_name = splits[0]
        kind = "pinned" if stream_name in pinned_stream_names else "unpinned"
        for match_position, word in enumerate(splits):
            if word.lower().startswith(search_text.lower()):
                matches[kind][match_position].append((datum, stream_name))

    ordered_matches = []
    ordered_names = []
    for matched_data in matches.values():
        if not matched_data:
            continue
        for match_position in range(max(matched_data.keys()) + 1):
            for datum, name in matched_data.get(match_position, []):
                if datum not in ordered_matches:
                    ordered_matches.append(datum)
                    ordered_names.append(name)
    return ordered_matches, ordered_names


def match_group(group_name: str, text: str) -> bool:
    """
    True if any group name matches with `text` (case insensitive),
    False otherwise.
    """
    return group_name.lower().startswith(text.lower())


def format_string(names: List[str], wrapping_text: str) -> List[str]:
    """
    Wrap a list of names using the wrapping characters for typeahead
    """
    return [wrapping_text.format(name) for name in names]


def powerset(
    iterable: Iterable[Any], map_func: Callable[[Any], Any] = set
) -> List[Any]:
    """
    >> powerset([1,2,3])
    returns: [set(), {1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}]"
    """
    s = list(iterable)
    powerset = chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))
    return list(map(map_func, list(powerset)))


def canonicalize_color(color: str) -> str:
    """
    Given a color of the format '#xxxxxx' or '#xxx', produces one of the
    format '#xxx'. Always produces lowercase hex digits.
    """
    if match(REGEX_COLOR_6_DIGIT, color, ASCII) is not None:
        # '#xxxxxx' color, stored by current zulip server
        return (color[:2] + color[3] + color[5]).lower()
    elif match(REGEX_COLOR_3_DIGIT, color, ASCII) is not None:
        # '#xxx' color, which may be stored by the zulip server <= 2.0.0
        # Potentially later versions too
        return color.lower()
    else:
        raise ValueError(f'Unknown format for color "{color}"')


def display_error_if_present(response: Dict[str, Any], controller: Any) -> None:
    if response["result"] == "error" and hasattr(controller, "view"):
        controller.report_error([response["msg"]])


def check_narrow_and_notify(
    outer_narrow: List[Any], inner_narrow: List[Any], controller: Any
) -> None:
    current_narrow = controller.model.narrow

    if (
        current_narrow != []
        and current_narrow != outer_narrow
        and current_narrow != inner_narrow
    ):
        key = primary_key_for_command("NARROW_MESSAGE_RECIPIENT")

        controller.report_success(
            [
                "Message is sent outside of current narrow."
                f" Press [{key}] to narrow to conversation."
            ],
            duration=6,
        )


def notify_if_message_sent_outside_narrow(
    message: Composition, controller: Any
) -> None:
    if message["type"] == "stream":
        stream_narrow = [["stream", message["to"]]]
        topic_narrow = stream_narrow + [["topic", message["subject"]]]
        check_narrow_and_notify(stream_narrow, topic_narrow, controller)
    elif message["type"] == "private":
        pm_narrow = [["is", "private"]]
        recipient_emails = [
            controller.model.user_id_email_dict[user_id] for user_id in message["to"]
        ]
        pm_with_narrow = [["pm-with", ", ".join(recipient_emails)]]
        check_narrow_and_notify(pm_narrow, pm_with_narrow, controller)


def hash_util_decode(string: str) -> str:
    """
    Returns a decoded string given a hash_util_encode() [present in
    zulip/zulip's zerver/lib/url_encoding.py] encoded string.
    """
    # Acknowledge custom string replacements in zulip/zulip's
    # zerver/lib/url_encoding.py before unquote.
    return unquote(string.replace(".", "%"))


def get_unused_fence(content: str) -> str:
    """
    Generates fence for quoted-message based on regex pattern
    of continuous back-ticks. Referred and translated from
    zulip/static/shared/js/fenced_code.js.
    """
    max_length_fence = 3

    matches = findall(REGEX_QUOTED_FENCE_LENGTH, content, flags=MULTILINE)
    if len(matches) != 0:
        max_length_fence = max(max_length_fence, len(max(matches, key=len)) + 1)

    return "`" * max_length_fence


@contextmanager
def suppress_output() -> Iterator[None]:
    """
    Context manager to redirect stdout and stderr to /dev/null.

    Adapted from https://stackoverflow.com/a/2323563
    """
    stdout = os.dup(1)
    stderr = os.dup(2)
    os.close(1)
    os.close(2)
    os.open(os.devnull, os.O_RDWR)
    try:
        yield
    finally:
        os.dup2(stdout, 1)
        os.dup2(stderr, 2)


@asynch
def process_media(controller: Any, link: str) -> None:
    """
    Helper to process media links.
    """
    if not link:
        controller.report_error("The media link is empty")
        return

    show_download_status = partial(
        controller.view.set_footer_text, "Downloading your media..."
    )
    media_path = download_media(controller, link, show_download_status)
    tool = ""

    # TODO: Add support for other platforms as well.
    if PLATFORM == "WSL":
        tool = "explorer.exe"
        # Modifying path to backward slashes instead of forward slashes
        media_path = media_path.replace("/", "\\")
    elif PLATFORM == "Linux":
        tool = "xdg-open"
    elif PLATFORM == "MacOS":
        tool = "open"
    else:
        controller.report_error("Media not supported for this platform")
        return

    controller.show_media_confirmation_popup(open_media, tool, media_path)


def download_media(
    controller: Any, url: str, show_download_status: Callable[..., None]
) -> str:
    """
    Helper to download media from given link. Returns the path to downloaded media.
    """
    media_name = url.split("/")[-1]
    client = controller.client
    auth = requests.auth.HTTPBasicAuth(client.email, client.api_key)

    with requests.get(url, auth=auth, stream=True) as response:
        response.raise_for_status()
        local_path = ""
        with NamedTemporaryFile(
            mode="wb", delete=False, prefix="zt-", suffix=f"-{media_name}"
        ) as file:
            local_path = file.name
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks.
                    file.write(chunk)
                    show_download_status()

        controller.report_success([" Downloaded ", ("bold", media_name)])
        return normalized_file_path(local_path)

    return ""


@asynch
def open_media(controller: Any, tool: str, media_path: str) -> None:
    """
    Helper to open a media file given its path and tool.
    """
    error = []
    command = [tool, media_path]
    try:
        process = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        exit_status = process.returncode
        if exit_status != successful_GUI_return_code():
            error = [
                " The tool ",
                ("footer_contrast", tool),
                " did not run successfully" ". Exited with ",
                ("footer_contrast", str(exit_status)),
            ]
    except FileNotFoundError:
        error = [" The tool ", ("footer_contrast", tool), " could not be found"]

    if error:
        controller.report_error(error)
