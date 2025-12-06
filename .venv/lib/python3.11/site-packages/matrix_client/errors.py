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


class MatrixError(Exception):
    """A generic Matrix error. Specific errors will subclass this."""
    pass


class MatrixUnexpectedResponse(MatrixError):
    """The home server gave an unexpected response. """

    def __init__(self, content=""):
        super(MatrixUnexpectedResponse, self).__init__(content)
        self.content = content


class MatrixRequestError(MatrixError):
    """ The home server returned an error response. """

    def __init__(self, code=0, content=""):
        super(MatrixRequestError, self).__init__("%d: %s" % (code, content))
        self.code = code
        self.content = content


class MatrixHttpLibError(MatrixError):
    """The library used for http requests raised an exception."""

    def __init__(self, original_exception, method, endpoint):
        super(MatrixHttpLibError, self).__init__(
            "Something went wrong in {} requesting {}: {}".format(method,
                                                                  endpoint,
                                                                  original_exception)
        )
        self.original_exception = original_exception
