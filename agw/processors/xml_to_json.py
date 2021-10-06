from typing import Dict, Any
from xmltodict import parse  # type: ignore  # hints missing...
from xml.parsers.expat import ExpatError

from mds_logging import getLogger, timed
from gateway_request_environment_plugin import GatewayRequestEnvironment
from agw_request import AGWRequestResponse
from service_exception_handler_plugin import InternalError

ll = getLogger("agw." + __name__)


class XmlToJson:
    def __init__(self, processor_definition: Dict[str, Any]) -> None:
        pass

    @timed
    def run(self, gre: GatewayRequestEnvironment, self_key: str) -> None:
        try:
            response: AGWRequestResponse = gre.get(f"{self_key}.response")
            response.json = parse(response.text)
        except ExpatError as e:
            raise InternalError(f"Error with XML response: {str(e)}")


AGW_PROCESSOR_CLASS = XmlToJson
