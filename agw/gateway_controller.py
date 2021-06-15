import json
import requests
from copy import deepcopy
from urllib.parse import parse_qs, urlencode
from typing import List

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

    def __init__(self, definition_filepath: str):
        self.definition_filepath = definition_filepath
        try:
            gateway_definition = json.load(open(definition_filepath, "r", encoding='utf-8'))
        except json.decoder.JSONDecodeError as e:
            ll.error(f"Parsing gateway definition '{definition_filepath}' failed: {e}")
            return

        if 'route' not in gateway_definition:
            ll.error(f"Gateway definition does not include a 'route'")
            return
        self.route_definition = AGWRouteDefinition(**gateway_definition['route'])

        self.request_definitions = []
        if 'requests' in gateway_definition:
            for req in gateway_definition['requests']:
                self.request_definitions.append(AGWRequestDefinition(**req))

        if 'response' not in gateway_definition:
            ll.error(f"Gateway definition does not include a 'response'")
            return
        self.response_definition = AGWResponseDefinition(**gateway_definition['response'])

        self.after_hooks = None
        if 'after_hooks' in gateway_definition:
            self.after_hooks = gateway_definition['after_hooks']

    def get_routes(self):
        plugins = self.__get_plugins()
        plugins.insert(0, ServiceExceptionHandlerPlugin())
        plugins.insert(0, GatewayRequestEnvironmentPlugin(self.route_definition, self.after_hooks))

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
        for req_def in self.request_definitions:
            agw_req = AGWRequest(req_def)
            gre.evaluate_and_add_request(agw_req)

            # Run builders
            if agw_req.builders:
                for builder_definition in agw_req.builders:
                    get_builder(builder_definition).run(gre)

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
                data=parse_qs(req.text) if req.headers['Content-Type'] == "application/x-www-form-urlencoded" else None,
                json=req.json() if req.headers['Content-Type'] == "application/json" else None
            )

            ll.verbose(f"Got response: {agw_req.response}")

            # Run processors
            if agw_req.processors:
                for processor_definition in agw_req.processors:
                    get_processor(processor_definition).run(gre, agw_req)

        agw_resp = AGWResponse(self.response_definition)
        gre.evaluate_and_add_response(agw_resp)

        # Run generators
        if agw_resp.generators:
            for generator_definition in agw_resp.generators:
                get_generator(generator_definition).run(gre)

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
