from importlib import import_module
from typing import Dict, Any

from operations import Operation
from service_exception_handler_plugin import InternalError


def get_generator(generator_definition: Dict[str, Any]) -> Operation:
    if 'generator' not in generator_definition:
        raise InternalError(f"Generator definition does not include 'generator' key: {generator_definition}")
    module = generator_definition['generator']
    try:
        generator = import_module(module)
    except ModuleNotFoundError as e:
        raise InternalError(f"Module '{module}' not found: {e}")
    if not hasattr(generator, 'AGW_GENERATOR_CLASS'):
        raise InternalError(f"'{module}' does not define 'AGW_GENERATOR_CLASS'")
    return generator.AGW_GENERATOR_CLASS(generator_definition)   # type: ignore  # already checker above
