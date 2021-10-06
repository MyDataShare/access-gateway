import numbers
from typing import Optional, List, Any, Tuple, Dict, Union
import re
from copy import deepcopy

from bottle import request
from requests.models import CaseInsensitiveDict

from mds_logging import getLogger
from agw_route import AGWRoute, AGWRouteDefinition
from agw_request import AGWRequest
from agw_response import AGWResponse
from util import EnvironmentReferenceError
from service_exception_handler_plugin import InternalError

ll = getLogger("agw." + __name__)


class GatewayRequestEnvironment:
    def __init__(
        self,
        constants: dict,
        route: AGWRoute,
        requests: Optional[List[AGWRequest]] = None,
        response: Optional[AGWResponse] = None,
        after_hooks: Optional[List[Dict]] = None,
        error: Optional[str] = None
    ) -> None:
        self.constants = constants
        self.route = route
        self.requests = requests if requests else []
        self.response = response
        self.after_hooks = after_hooks
        self.error = error

        self.requests_by_name: Dict[str, AGWRequest] = {}

    def evaluate_and_add_request(self, agw_request: AGWRequest):

        # Handle includes
        if agw_request.includes:
            for incl in agw_request.includes:
                self.arguments = {}
                if 'arguments' in incl:
                    self.arguments = incl['arguments']
                    self._evaluate_variables(incl['include'])
                    for key, val in incl['include'].items():
                        setattr(agw_request, key, val)
                    del incl['include']

        self._evaluate_variables(agw_request)
        self.requests.append(agw_request)
        if agw_request.name:
            self.requests_by_name[agw_request.name] = agw_request

    def evaluate_and_add_response(self, agw_response: AGWResponse):
        self._evaluate_variables(agw_response)
        self.response = agw_response

    @staticmethod
    def _split_gre_key(key: str):
        parts = []
        pos = 0
        open_sq_brackets = 0
        for i, c in enumerate(key):
            if c == '.' and open_sq_brackets == 0:
                parts.append(key[pos:i])
                pos = i + 1
            elif c == '[':
                open_sq_brackets += 1
            elif c == ']':
                open_sq_brackets -= 1
                if open_sq_brackets < 0:
                    raise ValueError(f"Syntax error {key}")
        parts.append(key[pos:])
        return parts

    def _get_node(self, key: str, create_path: bool = False) -> Tuple[Any, Any]:
        """
        Extract a reference to the innermost node and its index or key from given GRE key.

        The node reference and its key can be used for querying the value, changing it or deleting it.

        :param key: The full key pointing to a value in GRE.
        :param create_path: If True, missing paths in given key will be created instead of raising a KeyError.
        :return: A tuple where the first item is the node, and the second is its key or index where the value pointed
            by the given key can be found.
        :raises KeyError: If given key is not found in GRE.
        :raises IndexError: If a list index in given key was out of range.
        :raises ValueError: If the given key is not properly formed.
        """

        parts = self._split_gre_key(key)

        gre_node: Any = self
        for part_index, part in enumerate(parts):
            is_last_part = part_index == len(parts) - 1
            index_or_key: Optional[Union[str, int]] = None
            p = part
            if p[-1] == ']':
                subparts = p.split('[')
                if len(subparts) != 2:
                    raise ValueError(f"Env array notation failed for {part} (from: {key})")
                p = subparts[0]
                iok = subparts[1][0:-1]
                if iok.isdigit():
                    index_or_key = int(iok)
                elif iok[0] in ('"', "'"):
                    if iok[-1] not in ('"', "'"):
                        raise ValueError(f"Env dict notation failed for {part} (from: {key})")
                    index_or_key = iok[1:-1]
                else:
                    index_or_key = self.get(iok)

            if isinstance(gre_node, dict) or isinstance(gre_node, CaseInsensitiveDict):
                # Current node is a dict
                if p not in gre_node:
                    # Next key is not present in current node
                    if create_path:
                        # If create_path is True and next key is not the last one, create the next key
                        if not is_last_part:
                            gre_node[p] = {}
                        elif is_last_part and index_or_key is not None:
                            raise KeyError(f"Env does not contain '{part}' (from: {key}) (1)")
                    else:
                        raise KeyError(f"Env does not contain '{part}' (from: {key}) (2)")

                # If this is the last key, return current node and the key (regardless if the key exists)
                if is_last_part:
                    if index_or_key is not None:
                        return gre_node[p], index_or_key
                    return gre_node, p
                gre_node = gre_node[p]

            else:
                # Current node is some object (like AGWRequest, AGWRequestResponse...)
                if not hasattr(gre_node, p) and not is_last_part:
                    # We cannot create this types of objects dynamically, they should be present already so an error
                    # is raised always if not found.
                    raise KeyError(f"Env does not contain '{part}' (from: {key}) (3)")

                if is_last_part:
                    return gre_node, p
                gre_node = getattr(gre_node, p)

            if index_or_key is not None:
                if isinstance(index_or_key, int):
                    # Current node is a list (can be a list of AGWRequest)
                    if not isinstance(gre_node, list):
                        raise KeyError(f"Env '{part}' is not a list (from: {key})")
                    if is_last_part:
                        return gre_node, index_or_key
                    if len(gre_node) <= index_or_key:
                        raise IndexError(f"Env '{part}' list index out of range (from: {key})")
                    gre_node = gre_node[index_or_key]
                else:
                    # Current node is a dict
                    if not isinstance(gre_node, dict):
                        raise KeyError(f"Env '{part}' is not a dict (from: {key})")
                    if index_or_key not in gre_node:
                        raise KeyError(f"Env '{p}' does not contain {index_or_key} (from: {key}) (4)")
                    gre_node = gre_node[index_or_key]

        raise KeyError(f'Env {key} not found')

    def get(self, key: str) -> Any:
        """
        Get a value from GRE.

        :param key: The path to the value.
        :return: The found value.
        :raises EnvironmentReferenceError: If given key was not found in GRE or it was badly formed.
        """
        try:
            node, node_key = self._get_node(key)
            if isinstance(node, (list, dict, CaseInsensitiveDict)):
                return node[node_key]
            return getattr(node, node_key)
        except (ValueError, IndexError, KeyError, AttributeError) as e:
            raise EnvironmentReferenceError(e)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value to GRE.

        If the given path does not exist, it will be created. Missing lists in given key cannot be created
        automatically.

        :param key: The path to set the value to.
        :param value: The value to set.
        :return: None
        :raises EnvironmentReferenceError: If given key was not found in GRE or it was badly formed.
        """
        try:
            node, node_key = self._get_node(key, create_path=True)
            if isinstance(node, (dict, list, CaseInsensitiveDict)):
                node[node_key] = value
            else:
                setattr(node, node_key, value)
        except (ValueError, IndexError, KeyError) as e:
            raise EnvironmentReferenceError(e)

    def pop(self, key: str) -> Any:
        try:
            node, node_key = self._get_node(key)
            if isinstance(node, (dict, list, CaseInsensitiveDict)):
                return node.pop(node_key)
            value = getattr(node, node_key)
            delattr(node, node_key)
            return value
        except (ValueError, IndexError, KeyError) as e:
            raise EnvironmentReferenceError(e)

    def _process_variable(self, node, index_or_key):
        if not isinstance(node[index_or_key], str):
            return
        for m in re.finditer(r'\${([^}]+)}', node[index_or_key]):
            # group 0: e.g. ${requests[0].response.json}
            # group 1: e.g. requests[0].response.json
            str_to_replace = m.group(0)
            key = m.group(1)
            try:
                value = self.get(key)
            except EnvironmentReferenceError as e:
                raise InternalError(f'Gateway route reference error', log=f'Key not found in env: "{key}". Error: {e}')
            if not isinstance(value, (str, numbers.Number)):
                raise InternalError(f'Gateway route reference error',
                                    log=f'Env {key} is not a Number or str, cannot replace.')
            node[index_or_key] = node[index_or_key].replace(str_to_replace, str(value))

    def _evaluate_variables(self, node):
        if isinstance(node, AGWRequest) or isinstance(node, AGWResponse):
            node = node.__dict__

        if isinstance(node, dict):
            for key in node.keys():
                self._process_variable(node, key)
                self._evaluate_variables(node[key])
        elif isinstance(node, list):
            for i in range(len(node)):
                self._process_variable(node, i)
                self._evaluate_variables(node[i])


def multiDict_to_dict(multidict):
    if not multidict:
        return None
    ret = {}
    for key in multidict.keys():
        lst = multidict.getall(key)
        if len(lst) == 1:
            ret[key] = lst[0]
        if len(lst) > 1:
            ret[key] = lst
    return ret


class GatewayRequestEnvironmentPlugin:
    def __init__(self, constants: dict, route_definition: AGWRouteDefinition, after_hooks: Dict):
        self.constants = constants
        self.route_definition = route_definition
        self.after_hooks = after_hooks

    def apply(self, callback, route):
        def wrapper(**kwargs):
            agw_route = AGWRoute(self.route_definition)
            agw_route.headers = dict(request.headers)
            agw_route.dynamic = kwargs
            agw_route.query = multiDict_to_dict(request.query)
            agw_route.text = request.body.getvalue().decode('utf-8')
            agw_route.json = request.json if request.json else None
            agw_route.data = multiDict_to_dict(request.forms)
            gre = GatewayRequestEnvironment(
                self.constants,
                agw_route,
                after_hooks=deepcopy(self.after_hooks)  # type: ignore
            )

            ll.verbose(f'headers: {agw_route.headers}')
            if len(agw_route.dynamic):
                ll.verbose(f'dynamic: {agw_route.dynamic}')
            if agw_route.query and len(agw_route.query):
                ll.verbose(f'query: {agw_route.query}')
            if agw_route.json:
                ll.verbose(f'json: {agw_route.json}')
            if agw_route.data:
                ll.verbose(f'data: {agw_route.data}')
            if agw_route.text:
                ll.verbose(f'text: {agw_route.text}')

            request.environ['gre'] = gre
            ret = callback(gre=gre, **kwargs)
            return ret
        return wrapper
