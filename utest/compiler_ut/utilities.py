import json
import os
import random
import difflib
from compiler.utilities import JsonSerialization
from deepdiff import DeepDiff
import unittest

TEST_ROOT_DIR = os.path.join(os.getcwd(), "test_output")
SWAGGER_DIR = os.path.join(os.getcwd(), "compiler_ut", "swagger")


class NewSingletonError(Exception):
    pass


class UninitializedError(Exception):
    pass


def read_and_clean_file(file_path):
    """读取文件并去除空行和行首尾空格"""
    with open(file_path, 'r') as file:
        cleaned_lines = []
        for line in file:
            cleaned_line = line.strip()  # 去除行首和行尾的空白字符
            while "temp_" in cleaned_line:
                start_1 = cleaned_line.index("temp_")
                substr = cleaned_line[start_1:start_1 + len("temp_") + 4]
                cleaned_line = cleaned_line.replace(substr, "temp")

            if cleaned_line:  # 忽略空行
                cleaned_lines.append(cleaned_line)
    return cleaned_lines


def get_line_differences(expected_file_path, actual_file_path):
    cleaned_expected_file = read_and_clean_file(expected_file_path)
    cleaned_actual_file = read_and_clean_file(actual_file_path)
    # 使用 difflib 进行比较
    diff = difflib.unified_diff(cleaned_expected_file, cleaned_expected_file, lineterm='')
    differences_found = False
    str_value = ""
    for line in diff:
        if line:  # 只打印非空行
            str_value = str_value + "\n" + line
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
        file_path = os.path.join(os.path.dirname(__file__), "compiler_ut.json")
        with open(file_path) as data_handler:
            self._config_data = json.load(data_handler)
            data_handler.close()
        DebugConfigCases.__instance = self

    def get_cases_config(self, test_module, test_func):
        if self._config_data["debug_mode"]:
            return not self._config_data[test_module][test_func] == 2
        else:
            return False or self._config_data[test_module][test_func] != 0

    def get_x_ms_examples(self):
        return not self._config_data["x-ms-examples"]

    def get_open_api_v2(self):
        return not self._config_data["openapi_2.0"]

    def get_open_api_v3(self):
        return not self._config_data["openapi_3.0"]

    def get_debug_mode(self):
        return self._config_data["debug_mode"]

    def get_debug_file(self):
        return self._config_data["debug_file"]

    def get_debug_compiler(self):
        return self._config_data["compiler_ut"]

    def get_debug_reslter(self):
        return self._config_data["restler_ut"]
