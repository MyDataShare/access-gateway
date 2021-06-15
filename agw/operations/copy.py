from typing import Dict, Any

from operations import Operation


class CopyOperation(Operation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition, ['to', 'from'])

    def _run(self, environment) -> None:
        environment.set(self.definition['to'], environment.get(self.definition['from']))
