import os
import shutil
import json
import unittest
import random
import copy
import difflib
from deepdiff import DeepDiff

from compiler.workflow import generate_restler_grammar, Constants
from restler.restler import (
    execute_restler,
    load_common_engine,
    Restler_User_Settings,
    ExecuteParam)

from compiler.config import Config
from restler.utils import restler_logger as logger

from compiler.utilities import JsonSerialization

Dict_Json = Constants.NewDictionaryFileName
Dependencies_Json = Constants.DependenciesFileName
Debug_Dependencies_Json = Constants.DependenciesDebugFileName
Unresolved_Dependencies_Json = Constants.UnresolvedDependenciesFileName
Engine_Settings = Constants.DefaultEngineSettingsFileName


class NewSingletonError(Exception):
    pass


class UninitializedError(Exception):
    pass


business_config = {
    "IncludeOptionalParameters": True,
    "ResolveBodyDependencies": True,
    "UseBodyExamples": True,
    "UseQueryExamples": True,
    "UseHeaderExamples": True,
    "UsePathExamples": False,
    "ReadOnlyFuzz": False,
    "DiscoverExamples": False,
    "UseAllExamplePayloads": False,
    "DataFuzzing": False,
    "ExamplesDirectory": "",
    "ResolveQueryDependencies": True,
    "ResolveHeaderDependencies": False,
    "UseRefreshableToken": True,
    "AllowGetProducers": False,
    "TrackFuzzedParameterNames": False
}

curr_dir = os.path.dirname(os.path.abspath(__file__))

# restler's grammar saved in this folder
# GRAMMAR_ROOT_DIR = os.path.join(os.getcwd(), "grammar")
GRAMMAR_ROOT_DIR = os.path.join(curr_dir, "grammar")
# case folder
# CASE_ROOT_DIR = os.path.join(os.getcwd(), 'case')
CASE_ROOT_DIR = os.path.join(curr_dir, 'case')
# expected result in this folder
# BASELINE_ROOT_DIR = os.path.join(os.getcwd(), 'baseline')
BASELINE_ROOT_DIR = os.path.join(curr_dir, 'baseline')

all_checkers = ["InvalidValue", "InvalidDynamicObject", "NamespaceRule", "UseAfterFree", "LeakageRule",
                "ResourceHierarchy", "PayloadBody", "Examples"]

security_checkers = ["NamespaceRule", "UseAfterFree", "LeakageRule", "ResourceHierarchy"]

business_checkers = ["Examples"]

invalid_checkers = ["InvalidValue", "InvalidDynamicObject"]

invalid_value_checkers = ["InvalidValue"]


def custom_skip_decorator(condition):
    def decorator(test_func):
        if condition:
            return unittest.skip("custom condition met")(test_func)
        return test_func

    return decorator


def DebugConfig():
    """ Accessor for the RestlerSettings singleton """
    return DebugConfigCases.Instance()


class DebugConfigCases:
    __instance = None
    __skip_python_checking: bool
    __validate_grammar: bool

    @staticmethod
    def Instance():
        """ Singleton's instance accessor

        @return RestlerSettings instance
        @rtype  RestlerSettings

        """
        if DebugConfigCases.__instance is None:
            raise UninitializedError("RestlerSettings not yet initialized.")
        return DebugConfigCases.__instance

    @staticmethod
    def TEST_DeleteInstance():
        del DebugConfigCases.__instance
        DebugConfigCases.__instance = None

    def __init__(self):
        if DebugConfigCases.__instance:
            raise NewSingletonError("Attempting to create a new singleton instance.")
        with open(os.path.join(os.path.dirname(__file__), "atest.json")) as data_handler:
            self._config_data = json.load(data_handler)
            data_handler.close()
        self.__swagger_only = False
        debug_module = self._config_data["debug_module"]
        if debug_module is not None:
            debug_module_file = os.path.join(os.path.dirname(__file__), debug_module, "atest.json")
            with open(debug_module_file, encoding='utf-8') as data_handler:
                config_debug_module = json.load(data_handler)
                self._config_data.update(config_debug_module)
            data_handler.close()
        self.__skip_python_checking = self._config_data["skip_python"]
        self.__validate_grammar = self._config_data["validate_grammar"]
        DebugConfigCases.__instance = self

    def get_cases_config(self, test_module, test_func):
        if self._config_data["debug_mode"]:
            return not self._config_data[test_module][test_func] == 2
        else:
            return not self._config_data[test_module][test_func] in [0, 20]

    def get_module_config(self, test_module):
        return self._config_data[test_module]

    def get_test_func_config(self, test_module, test_func):
        return self._config_data[test_module][test_func]

    def get_debug_mode(self):
        return self._config_data["debug_mode"]

    def get_skip_python(self):
        return self._config_data["skip_python"]

    def get_debug_file(self):
        return self._config_data["debug_file"]

    def get_debug_module(self):
        return self._config_data["debug_module"]

    @property
    def validate_grammar(self):
        return self.__validate_grammar

    @validate_grammar.setter
    def validate_grammar(self, validate_grammar: bool):
        self.__validate_grammar = validate_grammar

    @property
    def swagger_only(self):
        return self.__swagger_only

    @swagger_only.setter
    def swagger_only(self, swagger_only):
        self.__swagger_only = swagger_only

    @property
    def skip_python_check(self):
        return self.__skip_python_checking

    @skip_python_check.setter
    def skip_python_check(self, is_skip: bool):
        self.__skip_python_checking = is_skip

    def debug_func(self):
        return self._config_data["debug_func"]


def read_and_clean_file(file_path):
    cleaned_lines = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            cleaned_line = line.strip()
            if "temp_" in cleaned_line:
                while "temp_" in cleaned_line:
                    start_1 = cleaned_line.index("temp_")
                    substr = cleaned_line[start_1:start_1 + len("temp_") + 4]
                    cleaned_line = cleaned_line.replace(substr, "temp")
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
    return cleaned_lines


def get_line_differences(expected_file_path, actual_file_path):
    cleaned_expected_file = read_and_clean_file(expected_file_path)
    cleaned_actual_file = read_and_clean_file(actual_file_path)
    if len(cleaned_actual_file) != len(cleaned_actual_file):
        return False, f"Different length of two files:{len(expected_file_path)} and {len(cleaned_actual_file)}."
    else:
        differences_found = False
        str_value = "\n"
        for index, line in enumerate(cleaned_actual_file):
            if cleaned_actual_file[index].strip() != cleaned_expected_file[index].strip():
                str_value = str_value + cleaned_actual_file[index] + "----" + cleaned_expected_file[index] + "\n"
                differences_found = True
        return differences_found, str_value


def get_random_grammar_output_directory_path():
    root_test_output_directory_path = os.path.join(os.path.dirname(__file__), "restlerTest")
    if not os.path.exists(root_test_output_directory_path):
        os.makedirs(root_test_output_directory_path)
    return os.path.join(root_test_output_directory_path, str(random.randint(0, 999999)))


def get_grammar_file_content(file_name):
    if os.path.exists(file_name):
        with open(file_name) as file_handler:
            return "".join(file_handler.readlines())


def compare_difference(jason_file, baseline_json_file):
    json1 = JsonSerialization.try_deeserialize_from_file(jason_file)
    json2 = JsonSerialization.try_deeserialize_from_file(baseline_json_file)
    diff = DeepDiff(json1, json2)
    if not diff:
        return True, ""
    else:
        return False, diff


def compile_spec(father_dir: str, dir_name: str, checking_more: [], swagger_only: str):
    # restler's grammar saved in this folder
    # GRAMMAR_ROOT_DIR = os.path.join(os.getcwd(), "grammar")
    GRAMMAR_ROOT_DIR = os.path.join(curr_dir, DebugConfig().get_debug_module(), "grammar")
    # case folder
    # CASE_ROOT_DIR = os.path.join(os.getcwd(), 'case')
    CASE_ROOT_DIR = os.path.join(curr_dir, DebugConfig().get_debug_module(), 'case')
    # expected result in this folder
    # BASELINE_ROOT_DIR = os.path.join(os.getcwd(), 'baseline')
    BASELINE_ROOT_DIR = os.path.join(curr_dir, DebugConfig().get_debug_module(), 'baseline')
    test_case_dir = ""
    father_grammar_dir = None
    expected_grammar_dir = ""
    grammar_dir = ""
    if father_dir and dir_name:  # Check if both father_dir and dir_name are not None or empty
        if DebugConfig().swagger_only:
            test_case_dir = os.path.join(CASE_ROOT_DIR, father_dir)
        else:
            test_case_dir = os.path.join(CASE_ROOT_DIR, father_dir, dir_name)
        expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, father_dir, dir_name)
        if father_dir == 'test_swagger_website':
            expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, 'test_swagger_only', dir_name)
        father_grammar_dir = os.path.join(GRAMMAR_ROOT_DIR, father_dir)
        if not os.path.exists(father_grammar_dir):
            if not os.path.exists(GRAMMAR_ROOT_DIR):
                os.mkdir(GRAMMAR_ROOT_DIR)
            os.mkdir(father_grammar_dir)
        grammar_dir = os.path.join(father_grammar_dir, dir_name)
        if os.path.exists(grammar_dir):
            shutil.rmtree(grammar_dir)
        os.mkdir(grammar_dir)
    elif father_dir:  # If only father_dir is provided
        test_case_dir = os.path.join(CASE_ROOT_DIR, father_dir)
        father_grammar_dir = os.path.join(GRAMMAR_ROOT_DIR, father_dir)
        if not os.path.exists(father_grammar_dir):
            if not os.path.exists(GRAMMAR_ROOT_DIR):
                os.mkdir(GRAMMAR_ROOT_DIR)
            os.mkdir(father_grammar_dir)
        expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, father_dir)
        if father_dir == 'test_swagger_website':
            expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, 'test_swagger_only', dir_name)
    elif dir_name:  # If only dir_name is provided
        test_case_dir = os.path.join(CASE_ROOT_DIR, dir_name)
        if not os.path.exists(grammar_dir):
            if not os.path.exists(GRAMMAR_ROOT_DIR):
                os.mkdir(GRAMMAR_ROOT_DIR)
            os.mkdir(grammar_dir)
        else:
            shutil.rmtree(grammar_dir)
            os.mkdir(grammar_dir)
        expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, dir_name)
        if father_dir == 'test_swagger_website':
            expected_grammar_dir = os.path.join(BASELINE_ROOT_DIR, 'test_swagger_only', dir_name)
    config_json = None
    if DebugConfig().swagger_only:
        swagger_file = os.path.join(test_case_dir, swagger_only)
        if os.path.exists(swagger_file):
            config_json = copy.deepcopy(business_config)
            config_json["SwaggerSpecFilePath"] = [swagger_file]
            obj_config = Config.init_from_json(config_json)
        else:
            raise Exception(f"swagger file {swagger_file} not exist!")
    else:
        config_file_path = os.path.join(test_case_dir, 'config.json')
        if os.path.exists(config_file_path):
            config_json = JsonSerialization.try_deeserialize_from_file(config_file_path)
            final_config = copy.deepcopy(business_config)
            final_config.update(config_json)
            obj_config = Config.init_from_json(final_config)
            obj_config.convert_relative_to_abs_paths(config_file_path)
        else:
            raise Exception(f"config file {config_file_path}")

    obj_config.GrammarOutputDirectoryPath = grammar_dir
    if not os.path.exists(obj_config.GrammarOutputDirectoryPath):
        os.makedirs(obj_config.GrammarOutputDirectoryPath)

    generate_restler_grammar(obj_config)
    actual_grammar_file = os.path.join(grammar_dir, Constants.DefaultJsonGrammarFileName)
    expected_grammar_file = os.path.join(expected_grammar_dir, Constants.DefaultJsonGrammarFileName)
    no_diff = True
    if DebugConfig().validate_grammar:
        no_diff, diff = compare_difference(actual_grammar_file, expected_grammar_file)
        if not no_diff:
            return False, (f"Grammar file: {Constants.DefaultJsonGrammarFileName}"
                           f" does not match baseline. First difference: {diff}")

        if not DebugConfig().skip_python_check:
            actual_grammar_file = os.path.join(grammar_dir, Constants.DefaultRestlerGrammarFileName)
            expected_grammar_file = os.path.join(expected_grammar_dir, Constants.DefaultRestlerGrammarFileName)
            found_diff, diff = get_line_differences(actual_grammar_file, expected_grammar_file)
            if found_diff and DebugConfig().debug_func() == 'compiler':
                return False, diff

        if checking_more:
            for item in checking_more:
                actual_grammar_file = os.path.join(grammar_dir, item)
                expected_grammar_file = os.path.join(expected_grammar_dir, item)
                no_diff, diff = compare_difference(actual_grammar_file, expected_grammar_file)
                if not no_diff:
                    return False, (f"checking file: {item}"
                                   f" does not match baseline. First difference: {diff}")

        if DebugConfig().debug_func() == 'compiler' and no_diff:
            return True, "Finish"

    if DebugConfig().debug_func() == 'restler':
        restler_file_setting = None
        if os.path.exists(os.path.join(test_case_dir, Restler_User_Settings)):
            restler_file_setting = load_common_engine(test_case_dir)

        params = ExecuteParam(settings=restler_file_setting,
                              working_dir=test_case_dir,
                              restler_grammar=os.path.join(grammar_dir,
                                                           Constants.DefaultRestlerGrammarFileName),
                              enable_checkers=[],
                              disable_checkers=[])
        execute_restler(config_arg=params)
        return True, "Skip the grammar validate! Finish generate compiler and do fuzz checking!"

    return True, "Skip the grammar validate! Just finish generate compiler!"
