import unittest
import os

from utilities import (
    DebugConfig,
    compile_spec,
    Dict_Json,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestAnnotation(unittest.TestCase):

    def setUp(self):
        DebugConfig().swagger_only = False

    def tearDown(self):
        pass

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_dynamic_object"))
    def test_array_example_dynamic_object(self):
        result, msg = compile_spec(module_name,
                                   'array_example_dynamic_object', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_header_deps"))
    def test_header_deps(self):
        result, msg = compile_spec(module_name,
                                   'header_deps', [],
                                   "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_ordering_test"))
    def test_ordering_test(self):
        result, msg = compile_spec(module_name,
                                   'ordering_test', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_pathAnnotationInSeparateFile"))
    def test_pathAnnotationInSeparateFile(self):
        result, msg = compile_spec(module_name,
                                   'pathAnnotationInSeparateFile', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_response_headers"))
    def test_response_headers(self):
        result, msg = compile_spec(module_name,
                                   'response_headers', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_same_body_dep"))
    def test_same_body_dep(self):
        result, msg = compile_spec(module_name,
                                   'same_body_dep', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_crud_api"))
    def test_simple_crud_api(self):
        result, msg = compile_spec(module_name,
                                   'simple_crud_api', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_api_soft_delete"))
    def test_simple_api_soft_delete(self):
        result, msg = compile_spec(module_name,
                                   'simple_api_soft_delete', [Dict_Json], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()