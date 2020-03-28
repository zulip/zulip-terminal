from copy import deepcopy
from typing import Any

import pytest

from zulipterminal.helper import (
    canonicalize_color, classify_unread_counts, index_messages, notify,
    powerset, set_count,
)


@pytest.fixture
def controller(mocker, index_multiple_messages):
    controller = mocker.patch('zulipterminal.core.Controller.__init__')
    controller.model.index = index_multiple_messages
    controller.model.is_muted_stream = mocker.patch(
            'zulipterminal.model.Model.is_muted_stream', return_value=False)
    controller.view.left_panel.is_in_topic_view = False
    return controller


@pytest.mark.parametrize('all_msg, unread_topics', [
    (6, {(1001, 'Topic 1'): 3, (1002, 'Topic 2'): 1, (1002, 'Topic 3'): 2}),
    ])
@pytest.mark.parametrize(
    'new_count, id_list, expected_all_msg, expected_unread_topics', [
     (1, [], 6, {(1001, 'Topic 1'): 3, (1002, 'Topic 2'): 1,
                 (1002, 'Topic 3'): 2}),
     (1, [7], 7, {(1001, 'Topic 1'): 4, (1002, 'Topic 2'): 1,
                  (1002, 'Topic 3'): 2}),
     (1, [7, 8, 9], 9, {(1001, 'Topic 1'): 4, (1002, 'Topic 2'): 1,
                        (1002, 'Topic 3'): 2, (1003, 'Topic 10'): 2}),
     (-1, [], 6, {(1001, 'Topic 1'): 3, (1002, 'Topic 2'): 1,
                  (1002, 'Topic 3'): 2}),
     (-1, [5], 5, {(1001, 'Topic 1'): 3, (1002, 'Topic 2'): 1,
                   (1002, 'Topic 3'): 1}),
     (-1, [1, 2, 4, 6], 2, {(1002, 'Topic 2'): 1, (1002, 'Topic 3'): 1}),
     (-1, [1, 2, 3, 4, 5, 6], 0, {}),
     ])
def test_set_count_stream(controller, initial_unread_counts,
                          unread_topics, all_msg, id_list, new_count,
                          expected_unread_topics, expected_all_msg):
    unread_counts = deepcopy(dict(initial_unread_counts,
                                  **{'all_msg': all_msg,
                                     'unread_topics': unread_topics}))
    expected_unread_counts = dict(initial_unread_counts,
                                  **{'all_msg': expected_all_msg,
                                     'unread_topics': expected_unread_topics})
    controller.model.unread_counts = unread_counts

    set_count(id_list, controller, new_count)
    assert controller.model.unread_counts == expected_unread_counts


@pytest.mark.parametrize('all_msg, all_pms, unread_pms, user_id', [
    (4, 3, {200: 2, 201: 1}, 202)
    ])
@pytest.mark.parametrize(('new_count, id_list, expected_all_msg,'
                         'expected_all_pms, expected_unread_pms'), [
    (-1, [10, 13], 2, 1, {201: 1}),
    (-1, [10, 13, 11], 1, 0, {}),
    (-1, [], 4, 3, {200: 2, 201: 1}),
    (-1, [15], 4, 3, {200: 2, 201: 1}),   # self-pm
    (1, [16, 10], 6, 5, {200: 4, 201: 1}),
    (1, [], 4, 3, {200: 2, 201: 1}),
    ])
def test_set_count_pms(controller, initial_unread_counts, all_msg,
                       all_pms, unread_pms, user_id, id_list, new_count,
                       expected_unread_pms, expected_all_pms,
                       expected_all_msg):
    controller.model.user_id = user_id
    unread_counts = deepcopy(dict(initial_unread_counts,
                                  **{'all_msg': all_msg, 'all_pms': all_pms,
                                     'unread_pms': unread_pms}))
    expected_unread_counts = dict(initial_unread_counts,
                                  **{'all_msg': expected_all_msg,
                                     'all_pms': expected_all_pms,
                                     'unread_pms': expected_unread_pms})
    controller.model.unread_counts = unread_counts

    set_count(id_list, controller, new_count)
    assert controller.model.unread_counts == expected_unread_counts


@pytest.mark.parametrize('all_msg, all_pms, unread_huddles', [
    (4, 3, {frozenset({202, 200, 201}): 2, frozenset({202, 200, 199, 198}): 1})
    ])
@pytest.mark.parametrize(('new_count, id_list, expected_all_msg,'
                         'expected_all_pms, expected_unread_huddles'), [
    (-1, [20, 18], 2, 1, {frozenset({202, 200, 199, 198}): 1}),
    (-1, [20, 18, 24], 1, 0, {}),
    (-1, [], 4, 3, {frozenset({202, 200, 201}): 2,
                    frozenset({202, 200, 199, 198}): 1}),
    (1, [17, 19], 6, 5, {frozenset({202, 200, 201}): 4,
                         frozenset({202, 200, 199, 198}): 1}),
    (1, [17, 19, 23], 7, 6, {frozenset({202, 200, 201}): 4,
                             frozenset({202, 200, 199, 198}): 1,
                             frozenset({202, 200, 199}): 1}),
    (1, [], 4, 3, {frozenset({202, 200, 201}): 2,
                   frozenset({202, 200, 199, 198}): 1}),
    ])
def test_set_count_group_pms(initial_unread_counts, all_msg, new_count,
                             all_pms, unread_huddles, user_id, id_list,
                             expected_unread_huddles, expected_all_pms,
                             expected_all_msg, controller):
    unread_counts = deepcopy(dict(initial_unread_counts,
                                  **{'all_msg': all_msg, 'all_pms': all_pms,
                                     'unread_huddles': unread_huddles}))
    expected_unread_counts = dict(initial_unread_counts,
                                  **{'all_msg': expected_all_msg,
                                     'all_pms': expected_all_pms,
                                     'unread_huddles': expected_unread_huddles
                                     })
    controller.model.unread_counts = unread_counts

    set_count(id_list, controller, new_count)
    assert controller.model.unread_counts == expected_unread_counts


@pytest.mark.parametrize('all_msg, unread_topics', [
    (6, {(1001, 'Topic 1'): 3, (1002, 'Topic 3'): 1, (1003, 'Topic 10'): 2}),
    ])
@pytest.mark.parametrize(
    'new_count, expected_unread_topics, id_list, muted_streams,\
            expected_all_msg', [
     (1, {(1001, 'Topic 1'): 4, (1002, 'Topic 3'): 1,
          (1003, 'Topic 10'): 4}, [7, 8, 9], [1001, 1003], 6),
     (1, {(1001, 'Topic 1'): 4, (1002, 'Topic 3'): 1,
          (1003, 'Topic 10'): 4}, [7, 8, 9], [1001, 1002, 1003], 6),
     (1, {(1001, 'Topic 1'): 4, (1002, 'Topic 3'): 2,
          (1003, 'Topic 10'): 4}, [7, 8, 9, 4], [1001, 1003], 7),
     (-1, {(1001, 'Topic 1'): 2, (1002, 'Topic 3'): 1,
           (1003, 'Topic 10'): 2}, [2], [1001], 6),
     (-1, {(1001, 'Topic 1'): 2, (1003, 'Topic 10'): 2}, [2, 4], [1001], 5),
     ])
def test_set_count_muted_streams(initial_unread_counts, muted_streams,
                                 unread_topics, all_msg, id_list, new_count,
                                 expected_unread_topics, expected_all_msg,
                                 controller):
    # all_msg does not change for muted streams.
    controller.model.is_muted_stream = lambda stream_id: \
        stream_id in muted_streams
    unread_counts = deepcopy(dict(initial_unread_counts,
                                  **{'all_msg': all_msg,
                                     'unread_topics': unread_topics}))
    expected_unread_counts = dict(initial_unread_counts,
                                  **{'all_msg': expected_all_msg,
                                     'unread_topics': expected_unread_topics})
    controller.model.unread_counts = unread_counts

    set_count(id_list, controller, new_count)
    assert controller.model.unread_counts == expected_unread_counts


@pytest.mark.parametrize('all_msg, unread_topics', [
    (6, {(1001, 'Topic 1'): 3, (1002, 'Topic 3'): 1, (1003, 'Topic 10'): 2}),
    ])
@pytest.mark.parametrize(
    'new_count, expected_unread_topics, id_list, muted_topics,\
            expected_all_msg', [
     (1, {(1001, 'Topic 1'): 4, (1002, 'Topic 3'): 1,
          (1003, 'Topic 10'): 4}, [7, 8, 9], [['stream 1', 'Topic 1'],
                                              ['stream 10', 'Topic 10']], 6),
     (1, {(1001, 'Topic 1'): 4, (1002, 'Topic 3'): 2, (1003, 'Topic 10'): 4},
      [7, 8, 9, 4], [['stream 1', 'Topic 1'], ['stream 10', 'Topic 10']], 7),
     (-1, {(1001, 'Topic 1'): 2, (1002, 'Topic 3'): 1,
           (1003, 'Topic 10'): 2}, [2], [['stream 1', 'Topic 1']], 6),
     (-1, {(1001, 'Topic 1'): 2, (1003, 'Topic 10'): 2}, [2, 4],
      [['stream 1', 'Topic 1']], 5),
     ])
def test_set_count_muted_topics(initial_unread_counts, muted_topics,
                                unread_topics, all_msg, id_list, new_count,
                                expected_unread_topics, expected_all_msg,
                                controller):
    # all_msg does not change for muted topics.
    controller.model.muted_topics = muted_topics
    unread_counts = deepcopy(dict(initial_unread_counts,
                                  **{'all_msg': all_msg,
                                     'unread_topics': unread_topics}))
    expected_unread_counts = dict(initial_unread_counts,
                                  **{'all_msg': expected_all_msg,
                                     'unread_topics': expected_unread_topics})
    controller.model.unread_counts = unread_counts

    set_count(id_list, controller, new_count)
    assert controller.model.unread_counts == expected_unread_counts


@pytest.mark.parametrize('id_list, new_count', [([], 1)])
def test_set_count_screen_updated(mocker, controller, id_list, new_count):
    controller.update_screen = mocker.patch(
            'zulipterminal.core.Controller.update_screen')
    set_count(id_list, controller, new_count)
    controller.update_screen.assert_called_once_with()


def test_index_messages_narrow_all_messages(mocker,
                                            messages_successful_response,
                                            index_all_messages,
                                            initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = []
    assert index_messages(messages, model, model.index) == index_all_messages


def test_index_messages_narrow_stream(mocker,
                                      messages_successful_response,
                                      index_stream,
                                      initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['stream', 'PTEST']]
    model.is_search_narrow.return_value = False
    model.stream_id = 205
    assert index_messages(messages, model, model.index) == index_stream


def test_index_messages_narrow_topic(mocker,
                                     messages_successful_response,
                                     index_topic,
                                     initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['stream', '7'],
                    ['topic', 'Test']]
    model.is_search_narrow.return_value = False
    model.stream_id = 205
    assert index_messages(messages, model, model.index) == index_topic


def test_index_messages_narrow_user(mocker,
                                    messages_successful_response,
                                    index_user,
                                    initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['pm_with', 'boo@zulip.com']]
    model.is_search_narrow.return_value = False
    model.user_id = 5140
    model.user_dict = {
        'boo@zulip.com': {
            'user_id': 5179,
        }
    }
    assert index_messages(messages, model, model.index) == index_user


def test_index_messages_narrow_user_multiple(mocker,
                                             messages_successful_response,
                                             index_user_multiple,
                                             initial_index) -> None:
    messages = messages_successful_response['messages']
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['pm_with', 'boo@zulip.com, bar@zulip.com']]
    model.is_search_narrow.return_value = False
    model.user_id = 5140
    model.user_dict = {
        'boo@zulip.com': {
            'user_id': 5179,
        },
        'bar@zulip.com': {
            'user_id': 5180
        }
    }
    assert index_messages(messages, model, model.index) == index_user_multiple


@pytest.mark.parametrize('edited_msgs', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_edited_message(mocker,
                              messages_successful_response,
                              empty_index,
                              edited_msgs,
                              initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in edited_msgs:
            msg['edit_history'] = []
    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = []

    expected_index = dict(empty_index, edited_messages=edited_msgs,
                          all_msg_ids={537286, 537287, 537288})
    for msg_id, msg in expected_index['messages'].items():
        if msg_id in edited_msgs:
            msg['edit_history'] = []

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('msgs_with_stars', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_starred(mocker,
                       messages_successful_response,
                       empty_index,
                       msgs_with_stars,
                       initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')

    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['is', 'starred']]
    model.is_search_narrow.return_value = False
    expected_index = dict(empty_index, private_msg_ids={537287, 537288},
                          starred_msg_ids=msgs_with_stars)
    for msg_id, msg in expected_index['messages'].items():
        if msg_id in msgs_with_stars and 'starred' not in msg['flags']:
            msg['flags'].append('starred')

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('mentioned_messages', [
    {537286, 537287, 537288},
    {537286}, {537287}, {537288},
    {537286, 537287}, {537286, 537288}, {537287, 537288},
])
def test_index_mentioned_messages(mocker,
                                  messages_successful_response,
                                  empty_index,
                                  mentioned_messages,
                                  initial_index):
    messages = messages_successful_response['messages']
    for msg in messages:
        if msg['id'] in mentioned_messages and 'mentioned' not in msg['flags']:
            msg['flags'].append('mentioned')

    model = mocker.patch('zulipterminal.model.Model.__init__',
                         return_value=None)
    model.index = initial_index
    model.narrow = [['is', 'mentioned']]
    model.is_search_narrow.return_value = False
    expected_index = dict(empty_index, private_msg_ids={537287, 537288},
                          mentioned_msg_ids=mentioned_messages)

    for msg_id, msg in expected_index['messages'].items():
        if msg_id in mentioned_messages and 'mentioned' not in msg['flags']:
            msg['flags'].append('mentioned')

    assert index_messages(messages, model, model.index) == expected_index


@pytest.mark.parametrize('iterable, map_func, expected_powerset', [
    ([], set, [set()]),
    ([1], set, [set(), {1}]),
    ([1, 2], set, [set(), {1}, {2}, {1, 2}]),
    ([1, 2, 3], set,
     [set(), {1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}]),
    ([1, 2], tuple, [(), (1,), (2,), (1, 2)]),
])
def test_powerset(iterable, map_func, expected_powerset):
    assert powerset(iterable, map_func) == expected_powerset


@pytest.mark.parametrize('muted_streams, muted_topics, vary_in_unreads', [
    ([99], [['Some general stream', 'Some general unread topic']], {
        'all_msg': 9,
        'streams': {99: 1},
        'unread_topics': {(99, 'Some private unread topic'): 1},
        'all_mentions': 0,
    }),
    ([1000], [['Secret stream', 'Some private unread topic']], {
        'all_msg': 11,
        'streams': {1000: 3},
        'unread_topics': {(1000, 'Some general unread topic'): 3},
        'all_mentions': 0,
    }),
    ([1], [], {'all_mentions': 0})
], ids=['mute_private_stream_mute_general_stream_topic',
        'mute_general_stream_mute_private_stream_topic',
        'no_mute_some_other_stream_muted']
)
def test_classify_unread_counts(mocker, initial_data, stream_dict,
                                classified_unread_counts, muted_topics,
                                muted_streams, vary_in_unreads):
    model = mocker.Mock()
    model.stream_dict = stream_dict
    model.initial_data = initial_data
    model.muted_topics = muted_topics
    model.muted_streams = muted_streams
    assert classify_unread_counts(model) == dict(classified_unread_counts,
                                                 **vary_in_unreads)


@pytest.mark.parametrize('color', [
    '#ffffff', '#f0f0f0', '#f0f1f2', '#fff', '#FFF', '#F3F5FA'
])
def test_color_formats(mocker, color):
    canon = canonicalize_color(color)
    assert canon == '#fff'


@pytest.mark.parametrize('color', [
    '#', '#f', '#ff', '#ffff', '#fffff', '#fffffff', '#abj', '#398a0s'
])
def test_invalid_color_format(mocker, color):
    with pytest.raises(ValueError) as e:
        canon = canonicalize_color(color)
    assert str(e.value) == 'Unknown format for color "{}"'.format(color)


@pytest.mark.parametrize('OS, is_notification_sent', [
    ([True, False, False], True),  # OS: [WSL, MACOS, LINUX]
    ([False, True, False], True),
    ([False, False, True], True),
    ([False, False, False], False),  # Unsupported OS
])
def test_notify(mocker, OS, is_notification_sent):
    title = "Author"
    text = "Hello!"
    mocker.patch('zulipterminal.helper.WSL', OS[0])
    mocker.patch('zulipterminal.helper.MACOS', OS[1])
    mocker.patch('zulipterminal.helper.LINUX', OS[2])
    subprocess = mocker.patch('zulipterminal.helper.subprocess')
    notify(title, text)
    assert subprocess.run.called == is_notification_sent
