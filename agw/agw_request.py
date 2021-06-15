from dataclasses import dataclass
from typing import Dict, Union, Any, Optional, List
from copy import deepcopy

from http_method import HttpMethod


@dataclass
class AGWRequestResponse:
    status: int
    headers: Dict[str, str]
    text: str
    json: Optional[Dict[str, Union[str, Any]]] = None
    data: Optional[Dict[str, Union[str, Any]]] = None
    extra: Optional[Dict[Any, Any]] = None


@dataclass
class AGWRequestDefinition:
    url: str
    method: HttpMethod
    headers: Optional[Dict[str, str]] = None
    text: Optional[str] = None
    json: Optional[Dict[str, Union[str, Any]]] = None
    data: Optional[Dict[str, Union[str, Any]]] = None
    builders: Optional[List[Dict[str, Union[str, Any]]]] = None
    processors: Optional[List[Dict[str, Union[str, Any]]]] = None


class AGWRequest(AGWRequestDefinition):
    def __init__(self, definition: AGWRequestDefinition):
        super().__init__(
            url=definition.url,
            method=definition.method,
            headers=deepcopy(definition.headers),
            text=definition.text,
            json=deepcopy(definition.json),
            data=deepcopy(definition.data),
            builders=deepcopy(definition.builders),
            processors=deepcopy(definition.processors)
        )

        self.response: Optional[AGWRequestResponse]
