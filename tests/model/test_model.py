import json
from platform import platform
from typing import Any

import pytest

from zulipterminal.model import Model


class TestModel:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: Any) -> None:
        self.controller = mocker.patch('zulipterminal.core.'
                                       'Controller',
                                       return_value=None)
        self.client = mocker.patch('zulipterminal.core.'
                                   'Controller.client')

    @pytest.fixture
    def model(self, mocker, initial_data, user_profile):
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
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
        assert model.anchor == 0
        assert model.num_before == 30
        assert model.num_after == 10
        assert model.msg_list is None
        assert model.narrow == []
        assert model.update is False
        assert model.stream_id == -1
        assert model.stream_dict == {}
        assert model.recipients == frozenset()
        assert model.index is None
        model.get_messages.assert_called_once_with(first_anchor=True)
        assert model.initial_data == initial_data
        model.client.get_profile.assert_called_once_with()
        assert model.user_id == user_profile['user_id']
        model.get_all_users.assert_called_once_with()
        assert model.users == []
        model.get_subscribed_streams.assert_called_once_with()
        assert model.streams == []
        self.classify_unread_counts.assert_called_once_with(model)
        assert model.unread_counts == []

    @pytest.mark.parametrize('msg_id', [1, 5, set()])
    @pytest.mark.parametrize('narrow', [
        [],
        [['stream', 'hello world']],
        [['stream', 'hello world'], ['topic', "what's it all about?"]],
        [['pm_with', 'FOO@zulip.com']],
        [['pm_with', 'Foo@zulip.com, Bar@zulip.com']],
        [['is', 'private']],
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
        ([['is', 'private']], {
            'all_private': {0, 1}
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {
            'private': {
                frozenset({1, 2}): {0, 1}
            }
        }, {0, 1}),
        ([['search', 'FOO']], {
            'search': {0, 1}
        }, {0, 1})
    ])
    def test_get_message_ids_in_current_narrow(self, mocker, model,
                                               narrow, index, current_ids):
        model.recipients = frozenset({1, 2})
        model.stream_id = 1
        model.narrow = narrow
        model.index = index
        assert current_ids == model.get_message_ids_in_current_narrow()

    def test_success_get_messages(self, mocker, messages_successful_response,
                                  index_all_messages, initial_data):
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        self.client.do_api_query.return_value = messages_successful_response
        mocker.patch('zulipterminal.model.index_messages',
                     return_value=index_all_messages)
        model = Model(self.controller)
        request = {
            'anchor': model.anchor,
            'num_before': model.num_before,
            'num_after': model.num_after,
            'apply_markdown': False,
            'use_first_unread_anchor': True,
            'client_gravatar': False,
            'narrow': json.dumps(model.narrow),
        }
        model.client.do_api_query.assert_called_once_with(
            request, '/json/messages', method="GET")
        assert model.index == index_all_messages
        anchor = messages_successful_response['anchor']
        assert model.index[str(model.narrow)] == anchor
        assert model.update is True

    def test_get_message_false_first_anchor(
            self, mocker, messages_successful_response, index_all_messages,
            initial_data
            ):
        # TEST FOR get_messages() with first_anchor=False

        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        messages_successful_response['anchor'] = 0
        self.client.do_api_query.return_value = messages_successful_response
        mocker.patch('zulipterminal.model.index_messages',
                     return_value=index_all_messages)

        model = Model(self.controller)
        model.get_messages(first_anchor=False)
        self.client.do_api_query.return_value = messages_successful_response
        # anchor should have remained the same
        anchor = messages_successful_response['anchor']
        assert model.index[str(model.narrow)] == 0

        # TEST `query_range` < no of messages received
        model.update = False  # RESET model.update value
        model.num_after = 0
        model.num_before = 0
        model.get_messages(first_anchor=False)
        assert model.update is False

    def test_fail_get_messages(self, mocker, error_response,
                               initial_data):
        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        self.client.do_api_query.return_value = error_response
        model = Model(self.controller)
        request = {
            'anchor': model.anchor,
            'num_before': model.num_before,
            'num_after': model.num_after,
            'apply_markdown': False,
            'use_first_unread_anchor': True,
            'client_gravatar': False,
            'narrow': json.dumps(model.narrow),
        }
        model.client.do_api_query.assert_called_once_with(
            request, '/json/messages', method="GET")
        assert model.index is None

    def test__update_initial_data(self, model, initial_data):
        assert model.initial_data == initial_data

    def test__update_initial_data_raises_exception(self, mocker, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.get_messages')
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
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

    def test_get_all_users(self, mocker, initial_data, user_list, user_dict):
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        model = Model(self.controller)
        assert model.user_dict == user_dict
        assert model.users == user_list

    def test_get_subscribed_streams(self, mocker, initial_data, streams):
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model._update_realm_users')
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        model = Model(self.controller)
        assert model.streams == streams

    @pytest.mark.parametrize('response, narrow, recipients, log', [
        ({'type': 'stream', 'id': 1}, [], frozenset(), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['is', 'private']], frozenset(), ['msg_w']),
        ({'type': 'stream', 'id': 1, 'subject': 'b'},
         [['stream', 'a'], ['topic', 'b']],
         frozenset(), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['pm_with', 'FOOBOO@gmail.com']],
         frozenset({5827, 5140}), ['msg_w']),  # User Ids taken from conftest
        ({'type': 'private', 'id': 1},
         [['is', 'search']],
         frozenset(), []),
        ({'type': 'private', 'id': 1},
         [['pm_with', 'FOOBOO@gmail.com']],
         frozenset({5827, 3212}), []),
    ])
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
        model.append_message(response)
        assert model.msg_list.log == log
        set_count.assert_called_once_with([response['id']], self.controller, 1)
        model.update = False
        model.append_message(response)
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

    def test_update_realm_users(self, mocker, initial_data, user_profile):
        mocker.patch('zulipterminal.model.Model.get_messages')
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        # NOTE: PATCH WHERE USED NOT WHERE DEFINED
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        self.client.get_profile.return_value = user_profile
        members = ["FOO", "BOO"]
        self.client.get_members.return_value = {"members": members}
        model = Model(self.controller)
        model._update_realm_users()
        assert model.initial_data['realm_users'] == members
