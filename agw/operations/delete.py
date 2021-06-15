from typing import Dict, Any

from operations import Operation


class DeleteOperation(Operation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition, ['key'])

    def _run(self, environment) -> None:
        environment.pop(self.definition['key'])
