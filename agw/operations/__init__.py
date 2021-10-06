from copy import deepcopy
from typing import Dict, Any, List, Optional, Union

from plugins import InternalError
from util import EnvironmentReferenceError
from mds_logging import getLogger

ll = getLogger("agw." + __name__)


class Operation:
    def __init__(self, definition: Dict[str, Any], required_keys: Optional[List[str]] = None) -> None:
        self.definition = deepcopy(definition)
        self.required_keys = required_keys
        self.validate_definition()

    def _check_if_statement(self, environment) -> bool:
        if 'if' in self.definition:
            if_ = self.definition['if']
            try:
                environment.get(if_)
                return True
            except EnvironmentReferenceError:
                return False
        return True

    def _convert_self_key(self, key: Union[str, int], self_key: str) -> Union[str, int]:
        if not isinstance(key, str):
            return key
        parts = key.split(".")
        if parts[0] == "self":
            return f"{self_key}.{'.'.join(parts[1:])}"
        return key

    def validate_definition(self) -> None:
        if not self.required_keys:
            return
        for key in self.required_keys:
            if key not in self.definition:
                raise InternalError('Gateway configuration error',
                                    log=f"{self.__class__.__name__} definition must include a '{key}' "
                                        f"key: {self.definition}.")

    def run(self, environment, self_key: str) -> None:
        try:
            self._run(environment, self_key)
        except EnvironmentReferenceError as e:
            raise InternalError(f'Gateway route reference error (Operation)', log=str(e))

    def _run(self, environment, self_key: str) -> None:
        raise NotImplementedError()
