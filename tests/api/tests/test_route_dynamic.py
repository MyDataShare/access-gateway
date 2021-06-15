from unittest import main

from .helpers import api, test_base


request_dynamic_parts = ["1337", "3.141592653589793", "dynamic_part_of_url"]
request_dynamic = "/".join(str(x) for x in request_dynamic_parts)


class RouteDynamicCases:
    class RouteDynamicBase(test_base.TestBase):
        def test_dynamicint_in_json(self):
            json = self.res.json()
            arg = 'dynamic_int'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_dynamic_parts[0])

        def test_dynamic_float_in_json(self):
            json = self.res.json()
            arg = 'dynamic_float'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_dynamic_parts[1])

        def test_dynamic_path_in_json(self):
            json = self.res.json()
            arg = 'dynamic_path'
            self.assertIn(arg, json)
            self.assertEqual(json[arg], request_dynamic_parts[2])


class TestRouteDynamicGet(RouteDynamicCases.RouteDynamicBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_dynamic_get/' + request_dynamic
        )


class TestRouteDynamicPost(RouteDynamicCases.RouteDynamicBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.post(
            cls.v['AGW'] + '/test_route_dynamic_post/' + request_dynamic,
            json={"empty": "content"}
        )


class TestRouteDynamicPut(RouteDynamicCases.RouteDynamicBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.put(
            cls.v['AGW'] + '/test_route_dynamic_put/' + request_dynamic,
            json={"empty": "content"}
        )


class TestRouteDynamicPatch(RouteDynamicCases.RouteDynamicBase, test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.patch(
            cls.v['AGW'] + '/test_route_dynamic_patch/' + request_dynamic,
            json={"empty": "content"}
        )


class TestRouteDynamicMissingArgs(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(
            cls.v['AGW'] + '/test_route_dynamic_get/1234/'
        )
        cls.expected_status_code = 404
        cls.expected_content_type = "text/html; charset=UTF-8"


if __name__ == '__main__':
    main()
