# -*- coding: utf-8 -*-
# Copyright 2015 OpenMarket Ltd
# Copyright 2018 Adam Beckmeyer
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
import logging
import re
from uuid import uuid4

from .checks import check_room_id
from .user import User
from .errors import MatrixRequestError

logger = logging.getLogger(__name__)


class Room(object):
    """Call room-specific functions after joining a room from the client.

    NOTE: This should ideally be called from within the Client.
    NOTE: This does not verify the room with the Home Server.
    """

    def __init__(self, client, room_id):
        check_room_id(room_id)

        self.room_id = room_id
        self.client = client
        self.listeners = []
        self.state_listeners = []
        self.ephemeral_listeners = []
        self.events = []
        self.event_history_limit = 20
        self.name = None
        self.canonical_alias = None
        self.aliases = []
        self.topic = None
        self.invite_only = None
        self.guest_access = None
        self._prev_batch = None
        self._members = {}
        self.members_displaynames = {
            # user_id: displayname
        }
        self.encrypted = False

    def set_user_profile(self,
                         displayname=None,
                         avatar_url=None,
                         reason="Changing room profile information"):
        """Set user profile within a room.

        This sets displayname and avatar_url for the logged in user only in a
        specific room. It does not change the user's global user profile.
        """
        member = self.client.api.get_membership(self.room_id, self.client.user_id)
        if member["membership"] != "join":
            raise Exception("Can't set profile if you have not joined the room.")
        if displayname is None:
            displayname = member["displayname"]
        if avatar_url is None:
            avatar_url = member["avatar_url"]
        self.client.api.set_membership(
            self.room_id,
            self.client.user_id,
            'join',
            reason, {
                "displayname": displayname,
                "avatar_url": avatar_url
            }
        )

    @property
    def display_name(self):
        """Calculates the display name for a room."""
        if self.name:
            return self.name
        elif self.canonical_alias:
            return self.canonical_alias

        # Member display names without me
        members = [u.get_display_name(self) for u in self.get_joined_members() if
                   self.client.user_id != u.user_id]
        members.sort()

        if len(members) == 1:
            return members[0]
        elif len(members) == 2:
            return "{0} and {1}".format(members[0], members[1])
        elif len(members) > 2:
            return "{0} and {1} others".format(members[0], len(members) - 1)
        else:  # len(members) <= 0 or not an integer
            # TODO i18n
            return "Empty room"

    def send_text(self, text):
        """Send a plain text message to the room."""
        return self.client.api.send_message(self.room_id, text)

    def get_html_content(self, html, body=None, msgtype="m.text"):
        return {
            "body": body if body else re.sub('<[^<]+?>', '', html),
            "msgtype": msgtype,
            "format": "org.matrix.custom.html",
            "formatted_body": html
        }

    def send_html(self, html, body=None, msgtype="m.text"):
        """Send an html formatted message.

        Args:
            html (str): The html formatted message to be sent.
            body (str): The unformatted body of the message to be sent.
        """
        return self.client.api.send_message_event(
            self.room_id, "m.room.message", self.get_html_content(html, body, msgtype))

    def set_account_data(self, type, account_data):
        return self.client.api.set_room_account_data(
            self.client.user_id, self.room_id, type, account_data)

    def get_tags(self):
        return self.client.api.get_user_tags(self.client.user_id, self.room_id)

    def remove_tag(self, tag):
        return self.client.api.remove_user_tag(
            self.client.user_id, self.room_id, tag
        )

    def add_tag(self, tag, order=None, content=None):
        return self.client.api.add_user_tag(
            self.client.user_id, self.room_id,
            tag, order, content
        )

    def send_emote(self, text):
        """Send an emote (/me style) message to the room."""
        return self.client.api.send_emote(self.room_id, text)

    def send_file(self, url, name, **fileinfo):
        """Send a pre-uploaded file to the room.

        See http://matrix.org/docs/spec/r0.2.0/client_server.html#m-file for
        fileinfo.

        Args:
            url (str): The mxc url of the file.
            name (str): The filename of the image.
            fileinfo (): Extra information about the file
        """

        return self.client.api.send_content(
            self.room_id, url, name, "m.file",
            extra_information=fileinfo
        )

    def send_notice(self, text):
        """Send a notice (from bot) message to the room."""
        return self.client.api.send_notice(self.room_id, text)

    # See http://matrix.org/docs/spec/r0.0.1/client_server.html#m-image for the
    # imageinfo args.
    def send_image(self, url, name, **imageinfo):
        """Send a pre-uploaded image to the room.

        See http://matrix.org/docs/spec/r0.0.1/client_server.html#m-image
        for imageinfo

        Args:
            url (str): The mxc url of the image.
            name (str): The filename of the image.
            imageinfo (): Extra information about the image.
        """
        return self.client.api.send_content(
            self.room_id, url, name, "m.image",
            extra_information=imageinfo
        )

    def send_location(self, geo_uri, name, thumb_url=None, **thumb_info):
        """Send a location to the room.

        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-location
        for thumb_info

        Args:
            geo_uri (str): The geo uri representing the location.
            name (str): Description for the location.
            thumb_url (str): URL to the thumbnail of the location.
            thumb_info (): Metadata about the thumbnail, type ImageInfo.
        """
        return self.client.api.send_location(self.room_id, geo_uri, name,
                                             thumb_url, thumb_info)

    def send_video(self, url, name, **videoinfo):
        """Send a pre-uploaded video to the room.

        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-video
        for videoinfo

        Args:
            url (str): The mxc url of the video.
            name (str): The filename of the video.
            videoinfo (): Extra information about the video.
        """
        return self.client.api.send_content(self.room_id, url, name, "m.video",
                                            extra_information=videoinfo)

    def send_audio(self, url, name, **audioinfo):
        """Send a pre-uploaded audio to the room.

        See http://matrix.org/docs/spec/client_server/r0.2.0.html#m-audio
        for audioinfo

        Args:
            url (str): The mxc url of the audio.
            name (str): The filename of the audio.
            audioinfo (): Extra information about the audio.
        """
        return self.client.api.send_content(self.room_id, url, name, "m.audio",
                                            extra_information=audioinfo)

    def redact_message(self, event_id, reason=None):
        """Redacts the message with specified event_id for the given reason.

        See https://matrix.org/docs/spec/r0.0.1/client_server.html#id112
        """
        return self.client.api.redact_event(self.room_id, event_id, reason)

    def add_listener(self, callback, event_type=None):
        """Add a callback handler for events going to this room.

        Args:
            callback (func(room, event)): Callback called when an event arrives.
            event_type (str): The event_type to filter for.
        Returns:
            uuid.UUID: Unique id of the listener, can be used to identify the listener.
        """
        listener_id = uuid4()
        self.listeners.append(
            {
                'uid': listener_id,
                'callback': callback,
                'event_type': event_type
            }
        )
        return listener_id

    def remove_listener(self, uid):
        """Remove listener with given uid."""
        self.listeners[:] = (listener for listener in self.listeners
                             if listener['uid'] != uid)

    def add_ephemeral_listener(self, callback, event_type=None):
        """Add a callback handler for ephemeral events going to this room.

        Args:
            callback (func(room, event)): Callback called when an ephemeral event arrives.
            event_type (str): The event_type to filter for.
        Returns:
            uuid.UUID: Unique id of the listener, can be used to identify the listener.
        """
        listener_id = uuid4()
        self.ephemeral_listeners.append(
            {
                'uid': listener_id,
                'callback': callback,
                'event_type': event_type
            }
        )
        return listener_id

    def remove_ephemeral_listener(self, uid):
        """Remove ephemeral listener with given uid."""
        self.ephemeral_listeners[:] = (listener for listener in self.ephemeral_listeners
                                       if listener['uid'] != uid)

    def add_state_listener(self, callback, event_type=None):
        """Add a callback handler for state events going to this room.

        Args:
            callback (func(roomchunk)): Callback called when an event arrives.
            event_type (str): The event_type to filter for.
        """
        self.state_listeners.append(
            {
                'callback': callback,
                'event_type': event_type
            }
        )

    def _put_event(self, event):
        self.events.append(event)
        if len(self.events) > self.event_history_limit:
            self.events.pop(0)
        if 'state_key' in event:
            self._process_state_event(event)

        # Dispatch for room-specific listeners
        for listener in self.listeners:
            if listener['event_type'] is None or listener['event_type'] == event['type']:
                listener['callback'](self, event)

    def _put_ephemeral_event(self, event):
        # Dispatch for room-specific listeners
        for listener in self.ephemeral_listeners:
            if listener['event_type'] is None or listener['event_type'] == event['type']:
                listener['callback'](self, event)

    def get_events(self):
        """Get the most recent events for this room."""
        return self.events

    def invite_user(self, user_id):
        """Invite a user to this room.

        Returns:
            boolean: Whether invitation was sent.
        """
        try:
            self.client.api.invite_user(self.room_id, user_id)
            return True
        except MatrixRequestError:
            return False

    def kick_user(self, user_id, reason=""):
        """Kick a user from this room.


        Args:
            user_id (str): The matrix user id of a user.
            reason  (str): A reason for kicking the user.

        Returns:
            boolean: Whether user was kicked.
        """
        try:
            self.client.api.kick_user(self.room_id, user_id)
            return True
        except MatrixRequestError:
            return False

    def ban_user(self, user_id, reason):
        """Ban a user from this room

        Args:
            user_id (str): The matrix user id of a user.
            reason  (str): A reason for banning the user.

        Returns:
            boolean: The user was banned.
        """
        try:
            self.client.api.ban_user(self.room_id, user_id, reason)
            return True
        except MatrixRequestError:
            return False

    def unban_user(self, user_id):
        """Unban a user from this room

        Returns:
            boolean: The user was unbanned.
        """
        try:
            self.client.api.unban_user(self.room_id, user_id)
            return True
        except MatrixRequestError:
            return False

    def leave(self):
        """Leave the room.

        Returns:
            boolean: Leaving the room was successful.
        """
        try:
            self.client.api.leave_room(self.room_id)
            del self.client.rooms[self.room_id]
            return True
        except MatrixRequestError:
            return False

    def update_room_name(self):
        """Updates self.name and returns True if room name has changed."""
        try:
            response = self.client.api.get_room_name(self.room_id)
            if "name" in response and response["name"] != self.name:
                self.name = response["name"]
                return True
            else:
                return False
        except MatrixRequestError:
            return False

    def set_room_name(self, name):
        """Return True if room name successfully changed."""
        try:
            self.client.api.set_room_name(self.room_id, name)
            self.name = name
            return True
        except MatrixRequestError:
            return False

    def send_state_event(self, event_type, content, state_key=""):
        """Send a state event to the room.

        Args:
            event_type (str): The type of event that you are sending.
            content (): An object with the content of the message.
            state_key (str, optional): A unique key to identify the state.
        """
        return self.client.api.send_state_event(
            self.room_id,
            event_type,
            content,
            state_key
        )

    def update_room_topic(self):
        """Updates self.topic and returns True if room topic has changed."""
        try:
            response = self.client.api.get_room_topic(self.room_id)
            if "topic" in response and response["topic"] != self.topic:
                self.topic = response["topic"]
                return True
            else:
                return False
        except MatrixRequestError:
            return False

    def set_room_topic(self, topic):
        """Set room topic.

        Returns:
            boolean: True if the topic changed, False if not
        """
        try:
            self.client.api.set_room_topic(self.room_id, topic)
            self.topic = topic
            return True
        except MatrixRequestError:
            return False

    def update_aliases(self):
        """Get aliases information from room state.

        Returns:
            boolean: True if the aliases changed, False if not
        """
        try:
            response = self.client.api.get_room_state(self.room_id)
            for chunk in response:
                if "content" in chunk and "aliases" in chunk["content"]:
                    if chunk["content"]["aliases"] != self.aliases:
                        self.aliases = chunk["content"]["aliases"]
                        return True
                    else:
                        return False
        except MatrixRequestError:
            return False

    def add_room_alias(self, room_alias):
        """Add an alias to the room and return True if successful."""
        try:
            self.client.api.set_room_alias(self.room_id, room_alias)
            return True
        except MatrixRequestError:
            return False

    def get_joined_members(self):
        """Returns list of joined members (User objects)."""
        if self._members:
            return list(self._members.values())
        response = self.client.api.get_room_members(self.room_id)
        for event in response["chunk"]:
            if event["content"]["membership"] == "join":
                user_id = event["state_key"]
                self._add_member(user_id, event["content"].get("displayname"))
        return list(self._members.values())

    def _add_member(self, user_id, displayname=None):
        if displayname:
            self.members_displaynames[user_id] = displayname
        if user_id in self._members:
            return
        if user_id in self.client.users:
            self._members[user_id] = self.client.users[user_id]
            return
        self._members[user_id] = User(self.client.api, user_id, displayname)
        self.client.users[user_id] = self._members[user_id]

    def backfill_previous_messages(self, reverse=False, limit=10):
        """Backfill handling of previous messages.

        Args:
            reverse (bool): When false messages will be backfilled in their original
                order (old to new), otherwise the order will be reversed (new to old).
            limit (int): Number of messages to go back.
        """
        res = self.client.api.get_room_messages(self.room_id, self.prev_batch,
                                                direction="b", limit=limit)
        events = res["chunk"]
        if not reverse:
            events = reversed(events)
        for event in events:
            self._put_event(event)

    def modify_user_power_levels(self, users=None, users_default=None):
        """Modify the power level for a subset of users

        Args:
            users(dict): Power levels to assign to specific users, in the form
                {"@name0:host0": 10, "@name1:host1": 100, "@name3:host3", None}
                A level of None causes the user to revert to the default level
                as specified by users_default.
            users_default(int): Default power level for users in the room

        Returns:
            True if successful, False if not
        """
        try:
            content = self.client.api.get_power_levels(self.room_id)
            if users_default:
                content["users_default"] = users_default

            if users:
                if "users" in content:
                    content["users"].update(users)
                else:
                    content["users"] = users

                # Remove any keys with value None
                for user, power_level in list(content["users"].items()):
                    if power_level is None:
                        del content["users"][user]
            self.client.api.set_power_levels(self.room_id, content)
            return True
        except MatrixRequestError:
            return False

    def modify_required_power_levels(self, events=None, **kwargs):
        """Modifies room power level requirements.

        Args:
            events(dict): Power levels required for sending specific event types,
                in the form {"m.room.whatever0": 60, "m.room.whatever2": None}.
                Overrides events_default and state_default for the specified
                events. A level of None causes the target event to revert to the
                default level as specified by events_default or state_default.
            **kwargs: Key/value pairs specifying the power levels required for
                    various actions:

                    - events_default(int): Default level for sending message events
                    - state_default(int): Default level for sending state events
                    - invite(int): Inviting a user
                    - redact(int): Redacting an event
                    - ban(int): Banning a user
                    - kick(int): Kicking a user

        Returns:
            True if successful, False if not
        """
        try:
            content = self.client.api.get_power_levels(self.room_id)
            content.update(kwargs)
            for key, value in list(content.items()):
                if value is None:
                    del content[key]

            if events:
                if "events" in content:
                    content["events"].update(events)
                else:
                    content["events"] = events

                # Remove any keys with value None
                for event, power_level in list(content["events"].items()):
                    if power_level is None:
                        del content["events"][event]

            self.client.api.set_power_levels(self.room_id, content)
            return True
        except MatrixRequestError:
            return False

    def set_invite_only(self, invite_only):
        """Set how the room can be joined.

        Args:
            invite_only(bool): If True, users will have to be invited to join
                the room. If False, anyone who knows the room link can join.

        Returns:
            True if successful, False if not
        """
        join_rule = "invite" if invite_only else "public"
        try:
            self.client.api.set_join_rule(self.room_id, join_rule)
            self.invite_only = invite_only
            return True
        except MatrixRequestError:
            return False

    def set_guest_access(self, allow_guests):
        """Set whether guests can join the room and return True if successful."""
        guest_access = "can_join" if allow_guests else "forbidden"
        try:
            self.client.api.set_guest_access(self.room_id, guest_access)
            self.guest_access = allow_guests
            return True
        except MatrixRequestError:
            return False

    def enable_encryption(self):
        """Enables encryption in the room.

        NOTE: Once enabled, encryption cannot be disabled.

        Returns:
        True if successful, False if not
        """
        try:
            self.send_state_event("m.room.encryption",
                                  {"algorithm": "m.megolm.v1.aes-sha2"})
            self.encrypted = True
            return True
        except MatrixRequestError:
            return False

    def _process_state_event(self, state_event):
        if "type" not in state_event:
            return  # Ignore event
        etype = state_event["type"]
        econtent = state_event["content"]
        clevel = self.client._cache_level

        # Don't keep track of room state if caching turned off
        if clevel >= 0:
            try:
                if etype == "m.room.name":
                    self.name = econtent.get("name")
                elif etype == "m.room.canonical_alias":
                    self.canonical_alias = econtent.get("alias")
                elif etype == "m.room.topic":
                    self.topic = econtent.get("topic")
                elif etype == "m.room.aliases":
                    self.aliases = econtent.get("aliases")
                elif etype == "m.room.join_rules":
                    self.invite_only = econtent["join_rule"] == "invite"
                elif etype == "m.room.guest_access":
                    self.guest_access = econtent["guest_access"] == "can_join"
                elif etype == "m.room.encryption":
                    if econtent.get("algorithm") == "m.megolm.v1.aes-sha2":
                        self.encrypted = True
                elif etype == "m.room.member" and clevel == clevel.ALL:
                    # tracking room members can be large e.g. #matrix:matrix.org
                    if econtent["membership"] == "join":
                        user_id = state_event["state_key"]
                        self._add_member(user_id, econtent.get("displayname"))
                    elif econtent["membership"] in ("leave", "kick", "invite"):
                        self._members.pop(state_event["state_key"], None)
            except KeyError:
                logger.exception("Unable to parse state event %s, passing over.",
                                 state_event['event_id'])

        for listener in self.state_listeners:
            if (
                listener['event_type'] is None or
                listener['event_type'] == state_event['type']
            ):
                listener['callback'](state_event)

    @property
    def prev_batch(self):
        return self._prev_batch

    @prev_batch.setter
    def prev_batch(self, prev_batch):
        self._prev_batch = prev_batch
