import os
import logging
import time
import math
import random  # nosec
import bottle

import mds_logging
import settings
from gateway_controller import GatewayController
from after_hooks import get_after_hook
from gateway_request_environment_plugin import GatewayRequestEnvironment

ll: mds_logging.MdsLogger = logging.getLogger("agw")


class AGW:
    def __init__(self):
        global ll
        mds_logging.MdsLogger.configure_loggers(ll)
        ll = mds_logging.getLogger("agw")
        ll.test_logger()
        settings.log_settings(ll.info)

        self.initialize_bottle()
        self.initialize_routes()

    def initialize_bottle(self):
        self.app = bottle.app()

        self.app.add_hook('before_request', before_request)
        self.app.add_hook('after_request', after_request)

    def initialize_routes(self):
        ll.info("Initializing routes:")

        for subdir, dirs, files in os.walk(settings.GATEWAYS_SEARCH_PATH):
            for filename in files:
                filepath = subdir + os.sep + filename

                if not filepath.endswith(".json"):
                    continue

                controller = GatewayController(filepath)
                for route in controller.get_routes():
                    ll.info(f"  * Adding route: {route['method']} {route['path']}")
                    self.app.route(**route)


# Hook callbacks for bottle

def before_request():
    string = '0123456789abcdefghijklmnopqrstuvwxyz'
    request_id = ""
    length = len(string)
    for _ in range(6):
        request_id += string[math.floor(random.random() * length)]  # nosec

    bottle.request.environ['request_time'] = time.time()
    bottle.request.environ['request_id'] = request_id
    ll.request("+++++++++++++++ REQUEST START: %s|%s|%s|%s|%s" % (
        bottle.request.environ.get('REQUEST_METHOD', ''),
        bottle.request.environ.get('RAW_URI', ''),
        bottle.request.environ.get('REMOTE_ADDR', ''),
        bottle.request.environ.get('HTTP_USER_AGENT', ''),
        bottle.request.environ.get('HTTP_X_FORWARDED_FOR', ''),
    ))

    bottle.response.headers.update({
        'X-Request-Id': request_id,
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'X-Frame-Options': 'DENY',
        'Content-Security-Policy': "default-src 'none'",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Cache-Control': 'private, no-cache, no-store, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
    })


def after_request():
    if 'gre' in bottle.request.environ:
        gre: GatewayRequestEnvironment = bottle.request.environ['gre']
        if gre.after_hooks:
            for after_hook_definition in gre.after_hooks:
                get_after_hook(after_hook_definition).run(gre)

    elapsed = time.time() - bottle.request.environ['request_time']
    ll.request(f"--------------- REQUEST END (request: {elapsed:.3f}s)")
