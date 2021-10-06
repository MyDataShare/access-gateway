from typing import Dict, Any

from operations import Operation
from mds_logging import getLogger

ll = getLogger("agw." + __name__)


class DeleteOperation(Operation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition, ['key'])

    def _run(self, environment, self_key: str) -> None:
        key = self._convert_self_key(self.definition['key'], self_key)

        if not self._check_if_statement(environment):
            ll.debug(f"Not deleting '{key}' as 'if' statement is false")
            return

        environment.pop(key)
