from unittest import main

from .helpers import api, test_base


request_json_payload = {
    "teststring": "teststring value",
    "teststring2": "teststring2 value",
    "testarray": ["value1", "value2"],
    "testarray2": ["t2_value1", "t2_value2", "t2_value3", "t2_value4"],
    "testdict": {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }
}


class RouteJsonPayloadCases:
    class RouteJsonPayloadBase(test_base.TestBase):
        def test_teststring_in_json(self):
            json = self.res.json()
            arg = 'teststring'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_json_payload[arg])

        def test_teststring2_in_json(self):
            json = self.res.json()
            arg = 'teststring2'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_json_payload[arg])

        def test_request_json_payload_copied_to_response_json(self):
            json = self.res.json()
            self.assertIn('json', json)
            for key in request_json_payload.keys():
                self.assertIn(key, json['json'])
                self.assertEqual(json['json'][key], request_json_payload[key])


class TestRouteJsonPayloadPost(RouteJsonPayloadCases.RouteJsonPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_json_payload_post',
            json=request_json_payload
        )


class TestRouteJsonPayloadPut(RouteJsonPayloadCases.RouteJsonPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_json_payload_put',
            json=request_json_payload
        )


class TestRouteJsonPayloadPatch(RouteJsonPayloadCases.RouteJsonPayloadBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_json_payload_patch',
            json=request_json_payload
        )


class TestRouteJsonPayloadMissingKeys(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_json_payload_post',
            json={"something": "else"}
        )
        cls.expected_status_code = 500
        cls.expected_error = "internal_error"


if __name__ == '__main__':
    main()
