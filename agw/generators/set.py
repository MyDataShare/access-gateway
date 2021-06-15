from typing import Dict, Any

from operations.set import SetOperation


class SetGenerator(SetOperation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition)
        del self.definition['generator']


AGW_GENERATOR_CLASS = SetGenerator
