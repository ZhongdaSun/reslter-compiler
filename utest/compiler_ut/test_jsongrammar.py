import unittest
import os
import shutil

from compiler.workflow import generate_restler_grammar, Constants

from compiler.config import Config
from utilities import (
    get_line_differences,
    TEST_ROOT_DIR,
    SWAGGER_DIR)


class JsonGrammarTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_ROOT_DIR):
            shutil.rmtree(TEST_ROOT_DIR)

        if not os.path.exists(TEST_ROOT_DIR):
            os.mkdir(TEST_ROOT_DIR)

    def test_required_and_optional_properties_correctly_set(self):

        source_dir = os.path.join(TEST_ROOT_DIR, "required_params")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': False,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(SWAGGER_DIR, "grammarTests", "required_params.json")],
        }
        obj_config = Config.init_from_json(config)
        # 确认基线匹配用于 grammar.json 和 grammar.py
        for include_optional_parameters in [True, False]:
            obj_config.IncludeOptionalParameters = include_optional_parameters
            generate_restler_grammar(obj_config)
            for extension in ['.json', '.py']:
                actual_grammar_file_name = os.path.splitext(Constants.DefaultRestlerGrammarFileName)[0]
                expected_grammar_file_name = "required_params_grammar" \
                    if extension == ".json" or include_optional_parameters else "required_params_grammar_requiredonly"

                expected_grammar_file_path = os.path.join(SWAGGER_DIR, "baselines", "grammarTests",
                                                          f"{expected_grammar_file_name}{extension}")
                actual_grammar_file_path = os.path.join(source_dir, f"{actual_grammar_file_name}{extension}")
                found_diff, diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)
                grammar_name = "Json" if extension == ".json" else "Python"
                message = f"{grammar_name} grammar does not match baseline. First difference: {diff}"
                self.assertFalse(found_diff, msg=message)


if __name__ == '__main__':
    unittest.main()
