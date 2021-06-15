from importlib import import_module
from typing import Dict, Any

from service_exception_handler_plugin import InternalError


def get_after_hook(after_hook_definition: Dict[str, Any]) -> object:
    if 'after_hook' not in after_hook_definition:
        raise InternalError(f"AfterHook definition does not include 'after_hook' key: {after_hook_definition}")
    module = after_hook_definition['after_hook']
    try:
        after_hook = import_module(module)
    except ModuleNotFoundError as e:
        raise InternalError(f"Module '{module}' not found: {e}")
    if not hasattr(after_hook, 'AGW_AFTER_HOOK_CLASS'):
        raise InternalError(f"'{module}' does not define 'AGW_AFTER_HOOK_CLASS'")
    return after_hook.AGW_AFTER_HOOK_CLASS(after_hook_definition)  # type: ignore  # already checker above
