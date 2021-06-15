from importlib import import_module
from typing import Dict, Any

from operations import Operation
from plugins import InternalError


def get_builder(builder_definition: Dict[str, Any]) -> Operation:
    if 'builder' not in builder_definition:
        raise InternalError(f"Builder definition does not include 'builder' key: {builder_definition}")
    module = builder_definition['builder']
    try:
        builder = import_module(module)
    except ModuleNotFoundError as e:
        raise InternalError(f"Module '{module}' not found: {e}")
    if not hasattr(builder, 'AGW_BUILDER_CLASS'):
        raise InternalError(f"'{module}' does not define 'AGW_BUILDER_CLASS'")
    return builder.AGW_BUILDER_CLASS(builder_definition)   # type: ignore  # already checker above
