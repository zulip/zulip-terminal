import os
import platform
import shlex
import subprocess
import time
from collections import defaultdict
from functools import wraps
from itertools import chain, combinations
from re import ASCII, match
from threading import Thread
from typing import (
    Any, Callable, DefaultDict, Dict, FrozenSet, Iterable, List, Optional, Set,
    Tuple, Union,
)

import lxml.html
from mypy_extensions import TypedDict


MACOS = platform.system() == "Darwin"
LINUX = platform.system() == "Linux"
WSL = 'microsoft' in platform.release().lower()

Message = Dict[str, Any]

Index = TypedDict('Index', {
    'pointer': Dict[str, Union[int, Set[None]]],  # narrow_str, message_id
    # Various sets of downloaded message ids (all, starred, ...)
    'all_msg_ids': Set[int],
    'starred_msg_ids': Set[int],
    'mentioned_msg_ids': Set[int],
    'private_msg_ids': Set[int],
    'private_msg_ids_by_user_ids': Dict[FrozenSet[int], Set[int]],
    'stream_msg_ids_by_stream_id': Dict[int, Set[int]],
    'topic_msg_ids': Dict[int, Dict[str, Set[int]]],
    # Extra cached information
    'edited_messages': Set[int],  # {message_ids, ...}
    'topics': Dict[int, List[str]],  # {topic names, ...}
    'search': Set[int],  # {message_id, ...}
    # Downloaded message data
    'messages': Dict[int, Message],  # message_id: Message
})

initial_index = Index(
    pointer=defaultdict(set),
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
    messages=defaultdict(dict),
)


UnreadCounts = TypedDict('UnreadCounts', {
    'all_msg': int,
    'all_pms': int,
    'all_mentions': int,
    'unread_topics': Dict[Tuple[int, str], int],  # stream_id, topic
    'unread_pms': Dict[int, int],  # sender_id
    'unread_huddles': Dict[FrozenSet[int], int],  # Group pms
    'streams': Dict[int, int],  # stream_id
})


def asynch(func: Any) -> Any:
    """
    Decorator for executing a function in a separate :class:`threading.Thread`.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # If calling when pytest is running simply return the function
        # to avoid running in asynch mode.
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return func(*args, **kwargs)

        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        return thread.start()
    return wrapper


def _set_count_in_model(new_count: int, changed_messages: List[Message],
                        unread_counts: UnreadCounts) -> None:
    """
        This function doesn't explicitly set counts in model,
        but updates `unread_counts` (which can update the model
        if it's passed in, but is not tied to it).
    """
    for message in changed_messages:
        if message['type'] == 'stream':
            key = (message['stream_id'], message['subject'])
            unreads = unread_counts['unread_topics']
        # self-pm has only one display_recipient
        # 1-1 pms have 2 display_recipient
        elif len(message['display_recipient']) <= 2:
            key = message['sender_id']
            unreads = unread_counts['unread_pms']  # type: ignore
        else:  # If it's a group pm
            key = frozenset(  # type: ignore
                recipient['id'] for recipient in message['display_recipient']
            )
            unreads = unread_counts['unread_huddles']  # type: ignore

        # broader unread counts (for all_* and streams) are updated
        # later conditionally.
        if key in unreads:
            unreads[key] += new_count
            if unreads[key] == 0:
                unreads.pop(key)
        elif new_count == 1:
            unreads[key] = new_count


def _set_count_in_view(controller: Any, new_count: int,
                       changed_messages: List[Message],
                       unread_counts: UnreadCounts) -> None:
    """
        This function for the most part contains the logic for setting the
        count in the UI buttons. The later buttons (all_msg, all_pms)
        additionally set the current count in the model and make use of the
        same in the UI.
    """
    stream_buttons_log = controller.view.stream_w.log
    is_open_topic_view = controller.view.left_panel.is_in_topic_view
    if is_open_topic_view:
        topic_buttons_log = controller.view.topic_w.log
        toggled_stream_id = controller.view.topic_w.stream_button.stream_id
    user_buttons_log = controller.view.user_w.log
    all_msg = controller.view.home_button
    all_pm = controller.view.pm_button
    all_mentioned = controller.view.mentioned_button
    for message in changed_messages:
        user_id = message['sender_id']

        # If we sent this message, don't increase the count
        if user_id == controller.model.user_id:
            continue

        msg_type = message['type']
        add_to_counts = True
        if 'mentioned' in message['flags']:
            unread_counts['all_mentions'] += new_count
            all_mentioned.update_count(unread_counts['all_mentions'])

        if msg_type == 'stream':
            stream_id = message['stream_id']
            msg_topic = message['subject']
            if controller.model.is_muted_stream(stream_id):
                add_to_counts = False  # if muted, don't add to eg. all_msg
            else:
                for stream_button in stream_buttons_log:
                    if stream_button.stream_id == stream_id:
                        # FIXME: Update unread_count[streams]?
                        stream_button.update_count(stream_button.count +
                                                   new_count)
                        break
            # FIXME: Update unread_counts['unread_topics']?
            if ([message['display_recipient'], msg_topic] in
                    controller.model.muted_topics):
                add_to_counts = False
            if is_open_topic_view and stream_id == toggled_stream_id:
                # If topic_view is open for incoming messages's stream,
                # We update the respective TopicButton count accordingly.
                for topic_button in topic_buttons_log:
                    if topic_button.topic_name == msg_topic:
                        topic_button.update_count(topic_button.count +
                                                  new_count)
        else:
            for user_button in user_buttons_log:
                if user_button.user_id == user_id:
                    user_button.update_count(user_button.count + new_count)
                    break
            unread_counts['all_pms'] += new_count
            all_pm.update_count(unread_counts['all_pms'])

        if add_to_counts:
            unread_counts['all_msg'] += new_count
            all_msg.update_count(unread_counts['all_msg'])


def set_count(id_list: List[int], controller: Any, new_count: int) -> None:
    # This method applies new_count for 'new message' (1) or 'read' (-1)
    # (we could ensure this in a different way by a different type)
    assert new_count == 1 or new_count == -1
    messages = controller.model.index['messages']
    unread_counts = controller.model.unread_counts  # type: UnreadCounts
    changed_messages = [messages[id] for id in id_list]
    _set_count_in_model(new_count, changed_messages, unread_counts)

    # if view is not yet loaded. Usually the case when first message is read.
    while not hasattr(controller, 'view'):
        time.sleep(0.1)

    _set_count_in_view(controller, new_count, changed_messages, unread_counts)

    while not hasattr(controller, 'loop'):
        time.sleep(0.1)
    controller.update_screen()


def index_messages(messages: List[Message],
                   model: Any,
                   index: Index) -> Index:
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
                'sender_short_name': 'iago',
                'sender_email': 'iago@zulip.com',
                'subject': '',
                'subject_links': [],
                'sender_id': 73,
                'type': 'private',
                'recipient_id': 124,
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
                'recipient_id': 119,
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

        if 'edit_history' in msg.keys():
            index['edited_messages'].add(msg['id'])

        index['messages'][msg['id']] = msg
        if not narrow:
            index['all_msg_ids'].add(msg['id'])

        elif model.is_search_narrow():
            index['search'].add(msg['id'])
            continue

        if len(narrow) == 1:

            if narrow[0][1] == 'starred':
                if 'starred' in msg['flags']:
                    index['starred_msg_ids'].add(msg['id'])

            if narrow[0][1] == 'mentioned':
                if 'mentioned' in msg['flags']:
                    index['mentioned_msg_ids'].add(msg['id'])

            if msg['type'] == 'private':
                index['private_msg_ids'].add(msg['id'])
                recipients = frozenset(set(
                    recipient['id'] for recipient in msg['display_recipient']
                ))

                if narrow[0][0] == 'pm_with':
                    narrow_emails = ([model.user_dict[email]['user_id']
                                      for email in narrow[0][1].split(', ')] +
                                     [model.user_id])
                    if recipients == frozenset(narrow_emails):
                        (index['private_msg_ids_by_user_ids'][recipients]
                         .add(msg['id']))

            if msg['type'] == 'stream' and msg['stream_id'] == model.stream_id:
                (index['stream_msg_ids_by_stream_id'][msg['stream_id']]
                 .add(msg['id']))

        if msg['type'] == 'stream' and len(narrow) == 2 and\
                narrow[1][1] == msg['subject']:

            topics_in_stream = index['topic_msg_ids'][msg['stream_id']]
            if not topics_in_stream.get(msg['subject']):
                topics_in_stream[msg['subject']] = set()
            topics_in_stream[msg['subject']].add(msg['id'])

    return index


def classify_unread_counts(model: Any) -> UnreadCounts:
    # TODO: support group pms
    unread_msg_counts = model.initial_data['unread_msgs']

    unread_counts = UnreadCounts(
        all_msg=0,
        all_pms=0,
        all_mentions=0,
        unread_topics=dict(),
        unread_pms=dict(),
        unread_huddles=dict(),
        streams=dict(),
    )

    mentions_count = len(unread_msg_counts['mentions'])
    unread_counts['all_mentions'] += mentions_count

    for pm in unread_msg_counts['pms']:
        count = len(pm['unread_message_ids'])
        unread_counts['unread_pms'][pm['sender_id']] = count
        unread_counts['all_msg'] += count
        unread_counts['all_pms'] += count

    for stream in unread_msg_counts['streams']:
        count = len(stream['unread_message_ids'])
        stream_id = stream['stream_id']
        if [model.stream_dict[stream_id]['name'],
                stream['topic']] in model.muted_topics:
            continue
        stream_topic = (stream_id, stream['topic'])
        unread_counts['unread_topics'][stream_topic] = count
        if not unread_counts['streams'].get(stream_id):
            unread_counts['streams'][stream_id] = count
        else:
            unread_counts['streams'][stream_id] += count
        unread_counts['all_msg'] += count

    # store unread count of group pms in `unread_huddles`
    for group_pm in unread_msg_counts['huddles']:
        count = len(group_pm['unread_message_ids'])
        user_ids = group_pm['user_ids_string'].split(',')
        user_ids = frozenset(map(int, user_ids))
        unread_counts['unread_huddles'][user_ids] = count
        unread_counts['all_msg'] += count
        unread_counts['all_pms'] += count

    return unread_counts


def match_user(user: Any, text: str) -> bool:
    """
    Matches if the user full name, last name or email matches
    with `text` or not.
    """
    full_name = user['full_name'].lower()
    keywords = full_name.split()
    # adding full_name helps in further narrowing down the right user.
    keywords.append(full_name)
    keywords.append(user['email'].lower())
    for keyword in keywords:
        if keyword.startswith(text.lower()):
            return True
    return False


def match_emoji(emoji: str, text: str) -> bool:
    """
    True if the emoji matches with `text` (case insensitive),
    False otherwise.
    """
    return emoji.lower().startswith(text.lower())


def match_stream(stream: Any, text: str) -> bool:
    """
    True if the stream matches with `text` (case insensitive),
    False otherwise.
    """
    stream_name = stream[0].lower()
    if stream_name.startswith(text.lower()):
        return True
    return False


def match_group(group_name: str, text: str) -> bool:
    """
    True if any group name matches with `text` (case insensitive),
    False otherwise.
    """
    return group_name.lower().startswith(text.lower())


def powerset(iterable: Iterable[Any],
             map_func: Callable[[Any], Any]=set) -> List[Any]:
    """
    >> powerset([1,2,3])
    returns: [set(), {1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}]"
    """
    s = list(iterable)
    powerset = chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
    return list(map(map_func, list(powerset)))


def canonicalize_color(color: str) -> str:
    """
    Given a color of the format '#xxxxxx' or '#xxx', produces one of the
    format '#xxx'. Always produces lowercase hex digits.
    """
    if match('^#[0-9A-Fa-f]{6}$', color, ASCII) is not None:
        # '#xxxxxx' color, stored by current zulip server
        return (color[:2] + color[3] + color[5]).lower()
    elif match('^#[0-9A-Fa-f]{3}$', color, ASCII) is not None:
        # '#xxx' color, which may be stored by the zulip server <= 2.0.0
        # Potentially later versions too
        return color.lower()
    else:
        raise ValueError('Unknown format for color "{}"'.format(color))


@asynch
def notify(title: str, html_text: str) -> None:
    document = lxml.html.document_fromstring(html_text)
    text = document.text_content()
    quoted_text = shlex.quote(text)

    quoted_title = shlex.quote(title)

    command_list = None
    if WSL:  # NOTE Tested and should work!
        # Escaping of quotes in powershell is done using ` instead of \
        escaped_text = text.replace('\'', '`\'').replace('\"', '`\"')
        quoted_text = '\"' + escaped_text + '\"'
        command_list = [
            'powershell.exe',
            "New-BurntToastNotification -Text {}, {}"
            .format(quoted_title, quoted_text)
        ]
        expected_length = 2
    elif MACOS:  # NOTE Tested and should work!
        command_list = shlex.split(
            "osascript -e "
            "'display notification \"\'{}\'\" with title \"\'{}\'\" "
            " sound name \"ZT_NOTIFICATION_SOUND\"'"
            .format(quoted_text, quoted_title)
        )
        expected_length = 3
    elif LINUX:
        command_list = shlex.split(
            'notify-send {} {}'.format(quoted_title, quoted_text)
        )
        expected_length = 3

    if command_list is not None:
        # NOTE: We assert this in tests, but this signals unexpected breakage
        assert len(command_list) == expected_length

        res = subprocess.run(command_list, stdout=subprocess.DEVNULL,
                             stderr=subprocess.STDOUT)
