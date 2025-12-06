import pytest
import responses

from matrix_client.api import MATRIX_V2_API_PATH
from matrix_client.client import MatrixClient
from matrix_client.user import User

HOSTNAME = "http://localhost"


class TestUser:
    cli = MatrixClient(HOSTNAME)
    user_id = "@test:localhost"
    room_id = "!test:localhost"

    @pytest.fixture()
    def user(self):
        return User(self.cli.api, self.user_id)

    @pytest.fixture()
    def room(self):
        return self.cli._mkroom(self.room_id)

    @responses.activate
    def test_get_display_name(self, user, room):
        displayname_url = HOSTNAME + MATRIX_V2_API_PATH + \
            "/profile/{}/displayname".format(user.user_id)
        displayname = 'test'
        room_displayname = 'room_test'

        # No displayname
        assert user.get_display_name(room) == user.user_id
        responses.add(responses.GET, displayname_url, json={})
        assert user.get_display_name() == user.user_id
        assert len(responses.calls) == 1

        # Get global displayname
        responses.replace(responses.GET, displayname_url,
                          json={"displayname": displayname})
        assert user.get_display_name() == displayname
        assert len(responses.calls) == 2

        # Global displayname already present
        assert user.get_display_name() == displayname
        # No new request
        assert len(responses.calls) == 2

        # Per-room displayname
        room.members_displaynames[user.user_id] = room_displayname
        assert user.get_display_name(room) == room_displayname
        # No new request
        assert len(responses.calls) == 2
