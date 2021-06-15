from importlib import import_module
from typing import Dict, Any

from service_exception_handler_plugin import InternalError


def get_plugin(plugin_definition: Dict[str, Any]) -> object:
    if 'plugin' not in plugin_definition:
        raise InternalError(f"Plugin definition does not include 'plugin' key: {plugin_definition}")
    module = plugin_definition['plugin']
    try:
        plugin = import_module(module)
    except ModuleNotFoundError as e:
        raise InternalError(f"Module '{module}' not found: {e}")
    if not hasattr(plugin, 'AGW_PLUGIN_CLASS'):
        raise InternalError(f"'{module}' does not define 'AGW_PLUGIN_CLASS'")
    return plugin.AGW_PLUGIN_CLASS(plugin_definition)   # type: ignore  # already checker above
