import unittest
import os
import shutil
from compiler.code_generate import (
    format_restler_primitive,
    generate_python_parameter,
    SPACE,
    get_requests)
from compiler.grammar import (
    Constant,
    LeafNode,
    PrimitiveType,
    LeafProperty,
    DynamicObject,
    RequestParameter,
    NestedType,
    ParameterList,
    Request,
    RequestId,
    OperationMethod,
    ParameterPayloadSource,
    RequestMetadata,
    RequestDependencyData,
    TokenKind,
    InternalNode,
    InnerProperty,
    ParameterKind)
from compiler.config import Config, ConfigSetting

from compiler.workflow import generate_restler_grammar, Constants
from compiler_ut.utilities import (
    TEST_ROOT_DIR,
    SWAGGER_DIR,
    compare_difference,
    DebugConfig,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestCodeGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_ROOT_DIR):
            shutil.rmtree(TEST_ROOT_DIR)

        if not os.path.exists(TEST_ROOT_DIR):
            os.mkdir(TEST_ROOT_DIR)

    def assert_json_file(self, source_dir, target_dir):
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

    # Test that after a grammar is produced (e.g. from a Swagger spec), the json grammar
    # can be modified manually to re-generate the Python grammar.
    # This is useful because the grammar json is validated
    # when deserialized by the RESTler compiler, avoiding typos made directly in python.
    # This also sanity checks that the grammar generation is deterministic.
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_python_grammar_request_sanity"))
    def test_python_grammar_request_sanity(self):
        constant_1 = Constant(primitive_type=PrimitiveType.Number, variable_name="1")

        leaf_node_1 = LeafNode(
            leaf_property=LeafProperty(name="page", payload=constant_1, is_required=True, is_readonly=False))
        leaf_node_2 = LeafNode(
            leaf_property=LeafProperty(name="page", payload=constant_1, is_required=True, is_readonly=False))
        constant_2 = Constant(primitive_type=PrimitiveType.String, variable_name="hello")
        leaf_node_3 = LeafNode(
            leaf_property=LeafProperty(name="payload", payload=constant_2, is_required=True, is_readonly=False))
        constant_3 = Constant(primitive_type=PrimitiveType.String, variable_name="api")

        constant_4 = Constant(primitive_type=PrimitiveType.String, variable_name="accounts")

        payload = DynamicObject(primitive_type=PrimitiveType.Int, variable_name="accountId",
                                is_writer=False)

        path_payload = [constant_3, constant_4, payload]

        query_list = [RequestParameter(name="", payload=leaf_node_1, serialization=None),
                      RequestParameter(name="", payload=leaf_node_2, serialization=None)]
        query_param = [(ParameterPayloadSource.Schema, ParameterList(request_parameters=query_list))]

        leaf_node_body = LeafNode(
            leaf_property=LeafProperty(name="theBody", payload=constant_1, is_required=True, is_readonly=False))
        body_list = [RequestParameter(name="", payload=leaf_node_body, serialization=None)]
        body_param = [(ParameterPayloadSource.Schema, ParameterList(request_parameters=body_list))]

        dependency_data = RequestDependencyData(response_parser=None,
                                                input_writer_variables=[],
                                                ordering_constraint_writer_variables=[],
                                                ordering_constraint_reader_variables=[])

        request_id = RequestId(endpoint="/api/accounts/{accountId}",
                               method=OperationMethod.Put, xms_path=None, has_example=False)
        request_id = Request(request_id=request_id,
                             method=OperationMethod.Put,
                             base_path="",
                             path=path_payload,
                             query_parameters=query_param,
                             body_parameters=body_param,
                             header_parameters=[],
                             token=TokenKind.Refreshable,
                             headers=[("Accept", "application/json"), ("Host", "fromSwagger"),
                                      ("Content-Type", "application/json")],
                             http_version="1.1",
                             dependency_data=dependency_data,
                             request_metadata=RequestMetadata(is_long_running_operation=False))

        elements = get_requests(requests=[request_id])
        self.assertTrue(len(elements) > 0)

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_python_grammar_parameter_sanity"))
    def test_python_grammar_parameter_sanity(self):
        constant_1 = Constant(primitive_type=PrimitiveType.Number, variable_name="WestUS")

        leaf_node_1 = LeafNode(
            leaf_property=LeafProperty(name="region", payload=constant_1, is_required=True, is_readonly=False))

        constant_2 = Constant(primitive_type=PrimitiveType.Number, variable_name="10")

        leaf_node_2 = LeafNode(
            leaf_property=LeafProperty(name="maxResources", payload=constant_2, is_required=True, is_readonly=False))

        inner_property = InnerProperty(name="subscription", payload=None, property_type=NestedType.Object,
                                       is_required=True, is_readonly=False)

        internal_node = InternalNode(inner_property=inner_property, leaf_properties=[leaf_node_1, leaf_node_2])

        request_parameter = RequestParameter(name="theBody", payload=internal_node,
                                             serialization=None)

        result = generate_python_parameter(parameter_source=ParameterPayloadSource.Schema,
                                           parameter_kind=ParameterKind.Body,
                                           request_parameter=request_parameter)

        format_str = ""
        for s in result:
            str_value = format_restler_primitive(s)
            if str_value:
                format_str = format_str + f"{SPACE}{str_value},\n"

        region = f"{"region":}"
        try:
            has_region = format_str.index(region)
        except ValueError:
            has_region = True
        self.assertTrue(has_region, "region not found")
        max_resources = f"{"maxResources":}"
        try:
            has_resources = format_str.index(max_resources)
        except ValueError:
            has_resources = True

        self.assertTrue(has_resources, "resources not found")
        subscription = f"{"subscription":}"
        try:
            has_sub = format_str.index(subscription)
        except ValueError:
            has_sub = True
        self.assertTrue(has_sub, "subscription not found")

    # Test that the generated python and json grammars for tracked parameters are correct
    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_tracked_parameters"))
    def test_tracked_parameters(self):
        source_dir = os.path.join(TEST_ROOT_DIR, "example_demo1")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        config = {
            "IncludeOptionalParameters": True,
            "GrammarOutputDirectoryPath": source_dir,
            "ResolveBodyDependencies": True,
            "UseBodyExamples": False,
            "SwaggerSpecFilePath": [os.path.join(SWAGGER_DIR, "example_demo1.json")],
            "CustomDictionaryFilePath": os.path.join(SWAGGER_DIR, "example_demo_dictionary.json")
        }
        obj_config = Config.init_from_json(config)
        generate_restler_grammar(obj_config)
        with open(os.path.join(source_dir, "grammar.py"), 'r') as f:
            grammar = f.read()
        # The grammar should not contain tracked parameters by default
        self.assertFalse("param_name=" in grammar)

        source_dir = os.path.join(TEST_ROOT_DIR, "example_demo2")
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        # Now turn on parameter tracking
        ConfigSetting().TrackFuzzedParameterNames = True
        ConfigSetting().GrammarOutputDirectoryPath = source_dir

        generate_restler_grammar(ConfigSetting())
        with open(os.path.join(source_dir, "grammar.py"), 'r') as f:
            grammar = f.read()

        param_storeId = f"param_name=\"storeId\""
        param_banned_brands = f"param_name=\"bannedBrands\""
        param_grocery_item_tags = f"param_name=\"groceryItemTags\""
        self.assertIn(param_storeId, grammar)
        self.assertIn(param_banned_brands, grammar)
        self.assertIn(param_grocery_item_tags, grammar)


if __name__ == "__main__":
    unittest.main()
