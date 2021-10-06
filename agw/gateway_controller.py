import json
import requests
from copy import deepcopy
from urllib.parse import parse_qs, urlencode
from typing import List, Optional, Dict

from bottle import response

from builders import get_builder
from processors import get_processor
from mds_logging import getLogger, timed
from agw_route import AGWRouteDefinition
from agw_request import AGWRequest, AGWRequestDefinition, AGWRequestResponse
from agw_response import AGWResponse, AGWResponseDefinition
from plugins import get_plugin
from generators import get_generator
from service_exception_handler_plugin import InternalError, ServiceExceptionHandlerPlugin
from gateway_request_environment_plugin import GatewayRequestEnvironmentPlugin, GatewayRequestEnvironment


ll = getLogger("agw." + __name__)


class GatewayController(object):

    def __init__(self, definition_filepath: str, includes: Optional[Dict] = None):
        self.definition_filepath = definition_filepath
        self.includes = includes
        self._read_definition()

    def _read_definition(self):
        ll.debug(f"Reading gateway definition: {self.definition_filepath}")
        try:
            gateway_definition = json.load(open(self.definition_filepath, "r", encoding='utf-8'))
        except json.decoder.JSONDecodeError as e:
            raise InternalError(f"Parsing gateway definition '{self.definition_filepath}' failed: {e}")

        self.constants = {}
        if 'constants' in gateway_definition:
            self.constants = gateway_definition['constants']
            if 'includes' in self.constants:
                basic_definition = deepcopy(self.constants)
                for incl in self.constants['includes']:
                    self.constants.update(self.includes[incl['file']])
                self.constants.update(basic_definition)

        if 'route' not in gateway_definition:
            raise InternalError(f"Gateway definition does not include a 'route'")
        self.route_definition = AGWRouteDefinition(**gateway_definition['route'])

        self.request_definitions = []
        if 'requests' in gateway_definition:
            for req in gateway_definition['requests']:
                if 'includes' in req:
                    for incl in req['includes']:
                        self._include(incl)
                self.request_definitions.append(AGWRequestDefinition(**req))

        if 'response' not in gateway_definition:
            raise InternalError(f"Gateway definition does not include a 'response'")
        self.response_definition = AGWResponseDefinition(**gateway_definition['response'])

        self.after_hooks = None
        if 'after_hooks' in gateway_definition:
            self.after_hooks = gateway_definition['after_hooks']

    def _include(self, incl):
        if not isinstance(incl, dict):
            raise InternalError("Include definition should be a dict")
        if not self.includes or 'file' not in incl:
            raise InternalError("Include definition does not include a 'file'")
        incl['include'] = deepcopy(self.includes[incl['file']])

    def get_routes(self):
        plugins = self.__get_plugins()
        plugins.insert(0, ServiceExceptionHandlerPlugin())
        plugins.insert(0, GatewayRequestEnvironmentPlugin(self.constants, self.route_definition, self.after_hooks))

        # TODO: Plugin might want to add another route (at least cors)

        return [
            {
                'path': self.route_definition.path,
                'method': self.route_definition.method,
                'apply': plugins,
                'callback': self.__handle_route
            }
        ]

    def __get_plugins(self) -> List:
        plugins = []
        if self.route_definition.plugins:
            for plugin_definition in self.route_definition.plugins:
                plugins.append(get_plugin(plugin_definition))
        return plugins

    @timed
    def __handle_route(self, gre: GatewayRequestEnvironment, **kwargs):
        for i, req_def in enumerate(self.request_definitions):
            agw_req = AGWRequest(req_def)
            gre.evaluate_and_add_request(agw_req)

            # Run builders
            if agw_req.builders:
                for builder_definition in agw_req.builders:
                    get_builder(builder_definition).run(gre, self_key=f"requests[{i}]")

            ll.debug(f"Requesting with: {agw_req}")

            req = requests.request(
                agw_req.method,
                agw_req.url,
                headers=agw_req.headers,
                data=agw_req.data if agw_req.data else None,
                json=agw_req.json if agw_req.json else None
            )

            agw_req.response = AGWRequestResponse(
                status=req.status_code,
                headers=deepcopy(req.headers),
                text=req.text,
                data=parse_qs(req.text) if "application/x-www-form-urlencoded" in req.headers['Content-Type'] else None,
                json=req.json() if "application/json" in req.headers['Content-Type'] else None
            )

            ll.verbose(f"Got response: {agw_req.response}")

            # Run processors
            if agw_req.processors:
                for processor_definition in agw_req.processors:
                    get_processor(processor_definition).run(gre, self_key=f"requests[{i}]")

        agw_resp = AGWResponse(self.response_definition)
        gre.evaluate_and_add_response(agw_resp)

        # Run generators
        if agw_resp.generators:
            for generator_definition in agw_resp.generators:
                get_generator(generator_definition).run(gre, self_key=f"response")

        response.status = agw_resp.status
        response.headers.update(agw_resp.headers)

        if 'Content-Length' in response.headers:
            del response.headers['Content-Length']

        if agw_resp.json:
            ll.verbose(f'returning json: {agw_resp.json}')
            return agw_resp.json
        elif agw_resp.data:
            ret = urlencode(agw_resp.data)
            ll.verbose(f'returning data: {ret}')
            return ret
        elif agw_resp.text:
            ll.verbose(f'returning text: {agw_resp.text}')
            return agw_resp.text

        raise InternalError(f"Response does not contain json, data or text.")
