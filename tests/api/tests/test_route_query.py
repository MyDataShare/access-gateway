from unittest import main
from urllib.parse import urlencode

from .helpers import api, test_base


request_query_params = {
    "testquery": "testquery value",
    "testquery2": "testquery2 value",
    "testarray": ["value1", "value2"],
    "testarray2": ["t2_value1", "t2_value2", "t2_value3", "t2_value4"]
}


class RouteQueryCases:
    class RouteQueryBase(test_base.TestBase):
        def test_testquery_in_json(self):
            json = self.res.json()
            arg = 'testquery'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_query_params[arg])

        def test_testquery2_in_json(self):
            json = self.res.json()
            arg = 'testquery2'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_query_params[arg])

        def test_request_query_copied_to_response_json(self):
            json = self.res.json()
            self.assertIn('query', json)
            for key in request_query_params.keys():
                self.assertIn(key, json['query'])
                self.assertEqual(json['query'][key], request_query_params[key])


class TestRouteQueryGet(RouteQueryCases.RouteQueryBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_query_get?' + urlencode(request_query_params, True)
        )


class TestRouteQueryPost(RouteQueryCases.RouteQueryBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_query_post?' + urlencode(request_query_params, True),
            json={"empty": "content"}
        )


class TestRouteQueryPut(RouteQueryCases.RouteQueryBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_query_put?' + urlencode(request_query_params, True),
            json={"empty": "content"}
        )


class TestRouteQueryPatch(RouteQueryCases.RouteQueryBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_query_patch?' + urlencode(request_query_params, True),
            json={"empty": "content"}
        )


class TestRouteQueryMissingArgs(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_query_get'
        )
        cls.expected_status_code = 500
        cls.expected_error = "internal_error"


class TestRouteQueryArrayWhenExpectingString(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_query_get?testquery=a&testquery2=b&testquery=c'
        )
        cls.expected_status_code = 500
        cls.expected_error = "internal_error"


if __name__ == '__main__':
    main()
