from typing import Any, List, Dict
from functools import wraps
from threading import Thread
from collections import defaultdict

CMSG = Dict[str, List[Dict[str, Any]]]  # Classified Messages
NMSGL = List[Dict[str, Any]]  # Normal Message List


def async(func: Any) -> Any:
    """
    Decorator for executing a function in a separate :class:`threading.Thread`.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        return thread.start()
    return wrapper


def set_count(id_list, controller):
    streams = controller.view.stream_w.log
    users = controller.view.user_w.log
    all_msg = controller.view.home_button
    all_pm = controller.view.pm_button
    messages = controller.model.index['messages']
    for id in id_list:
        msg_type = messages[id]['type']
        if msg_type == 'stream':
            stream_id = messages[id]['stream_id']
            for stream in streams:
                if stream.stream_id == stream_id:
                    stream.update_count(stream.count - 1)
                    break

        else:
            user_id = messages[id]['sender_id']
            for user in users:
                if user.user_id == user_id:
                    user.update_count(user.count - 1)
                    break
            all_pm.update_count(all_pm.count - 1)
        all_msg.update_count(all_msg.count - 1)
    controller.loop.draw_screen()


@async
def update_flag(id_list: List[int], controller: Any) -> None:
    if id_list == []:
        return
    request = {
        'messages': id_list,
        'flag': 'read',
        'op': 'add',
    }
    client = controller.client
    client.do_api_query(request, '/json/messages/flags', method="POST")
    set_count(id_list, controller)


def index_messages(messages, model, index=None):
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
        'all_messages': {
            14231,
            23423,
            ...
        },
        'all_private': {
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
        }
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
    if index is None:
        index = {
            'pointer': defaultdict(set),
            'stream': defaultdict(dict),
            'private': defaultdict(set),
            'all_messages': set(),
            'all_private': set(),
            'all_stream': defaultdict(set),
            'messages': defaultdict(dict),
        }
    narrow = model.narrow
    for msg in messages:

        index['messages'][msg['id']] = msg
        if narrow == []:
            index['all_messages'].add(msg['id'])

        if len(narrow) == 1:

            if msg['type'] == 'private':
                index['all_private'].add(msg['id'])
                recipients = frozenset(set(
                    recipient['id'] for recipient in msg['display_recipient']
                ))

                if narrow[0][0] == 'pm_with' and recipients == frozenset({
                        model.user_id, model.user_dict[narrow[0][1]]['user_id']
                        }):
                    index['private'][recipients].add(msg['id'])

            if msg['type'] == 'stream' and msg['stream_id'] == model.stream_id:
                index['all_stream'][msg['stream_id']].add(msg['id'])

        if msg['type'] == 'stream' and len(narrow) == 2 and\
                narrow[1][1] == msg['subject']:

            if not index['stream'][msg['stream_id']].get(msg['subject']):
                index['stream'][msg['stream_id']][msg['subject']] = set()
            index['stream'][msg['stream_id']][msg['subject']].add(msg['id'])

    return index


def classify_unread_counts(unread_msg_counts: Dict[str, Any]):
    # TODO: supprot group pms
    unread_counts = dict()
    unread_counts['all_msg'] = 0
    unread_counts['all_pms'] = 0
    for pm in unread_msg_counts['pms']:
        count = len(pm['unread_message_ids'])
        unread_counts[pm['sender_id']] = count
        unread_counts['all_msg'] += count
        unread_counts['all_pms'] += count

    for stream in unread_msg_counts['streams']:
        count = len(stream['unread_message_ids'])
        if not unread_counts.get(stream['stream_id']):
            unread_counts[stream['stream_id']] = count
        else:
            unread_counts[stream['stream_id']] += count
        unread_counts['all_msg'] += count

    return unread_counts
