# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import json
import sys
from pathlib import Path
import signal
import argparse
import logging


if __name__ == '__main__' and 'compiler' not in sys.modules:
    autotest_dir = Path(__file__).absolute().parent
    sys.path = [str(autotest_dir.parent)] + [p for p in sys.path if Path(p) != autotest_dir]
    print(f"autotest_dir={autotest_dir} sys.path={sys.path}")

from rest.compiler.code_generate import (
    generate_code,
    generate_custom_value_gen_template)
from rest.compiler.swagger import SwaggerDoc
from rest.compiler.annotations import get_global_annotations_from_file
from rest.compiler.dictionary import (
    init_user_dictionary,
    get_dictionary,
    get_dictionary_from_string)
from rest.compiler.config import (
    ConfigSetting,
    Config,
    convert_to_abs_path,
    SwaggerSpecConfigClass)
from rest.compiler.utilities import JsonSerialization
from rest.compiler.example import get_example_config_file
from rest.compiler.compiler import generate_request_grammar
from rest.compiler.restler_engine_settings import update_engine_settings
from rest.restler.utils import restler_logger as logger


class Constants:
    DefaultJsonGrammarFileName = "grammar.json"
    DefaultRestlerGrammarFileName = "grammar.py"
    NewDictionaryFileName = "dict.json"
    UnresolvedDependenciesFileName = "unresolved_dependencies.json"
    DependenciesFileName = "dependencies.json"
    DependenciesDebugFileName = "dependencies_debug.json"
    DefaultExampleMetadataFileName = "examples.json"
    DefaultEngineSettingsFileName = "engine_settings.json"
    CustomValueGeneratorTemplateFileName = "custom_value_gen_template.py"
    DefaultAnnotationFileName = "annotations.json"
    DefaultCompilerConfigName = "config.json"
    DefaultGrammarOutputDirectory = "Compile"


class GrammarGroup:
    json_grammar: str
    python_grammar: str
    swagger_doc: str

    def __init__(self, swagger_doc_file):
        self.json_grammar = ""
        self.python_grammar = ""
        self.swagger_doc = swagger_doc_file


def generate_python(grammar_output_directory_path, grammar):
    code_file = os.path.join(grammar_output_directory_path, Constants.DefaultRestlerGrammarFileName)
    try:
        with open(code_file, "w", encoding='utf-8') as file:
            generate_code(grammar, file.writelines)
            file.close()
    except Exception as err:
        import traceback
        traceback.print_stack()
        print(f"Exception writing to main log: {err!s}")
    finally:
        return


def get_swagger_data_for_doc(doc: SwaggerSpecConfigClass,
                             working_directory: str) -> SwaggerDoc:
    swagger_object = SwaggerDoc()
    swagger_object.get_swagger_document(swagger_path=doc.SpecFilePath,
                                        working_directory=working_directory)

    logger.write_to_main(f"swagger_doc={swagger_object.__str__()}", ConfigSetting().LogConfig.work_flow)

    if doc.AnnotationFilePath:
        logger.write_to_main(f"AnnotationFilePath={doc.AnnotationFilePath}", ConfigSetting().LogConfig.work_flow)
        if os.path.exists(doc.AnnotationFilePath):
            swagger_object.global_annotations = get_global_annotations_from_file(doc.AnnotationFilePath)
        else:
            print(f"ERROR: invalid path found in the list of annotation files given: {doc.AnnotationFilePath}")
            raise ValueError("Invalid annotation file path")

    dictionary = None
    if doc.DictionaryFilePath or doc.Dictionary:
        if doc.DictionaryFilePath:
            if os.path.exists(doc.DictionaryFilePath):
                dictionary = get_dictionary(doc.DictionaryFilePath)
            else:
                print(f"ERROR: invalid path found in the list of dictionary files given: {doc.DictionaryFilePath}")
                raise ValueError("Invalid dictionary file path")
        else:
            dictionary = get_dictionary_from_string(doc.Dictionary)
    swagger_object.dictionary = dictionary
    # todo not support x-ms-paths
    # xms_paths_mapping = preprocessing_result.value.xMs_paths_mapping if preprocessing_result else None
    xms_paths_mapping = ''
    return swagger_object


# generateGrammarFromSwagger
def generate_grammar_from_swagger(grammar_output_directory_path: str):
    # Extract the Swagger documents and corresponding document-specific configuration, if any
    swagger_spec_configs: list[SwaggerSpecConfigClass] = (
        ConfigSetting().get_swagger_spec_configs_from_compiler_config())

    dictionary = init_user_dictionary()
    configured_swagger_docs: list[SwaggerDoc] = []
    for doc in swagger_spec_configs:
        logger.write_to_main(f"type(doc)={type(doc)}", ConfigSetting().LogConfig.work_flow)
        temp_value = get_swagger_data_for_doc(doc, grammar_output_directory_path)
        configured_swagger_docs.append(temp_value)

    if ConfigSetting().CustomDictionaryFilePath is not None:
        dictionary_file_path = ConfigSetting().CustomDictionaryFilePath
        dictionary = get_dictionary(dictionary_file_path)

    logger.write_to_main(f"dictionary={dictionary.__dict__()}", ConfigSetting().LogConfig.work_flow)
    global_external_annotations = []

    string_value = ConfigSetting().AnnotationFilePath
    if string_value and os.path.exists(ConfigSetting().AnnotationFilePath):
        global_external_annotations = get_global_annotations_from_file(ConfigSetting().AnnotationFilePath)
    elif string_value:
        raise ValueError(f"ERROR: invalid global annotation file given: {ConfigSetting().AnnotationFilePath}")

    examples_directory = ConfigSetting().ExamplesDirectory \
        if ConfigSetting().ExamplesDirectory else os.path.join(grammar_output_directory_path, "examples")

    if ConfigSetting().DiscoverExamples:
        if not os.path.exists(examples_directory):
            os.mkdir(examples_directory)

    user_specified_examples = []
    if ConfigSetting().ExampleConfigFilePath:
        example_file = get_example_config_file(ConfigSetting().ExampleConfigFilePath, False)
        if example_file:
            user_specified_examples.append(example_file)
    if ConfigSetting().ExampleConfigFiles:
        for ecf in ConfigSetting().ExampleConfigFiles:
            example_file = get_example_config_file(ecf.file_path, ecf.exact_copy)
            if example_file:
                user_specified_examples.append(example_file)

    logger.write_to_main(f"user_specified_examples={user_specified_examples}", ConfigSetting().LogConfig.work_flow)

    grammar, dependencies, new_dictionary, per_resource_dictionaries, examples = (
        generate_request_grammar(
            configured_swagger_docs,
            dictionary,
            global_external_annotations,
            user_specified_examples))

    grammar_file_path = os.path.join(grammar_output_directory_path, Constants.DefaultJsonGrammarFileName)
    logger.write_to_main("grammar={}".format(grammar.__dict__()), ConfigSetting().LogConfig.work_flow)
    JsonSerialization.serialize_to_file(grammar_file_path, grammar.__dict__())

    # The below statement is present as an assertion, to check for deserialization issues for
    # specific grammars.
    TEST_GRAMMAR = False
    if TEST_GRAMMAR:
        with open(grammar_file_path, 'r') as file_handler:
            json_data = json.load(file_handler)
        file_handler.close()

    # If examples were discovered, create a new examples file
    if ConfigSetting().DiscoverExamples:
        discovered_examples_file_path = os.path.join(examples_directory, Constants.DefaultExampleMetadataFileName)
        if isinstance(examples, list):
            str_value = ''
            for item in examples:
                # str_value = str_value + item[1].__dict__()
                pass
            JsonSerialization.serialize_to_file(discovered_examples_file_path, str_value)
        else:
            JsonSerialization.serialize_to_file(discovered_examples_file_path, examples.__dict__())

    # Write the updated dictionary.
    def write_dictionary(dictionary_mame, new_dict_mutation):
        new_dictionary_file_path = os.path.join(grammar_output_directory_path, dictionary_mame)
        current_dict = init_user_dictionary()
        print("Writing new dictionary to", new_dictionary_file_path)
        # A helper function to override defaults with user-specified dictionary values
        # when the user specifies only some of the properties
        current_dict.merged_dictionary(new_dict_mutation)
        JsonSerialization.serialize_to_file(new_dictionary_file_path, current_dict.__dict__())

    # todo
    write_dictionary(Constants.NewDictionaryFileName, new_dictionary)

    new_dict_json = json.dumps(new_dictionary.__dict__())
    custom_value_generator_template_file_path = os.path.join(grammar_output_directory_path,
                                                             Constants.CustomValueGeneratorTemplateFileName)
    template_lines = generate_custom_value_gen_template(new_dict_json)

    with open(custom_value_generator_template_file_path, 'w', encoding='utf-8') as file_handler:
        for item in template_lines:
            file_handler.writelines(item)
        file_handler.close()

    # todo

    if per_resource_dictionaries and len(per_resource_dictionaries) > 1:
        for dict_name, dict_contents in per_resource_dictionaries.items():
            write_dictionary(f"{dict_contents[0][0]}.json", dict_contents[0][1])

    # unresolved_dependencies_file_path = os.path.join(grammar_output_directory_path,
    #                                                 Constants.UnresolvedDependenciesFileName)

    # write_dependencies(unresolved_dependencies_file_path, dependencies, True)
    # dependencies_file_path = os.path.join(grammar_output_directory_path, Constants.DependenciesFileName)
    # write_dependencies(dependencies_file_path, dependencies, False)

    # dependencies_debug_file_path = os.path.join(grammar_output_directory_path, Constants.DependenciesDebugFileName)

    # write_dependencies_debug(dependencies_debug_file_path)

    # 更新引擎设置
    new_engine_settings_file_path = os.path.join(grammar_output_directory_path, Constants.DefaultEngineSettingsFileName)
    logger.write_to_main(f"per_resource_dictionaries={per_resource_dictionaries}, "
                         f"len(per_resource_dictionaries)={len(per_resource_dictionaries)}",
                         ConfigSetting().LogConfig.work_flow)

    update_engine_settings_result = update_engine_settings(grammar.Requests, per_resource_dictionaries,
                                                           ConfigSetting().EngineSettingsFilePath,
                                                           grammar_output_directory_path,
                                                           new_engine_settings_file_path)
    if not update_engine_settings_result:
        print(update_engine_settings_result)
        exit(1)

    return grammar


def load_log_config(config: Config):
    file_name = os.path.join(os.path.dirname(__file__), "compiler_settings.json")
    config.LogConfig.init_from_json(config_args=JsonSerialization.try_deeserialize_from_file(file_name))


# generateRestlerGrammar
def generate_restler_grammar(config: Config):
    load_log_config(config)
    grammar_output_directory_path = ConfigSetting().GrammarOutputDirectoryPath
    if grammar_output_directory_path is None:
        raise ValueError("GrammarOutputDirectoryPath must be specified in the config")

    if not os.path.exists(grammar_output_directory_path):
        os.makedirs(grammar_output_directory_path)

    if ConfigSetting().ExamplesDirectory == "":
        ConfigSetting().ExamplesDirectory = grammar_output_directory_path

    logger.create_experiment_dir(grammar_output_directory_path)

    grammar_input_file_path = ConfigSetting().GrammarInputFilePath

    if grammar_input_file_path and os.path.exists(grammar_input_file_path):
        with open(grammar_input_file_path, "r") as file:
            grammar = json.load(file)
    else:
        print(f"Generating grammar...{grammar_output_directory_path}")
        grammar = generate_grammar_from_swagger(grammar_output_directory_path)
    print(f"Generating Python grammar...")
    generate_python(grammar_output_directory_path, grammar)
    print("Done generating Python grammar.")
    print(f"Workflow completed. See {grammar_output_directory_path} for REST-ler grammar.")

    return grammar


def main(args):
    if args.api_spec is not None:
        if os.path.exists(args.api_spec):
            obj = Config()
            if ConfigSetting().GrammarOutputDirectoryPath == "":
                ConfigSetting().GrammarOutputDirectoryPath = (
                    convert_to_abs_path(os.path.dirname(__file__), Constants.DefaultGrammarOutputDirectory))
            if isinstance(args.api_spec, str):
                ConfigSetting().SwaggerSpecFilePath = [convert_to_abs_path(os.path.dirname(__file__),
                                                                           args.api_spec)]
    elif args.config is not None:
        config_file_path = args.config
        if os.path.exists(config_file_path):
            json_config = JsonSerialization.try_deeserialize_from_file(config_file_path)
            obj = Config.init_from_json(config=json_config)
            if ConfigSetting().GrammarOutputDirectoryPath is None:
                raise Exception("'GrammarOutputDirectoryPath' must be specified in the config file.")
            else:
                if ConfigSetting().GrammarOutputDirectoryPath == "":
                    ConfigSetting().GrammarOutputDirectoryPath = (
                        convert_to_abs_path(os.path.dirname(__file__), Constants.DefaultGrammarOutputDirectory))
                obj.convert_relative_to_abs_paths(config_file_path)
        else:
            print("Path not found:", config_file_path)
            sys.exit(1)
    else:
        print("exit")
        sys.exit(1)

    generate_restler_grammar(ConfigSetting())

    return 0


def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    # Stop the Sync Manager process to avoid a zombie process
    global MANAGER_HANDLE
    if MANAGER_HANDLE is not None:
        MANAGER_HANDLE.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--api_spec', help='API Spec IP',
                        type=str, default=None, required=False)
    parser.add_argument('--config', help='API Spec IP',
                        type=str, default=None, required=False)
    args = parser.parse_args()
    api_spec = args.api_spec
    main(args)
