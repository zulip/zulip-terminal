# -*- coding: utf-8 -*-
# Copyright 2015 OpenMarket Ltd
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
from warnings import warn

from .checks import check_user_id


class User(object):
    """ The User class can be used to call user specific functions.
    """
    def __init__(self, api, user_id, displayname=None):
        check_user_id(user_id)

        self.user_id = user_id
        self.displayname = displayname
        self.api = api

    def get_display_name(self, room=None):
        """Get this user's display name.

        Args:
            room (Room): Optional. When specified, return the display name of the user
                in this room.

        Returns:
            The display name. Defaults to the user ID if not set.
        """
        if room:
            try:
                return room.members_displaynames[self.user_id]
            except KeyError:
                return self.user_id
        if not self.displayname:
            self.displayname = self.api.get_display_name(self.user_id)
        return self.displayname or self.user_id

    def get_friendly_name(self):
        """Deprecated. Use :meth:`get_display_name` instead."""
        warn("get_friendly_name is deprecated. Use get_display_name instead.",
             DeprecationWarning)
        return self.get_display_name()

    def set_display_name(self, display_name):
        """ Set this users display name.

        Args:
            display_name (str): Display Name
        """
        self.displayname = display_name
        return self.api.set_display_name(self.user_id, display_name)

    def get_avatar_url(self):
        mxcurl = self.api.get_avatar_url(self.user_id)
        url = None
        if mxcurl is not None:
            url = self.api.get_download_url(mxcurl)
        return url

    def set_avatar_url(self, avatar_url):
        """ Set this users avatar.

        Args:
            avatar_url (str): mxc url from previously uploaded
        """
        return self.api.set_avatar_url(self.user_id, avatar_url)
