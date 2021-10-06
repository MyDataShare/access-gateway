from operations import Operation
from mds_logging import getLogger

ll = getLogger("agw." + __name__)


class SetOperation(Operation):
    def _run(self, environment, self_key: str) -> None:
        if not self._check_if_statement(environment):
            ll.debug(f"Not setting as 'if' statement is false")
            return

        for key, value in self.definition.items():
            environment.set(self._convert_self_key(key, self_key), self._convert_self_key(value, self_key))
