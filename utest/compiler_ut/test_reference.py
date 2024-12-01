import logging
import os
import unittest
import shutil

from compiler.workflow import generate_restler_grammar, Constants
from compiler.config import Config, ConfigSetting, convert_to_abs_path
from compiler_ut.utilities import (
    get_line_differences,
    get_grammar_file_content,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


# This test suite contains coverage for tricky references in Swagger files.
# It primarily serves as a regression suite for the framework used to parse Swagger files.
class TestReferences(unittest.TestCase):
    test_root_dir = os.path.join(os.getcwd(), "test_output")
    swagger_dir = os.path.join(os.getcwd(), "compiler_ut", "swagger")

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TestReferences.test_root_dir):
            shutil.rmtree(TestReferences.test_root_dir)

        if not os.path.exists(TestReferences.test_root_dir):
            os.mkdir(TestReferences.test_root_dir)

    def reference_types(self, spec_file_name):
        file_path = os.path.join(self.swagger_dir, "referencesTests", spec_file_name)
        logging.warning(f"file_path={file_path}")
        config = Config()
        if ConfigSetting().GrammarOutputDirectoryPath == "":
            ConfigSetting().GrammarOutputDirectoryPath = (
                convert_to_abs_path(os.path.dirname(__file__), self.test_root_dir))
            ConfigSetting().SwaggerSpecFilePath = [file_path]

        generate_restler_grammar(config)
        grammar_file = os.path.join(self.test_root_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(grammar_file)
        self.assertIn('[]', grammar)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_external_refs_multiple_visits_first"))
    def test_external_refs_multiple_visits_first(self):
        # Test external references for first file
        # Tests the case where file2 is parsed, it has references to file1, then back to file2.
        # Depending on the ordering, this was not handled correctly in NSwag (V10 and earlier).
        # Both parsing first or second as the main Swagger file should work.
        self.reference_types("first.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_external_refs_multiple_visits_second"))
    def test_external_refs_multiple_visits_second(self):
        # Test external references for second file
        # Tests the case where file2 is parsed, it has references to file1, then back to file2.
        # Depending on the ordering, this was not handled correctly in NSwag (V10 and earlier).
        # Both parsing first or second as the main Swagger file should work.
        self.reference_types("second.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_circular_reference")
        or DebugConfig().get_open_api_v3())
    def test_array_circular_reference(self):
        self.reference_types("circular_array.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_cached_circular_references_infinite_recursion"))
    def test_cached_circular_references_infinite_recursion(self):
        self.reference_types("multiple_circular_paths.json")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_cached_circular_references_missing_properties"))
    def test_cached_circular_references_missing_properties(self):
        self.reference_types("circular_path.json")


if __name__ == "__main__":
    unittest.main()
