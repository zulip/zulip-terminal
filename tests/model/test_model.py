import json
from platform import platform
from typing import Any

import pytest
from zulip import ZulipError

from zulipterminal.helper import initial_index, powerset
from zulipterminal.model import Model, ServerConnectionFailure


class TestModel:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker: Any) -> None:
        self.urlparse = mocker.patch('urllib.parse.urlparse')
        self.controller = mocker.patch('zulipterminal.core.'
                                       'Controller',
                                       return_value=None)
        self.client = mocker.patch('zulipterminal.core.'
                                   'Controller.client')
        self.client.base_url = 'chat.zulip.zulip'
        mocker.patch('zulipterminal.model.Model._start_presence_updates')

    @pytest.fixture
    def model(self, mocker, initial_data, user_profile):
        mocker.patch('zulipterminal.model.Model.get_messages',
                     return_value='')
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
        assert model.found_newest is False
        assert model.stream_id == -1
        assert model.stream_dict == {}
        assert model.recipients == frozenset()
        assert model.index == initial_index
        model.get_messages.assert_called_once_with(num_before=30,
                                                   num_after=10,
                                                   anchor=None)
        assert model.initial_data == initial_data
        assert model.user_id == user_profile['user_id']
        assert model.user_full_name == user_profile['full_name']
        assert model.user_email == user_profile['email']
        assert model.server_name == initial_data['realm_name']
        # FIXME Add test here for model.server_url
        model.get_all_users.assert_called_once_with()
        assert model.users == []
        (model._stream_info_from_subscriptions.
         assert_called_once_with(initial_data['subscriptions']))
        assert model.pinned_streams == []
        assert model.unpinned_streams == []
        self.classify_unread_counts.assert_called_once_with(model)
        assert model.unread_counts == []

    def test_init_InvalidAPIKey_response(self, mocker, initial_data):
        # Both network calls indicate the same response
        mocker.patch('zulipterminal.model.Model.get_messages',
                     return_value='Invalid API key')
        mocker.patch('zulipterminal.model.Model._register_desired_events',
                     return_value='Invalid API key')

        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        with pytest.raises(ServerConnectionFailure) as e:
            model = Model(self.controller)

        assert str(e.value) == 'Invalid API key (get_messages, register)'

    def test_init_ZulipError_exception(self, mocker, initial_data,
                                       exception_text="X"):
        # Both network calls fail, resulting in exceptions
        mocker.patch('zulipterminal.model.Model.get_messages',
                     side_effect=ZulipError(exception_text))
        mocker.patch('zulipterminal.model.Model._register_desired_events',
                     side_effect=ZulipError(exception_text))

        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        with pytest.raises(ServerConnectionFailure) as e:
            model = Model(self.controller)

        assert str(e.value) == exception_text + ' (get_messages, register)'

    def test_register_initial_desired_events(self, mocker, initial_data):
        mocker.patch('zulipterminal.model.Model.get_messages',
                     return_value='')
        mocker.patch('zulipterminal.model.Model.get_all_users')
        mocker.patch('zulipterminal.model.Model.fetch_all_topics')
        self.client.register.return_value = initial_data

        model = Model(self.controller)

        event_types = [
            'message',
            'update_message',
            'reaction',
            'subscription',
            'typing',
            'update_message_flags',
        ]
        fetch_event_types = [
            'realm',
            'presence',
            'subscription',
            'message',
            'update_message_flags',
            'muted_topics',
            'realm_user',
            'realm_user_groups',
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

    @pytest.mark.parametrize('narrow, is_search_narrow', [
        ([], False),
        ([['search', 'FOO']], True),
        ([['is', 'private']], False),
        ([['is', 'private'], ['search', 'FOO']], True),
        ([['search', 'FOO'], ['is', 'private']], True),
        ([['stream', 'PTEST']], False),
        ([['stream', 'PTEST'], ['search', 'FOO']], True),
        ([['stream', '7'], ['topic', 'Test']], False),
        ([['stream', '7'], ['topic', 'Test'], ['search', 'FOO']], True),
        ([['stream', '7'], ['search', 'FOO'], ['topic', 'Test']], True),
        ([['search', 'FOO'], ['stream', '7'], ['topic', 'Test']], True)
    ])
    def test_is_search_narrow(self, model, narrow, is_search_narrow):
        model.narrow = narrow
        assert model.is_search_narrow() == is_search_narrow

    @pytest.mark.parametrize('bad_args', [
        dict(topic='some topic'),
        dict(stream='foo', pm_with='someone'),
        dict(topic='blah', pm_with='someone'),
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
        ([['is', 'starred']], dict(starred=True)),
        ([['is', 'mentioned']], dict(mentioned=True)),
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
        ([], [['is', 'mentioned']], dict(mentioned=True)),
        ([], [['is', 'private']], dict(pms=True)),
        ([], [['pm_with', 'FOOBOO@gmail.com']],
         dict(pm_with='FOOBOO@gmail.com')),
    ])
    def test_set_narrow_not_already_set(self, model, initial_narrow, narrow,
                                        good_args, user_dict):
        model.narrow = initial_narrow
        model.user_dict = user_dict
        assert not model.set_narrow(**good_args)
        assert model.narrow != initial_narrow
        assert model.narrow == narrow
        # FIXME: Add assert for recipients being updated (other tests too?)

    @pytest.mark.parametrize("narrow, index, current_ids", [
        ([], {
            "all_msg_ids": {0, 1}
        }, {0, 1}),
        ([['stream', 'FOO']], {
            "stream_msg_ids_by_stream_id": {
                1: {0, 1}
            }
        }, {0, 1}),
        ([['stream', 'FOO'],
         ['topic', 'BOO']], {
             'topic_msg_ids': {
                 1: {
                     'BOO': {0, 1}
                 }
             }
         }, {0, 1}),
        ([['stream', 'FOO'],  # Covers one empty-set case
         ['topic', 'BOOBOO']], {
             'topic_msg_ids': {
                 1: {
                     'BOO': {0, 1}
                 }
             }
         }, set()),
        ([['is', 'private']], {
            'private_msg_ids': {0, 1}
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {
            'private_msg_ids_by_user_ids': {
                frozenset({1, 2}): {0, 1}
            }
        }, {0, 1}),
        ([['pm_with', 'FOO@zulip.com']], {  # Covers recipient empty-set case
            'private_msg_ids_by_user_ids': {
                frozenset({1, 3}): {0, 1}  # NOTE {1,3} not {1,2}
            }
        }, set()),
        ([['search', 'FOO']], {
            'search': {0, 1}
        }, {0, 1}),
        ([['is', 'starred']], {
            'starred_msg_ids': {0, 1}
        }, {0, 1}),
        ([['stream', 'FOO'], ['search', 'FOO']], {
            "stream_msg_ids_by_stream_id": {
                1: {0, 1, 2}  # NOTE Should not be returned
            },
            'search': {0, 1},
        }, {0, 1}),
        ([['is', 'mentioned']], {
            'mentioned_msg_ids': {0, 1}
        }, {0, 1}),
    ])
    def test_get_message_ids_in_current_narrow(self, mocker, model,
                                               narrow, index, current_ids):
        model.recipients = frozenset({1, 2})
        model.stream_id = 1
        model.narrow = narrow
        model.index = index
        assert current_ids == model.get_message_ids_in_current_narrow()

    @pytest.mark.parametrize("response, expected_index, return_value", [
        ({'result': 'success', 'topics': [{'name': 'Foo'}, {'name': 'Boo'}]},
         {23: ['Foo', 'Boo']}, ''),
        ({'result': 'success', 'topics': []},
         {23: []}, ''),
        ({'result': 'failure', 'msg': 'Some Error', 'topics': []},
         {23: []}, 'Some Error')
    ])
    def test_get_topics_in_streams(self, mocker, response, model, return_value,
                                   expected_index) -> None:
        self.client.get_stream_topics = mocker.Mock(return_value=response)

        result = model.get_topics_in_stream([23])

        self.client.get_stream_topics.assert_called_once_with(23)
        assert model.index['topics'] == expected_index
        assert result == return_value

    @pytest.mark.parametrize("user_key", ['user_id', 'id'])
    @pytest.mark.parametrize("msg_id, existing_reactions, expected_method", [
        (5, [], 'POST'),
        (5, [dict(user='me', emoji_code='1f44d')], 'DELETE'),
        (5, [dict(user='not me', emoji_code='1f44d')], 'POST'),
        (5, [dict(user='me', emoji_code='1f614')], 'POST'),
        (5, [dict(user='not me', emoji_code='1f614')], 'POST'),
    ])
    def test_react_to_message_with_thumbs_up(self, model,
                                             user_key,
                                             msg_id,
                                             existing_reactions,
                                             expected_method):
        full_existing_reactions = [
            dict(er, user={user_key: (model.user_id if er['user'] == 'me'
                                      else model.user_id+1)})  # non-match
            for er in existing_reactions
        ]
        message = dict(
            id=msg_id,
            reactions=full_existing_reactions)
        reaction_spec = dict(
            emoji_name='thumbs_up',
            reaction_type='unicode_emoji',
            emoji_code='1f44d',
            message_id=str(msg_id))

        model.react_to_message(message, 'thumbs_up')

        if expected_method == 'POST':
            model.client.add_reaction.assert_called_once_with(reaction_spec)
            model.client.delete_reaction.assert_not_called()
        elif expected_method == 'DELETE':
            model.client.remove_reaction.assert_called_once_with(reaction_spec)
            model.client.add_reaction.assert_not_called()

    def test_react_to_message_for_not_thumbs_up(self, model):
        with pytest.raises(AssertionError):
            model.react_to_message(dict(), 'x')

    @pytest.mark.parametrize('response, return_value', [
        ({'result': 'success'}, True),
        ({'result': 'some_failure'}, False),
    ])
    def test_send_private_message(self, mocker, model,
                                  response, return_value,
                                  content="hi!",
                                  recipients="notification-bot@zulip.com"):
        self.client.send_message = mocker.Mock(return_value=response)

        result = model.send_private_message(recipients, content)

        req = dict(type='private', to=recipients, content=content)
        self.client.send_message.assert_called_once_with(req)

        assert result == return_value

    @pytest.mark.parametrize('response, return_value', [
        ({'result': 'success'}, True),
        ({'result': 'some_failure'}, False),
    ])
    def test_send_stream_message(self, mocker, model,
                                 response, return_value,
                                 content="hi!",
                                 stream="foo", topic="bar"):
        self.client.send_message = mocker.Mock(return_value=response)

        result = model.send_stream_message(stream, topic, content)

        req = dict(type='stream', to=stream, subject=topic, content=content)
        self.client.send_message.assert_called_once_with(req)

        assert result == return_value

    @pytest.mark.parametrize('response, return_value', [
        ({'result': 'success'}, True),
        ({'result': 'some_failure'}, False),
    ])
    def test_update_private_message(self, mocker, model,
                                    response, return_value,
                                    content="hi!",
                                    msg_id=1):
        self.client.update_message = mocker.Mock(return_value=response)

        result = model.update_private_message(msg_id, content)

        req = dict(message_id=msg_id, content=content)
        self.client.update_message.assert_called_once_with(req)

        assert result == return_value

    @pytest.mark.parametrize('response, return_value', [
        ({'result': 'success'}, True),
        ({'result': 'some_failure'}, False),
    ])
    def test_update_stream_message(self, mocker, model,
                                   response, return_value,
                                   content="hi!",
                                   subject='Hello',
                                   msg_id=1):
        self.client.update_message = mocker.Mock(return_value=response)

        result = model.update_stream_message(subject, msg_id, content)

        req = dict(subject=subject, propagate_mode="change_one",
                   message_id=msg_id, content=content)
        self.client.update_message.assert_called_once_with(req)

        assert result == return_value

    # NOTE: This tests only getting next-unread, not a fixed anchor
    def test_success_get_messages(self, mocker, messages_successful_response,
                                  index_all_messages, initial_data,
                                  num_before=30, num_after=10):
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mocks before calling get_messages
        self.client.get_messages.return_value = messages_successful_response
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
        (model.client.get_messages.
         assert_called_once_with(message_filters=request))
        assert model.index == index_all_messages
        anchor = messages_successful_response['anchor']
        if anchor < 10000000000000000:
            assert model.index['pointer'][str(model.narrow)] == anchor
        assert model.found_newest is True

    def test_get_message_false_first_anchor(
            self, mocker, messages_successful_response, index_all_messages,
            initial_data, num_before=30, num_after=10
            ):
        # TEST FOR get_messages() with first_anchor=False
        # and anchor=0

        # Initialize Model
        self.client.register.return_value = initial_data
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
        self.client.get_messages.return_value = messages_successful_response
        mocker.patch('zulipterminal.model.index_messages',
                     return_value=index_all_messages)

        model = Model(self.controller)
        model.get_messages(num_before=num_before, num_after=num_after,
                           anchor=0)
        self.client.get_messages.return_value = messages_successful_response
        # anchor should have remained the same
        anchor = messages_successful_response['anchor']
        assert model.index['pointer'][str(model.narrow)] == 0

        # TEST `query_range` < no of messages received
        model.found_newest = False  # RESET model.found_newest value
        model.get_messages(num_after=0, num_before=0, anchor=0)
        assert model.found_newest is False

    # FIXME This only tests the case where the get_messages is in __init__
    def test_fail_get_messages(self, mocker, error_response,
                               initial_data, num_before=30, num_after=10):
        # Initialize Model
        self.client.register.return_value = initial_data
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.'
                     '_stream_info_from_subscriptions',
                     return_value=({}, set(), [], []))
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])

        # Setup mock before calling get_messages
        # FIXME This has no influence on the result
        # self.client.do_api_query.return_value = error_response

        with pytest.raises(ServerConnectionFailure):
            model = Model(self.controller)

    @pytest.mark.parametrize('initial_muted_streams, value', [
        ({315}, True),
        ({205, 315}, False),
        (set(), True),
        ({205}, False),
    ], ids=['muting_205', 'unmuting_205', 'first_muted_205',
            'last_unmuted_205'])
    def test_toggle_stream_muted_status(self, mocker, model,
                                        initial_muted_streams, value):
        model.muted_streams = initial_muted_streams
        model.client.update_subscription_settings.return_value = \
            {'result': "success"}
        model.toggle_stream_muted_status(205)
        request = [{
            'stream_id': 205,
            'property': 'is_muted',
            'value': value
        }]
        model.client.update_subscription_settings.\
            assert_called_once_with(request)

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
        model.client.update_message_flags.assert_called_once_with(request)

    def test_mark_message_ids_as_read(self, model, mocker: Any) -> None:
        mock_api_query = mocker.patch('zulipterminal.core.Controller'
                                      '.client.update_message_flags')

        model.mark_message_ids_as_read([1, 2])

        mock_api_query.assert_called_once_with(
            {'flag': 'read', 'messages': [1, 2], 'op': 'add'},
        )

    def test_mark_message_ids_as_read_empty_msg_list(self, model) -> None:
        assert model.mark_message_ids_as_read([]) is None

    def test__update_initial_data(self, model, initial_data):
        assert model.initial_data == initial_data

    def test__update_initial_data_raises_exception(self, mocker, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.get_messages', return_value='')
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

    def test__group_info_from_realm_user_groups(self, model,
                                                user_groups_fixture):
        user_group_names = model._group_info_from_realm_user_groups(
            user_groups_fixture)
        assert model.user_group_by_id == {
            group['id']: {'members': group['members'],
                          'name': group['name'],
                          'description': group['description']}
            for group in user_groups_fixture
            }
        assert user_group_names == ['Group 1', 'Group 2', 'Group 3', 'Group 4']

    def test_get_all_users(self, mocker, initial_data, user_list, user_dict,
                           user_id):
        mocker.patch('zulipterminal.model.Model.get_messages', return_value='')
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

    @pytest.mark.parametrize('muted', powerset([1, 2, 99, 1000]))
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

    def test_append_message_with_Falsey_log(self, mocker, model,
                                            message_fixture):
        model.found_newest = True
        mocker.patch('zulipterminal.model.Model.update_topic_index')
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        model.msg_list = mocker.Mock()
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        model.notify_user = mocker.Mock()
        model.msg_list.log = []
        event = {'message': message_fixture}

        model.append_message(event)

        assert len(model.msg_list.log) == 1  # Added "msg_w" element
        model.notify_user.assert_called_once_with(event['message'])
        (create_msg_box_list.
         assert_called_once_with(model, [message_fixture['id']],
                                 last_message=None))

    def test_append_message_with_valid_log(self, mocker, model,
                                           message_fixture):
        model.found_newest = True
        mocker.patch('zulipterminal.model.Model.update_topic_index')
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        model.msg_list = mocker.Mock()
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        model.notify_user = mocker.Mock()
        model.msg_list.log = [mocker.Mock()]
        event = {'message': message_fixture}

        model.append_message(event)

        assert len(model.msg_list.log) == 2  # Added "msg_w" element
        model.notify_user.assert_called_once_with(event['message'])
        # NOTE: So we expect the first element *was* the last_message parameter
        expected_last_msg = model.msg_list.log[0].original_widget.message
        (create_msg_box_list.
         assert_called_once_with(model, [message_fixture['id']],
                                 last_message=expected_last_msg))

    def test_append_message_event_flags(self, mocker, model, message_fixture):
        model.found_newest = True
        mocker.patch('zulipterminal.model.Model.update_topic_index')
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        model.msg_list = mocker.Mock()
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        model.notify_user = mocker.Mock()
        model.msg_list.log = [mocker.Mock()]
        set_count = mocker.patch('zulipterminal.model.set_count')

        # Test event with flags
        event = {'message': message_fixture, 'flags': ['read', 'mentioned']}
        model.append_message(event)
        # set count not called since 'read' flag present.
        set_count.assert_not_called()

        # Test event without flags
        model.notify_user.assert_called_once_with(event['message'])
        model.msg_list.log = [mocker.Mock()]
        event = {'message': message_fixture, 'flags': []}
        model.append_message(event)
        # set count called since the message is unread.
        set_count.assert_called_once_with([event['message']['id']],
                                          self.controller, 1)

    @pytest.mark.parametrize('response, narrow, recipients, log', [
        ({'type': 'stream', 'stream_id': 1, 'subject': 'FOO',
          'id': 1}, [], frozenset(), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['is', 'private']], frozenset(), ['msg_w']),
        ({'type': 'stream', 'id': 1, 'stream_id': 1, 'subject': 'FOO',
          'display_recipient': 'a'},
         [['stream', 'a']], frozenset(), ['msg_w']),
        ({'type': 'stream', 'id': 1, 'stream_id': 1, 'subject': 'b',
          'display_recipient': 'a'},
         [['stream', 'a'], ['topic', 'b']],
         frozenset(), ['msg_w']),
        ({'type': 'stream', 'id': 1, 'stream_id': 1, 'subject': 'b',
          'display_recipient': 'a'},
         [['stream', 'c'], ['topic', 'b']],
         frozenset(), []),
        ({'type': 'private', 'id': 1,
          'display_recipient': [{'id': 5827}, {'id': 5}]},
         [['pm_with', 'notification-bot@zulip.com']],
         frozenset({5827, 5}), ['msg_w']),
        ({'type': 'private', 'id': 1},
         [['is', 'search']],
         frozenset(), []),
        ({'type': 'private', 'id': 1,
          'display_recipient': [{'id': 5827}, {'id': 3212}]},
         [['pm_with', 'notification-bot@zulip.com']],
         frozenset({5827, 5}), []),
    ], ids=['stream_to_all_messages', 'private_to_all_private',
            'stream_to_stream', 'stream_to_topic',
            'stream_to_different_stream_same_topic',
            'user_pm_x_appears_in_narrow_with_x', 'search',
            'user_pm_x_does_not_appear_in_narrow_without_x'])
    def test_append_message(self, mocker, user_profile, response,
                            narrow, recipients, model, log):
        model.found_newest = True
        mocker.patch('zulipterminal.model.Model.update_topic_index')
        index_msg = mocker.patch('zulipterminal.model.index_messages',
                                 return_value={})
        create_msg_box_list = mocker.patch('zulipterminal.model.'
                                           'create_msg_box_list',
                                           return_value=["msg_w"])
        set_count = mocker.patch('zulipterminal.model.set_count')
        model.msg_list = mocker.Mock()
        model.msg_list.log = []
        model.notify_user = mocker.Mock()
        model.narrow = narrow
        model.recipients = recipients
        model.user_id = user_profile['user_id']
        event = {'message': response}

        model.append_message(event)

        assert model.msg_list.log == log
        set_count.assert_called_once_with([response['id']], self.controller, 1)

        model.found_newest = False
        model.notify_user.assert_called_once_with(response)
        model.append_message(event)
        # LOG REMAINS THE SAME IF UPDATE IS FALSE
        assert model.msg_list.log == log

    @pytest.mark.parametrize('topic_name, topic_order_intial,\
                             topic_order_final', [
        ('TOPIC3', ['TOPIC2', 'TOPIC3', 'TOPIC1'],
                   ['TOPIC3', 'TOPIC2', 'TOPIC1']),
        ('TOPIC1', ['TOPIC1', 'TOPIC2', 'TOPIC3'],
                   ['TOPIC1', 'TOPIC2', 'TOPIC3']),
        ('TOPIC4', ['TOPIC1', 'TOPIC2', 'TOPIC3'],
                   ['TOPIC4', 'TOPIC1', 'TOPIC2', 'TOPIC3']),
        ('TOPIC1', [], ['TOPIC1'])
    ], ids=['reorder_topic3', 'topic1_discussion_continues', 'new_topic4',
            'first_topic_1'])
    def test_update_topic_index(self, topic_name, topic_order_intial,
                                topic_order_final, model):
        model.index = {
            'topics': {
                86: topic_order_intial,
            }
        }
        model.update_topic_index(86, topic_name)
        assert model.index['topics'][86] == topic_order_final

    # TODO: Ideally message_fixture would use standardized ids?
    @pytest.mark.parametrize('user_id, vary_each_msg, \
                              types_when_notify_called', [
        (5140, {}, []),  # message_fixture sender_id is 5140
        (5179, {'flags': ['mentioned']}, ['stream', 'private']),
        (5179, {'flags': ['wildcard_mentioned']}, ['stream', 'private']),
        (5179, {'flags': []}, ['private']),
    ], ids=['self_message', 'mentioned_msg', 'wildcard_mentioned',
            'not_mentioned'])
    def test_notify_users_calling_msg_type(self, mocker, model,
                                           message_fixture,
                                           user_id,
                                           vary_each_msg,
                                           types_when_notify_called):
        message_fixture.update(vary_each_msg)
        model.user_id = user_id
        notify = mocker.patch('zulipterminal.model.notify')
        model.notify_user(message_fixture)
        if message_fixture['type'] in types_when_notify_called:
            who = message_fixture['type']
            if who == 'stream':
                target = 'PTEST -> Test'
            elif who == 'private':
                target = 'you'
                if len(message_fixture['display_recipient']) > 2:
                    target += ', Bar Bar'
            title = 'Test Organization Name:\nFoo Foo (to {})'.format(target)
            # TODO: Test message content too?
            notify.assert_called_once_with(title, mocker.ANY)
        else:
            notify.assert_not_called

    @pytest.mark.parametrize('notify_enabled, is_notify_called', [
        (True, True),
        (False, False),
    ])
    def test_notify_users_enabled(self, mocker, model, message_fixture,
                                  notify_enabled, is_notify_called):
        message_fixture.update({'sender_id': 2, 'flags': ['mentioned']})
        model.controller.notify_enabled = notify_enabled
        model.user_id = 1
        notify = mocker.patch('zulipterminal.model.notify')
        model.notify_user(message_fixture)
        assert notify.called == is_notify_called

    @pytest.mark.parametrize('response, update_call_count, new_index', [
        ({  # Only subject of 1 message is updated.
            'message_id': 1,
            'subject': 'new subject',
            'message_ids': [1],
        }, 1, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'old content',
                    'subject': 'new subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'old subject'
                }},
            'edited_messages': {1}
        }),
        ({  # Subject of 2 messages is updated
            'message_id': 1,
            'subject': 'new subject',
            'message_ids': [1, 2],
        }, 2, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'old content',
                    'subject': 'new subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'new subject'
                }},
            'edited_messages': {1}
        }),
        ({  # Message content is updated
            'message_id': 1,
            'rendered_content': '<p>new content</p>',
        }, 1, {
            'messages': {
                1: {
                    'id': 1,
                    'content': '<p>new content</p>',
                    'subject': 'old subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'old subject'
                }},
            'edited_messages': {1}
        }),
        ({  # Both message content and subject is updated.
            'message_id': 1,
            'rendered_content': '<p>new content</p>',
            'subject': 'new subject',
            'message_ids': [1],
        }, 2, {
            'messages': {
                1: {
                    'id': 1,
                    'content': '<p>new content</p>',
                    'subject': 'new subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'old subject'
                }},
            'edited_messages': {1}
        }),
        ({  # Some new type of update which we don't handle yet.
            'message_id': 1,
            'foo': 'boo',
        }, 0, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'old content',
                    'subject': 'old subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'old subject'
                }},
            'edited_messages': {1}
        }),
        ({  # message_id not present in index.
            'message_id': 3,
            'rendered_content': '<p>new content</p>',
            'subject': 'new subject',
            'message_ids': [3],
        }, 0, {
            'messages': {
                1: {
                    'id': 1,
                    'content': 'old content',
                    'subject': 'old subject'
                },
                2: {
                    'id': 2,
                    'content': 'old content',
                    'subject': 'old subject'
                }},
            'edited_messages': set()
        }),
    ])
    def test_update_message(self, mocker, model, response, new_index,
                            update_call_count):
        model.index = {
            'messages': {
                message_id: {
                    'id': message_id,
                    'content': 'old content',
                    'subject': 'old subject',
                } for message_id in [1, 2]
            },
            'edited_messages': set()
        }
        mocker.patch('zulipterminal.model.Model.update_rendered_view')

        model.update_message(response)

        assert model.index == new_index
        assert model.update_rendered_view.call_count == update_call_count

    @pytest.mark.parametrize('subject, narrow, new_log_len', [
        ('foo', [['stream', 'boo'], ['topic', 'foo']], 2),
        ('foo', [['stream', 'boo'], ['topic', 'not foo']], 1),
        ('foo', [], 2),
    ], ids=[
        'msgbox_updated_in_topic_narrow',
        'msgbox_removed_due_to_topic_narrow_mismatch',
        'msgbox_updated_in_all_messages_narrow',
    ])
    def test_update_rendered_view(self, mocker, model, subject, narrow,
                                  new_log_len, msg_id=1):
        msg_w = mocker.Mock()
        other_msg_w = mocker.Mock()
        msg_w.original_widget.message = {'id': msg_id, 'subject': subject}
        model.narrow = narrow
        other_msg_w.original_widget.message = {'id': 2}
        model.msg_list = mocker.Mock()
        model.msg_list.log = [msg_w, other_msg_w]
        # New msg widget generated after updating index.
        new_msg_w = mocker.Mock()
        cmbl = mocker.patch('zulipterminal.model.create_msg_box_list',
                            return_value=[new_msg_w])

        model.update_rendered_view(msg_id)

        # If there are 2 msgs and first one is updated, next one is updated too
        if new_log_len == 2:
            other_msg_w = new_msg_w
        assert model.msg_list.log == [new_msg_w, other_msg_w][-new_log_len:]
        assert model.controller.update_screen.called

    @pytest.mark.parametrize('subject, narrow, narrow_changed', [
        ('foo', [['stream', 'boo'], ['topic', 'foo']], False),
        ('foo', [['stream', 'boo'], ['topic', 'not foo']], True),
        ('foo', [], False),
    ], ids=[
        'same_topic_narrow',
        'previous_topic_narrow_empty_so_change_narrow',
        'same_all_messages_narrow',
    ])
    def test_update_rendered_view_change_narrow(self, mocker, model, subject,
                                                narrow, narrow_changed,
                                                msg_id=1):
        msg_w = mocker.Mock()
        other_msg_w = mocker.Mock()
        msg_w.original_widget.message = {'id': msg_id, 'subject': subject}
        model.narrow = narrow
        model.msg_list = mocker.Mock()
        model.msg_list.log = [msg_w]
        # New msg widget generated after updating index.
        new_msg_w = mocker.Mock()
        cmbl = mocker.patch('zulipterminal.model.create_msg_box_list',
                            return_value=[new_msg_w])

        model.update_rendered_view(msg_id)

        assert model.controller.narrow_to_topic.called == narrow_changed
        assert model.controller.update_screen.called

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
        event = dict(messages=[1], flag='starred', all=False, operation='add')
        mocker.patch('zulipterminal.model.Model.update_rendered_view')
        set_count = mocker.patch('zulipterminal.model.set_count')

        model.update_message_flag_status(event)

        assert model.index == dict(messages={})
        model.update_rendered_view.assert_not_called()
        set_count.assert_not_called()

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
        set_count = mocker.patch('zulipterminal.model.set_count')
        with pytest.raises(RuntimeError):
            model.update_message_flag_status(event)
        model.update_rendered_view.assert_not_called()
        set_count.assert_not_called()

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
        set_count = mocker.patch('zulipterminal.model.set_count')

        model.update_message_flag_status(event)

        changed_ids = set(indexed_ids) & set(event_message_ids)
        for changed_id in changed_ids:
            assert model.index['messages'][changed_id]['flags'] == flags_after
        (model.update_rendered_view.
         assert_has_calls([mocker.call(changed_id)
                          for changed_id in changed_ids]))

        for unchanged_id in (set(indexed_ids) - set(event_message_ids)):
            assert (model.index['messages'][unchanged_id]['flags'] ==
                    flags_before)

        set_count.assert_not_called()

    @pytest.mark.parametrize('event_message_ids, indexed_ids', [
        ([1], [1]),
        ([1, 2], [1]),
        ([1, 2], [1, 2]),
        ([1], [1, 2]),
        ([], [1, 2]),
        ([1, 2], []),
    ])
    @pytest.mark.parametrize('event_op, flags_before, flags_after', [
        ('add', [], ['read']),
        ('add', ['read'], ['read']),
        ('add', ['starred'], ['starred', 'read']),
        ('add', ['read', 'starred'], ['read', 'starred']),
        ('remove', [], []),
        ('remove', ['read'], ['read']),   # msg cannot be marked 'unread'
        ('remove', ['starred'], ['starred']),
        ('remove', ['starred', 'read'], ['starred', 'read']),
        ('remove', ['read', 'starred'], ['read', 'starred']),
    ])
    def test_update_read_status(self, mocker, model, event_op,
                                event_message_ids, indexed_ids,
                                flags_before, flags_after):
        model.index = dict(messages={msg_id: {'flags': flags_before}
                                     for msg_id in indexed_ids})
        event = {
            'messages': event_message_ids,
            'type': 'update_message_flags',
            'flag': 'read',
            'operation': event_op,
            'all': False,
        }

        mocker.patch('zulipterminal.model.Model.update_rendered_view')
        set_count = mocker.patch('zulipterminal.model.set_count')

        model.update_message_flag_status(event)

        changed_ids = set(indexed_ids) & set(event_message_ids)
        for changed_id in changed_ids:
            assert model.index['messages'][changed_id]['flags'] == flags_after

            if event_op == 'add':
                model.update_rendered_view.assert_has_calls(
                        [mocker.call(changed_id)])
            elif event_op == 'remove':
                model.update_rendered_view.assert_not_called()

        for unchanged_id in (set(indexed_ids) - set(event_message_ids)):
            assert (model.index['messages'][unchanged_id]['flags'] ==
                    flags_before)

        if event_op == 'add':
            set_count.assert_called_once_with(list(changed_ids),
                                              self.controller, -1)
        elif event_op == 'remove':
            set_count.assert_not_called()

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

    @pytest.mark.parametrize('event, final_muted_streams, ', [
        (
            {'property': 'in_home_view',
             'stream_id': 19,
             'value': True},
            {15}
        ),
        (
            {'property': 'in_home_view',
             'stream_id': 30,
             'value': False},
            {15, 19, 30}
        )
    ], ids=[
        'remove_19', 'add_30'
    ])
    def test_update_subscription(self, model, mocker, event, stream_button,
                                 final_muted_streams):
        model.muted_streams = {15, 19}
        model.controller.view.stream_id_to_button = {
            event['stream_id']: stream_button  # stream id is known
        }
        mark_muted = mocker.patch(
            'zulipterminal.ui_tools.buttons.StreamButton.mark_muted')
        mark_unmuted = mocker.patch(
            'zulipterminal.ui_tools.buttons.StreamButton.mark_unmuted')
        model.update_subscription(event)
        assert model.muted_streams == final_muted_streams
        if event['value']:
            mark_unmuted.assert_called_once_with()
        else:
            mark_muted.assert_called_once_with()
        model.controller.update_screen.assert_called_once_with()

    @pytest.mark.parametrize('muted_streams, stream_id, is_muted', [
        ({1},   1, True),
        ({1},   2, False),
        (set(), 1, False),
    ], ids=['muted_stream', 'unmuted_stream', 'unmuted_stream_nostreamsmuted'])
    def test_is_muted_stream(self, muted_streams, stream_id, is_muted,
                             stream_dict, model):
        model.stream_dict = stream_dict
        model.muted_streams = muted_streams
        assert model.is_muted_stream(stream_id) == is_muted

    @pytest.mark.parametrize('topic, is_muted', [
        ((1, 'stream muted & unmuted topic'), True),
        ((2, 'muted topic'), True),
        ((1, 'muted stream muted topic'), True),
        ((2, 'unmuted topic'), False),
    ])
    def test_is_muted_topic(self, topic, is_muted, stream_dict, model):
        model.stream_dict = stream_dict
        model.muted_streams = [1]
        model.muted_topics = [
            ['Stream 2', 'muted topic'],
            ['Stream 1', 'muted stream muted topic'],
        ]
        assert model.is_muted_topic(stream_id=topic[0],
                                    topic=topic[1]) == is_muted
