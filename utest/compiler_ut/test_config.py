import unittest
import os
import shutil

from compiler.workflow import generate_restler_grammar, Constants

from compiler.config import Config
from compiler.utilities import JsonSerialization
from compiler_ut.utilities import (
    get_line_differences,
    TEST_ROOT_DIR,
    SWAGGER_DIR,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_ROOT_DIR):
            shutil.rmtree(TEST_ROOT_DIR)

        if not os.path.exists(TEST_ROOT_DIR):
            os.mkdir(TEST_ROOT_DIR)

    # Combines two API definitions and validates the correct engine settings for per-endpoint dictionaries.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_swagger_config_custom_dictionary_sanity_1"))
    def test_swagger_config_custom_dictionary_sanity_1(self):
        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "swagger1")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        multi_dict_config = {
            "SwaggerSpecFilePath": None,
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "maindict.json"),
            "UseBodyExamples": False,
            "ResolveBodyDependencies": True,
            "SwaggerSpecConfig": [
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger1.json"),
                    "DictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "dict1.json"),
                },
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger2.json"),
                    "DictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "dict2.json"),
                },
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger3.json"),
                }
            ],
            "EngineSettingsFilePath": os.path.join(SWAGGER_DIR, "configTests", "restlerEngineSettings.json"),
            "GrammarOutputDirectoryPath": grammar_output_directory
        }

        new_settings_file_path = os.path.join(grammar_output_directory, "engine_settings.json")
        obj_config = Config.init_from_json(multi_dict_config)
        generate_restler_grammar(obj_config)

        per_resource_settings = JsonSerialization.try_deeserialize_from_file(new_settings_file_path)
        # per_resource_settings = RestlerSettings(jason_data)

        if "error" in per_resource_settings:
            self.fail(f"Engine settings error: {per_resource_settings['error']}")
        per_resource_settings_dict = per_resource_settings.get("per_resource_settings")
        spec1_dict = per_resource_settings_dict.get("/first")
        spec2_dict = per_resource_settings_dict.get("/second")
        spec3_dict = per_resource_settings_dict.get("/third")

        def payload_contains(dictionary, payload_name, payload, is_uuid_suffix):
            if dictionary is None:
                return False
            if is_uuid_suffix:
                entry = dictionary.get("restler_custom_payload_uuid4_suffix").get(payload_name)
                return entry == payload
            else:
                dictionary_file = dictionary.get("custom_dictionary")
                dictionary_info = JsonSerialization.try_deeserialize_from_file(
                    os.path.join(grammar_output_directory, dictionary_file))
                entry = dictionary_info.get("restler_custom_payload").get(payload_name)
            return entry and payload in entry

        # Check that each dictionary contains the custom payload from the source dictionary.
        self.assertTrue(payload_contains(spec1_dict, "banana", "banana_1", False),
                        "incorrect output dictionary from spec1, expected to find 'banana_1'")
        self.assertTrue(payload_contains(spec2_dict, "apple", "apple_2", False),
                        "incorrect output dictionary from spec2, expected to find 'apple_2'")
        self.assertIsNone(spec3_dict, "the third spec should not have a dictionary")

        # Check that the main output dictionary has all the expected "custom_payload_uuid_suffix" values.
        output_dict = JsonSerialization.try_deeserialize_from_file(os.path.join(grammar_output_directory, "dict.json"))
        self.assertTrue(payload_contains(output_dict, "orderId", "orderid", True))

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_swagger_config_custom_dictionary_sanity_2"))
    def test_swagger_config_custom_dictionary_sanity_2(self):
        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "swagger1")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        multi_dict_config = {
            "SwaggerSpecFilePath": None,
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "maindict.json"),
            "UseBodyExamples": False,
            "ResolveBodyDependencies": True,
            "SwaggerSpecConfig": [
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger1.json"),
                    "DictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "dict1.json"),
                },
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger2.json"),
                    "DictionaryFilePath": os.path.join(SWAGGER_DIR, "configTests", "dict2.json"),
                },
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "configTests", "swagger3.json"),
                }
            ],
            "EngineSettingsFilePath": os.path.join(SWAGGER_DIR, "configTests", "restlerEngineSettings.json"),
            "GrammarOutputDirectoryPath": grammar_output_directory
        }

        obj_config = Config.init_from_json(multi_dict_config)
        generate_restler_grammar(obj_config)

        # TODO Check that the grammar contains references to the custom payload and uuid suffix.
        grammar_file_path = os.path.join(grammar_output_directory, "grammar.py")
        with open(grammar_file_path, 'r') as grammar_file:
            grammar_lines = grammar_file.readlines()
        apple_count = sum(
            "primitives.restler_custom_payload(\"apple\", quoted=True)," in line for line in grammar_lines)
        banana_count = sum(
            "primitives.restler_custom_payload(\"banana\", quoted=True)," in line for line in grammar_lines)

        self.assertEqual(apple_count, 1, f"apple custom payload count should be 1, found {apple_count}")
        self.assertEqual(banana_count, 1, f"banana custom payload count should be 1, found {banana_count}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_swagger_config_custom_annotations_sanity_1"))
    def test_swagger_config_custom_annotations_sanity_1(self):
        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "pathAnnotation")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        config = {
            "GrammarOutputDirectoryPath": grammar_output_directory,
            "ResolveBodyDependencies": True,
            "UseBodyExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "annotationTests",
                                                 "pathAnnotation.json")]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_inline_file_path = os.path.join(grammar_output_directory, "grammar.py")

        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "pathAnnotationInSeparateFile")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        no_annotations_config = {
            "GrammarOutputDirectoryPath": grammar_output_directory,
            "SwaggerSpecFilePath": [
                os.path.join(SWAGGER_DIR, "annotationTests",
                             "pathAnnotationInSeparateFile.json")]
        }
        obj_no_annotations_config = Config.init_from_json(no_annotations_config)
        generate_restler_grammar(obj_no_annotations_config)
        grammar_no_annotations_file_path = os.path.join(grammar_output_directory, "grammar.py")

        found, grammar_diff = get_line_differences(grammar_inline_file_path, grammar_no_annotations_file_path)
        self.assertFalse(found, msg="Test Bug: Found no differences after removing annotations.")


    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_swagger_config_custom_annotations_sanity_2"))
    def test_swagger_config_custom_annotations_sanity_2(self):
        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "pathAnnotation")

        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        config = {
            "GrammarOutputDirectoryPath": grammar_output_directory,
            "ResolveBodyDependencies": True,
            "UseBodyExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "annotationTests",
                                                 "pathAnnotation.json")]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        grammar_inline_file_path = os.path.join(grammar_output_directory, "grammar.py")

        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "globalAnnotations")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)
        external_config = {
            "GrammarOutputDirectoryPath": grammar_output_directory,
            "SwaggerSpecConfig": [
                {
                    "SpecFilePath": os.path.join(SWAGGER_DIR, "annotationTests",
                                                 "pathAnnotationInSeparateFile.json"),
                    "AnnotationFilePath": os.path.join(SWAGGER_DIR, "annotationTests",
                                                       "globalAnnotations.json")
                }
            ]
        }

        obj_external_config = Config.init_from_json(external_config)
        generate_restler_grammar(obj_external_config)
        grammar_external_filepath = os.path.join(grammar_output_directory, "grammar.py")
        found, grammars_with_annotations_diff = get_line_differences(grammar_inline_file_path,
                                                                     grammar_external_filepath)
        # self.assertFalse(found, f"Found differences, expected none: {grammars_with_annotations_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_multiple_example_configs_sanity"))
    def test_multiple_example_configs_sanity(self):
        grammar_output_directory = os.path.join(TEST_ROOT_DIR, "exampleConfigTestPut")
        if not os.path.exists(grammar_output_directory):
            os.mkdir(grammar_output_directory)

        config = {
            "SwaggerSpecFilePath": [
                os.path.join(SWAGGER_DIR, "configTests", "exampleConfigTestPut.json")],
            "ExampleConfigFiles": [
                {"exactCopy": False,
                 "filePath": os.path.join(SWAGGER_DIR, "configTests",
                                          "exampleConfigTestConfig1.json")},
                {"exactCopy": True,
                 "filePath": os.path.join(SWAGGER_DIR, "configTests",
                                          "exampleConfigTestConfig2.json")}
            ],
            "UseBodyExamples": True,
            "GrammarOutputDirectoryPath": grammar_output_directory
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_file_path = os.path.join(grammar_output_directory, "grammar.py")
        with open(grammar_file_path, 'r') as grammar_file:
            grammar_lines = grammar_file.readlines()

        window_count = sum("window" in line for line in grammar_lines)
        door_count = sum("door" in line for line in grammar_lines)
        wood_count = sum("wood" in line for line in grammar_lines)

        self.assertEqual(window_count, 1, f"There should be 1 window from example, found {window_count}")
        self.assertEqual(door_count, 0, f"There should be 0 door from example, found {door_count}")
        self.assertEqual(wood_count, 1, f"There should be 1 wood from example, found {wood_count}")


if __name__ == "__main__":
    unittest.main()
