import time
from collections import defaultdict
from functools import wraps
from threading import Thread
from typing import (
    Any, Dict, List, Set, Tuple, Optional, DefaultDict, FrozenSet, Union
)
from mypy_extensions import TypedDict

import os

Message = Dict[str, Any]

Index = TypedDict('Index', {
    'pointer': Dict[str, Union[int, Set[None]]],  # narrow_str, message_id
    # stream_id: topic_str: {message_id, ...}
    'stream': Dict[int, Dict[str, Set[int]]],
    # {user_id, ...}: {message_id, ...}
    'private': Dict[FrozenSet[int], Set[int]],
    'topics': Dict[int, List[str]],  # {topic names, ...}
    'all_msg_ids': Set[int],  # {message_id, ...}
    'starred_msg_ids': Set[int],  # {message_id, ...}
    'private_msg_ids': Set[int],  # {message_id, ...}
    'all_stream': Dict[int, Set[int]],  # stream_id: {message_id, ...}
    'edited_messages': Set[int],  # {message_ids, ...}
    'search': Set[int],  # {message_id, ...}
    'messages': Dict[int, Message],  # message_id: Message
})

initial_index = Index(
    pointer=defaultdict(set),
    stream=defaultdict(dict),
    private=defaultdict(set),
    topics=defaultdict(list),
    all_msg_ids=set(),
    starred_msg_ids=set(),
    private_msg_ids=set(),
    all_stream=defaultdict(set),
    edited_messages=set(),
    messages=defaultdict(dict),
    search=set(),
)


UnreadCounts = TypedDict('UnreadCounts', {
    'all_msg': int,
    'all_pms': int,
    'unread_topics': Dict[Tuple[int, str], int],  # stream_id, topic
    'unread_pms': Dict[int, int],  # sender_id
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


def set_count(id_list: List[int], controller: Any, new_count: int) -> None:
    # This method applies new_count for 'new message' (1) or 'read' (-1)
    # (we could ensure this in a different way by a different type)
    assert new_count == 1 or new_count == -1

    messages = controller.model.index['messages']
    unread_counts = controller.model.unread_counts  # type: UnreadCounts

    for id in id_list:
        msg = messages[id]

        if msg['type'] == 'stream':
            key = (messages[id]['stream_id'], msg['subject'])
            unreads = unread_counts['unread_topics']
        else:
            key = messages[id]['sender_id']
            unreads = unread_counts['unread_pms']  # type: ignore

        # broader unread counts (for all_* and streams) are updated
        # later conditionally.
        if key in unreads:
            unreads[key] += new_count
            if unreads[key] == 0:
                unreads.pop(key)
        elif new_count == 1:
            unreads[key] = new_count

    # if view is not yet loaded. Usually the case when first message is read.
    while not hasattr(controller, 'view'):
        time.sleep(0.1)

    streams = controller.view.stream_w.log
    users = controller.view.user_w.log
    all_msg = controller.view.home_button
    all_pm = controller.view.pm_button
    for id in id_list:
        user_id = messages[id]['sender_id']

        # If we sent this message, don't increase the count
        if user_id == controller.model.user_id:
            continue

        msg_type = messages[id]['type']
        add_to_counts = True
        if msg_type == 'stream':
            stream_id = messages[id]['stream_id']
            if stream_id in controller.model.muted_streams:
                add_to_counts = False  # if muted, don't add to eg. all_msg
            else:
                for stream in streams:
                    if stream.stream_id == stream_id:
                        # FIXME: Update unread_count[streams]?
                        stream.update_count(stream.count + new_count)
                        break
        else:
            for user in users:
                if user.user_id == user_id:
                    user.update_count(user.count + new_count)
                    break
            unread_counts['all_pms'] += new_count
            all_pm.update_count(unread_counts['all_pms'])

        if add_to_counts:
            unread_counts['all_msg'] += new_count
            all_msg.update_count(unread_counts['all_msg'])

    while not hasattr(controller, 'loop'):
        time.sleep(0.1)
    controller.update_screen()


def index_messages(messages: List[Any],
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
        'stream': {
            123: {    # stream_id
                'topic name': {
                    51234,  # message id
                    56454,
                    ...
                }
        },
        'private': {
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
        'all_stream': {
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

        elif narrow[0][0] == 'search':
            index['search'].add(msg['id'])
            continue

        if len(narrow) == 1:

            if narrow[0][1] == 'starred':
                if 'starred' in msg['flags']:
                    index['starred_msg_ids'].add(msg['id'])

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
                        index['private'][recipients].add(msg['id'])

            if msg['type'] == 'stream' and msg['stream_id'] == model.stream_id:
                index['all_stream'][msg['stream_id']].add(msg['id'])

        if msg['type'] == 'stream' and len(narrow) == 2 and\
                narrow[1][1] == msg['subject']:

            if not index['stream'][msg['stream_id']].get(msg['subject']):
                index['stream'][msg['stream_id']][msg['subject']] = set()
            index['stream'][msg['stream_id']][msg['subject']].add(msg['id'])

    return index


def classify_unread_counts(model: Any) -> UnreadCounts:
    # TODO: support group pms
    unread_msg_counts = model.initial_data['unread_msgs']

    unread_counts = UnreadCounts(
        all_msg=0,
        all_pms=0,
        unread_topics=dict(),
        unread_pms=dict(),
        streams=dict(),
    )

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
