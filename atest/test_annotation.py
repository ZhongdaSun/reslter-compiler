import unittest
import os

from atest.utilities import (
    DebugConfig,
    compile_spec,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestAnnotation(unittest.TestCase):

    def setUpClass(self):
        DebugConfig().swagger_only = False

    def tearDownClass(self):
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
                                   'same_body_dep', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_crud_api"))
    def test_simple_crud_api(self):
        result, msg = compile_spec(module_name,
                                   'simple_crud_api', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_swagger_annotations"))
    def test_simple_swagger_annotations(self):
        result, msg = compile_spec(module_name,
                                   'simple_swagger_annotations', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_soft_delete"))
    def test_soft_delete(self):
        result, msg = compile_spec(module_name,
                                   'soft_delete', [], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()