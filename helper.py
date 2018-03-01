from typing import Any, List, Dict
from functools import wraps
from threading import Thread
from collections import defaultdict
import urwid

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

def classify_message(own_email: str, new_messages: NMSGL, classified_messages: CMSG=None) -> CMSG:
    """
    Classifies messages into their respective types/streams.
    """
    # Initialize classified_messages
    if classified_messages is None:
        # defaultdict is used to ease the process of adding new keys
        classified_messages = defaultdict(list)

    for msg in new_messages:
        if msg['type'] == 'stream':
            msg_type = msg['stream_id']
            sender = msg['sender_full_name']
        else:  # Private message
            # Just a hunch to get the email of the other person in PM
            msg_type = msg['display_recipient'][0]['email']
            pm_with_name = msg['display_recipient'][0]['full_name']
            if msg_type == own_email:
                try:
                    msg_type = msg['display_recipient'][1]['email']
                    pm_with_name = msg['display_recipient'][1]['full_name']
                except IndexError:
                    pass

            if own_email == msg['sender_email']:
                pm_with_name = "You and " + pm_with_name
            sender = pm_with_name

        classified_messages[msg_type].append({
            'sender' : sender,
            'time' : int(msg['timestamp']),
            'stream' : msg['display_recipient'],
            'title' : msg['subject'],
            'content' : msg['content'],
            'type' : msg['type'],
            'sender_email' : msg['sender_email'],
        })
    return classified_messages
