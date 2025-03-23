import unittest
import os

from utilities import (
    DebugConfig,
    compile_spec,
    Dict_Json,
    Engine_Settings,
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
                                   'array_example_external', [Dict_Json, "dict_0.json", Engine_Settings], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_object_example"))
    def test_object_example(self):
        result, msg = compile_spec(module_name,
                                   'object_example', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_in_grammar_without_dependencies"))
    def test_example_in_grammar_without_dependencies(self):
        result, msg = compile_spec(module_name,
                                   'example_without_dependencies', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_in_grammar_with_dependencies"))
    def test_example_in_grammar_with_dependencies(self):
        result, msg = compile_spec(module_name,
                                   'example_with_dependencies', [Dict_Json], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
