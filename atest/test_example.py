import unittest
import os

from atest.utilities import (
    DebugConfig,
    compile_spec,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestArrayExample(unittest.TestCase):

    def setUpClass(self):
        DebugConfig().swagger_only = False

    def tearDownClass(self):
        pass

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example"))
    def test_array_example(self):
        result, msg = compile_spec(module_name,
                                   'array_example', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_body_param"))
    def test_body_param(self):
        result, msg = compile_spec(module_name,
                                   'body_param', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_exact_copy_values_are_correct"))
    def test_exact_copy_values_are_correct(self):
        result, msg = compile_spec(module_name,
                                   'exact_copy_values_are_correct', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_exampleConfigTestPut"))
    def test_exampleConfigTestPut(self):
        result, msg = compile_spec(module_name,
                                   'exampleConfigTestPut', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_optional_params"))
    def test_optional_params(self):
        result, msg = compile_spec(module_name,
                                   'optional_params', [], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()