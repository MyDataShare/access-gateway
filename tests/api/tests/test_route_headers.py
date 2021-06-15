from unittest import main
from copy import deepcopy

from .helpers import api, test_base


request_headers = {
    "Testheader": "Testheader value",
    "Test-Header-With-Dashes": "tTest-Header-With-Dashes value",
    "Anotherheader": "Anotherheader value",
    "Another-Header-With-Dashes": "Another-Header-With-Dashes value"
}


class RouteHeaderCases:
    class RouteHeaderBase(test_base.TestBase):
        def test_testheader_in_json(self):
            json = self.res.json()
            header = 'Testheader'
            self.assertIn(header, json)
            self.assertEqual(json[header], request_headers[header])

        def test_test_header_with_dash_in_json(self):
            json = self.res.json()
            header = 'Test-Header-With-Dashes'
            self.assertIn(header, json)
            self.assertEqual(json[header], request_headers[header])

        def test_request_headers_copied_to_response_headers(self):
            for key in request_headers.keys():
                self.assertIn(key, self.res.headers)
                self.assertEqual(self.res.headers[key], request_headers[key])

        def test_request_headers_copied_to_response_json(self):
            json = self.res.json()
            self.assertIn('all_headers', json)
            for key in request_headers.keys():
                self.assertIn(key, json['all_headers'])
                self.assertEqual(json['all_headers'][key], request_headers[key])


class TestRouteHeadersGet(RouteHeaderCases.RouteHeaderBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_headers_get',
            headers=deepcopy(request_headers)
        )


class TestRouteHeadersPost(RouteHeaderCases.RouteHeaderBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_headers_post',
            json={"empty": "content"},
            headers=deepcopy(request_headers)
        )


class TestRouteHeadersPut(RouteHeaderCases.RouteHeaderBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_headers_put',
            json={"empty": "content"},
            headers=deepcopy(request_headers)
        )


class TestRouteHeadersPatch(RouteHeaderCases.RouteHeaderBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_headers_patch',
            json={"empty": "content"},
            headers=deepcopy(request_headers)
        )


class TestRouteHeadersMissingHeader(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_headers_get',
            headers={"something": "else"}
        )
        cls.expected_status_code = 500
        cls.expected_error = "internal_error"


if __name__ == '__main__':
    main()
