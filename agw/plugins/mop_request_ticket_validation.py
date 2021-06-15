from typing import Optional, Dict, Any

import json
import bottle
import requests
from jwcrypto import jwk, jwt, jws  # type: ignore

from gateway_request_environment_plugin import GatewayRequestEnvironment
from service_exception_handler_plugin import AuthorizationError, ForbiddenError, InternalError, BadRequestError
from mds_logging import getLogger, timed
from settings import get_required_setting

ll = getLogger("agw." + __name__)


def get_setting(key: str) -> str:
    return get_required_setting(f'MOP_REQUEST_TICKET_VALIDATION_{key}')


class MopRequestTicketValidationPlugin:
    _SESSION = requests.session()
    _TOKEN_ENDPOINT: Optional[str] = None
    _AGW_TOKEN: Optional[str] = None
    _IDPROVIDER_OPENID_CONFIGURATION: Optional[str] = None
    _IDPROVIDER_CLIENT_ID: Optional[str] = None
    _IDPROVIDER_SECRET: Optional[str] = None
    _TICKET_INTROSPECTION_ENDPOINT: Optional[str] = None
    _JWKS_ENDPOINT: Optional[str] = None
    _KID: Optional[str] = None
    _EXP_LEEWAY_SECONDS = 60
    _ISS: Optional[str] = None
    _PUBLIC_KEY: Optional[jwk.JWK] = None

    def __init__(self, plugin_definition: Dict[str, Any]):
        self.__class__._IDPROVIDER_OPENID_CONFIGURATION = get_setting('IDPROVIDER_OPENID_CONFIGURATION')
        self.__class__._IDPROVIDER_CLIENT_ID = get_setting('IDPROVIDER_CLIENT_ID')
        self.__class__._IDPROVIDER_SECRET = get_setting('IDPROVIDER_SECRET')
        self.__class__._TICKET_INTROSPECTION_ENDPOINT = get_setting('TICKET_INTROSPECTION_ENDPOINT')
        self.__class__._JWKS_ENDPOINT = get_setting('PUBLIC_SIGNATURE_JWKS_ENDPOINT')
        self.__class__._KID = get_setting('PUBLIC_SIGNATURE_KID')
        self.__class__._ISS = get_setting('ISS')
        self.__class__._EXP_LEEWAY_SECONDS = int(get_setting('PUBLIC_SIGNATURE_EXP_LEEWAY_SECONDS'))
        self.plugin_definition = plugin_definition

    @classmethod
    @timed
    def _fetch_and_parse_openid_configuration(cls):
        try:
            ll.info(f"Fetching openid configuration from '{cls._IDPROVIDER_OPENID_CONFIGURATION}'")
            r = requests.get(str(cls._IDPROVIDER_OPENID_CONFIGURATION))
            r.raise_for_status()
            open_id_config = r.json()
            cls._TOKEN_ENDPOINT = open_id_config['token_endpoint']
        except (ConnectionRefusedError, requests.RequestException) as e:
            raise InternalError(f"Couldn't connect to IDP openid-configuration endpoint: {e}")
        except (KeyError, ValueError) as e:
            raise InternalError(f"Error parsing OpenId configuration: {e}")

    @classmethod
    @timed
    def _get_agw_token(cls):
        if not cls._TOKEN_ENDPOINT:
            cls._fetch_and_parse_openid_configuration()

        try:
            token_response = cls._SESSION.post(
                str(cls._TOKEN_ENDPOINT),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                auth=requests.auth.HTTPBasicAuth(cls._IDPROVIDER_CLIENT_ID, cls._IDPROVIDER_SECRET),
                data="grant_type=client_credentials&scope=agw"
            )
            ll.debug(f'Token endpoint response status={token_response.status_code}, '
                     f'content={str(token_response.content)}')
            token_response.raise_for_status()
            json_response = token_response.json()
            if 'access_token' not in json_response:
                raise InternalError('access_token is not present in token endpoint response')
            cls._AGW_TOKEN = json_response['access_token']
        except requests.RequestException as e:
            raise InternalError(f'Cannot get AGW token: {e}')
        except ValueError:
            raise InternalError(f'Did not receive JSON response from token endpoint')

    @classmethod
    @timed
    def _get_public_key(cls):
        try:
            jwks_response = cls._SESSION.get(str(cls._JWKS_ENDPOINT))
            jwks_response.raise_for_status()
            jwkset = jwk.JWKSet.from_json(jwks_response.text)
            sign_keys = jwkset.get_key(cls._KID)
            cls._PUBLIC_KEY = jwk.JWK()
            cls._PUBLIC_KEY.import_key(**sign_keys.export_public(as_dict=True))
        except requests.RequestException as e:
            raise InternalError(f'Cannot get JWKS: {e}')

    def apply(self, callback, route):
        def wrapper(gre: GatewayRequestEnvironment, **kwargs):
            request_ticket = self._get_request_ticket_from_headers(bottle.request.headers)
            self._validate_request_ticket(request_ticket, gre)
            return callback(gre, **kwargs)

        return wrapper

    def _get_request_ticket_from_headers(self, headers) -> str:
        """
        Gets request ticket from headers dict.

        :param headers: dict-like object with headers of the HTTP request
        :raises AuthorizationError: If reading the ticket fails
        :return: The request ticket
        """
        # Header has to be present in the form "Authorization: Bearer token"
        if 'MyDataShare-Request-Ticket' not in headers:
            raise AuthorizationError('MyDataShare-Request-Ticket field was missing in the HTTP headers.')

        return headers['MyDataShare-Request-Ticket']

    def _generate_route_extra(self, json_response: Dict):
        cls = self.__class__
        ret = {
            'access_item_uuid': json_response['access_item_uuid'],
            'agw_token': cls._AGW_TOKEN,
        }
        if 'identifiers' in json_response:
            ret['identifiers'] = {}
            for identifier in json_response['identifiers']:
                if 'id_type' not in identifier:
                    raise InternalError(f'IdType missing in identifier returned by request_ticket intropection')

                if identifier['id_type'] == 'ssn':
                    if 'country' not in identifier:
                        raise InternalError(f'Country missing in identifier returned by request_ticket intropection')
                    country = identifier['country']
                    if 'ssn' not in ret['identifiers']:
                        ret['identifiers']['ssn'] = {}
                    if country in ret['identifiers']['ssn']:
                        ll.warning(f"Multiple {country}-ssn pairs detected. Only picking the first one.")
                        continue
                    ret['identifiers']['ssn'][country] = identifier['id']

                elif identifier['id_type'] == 'email':
                    if 'email' not in ret['identifiers']:
                        ret['identifiers']['email'] = []
                    ret['identifiers']['email'].append(identifier['id'])

                elif identifier['id_type'] == 'pairwise':
                    if 'pairwise' in ret['identifiers']:
                        ll.warning(f"Multiple pairwises detected. Only picking the first one.")
                        continue
                    ret['identifiers']['pairwise'] = identifier['id']

                elif identifier['id_type'] == 'phone_number':
                    if 'phone_number' not in ret['identifiers']:
                        ret['identifiers']['phone_number'] = []
                    ret['identifiers']['phone_number'].append(identifier['id'])

        return ret

    def _verify_request_ticket_signature(self, request_ticket: str) -> Dict:
        """
        Verifies the request ticket signature

        :param request_ticket: Request ticket to be validated
        :raises BadRequestError: If signature is invalid or claims cannot be read
        :raises InternalError: If connection to the JWKS enpoint fails
        :return: Request ticket claims
        """
        cls = self.__class__
        if not cls._PUBLIC_KEY:
            cls._get_public_key()

        token = jwt.JWT()
        token.leeway = cls._EXP_LEEWAY_SECONDS
        try:
            token.deserialize(request_ticket, cls._PUBLIC_KEY)
            return json.loads(token.claims)
        except jws.InvalidJWSSignature as e:
            raise BadRequestError(f'Invalid signature: {str(e)}')
        except json.decoder.JSONDecodeError as e:
            raise BadRequestError(f'Error decoding JWT claims: {str(e)}')

    def _verify_route(self, claims: Dict, gre: GatewayRequestEnvironment):
        """
        Verifies the request ticket and route matches

        :param claims: Request ticket claims
        :raises ForbiddenError: If curent route and request ticket aud do not match
        """
        if 'aud' not in claims:
            raise BadRequestError('aud claim missing.')

        request_url_parts = bottle.request.url.split('/')
        request_url_prefix = '/'.join(request_url_parts[0:3])
        request_url_path = '/' + '/'.join(request_url_parts[3:])

        aud = ''
        if 'aud' in self.plugin_definition:
            aud = self.plugin_definition['aud']
        else:
            aud = request_url_prefix
            for i in range(0, len(request_url_path)):
                if i < len(gre.route.path) and request_url_path[i] == gre.route.path[i]:
                    aud += request_url_path[i]
                else:
                    break
            aud = aud.rstrip('/')

        ll.debug(f"Ticket aud: '{claims['aud']}', request aud: '{aud}'")

        if claims['aud'] != aud:
            raise ForbiddenError(f"Wrong audience. Expecting '{aud}' but got '{claims['aud']}'.")

    @timed
    def _introspect_request_ticket(self, request_ticket: str, gre: GatewayRequestEnvironment):
        """
        Introspects the request ticket with MOP

        :param request_ticket: Request ticket to be validated
        :raises AuthorizationError: With error information, if the validation fails
        :raises InternalError: If connection to the authentication server fails
        :raises BadRequestError: If request ticket is not active but we did not receive a reason.
        """

        cls = self.__class__
        if not cls._AGW_TOKEN:
            cls._get_agw_token()

        max_tries = 3
        try_count = 1
        while try_count <= max_tries:
            try_count += 1
            try:
                introspection_response = cls._SESSION.post(
                    str(cls._TICKET_INTROSPECTION_ENDPOINT),
                    headers={'Authorization': f'bearer {cls._AGW_TOKEN}'},
                    json={'request_ticket': request_ticket})
            except requests.RequestException as e:
                raise InternalError(f'Connection to MOP failed: {str(e)}')

            if introspection_response.status_code == 200:
                try:
                    json_response = introspection_response.json()
                except ValueError:
                    raise InternalError('IdProvider response is not valid JSON')
                if json_response.get('active') is not True:
                    err = "Request ticket is not active or valid."
                    if 'reason' in json_response:
                        err += f" Reason: '{json_response['reason']}'"
                    raise BadRequestError(err)
                else:
                    if 'access_item_uuid' in json_response:
                        gre.route.extra['mop_request_ticket_validation'] = self._generate_route_extra(json_response)
                    else:
                        ll.warning("access_item_uuid missing from introspection response")
                    return
            if introspection_response.status_code == 401:
                # TODO: It seems we get other errors here too.... Handle those...
                ll.info(f"AGW token has expired: {introspection_response.text}")
                if try_count <= max_tries:
                    cls._get_agw_token()
            else:
                raise InternalError("Introspection response has unknown status code: "
                                    f"{introspection_response.status_code}, response: {introspection_response.text}")
        raise InternalError("Could not validate request ticket")

    @timed
    def _validate_request_ticket(self, request_ticket: str, gre: GatewayRequestEnvironment):
        """
        Verifies and introspects the request ticket

        :param request_ticket: Request ticket to be validated
        :raises AuthorizationError: With error information, if the validation fails
        :raises ForbiddenError: If curent route and request ticket aud do not match
        :raises InternalError: If connection to the authentication server fails
        :raises BadRequestError: If request ticket is not active but we did not receive a reason or if signature is
                                 invalid or claims cannot be read
        """
        cls = self.__class__
        claims = self._verify_request_ticket_signature(request_ticket)
        if cls._ISS != claims['iss']:
            raise AuthorizationError(f"Bad issuer. Expected '{cls._ISS}' but got '{claims['iss']}'")
        self._verify_route(claims, gre)
        self._introspect_request_ticket(request_ticket, gre)


AGW_PLUGIN_CLASS = MopRequestTicketValidationPlugin
