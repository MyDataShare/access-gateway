from unittest import main

from .helpers import api, test_base


request_data_payload = {
    "teststring": "teststring value",
    "teststring2": "teststring2 value",
    "testarray": ["value1", "value2"],
    "testarray2": ["t2_value1", "t2_value2", "t2_value3", "t2_value4"]
}


class RouteDataPayloadCases:
    class RouteDataPayloadBase(test_base.TestBase):
        def test_teststring_in_json(self):
            json = self.res.json()
            arg = 'teststring'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_data_payload[arg])

        def test_teststring2_in_json(self):
            json = self.res.json()
            arg = 'teststring2'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_data_payload[arg])

        def test_request_data_payload_copied_to_response_json(self):
            json = self.res.json()
            self.assertIn('data', json)
            for key in request_data_payload.keys():
                self.assertIn(key, json['data'])
                self.assertEqual(json['data'][key], request_data_payload[key])


class TestRouteDataPayloadPost(RouteDataPayloadCases.RouteDataPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_data_payload_post',
            data=request_data_payload
        )


class TestRouteDataPayloadPut(RouteDataPayloadCases.RouteDataPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_data_payload_put',
            data=request_data_payload
        )


class TestRouteDataPayloadPatch(RouteDataPayloadCases.RouteDataPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_data_payload_patch',
            data=request_data_payload
        )


class TestRouteDataPayloadMissingKeys(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_data_payload_post',
            data={"something": "else"}
        )
        cls.expected_status_code = 500
        cls.expected_error = "internal_error"


if __name__ == '__main__':
    main()
