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


def check_room_id(room_id):
    if not room_id.startswith("!"):
        raise ValueError("RoomIDs start with !")

    if ":" not in room_id:
        raise ValueError("RoomIDs must have a domain component, seperated by a :")


def check_user_id(user_id):
    if not user_id.startswith("@"):
        raise ValueError("UserIDs start with @")

    if ":" not in user_id:
        raise ValueError("UserIDs must have a domain component, seperated by a :")
