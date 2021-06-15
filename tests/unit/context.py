import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'agw')))

os.environ['AGW_GATEWAYS_SEARCH_PATH'] = 'unittest'

import agw_request  # noqa
import agw_response  # noqa
import agw_route  # noqa
from gateway_request_environment_plugin import GatewayRequestEnvironment # noqa
from util import EnvironmentReferenceError  # noqa
