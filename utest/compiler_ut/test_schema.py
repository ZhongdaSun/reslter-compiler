import unittest
import os
import shutil

from compiler.workflow import generate_restler_grammar, Constants

from compiler.config import Config
from compiler_ut.utilities import (
    get_line_differences,
    get_grammar_file_content,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class SchemaTests(unittest.TestCase):
    test_root_dir = os.path.join(os.getcwd(), "test_output")
    swagger_dir = os.path.join(os.getcwd(), "compiler_ut", "swagger")

    @classmethod
    def setUpClass(cls):
        if os.path.exists(SchemaTests.test_root_dir):
            shutil.rmtree(SchemaTests.test_root_dir)

        if not os.path.exists(SchemaTests.test_root_dir):
            os.mkdir(SchemaTests.test_root_dir)

    def assert_json_files(self, source_dir, target_dir):
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

    def assert_json_file(self, source_file_name, target_file_name):
        if os.path.exists(source_file_name) and os.path.exists(target_file_name):
            result, diff = compare_difference(source_file_name, target_file_name)
            self.assertTrue(result, msg=f"file:{source_file_name}, diff:{diff}")
        elif not os.path.exists(source_file_name) and not os.path.exists(target_file_name):
            self.assertTrue(True, f"both not exists file.")
        else:
            self.assertFalse(True,
                             f"result: not exists file {source_file_name} or {target_file_name}")

    def compile_spec(self, spec_file_name):
        folder_name = spec_file_name.rsplit('.json', 1)[0]
        file_name_grammar_json = f"{folder_name}_grammar.json"
        file_name_grammar_py = f"{folder_name}_grammar.py"

        file_path = os.path.join(self.swagger_dir, "schemaTests", spec_file_name)

        source_dir = os.path.join(self.test_root_dir, folder_name)
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = Config()
        config.IncludeOptionalParameters = True
        config.GrammarOutputDirectoryPath = source_dir
        config.ResolveBodyDependencies = True
        config.UseBodyExamples = True
        config.UseQueryExamples = True
        config.UseHeaderExamples = True
        config.UseBodyExamples = True
        config.UsePathExamples = True
        config.UseAllExamplePayloads = False
        config.DataFuzzing = True
        config.SwaggerSpecFilePath = [file_path]
        config.CustomDictionaryFilePath = None

        generate_restler_grammar(config=config)

        grammar_output_file_path = os.path.join(source_dir, "grammar.py")

        assert os.path.exists(grammar_output_file_path)

        grammar_output_file_path = os.path.join(source_dir, "grammar.json")
        baseline_grammar = os.path.join(self.swagger_dir, "baselines", "schemaTests", file_name_grammar_json)

        self.assert_json_file(grammar_output_file_path, baseline_grammar)

        baseline_grammar = os.path.join(self.swagger_dir, "baselines", "schemaTests", file_name_grammar_py)
        found, grammar_diff = get_line_differences(grammar_output_file_path, baseline_grammar)

        self.assertFalse(found, f"Grammar does not match baseline. First difference: {grammar_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_required_header_parsed_successfully")
        or DebugConfig().get_open_api_v3())
    def test_required_header_parsed_successfully(self):
        self.compile_spec("requiredHeader.yml")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_spec_with_x_ms_paths_parsed_successfully")
        or DebugConfig().get_open_api_v2())
    def test_spec_with_x_ms_paths_parsed_successfully(self):
        # 测试 x-ms-paths 的规格文件
        self.compile_spec("xMsPaths.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_parameter_read_from_global_parameters"))
    def test_path_parameter_read_from_global_parameters(self):
        self.compile_spec("global_path_parameters.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_swagger_escape_characters_parsed_successfully")
        or DebugConfig().get_open_api_v3())
    def test_swagger_escape_characters_parsed_successfully(self):
        self.compile_spec("swagger_escape_characters.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_json_depth_limit"))
    def test_json_depth_limit(self):
        source_dir = os.path.join(self.test_root_dir, "large_json_body")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "IncludeOptionalParameters": True,
            "GrammarOutputDirectoryPath": source_dir,
            "ResolveBodyDependencies": True,
            "ResolveQueryDependencies": True,
            "UseBodyExamples": False,
            "UseQueryExamples": False,
            "SwaggerSpecFilePath": [os.path.join(self.swagger_dir, "schemaTests", "large_json_body.json")],
        }
        upper_limit = 6
        lower_limit = 1
        for depth_limit in range(lower_limit, upper_limit):
            object_name = f"object_level_{depth_limit}"
            next_object_name = f"object_level_{depth_limit + 1}"
            obj_config = Config.init_from_json(config)
            obj_config.JsonPropertyMaxDepth = depth_limit
            generate_restler_grammar(obj_config)

            grammar_file = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
            grammar = get_grammar_file_content(grammar_file)

            # Make sure the object for this level is present, and the one for the next level is not
            if depth_limit > lower_limit:
                self.assertIn(object_name, grammar)
                self.assertNotIn(next_object_name, grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_additional_properties_schema")
        or DebugConfig().get_open_api_v3())
    def test_additional_properties_schema(self):
        self.compile_spec("additionalProperties.yml")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_parameter_substrings")
        or DebugConfig().get_open_api_v3())
    def test_path_parameter_substrings(self):
        self.compile_spec("path_param_substrings.json")


if __name__ == '__main__':
    unittest.main()
