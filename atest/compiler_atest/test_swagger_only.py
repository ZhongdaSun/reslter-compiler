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
        business_config["JsonPropertyMaxDepth"] = None

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_circular_path"))
    def test_circular_path(self):
        result, msg = compile_spec('swagger_only',
                                   'circular_path', [], "circular_path.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_first"))
    def test_first(self):
        result, msg = compile_spec('swagger_only',
                                   'first', [], "first.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_second"))
    def test_second(self):
        result, msg = compile_spec('swagger_only',
                                   'second', [], "second.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_subnet_id"))
    def test_subnet_id(self):
        result, msg = compile_spec('swagger_only',
                                   'subnet_id', [], "subnet_id.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inline_examples"))
    def test_inline_examples(self):
        result, msg = compile_spec('swagger_only',
                                   'inline_examples', [], "inline_examples.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation"))
    def test_path_annotation(self):
        result, msg = compile_spec('swagger_only',
                                   'path_annotation', [], "pathAnnotation.json")
        self.assertTrue(result, msg=msg)

    # block by test_inconsistent_camel_case_fixed_by_restler
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_frontend_port_id"))
    def test_frontend_port_id(self):
        result, msg = compile_spec('swagger_only',
                                   'frontend_port_id', [], "frontend_port_id.json")
        self.assertTrue(result, msg=msg)

    # block by test_inconsistent_camel_case_fixed_by_restler
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inconsistent_casing_paths"))
    def test_inconsistent_casing_paths(self):
        result, msg = compile_spec('swagger_only',
                                   'inconsistent_casing_paths', [], "inconsistent_casing_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_ip_configurations_get"))
    def test_ip_configurations_get(self):
        result, msg = compile_spec('swagger_only',
                                   'ip_configurations_get', [], "ip_configurations_get.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_multiple_circular_paths"))
    def test_multiple_circular_paths(self):
        result, msg = compile_spec('swagger_only',
                                   'multiple_circular_paths', [], "multiple_circular_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_nested_objects_naming"))
    def test_nested_objects_naming(self):
        result, msg = compile_spec('swagger_only',
                                   'nested_objects_naming', [Dict_Json], "nested_objects_naming.json")
        self.assertTrue(result, msg=msg)

    # block by test_patch_request_body_parameter_producers_from_post
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_post_patch_dependency"))
    def test_post_patch_dependency(self):
        result, msg = compile_spec('swagger_only',
                                   'post_patch_dependency', [], "post_patch_dependency.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_put_createorupdate"))
    def test_put_createorupdate(self):
        result, msg = compile_spec('',
                                   'put_cswagger_onlyreateorupdate', [Dict_Json, Engine_Settings],
                                   "put_createorupdate.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body"))
    def test_large_json_body(self):
        result, msg = compile_spec('swagger_only',
                                   'large_json_body', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_1"))
    def test_large_json_body_level_1(self):
        business_config["JsonPropertyMaxDepth"] = 1
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_1', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_2"))
    def test_large_json_body_level_2(self):
        business_config["JsonPropertyMaxDepth"] = 2
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_2', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_3"))
    def test_large_json_body_level_3(self):
        business_config["JsonPropertyMaxDepth"] = 3
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_3', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_4"))
    def test_large_json_body_level_4(self):
        business_config["JsonPropertyMaxDepth"] = 4
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_4', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_5"))
    def test_large_json_body_level_5(self):
        business_config["JsonPropertyMaxDepth"] = 5
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_5', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_large_json_body_level_6"))
    def test_large_json_body_level_6(self):
        business_config["JsonPropertyMaxDepth"] = 6
        result, msg = compile_spec('swagger_only',
                                   'large_json_body_level_6', [], "large_json_body.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_read_only"))
    def test_read_only(self):
        result, msg = compile_spec('swagger_only',
                                   'readonly_test', [], "readonly_test.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_lowercase_paths"))
    def test_lowercase_paths(self):
        result, msg = compile_spec('swagger_only',
                                   'lowercase_paths', [Dict_Json], "lowercase_paths.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation_in_separate_file"))
    def test_path_annotation_in_separate_file(self):
        result, msg = compile_spec('swagger_only',
                                   'path_annotation_in_separate', [], "pathAnnotationInSeparate.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_local_annotations"))
    def test_local_annotations(self):
        result, msg = compile_spec('swagger_only',
                                   'local_annotations', [], "localAnnotation.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_body_dependency_cycles"))
    def test_body_dependency_cycles(self):
        result, msg = compile_spec('swagger_only',
                                   'body_dependency_cycles', [], "body_dependency_cycles.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_no_params"))
    def test_no_params(self):
        result, msg = compile_spec('swagger_only',
                                   'no_params', [], "no_params.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_swagger"))
    def test_custom_payload_swagger(self):
        result, msg = compile_spec('swagger_only',
                                   'custom_payload_swagger', [],
                                   "customPayloadSwagger.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_content_type_swagger"))
    def test_custom_payload_content_type_swagger(self):
        result, msg = compile_spec('swagger_only',
                                   'custom_payload_content_type_swagger', [],
                                   "customPayloadContentTypeSwagger.json")
        self.assertTrue(result, msg=msg)
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example"))
    def test_array_example(self):
        result, msg = compile_spec('swagger_only',
                                   'array_example', [],
                                   "array_example.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_empty_array_example"))
    def test_empty_array_example(self):
        result, msg = compile_spec('swagger_only',
                                   'empty_array_example', [],
                                   "empty_array_example.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_global_path_parameters"))
    def test_required_params_include_optional_parameters(self):
        temp = business_config["IncludeOptionalParameters"]
        business_config["IncludeOptionalParameters"] = True
        result, msg = compile_spec('swagger_only',
                                   'required_params_include_optional_parameters', [],
                                   "required_params.json")
        self.assertTrue(result, msg=msg)
        business_config["IncludeOptionalParameters"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_global_path_parameters"))
    def test_required_params_not_include_optional_parameters(self):
        temp = business_config["IncludeOptionalParameters"]
        business_config["IncludeOptionalParameters"] = False
        result, msg = compile_spec('swagger_only',
                                   'required_params_not_include_optional_parameters', [],
                                   "required_params.json")
        self.assertTrue(result, msg=msg)
        business_config["IncludeOptionalParameters"] = temp

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo"))
    def test_example_demo(self):
        result, msg = compile_spec('swagger_only',
                                   'example_demo', [],
                                   "example_demo.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo"))
    def test_example_demo(self):
        result, msg = compile_spec('swagger_only',
                                   'example_demo', [],
                                   "example_demo.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_path_dependencies"))
    def test_get_path_dependencies(self):
        result, msg = compile_spec('swagger_only',
                                   'get_path_dependencies', [],
                                   "get_path_dependencies.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation_in_separate_file"))
    def test_path_annotation_in_separate_file(self):
        result, msg = compile_spec('swagger_only',
                                   'path_annotation_in_separate_file', [],
                                   "pathAnnotationInSeparateFile.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_dictionary_payload"))
    def test_path_dictionary_payload(self):
        result, msg = compile_spec('swagger_only',
                                   'path_dictionary_payload', [],
                                   "pathDictionaryPayload.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_simple_swagger_all_param_data_types"))
    def test_simple_swagger_all_param_data_types(self):
        result, msg = compile_spec('swagger_only',
                                   'simple_swagger_all_param_data_types', [],
                                   "simple_swagger_all_param_data_types.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_uuidsuffix_test"))
    def test_uuidsuffix_test(self):
        result, msg = compile_spec('swagger_only',
                                   'uuidsuffix_test', [],
                                   "uuidsuffix_test.json")
        self.assertTrue(result, msg=msg)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_input_producer_spec"))
    def test_input_producer_spec(self):
        result, msg = compile_spec('swagger_only',
                                   'input_producer_spec', [],
                                   "input_producer_spec.json")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
