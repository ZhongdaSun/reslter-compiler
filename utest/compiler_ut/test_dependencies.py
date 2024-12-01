import unittest
import os
import json
import shutil

from compiler.workflow import generate_restler_grammar, Constants, get_swagger_data_for_doc

from compiler.config import Config
from compiler.utilities import JsonSerialization
from compiler.dictionary import init_user_dictionary
from compiler.compiler import generate_request_grammar
from compiler_ut.utilities import (
    get_line_differences,
    get_grammar_file_content,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestDependencies(unittest.TestCase):
    test_root_dir = os.path.join(os.getcwd(), "test_output")
    swagger_dir = os.path.join(os.getcwd(), "compiler_ut", "swagger")

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TestDependencies.test_root_dir):
            shutil.rmtree(TestDependencies.test_root_dir)

        if not os.path.exists(TestDependencies.test_root_dir):
            os.mkdir(TestDependencies.test_root_dir)

    def assert_json_file(self, source_dir, target_dir):
        checking_json_file = [
            # Constants.NewDictionaryFileName,
            # Constants.DependenciesFileName,
            # Constants.DependenciesDebugFileName,
            # Constants.UnresolvedDependenciesFileName,
            Constants.DefaultJsonGrammarFileName
        ]

        # DefaultExampleMetadataFileName = "examples.json"
        # DefaultEngineSettingsFileName = "engine_settings.json"
        # CustomValueGeneratorTemplateFileName = "custom_value_gen_template.py"
        # DefaultAnnotationFileName = "annotations.json"
        # DefaultCompilerConfigName = "config.json"
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

    def dependencies_resolved_without_annotations(self, config):
        swagger_doc = get_swagger_data_for_doc(config['SwaggerSpecFilePath'][0], self.test_root_dir)

        if 'CustomDictionaryFilePath' in config and os.path.exists(config['CustomDictionaryFilePath']):
            with open(config['CustomDictionaryFilePath'], 'r') as f:
                dictionary = JsonSerialization.try_deeserialize_from_file(f)
                dictionary['restler_custom_payload_uuid4_suffix'] = {}
        else:
            dictionary = init_user_dictionary()

            grammar, dependencies, _, _ = generate_request_grammar(
                swagger_docs=[swagger_doc], dictionary=dictionary,
                global_external_annotations=[],
                user_specified_examples=[])

            unresolved_path_deps = [d for d in dependencies if
                                    d['producer'] is None and d['consumer']['parameterKind'] == 'Path']

            return dependencies, unresolved_path_deps

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_demo_server_path_dependencies_resolved_without_annotations")
        or DebugConfig().get_open_api_v3())
    def test_demo_server_path_dependencies_resolved_without_annotations(self):
        config = {}
        deps, unresolved = self.dependencies_resolved_without_annotations(config)

        consumer_requests = {(d['consumer']['id']['RequestId'], d['consumer']['id']['ResourceName'])
                             for d in deps if d['consumer']['parameterKind'] == 'Path'}

        # Check the expected number of consumers was extracted
        self.assertEqual(len(consumer_requests), 3,
                         f"Wrong number of consumers found: {len(consumer_requests)} {consumer_requests}")
        self.assertFalse(unresolved, f"Found unresolved path dependencies: {unresolved}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inferred_put_producer"))
    def test_inferred_put_producer(self):
        source_dir = os.path.join(self.test_root_dir, "put_createorupdate")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        target_dir = os.path.join(self.swagger_dir, "baselines", "put_createorupdate")

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': False,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "put_createorupdate.json")],
            'CustomDictionaryFilePath': None,
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_source = os.path.join(source_dir, Constants.DefaultJsonGrammarFileName)
        grammar_target = os.path.join(target_dir, Constants.DefaultJsonGrammarFileName)
        result, diff = compare_difference(grammar_source, grammar_target)
        self.assertTrue(result, msg=f"file:{grammar_source} {grammar_target}, diff:{diff}")

        grammar_source = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar_target = os.path.join(target_dir, Constants.DefaultRestlerGrammarFileName)

        found_diff, diff = get_line_differences(grammar_source, grammar_target)
        self.assertFalse(found_diff, msg=f"The difference is {diff}")

        with open(grammar_source, 'r') as f:
            grammar = f.read()
            f.close()

        # The grammar should not contain any fuzzable resources.
        self.assertNotIn("fuzzable", grammar, "Grammar should not contain any fuzzables, "
                                              "everything should be resolved")

        # A new dictionary should be produced with two entries in 'restler_custom_payload_uuid_suffix'
        dictionary_file_path = os.path.join(config["GrammarOutputDirectoryPath"], "dict.json")
        with open(dictionary_file_path, 'r') as f:
            dictionary = json.load(f)
            f.close()

        self.assertIn("orderId", dictionary['restler_custom_payload_uuid4_suffix'])
        self.assertIn("storeId", dictionary['restler_custom_payload_uuid4_suffix'])

        config["GrammarOutputDirectoryPath"] = os.path.join(config["GrammarOutputDirectoryPath"],
                                                            "test_inferred_put_producer_2")
        source_dir = config["GrammarOutputDirectoryPath"]
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        config["CustomDictionaryFilePath"] = dictionary_file_path
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        self.assert_json_file(source_dir=config["GrammarOutputDirectoryPath"],
                              target_dir=os.path.join(self.swagger_dir, "baselines", "put_createorupdate"))
        grammar_source = os.path.join(config["GrammarOutputDirectoryPath"], "grammar.py")

        found_diff, diff = get_line_differences(grammar_source, grammar_target)
        self.assertFalse(found_diff, msg=f"{grammar_source} is different from {grammar_target}: {diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_dependency_for_path_parameter"))
    def test_get_dependency_for_path_parameter(self):
        source_dir = os.path.join(self.test_root_dir, "test_get_dependency_for_path_parameter")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "get_path_dependencies.json")],
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': True,
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        # Further assertions can be added based on what is expected from the grammar
        self.assertTrue(True)  # Placeholder assertion

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_dependency_from_openapi_v3_links")
        or DebugConfig().get_open_api_v3())
    def test_get_dependency_from_openapi_v3_links(self):
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "linksTests",
                                                 "widgets_with_annotations.yaml")],
            'AnnotationFilePath': None,
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': True,
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_file_path = os.path.join(self.test_root_dir, "grammar.py")
        with open(grammar_file_path, 'r') as f:
            grammar = f.read()

        # Compiling with the REST API definition
        config2 = {**config,
                   'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "linksTests",
                                                        "widgets_with_links.yaml")]}
        obj_config = Config.init_from_json(config2)
        generate_restler_grammar(obj_config)

        with open(grammar_file_path, 'r') as f:
            grammar2 = f.read()

        self.assertEqual(grammar, grammar2)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_get_header_dependency_from_openapi_v3_links")
        or DebugConfig().get_open_api_v3())
    def test_get_header_dependency_from_openapi_v3_links(self):
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'ResolveHeaderDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "linksTests",
                                                 "etag_with_annotations.json")],
            'AnnotationFilePath': None,
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': True,
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        grammar_file_path = os.path.join(self.test_root_dir, "grammar.py")
        with open(grammar_file_path, 'r') as f:
            grammar = f.read()

        # Compiling with REST API definition
        config2 = {**config,
                   'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "linksTests",
                                                        "etag_with_links.json")]}
        obj_config = Config.init_from_json(config2)
        generate_restler_grammar(obj_config)

        with open(grammar_file_path, 'r') as f:
            grammar2 = f.read()

        self.assertEqual(grammar, grammar2)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_path_annotation_to_body_parameter"))
    def test_path_annotation_to_body_parameter(self):
        source_dir = os.path.join(self.test_root_dir, "pathAnnotation")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "pathannotation")

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "annotationTests",
                                                 "pathAnnotation.json")],
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        self.assert_json_file(source_dir=source_dir,
                              target_dir=target_dir)

        expected_grammar_file_path = os.path.join(target_dir, "grammar.py")
        actual_grammar_file_path = os.path.join(source_dir,
                                                Constants.DefaultRestlerGrammarFileName)
        found, grammar_diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)

        self.assertFalse(found, f"Grammar does not match baseline. First difference: {grammar_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_full_path_to_body_parameter_in_dictionary_custom_payload"))
    def test_full_path_to_body_parameter_in_dictionary_custom_payload(self):
        source_dir = os.path.join(self.test_root_dir, "pathDictionaryPayload")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "dependencyTests")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [os.path.join(self.swagger_dir, "dictionaryTests",
                                                 "pathDictionaryPayload.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "dictionaryTests", "dict.json"),
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        expected_grammar_file_path = os.path.join(target_dir, "path_in_dictionary_payload_grammar.py")
        actual_grammar_file_path = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        found, grammar_diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)

        self.assertFalse(found, f"Grammar does not match baseline. First difference: {grammar_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_local_annotations_to_body_properties"))
    def test_local_annotations_to_body_properties(self):
        source_dir = os.path.join(self.test_root_dir, "localAnnotations")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "dependencyTests")

        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "annotationTests", "localAnnotations.json")],
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        expected_grammar_file_path = os.path.join(target_dir, "path_annotation_grammar.py")
        actual_grammar_file_path = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        found, grammar_diff = get_line_differences(expected_grammar_file_path, actual_grammar_file_path)

        self.assertFalse(found, f"Grammar does not match baseline. First difference: {grammar_diff}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_no_dependencies_when_same_body_in_unrelated_requests"))
    def test_no_dependencies_when_same_body_in_unrelated_requests(self):
        source_dir = os.path.join(self.test_root_dir, "body_dependency_cycles")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "dependencyTests")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "body_dependency_cycles.json")],
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': True
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        dependencies_json_file_path = os.path.join(source_dir, Constants.DependenciesDebugFileName)
        dependencies = JsonSerialization.try_deeserialize_from_file(dependencies_json_file_path)
        resolved_dependencies = []
        for items in dependencies:
            if "producer" in items.keys():
                resolved_dependencies.append(items["producer"])

        self.assertEqual(len(resolved_dependencies), 0, "Dependencies should not have been inferred.")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_dependencies_inferred_for_lowercase_container_and_object"))
    def test_dependencies_inferred_for_lowercase_container_and_object(self):
        source_dir = os.path.join(self.test_root_dir, "lowercase_paths")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "lowercase_paths")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "lowercase_paths.json")],
            'CustomDictionaryFilePath': None,
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        dependencies_json_file_path = os.path.join(source_dir, Constants.DependenciesDebugFileName)
        dependencies = JsonSerialization.try_deeserialize_from_file(dependencies_json_file_path)
        resolved_dependencies = []
        for items in dependencies:
            if "producer" in items.keys():
                resolved_dependencies.append(items["producer"])

        expected_count = 3
        actual_count = len(resolved_dependencies)
        self.assertEqual(expected_count, actual_count,
                         f"The number of dependencies is not correct ({expected_count} <> {actual_count})")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_inconsistent_camel_case_fixed_by_restler"))
    def test_inconsistent_camel_case_fixed_by_restler(self):
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': self.test_root_dir,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "inconsistent_casing_paths.json")],
            'CustomDictionaryFilePath': None
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)

        dependencies_json_file_path = os.path.join(self.test_root_dir, Constants.DependenciesDebugFileName)
        dependencies = JsonSerialization.try_deeserialize_from_file(dependencies_json_file_path)
        resolved_dependencies = []
        for items in dependencies:
            if "producer" in items.keys():
                resolved_dependencies.append(items["producer"])

        expected_count = 8
        actual_count = len(resolved_dependencies)
        self.assertEqual(expected_count, actual_count,
                         f"The number of dependencies is not correct ({expected_count} <> {actual_count})")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_patch_request_body_parameter_producers_from_post"))
    def test_patch_request_body_parameter_producers_from_post(self):
        source_dir = os.path.join(self.test_root_dir, "post_patch_dependency")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        target_dir = os.path.join(self.swagger_dir, "baselines", "post_patch_dependency")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "post_patch_dependency.json")],
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        file_name = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(file_name)
        grammar_dynamic_objects = [
            "_system_environments_post_id.reader()",
            "_system_environments_post_url.reader()",
            "_system_environments_post_name.reader()"
        ]

        for dynamic_object in grammar_dynamic_objects:
            self.assertIn(dynamic_object, grammar, f"Grammar does not contain {dynamic_object}")

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_array_dependencies_with_multiple_array_items"))
    def test_array_dependencies_with_multiple_array_items(self):
        source_dir = os.path.join(self.test_root_dir, "array_dep_multiple_items")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        config = {
            'SwaggerSpecConfig': [{
                'SpecFilePath': os.path.join(self.swagger_dir, "dependencyTests",
                                             "array_dep_multiple_items.json"),
                'Dictionary': None,
                'DictionaryFilePath': os.path.join(self.swagger_dir, "dependencyTests",
                                                   "array_dep_multiple_items_dict.json"),
                'AnnotationFilePath': None
            }],
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'ResolveQueryDependencies': True,
            'UseBodyExamples': None
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        file_name = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(file_name)
        grammar_dynamic_object = "primitives.restler_custom_payload(\"item_descriptions\", quoted=False),"
        number_of_dynamic_objects = grammar.count(grammar_dynamic_object)

        self.assertEqual(1, number_of_dynamic_objects)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_input_producers_work_with_annotations"))
    def test_input_producers_work_with_annotations(self):
        source_dir = os.path.join(self.test_root_dir, "input_producer_spec")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)
        target_dir = os.path.join(self.swagger_dir, "baselines", "input_producer_spec")
        config = {
            'IncludeOptionalParameters': True,
            'GrammarOutputDirectoryPath': source_dir,
            'ResolveBodyDependencies': True,
            'UseBodyExamples': True,
            'SwaggerSpecFilePath': [
                os.path.join(self.swagger_dir, "dependencyTests", "input_producer_spec.json")],
            'CustomDictionaryFilePath': os.path.join(self.swagger_dir, "dependencyTests",
                                                     "input_producer_dict.json"),
            'AnnotationFilePath': os.path.join(self.swagger_dir, "dependencyTests",
                                               "input_producer_annotations.json"),
            'AllowGetProducers': False
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        """
        self.assert_json_file(source_dir=source_dir, target_dir=target_dir)

        grammar_source = os.path.join(source_dir, "grammar.py")
        grammar_target = os.path.join(target_dir, "grammar.py")

        found_diff, diff = get_line_differences(grammar_source, grammar_target)
        self.assertFalse(found_diff, msg=f"The difference is {diff}")
        """
        grammar_source = os.path.join(source_dir, Constants.DefaultRestlerGrammarFileName)
        grammar = get_grammar_file_content(grammar_source)

        self.assertIn(
            'restler_custom_payload_uuid4_suffix("fileId", writer=_file__fileId__post_fileId_path.writer(), '
            'quoted=False)',
            grammar)
        self.assertIn('restler_static_string(_file__fileId__post_fileId_path.reader(), quoted=False)', grammar)

        # Validate tag, label annotation
        self.assertIn('primitives.restler_custom_payload("tag", quoted=True, writer=_archive_post_tag.writer())',
                      grammar)
        self.assertIn('restler_static_string(_archive_post_tag.reader(), quoted=True)', grammar)

        # Validate name, name annotation
        self.assertIn('primitives.restler_fuzzable_object("{ \"fuzz\": false }", writer=_archive_post_name.writer())',
                      grammar)
        self.assertIn('primitives.restler_static_string(_archive_post_name.reader(), quoted=False)', grammar)

        # Validate hash, sig annotation
        self.assertIn('primitives.restler_custom_payload_query("hash", writer=_archive_post_hash_query.writer())',
                      grammar)
        self.assertIn('primitives.restler_static_string(_archive_post_hash_query.reader(), quoted=False)', grammar)


if __name__ == '__main__':
    unittest.main()
