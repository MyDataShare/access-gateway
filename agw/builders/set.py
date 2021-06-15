from typing import Dict, Any

from operations.set import SetOperation


class SetBuilder(SetOperation):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition)
        del self.definition['builder']


AGW_BUILDER_CLASS = SetBuilder
