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
        mocker.patch('zulipterminal.model.Model.fetch_initial_data',
                     return_value=initial_data)
        mocker.patch('zulipterminal.model.Model.get_all_users',
                     return_value=[])
        mocker.patch('zulipterminal.model.Model.get_subscribed_streams',
                     return_value=[])
        # NOTE: PATCH WHERE USED NOT WHERE DEFINED
        self.classify_unread_counts = mocker.patch(
            'zulipterminal.model.classify_unread_counts',
            return_value=[])
        self.client.get_profile.return_value = user_profile
        return Model(self.controller)

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
        model.fetch_initial_data.assert_called_once_with()
        assert model.initial_data == initial_data
        model.client.get_profile.assert_called_once_with()
        assert model.user_id == user_profile['user_id']
        model.get_all_users.assert_called_once_with()
        assert model.users == []
        model.get_subscribed_streams.assert_called_once_with()
        assert model.streams == []
        self.classify_unread_counts.assert_called_once_with(
            initial_data['unread_msgs']
        )
        assert model.unread_counts == []

    def test_success_get_messages(self, mocker, messages_successful_response,
                                  index_all_messages, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.fetch_initial_data',
                     return_value=initial_data)
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
        mocker.patch('zulipterminal.model.Model.fetch_initial_data',
                     return_value=initial_data)
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
        mocker.patch('zulipterminal.model.Model.fetch_initial_data',
                     return_value=initial_data)
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

    def test_fetch_initial_data(self, mocker, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.get_messages')
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
        assert model.initial_data == initial_data

    def test_fetch_initial_data_raises_exception(self, mocker, initial_data):
        # Initialize Model
        mocker.patch('zulipterminal.model.Model.get_messages')
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
            model.fetch_initial_data()
