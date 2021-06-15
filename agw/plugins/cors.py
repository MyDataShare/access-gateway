import logging
import re
from typing import Optional

from bottle import response, request

import settings

ll = logging.getLogger("mop." + __name__)


class CorsPlugin:
    def __init__(
            self,
            origin_pattern: Optional[str] = None,
            methods: str = 'PUT, GET, POST, PATCH, DELETE, OPTIONS',
            headers: str = 'Authorization, Origin, Accept, Content-Type, X-Requested-With',
            credentials: str = 'true',
    ):
        self.origin_pattern = settings.get_required_setting('CORS_ORIGIN_PATTERN')\
            if origin_pattern is None else origin_pattern
        self.origin_re = re.compile(self.origin_pattern)
        self.methods = methods
        self.headers = headers
        self.credentials = credentials

    def apply(self, callback, route):
        def wrapper(**kwargs):
            origin = request.headers.get('Origin')
            ll.debug(f'Request "Origin" header: {origin}, allowed origin: {self.origin_pattern}')
            if origin is not None and self.origin_re.fullmatch(origin) is not None:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers.update({
                'Access-Control-Allow-Headers': self.headers,
                'Access-Control-Allow-Methods': self.methods,
                'Access-Control-Allow-Credentials': self.credentials,
            })
            return callback(**kwargs)
        return wrapper

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return str(self.__dict__)
