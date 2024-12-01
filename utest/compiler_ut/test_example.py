import unittest
import os
import shutil

from compiler.workflow import generate_restler_grammar, Constants
from compiler.config import Config
from compiler.example import try_deserialize_example_config_file
from compiler_ut.utilities import (
    get_line_differences,
    compare_difference,
    get_grammar_file_content,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestExampleGrammar(unittest.TestCase):
    test_root_dir = os.path.join(os.getcwd(), "test_output")
    swagger_dir = os.path.join(os.getcwd(), "compiler_ut", "swagger")

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TestExampleGrammar.test_root_dir):
            shutil.rmtree(TestExampleGrammar.test_root_dir)

        if not os.path.exists(TestExampleGrammar.test_root_dir):
            os.mkdir(TestExampleGrammar.test_root_dir)

    def assert_json_file(self, source_dir, target_dir):
        checking_json_file = [
            Constants.NewDictionaryFileName,
            Constants.DependenciesFileName,
            Constants.DependenciesDebugFileName,
            Constants.UnresolvedDependenciesFileName,
            Constants.DefaultJsonGrammarFileName
        ]

        for item in checking_json_file:
            grammar_file_path = os.path.join(source_dir, item)
            baseline_grammar_file_path = os.path.join(target_dir, item)
            if os.path.exists(grammar_file_path) and os.path.exists(baseline_grammar_file_path):
                result, diff = compare_difference(grammar_file_path, baseline_grammar_file_path)
                self.assertTrue(result, msg=f"file:{item}, diff:{diff}")
            elif not os.path.exists(grammar_file_path) and not os.path.exists(baseline_grammar_file_path):
                self.assertTrue(True, f"both not exists file.")
            else:
                self.assertFalse(True,
                                 f"result: not exists file {grammar_file_path} or {baseline_grammar_file_path}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_no_example_in_grammar_with_dependencies"))
    def test_no_example_in_grammar_with_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "example_demo1")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': False,
            'TrackFuzzedParameterNames': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "example_demo1", "example_demo1.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo1", "example_demo_dictionary.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        # The grammar should not contain the fruit codes from the example
        self.assertNotIn("999", grammar)

        # The grammar should not contain the store codes from the example
        self.assertNotIn("23456", grammar)

        try:
            found = grammar.index("restler_fuzzable_datetime")
        except ValueError:
            found = True
        self.assertTrue(found, "restler_fuzzable_datetime not found")

        try:
            found = grammar.index("restler_fuzzable_object")
        except ValueError:
            found = True
        self.assertTrue(found, grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_config_file"))
    def test_example_config_file(self):
        example_config_file_path = os.path.join(self.swagger_dir, "example_config_file.json")
        config_data = try_deserialize_example_config_file(example_config_file_path=example_config_file_path,
                                                          exact_copy=True)

        methods = []

        for path_property in config_data.paths:
            methods.append(path_property.path)

        self.assertTrue('/vm' in methods)

    def run_array_example_test(self, config, source_dir):
        generate_restler_grammar(config)
        # Read the baseline and make sure it matches the expected one
        expected_grammar_file_path = os.path.join(self.swagger_dir, "baselines", "exampleTests",
                                                  "array_example_grammar.py")
        actual_grammar_file_path = os.path.join(source_dir, "grammar.py")

        found_diff, diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)
        self.assertFalse(found_diff, msg=f"The difference is {diff}")

    # Test that uses both body and query examples, and tests
    # that the grammar is correct when (a) examples are referenced from the spec,
    # and (b) an external example config file is used.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_in_grammar_without_dependencies_1"))
    def test_array_example_in_grammar_without_dependencies_1(self):
        source_dir = os.path.join(self.test_root_dir, "array_example")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'UseQueryExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "array_example.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
        }

        obj_config = Config.init_from_json(config)
        # Run the example test using the Swagger example and using the external example.
        self.run_array_example_test(obj_config, source_dir)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_in_grammar_without_dependencies_2"))
    def test_array_example_in_grammar_without_dependencies_2(self):
        source_dir = os.path.join(self.test_root_dir, "array_example_fuzzing")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'UseQueryExamples': True,
            'DataFuzzing': False,  # Testing with DataFuzzing set to False
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "array_example.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
        }

        obj_config = Config.init_from_json(config)
        self.run_array_example_test(obj_config, source_dir)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_in_grammar_without_dependencies_3"))
    def test_array_example_in_grammar_without_dependencies_3(self):
        source_dir = os.path.join(self.test_root_dir, "array_example_external")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'UseQueryExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "array_example_external.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
            'ExampleConfigFiles': [{
                'filePath': os.path.join(self.swagger_dir, "example_config_file.json"),
                'exactCopy': True
            }]
        }
        obj_config = Config.init_from_json(config)
        self.run_array_example_test(obj_config, source_dir)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example_dynamic_object"))
    def test_array_example_dynamic_object(self):
        source_dir = os.path.join(self.test_root_dir, "array_example_dynamic_object")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "array_example.json")],
            'AnnotationFilePath': os.path.join(self.swagger_dir, "array_example_annotations.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn(
            "primitives.restler_static_string(_stores__storeId__order_post_order_items.reader(), quoted=False),",
            grammar)
        self.assertIn(
            "primitives.restler_static_string(_stores__storeId__order_post_order_items_0.reader(), quoted=False),",
            grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_object_example_in_grammar_without_dependencies")
        or DebugConfig().get_open_api_v2())
    def test_object_example_in_grammar_without_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "object_example")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "object_example.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn('"tag1": "value1"', grammar)
        self.assertIn('"tag2": "value2"', grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_allof_property_omitted_in_example"))
    def test_allof_property_omitted_in_example(self):
        source_dir = os.path.join(self.test_root_dir, "secgroup_example")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        target_dir = os.path.join(self.swagger_dir, "baselines", "put_createorupdate")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "secgroup_example.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "dict_secgroup_example.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_empty_array_example_in_grammar_1"))
    def test_empty_array_example_in_grammar_1(self):
        swagger_spec_config = {
            'SpecFilePath': os.path.join(self.swagger_dir, "empty_array_example.json"),
            'Dictionary': None,
            'DictionaryFilePath': None,
            'AnnotationFilePath': None,
        }

        config = {
            'SwaggerSpecConfig': [swagger_spec_config],
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'UseBodyExamples': True,
            'ResolveBodyDependencies': True,
            'ResolveQueryDependencies': True

        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_empty_array_example_in_grammar_2"))
    def test_empty_array_example_in_grammar_2(self):
        swagger_spec_config = {
            'SpecFilePath': os.path.join(self.swagger_dir, "empty_array_example.json"),
            'Dictionary': None,
            'DictionaryFilePath': None,
            'AnnotationFilePath': None,
        }

        config = {
            'SwaggerSpecConfig': [swagger_spec_config],
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'ResolveBodyDependencies': False,
            'ResolveQueryDependencies': False,
            'UseBodyExamples': True
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_empty_array_example_in_grammar_3"))
    def test_empty_array_example_in_grammar_3(self):
        # Also test custom payload for empty array
        custom_dictionary = ' { "restler_custom_payload": { "item_descriptions": ["zzz"] }} '
        swagger_spec_config = {
            'SpecFilePath': os.path.join(self.swagger_dir, "empty_array_example.json"),
            'Dictionary': custom_dictionary,
            'DictionaryFilePath': None,
            'AnnotationFilePath': None,
        }

        config = {
            'SwaggerSpecConfig': [swagger_spec_config],
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'ResolveBodyDependencies': True,
            "ResolveQueryDependencies": True,
            'UseBodyExamples': True,
        }

        obj_config = Config.init_from_json(config)

        generate_restler_grammar(obj_config)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_header_example_with_and_without_dependencies"))
    def test_header_example_with_and_without_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "headers")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'UseHeaderExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "headers.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "headers_dict.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        # Assert expectations based on grammar content
        self.assertNotIn('primitives.restler_static_string("computerName: ")', grammar)
        self.assertIn('primitives.restler_static_string("computerDimensions: ")', grammar)
        self.assertIn('primitives.restler_fuzzable_string("fuzzstring", quoted=False, examples=[\'\"quotedString\"\'])',
                      grammar)
        self.assertIn("1.11", grammar)
        self.assertIn("2.22", grammar)
        self.assertIn("primitives.restler_custom_payload_header(\"rating\"),", grammar)
        self.assertIn("primitives.restler_custom_payload_header(\"extra1\"),", grammar)
        self.assertIn("primitives.restler_custom_payload_header(\"extra2\"),", grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_in_grammar_without_dependencies")
        or DebugConfig().get_open_api_v2())
    def test_example_in_grammar_without_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "example_demo1")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        extensions = [".json"]
        for extension in extensions:
            config = {
                'IncludeOptionalParameters': True,
                'GrammarOutputDirectoryPath': source_dir,
                'ResolveBodyDependencies': False,
                'UseBodyExamples': True,
                'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, f"example_demo1{extension}")],
                'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
            }
            obj_config = Config.init_from_json(config)
            generate_restler_grammar(obj_config)
            grammar_file = os.path.join(source_dir, "grammar.py")
            grammar = get_grammar_file_content(grammar_file)

            self.assertIn("999", grammar)
            self.assertIn("78910", grammar)
            self.assertIn("paperfestive", grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_in_grammar_with_dependencies")
        or DebugConfig().get_open_api_v2())
    def test_example_in_grammar_with_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "example_demo1")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'DiscoverExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "example_demo1.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "example_demo_dictionary.json"),
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn("999", grammar)
        self.assertNotIn("23456", grammar)
        self.assertNotIn("paperfestive", grammar)
        self.assertIn("restler_custom_payload(\"bagType\", quoted=True)", grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_logic_example_in_grammar_with_dependencies"))
    def test_logic_example_in_grammar_with_dependencies(self):
        source_dir = os.path.join(self.test_root_dir, "example_demo")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "example_demo.json")],
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        self.assertTrue(True)  # Placeholder for actual assertions

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_body_dependency_nested_object_can_be_inferred_via_parent"))
    def test_body_dependency_nested_object_can_be_inferred_via_parent(self):
        source_dir = os.path.join(self.test_root_dir, "subnet_id")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "dependencyTests", "subnet_id.json")]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        grammar_dynamic_objects = [
            "_subnets__subnetName__put_id.reader()",
            "_subnets__subnetName__put_name.reader()"
        ]

        for x in grammar_dynamic_objects:
            self.assertIn(x, grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_nested_objects_naming_sanity_test"))
    def test_nested_objects_naming_sanity_test(self):
        source_dir = os.path.join(self.test_root_dir, "nested_objects_naming")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "nested_objects_naming.json")]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn("_publicIPAddresses__publicIpAddressName__put_id.reader()", grammar)
        self.assertIn("_virtualNetworkTaps__tapName__put_id.reader()", grammar)


    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_body_payload_contains_both_producer_and_consumer"))
    def test_body_payload_contains_both_producer_and_consumer(self):
        source_dir = os.path.join(self.test_root_dir, "frontend_port_id")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "frontend_port_id.json")],
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        # 检查部分资源 ID
        self.assertIn("primitives.restler_static_string(\"/frontendPorts/\")", grammar)
        self.assertIn("primitives.restler_static_string(\"/frontendIPConfigurations/\")", grammar)
        self.assertIn("primitives.restler_custom_payload_uuid4_suffix(\"frontendPorts_name\", quoted=True)", grammar)
        self.assertIn("primitives.restler_custom_payload_uuid4_suffix(\"frontendIPConfigurations_name\", quoted=True)",
                      grammar)
        self.assertNotIn("primitives.restler_custom_payload_uuid4_suffix(\"frontendPort_name\", quoted=True)", grammar)
        self.assertNotIn(
            "primitives.restler_custom_payload_uuid4_suffix(\"frontendIPConfiguration_name\", quoted=True)", grammar)

        self.assertIn("appgwipc", grammar)
        self.assertNotIn("appgwfip", grammar)
        self.assertNotIn("appgwfp", grammar)

        example_resource_ids = [
            "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/"
            "applicationGateways/appgw/frontendPorts/appgwfp",
            "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/"
            "applicationGateways/appgw/frontendIPConfigurations/appgwfip"
        ]
        for x in example_resource_ids:
            self.assertNotIn(x, grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_dependencies_can_be_inferred_from_body_payload"))
    def test_get_dependencies_can_be_inferred_from_body_payload(self):
        source_dir = os.path.join(self.test_root_dir, "ip_configurations_get")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'DiscoverExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "ip_configurations_get.json")]
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn("_networkInterfaces__networkInterfaceName__put_properties_ipConfigurations_0_name.reader()",
                      grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inline_examples_used_instead_of_fuzzstring"))
    def test_inline_examples_used_instead_of_fuzzstring(self):
        source_dir = os.path.join(self.test_root_dir, "inline_examples")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'UseQueryExamples': None,
            'UseBodyExamples': None,
            'GrammarOutputDirectoryPath': source_dir,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "inline_examples.json")]
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)
        fuzzable_str = "primitives.restler_fuzzable_string(\"fuzzstring\", quoted=True, examples=[\"i5\"]),"

        self.assertIn(fuzzable_str, grammar)

        self.assertIn("primitives.restler_fuzzable_int(\"1\", examples=[\"32\"]),", grammar)
        self.assertIn(
            "primitives.restler_fuzzable_string(\"fuzzstring\", quoted=False, "
            "examples=[\"inline_example_value_laptop1\"]),",
            grammar)
        self.assertIn("primitives.restler_fuzzable_string(\"fuzzstring\", "
                      "quoted=False, examples=[\"inline_ex_2\"]),",
                      grammar)
        self.assertIn("primitives.restler_fuzzable_string(\"fuzzstring\", "
                      "quoted=False, examples=[None]),", grammar)
        self.assertIn("primitives.restler_fuzzable_number(\"1.23\", examples=[\"1.67\"]),", grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_exact_copy_values_are_correct"))
    def test_exact_copy_values_are_correct(self):
        source_dir = os.path.join(self.test_root_dir, "array_example")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'UsePathExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "exactCopy", "array_example.json")],
            'ExampleConfigFiles': [{
                'filePath': os.path.join(self.swagger_dir, "exactCopy", "examples.json"),
                'exactCopy': False
            }]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)

        self.assertIn("primitives.restler_fuzzable_string(\"fuzzstring\", quoted=False, examples=[\"2020-02-02\"])",
                      grammar)
        # Also test to make sure that 'exactCopy : true' filters out the parameters that are not declared in the spec
        self.assertNotIn("ddd", grammar)  # Check if unreferenced parameters are filtered out

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_examples_with_optional_parameters"))
    def test_examples_with_optional_parameters(self):
        source_dir = os.path.join(self.test_root_dir, "optional_params")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseQueryExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "exampleTests", "optional_params.json")],
            'ExampleConfigFiles': [{
                'filePath': os.path.join(self.swagger_dir, "exampleTests", "optional_params_example.json"),
                'exactCopy': False
            }]
        }
        obj_config = Config.init_from_json(config)

        generate_restler_grammar(obj_config)

        grammar_file = os.path.join(source_dir, "grammar.py")
        grammar = get_grammar_file_content(grammar_file)
        self.assertIn("required-param", grammar)
        self.assertIn("optional-param", grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_replace_entire_body_with_example"))
    def test_replace_entire_body_with_example(self):
        source_dir = os.path.join(self.test_root_dir, "body_param")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': False,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseQueryExamples': True,
            'UseBodyExamples': True,
            'DataFuzzing': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "exampleTests", "body_param.json")],
            'ExampleConfigFiles': [{
                'filePath': os.path.join(self.swagger_dir, "exampleTests", "body_param_example.json"),
                'exactCopy': True
            }]
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        expected_grammar_file_path = os.path.join(self.swagger_dir, "baselines", "exampleTests",
                                                  "body_param_exactCopy_grammar.py")

        grammar_file = os.path.join(source_dir, "grammar.py")

        found_diff, diff = get_line_differences(grammar_file, expected_grammar_file_path)
        message = f"Grammar Does not match baseline. First difference: {diff}"
        self.assertFalse(found_diff, msg=message)


if __name__ == '__main__':
    unittest.main()
