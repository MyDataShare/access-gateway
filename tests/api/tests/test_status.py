from unittest import main

from .helpers import api, test_base


class TestStatus(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(cls.v['AGW'] + '/status')

    def test_json_status_is_ok(self):
        json = self.res.json()
        self.assertIn('status', json)
        self.assertEqual('ok', json['status'])


if __name__ == '__main__':
    main()
