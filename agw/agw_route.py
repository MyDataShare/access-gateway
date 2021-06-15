from dataclasses import dataclass
from typing import Dict, Union, List, Any, Optional
from copy import deepcopy

from http_method import HttpMethod


@dataclass
class AGWRouteDefinition:
    path: str
    method: HttpMethod
    plugins: Optional[List[Dict[str, Union[str, Any]]]] = None


class AGWRoute(AGWRouteDefinition):
    def __init__(self, definition: AGWRouteDefinition):
        super().__init__(
            path=definition.path,
            method=definition.method,
            plugins=deepcopy(definition.plugins)
        )

        self.headers: Optional[Dict[str, str]]
        self.dynamic: Optional[Dict[str, str]]
        self.query: Optional[Dict[str, str]]
        self.text: Optional[str]
        self.json: Optional[Dict[str, Union[str, Any]]]
        self.data: Optional[Dict[str, Union[str, Any]]]
        self.extra: Optional[Dict[str, Union[str, Any]]] = {}
