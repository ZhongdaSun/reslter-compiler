import unittest
import os

from atest.utilities import (
    DebugConfig,
    compile_spec,
    Dict_Json,
    Engine_Settings,
    business_config,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestSwaggerOnly(unittest.TestCase):

    def setUp(self):
        DebugConfig().swagger_only = True

    def tearDown(self):
        DebugConfig().swagger_only = False
        DebugConfig().skip_python_check = DebugConfig().get_skip_python()
        business_config["JsonPropertyMaxDepth"] = None

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_circular_path"))
    def test_circular_path(self):
        result, msg = compile_spec(module_name,
                                   'circular_path', [], "circular_path.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_subnet_id"))
    def test_subnet_id(self):
        result, msg = compile_spec(module_name,
                                   'subnet_id', [], "subnet_id.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inline_examples"))
    def test_inline_examples(self):
        result, msg = compile_spec(module_name,
                                   'inline_examples', [], "inline_examples.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation"))
    def test_path_annotation(self):
        result, msg = compile_spec(module_name,
                                   'path_annotation', [], "pathAnnotation.json")
        self.assertTrue(result, msg=msg)

    # block by test_inconsistent_camel_case_fixed_by_restler
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_frontend_port_id"))
    def test_frontend_port_id(self):
        result, msg = compile_spec(module_name,
                                   'frontend_port_id', [],
                                   "frontend_port_id.json")
        self.assertTrue(result, msg=msg)

    # block by test_inconsistent_camel_case_fixed_by_restler
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inconsistent_casing_paths"))
    def test_inconsistent_casing_paths(self):
        result, msg = compile_spec(module_name,
                                   'inconsistent_casing_paths', [], "inconsistent_casing_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_ip_configurations_get"))
    def test_ip_configurations_get(self):
        result, msg = compile_spec(module_name,
                                   'ip_configurations_get', [], "ip_configurations_get.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_multiple_circular_paths"))
    def test_multiple_circular_paths(self):
        result, msg = compile_spec(module_name,
                                   'multiple_circular_paths', [], "multiple_circular_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_nested_objects_naming"))
    def test_nested_objects_naming(self):
        result, msg = compile_spec(module_name,
                                   'nested_objects_naming', [Dict_Json], "nested_objects_naming.json")
        self.assertTrue(result, msg=msg)

    # block by test_patch_request_body_parameter_producers_from_post
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_post_patch_dependency"))
    def test_post_patch_dependency(self):
        result, msg = compile_spec(module_name,
                                   'post_patch_dependency', [], "post_patch_dependency.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_put_createorupdate"))
    def test_put_createorupdate(self):
        result, msg = compile_spec(module_name,
                                   'put_createorupdate', [Dict_Json],
                                   "put_createorupdate.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_put_createorupdate_engine"))
    def test_put_createorupdate_engine(self):
        result, msg = compile_spec(module_name,
                                   'put_createorupdate', [Engine_Settings],
                                   "put_createorupdate.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body"))
    def test_large_json_body(self):
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_1"))
    def test_large_json_body_level_1(self):
        business_config["JsonPropertyMaxDepth"] = 1
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_1") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_1', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_2"))
    def test_large_json_body_level_2(self):
        business_config["JsonPropertyMaxDepth"] = 2
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_2") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_2', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_3"))
    def test_large_json_body_level_3(self):
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_3") == 20:
            DebugConfig().skip_python_check = True
        business_config["JsonPropertyMaxDepth"] = 3
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_3', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_4"))
    def test_large_json_body_level_4(self):
        business_config["JsonPropertyMaxDepth"] = 4
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_4") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_4', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_5"))
    def test_large_json_body_level_5(self):
        business_config["JsonPropertyMaxDepth"] = 5
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_5") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_5', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_6"))
    def test_large_json_body_level_6(self):
        business_config["JsonPropertyMaxDepth"] = 6
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_6") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_6', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_7"))
    def test_large_json_body_level_7(self):
        business_config["JsonPropertyMaxDepth"] = 7
        if DebugConfig().get_test_func_config(module_name, "test_large_json_body_level_7") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'large_json_body_level_7', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_read_only"))
    def test_read_only(self):
        result, msg = compile_spec(module_name,
                                   'readonly_test', [], "readonly_test.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_lowercase_paths"))
    def test_lowercase_paths(self):
        result, msg = compile_spec(module_name,
                                   'lowercase_paths', [Dict_Json], "lowercase_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation_in_separate_file"))
    def test_path_annotation_in_separate_file(self):
        result, msg = compile_spec(module_name,
                                   'path_annotation_in_separate', [], "pathAnnotationInSeparate.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_local_annotations"))
    def test_local_annotations(self):
        result, msg = compile_spec(module_name,
                                   'local_annotations', [], "localAnnotations.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_body_dependency_cycles"))
    def test_body_dependency_cycles(self):
        result, msg = compile_spec(module_name,
                                   'body_dependency_cycles', [], "body_dependency_cycles.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_object_example"))
    def test_object_example(self):
        result, msg = compile_spec(module_name,
                                   'object_example', [], "object_example.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_null_test_swagger"))
    def test_null_test_swagger(self):
        temp = business_config["DataFuzzing"]
        business_config["DataFuzzing"] = True
        result, msg = compile_spec(module_name,
                                   'null_test_swagger', [], "null_test_swagger.json")
        self.assertTrue(result, msg=msg)
        business_config["DataFuzzing"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_no_params"))
    def test_no_params(self):
        result, msg = compile_spec(module_name,
                                   'no_params', [], "no_params.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_swagger"))
    def test_custom_payload_swagger(self):
        result, msg = compile_spec(module_name,
                                   'custom_payload_swagger', [],
                                   "customPayloadSwagger.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_content_type_swagger"))
    def test_custom_payload_content_type_swagger(self):
        result, msg = compile_spec(module_name,
                                   'custom_payload_content_type_swagger', [],
                                   "customPayloadContentTypeSwagger.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example"))
    def test_array_example(self):
        temp = business_config["DataFuzzing"]
        business_config["DataFuzzing"] = True
        result, msg = compile_spec(module_name,
                                   'array_example', [],
                                   "array_example.json")
        self.assertTrue(result, msg=msg)
        business_config["DataFuzzing"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_empty_array_example"))
    def test_empty_array_example(self):
        result, msg = compile_spec(module_name,
                                   'empty_array_example', [],
                                   "empty_array_example.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_required_params_include_optional_parameters"))
    def test_required_params_include_optional_parameters(self):
        temp = business_config["IncludeOptionalParameters"]
        business_config["IncludeOptionalParameters"] = True
        result, msg = compile_spec(module_name,
                                   'required_params_include_optional_parameters', [],
                                   "required_params.json")
        self.assertTrue(result, msg=msg)
        business_config["IncludeOptionalParameters"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_required_params_not_include_optional_parameters"))
    def test_required_params_not_include_optional_parameters(self):
        temp = business_config["IncludeOptionalParameters"]
        business_config["IncludeOptionalParameters"] = False
        result, msg = compile_spec(module_name,
                                   'required_params_not_include_optional_parameters', [],
                                   "required_params.json")
        self.assertTrue(result, msg=msg)
        business_config["IncludeOptionalParameters"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_global_path_parameters"))
    def test_global_path_parameters(self):
        result, msg = compile_spec(module_name,
                                   'global_path_parameters', [],
                                   "global_path_parameters.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_global_path_parameters_engine"))
    def test_global_path_parameters_engine(self):
        result, msg = compile_spec(module_name,
                                   'global_path_parameters', [Engine_Settings, Dict_Json],
                                   "global_path_parameters.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo"))
    def test_example_demo(self):
        if DebugConfig().get_test_func_config(module_name, "test_example_demo") == 20:
            DebugConfig().skip_python_check = True
        result, msg = compile_spec(module_name,
                                   'example_demo', [],
                                   "example_demo.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_dep_multiple_items"))
    def test_array_dep_multiple_items(self):
        result, msg = compile_spec(module_name,
                                   'array_dep_multiple_items', [],
                                   "array_dep_multiple_items.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_path_dependencies"))
    def test_get_path_dependencies(self):
        result, msg = compile_spec(module_name,
                                   'get_path_dependencies', [],
                                   "get_path_dependencies.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation_in_separate_file"))
    def test_path_annotation_in_separate_file(self):
        result, msg = compile_spec(module_name,
                                   'path_annotation_in_separate_file', [],
                                   "pathAnnotationInSeparateFile.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_dictionary_payload"))
    def test_path_dictionary_payload(self):
        result, msg = compile_spec(module_name,
                                   'path_dictionary_payload', [],
                                   "pathDictionaryPayload.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_swagger_all_param_data_types"))
    def test_simple_swagger_all_param_data_types(self):
        result, msg = compile_spec(module_name,
                                   'simple_swagger_all_param_data_types', [],
                                   "simple_swagger_all_param_data_types.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_uuidsuffix_test"))
    def test_uuidsuffix_test(self):
        result, msg = compile_spec(module_name,
                                   'uuidsuffix_test', [],
                                   "uuidsuffix_test.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_input_producer_spec"))
    def test_input_producer_spec(self):
        result, msg = compile_spec(module_name,
                                   'input_producer_spec', [Dict_Json],
                                   "input_producer_spec.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_api_soft_delete"))
    def test_simple_api_soft_delete(self):
        result, msg = compile_spec(module_name,
                                   'simple_api_soft_delete', [Dict_Json],
                                   "simple_api_soft_delete.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_ordering_test"))
    def test_ordering_test(self):
        result, msg = compile_spec(module_name,
                                   'ordering_test', [], "ordering_test.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_response_headers"))
    def test_response_headers(self):
        result, msg = compile_spec(module_name,
                                   'response_headers', [], "response_headers.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_same_body_dep"))
    def test_same_body_dep(self):
        result, msg = compile_spec(module_name,
                                   'same_body_dep', [], "same_body_dep.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_secgroup_example"))
    def test_secgroup_example(self):
        result, msg = compile_spec(module_name,
                                   'secgroup_example', [], "secgroup_example.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_multipleIdenticalUuidSuffix"))
    def test_multipleIdenticalUuidSuffix(self):
        result, msg = compile_spec(module_name,
                                   'multipleIdenticalUuidSuffix', [], "multipleIdenticalUuidSuffix.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo_yaml"))
    def test_example_demo_yaml(self):
        result, msg = compile_spec(module_name,
                                   'example_demo_yaml', [], "example_demo.yaml")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo_1"))
    def test_example_demo_1(self):
        result, msg = compile_spec(module_name,
                                   'example_demo_1', [], "example_demo_1.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_definition_type_schema"))
    def test_definition_type_schema(self):
        result, msg = compile_spec(module_name,
                                   'definition_type_schema', [], "definition_type_schema.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_type_checking"))
    def test_type_checking(self):
        result, msg = compile_spec(module_name,
                                   'type_checking', [], "type_checking.json")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
