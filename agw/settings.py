import os
from typing import Callable, Optional, Any, Dict, Tuple

_SETTINGS: Dict[str, Tuple[Optional[str], bool]] = {}


class MissingEnvironmentVariableError(Exception):
    def __init__(self, variable_name: str):
        super().__init__(f'Missing or empty required environment variable: {variable_name}')


def log_settings(log_fn: Callable) -> None:
    log_fn(f'Settings:')
    for name, (value, is_secret) in _SETTINGS.items():
        logged_val = '****' if is_secret else f'"{value}"'
        log_fn(f'  * {name}: {logged_val}')


def get_required_setting(setting_name: str, secret: bool = False) -> str:
    global _SETTINGS
    var = os.getenv(f'AGW_{setting_name}')
    if not var:
        raise MissingEnvironmentVariableError(f'AGW_{setting_name}')
    _SETTINGS.setdefault(setting_name, (var, secret))
    return var


def get_setting(setting_name: str, default: Any = None, secret: bool = False) -> Any:
    global _SETTINGS
    var = os.getenv(f'AGW_{setting_name}', default=default)
    return _SETTINGS.setdefault(setting_name, (var, secret))[0]


GATEWAYS_SEARCH_PATH: str = get_required_setting('GATEWAYS_SEARCH_PATH')

LOGGING_LEVEL: str = get_setting('LOGGING_LEVEL', 'INFO')
LOGGING_COLOR: bool = True if get_setting('LOGGING_COLOR', 'true').lower() in ('true', 'y', 'yes') else False

CORS_ORIGIN_PATTERN: Optional[str] = get_setting('CORS_ORIGIN_PATTERN')

MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_OPENID_CONFIGURATION: Optional[str] = \
    get_setting('MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_OPENID_CONFIGURATION')
MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_CLIENT_ID: Optional[str] = \
    get_setting('MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_CLIENT_ID')
MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_SECRET: Optional[str] = \
    get_setting('MOP_REQUEST_TICKET_VALIDATION_IDPROVIDER_SECRET', secret=True)
MOP_REQUEST_TICKET_VALIDATION_TICKET_INTROSPECTION_ENDPOINT: Optional[str] = \
    get_setting('MOP_REQUEST_TICKET_VALIDATION_TICKET_INTROSPECTION_ENDPOINT')
