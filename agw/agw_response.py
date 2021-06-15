from dataclasses import dataclass
from typing import Dict, Union, Any, Optional, List
from copy import deepcopy


@dataclass
class AGWResponseDefinition:
    status: Optional[int]
    headers: Optional[Dict[str, str]]
    text: Optional[str] = None
    json: Optional[Dict[str, Union[str, Any]]] = None
    data: Optional[Dict[str, Union[str, Any]]] = None
    generators: Optional[List[Dict[str, Union[str, Any]]]] = None


class AGWResponse(AGWResponseDefinition):
    def __init__(self, definition: AGWResponseDefinition):
        super().__init__(
            status=definition.status,
            headers=deepcopy(definition.headers),
            text=definition.text,
            json=deepcopy(definition.json),
            data=deepcopy(definition.data),
            generators=deepcopy(definition.generators)
        )
