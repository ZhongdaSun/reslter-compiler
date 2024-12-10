import unittest
import os

from atest.utilities import (
    DebugConfig,
    compile_spec,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestExampleConfigTestPut(unittest.TestCase):

    def setUp(self):
        DebugConfig().swagger_only = False

    def tearDown(self):
        pass

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_external"))
    def test_array_example_external(self):
        result, msg = compile_spec(module_name,
                                   'array_example_external', [], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
