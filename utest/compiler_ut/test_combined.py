import unittest
import os
import shutil

from compiler.workflow import generate_restler_grammar, Constants
from compiler.config import Config
from compiler_ut.utilities import (
    get_line_differences,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class CombinedTests(unittest.TestCase):
    test_root_dir = os.path.join(os.getcwd(), "test_output")
    swagger_dir = os.path.join(os.getcwd(), "compiler_ut", "swagger")

    @classmethod
    def setUpClass(cls):
        if os.path.exists(CombinedTests.test_root_dir):
            shutil.rmtree(CombinedTests.test_root_dir)

        if not os.path.exists(CombinedTests.test_root_dir):
            os.mkdir(CombinedTests.test_root_dir)

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

    def compile_spec(self,
                     spec_file_name,
                     target_folder_name):
        folder_name = spec_file_name.rsplit('.json', 1)[0]
        file_name_grammar_json = f"{folder_name}_grammar.json"
        file_name_grammar_py = f"{folder_name}_grammar.py"

        file_path = os.path.join(self.swagger_dir, target_folder_name, spec_file_name)

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
        config.SwaggerSpecFilePath = [file_path]
        config.CustomDictionaryFilePath = None

        generate_restler_grammar(config=config)

        grammar_output_file_path = os.path.join(source_dir, "grammar.py")

        assert os.path.exists(grammar_output_file_path)

        grammar_output_file_path = os.path.join(source_dir, "grammar.json")
        baseline_grammar = os.path.join(self.swagger_dir, "baselines", target_folder_name, file_name_grammar_json)
        import logging
        logging.info(f"grammar_output_file_path={grammar_output_file_path}\n, baseline_grammar={baseline_grammar}")
        self.assert_json_file(grammar_output_file_path, baseline_grammar)

        baseline_grammar = os.path.join(self.swagger_dir, "baselines", target_folder_name, file_name_grammar_py)
        found, grammar_diff = get_line_differences(grammar_output_file_path, baseline_grammar)

        self.assertFalse(found, f"Grammar does not match baseline. First difference: {grammar_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_null_test_swagger"))
    def test_null_test_swagger(self):
        self.compile_spec("null_test_swagger.json", "schemaTests")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_parameter_read_from_global_parameters"))
    def test_path_parameter_read_from_global_parameters(self):
        self.compile_spec("global_path_parameters.json", "schemaTests")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_example"))
    def test_array_example(self):
        self.compile_spec("array_example.json", "combinedTest")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_example_demo1"))
    def test_example_demo1(self):
        self.compile_spec("example_demo1.json", "combinedTest")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_combined_array_example_spec"))
    def test_combined_array_example_spec(self):
        source_dir = os.path.join(self.test_root_dir, "array_example")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            "UseHeaderExamples": True,
            "UsePathExamples": False,
            "UseQueryExamples": True,
            "UseAllExamplePayloads": False,
            "DiscoverExamples": False,
            "ExamplesDirectory": "",
            "DataFuzzing": True,
            "ReadOnlyFuzz": False,
            "ResolveQueryDependencies": True,
            "ResolveHeaderDependencies": False,
            "UseRefreshableToken": True,
            "AllowGetProducers": False,
            "TrackFuzzedParameterNames": False,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "array_example.json")]
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)


if __name__ == '__main__':
    unittest.main()
