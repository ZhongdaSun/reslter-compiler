import unittest
import os
import shutil

from rest.compiler.workflow import generate_restler_grammar, Constants
from rest.compiler.config import Config
from rest.compiler.utilities import JsonSerialization
from rest.compiler.dictionary import get_dictionary
from compiler_ut.utilities import (
    get_line_differences,
    get_grammar_file_content,
    TEST_ROOT_DIR,
    SWAGGER_DIR,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestDictionary(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_ROOT_DIR):
            shutil.rmtree(TEST_ROOT_DIR)

        if not os.path.exists(TEST_ROOT_DIR):
            os.mkdir(TEST_ROOT_DIR)

    # Baseline test for all types in the grammar supported by RESTler.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_quoting_is_correct_in_the_grammar"))
    def test_quoting_is_correct_in_the_grammar(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "customPayloadSwagger")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "IncludeOptionalParameters": True,
            "GrammarOutputDirectoryPath": source_dir,
            "ResolveBodyDependencies": True,
            "ResolveQueryDependencies": True,
            "UseBodyExamples": False,
            "UseQueryExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "dictionaryTests", "customPayloadSwagger.json")],
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR, "dictionaryTests", "customPayloadDict.json")
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        expected_grammar_file_path = os.path.join(SWAGGER_DIR, "baselines", "dictionaryTests",
                                                  "quoted_primitives_grammar.py")
        actual_grammar_file_path = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        found_diff, diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)
        self.assertFalse(found_diff, msg=f"Grammar does not match baseline. First difference: {diff}")

    # Test for custom payload uuid suffix
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_and_body_parameter_set_to_same_uuid_suffix_payload"))
    def test_path_and_body_parameter_set_to_same_uuid_suffix_payload(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "multipleIdenticalUuidSuffix")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "GrammarOutputDirectoryPath": source_dir,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "dictionaryTests",
                                                 "multipleIdenticalUuidSuffix.json")],
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR, "dictionaryTests",
                                                     "multipleIdenticalUuidSuffixDict.json"),
            "IncludeOptionalParameters": True,
            "UseQueryExamples": False,
            "UseBodyExamples": False,
            "ResolveQueryDependencies": True,
            "ResolveBodyDependencies": True,
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(grammar_file)
        # the grammar should contain both of the custom payload uuid suffixes from the dictionary
        self.assertIn('primitives.restler_custom_payload_uuid4_suffix("resourceId", quoted=False)', grammar)
        # TODO: the generated grammar currently contains a known bug - the resoruce ID is an integer and is being
        # assigned a uuid suffix, which currently only supports strings.  The 'quoted' value is correctly 'False'
        # because ID is an integer type, but
        # in the future this should be a different primitive, e.g. 'custom_payload_unique_integer'
        self.assertIn('primitives.restler_custom_payload_uuid4_suffix("/resource/id", quoted=False)', grammar)

    # Test that when a custom payload query (resp. header) is specified in the dictionary, it is injected.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_query_and_header_is_correctly_injected_1"))
    def test_custom_payload_query_and_header_is_correctly_injected_1(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "custom_payload_query_and_header_is_correctly_injected_1")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "IncludeOptionalParameters": True,
            "GrammarOutputDirectoryPath": source_dir,
            "ResolveBodyDependencies": True,
            "ResolveQueryDependencies": True,
            "UseBodyExamples": False,
            "UseQueryExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "dictionaryTests", "no_params.json")],
        }

        # Generate without dictionary
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(grammar_file)
        # Without the dictionary, there should be 4 fuzzable strings corresponding to the 4 spec parameters
        num_fuzzable_strings = sum(1 for s in grammar.splitlines() if "restler_fuzzable_string(" in s)
        self.assertEqual(num_fuzzable_strings, 4)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_custom_payload_query_and_header_is_correctly_injected_2"))
    def test_custom_payload_query_and_header_is_correctly_injected_2(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "custom_payload_query_and_header_is_correctly_injected_2")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "IncludeOptionalParameters": True,
            "GrammarOutputDirectoryPath": source_dir,
            "ResolveBodyDependencies": True,
            "ResolveQueryDependencies": True,
            "UseBodyExamples": False,
            "UseQueryExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "dictionaryTests", "no_params.json")],
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR,
                                                     "dictionaryTests", "inject_custom_payloads_dict.json")
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_file = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(grammar_file)

        # The header 'spec_header1' is declared in the spec and in the 'custom_payload_header' section.
        # There should be a custom_payload_header("spec_header1"),  in the grammar.
        self.assertIn('restler_custom_payload_header("spec_header1")', grammar)
        # The query parameter 'spec_query1' is declared in the spec and in the 'custom_payload_query' section.
        # There should be a custom_payload_query("spec_header1"),  in the grammar.
        self.assertIn('restler_custom_payload_query("spec_query1")', grammar)

        # The query and header parameters 'spec_query2' and 'spec_header2' are
        # declared in the spec and in the 'custom_payload_query' section.
        # The query should be substituted with the dictionary values (legacy behavior; this may
        # be updated in the future to require restler_custom_payload_query)
        # The header should not be substituted with the dictionary values (restler_custom_payload_header
        # should be used instead).
        self.assertFalse('restler_custom_payload("spec_header2")' in grammar)
        self.assertTrue('restler_custom_payload("spec_query2",' in grammar)

        # The injected query and headers should be present
        self.assertTrue('restler_custom_payload_header("extra_header1")' in grammar)
        self.assertTrue('restler_custom_payload_header("extra_header2")' in grammar)
        self.assertTrue('restler_custom_payload_query("extra_query1")' in grammar)
        self.assertTrue('restler_custom_payload_query("extra_query2")' in grammar)

        # There should be just one fuzzable string
        grammar_lines2 = grammar.split("\n")
        # Without the dictionary, there should be 4 fuzzable strings corresponding to the 4 spec parameters
        num_fuzzable_strings_2 = sum(1 for s in grammar.splitlines() if "restler_fuzzable_string(" in s)
        self.assertEqual(num_fuzzable_strings_2, 1)

    # Test replacing the content type of the request payload
    # The test checks 3 paths:
    # - /stores/{storeId}/order - body of type json, query parameters, no headers.
    # - /stores/{storeId}/order2 - body of type json, headers, no Content-Type header defined.
    # - /stores/{storeId}/order3 - body of type json, with Content-Type header defined.
    # - /stores/{storeId}/order4 - body of type json, with Content-Type header defined.
    # The first three cases will have content-type defined in custom payload and custom payload header (in
    # different dictionary tests).  The last one will not have any custom payload and Content-Type should be json.
    # The results are compared against a grammar baseline.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_content_type_can_be_modified_via_custom_payload_header"))
    def test_content_type_can_be_modified_via_custom_payload_header(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "customPayloadContentTypeSwagger")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'ResolveQueryDependencies': True,
            'UseBodyExamples': False,
            'UseQueryExamples': False,
            'SwaggerSpecFilePath': [
                os.path.join(SWAGGER_DIR, "dictionaryTests", "customPayloadContentTypeSwagger.json")],
            'CustomDictionaryFilePath': None
        }
        obj_config = Config.init_from_json(config)

        def run_test(dictionary_file_path, expected_grammar_file_path):
            # 测试同一规范，使用字典中的自定义负载头
            obj_config.CustomDictionaryFilePath = dictionary_file_path
            generate_restler_grammar(obj_config)

            actual_grammar_file_path = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
            found_diff, diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)
            self.assertFalse(found_diff, msg=f"Grammar does not match baseline. First difference: {diff}")

        # 测试 restler_custom_payload
        custom_dictionary_file_path = os.path.join(SWAGGER_DIR, "dictionaryTests",
                                                   "customPayloadRequestTypeDict.json")
        expected_grammar_file_path = os.path.join(SWAGGER_DIR, "baselines", "dictionaryTests",
                                                  "customPayloadContentType_grammar.py")
        run_test(custom_dictionary_file_path, expected_grammar_file_path)

        # 测试 restler_custom_payload_header
        custom_dictionary_file_path = os.path.join(SWAGGER_DIR, "dictionaryTests",
                                                   "customPayloadHeaderRequestTypeDict.json")
        expected_grammar_file_path = os.path.join(SWAGGER_DIR, "baselines", "dictionaryTests",
                                                  "customPayloadHeaderContentType_grammar.py")
        run_test(custom_dictionary_file_path, expected_grammar_file_path)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_generated_custom_value_generator_template_is_correct"))
    def test_generated_custom_value_generator_template_is_correct(self):

        source_dir = os.path.join(TEST_ROOT_DIR, "customPayloadSwagger")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'ResolveQueryDependencies': True,
            'UseBodyExamples': False,
            'UseQueryExamples': False,
            'SwaggerSpecFilePath': [
                os.path.join(SWAGGER_DIR, "dictionaryTests", "customPayloadSwagger.json")],
            'CustomDictionaryFilePath': os.path.join(SWAGGER_DIR, "dictionaryTests",
                                                     "customPayloadDict.json")
        }

        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        expected_grammar_file_path = os.path.join(SWAGGER_DIR, "baselines", "dictionaryTests",
                                                  "customPayloadDict_ValueGeneratorTemplate.py")

        actual_grammar_file_path = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        found_diff, diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)
        message = f"Template value generator does not match baseline. First difference: {diff}"
        self.assertFalse(found_diff, msg=message)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name,
                                       "test_date_format_is_preserved_after_deserialization_and_serialization"))
    def test_date_format_is_preserved_after_deserialization_and_serialization(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "customPayloadSwagger")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        dictionary_file_path = os.path.join(SWAGGER_DIR, "dictionaryTests", "serializationTestDict.json")

        deserialized = get_dictionary(dictionary_file_path)
        custom_payload = deserialized.restler_custom_payload
        fuzzable_date = deserialized.restler_fuzzable_datetime

        self.assertEqual(custom_payload["custom_date2"][0], "03/13/2023 10:36:56 ")
        self.assertEqual(custom_payload["custom_date1"][0], "2023-03-13T10:36:56.0000000Z")
        self.assertEqual(fuzzable_date[0], "2023-03-13T10:36:56.0000000Z")

        serialized = JsonSerialization.serialize(deserialized.__dict__())
        self.assertIn("2023-03-13T10:36:56.0000000Z", serialized)
        self.assertIn("03/13/2023 10:36:56 ", serialized)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'ResolveQueryDependencies': True,
            'UseBodyExamples': False,
            'UseQueryExamples': False,
            'SwaggerSpecFilePath': [
                os.path.join(SWAGGER_DIR, "dictionaryTests", "customPayloadSwagger.json")],
            'CustomDictionaryFilePath': dictionary_file_path
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        output_dict_path = os.path.join(source_dir, Constants.NewDictionaryFileName)
        with open(output_dict_path) as file_handler:
            dictionary_string = file_handler.read()
            file_handler.close()

        self.assertIn("2023-03-13T10:36:56.0000000Z", dictionary_string)
        self.assertIn("03/13/2023 10:36:56 ", dictionary_string)


if __name__ == '__main__':
    unittest.main()
