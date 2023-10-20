# -*- coding: utf-8 -*-

"""
DooraApi HTTP Client Library
~~~~~~~~~~~~~~~~~~~~~
Requests is an HTTP library, written in Python, for human beings.
DoorayApi is an HTTP Client library, written in Python, for those who use the dooray api
(https://helpdesk.dooray.com/share/pages/9wWo-xwiR66BO5LGshgVTg/2939987647631384419)
Basic GET usage:
   >>> import dooray_api
   >>> r = dooray_api.ServiceClient(host="https://api.dooray.com", request_headers={'Authorization': 'dooray-api ~~~~'}).common.v1.members.get()
   >>> r.status_code
   200
... or POST:
   >>> data = {"code": "테스트", "description": "", "scope": "private"}
   >>> r = ServiceClient(host="https://api.dooray.com", request_headers={'Authorization': 'dooray-api ~~~~'}).project.v1.projects.post(request_body=data)
   >>> r.to_dict()
   {
     ...
     "form": {
       "key1": "value1",
       "key2": "value2"
     },
     ...
   }
The other HTTP methods are supported - see `requests.api`. Full documentation
is at <https://requests.readthedocs.io>.
:copyright: (c) 2017 by Kenneth Reitz.
:license: Apache 2.0, see LICENSE for more details.
"""

from .client import Response, ServiceClient
from .exceptions import (
    HTTPError,
    BadRequestsError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    MethodNotAllowedError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    TooManyRequestsError,
    InternalServerError,
    ServiceUnavailableError,
    GatewayTimeoutError,
    err_dict
)