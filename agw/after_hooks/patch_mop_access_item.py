from typing import Dict, Any, Optional
import requests

from mds_logging import getLogger, timed
from gateway_request_environment_plugin import GatewayRequestEnvironment
from service_exception_handler_plugin import InternalError
from settings import get_required_setting


ll = getLogger("agw." + __name__)


class PatchMopAccessItem:
    _SESSION = requests.session()
    _PATCH_ENDPOINT: Optional[str] = None
    _TICKET_INTROSPECTION_ENDPOINT: Optional[str] = None

    def __init__(self, after_hook_definition: Dict[str, Any]) -> None:
        self.__class__._TICKET_INTROSPECTION_ENDPOINT = get_required_setting(
            'PATCH_MOP_ACCESS_ITEM_PATCH_ENDPOINT')

    @timed
    def run(self, gre: GatewayRequestEnvironment) -> None:
        cls = self.__class__

        if 'mop_request_ticket' not in gre.route.extra:
            return
        info = gre.route.extra['mop_request_ticket']
        if 'access_item_uuid' not in info or 'agw_token' not in info:
            raise InternalError("Badly formed 'mop_request_ticket' in GatewayRequestEnvironment "
                                "'route.extra'")

        access_item_uuid = info['access_item_uuid']
        ll.debug(f"MOP access_item_uuid: {access_item_uuid}")

        agw_token = info['agw_token']

        try:
            patch_response = cls._SESSION.patch(
                f"{cls._TICKET_INTROSPECTION_ENDPOINT}/{access_item_uuid}",
                headers={'Authorization': f'bearer {agw_token}'},
                json={
                    'success': True if not gre.error else False,
                    'additional_info': "" if not gre.error else gre.error,
                    'status': 'completed'
                })
        except requests.RequestException as e:
            raise InternalError(f'Connection to MOP failed: {str(e)}')

        if patch_response.status_code != 200:
            raise InternalError(f"Patching of MOP access item failed. Status: {patch_response.status_code}, "
                                f"response: {patch_response.text}")


AGW_AFTER_HOOK_CLASS = PatchMopAccessItem
