import json
from platform import platform
from typing import Any

import pytest

from zulipterminal.model import Model, ServerConnectionFailure
from zulipterminal.helper import initial_index


class TestModel:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: Any) -> None:
        self.controller = mocker.patch('zulipterminal.core.'
                                       'Controller',
                                       return_value=None)
        self.client = mocker.patch('zulipterminal.core.'
                                   'Controller.client')
        mocker.patch('zulipterminal.model.Model.update_presence')

    @pytest.fixture
    def model(self, mocker, initial_data, user_profile):
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        # NOTE: PATCH WHERE USED NOT WHERE DEFINED
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        self.client.get_profile.return_value = user_profile
        model = Model(self.controller)
        return model

    def test_init(self, model, initial_data, user_profile):
        assert hasattr(model, 'controller')
        assert hasattr(model, 'client')
        assert model.msg_view is None
        assert model.msg_list is None
        assert model.narrow == []
        assert model.update is False
        assert model.stream_id == -1
        assert model.stream_dict == {}
        assert model.recipients == frozenset()
        assert model.index == initial_index
        model.get_messages.assert_called_once_with(num_before=30,
                                                   num_after=10,
                                                   anchor=None)
        assert model.initial_data == initial_data
        model.client.get_profile.assert_called_once_with()
        assert model.user_id == user_profile['user_id']
        model.get_all_users.assert_called_once_with()
        assert model.users == []
        (model._stream_info_from_subscriptions.
         assert_called_once_with(initial_data['subscriptions']))
        assert model.pinned_streams == []
        assert model.unpinned_streams == []
        self.classify_unread_counts.assert_called_once_with(model)
        assert model.unread_counts == []

    def test_register_initial_desired_events(self, mocker, initial_data):
        mocker.patch('zulipterminal.model.Model._update_user_id')
        mocker.patch('zulipterminal.model.Model.get_messages')
        mocker.patch('zulipterminal.model.Model.get_all_users')
        self.client.register.return_value = initial_data

        model = Model(self.controller)

        event_types = [
            'message',
            'update_message',
            'reaction',
            'typing',
            'update_message_flags',
        ]
        fetch_event_types = [
            'presence',
            'subscription',
            'message',
            'update_message_flags',
            'muted_topics',
            'realm_user',
        ]
        model.client.register.assert_called_once_with(
                event_types=event_types,
                fetch_event_types=fetch_event_types,
                apply_markdown=True,
                client_gravatar=True)

    @pytest.mark.parametrize('msg_id', [1, 5, set()])
    @pytest.mark.parametrize('narrow', [
        [],
        [['stream', 'hello world']],
        [['stream', 'hello world'], ['topic', "what's it all about?"]],
        [['pm_with', 'FOO@zulip.com']],
        [['pm_with', 'Foo@zulip.com, Bar@zulip.com']],
        [['is', 'private']],
        [['is', 'starred']],
    ])
    def test_get_focus_in_current_narrow_individually(self,
                                                      model, msg_id, narrow):
        model.index = {'pointer': {str(narrow): msg_id}}
        model.narrow = narrow
        assert model.get_focus_in_current_narrow() == msg_id

    @pytest.mark.parametrize('msg_id', [1, 5])
    @pytest.mark.parametrize('narrow', [
        [],
        [['stream', 'hello world']],
        [['stream', 'hello world'], ['topic', "what's it all about?"]],
        [['pm_with', 'FOO@zulip.com']],
        [['pm_with', 'Foo@zulip.com, Bar@zulip.com']],
        [['is', 'private']],
        [['is', 'starred']],
    ])
    def test_set_focus_in_current_narrow(self, mocker, model, narrow, msg_id):
        from collections import defaultdict
        model.index = dict(pointer=defaultdict(set))
        model.narrow = narrow
        model.set_focus_in_current_narrow(msg_id)
        assert model.index['pointer'][str(narrow)] == msg_id

    @pytest.mark.parametrize('bad_args', [
        dict(topic='some topic'),
        dict(stream='foo', search='text'),
        dict(topic='blah', search='text'),
        dict(pm_with='someone', topic='foo')
    ])
    def test_set_narrow_bad_input(self, model, bad_args):
        with pytest.raises(RuntimeError):
            model.set_narrow(**bad_args)

    @pytest.mark.parametrize('narrow, good_args', [
        ([], dict()),
        ([['stream', 'some stream']], dict(stream='some stream')),
        ([['stream', 'some stream'], ['topic', 'some topic']],
         dict(stream='some stream', topic='some topic')),
        ([['search', 'something interesting']],
         dict(search='something interesting')),
        ([['is', 'starred']], dict(starred=True)),
        ([['is', 'private']], dict(pms=True)),
        ([['pm_with', 'FOO@zulip.com']], dict(pm_with='FOO@zulip.com')),
    ])
    def test_set_narrow_already_set(self, model, narrow, good_args):
        model.narrow = narrow
        assert model.set_narrow(**good_args)
        assert model.narrow == narrow

    @pytest.mark.parametrize('initial_narrow, narrow, good_args', [
        ([['stream', 'foo']], [], dict()),
        ([], [['stream', 'some stream']], dict(stream='some stream')),
        ([], [['stream', 'some stream'], ['topic', 'some topic']],
         dict(stream='some stream', topic='some topic')),
        ([], [['is', 'starred']], dict(starred=True)),
        ([], [['is', 'private']], dict(pms=True)),
        ([], [['pm_with', 'FOO@zulip.com']], dict(pm_with='FOO@zulip.com')),
    ])
    def test_set_narrow_not_already_set(self, model, initial_narrow, narrow,
                                        good_args):
        model.narrow = initial_narrow
        assert not model.set_narrow(**good_args)
        assert model.narrow != initial_narrow
        assert model.narrow == narrow

    @pytest.mark.parametrize("narrow, index, current_ids", [
        ([], {
            "all_messages": {0, 1}
        }, {0, 1}),
        ([['stream', 'FOO']], {
            "all_stream": {
                1: {0, 1}
            }
        }, {0, 1}),
        ([['stream', 'FOO'],
         ['topic', 'BOO']], {
             'stream': {
                 1: {
                     'BOO': {0, 1}
                 }
             }
         }, {0, 1}),
        ([['stream', 'FOO'],  # Covers one empty-set case
         ['topic', 'BOOBOO']], {
             'stream': {
                 1: {
                     'BOO': {0, 1}
                 }
             }
         }, set()),
        ([['is', 'private']], {
            'all_private': {0, 1}
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {
            'private': {
                frozenset({1, 2}): {0, 1}
            }
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {  # Covers recipient empty-set case
            'private': {
                frozenset({1, 3}): {0, 1}  # NOTE {1,3} not {1,2}
            }
        }, set()),
        ([['search', 'FOO']], {
            'search': {0, 1}
        }, {0, 1}),
        ([['is', 'starred']], {
            'all_starred': {0, 1}
        }, {0, 1})
    ])
    def test_get_message_ids_in_current_narrow(self, mocker, model,
                                               narrow, index, current_ids):
        model.recipients = frozenset({1, 2})
        model.stream_id = 1
        model.narrow = narrow
        model.index = index
        assert current_ids == model.get_message_ids_in_current_narrow()

    @pytest.mark.parametrize("msg_id, existing_reactions, expected_method", [
        (5, [], 'POST'),
        (5, [dict(user='me', emoji_code='1f44d')], 'DELETE'),
        (5, [dict(user='not me', emoji_code='1f44d')], 'POST'),
        (5, [dict(user='me', emoji_code='1f614')], 'POST'),
        (5, [dict(user='not me', emoji_code='1f614')], 'POST'),
    ])
    def test_react_to_message_with_thumbs_up(self, model,
                                             msg_id,
                                             existing_reactions,
                                             expected_method):
        full_existing_reactions = [dict(er, user=dict(user_id=model.user_id
                                                      if er['user'] == 'me'
                                                      else model.user_id+1))
                                   for er in existing_reactions]
        message = dict(
            id=msg_id,
            reactions=full_existing_reactions)
        reaction_spec = dict(
            emoji_name='thumbs_up',
            reaction_type='unicode_emoji',
            emoji_code='1f44d')
        model.react_to_message(message, 'thumbs_up')
        model.client.call_endpoint.assert_called_once_with(
            url='messages/{}/reactions'.format(msg_id),
            method=expected_method,
            request=reaction_spec)

    def test_react_to_message_for_not_thumbs_up(self, model):
        with pytest.raises(AssertionError):
            model.react_to_message(dict(), 'x')

    # NOTE: This tests only getting next-unread, not a fixed anchor
    def test_success_get_messages(self, mocker, messages_successful_response,
                                  index_all_messages, initial_data,
                                  num_before=30, num_after=10):
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_user_id')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        self.client.do_api_query.return_value = messages_successful_response
        mocker.patch('zulipterminal.model.index_messages',
                     return_value=index_all_messages)
        model = Model(self.controller)
        request = {
            'anchor': 0,
            'num_before': num_before,
            'num_after': num_after,
            'apply_markdown': True,
            'use_first_unread_anchor': True,
            'client_gravatar': True,
            'narrow': json.dumps(model.narrow),
        }
        model.client.do_api_query.assert_called_once_with(
            request, '/json/messages', method="GET")
        assert model.index == index_all_messages
        anchor = messages_successful_response['anchor']
        if anchor < 10000000000000000:
            assert model.index['pointer'][str(model.narrow)] == anchor
        assert model.update is True

    def test_get_message_false_first_anchor(
            self, mocker, messages_successful_response, index_all_messages,
            initial_data, num_before=30, num_after=10
            ):
        # TEST FOR get_messages() with first_anchor=False
        # and anchor=0

        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_user_id')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        messages_successful_response['anchor'] = 0
        self.client.do_api_query.return_value = messages_successful_response
        mocker.patch('zulipterminal.model.index_messages',
                     return_value=index_all_messages)

        model = Model(self.controller)
        model.get_messages(num_before=num_before, num_after=num_after,
                           anchor=0)
        self.client.do_api_query.return_value = messages_successful_response
        # anchor should have remained the same
        anchor = messages_successful_response['anchor']
        assert model.index['pointer'][str(model.narrow)] == 0

        # TEST `query_range` < no of messages received
        model.update = False  # RESET model.update value
        model.get_messages(num_after=0, num_before=0, anchor=0)
        assert model.update is False

    # FIXME This only tests the case where the get_messages is in __init__
    def test_fail_get_messages(self, mocker, error_response,
                               initial_data, num_before=30, num_after=10):
        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_user_id')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mock before calling get_messages
        self.client.do_api_query.return_value = error_response

        with pytest.raises(ServerConnectionFailure):
            model = Model(self.controller)

    @pytest.mark.parametrize('flags_before, expected_operator', [
        ([], 'add'),
        (['starred'], 'remove'),
        (['read'], 'add'),
        (['read', 'starred'], 'remove'),
        (['starred', 'read'], 'remove'),
    ])
    def test_toggle_message_star_status(self, mocker, model, flags_before,
                                        expected_operator):
        mocker.patch('zulip.Client')
        message = {
            'id': 99,
            'flags': flags_before,
        }
        model.toggle_message_star_status(message)

        request = {
            'flag': 'starred',
            'messages': [99],
            'op': expected_operator
        }
        model.client.call_endpoint.assert_called_once_with(
            url="messages/flags",
            method="POST",
            request=request
        )

    def test_update_flag(self, model, mocker: Any) -> None:
        mock_api_query = mocker.patch('zulipterminal.core.Controller'
                                      '.client.do_api_query')

        model.update_flag([1, 2])

        mock_api_query.assert_called_once_with(
            {'flag': 'read', 'messages': [1, 2], 'op': 'add'},
            '/json/messages/flags',
            method='POST'
        )

    def test_update_flag_empty_msg_list(self, model) -> None:
        assert model.update_flag([]) is None

    def test__update_initial_data(self, model, initial_data):
        assert model.initial_data == initial_data

    def test__update_initial_data_raises_exception(self, mocker, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.get_messages')
        mocker.patch('zulipterminal.model.Model._update_user_id')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        self.client.register.return_value = initial_data
        self.client.get_members.return_value = {
            'members': initial_data['realm_users']}
        model = Model(self.controller)

        # Test if raises Exception
        self.client.register.side_effect = Exception()
        with pytest.raises(Exception):
            model._update_initial_data()

    def test_get_all_users(self, mocker, initial_data, user_list, user_dict,
                           user_id):
        mocker.patch('zulipterminal.model.Model._update_user_id',
                     return_value=user_id)
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        model = Model(self.controller)
        assert model.user_dict == user_dict
        assert model.users == user_list

    @pytest.mark.parametrize('muted', [
        set(), {86}, {14}, {99}, {99, 14}, {14, 86, 99}
    ])
    def test__stream_info_from_subscriptions(self, initial_data, streams,
                                             muted):
        subs = [dict(entry, in_home_view=entry['stream_id'] not in muted)
                for entry in initial_data['subscriptions']]
        by_id, muted_streams, pinned, unpinned = (
                Model._stream_info_from_subscriptions(subs))
        assert len(by_id)
        assert all(msg_id == msg['stream_id'] for msg_id, msg in by_id.items())
        assert muted_streams == muted
        assert pinned == []  # FIXME generalize/parametrize
        assert unpinned == streams  # FIXME generalize/parametrize

    def test_append_message_with_Falsey_log(self, mocker, model):
        model.update = True
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        model.msg_list = mocker.Mock()
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        model.msg_list.log = []
        event = {'message': {'id': 0}}

        model.append_message(event)

        assert len(model.msg_list.log) == 1  # Added "msg_w" element
        (create_msg_box_list.
         assert_called_once_with(model, [0], last_message=None))

    def test_append_message_with_valid_log(self, mocker, model):
        model.update = True
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        model.msg_list = mocker.Mock()
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        model.msg_list.log = [mocker.Mock()]
        event = {'message': {'id': 0}}

        model.append_message(event)

        assert len(model.msg_list.log) == 2  # Added "msg_w" element
        # NOTE: So we expect the first element *was* the last_message parameter
        expected_last_msg = model.msg_list.log[0].original_widget.message
        (create_msg_box_list.
         assert_called_once_with(model, [0], last_message=expected_last_msg))

    @pytest.mark.parametrize('response, narrow, recipients, log', [
        ({'type': 'stream', 'id': 1}, [], frozenset(), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['is', 'private']], frozenset(), ['msg_w']),
        ({'type': 'stream', 'id': 1, 'subject': 'b'},
         [['stream', 'a'], ['topic', 'b']],
         frozenset(), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['pm_with', 'notification-bot@zulip.com']],
         frozenset({5827, 5}), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['is', 'search']],
         frozenset(), []),
        ({'type': 'private', 'id': 1},
         [['pm_with', 'notification-bot@zulip.com']],
         frozenset({5827, 3212}), []),
    ], ids=['stream', 'all_private', 'topic', 'pm_existing_conv',
            'search', 'pm_no_existing_conv'])
    def test_append_message(self, mocker, user_dict, user_profile, response,
                            narrow, recipients, model, log):
        model.update = True
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        set_count = mocker.patch('zulipterminal.model.set_count')
        model.msg_list = mocker.Mock()
        model.msg_list.log = []
        model.narrow = narrow
        model.recipients = recipients
        model.user_id = user_profile['user_id']
        model.user_dict = user_dict
        event = {'message': response}

        model.append_message(event)

        assert model.msg_list.log == log
        set_count.assert_called_once_with([response['id']], self.controller, 1)

        model.update = False
        model.append_message(event)
        # LOG REMAINS THE SAME IF UPDATE IS FALSE
        assert model.msg_list.log == log

    @pytest.mark.parametrize('response, index', [
        ({
            'message_id': 1,
            'content': 'Foo is Boo',
        }, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'Boo is Foo',
                },
                2: {
                    'id': 2,
                    'content': "Boo is not Foo"
                }
            }
        })
    ])
    def test_update_message(self, mocker, model, response, index):
        model.index = index
        model.msg_list = mocker.Mock()
        mock_msg = mocker.Mock()
        another_msg = mocker.Mock()
        model.msg_list.log = [mock_msg, another_msg]
        mock_msg.original_widget.message = index['messages'][1]
        another_msg.original_widget.message = index['messages'][2]
        mocker.patch('zulipterminal.model.create_msg_box_list',
                     return_value=[mock_msg])
        model.update_message(response)
        assert model.index['messages'][1]['content'] == response['content']
        assert model.msg_list.log[0] == mock_msg
        self.controller.update_screen.assert_called_once_with()

        # TEST FOR FALSE CASES
        model.index['messages'][1] = {}
        model.update_message(response)
        # If there was no message earlier then don't update
        assert model.index['messages'][1] == {}

    @pytest.mark.parametrize('response, index', [
        ({'emoji_code': '1f44d',
          'id': 2,
          'user': {
              'email': 'Foo@zulip.com',
              'user_id': 5140,
              'full_name': 'Foo Boo'
          },
          'reaction_type': 'unicode_emoji',
          'message_id': 1,
          'emoji_name': 'thumbs_up',
          'type': 'reaction',
          'op': 'add'
          }, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'Boo is Foo',
                    'reactions': [
                        {
                            'user': {
                                'email': 'Foo@zulip.com',
                                'user_id': 1,
                                'full_name': 'Foo Boo'
                            },
                            'reaction_type': 'unicode_emoji',
                            'emoji_code': '1232',
                            'emoji_name': 'thumbs_up'
                        }
                    ],
                },
                2: {
                    'id': 2,
                    'content': "Boo is not Foo",
                    'reactions': [],
                }
            }
        })])
    def test_update_reaction(self, mocker, model, response, index):
        model.index = index
        model.msg_list = mocker.Mock()
        mock_msg = mocker.Mock()
        another_msg = mocker.Mock()
        model.msg_list.log = [mock_msg, another_msg]
        mock_msg.original_widget.message = index['messages'][1]
        another_msg.original_widget.message = index['messages'][2]
        mocker.patch('zulipterminal.model.create_msg_box_list',
                     return_value=[mock_msg])
        model.update_reaction(response)
        update_emoji = model.index['messages'][1]['reactions'][1]['emoji_code']
        assert update_emoji == response['emoji_code']
        self.controller.update_screen.assert_called_once_with()

        # TEST FOR FALSE CASES
        model.index['messages'][1] = {}
        model.update_reaction(response)
        # If there was no message earlier then don't update
        assert model.index['messages'][1] == {}

    @pytest.mark.parametrize('response, index', [
        ({'emoji_code': '1f44d',
          'id': 2,
          'user': {
              'email': 'Foo@zulip.com',
              'user_id': 5140,
              'full_name': 'Foo Boo'
          },
          'reaction_type': 'unicode_emoji',
          'message_id': 1,
          'emoji_name': 'thumbs_up',
          'type': 'reaction',
          'op': 'add'
          }, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'Boo is Foo',
                    'reactions': [
                        {
                            'user': {
                                'email': 'Foo@zulip.com',
                                'user_id': 1,
                                'full_name': 'Foo Boo'
                            },
                            'reaction_type': 'unicode_emoji',
                            'emoji_code': '1232',
                            'emoji_name': 'thumbs_up'
                        }
                    ],
                },
                2: {
                    'id': 2,
                    'content': "Boo is not Foo",
                    'reactions': [],
                }
            }
        })])
    def test_update_reaction_remove_reaction(self, mocker, model, response,
                                             index):
        model.index = index
        model.msg_list = mocker.Mock()
        mock_msg = mocker.Mock()
        another_msg = mocker.Mock()
        model.msg_list.log = [mock_msg, another_msg]
        mock_msg.original_widget.message = index['messages'][1]
        another_msg.original_widget.message = index['messages'][2]
        mocker.patch('zulipterminal.model.create_msg_box_list',
                     return_value=[mock_msg])

        # Test removing of reaction.
        response['op'] = 'remove'
        model.update_reaction(response)
        assert len(model.index['messages'][1]['reactions']) == 1

    def test_update_star_status_no_index(self, mocker, model):
        model.index = dict(messages={})  # Not indexed
        event = dict(messages=[1], flag='starred', all=False)
        mocker.patch('zulipterminal.model.Model.update_rendered_view')

        model.update_message_flag_status(event)

        assert model.index == dict(messages={})
        model.update_rendered_view.assert_not_called()

    def test_update_star_status_invalid_operation(self, mocker, model):
        model.index = dict(messages={1: {'flags': None}})  # Minimal
        event = {
            'messages': [1],
            'type': 'update_message_flags',
            'flag': 'starred',
            'operation': 'OTHER',  # not 'add' or 'remove'
            'all': False,
        }
        mocker.patch('zulipterminal.model.Model.update_rendered_view')
        with pytest.raises(RuntimeError):
            model.update_message_flag_status(event)
        model.update_rendered_view.assert_not_called()

    @pytest.mark.parametrize('event_message_ids, indexed_ids', [
        ([1], [1]),
        ([1, 2], [1]),
        ([1, 2], [1, 2]),
        ([1], [1, 2]),
        ([], [1, 2]),
        ([1, 2], []),
    ])
    @pytest.mark.parametrize('event_op, flags_before, flags_after', [
        ('add', [], ['starred']),
        ('add', ['read'], ['read', 'starred']),
        ('add', ['starred'], ['starred']),
        ('add', ['read', 'starred'], ['read', 'starred']),
        ('remove', [], []),
        ('remove', ['read'], ['read']),
        ('remove', ['starred'], []),
        ('remove', ['read', 'starred'], ['read']),
        ('remove', ['starred', 'read'], ['read']),
    ])
    def test_update_star_status(self, mocker, model, event_op,
                                event_message_ids, indexed_ids,
                                flags_before, flags_after):
        model.index = dict(messages={msg_id: {'flags': flags_before}
                                     for msg_id in indexed_ids})
        event = {
            'messages': event_message_ids,
            'type': 'update_message_flags',
            'flag': 'starred',
            'operation': event_op,
            'all': False,
        }
        mocker.patch('zulipterminal.model.Model.update_rendered_view')

        model.update_message_flag_status(event)

        changed_ids = set(indexed_ids) & set(event_message_ids)
        for changed_id in changed_ids:
            assert model.index['messages'][changed_id]['flags'] == flags_after
        (model.update_rendered_view.
         has_calls([mocker.call(changed_id) for changed_id in changed_ids]))

        for unchanged_id in (set(indexed_ids) - set(event_message_ids)):
            assert (model.index['messages'][unchanged_id]['flags'] ==
                    flags_before)

    @pytest.mark.parametrize('narrow, event, called', [
        # Not in PM Narrow
        ([], {}, False),
        # Not in PM Narrow with sender
        (
            [['pm_with', 'iago@zulip.com']],
            {
                'type': 'typing',
                'op': 'start',
                'sender': {
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                },
                'recipients': [{
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                }, {
                    'user_id': 5,
                    'email': 'iago@zulip.com'
                }],
                'id': 0
            },
            False,
        ),
        # In PM narrow with the sender, OP - 'start'
        (
            [['pm_with', 'hamlet@zulip.com']],
            {
                'type': 'typing',
                'op': 'start',
                'sender': {
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                },
                'recipients': [{
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                }, {
                    'user_id': 5,
                    'email': 'iago@zulip.com'
                }],
                'id': 0
            },
            True,
        ),
        # OP - 'stop'
        (
            [['pm_with', 'hamlet@zulip.com']],
            {
                'type': 'typing',
                'op': 'stop',
                'sender': {
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                },
                'recipients': [{
                    'user_id': 4,
                    'email': 'hamlet@zulip.com'
                }, {
                    'user_id': 5,
                    'email': 'iago@zulip.com'
                }],
                'id': 0
            },
            True,
        )
    ], ids=['not_in_pm_narrow', 'not_in_pm_narrow_with_sender',
            'start', 'stop'])
    def test_handle_typing_event(self, mocker, model,
                                 narrow, event, called):
        mocker.patch('zulipterminal.ui.View.set_footer_text')
        model.narrow = narrow
        model.user_dict = {'hamlet@zulip.com': {'full_name': 'hamlet'}}

        model.handle_typing_event(event)

        assert model.controller.view.set_footer_text.called == called
