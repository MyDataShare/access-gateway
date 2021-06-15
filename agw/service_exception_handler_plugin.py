import bottle
import logging
import json
from typing import Optional

import mds_logging


ll = mds_logging.getLogger("agw." + __name__)


UNEXPECTED_ERROR_MSG = 'Unexpected error occurred.'


class ServiceError(Exception):
    error = "service_error"
    status = 500
    log_level = logging.INFO

    def __init__(self, description: str, log: Optional[str] = None):
        self.error = self.__class__.error
        self.status = self.__class__.status
        self.description = description
        self.log = log

    def __str__(self) -> str:
        return self.log if self.log else self.description  # pyre-ignore


class BadRequestError(ServiceError):
    error = "bad_request"
    status = 400


class AuthorizationError(ServiceError):
    error = "authorization_error"
    status = 401


class ForbiddenError(ServiceError):
    error = "forbidden"
    status = 403


class NotFoundError(ServiceError):
    error = "not_found_error"
    status = 404


class ConflictError(ServiceError):
    error = "conflict_error"
    status = 409


class InternalError(ServiceError):
    error = "internal_error"
    status = 500
    log_level = logging.ERROR


class ServiceExceptionHandlerPlugin(object):

    _DEBUG_FLAG = False

    @staticmethod
    def set_debug(value: bool):
        ServiceExceptionHandlerPlugin._DEBUG_FLAG = value

    def apply(self, callback, route):
        def wrapper(**kwargs):
            try:
                return callback(**kwargs)
            except ServiceError as service_error:
                ServiceExceptionHandlerPlugin.handle_service_error(service_error)
            # This is to hide all the unexpected errors
            except Exception as e:
                ll.exception(e)
                gre = bottle.request.environ['gre']
                gre.error = UNEXPECTED_ERROR_MSG

                if not ServiceExceptionHandlerPlugin._DEBUG_FLAG:
                    raise bottle.HTTPResponse(
                        status=500,
                        headers={
                            **bottle.response.headers,
                            'Content-Type': 'application/json',
                        },
                        body=json.dumps({
                            'error': 'internal_error',
                            'description': UNEXPECTED_ERROR_MSG,
                            'request_id': bottle.request.environ.get('request_id')
                        })
                    )
                else:
                    raise e

        return wrapper

    @staticmethod
    def handle_service_error(service_error: ServiceError):
        """
        Raise a HTTPResponse from a ServiceError.

        If the given ServiceError has a `log`, it will be used for logging the error and the ServiceError's
        `description` is logged in DEBUG log level only. If the ServiceError does not have `log`, its `description` is
        logged in the ServiceError's `log_level`.

        The HTTPResponse will always contain `description` in its 'description' key.

        :param service_error: The ServiceError to be converted into a HTTPResponse
        :return: None
        """
        if service_error.log:
            ll.debug(f'{service_error.__class__.__name__}: Error description: {service_error.description}')
            log_msg = service_error.log
        else:
            log_msg = service_error.description
        ll.log(service_error.log_level, f"{service_error.__class__.__name__}: {log_msg}")

        gre = bottle.request.environ['gre']
        gre.error = log_msg

        raise bottle.HTTPResponse(
            status=service_error.status,
            headers={
                **bottle.response.headers,
                'Content-Type': 'application/json',
            },
            body=json.dumps({
                'error': service_error.error,
                'description': service_error.description,
                'request_id': bottle.request.environ.get('request_id')
            })
        )
