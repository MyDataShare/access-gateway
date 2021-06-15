from copy import deepcopy
from typing import Dict, Any, List, Optional

from plugins import InternalError
from util import EnvironmentReferenceError


class Operation:
    def __init__(self, definition: Dict[str, Any], required_keys: Optional[List[str]] = None) -> None:
        self.definition = deepcopy(definition)
        self.required_keys = required_keys
        self.validate_definition()

    def validate_definition(self) -> None:
        if not self.required_keys:
            return
        for key in self.required_keys:
            if key not in self.definition:
                raise InternalError('Gateway configuration error',
                                    log=f"{self.__class__.__name__} definition must include a '{key}' "
                                        f"key: {self.definition}.")

    def run(self, environment) -> None:
        try:
            self._run(environment)
        except EnvironmentReferenceError as e:
            raise InternalError(f'Gateway route reference error', log=str(e))

    def _run(self, environment) -> None:
        raise NotImplementedError()
