from typing import Optional
from unittest import TestCase

import requests
from jsonschema import validate   # type: ignore
import base64
from .environment import get_run_env_vars


def create_basic_token(client_id, client_secret):
    token_input = bytes(f'{client_id}:{client_secret}', 'utf-8')
    token = base64.b64encode(token_input).decode('ascii')
    return token


def auth(payload, token):
    v = get_run_env_vars()
    url = v['IDPMOCK'] + '/oxauth/restv1/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {token}',
        'cache-control': 'no-cache'
    }

    return requests.request('POST', url, data=payload, headers=headers, timeout=5.0)


def auth_admin():
    v = get_run_env_vars()
    payload = 'grant_type=client_credentials&scope=admin'
    auth_res = auth(payload, create_basic_token(v['ADMIN_CLIENT_ID'], v['ADMIN_SECRET']))
    return auth_res.json()['access_token']


def auth_agw(agw: int = 1):
    v = get_run_env_vars()
    client_id = v[f'AGW_CLIENT_ID_{agw}']
    secret = v[f'AGW_SECRET_{agw}']
    payload = 'grant_type=client_credentials&scope=agw'
    auth_res = auth(payload, create_basic_token(client_id, secret))
    return auth_res.json()['access_token']


def auth_organization(organization: int = 1):
    v = get_run_env_vars()
    client_id = v[f'ORGANIZATION_CLIENT_ID_{organization}']
    secret = v[f'ORGANIZATION_SECRET_{organization}']
    payload = 'grant_type=client_credentials&scope=organization'
    auth_res = auth(payload, create_basic_token(client_id, secret))
    return auth_res.json()['access_token']


def auth_wallet_user(user: int = 1):
    v = get_run_env_vars()
    username = v[f'USER_{user}_USERNAME']
    password = v[f'USER_{user}_PASSWORD']
    payload = f'grant_type=password&scope=openid+profile+wallet' \
              f'&username={username}&password={password}'
    auth_res = auth(payload, create_basic_token(v['WALLET_CLIENT_ID'], v['WALLET_CLIENT_SECRET']))
    return auth_res.json()['access_token']


def get(url, token=None, headers: dict = None):
    if token:
        if not headers:
            headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        headers['cache-control'] = 'no-cache'
    return requests.get(url, headers=headers, timeout=5.0)


def delete(url, token=None, headers: dict = None):
    if token:
        if not headers:
            headers = {}
        headers.update({
            'Authorization': f'Bearer {token}',
            'cache-control': 'no-cache',
        })
    return requests.delete(url, headers=headers, timeout=5.0)


def _build_headers(headers, json=None, text=None, data=None, token=None):
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if text:
        headers['Content-Type'] = 'application/octet-stream'
    elif data:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif json:
        headers['Content-Type'] = 'application/json'


def post(url, json=None, data=None, text=None, token=None, headers: dict = None):
    if not headers:
        headers = {}
    _build_headers(headers, json, text, data, token)
    d = text.encode('utf-8') if text else data
    return requests.request("POST", url, json=json, data=d, headers=headers, timeout=5.0)


def put(url, json=None, data=None, text=None, token=None, headers: dict = None):
    if not headers:
        headers = {}
    _build_headers(headers, json, text, data, token)
    d = text.encode('utf-8') if text else data
    return requests.request("PUT", url, json=json, data=d, headers=headers, timeout=5.0)


def patch(url, json=None, data=None, text=None, token=None, headers: dict = None):
    if not headers:
        headers = {}
    _build_headers(headers, json, text, data, token)
    d = text.encode('utf-8') if text else data
    return requests.request('PATCH', url, json=json, data=d, headers=headers, timeout=5.0)


class APITests(object):
    expected_status_code = 200
    expected_content_type = "application/json"
    expected_error: Optional[str] = None

    def assertEqual(self, a, b, c=None):  # Will be overriden
        raise NotImplementedError("SHOULD NOT BE SEEN EVER!!!")

    # def assertTrue(self, a, b, c=None):  # Will be overriden
    #    raise NotImplementedError("SHOULD NOT BE SEEN EVER!!!")

    def fail(self, a):  # Will be overriden
        raise NotImplementedError("SHOULD NOT BE SEEN EVER!!!")

    def _get_testcase(self, tc: TestCase = None):
        if tc:
            test = tc
        elif isinstance(self, TestCase):
            test = self
        else:
            raise Exception('Not subclassing TestCase, and tc parameter not given!')
        return test

    def _get_attrs_or_override(self, **kwargs):
        r = {}
        for arg in kwargs:
            if kwargs[arg] is not None:
                r[arg] = kwargs[arg]
            elif hasattr(self, arg):
                r[arg] = getattr(self, arg)
        return r

    def assertSchema(self, res, url, tc: TestCase = None):
        test = self._get_testcase(tc)
        try:
            schema = get(url).json()
            validate(instance=res.json(), schema=schema)
        except Exception as e:
            test.fail('Schema validation failed: ' + str(e))

    def test_status_code(self, res=None, expected_status_code=None, tc: TestCase = None):
        attr = self._get_attrs_or_override(res=res, expected_status_code=expected_status_code)

        status = 200
        if 'expected_status_code' in attr:
            status = attr['expected_status_code']

        test = self._get_testcase(tc)
        test.assertEqual(status, attr['res'].status_code, "REPLY: %s" % attr['res'].text)

    def test_content_type(self, res=None, expected_content_type=None, tc: TestCase = None):
        attr = self._get_attrs_or_override(res=res, expected_content_type=expected_content_type)

        ct = 'application/json'
        if 'expected_content_type' in attr:
            ct = attr['expected_content_type']

        test = self._get_testcase(tc)
        test.assertEqual(ct, attr['res'].headers['content-type'], "REPLY: %s" % attr['res'].text)

    def test_error(self, res=None, expected_error=None, tc: TestCase = None):
        attr = self._get_attrs_or_override(res=res, expected_error=expected_error)

        if 'expected_error' not in attr or not attr['expected_error']:
            return

        test = self._get_testcase(tc)
        try:
            json = attr['res'].json()
            test.assertTrue('error' in json,  "REPLY: %s" % attr['res'].text)
            test.assertEqual(attr['expected_error'], json['error'],  "REPLY: %s" % attr['res'].text)
        except ValueError as e:
            test.fail(e)

    def test_schema_validates(self, res=None, schema_path=None, tc: TestCase = None):
        attr = self._get_attrs_or_override(res=res, schema_path=schema_path, v=None)

        if hasattr(self, 'schema_path'):
            self.assertSchema(attr['res'], attr['v']['MDS'] + attr['schema_path'], tc=tc)
