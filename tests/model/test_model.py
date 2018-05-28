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
        mocker.patch('zulipterminal.core.Controller.client.get_profile',
                     return_value=user_profile)
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
