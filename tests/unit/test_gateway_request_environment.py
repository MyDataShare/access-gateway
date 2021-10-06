from unittest import TestCase, main

from .context import agw_request
from .context import agw_response
from .context import agw_route

from .context import EnvironmentReferenceError
from .context import GatewayRequestEnvironment

REQUEST_DEF_1 = {
    'url': 'test_agw_request_1_url',
    'method': 'POST',
    'json': {
        'test_agw_request_1_json_val_str': 'a string',
        'test_agw_request_1_json_val_int': 2,
        'test_agw_request_1_json_val_float': 2.0,
        'test_agw_request_1_json_val_none': None,
        'test_agw_request_1_json_val_list': ['a', 'b', 'c'],
        'test_agw_request_1_json_val_dict': {
            'a': 1,
            'b': 2,
            'c': [3, 4]
        },
    }
}

REQUEST_DEF_2 = {
    'url': 'test_agw_request_2_url',
    'method': 'GET',
    'json': {
        'test_agw_request_2_json_val_str': 'a string',
        'test_agw_request_2_json_val_int': 3,
        'test_agw_request_2_json_val_float': 3.0,
        'test_agw_request_2_json_val_none': None,
    }
}

RESPONSE_DEF = {
    'status': 200,
    'headers': None,
    'json': {
        'test_agw_response_json_val_str': 'string',
        'test_agw_response_json_val_int': 1,
        'test_agw_response_json_val_float': 1.0,
        'test_agw_response_json_val_none': None,
        'test_agw_response_json_val_list': ['a', 'b', 'c'],
        'test_agw_response_json_val_dict': {
            'a': 1,
            'b': 2,
            'c': [3, 4]
        },
    }
}

ROUTE_DEF = {
    'path': '/agw/some/path',
    'method': 'GET',
}


class TestGetFromRequest(TestCase):
    def setUp(self):
        self.agw_route = agw_route.AGWRoute(agw_route.AGWRouteDefinition(**ROUTE_DEF))
        self.agw_request_1 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_1))
        self.agw_request_2 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_2))
        self.agw_response = agw_response.AGWResponse(agw_response.AGWResponseDefinition(**RESPONSE_DEF))
        self.gre = GatewayRequestEnvironment({}, self.agw_route, requests=[self.agw_request_1, self.agw_request_2],
                                             response=self.agw_response)

    def test_top_level_first(self):
        self.assertEqual('POST', self.gre.get('requests[0].method'))

    def test_top_level_index(self):
        self.assertEqual('GET', self.gre.get('requests[1].method'))

    def test_json_string(self):
        self.assertEqual('a string', self.gre.get('requests[0].json.test_agw_request_1_json_val_str'))

    def test_json_int(self):
        self.assertEqual(2, self.gre.get('requests[0].json.test_agw_request_1_json_val_int'))

    def test_json_float(self):
        self.assertEqual(2.0, self.gre.get('requests[0].json.test_agw_request_1_json_val_float'))

    def test_json_none(self):
        self.assertEqual(None, self.gre.get('requests[0].json.test_agw_request_1_json_val_none'))

    def test_json_list_first(self):
        self.assertEqual('a', self.gre.get('requests[0].json.test_agw_request_1_json_val_list[0]'))

    def test_json_list_last(self):
        self.assertEqual('c', self.gre.get('requests[0].json.test_agw_request_1_json_val_list[2]'))

    def test_json_dict_key(self):
        self.assertEqual(1, self.gre.get('requests[0].json.test_agw_request_1_json_val_dict.a'))

    def test_json_dict_key_list(self):
        self.assertEqual(4, self.gre.get('requests[0].json.test_agw_request_1_json_val_dict.c[1]'))

    def test_not_found_top_level_list(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.get('requests[2].does_not_exist')

    def test_not_found_top_level(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.get('requests[0].does_not_exist')

    def test_not_found_json_top_level(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.get('requests[0].json.does_not_exist')

    def test_not_found_json_list(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.get('requests[0].json.test_agw_request_1_json_val_list[3]')

    def test_not_found_dict_key(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.get('requests[0].json.test_agw_request_1_json_val_dict.d')


class TestSetToResponse(TestCase):
    def setUp(self):
        self.agw_route = agw_route.AGWRoute(agw_route.AGWRouteDefinition(**ROUTE_DEF))
        self.agw_request_1 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_1))
        self.agw_request_2 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_2))
        self.agw_response = agw_response.AGWResponse(agw_response.AGWResponseDefinition(**RESPONSE_DEF))
        self.gre = GatewayRequestEnvironment({}, self.agw_route, requests=[self.agw_request_1, self.agw_request_2],
                                             response=self.agw_response)

    def test_set_top_level(self):
        self.gre.set('response.status', 401)
        self.assertEqual(401, self.gre.response.status)

    def test_set_list(self):
        self.gre.set('response.json.test_agw_response_json_val_list[1]', 'ö')
        self.assertEqual('ö', self.gre.response.json['test_agw_response_json_val_list'][1])

    def test_set_list_value(self):
        self.gre.set('response.json.test_agw_response_json_val_list[1]', ['ö'])
        self.assertEqual(['ö'], self.gre.response.json['test_agw_response_json_val_list'][1])

    def test_set_json_key(self):
        self.gre.set('response.json.test_agw_response_json_val_dict.a', 'new a')
        self.assertEqual('new a', self.gre.response.json['test_agw_response_json_val_dict']['a'])

    def test_set_json_key_list(self):
        self.gre.set('response.json.test_agw_response_json_val_dict.c[1]', 'new c 1')
        self.assertEqual('new c 1', self.gre.response.json['test_agw_response_json_val_dict']['c'][1])

    def test_set_json_key_new_path(self):
        self.gre.set('response.json.test_agw_response_json_val_dict.d.new_key', 'new value')
        self.assertEqual('new value', self.gre.response.json['test_agw_response_json_val_dict']['d']['new_key'])

    def test_set_fails_with_missing_list(self):
        with self.assertRaises(EnvironmentReferenceError):
            self.gre.set('response.json.test_agw_response_json_val_dict.f[0]', 'new value')


class TestPopFromResponse(TestCase):
    def setUp(self):
        self.agw_route = agw_route.AGWRoute(agw_route.AGWRouteDefinition(**ROUTE_DEF))
        self.agw_request_1 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_1))
        self.agw_request_2 = agw_request.AGWRequest(agw_request.AGWRequestDefinition(**REQUEST_DEF_2))
        self.agw_response = agw_response.AGWResponse(agw_response.AGWResponseDefinition(**RESPONSE_DEF))
        self.gre = GatewayRequestEnvironment({}, self.agw_route, requests=[self.agw_request_1, self.agw_request_2],
                                             response=self.agw_response)

    def test_list(self):
        value = self.gre.pop('response.json.test_agw_response_json_val_list[1]')
        self.assertEqual('b', value)
        self.assertEqual(['a', 'c'], self.agw_response.json['test_agw_response_json_val_list'])

    def test_dict_key(self):
        value = self.gre.pop('response.json.test_agw_response_json_val_dict.a')
        self.assertEqual(1, value)
        self.assertEqual({'b': 2, 'c': [3, 4]}, self.agw_response.json['test_agw_response_json_val_dict'])

    def test_dict_key_list(self):
        value = self.gre.pop('response.json.test_agw_response_json_val_dict.c[0]')
        self.assertEqual(3, value)
        self.assertEqual({'a': 1, 'b': 2, 'c': [4]}, self.agw_response.json['test_agw_response_json_val_dict'])


if __name__ == '__main__':
    main()
