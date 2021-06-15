from abc import ABC
from typing import List, Any, Dict
from unittest import TestCase
from uuid import UUID

from .environment import get_run_env_vars


class TestBase(TestCase, ABC):
    v: Dict[str, str] = {}
    res: Any = None

    @classmethod
    def setUpClass(cls):
        cls.v = get_run_env_vars()
        cls.setup()

    @classmethod
    def setup(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def teardown(cls):
        pass

    def assertListItemsEqual(self, list1: List[Any], list2: List[Any],
                             msg: Any = ...) -> None:
        return self.assertListEqual(sorted(list1), sorted(list2), msg=msg)

    def assertSubTestEqual(self, expected_value, actual_value, msg: str) -> None:
        with self.subTest(msg):
            self.assertEqual(expected_value, actual_value, msg=msg)

    def assertEqual(self, first: Any, second: Any, msg: Any = ...):
        """Override assertEqual to allow less strict comparison of UUIDs"""
        if isinstance(first, UUID) or isinstance(second, UUID):
            return super().assertEqual(str(first), str(second), msg=msg)
        return super().assertEqual(first, second, msg=msg)
