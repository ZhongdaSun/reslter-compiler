import unittest
import os

from utilities import (
    DebugConfig,
    compile_spec,
    Dict_Json,
    Engine_Settings,
    business_config,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestDict(unittest.TestCase):

    def setUp(self):
        DebugConfig().swagger_only = False

    def tearDown(self):
        pass

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_dep_multiple_items"))
    def test_array_dep_multiple_items(self):
        result, msg = compile_spec(module_name,
                                   'array_dep_multiple_items', [Engine_Settings, "dict_0.json"], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_data_fuzz_false"))
    def test_array_example_data_fuzz_false(self):
        result, msg = compile_spec(module_name,
                                   'array_example_data_fuzz_false', [Dict_Json],
                                   "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_data_fuzz_true"))
    def test_array_example_data_fuzz_true(self):
        result, msg = compile_spec(module_name,
                                   'array_example_data_fuzz_true', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_customPayloadContentTypeSwagger_1"))
    def test_customPayloadContentTypeSwagger_1(self):
        result, msg = compile_spec(module_name,
                                   'customPayloadContentTypeSwagger_1', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_customPayloadContentTypeSwagger_2"))
    def test_customPayloadContentTypeSwagger_2(self):
        result, msg = compile_spec(module_name,
                                   'customPayloadContentTypeSwagger_2', [], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_customPayloadSwagger_1"))
    def test_customPayloadSwagger_1(self):
        result, msg = compile_spec(module_name,
                                   'customPayloadSwagger_1', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_customPayloadSwagger_2"))
    def test_customPayloadSwagger_2(self):
        result, msg = compile_spec(module_name,
                                   'customPayloadSwagger_2', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_customPayloadSwagger_3"))
    def test_customPayloadSwagger_3(self):
        result, msg = compile_spec(module_name,
                                   'customPayloadSwagger_3', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo"))
    def test_example_demo(self):
        result, msg = compile_spec(module_name,
                                   'example_demo', [Dict_Json, Engine_Settings, 'dict_0.json'], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo_yaml"))
    def test_example_demo_yaml(self):
        result, msg = compile_spec(module_name,
                                   'example_demo_yaml', [Dict_Json, "dict_0.json", Engine_Settings], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_headers"))
    def test_headers(self):
        result, msg = compile_spec(module_name,
                                   'headers', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_maindict"))
    def test_maindict(self):
        result, msg = compile_spec(module_name,
                                   'maindict', [Dict_Json, Engine_Settings, 'dict_0.json', 'dict_1.json'], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_multipleIdenticalUuidSuffix"))
    def test_multipleIdenticalUuidSuffix(self):
        result, msg = compile_spec(module_name,
                                   'multipleIdenticalUuidSuffix', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_no_params"))
    def test_no_params(self):
        result, msg = compile_spec(module_name,
                                   'no_params', [Dict_Json], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_secgroup_example"))
    def test_secgroup_example(self):
        result, msg = compile_spec(module_name,
                                   'secgroup_example', [Dict_Json, Engine_Settings], "")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_swagger_all_param_types"))
    def test_simple_swagger_all_param_types(self):
        result, msg = compile_spec(module_name,
                                   'simple_swagger_all_param_types', [Dict_Json], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
