import json
from requests import exceptions


class HTTPError(Exception):
    """"""

    def __init__(self, *args):
        self.status_code = args[1]

    def __str__(self):
        return 'HTTP Error %s:' % self.status_code


class BadRequestsError(HTTPError):
    pass


class UnauthorizedError(HTTPError):
    pass


class ForbiddenError(HTTPError):
    pass


class NotFoundError(HTTPError):
    pass


class MethodNotAllowedError(HTTPError):
    pass


class RequestCreateDuplicateResourcesError(HTTPError):
    pass


class PayloadTooLargeError(HTTPError):
    pass


class UnsupportedMediaTypeError(HTTPError):
    pass


class TooManyRequestsError(HTTPError):
    pass


class InternalServerError(HTTPError):
    pass


class ServiceUnavailableError(HTTPError):
    pass


class GatewayTimeoutError(HTTPError):
    pass


err_dict = {
    400: BadRequestsError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    405: MethodNotAllowedError,
    409: RequestCreateDuplicateResourcesError,
    413: PayloadTooLargeError,
    415: UnsupportedMediaTypeError,
    429: TooManyRequestsError,
    500: InternalServerError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError
}