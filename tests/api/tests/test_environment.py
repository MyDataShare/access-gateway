from unittest import main

from .helpers import api, test_base


class TestEnvironment(test_base.TestBase, api.APITests):
    @classmethod
    def setup(cls):
        cls.res = api.get(cls.v['AGW'] + '/test_environment')

    def test_environment_variable_is_accessible(self):
        json = self.res.json()
        self.assertIn('AGW_LOGGING_LEVEL', json)
        self.assertEqual('VERBOSE', json['AGW_LOGGING_LEVEL'])


if __name__ == '__main__':
    main()
