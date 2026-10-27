import pytest
import responses
import json
from copy import deepcopy
from matrix_client.client import MatrixClient, Room, User, CACHE
from matrix_client.api import MATRIX_V2_API_PATH
from . import response_examples
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

HOSTNAME = "http://example.com"


def test_create_client():
    MatrixClient("http://example.com")


@responses.activate
def test_create_client_with_token():
    user_id = "@alice:example.com"
    token = "Dp0YKRXwx0iWDhFj7lg3DVjwsWzGcUIgARljgyAip2JD8qd5dSaW" \
            "cxowTKEFetPulfLijAhv8eOmUSScyGcWgZyNMRTBmoJ0RFc0HotPvTBZ" \
            "U98yKRLtat7V43aCpFmK"
    whoami_url = HOSTNAME+MATRIX_V2_API_PATH+"/account/whoami"
    responses.add(
        responses.GET,
        whoami_url,
        body='{"user_id": "%s"}' % user_id
    )
    sync_response = deepcopy(response_examples.example_sync)
    response_body = json.dumps(sync_response)
    sync_url = HOSTNAME + MATRIX_V2_API_PATH + "/sync"
    responses.add(responses.GET, sync_url, body=response_body)
    MatrixClient(HOSTNAME, token=token)
    req = responses.calls[0].request
    assert req.method == 'GET'
    assert whoami_url in req.url


def test_sync_token():
    client = MatrixClient("http://example.com")
    assert client.get_sync_token() is None
    client.set_sync_token("FAKE_TOKEN")
    assert client.get_sync_token() == "FAKE_TOKEN"


def test__mkroom():
    client = MatrixClient("http://example.com")

    roomId = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    goodRoom = client._mkroom(roomId)

    assert isinstance(goodRoom, Room)
    assert goodRoom.room_id is roomId

    with pytest.raises(ValueError):
        client._mkroom("BAD_ROOM:matrix.org")
        client._mkroom("!BAD_ROOMmatrix.org")
        client._mkroom("!BAD_ROOM::matrix.org")


def test_get_rooms():
    client = MatrixClient("http://example.com")
    rooms = client.get_rooms()
    assert isinstance(rooms, dict)
    assert len(rooms) == 0

    client = MatrixClient("http://example.com")

    client._mkroom("!abc:matrix.org")
    client._mkroom("!def:matrix.org")
    client._mkroom("!ghi:matrix.org")

    rooms = client.get_rooms()
    assert isinstance(rooms, dict)
    assert len(rooms) == 3


def test_bad_state_events():
    client = MatrixClient("http://example.com")
    room = client._mkroom("!abc:matrix.org")

    ev = {
        "tomato": False
    }

    room._process_state_event(ev)


def test_state_event():
    client = MatrixClient("http://example.com")
    room = client._mkroom("!abc:matrix.org")

    room.name = False
    room.topic = False
    room.aliases = False

    ev = {
        "type": "m.room.name",
        "content": {},
        "event_id": "$10000000000000AAAAA:matrix.org"
    }

    room._process_state_event(ev)
    assert room.name is None

    ev["content"]["name"] = "TestName"
    room._process_state_event(ev)
    assert room.name == "TestName"

    ev["type"] = "m.room.topic"
    room._process_state_event(ev)
    assert room.topic is None

    ev["content"]["topic"] = "TestTopic"
    room._process_state_event(ev)
    assert room.topic == "TestTopic"

    ev["type"] = "m.room.aliases"
    room._process_state_event(ev)
    assert room.aliases is None

    aliases = ["#foo:matrix.org", "#bar:matrix.org"]
    ev["content"]["aliases"] = aliases
    room._process_state_event(ev)
    assert room.aliases is aliases

    # test member join event
    ev["type"] = "m.room.member"
    ev["content"] = {'membership': 'join', 'displayname': 'stereo'}
    ev["state_key"] = "@stereo:xxx.org"
    room._process_state_event(ev)
    assert len(room._members) == 1
    assert room._members["@stereo:xxx.org"]
    # test member leave event
    ev["content"]['membership'] = 'leave'
    room._process_state_event(ev)
    assert len(room._members) == 0

    # test join_rules
    room.invite_only = False
    ev["type"] = "m.room.join_rules"
    ev["content"] = {"join_rule": "invite"}
    room._process_state_event(ev)
    assert room.invite_only

    # test guest_access
    room.guest_access = False
    ev["type"] = "m.room.guest_access"
    ev["content"] = {"guest_access": "can_join"}
    room._process_state_event(ev)
    assert room.guest_access

    # test malformed event (check does not throw exception)
    room.guest_access = False
    ev["type"] = "m.room.guest_access"
    ev["content"] = {}
    room._process_state_event(ev)
    assert not room.guest_access

    # test encryption
    room.encrypted = False
    ev["type"] = "m.room.encryption"
    ev["content"] = {"algorithm": "m.megolm.v1.aes-sha2"}
    room._process_state_event(ev)
    assert room.encrypted
    # encrypted flag must not be cleared on configuration change
    ev["content"] = {"algorithm": None}
    room._process_state_event(ev)
    assert room.encrypted


def test_get_user():
    client = MatrixClient("http://example.com")

    assert isinstance(client.get_user("@foobar:matrix.org"), User)

    with pytest.raises(ValueError):
        client.get_user("badfoobar:matrix.org")
        client.get_user("@badfoobarmatrix.org")
        client.get_user("@badfoobar:::matrix.org")


def test_get_download_url():
    client = MatrixClient("http://example.com")
    real_url = "http://example.com/_matrix/media/r0/download/foobar"
    assert client.api.get_download_url("mxc://foobar") == real_url

    with pytest.raises(ValueError):
        client.api.get_download_url("http://foobar")


def test_remove_listener():
    def dummy_listener():
        pass

    client = MatrixClient("http://example.com")
    handler = client.add_listener(dummy_listener)

    found_listener = False
    for listener in client.listeners:
        if listener["uid"] == handler:
            found_listener = True
            break

    assert found_listener, "listener was not added properly"

    client.remove_listener(handler)
    found_listener = False
    for listener in client.listeners:
        if listener["uid"] == handler:
            found_listener = True
            break

    assert not found_listener, "listener was not removed properly"


class TestClientRegister:
    cli = MatrixClient(HOSTNAME)

    @responses.activate
    def test_register_as_guest(self):
        cli = self.cli

        def _sync(self):
            self._sync_called = True
        cli.__dict__[_sync.__name__] = _sync.__get__(cli, cli.__class__)
        register_guest_url = HOSTNAME + MATRIX_V2_API_PATH + "/register"
        response_body = json.dumps({
            'access_token': 'EXAMPLE_ACCESS_TOKEN',
            'device_id': 'guest_device',
            'home_server': 'example.com',
            'user_id': '@455:example.com'
        })
        responses.add(responses.POST, register_guest_url, body=response_body)
        cli.register_as_guest()
        assert cli.token == cli.api.token == 'EXAMPLE_ACCESS_TOKEN'
        assert cli.hs == 'example.com'
        assert cli.user_id == '@455:example.com'
        assert cli._sync_called


def test_get_rooms_display_name():

    def add_members(api, room, num):
        for i in range(num):
            room._add_member('@frho%s:matrix.org' % i, 'ho%s' % i)

    client = MatrixClient("http://example.com")
    client.user_id = "@frho0:matrix.org"
    room1 = client._mkroom("!abc:matrix.org")
    add_members(client.api, room1, 1)
    room2 = client._mkroom("!def:matrix.org")
    add_members(client.api, room2, 2)
    room3 = client._mkroom("!ghi:matrix.org")
    add_members(client.api, room3, 3)
    room4 = client._mkroom("!rfi:matrix.org")
    add_members(client.api, room4, 30)

    rooms = client.get_rooms()
    assert len(rooms) == 4
    assert room1.display_name == "Empty room"
    assert room2.display_name == "ho1"
    assert room3.display_name == "ho1 and ho2"
    assert room4.display_name == "ho1 and 28 others"


@responses.activate
def test_presence_listener():
    client = MatrixClient("http://example.com")
    accumulator = []

    def dummy_callback(event):
        accumulator.append(event)
    presence_events = [
        {
            "content": {
                "avatar_url": "mxc://localhost:wefuiwegh8742w",
                "currently_active": False,
                "last_active_ago": 2478593,
                "presence": "online",
                "user_id": "@example:localhost"
            },
            "event_id": "$WLGTSEFSEF:localhost",
            "type": "m.presence"
        },
        {
            "content": {
                "avatar_url": "mxc://localhost:weaugwe742w",
                "currently_active": True,
                "last_active_ago": 1478593,
                "presence": "online",
                "user_id": "@example2:localhost"
            },
            "event_id": "$CIGTXEFREF:localhost",
            "type": "m.presence"
        },
        {
            "content": {
                "avatar_url": "mxc://localhost:wefudweg13742w",
                "currently_active": False,
                "last_active_ago": 24795,
                "presence": "offline",
                "user_id": "@example3:localhost"
            },
            "event_id": "$ZEGASEDSEF:localhost",
            "type": "m.presence"
        },
    ]
    sync_response = deepcopy(response_examples.example_sync)
    sync_response["presence"]["events"] = presence_events
    response_body = json.dumps(sync_response)
    sync_url = HOSTNAME + MATRIX_V2_API_PATH + "/sync"

    responses.add(responses.GET, sync_url, body=response_body)
    callback_uid = client.add_presence_listener(dummy_callback)
    client._sync()
    assert accumulator == presence_events

    responses.add(responses.GET, sync_url, body=response_body)
    client.remove_presence_listener(callback_uid)
    accumulator = []
    client._sync()
    assert accumulator == []


@responses.activate
def test_changing_user_power_levels():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    PL_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.power_levels"

    # Code should first get current power_levels and then modify them
    responses.add(responses.GET, PL_state_path,
                  json=response_examples.example_pl_event["content"])
    responses.add(responses.PUT, PL_state_path,
                  json=response_examples.example_event_response)
    # Removes user from user and adds user to to users list
    assert room.modify_user_power_levels(users={"@example:localhost": None,
                                                "@foobar:example.com": 49})

    expected_request = deepcopy(response_examples.example_pl_event["content"])
    del expected_request["users"]["@example:localhost"]
    expected_request["users"]["@foobar:example.com"] = 49

    assert json.loads(responses.calls[1].request.body) == expected_request


@responses.activate
def test_changing_default_power_level():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    PL_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.power_levels"

    # Code should first get current power_levels and then modify them
    responses.add(responses.GET, PL_state_path,
                  json=response_examples.example_pl_event["content"])
    responses.add(responses.PUT, PL_state_path,
                  json=response_examples.example_event_response)
    assert room.modify_user_power_levels(users_default=23)

    expected_request = deepcopy(response_examples.example_pl_event["content"])
    expected_request["users_default"] = 23

    assert json.loads(responses.calls[1].request.body) == expected_request


@responses.activate
def test_changing_event_required_power_levels():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    PL_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.power_levels"

    # Code should first get current power_levels and then modify them
    responses.add(responses.GET, PL_state_path,
                  json=response_examples.example_pl_event["content"])
    responses.add(responses.PUT, PL_state_path,
                  json=response_examples.example_event_response)
    # Remove event from events and adds new controlled event
    assert room.modify_required_power_levels(events={"m.room.name": None,
                                                     "example.event": 51})

    expected_request = deepcopy(response_examples.example_pl_event["content"])
    del expected_request["events"]["m.room.name"]
    expected_request["events"]["example.event"] = 51

    assert json.loads(responses.calls[1].request.body) == expected_request


@responses.activate
def test_changing_other_required_power_levels():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    PL_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.power_levels"

    # Code should first get current power_levels and then modify them
    responses.add(responses.GET, PL_state_path,
                  json=response_examples.example_pl_event["content"])
    responses.add(responses.PUT, PL_state_path,
                  json=response_examples.example_event_response)
    # Remove event from events and adds new controlled event
    assert room.modify_required_power_levels(kick=53, redact=2,
                                             state_default=None)

    expected_request = deepcopy(response_examples.example_pl_event["content"])
    expected_request["kick"] = 53
    expected_request["redact"] = 2
    del expected_request["state_default"]

    assert json.loads(responses.calls[1].request.body) == expected_request


@responses.activate
def test_cache():
    m_none = MatrixClient("http://example.com", cache_level=CACHE.NONE)
    m_some = MatrixClient("http://example.com", cache_level=CACHE.SOME)
    m_all = MatrixClient("http://example.com", cache_level=CACHE.ALL)
    sync_url = HOSTNAME + MATRIX_V2_API_PATH + "/sync"
    room_id = "!726s6s6q:example.com"
    room_name = "The FooBar"
    sync_response = deepcopy(response_examples.example_sync)

    with pytest.raises(ValueError):
        MatrixClient("http://example.com", cache_level=1)
        MatrixClient("http://example.com", cache_level=5)
        MatrixClient("http://example.com", cache_level=0.5)
        MatrixClient("http://example.com", cache_level=-5)
        MatrixClient("http://example.com", cache_level="foo")
        MatrixClient("http://example.com", cache_level=0.0)

    sync_response["rooms"]["join"][room_id]["state"]["events"].append(
        {
            "sender": "@alice:example.com",
            "type": "m.room.name",
            "state_key": "",
            "content": {"name": room_name},
        }
    )

    responses.add(responses.GET, sync_url, json.dumps(sync_response))
    m_none._sync()
    responses.add(responses.GET, sync_url, json.dumps(sync_response))
    m_some._sync()
    responses.add(responses.GET, sync_url, json.dumps(sync_response))
    m_all._sync()

    assert m_none.rooms[room_id].name is None
    assert m_some.rooms[room_id].name == room_name
    assert m_all.rooms[room_id].name == room_name

    assert m_none.rooms[room_id]._members == m_some.rooms[room_id]._members == {}
    assert len(m_all.rooms[room_id]._members) == 2
    assert m_all.rooms[room_id]._members["@alice:example.com"]


@responses.activate
def test_room_join_rules():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    assert room.invite_only is None
    join_rules_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.join_rules"

    responses.add(responses.PUT, join_rules_state_path,
                  json=response_examples.example_event_response)

    assert room.set_invite_only(True)
    assert room.invite_only


@responses.activate
def test_room_guest_access():
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    assert room.guest_access is None
    guest_access_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.guest_access"

    responses.add(responses.PUT, guest_access_state_path,
                  json=response_examples.example_event_response)

    assert room.set_guest_access(True)
    assert room.guest_access


@responses.activate
def test_enable_encryption():
    pytest.importorskip('olm')
    client = MatrixClient(HOSTNAME, encryption=True)

    login_path = HOSTNAME + MATRIX_V2_API_PATH + "/login"
    responses.add(responses.POST, login_path,
                  json=response_examples.example_success_login_response)

    upload_path = HOSTNAME + MATRIX_V2_API_PATH + '/keys/upload'
    responses.add(responses.POST, upload_path, body='{"one_time_key_counts": {}}')

    client.login("@example:localhost", "password", sync=False)

    assert client.olm_device


@responses.activate
def test_enable_encryption_in_room():
    pytest.importorskip('olm')
    client = MatrixClient(HOSTNAME)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"
    room = client._mkroom(room_id)
    assert not room.encrypted
    encryption_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.encryption"

    responses.add(responses.PUT, encryption_state_path,
                  json=response_examples.example_event_response)

    assert room.enable_encryption()
    assert room.encrypted


@responses.activate
def test_detect_encryption_state():
    pytest.importorskip('olm')
    client = MatrixClient(HOSTNAME, encryption=True)
    room_id = "!UcYsUzyxTGDxLBEvLz:matrix.org"

    encryption_state_path = HOSTNAME + MATRIX_V2_API_PATH + \
        "/rooms/" + quote(room_id) + "/state/m.room.encryption"
    responses.add(responses.GET, encryption_state_path,
                  json={"algorithm": "m.megolm.v1.aes-sha2"})
    responses.add(responses.GET, encryption_state_path,
                  json={}, status=404)

    room = client._mkroom(room_id)
    assert room.encrypted

    room = client._mkroom(room_id)
    assert not room.encrypted


@responses.activate
def test_one_time_keys_sync():
    pytest.importorskip('olm')
    client = MatrixClient(HOSTNAME, encryption=True)
    sync_url = HOSTNAME + MATRIX_V2_API_PATH + "/sync"
    sync_response = deepcopy(response_examples.example_sync)
    payload = {'dummy': 1}
    sync_response["device_one_time_keys_count"] = payload
    sync_response['rooms']['join'] = {}

    class DummyDevice:

        def update_one_time_key_counts(self, payload):
            self.payload = payload

    device = DummyDevice()
    client.olm_device = device

    responses.add(responses.GET, sync_url, json=sync_response)

    client._sync()
    assert device.payload == payload
