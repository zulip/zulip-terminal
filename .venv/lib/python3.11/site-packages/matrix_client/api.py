# -*- coding: utf-8 -*-
# Copyright 2015 OpenMarket Ltd
# Copyright 2017, 2018 Adam Beckmeyer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import warnings
from requests import Session, RequestException
from time import time, sleep
from .__init__ import __version__
from .errors import MatrixError, MatrixRequestError, MatrixHttpLibError
from urllib3.util import parse_url
from urllib3.exceptions import LocationParseError

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

MATRIX_V2_API_PATH = "/_matrix/client/r0"


class MatrixHttpApi(object):
    """Contains all raw Matrix HTTP Client-Server API calls.

    For room and sync handling, consider using MatrixClient.

    Args:
        base_url (str): The home server URL e.g. 'http://localhost:8008'
        token (str): Optional. The client's access token.
        identity (str): Optional. The mxid to act as (For application services only).
        default_429_wait_ms (int): Optional. Time in millseconds to wait before retrying
                                             a request when server returns a HTTP 429
                                             response without a 'retry_after_ms' key.
        use_authorization_header (bool): Optional. Use Authorization header instead
                `                        of access_token query parameter.

    Examples:
        Create a client and send a message::

            matrix = MatrixHttpApi("https://matrix.org", token="foobar")
            response = matrix.sync()
            response = matrix.send_message("!roomid:matrix.org", "Hello!")
    """

    def __init__(
            self, base_url, token=None, identity=None,
            default_429_wait_ms=5000,
            use_authorization_header=True
    ):
        try:
            scheme, auth, host, port, path, query, fragment = parse_url(base_url)
        except LocationParseError:
            raise MatrixError("Invalid homeserver url %s" % base_url)
        if not scheme:
            raise MatrixError("No scheme in homeserver url %s" % base_url)
        self._base_url = base_url

        self.token = token
        self.identity = identity
        self.txn_id = 0
        self.validate_cert = True
        self.session = Session()
        self.default_429_wait_ms = default_429_wait_ms
        self.use_authorization_header = use_authorization_header

    def initial_sync(self, limit=1):
        """
        .. warning::

            Deprecated. Use sync instead.

        Perform /initialSync.

        Args:
            limit (int): The limit= param to provide.
        """
        warnings.warn("initial_sync is deprecated. Use sync instead.", DeprecationWarning)
        return self._send("GET", "/initialSync", query_params={"limit": limit})

    def sync(self, since=None, timeout_ms=30000, filter=None,
             full_state=None, set_presence=None):
        """ Perform a sync request.

        Args:
            since (str): Optional. A token which specifies where to continue a sync from.
            timeout_ms (int): Optional. The time in milliseconds to wait.
            filter (int|str): Either a Filter ID or a JSON string.
            full_state (bool): Return the full state for every room the user has joined
                Defaults to false.
            set_presence (str): Should the client be marked as "online" or" offline"
        """

        request = {
            # non-integer timeouts appear to cause issues
            "timeout": int(timeout_ms)
        }

        if since:
            request["since"] = since

        if filter:
            request["filter"] = filter

        if full_state:
            request["full_state"] = json.dumps(full_state)

        if set_presence:
            request["set_presence"] = set_presence

        return self._send("GET", "/sync", query_params=request,
                          api_path=MATRIX_V2_API_PATH)

    def validate_certificate(self, valid):
        self.validate_cert = valid

    def register(self, auth_body=None, kind="user", bind_email=None,
                 username=None, password=None, device_id=None,
                 initial_device_display_name=None, inhibit_login=None):
        """Performs /register.

        Args:
            auth_body (dict): Authentication Params.
            kind (str): Specify kind of account to register. Can be 'guest' or 'user'.
            bind_email (bool): Whether to use email in registration and authentication.
            username (str): The localpart of a Matrix ID.
            password (str): The desired password of the account.
            device_id (str): ID of the client device.
            initial_device_display_name (str): Display name to be assigned.
            inhibit_login (bool): Whether to login after registration. Defaults to false.
        """
        content = {}
        content["kind"] = kind
        if auth_body:
            content["auth"] = auth_body
        if username:
            content["username"] = username
        if password:
            content["password"] = password
        if device_id:
            content["device_id"] = device_id
        if initial_device_display_name:
            content["initial_device_display_name"] = \
                    initial_device_display_name
        if bind_email:
            content["bind_email"] = bind_email
        if inhibit_login:
            content["inhibit_login"] = inhibit_login
        return self._send(
            "POST",
            "/register",
            content=content,
            query_params={'kind': kind}
        )

    def login(self, login_type, **kwargs):
        """Perform /login.

        Args:
            login_type (str): The value for the 'type' key.
            **kwargs: Additional key/values to add to the JSON submitted.
        """
        content = {
            "type": login_type
        }
        for key in kwargs:
            if kwargs[key]:
                content[key] = kwargs[key]

        return self._send("POST", "/login", content)

    def logout(self):
        """Perform /logout.
        """
        return self._send("POST", "/logout")

    def logout_all(self):
        """Perform /logout/all."""
        return self._send("POST", "/logout/all")

    def create_room(
                self,
                alias=None,
                name=None,
                is_public=False,
                invitees=None,
                federate=None
            ):
        """Perform /createRoom.

        Args:
            alias (str): Optional. The room alias name to set for this room.
            name (str): Optional. Name for new room.
            is_public (bool): Optional. The public/private visibility.
            invitees (list<str>): Optional. The list of user IDs to invite.
            federate (bool): Optional. Сan a room be federated.
                Default to True.
        """
        content = {
            "visibility": "public" if is_public else "private"
        }
        if alias:
            content["room_alias_name"] = alias
        if invitees:
            content["invite"] = invitees
        if name:
            content["name"] = name
        if federate is not None:
            content["creation_content"] = {'m.federate': federate}
        return self._send("POST", "/createRoom", content)

    def join_room(self, room_id_or_alias):
        """Performs /join/$room_id

        Args:
            room_id_or_alias (str): The room ID or room alias to join.
        """
        if not room_id_or_alias:
            raise MatrixError("No alias or room ID to join.")

        path = "/join/%s" % quote(room_id_or_alias)

        return self._send("POST", path)

    def event_stream(self, from_token, timeout=30000):
        """ Deprecated. Use sync instead.
        Performs /events

        Args:
            from_token (str): The 'from' query parameter.
            timeout (int): Optional. The 'timeout' query parameter.
        """
        warnings.warn("event_stream is deprecated. Use sync instead.",
                      DeprecationWarning)
        path = "/events"
        return self._send(
            "GET", path, query_params={
                "timeout": timeout,
                "from": from_token
            }
        )

    def send_state_event(self, room_id, event_type, content, state_key="",
                         timestamp=None):
        """Perform PUT /rooms/$room_id/state/$event_type

        Args:
            room_id(str): The room ID to send the state event in.
            event_type(str): The state event type to send.
            content(dict): The JSON content to send.
            state_key(str): Optional. The state key for the event.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        path = "/rooms/%s/state/%s" % (
            quote(room_id), quote(event_type),
        )
        if state_key:
            path += "/%s" % (quote(state_key))
        params = {}
        if timestamp:
            params["ts"] = timestamp
        return self._send("PUT", path, content, query_params=params)

    def get_state_event(self, room_id, event_type):
        """Perform GET /rooms/$room_id/state/$event_type

        Args:
            room_id(str): The room ID.
            event_type (str): The type of the event.

        Raises:
            MatrixRequestError(code=404) if the state event is not found.
        """
        return self._send("GET", "/rooms/{}/state/{}".format(quote(room_id), event_type))

    def send_message_event(self, room_id, event_type, content, txn_id=None,
                           timestamp=None):
        """Perform PUT /rooms/$room_id/send/$event_type

        Args:
            room_id (str): The room ID to send the message event in.
            event_type (str): The event type to send.
            content (dict): The JSON content to send.
            txn_id (int): Optional. The transaction ID to use.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        if not txn_id:
            txn_id = self._make_txn_id()

        path = "/rooms/%s/send/%s/%s" % (
            quote(room_id), quote(event_type), quote(str(txn_id)),
        )
        params = {}
        if timestamp:
            params["ts"] = timestamp
        return self._send("PUT", path, content, query_params=params)

    def redact_event(self, room_id, event_id, reason=None, txn_id=None, timestamp=None):
        """Perform PUT /rooms/$room_id/redact/$event_id/$txn_id/

        Args:
            room_id(str): The room ID to redact the message event in.
            event_id(str): The event id to redact.
            reason (str): Optional. The reason the message was redacted.
            txn_id(int): Optional. The transaction ID to use.
            timestamp(int): Optional. Set origin_server_ts (For application services only)
        """
        if not txn_id:
            txn_id = self._make_txn_id()

        path = '/rooms/%s/redact/%s/%s' % (
            room_id, event_id, txn_id
        )
        content = {}
        if reason:
            content['reason'] = reason
        params = {}
        if timestamp:
            params["ts"] = timestamp
        return self._send("PUT", path, content, query_params=params)

    # content_type can be a image,audio or video
    # extra information should be supplied, see
    # https://matrix.org/docs/spec/r0.0.1/client_server.html
    def send_content(self, room_id, item_url, item_name, msg_type,
                     extra_information=None, timestamp=None):
        if extra_information is None:
            extra_information = {}

        content_pack = {
            "url": item_url,
            "msgtype": msg_type,
            "body": item_name,
            "info": extra_information
        }
        return self.send_message_event(room_id, "m.room.message", content_pack,
                                       timestamp=timestamp)

    # http://matrix.org/docs/spec/client_server/r0.2.0.html#m-location
    def send_location(self, room_id, geo_uri, name, thumb_url=None, thumb_info=None,
                      timestamp=None):
        """Send m.location message event

        Args:
            room_id (str): The room ID to send the event in.
            geo_uri (str): The geo uri representing the location.
            name (str): Description for the location.
            thumb_url (str): URL to the thumbnail of the location.
            thumb_info (dict): Metadata about the thumbnail, type ImageInfo.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        content_pack = {
            "geo_uri": geo_uri,
            "msgtype": "m.location",
            "body": name,
        }
        if thumb_url:
            content_pack["thumbnail_url"] = thumb_url
        if thumb_info:
            content_pack["thumbnail_info"] = thumb_info

        return self.send_message_event(room_id, "m.room.message", content_pack,
                                       timestamp=timestamp)

    def send_message(self, room_id, text_content, msgtype="m.text", timestamp=None):
        """Perform PUT /rooms/$room_id/send/m.room.message

        Args:
            room_id (str): The room ID to send the event in.
            text_content (str): The m.text body to send.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        return self.send_message_event(
            room_id, "m.room.message",
            self.get_text_body(text_content, msgtype),
            timestamp=timestamp
        )

    def send_emote(self, room_id, text_content, timestamp=None):
        """Perform PUT /rooms/$room_id/send/m.room.message with m.emote msgtype

        Args:
            room_id (str): The room ID to send the event in.
            text_content (str): The m.emote body to send.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        return self.send_message_event(
            room_id, "m.room.message",
            self.get_emote_body(text_content),
            timestamp=timestamp
        )

    def send_notice(self, room_id, text_content, timestamp=None):
        """Perform PUT /rooms/$room_id/send/m.room.message with m.notice msgtype

        Args:
            room_id (str): The room ID to send the event in.
            text_content (str): The m.notice body to send.
            timestamp (int): Set origin_server_ts (For application services only)
        """
        body = {
            "msgtype": "m.notice",
            "body": text_content
        }
        return self.send_message_event(room_id, "m.room.message", body,
                                       timestamp=timestamp)

    def get_room_messages(self, room_id, token, direction, limit=10, to=None):
        """Perform GET /rooms/{roomId}/messages.

        Args:
            room_id (str): The room's id.
            token (str): The token to start returning events from.
            direction (str):  The direction to return events from. One of: ["b", "f"].
            limit (int): The maximum number of events to return.
            to (str): The token to stop returning events at.
        """
        query = {
            "roomId": room_id,
            "from": token,
            "dir": direction,
            "limit": limit,
        }

        if to:
            query["to"] = to

        return self._send("GET", "/rooms/{}/messages".format(quote(room_id)),
                          query_params=query, api_path="/_matrix/client/r0")

    def get_room_name(self, room_id):
        """Perform GET /rooms/$room_id/state/m.room.name
        Args:
            room_id(str): The room ID
        """
        return self.get_state_event(room_id, "m.room.name")

    def set_room_name(self, room_id, name, timestamp=None):
        """Perform PUT /rooms/$room_id/state/m.room.name
        Args:
            room_id (str): The room ID
            name (str): The new room name
            timestamp (int): Set origin_server_ts (For application services only)
        """
        body = {
            "name": name
        }
        return self.send_state_event(room_id, "m.room.name", body, timestamp=timestamp)

    def get_room_topic(self, room_id):
        """Perform GET /rooms/$room_id/state/m.room.topic
        Args:
            room_id (str): The room ID
        """
        return self.get_state_event(room_id, "m.room.topic")

    def set_room_topic(self, room_id, topic, timestamp=None):
        """Perform PUT /rooms/$room_id/state/m.room.topic
        Args:
            room_id (str): The room ID
            topic (str): The new room topic
            timestamp (int): Set origin_server_ts (For application services only)
        """
        body = {
            "topic": topic
        }
        return self.send_state_event(room_id, "m.room.topic", body, timestamp=timestamp)

    def get_power_levels(self, room_id):
        """Perform GET /rooms/$room_id/state/m.room.power_levels

        Args:
            room_id(str): The room ID
        """
        return self.get_state_event(room_id, "m.room.power_levels")

    def set_power_levels(self, room_id, content):
        """Perform PUT /rooms/$room_id/state/m.room.power_levels

        Note that any power levels which are not explicitly specified
        in the content arg are reset to default values.

        Args:
            room_id (str): The room ID
            content (dict): The JSON content to send. See example content below.

        Example::

            api = MatrixHttpApi("http://example.com", token="foobar")
            api.set_power_levels("!exampleroom:example.com",
                {
                    "ban": 50, # defaults to 50 if unspecified
                    "events": {
                        "m.room.name": 100, # must have PL 100 to change room name
                        "m.room.power_levels": 100 # must have PL 100 to change PLs
                    },
                    "events_default": 0, # defaults to 0
                    "invite": 50, # defaults to 50
                    "kick": 50, # defaults to 50
                    "redact": 50, # defaults to 50
                    "state_default": 50, # defaults to 50 if m.room.power_levels exists
                    "users": {
                        "@someguy:example.com": 100 # defaults to 0
                    },
                    "users_default": 0 # defaults to 0
                }
            )
        """
        # Synapse returns M_UNKNOWN if body['events'] is omitted,
        #  as of 2016-10-31
        if "events" not in content:
            content["events"] = {}

        return self.send_state_event(room_id, "m.room.power_levels", content)

    def leave_room(self, room_id):
        """Perform POST /rooms/$room_id/leave

        Args:
            room_id (str): The room ID
        """
        return self._send("POST", "/rooms/" + room_id + "/leave", {})

    def forget_room(self, room_id):
        """Perform POST /rooms/$room_id/forget

        Args:
            room_id(str): The room ID
        """
        return self._send("POST", "/rooms/" + room_id + "/forget", content={})

    def invite_user(self, room_id, user_id):
        """Perform POST /rooms/$room_id/invite

        Args:
            room_id (str): The room ID
            user_id (str): The user ID of the invitee
        """
        body = {
            "user_id": user_id
        }
        return self._send("POST", "/rooms/" + room_id + "/invite", body)

    def kick_user(self, room_id, user_id, reason=""):
        """Calls set_membership with membership="leave" for the user_id provided
        """
        self.set_membership(room_id, user_id, "leave", reason)

    def get_membership(self, room_id, user_id):
        """Perform GET /rooms/$room_id/state/m.room.member/$user_id

        Args:
            room_id (str): The room ID
            user_id (str): The user ID
        """
        return self._send(
            "GET",
            "/rooms/%s/state/m.room.member/%s" % (room_id, user_id)
        )

    def set_membership(self, room_id, user_id, membership, reason="", profile=None,
                       timestamp=None):
        """Perform PUT /rooms/$room_id/state/m.room.member/$user_id

        Args:
            room_id (str): The room ID
            user_id (str): The user ID
            membership (str): New membership value
            reason (str): The reason
            timestamp (int): Set origin_server_ts (For application services only)
        """
        if profile is None:
            profile = {}
        body = {
            "membership": membership,
            "reason": reason
        }
        if 'displayname' in profile:
            body["displayname"] = profile["displayname"]
        if 'avatar_url' in profile:
            body["avatar_url"] = profile["avatar_url"]

        return self.send_state_event(room_id, "m.room.member", body, state_key=user_id,
                                     timestamp=timestamp)

    def ban_user(self, room_id, user_id, reason=""):
        """Perform POST /rooms/$room_id/ban

        Args:
            room_id (str): The room ID
            user_id (str): The user ID of the banee(sic)
            reason (str): The reason for this ban
        """
        body = {
            "user_id": user_id,
            "reason": reason
        }
        return self._send("POST", "/rooms/" + room_id + "/ban", body)

    def unban_user(self, room_id, user_id):
        """Perform POST /rooms/$room_id/unban

        Args:
            room_id (str): The room ID
            user_id (str): The user ID of the banee(sic)
        """
        body = {
            "user_id": user_id
        }
        return self._send("POST", "/rooms/" + room_id + "/unban", body)

    def get_user_tags(self, user_id, room_id):
        return self._send(
            "GET",
            "/user/%s/rooms/%s/tags" % (user_id, room_id),
        )

    def remove_user_tag(self, user_id, room_id, tag):
        return self._send(
            "DELETE",
            "/user/%s/rooms/%s/tags/%s" % (user_id, room_id, tag),
        )

    def add_user_tag(self, user_id, room_id, tag, order=None, body=None):
        if body:
            pass
        elif order:
            body = {"order": order}
        else:
            body = {}
        return self._send(
            "PUT",
            "/user/%s/rooms/%s/tags/%s" % (user_id, room_id, tag),
            body,
        )

    def set_account_data(self, user_id, type, account_data):
        return self._send(
            "PUT",
            "/user/%s/account_data/%s" % (user_id, type),
            account_data,
        )

    def set_room_account_data(self, user_id, room_id, type, account_data):
        return self._send(
            "PUT",
            "/user/%s/rooms/%s/account_data/%s" % (user_id, room_id, type),
            account_data
        )

    def get_room_state(self, room_id):
        """Perform GET /rooms/$room_id/state

        Args:
            room_id (str): The room ID
        """
        return self._send("GET", "/rooms/" + room_id + "/state")

    def get_text_body(self, text, msgtype="m.text"):
        return {
            "msgtype": msgtype,
            "body": text
        }

    def get_emote_body(self, text):
        return {
            "msgtype": "m.emote",
            "body": text
        }

    def get_filter(self, user_id, filter_id):
        return self._send("GET", "/user/{userId}/filter/{filterId}"
                          .format(userId=user_id, filterId=filter_id))

    def create_filter(self, user_id, filter_params):
        return self._send("POST",
                          "/user/{userId}/filter".format(userId=user_id),
                          filter_params)

    def _send(self, method, path, content=None, query_params=None, headers=None,
              api_path=MATRIX_V2_API_PATH, return_json=True):
        if query_params is None:
            query_params = {}
        if headers is None:
            headers = {}

        if "User-Agent" not in headers:
            headers["User-Agent"] = "matrix-python-sdk/%s" % __version__

        method = method.upper()
        if method not in ["GET", "PUT", "DELETE", "POST"]:
            raise MatrixError("Unsupported HTTP method: %s" % method)

        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        if self.use_authorization_header:
            headers["Authorization"] = 'Bearer %s' % self.token
        else:
            query_params["access_token"] = self.token

        if self.identity:
            query_params["user_id"] = self.identity

        endpoint = self._base_url + api_path + path

        if headers["Content-Type"] == "application/json" and content is not None:
            content = json.dumps(content)

        while True:
            try:
                response = self.session.request(
                    method, endpoint,
                    params=query_params,
                    data=content,
                    headers=headers,
                    verify=self.validate_cert
                )
            except RequestException as e:
                raise MatrixHttpLibError(e, method, endpoint)

            if response.status_code == 429:
                waittime = self.default_429_wait_ms / 1000
                try:
                    waittime = response.json()['retry_after_ms'] / 1000
                except KeyError:
                    try:
                        errordata = json.loads(response.json()['error'])
                        waittime = errordata['retry_after_ms'] / 1000
                    except KeyError:
                        pass
                sleep(waittime)
            else:
                break

        if response.status_code < 200 or response.status_code >= 300:
            raise MatrixRequestError(
                code=response.status_code, content=response.text
            )
        if return_json:
            return response.json()
        else:
            return response

    def media_upload(self, content, content_type, filename=None):
        query_params = {}
        if filename is not None:
            query_params['filename'] = filename

        return self._send(
            "POST", "",
            content=content,
            headers={"Content-Type": content_type},
            api_path="/_matrix/media/r0/upload",
            query_params=query_params
        )

    def get_display_name(self, user_id):
        content = self._send("GET", "/profile/%s/displayname" % user_id)
        return content.get('displayname', None)

    def set_display_name(self, user_id, display_name):
        content = {"displayname": display_name}
        return self._send("PUT", "/profile/%s/displayname" % user_id, content)

    def get_avatar_url(self, user_id):
        content = self._send("GET", "/profile/%s/avatar_url" % user_id)
        return content.get('avatar_url', None)

    def set_avatar_url(self, user_id, avatar_url):
        content = {"avatar_url": avatar_url}
        return self._send("PUT", "/profile/%s/avatar_url" % user_id, content)

    def get_download_url(self, mxcurl):
        if mxcurl.startswith('mxc://'):
            return self._base_url + "/_matrix/media/r0/download/" + mxcurl[6:]
        else:
            raise ValueError("MXC URL did not begin with 'mxc://'")

    def media_download(self, mxcurl, allow_remote=True):
        """Download raw media from provided mxc URL.

        Args:
            mxcurl (str): mxc media URL.
            allow_remote (bool): indicates to the server that it should not
                attempt to fetch the media if it is deemed remote. Defaults
                to true if not provided.
        """
        query_params = {}
        if not allow_remote:
            query_params["allow_remote"] = False
        if mxcurl.startswith('mxc://'):
            return self._send(
                "GET", mxcurl[6:],
                api_path="/_matrix/media/r0/download/",
                query_params=query_params,
                return_json=False
            )
        else:
            raise ValueError(
                "MXC URL '%s' did not begin with 'mxc://'" % mxcurl
            )

    def get_thumbnail(self, mxcurl, width, height, method='scale', allow_remote=True):
        """Download raw media thumbnail from provided mxc URL.

        Args:
            mxcurl (str): mxc media URL
            width (int): desired thumbnail width
            height (int): desired thumbnail height
            method (str): thumb creation method. Must be
                in ['scale', 'crop']. Default 'scale'.
            allow_remote (bool): indicates to the server that it should not
                attempt to fetch the media if it is deemed remote. Defaults
                to true if not provided.
        """
        if method not in ['scale', 'crop']:
            raise ValueError(
                "Unsupported thumb method '%s'" % method
            )
        query_params = {
                    "width": width,
                    "height": height,
                    "method": method
                }
        if not allow_remote:
            query_params["allow_remote"] = False
        if mxcurl.startswith('mxc://'):
            return self._send(
                "GET", mxcurl[6:],
                query_params=query_params,
                api_path="/_matrix/media/r0/thumbnail/",
                return_json=False
            )
        else:
            raise ValueError(
                "MXC URL '%s' did not begin with 'mxc://'" % mxcurl
            )

    def get_url_preview(self, url, ts=None):
        """Get preview for URL.

        Args:
            url (str): URL to get a preview
            ts (double): The preferred point in time to return
                 a preview for. The server may return a newer
                 version if it does not have the requested
                 version available.
        """
        params = {'url': url}
        if ts:
            params['ts'] = ts
        return self._send(
            "GET", "",
            query_params=params,
            api_path="/_matrix/media/r0/preview_url"
        )

    def get_room_id(self, room_alias):
        """Get room id from its alias.

        Args:
            room_alias (str): The room alias name.

        Returns:
            Wanted room's id.
        """
        content = self._send("GET", "/directory/room/{}".format(quote(room_alias)))
        return content.get("room_id", None)

    def set_room_alias(self, room_id, room_alias):
        """Set alias to room id

        Args:
            room_id (str): The room id.
            room_alias (str): The room wanted alias name.
        """
        data = {
            "room_id": room_id
        }

        return self._send("PUT", "/directory/room/{}".format(quote(room_alias)),
                          content=data)

    def remove_room_alias(self, room_alias):
        """Remove mapping of an alias

        Args:
            room_alias(str): The alias to be removed.

        Raises:
            MatrixRequestError
        """
        return self._send("DELETE", "/directory/room/{}".format(quote(room_alias)))

    def get_room_members(self, room_id):
        """Get the list of members for this room.

        Args:
            room_id (str): The room to get the member events for.
        """
        return self._send("GET", "/rooms/{}/members".format(quote(room_id)))

    def set_join_rule(self, room_id, join_rule):
        """Set the rule for users wishing to join the room.

        Args:
            room_id(str): The room to set the rules for.
            join_rule(str): The chosen rule. One of: ["public", "knock",
                "invite", "private"]
        """
        content = {
            "join_rule": join_rule
        }
        return self.send_state_event(room_id, "m.room.join_rules", content)

    def set_guest_access(self, room_id, guest_access):
        """Set the guest access policy of the room.

        Args:
            room_id(str): The room to set the rules for.
            guest_access(str): Wether guests can join. One of: ["can_join",
                "forbidden"]
        """
        content = {
            "guest_access": guest_access
        }
        return self.send_state_event(room_id, "m.room.guest_access", content)

    def get_devices(self):
        """Gets information about all devices for the current user."""
        return self._send("GET", "/devices")

    def get_device(self, device_id):
        """Gets information on a single device, by device id."""
        return self._send("GET", "/devices/%s" % device_id)

    def update_device_info(self, device_id, display_name):
        """Update the display name of a device.

        Args:
            device_id (str): The device ID of the device to update.
            display_name (str): New display name for the device.
        """
        content = {
            "display_name": display_name
        }
        return self._send("PUT", "/devices/%s" % device_id, content=content)

    def delete_device(self, auth_body, device_id):
        """Deletes the given device, and invalidates any access token associated with it.

        NOTE: This endpoint uses the User-Interactive Authentication API.

        Args:
            auth_body (dict): Authentication params.
            device_id (str): The device ID of the device to delete.
        """
        content = {
            "auth": auth_body
        }
        return self._send("DELETE", "/devices/%s" % device_id, content=content)

    def delete_devices(self, auth_body, devices):
        """Bulk deletion of devices.

        NOTE: This endpoint uses the User-Interactive Authentication API.

        Args:
            auth_body (dict): Authentication params.
            devices (list): List of device ID"s to delete.
        """
        content = {
            "auth": auth_body,
            "devices": devices
        }
        return self._send("POST", "/delete_devices", content=content)

    def upload_keys(self, device_keys=None, one_time_keys=None):
        """Publishes end-to-end encryption keys for the device.

        Said device must be the one used when logging in.

        Args:
            device_keys (dict): Optional. Identity keys for the device. The required
                keys are:

                | user_id (str): The ID of the user the device belongs to. Must match
                    the user ID used when logging in.
                | device_id (str): The ID of the device these keys belong to. Must match
                    the device ID used when logging in.
                | algorithms (list<str>): The encryption algorithms supported by this
                    device.
                | keys (dict): Public identity keys. Should be formatted as
                    <algorithm:device_id>: <key>.
                | signatures (dict): Signatures for the device key object. Should be
                    formatted as <user_id>: {<algorithm:device_id>: <key>}

            one_time_keys (dict): Optional. One-time public keys. Should be
                formatted as <algorithm:key_id>: <key>, the key format being
                determined by the algorithm.
        """
        content = {}
        if device_keys:
            content["device_keys"] = device_keys
        if one_time_keys:
            content["one_time_keys"] = one_time_keys
        return self._send("POST", "/keys/upload", content=content)

    def query_keys(self, user_devices, timeout=None, token=None):
        """Query HS for public keys by user and optionally device.

        Args:
            user_devices (dict): The devices whose keys to download. Should be
                formatted as <user_id>: [<device_ids>]. No device_ids indicates
                all devices for the corresponding user.
            timeout (int): Optional. The time (in milliseconds) to wait when
                downloading keys from remote servers.
            token (str): Optional. If the client is fetching keys as a result of
                a device update received in a sync request, this should be the
                'since' token of that sync request, or any later sync token.
        """
        content = {"device_keys": user_devices}
        if timeout:
            content["timeout"] = timeout
        if token:
            content["token"] = token
        return self._send("POST", "/keys/query", content=content)

    def claim_keys(self, key_request, timeout=None):
        """Claims one-time keys for use in pre-key messages.

        Args:
            key_request (dict): The keys to be claimed. Format should be
                <user_id>: { <device_id>: <algorithm> }.
            timeout (int): Optional. The time (in milliseconds) to wait when
                downloading keys from remote servers.
        """
        content = {"one_time_keys": key_request}
        if timeout:
            content["timeout"] = timeout
        return self._send("POST", "/keys/claim", content=content)

    def key_changes(self, from_token, to_token):
        """Gets a list of users who have updated their device identity keys.

        Args:
            from_token (str): The desired start point of the list. Should be the
                next_batch field from a response to an earlier call to /sync.
            to_token (str): The desired end point of the list. Should be the next_batch
                field from a recent call to /sync - typically the most recent such call.
        """
        params = {"from": from_token, "to": to_token}
        return self._send("GET", "/keys/changes", query_params=params)

    def send_to_device(self, event_type, messages, txn_id=None):
        """Sends send-to-device events to a set of client devices.

        Args:
            event_type (str): The type of event to send.
            messages (dict): The messages to send. Format should be
                <user_id>: {<device_id>: <event_content>}.
                The device ID may also be '*', meaning all known devices for the user.
            txn_id (str): Optional. The transaction ID for this event, will be generated
                automatically otherwise.
        """
        txn_id = txn_id if txn_id else self._make_txn_id()
        return self._send(
            "PUT",
            "/sendToDevice/{}/{}".format(event_type, txn_id),
            content={"messages": messages}
        )

    def _make_txn_id(self):
        txn_id = str(self.txn_id) + str(int(time() * 1000))
        self.txn_id += 1
        return txn_id

    def whoami(self):
        """Determine user_id for authenticated user.
        """
        if not self.token:
            raise MatrixError("Authentication required.")
        return self._send(
            "GET",
            "/account/whoami"
        )
