from importlib import import_module
from typing import Dict, Any

from service_exception_handler_plugin import InternalError


def get_processor(processor_definition: Dict[str, Any]):
    if 'processor' not in processor_definition:
        raise InternalError(f"Processor definition does not include 'processor' key: {processor_definition}")
    module = processor_definition['processor']
    try:
        processor = import_module(module)
    except ModuleNotFoundError as e:
        raise InternalError(f"Module '{module}' not found: {e}")
    if not hasattr(processor, 'AGW_PROCESSOR_CLASS'):
        raise InternalError(f"'{module}' does not define 'AGW_PROCESSOR_CLASS'")
    return processor.AGW_PROCESSOR_CLASS(processor_definition)   # type: ignore  # already checker above
