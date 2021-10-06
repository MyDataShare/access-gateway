from typing import Dict, Any

from operations import Operation
from mds_logging import getLogger

ll = getLogger("agw." + __name__)


class CopyOperation(Operation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition, ['to', 'from'])

    def _run(self, environment, self_key: str) -> None:
        from_ = self._convert_self_key(self.definition['from'], self_key)
        to_ = self._convert_self_key(self.definition['to'], self_key)

        if not self._check_if_statement(environment):
            ll.debug(f"Not copying from: '{from_}' to: '{to_}' as 'if' statement is false")
            return

        environment.set(to_, environment.get(from_))
