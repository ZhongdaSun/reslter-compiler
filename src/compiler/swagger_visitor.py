# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import json
from typing import Union
import re

from collections import defaultdict
from typing import Any, Optional, Tuple
from compiler.utilities import JsonSerialization
from compiler.grammar import (
    PrimitiveType,
    PrimitiveTypeEnum,
    LeafProperty,
    InnerProperty,
    InternalNode,
    FuzzablePayload,
    LeafNode,
    NestedType,
    get_primitive_type_from_string,
    DefaultPrimitiveValues,
    Tree)
from compiler.swagger import SwaggerDoc
from compiler.config import ConfigSetting
from compiler.swagger_spec_preprocess import (
    get_definition_ref,
    RefResolution,
    get_definition_reference)

from swagger.objects import (
    Schema,
    Parameter,
    Header,
    Response)


class UnsupportedType(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class NullArraySchema(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnsupportedArrayExample(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class UnsupportedRecursiveExample(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class SchemaUtilities:

    def __init__(self):
        pass

    @staticmethod
    def get_correct_example_value(example_object, param_type: str):
        if param_type is None or param_type == "":
            return example_object

        if example_object is None:
            if param_type == 'object':
                return {"Some": None}
            else:
                return example_object

        if isinstance(example_object, dict) and param_type == "object":
            return example_object
        elif isinstance(example_object, list) and param_type == "array":
            return example_object
        elif (isinstance(example_object, dict) or isinstance(example_object, list) and
              param_type in ["number", "int", "integer", "bool", "boolean", "str", "string"]):
            if isinstance(example_object, dict):
                return SchemaUtilities.get_correct_example_value(list(example_object.values())[0], param_type)
            elif isinstance(example_object, list):
                final_result = "["
                for index, item in enumerate(example_object):
                    if index == 0:
                        final_result = final_result + JsonSerialization.serialize(item)
                    else:
                        final_result = final_result + "," + JsonSerialization.serialize(item)
                final_result = final_result + "]"
                return final_result
            else:
                raise Exception(f"example dict {example_object} is not type{param_type}")
        elif isinstance(example_object, str) and param_type in ["number", "int", "integer"]:
            return f"{example_object}"
        else:
            if param_type in ["number"]:
                if isinstance(example_object, float) or isinstance(example_object, int):
                    return example_object
                else:
                    raise Exception(
                        f"{example_object} can't be changed to {param_type}.")
            elif param_type in ["int", "integer"]:
                if isinstance(example_object, int):
                    return example_object
                elif isinstance(example_object, str):
                    return JsonSerialization.serialize(example_object)
                else:
                    raise Exception(
                        f"{example_object} can't be changed to {param_type}.")
            elif param_type in ["bool", "boolean"]:
                if isinstance(example_object, bool):
                    return example_object
                elif isinstance(example_object, str):
                    return f"{example_object}"
                else:
                    raise Exception(
                        f"{example_object} can't be changed to {param_type}.")
            elif param_type in ["str", "string"]:
                if isinstance(example_object, str):
                    return example_object
                else:
                    raise Exception(
                        f"{example_object} can't be changed to {param_type}.")

    @staticmethod
    def format_example_value(example_object: Any) -> str:
        if isinstance(example_object, str):
            return example_object
        else:
            if example_object == {"Some": None}:
                return example_object
            else:
                return json.dumps(example_object, separators=(',', ':'))

    # Get an example value as a string, either directly from the 'example' attribute or
    # from the extension 'Examples' property.
    @staticmethod
    def try_get_schema_example_value(schema: Union[Schema, Parameter, Response]):
        if schema.is_set("example"):
            return getattr(schema, schema.get_private_name("example"))
        elif schema.is_set("examples"):
            extension_data_example = getattr(schema, schema.get_private_name("examples"))
            if extension_data_example:
                examples = extension_data_example if isinstance(extension_data_example, dict) else {}
                spec_example_values = [SchemaUtilities.format_example_value(example_value) for example_value in
                                       examples.values()]
                return spec_example_values[0]
        return None

    @staticmethod
    def get_grammar_primitive_type_with_default_value(object_type: str,
                                                      json_format: str,
                                                      example_value: Optional[str],
                                                      property_name: Optional[str]) \
            -> Tuple[PrimitiveType, str, str, Optional[str]]:
        track_parameters = ConfigSetting().TrackFuzzedParameterNames

        if object_type.lower() == "string":
            default_string_type = (PrimitiveType.String, DefaultPrimitiveValues[PrimitiveType.String],
                                   example_value,
                                   property_name)
            if json_format:
                format_lower = json_format.lower()
                if format_lower == "uuid" or format_lower == "guid":
                    return PrimitiveType.Uuid, DefaultPrimitiveValues[PrimitiveType.Uuid], example_value, property_name
                elif format_lower == "date-time" or format_lower == "datetime":
                    return PrimitiveType.DateTime, DefaultPrimitiveValues[
                        PrimitiveType.DateTime], example_value, property_name
                elif format_lower == "date":
                    return PrimitiveType.Date, DefaultPrimitiveValues[PrimitiveType.Date], example_value, property_name
                elif format_lower == "double":
                    return PrimitiveType.Number, DefaultPrimitiveValues[
                        PrimitiveType.Number], example_value, property_name
                else:
                    print(f"found unsupported format: {json_format}")
                    return default_string_type
            else:
                return default_string_type
        elif object_type.lower() == "number":
            return PrimitiveType.Number, DefaultPrimitiveValues[PrimitiveType.Number], example_value, property_name
        elif object_type.lower() == "int" or object_type == "integer":
            return PrimitiveType.Int, DefaultPrimitiveValues[PrimitiveType.Int], example_value, property_name
        elif object_type.lower() == "bool" or object_type == "boolean":
            return PrimitiveType.Bool, DefaultPrimitiveValues[PrimitiveType.Bool], example_value, property_name
        elif object_type.lower() == "object":
            return PrimitiveType.Object, DefaultPrimitiveValues[PrimitiveType.Object], example_value, property_name
        elif object_type.lower() == "array":
            raise Exception(
                f"{object_type} is not a fuzzable primitive type. Please make sure your Swagger file is valid.")

    @staticmethod
    def get_fuzzable_value_for_object_type(object_type: str,
                                           format_str: str,
                                           example_value: Optional[str],
                                           property_name: Optional[str]):
        primitive_type, default_value, example_value, property_name = (
            SchemaUtilities.get_grammar_primitive_type_with_default_value(object_type, format_str, example_value,
                                                                          property_name))
        fuzzable_value = FuzzablePayload(
            primitive_type=primitive_type,
            default_value=default_value,
            example_value=example_value,
            parameter_name=property_name,
            dynamic_object=None)
        return fuzzable_value

    @staticmethod
    def get_property_read_only(schema: Union[Schema, Parameter, Response]) -> bool:
        return (SchemaUtilities.get_property(schema, "readonly") or
                SchemaUtilities.get_property(schema, "readOnly"))

    @staticmethod
    def get_property(schema: Union[Schema, Parameter, Response], name: str) -> Union[dict, Schema, str, bool, None]:
        if name in ["readonly", "required", "explode", "readOnly"]:
            return bool(getattr(schema, schema.get_private_name(name))) if schema.is_set(name) else False
        elif name in ["properties", "examples", "example", "$ref", "schema", "items", "additionalProperties"]:
            if schema.is_set(name):
                return getattr(schema, schema.get_private_name(name))
            else:
                return None
        elif name in ["type", "name", "format", "in", "style"]:
            if schema.is_set(name):
                result = getattr(schema, schema.get_private_name(name))
                if isinstance(result, str):
                    return result
                # issue fix for atest/swagger_only/simple_swagger_all_param_data_types.json type: ["string"]
                elif isinstance(result, list):
                    return result[0]
                else:
                    raise Exception(f"{name} is {result}. Its type is not string")
            else:
                return ""
        else:
            raise Exception(f"property name: {name} is wrong!")


class CachedGrammarTree:
    def __init__(self, tree: Tree):
        self.tree = tree


class Cycle:
    def __init__(self, root, parents, members):
        self.root = root
        self.parents = parents
        self.members = members


class SchemaCache:
    cache = defaultdict(CachedGrammarTree)

    cycles = set()

    definition_cache = defaultdict()

    def __init__(self):
        self.cache = {}
        self.cycles = set()
        self.definition_cache = {}

    def add_cycle(self, schema_list):
        root = schema_list[0]
        members = [x for x in schema_list[1:] if x != root]
        members = [root] + members
        parents = schema_list[len(members) + 1:]
        cycle = Cycle(root, parents, members)
        self.cycles.add(cycle)

    def try_get(self, schema):
        return self.cache.get(schema, None)

    def add(self, schema, parents, grammar_element, is_example):
        cycles_with_schema = [cycle for cycle in self.cycles if schema in cycle.members]
        cycle_root = next((cycle for cycle in cycles_with_schema if cycle.root == schema and cycle.parents == parents),
                          None)

        should_cache = not is_example and (not cycles_with_schema or cycle_root is not None)

        if should_cache:
            self.cache[schema] = CachedGrammarTree(grammar_element)
        if cycle_root is not None:
            self.cycles.remove(cycle_root)

    def add_definition_cache(self, ref_definition, value):
        if ref_definition not in self.definition_cache.keys():
            self.definition_cache[ref_definition] = value

    def remove_definition_cache(self, ref_definition):
        if ref_definition in self.definition_cache.keys():
            self.definition_cache.pop(ref_definition)

    def try_get_definition_cache(self, ref_definition):
        return self.definition_cache.get(ref_definition, None)


class GenerateGrammarElements:
    @staticmethod
    def format_jtoken_property(primitive_type, raw_value):
        if primitive_type in ['array']:
            if raw_value is None:
                return None
            if len(raw_value) > 1 and (raw_value[0] == "'" or raw_value[0] == '"'):
                if raw_value[0] == '"' and raw_value[-1] == '"':
                    return raw_value[1:-1]
                else:
                    print(
                        f"WARNING: example file contains malformed value in property {primitive_type}. "
                        f"The compiler does not currently support this. Please modify the grammar manually "
                        f"to send the desired payload.")
                    return raw_value
        elif primitive_type in ["number", "int", "integer", "object", "boolean", "bool"]:
            if isinstance(raw_value, str):
                def is_in_correct_format(value):
                    # Check if the string starts and ends with escaped double quotes
                    return (value.startswith('\"') and value.endswith('\"')
                            or value.startswith('\'') and value.endswith('\''))
                if primitive_type in ["boolean", "bool"]:
                    return raw_value
                if is_in_correct_format(raw_value):
                    return raw_value
                else:
                    if primitive_type in ["int", "integer"]:
                        try:
                            return int(''.join(re.findall(r'\d+', raw_value)))
                        except ValueError:
                            return raw_value
                    else:
                        return eval(raw_value)
            else:
                return raw_value
        elif primitive_type in ["string"]:
            if raw_value is None:
                return "None"
            else:
                return raw_value
        else:
            return raw_value


# getFuzzableValueForProperty
def get_fuzzable_value_for_property(property_name: str,
                                    property_schema: Schema,
                                    enumeration,
                                    example_value: Optional):
    property_type = SchemaUtilities.get_property(property_schema, "type").lower()
    property_format = SchemaUtilities.get_property(property_schema, "format")

    if property_type in ["string", "number", "int", "boolean", "integer", "bool"]:
        if enumeration is None:
            fuzzable_value = SchemaUtilities.get_fuzzable_value_for_object_type(property_type,
                                                                                property_format,
                                                                                example_value,
                                                                                property_name)
            return fuzzable_value
        else:
            enum_values = [str(e) for e in enumeration]
            grammar_primitive_type, default_value, example_value, property_name = (
                SchemaUtilities.get_grammar_primitive_type_with_default_value(
                    property_type,
                    property_format,
                    example_value,
                    property_name))
            default_fuzzable_enum_value = enum_values[0] if enum_values else None
            fuzzable_value = FuzzablePayload(primitive_type=PrimitiveType.Enum,
                                             default_value=PrimitiveTypeEnum(name=property_name,
                                                                             primitive_type=get_primitive_type_from_string(
                                                                                 property_type),
                                                                             value=enumeration,
                                                                             default_value=default_fuzzable_enum_value),
                                             example_value=example_value,
                                             parameter_name=property_name,
                                             dynamic_object=None)
            return fuzzable_value
    elif property_type in ["object"] or property_type is None:
        # Example of JsonObjectType.None: "content": {} without a type specified in Swagger.
        # Let's treat these the same as Object.
        fuzzable_value = SchemaUtilities.get_fuzzable_value_for_object_type(PrimitiveType.Object,
                                                                            property_format,
                                                                            example_value,
                                                                            property_name)
        return fuzzable_value
    elif property_type == PrimitiveType.File:
        track_parameters = ConfigSetting().TrackFuzzedParameterNames
        fuzzable_value = FuzzablePayload(
            primitive_type=PrimitiveType.String,
            default_value="file object",
            example_value=None,
            parameter_name=property_name if track_parameters else None,
            dynamic_object=None
        )
        return fuzzable_value
    else:
        raise Exception(f"Unsupported type formatting: {property_type}")


# tryGetEnumeration
# issue fix for atest/swagger_only/simple_swagger_all_param_data_types.json
# "enum": [
#             1024,
#             512
#           ]
# output should be ["1024", "512"]
def try_get_enumeration(property_schema):
    enumeration = getattr(property_schema, property_schema.get_private_name("enum")) \
        if property_schema.is_set("enum") else None
    if enumeration:
        return [SchemaUtilities.format_example_value(item) for item in list(enumeration)]
    else:
        return None


# tryGetDefault
def try_get_default(property: Schema):
    default_value = property.get_private_name("default") \
        if property.is_set("default") and property.get_private_name("default").strip() else None
    return default_value


# addTrackedParameterName
def add_tracked_parameter_name(tree: Tree, param_name: str, is_readonly: bool):
    if not ConfigSetting().TrackFuzzedParameterNames:
        return tree

    if isinstance(tree, LeafNode):
        leaf_property = tree.leaf_property
        payload = leaf_property.payload
        leaf_property.is_readonly = is_readonly
        if isinstance(payload, FuzzablePayload):
            payload.parameter_name = param_name
            return LeafNode(leaf_property=leaf_property)
        else:
            return tree

    elif isinstance(tree, InternalNode):
        return tree


class ExampleHelpers:
    @staticmethod
    def get_array_examples(pv):
        max_array_elements_from_example = 5
        if pv:
            return pv[:max_array_elements_from_example]
        return None

    @staticmethod
    def try_get_array_schema_example(schema):
        schema_example_value = SchemaUtilities.try_get_schema_example_value(schema)
        schema_array_examples = ExampleHelpers.get_array_examples(schema_example_value)

        if schema_array_examples is None or not schema_array_examples:
            return None
        else:
            return [(example, True) for example in schema_array_examples]


def process_property(swagger_doc: SwaggerDoc,
                     property_name: str,
                     property_schema: [Schema, Parameter, Response],
                     property_payload_example_value,
                     generate_fuzzable_payload,
                     track_parameters: bool,
                     parents: list,
                     schema_cache: SchemaCache,
                     cont):
    # If an example value was not specified, also check for a locally defined example
    # in the Swagger specification.
    property_type = SchemaUtilities.get_property(property_schema, "type").lower()
    property_required = SchemaUtilities.get_property(property_schema, "required")
    is_readonly = SchemaUtilities.get_property_read_only(property_schema)
    if property_type in ["string", "number", "int", "boolean", "integer", "bool", "object"]:
        if property_type == "object" and (ConfigSetting().JsonPropertyMaxDepth is not None
                                          and len(parents) >= ConfigSetting().JsonPropertyMaxDepth):
            if property_payload_example_value is not None:
                property_payload_example_value = (
                    GenerateGrammarElements.format_jtoken_property(property_type, property_payload_example_value))

                property_payload_example_value = SchemaUtilities.format_example_value(property_payload_example_value)
            object_payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                             default_value="{ }",
                                             example_value=property_payload_example_value,
                                             parameter_name=property_name,
                                             dynamic_object=None)
            return LeafNode(leaf_property=LeafProperty(name=property_name,
                                                       payload=object_payload,
                                                       is_required=property_required,
                                                       is_readonly=is_readonly))
        else:
            fuzzable_property_payload = get_fuzzable_value_for_property(property_name,
                                                                        property_schema,
                                                                        try_get_enumeration(property_schema),
                                                                        SchemaUtilities.try_get_schema_example_value(
                                                                            property_schema))
            if property_payload_example_value is not None:
                property_payload_example_value = (
                    GenerateGrammarElements.format_jtoken_property(property_type, property_payload_example_value))

                example_property_payload = SchemaUtilities.format_example_value(property_payload_example_value)

                fuzzable_property_payload.example_value = example_property_payload
            else:
                fuzzable_property_payload.example_value = property_payload_example_value
            return LeafNode(leaf_property=LeafProperty(name=property_name,
                                                       payload=fuzzable_property_payload,
                                                       is_required=property_required,
                                                       is_readonly=is_readonly))
    elif property_type is None:
        obj_tree = generate_grammar_element_for_schema(swagger_doc,
                                                       property_schema,
                                                       property_payload_example_value,
                                                       generate_fuzzable_payload,
                                                       track_parameters,
                                                       property_required,
                                                       parents,
                                                       schema_cache,
                                                       cont)
        if isinstance(obj_tree, LeafNode):
            return cont(obj_tree)
        elif isinstance(obj_tree, InternalNode):
            inner_property = InnerProperty(name=property_name,
                                           payload=None,
                                           property_type=NestedType.Property,
                                           is_required=property_required,
                                           is_readonly=False)
            return InternalNode(inner_property=inner_property, leaf_properties=[obj_tree])
    elif property_type == "array":
        if not property_schema.is_set("items"):
            raise Exception("Invalid array schema: found array property without a declared element")

        array_item = getattr(property_schema, property_schema.get_private_name("items"))
        array_type = SchemaUtilities.get_property(array_item, "type").lower()
        array_read_only = SchemaUtilities.get_property_read_only(array_item)
        if array_read_only != is_readonly:
            array_item.update_field("readonly", is_readonly)
        inner_array_property = InnerProperty(name=property_name,
                                             payload=None,
                                             property_type=NestedType.Array,
                                             is_required=property_required,
                                             is_readonly=is_readonly)
        if array_type == "" and ConfigSetting().JsonPropertyMaxDepth is not None:
                if len(parents) >= ConfigSetting().JsonPropertyMaxDepth:
                    return InternalNode(inner_property=inner_array_property, leaf_properties=[])
                if len(parents) + 1 == ConfigSetting().JsonPropertyMaxDepth:
                    payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                              default_value="{ }",
                                              example_value=property_payload_example_value,
                                              parameter_name=property_name,
                                              dynamic_object=None)
                    leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                                    payload=payload,
                                                                    is_required=property_required,
                                                                    is_readonly=is_readonly))

                    return InternalNode(inner_property=inner_array_property, leaf_properties=[leaf_node])
        if array_type == "" and property_payload_example_value is None:
            array_with_elements = generate_grammar_element_for_schema(swagger_doc,
                                                                      array_item,
                                                                      property_payload_example_value,
                                                                      generate_fuzzable_payload,
                                                                      track_parameters,
                                                                      property_required,
                                                                      [property_schema] + parents,
                                                                      schema_cache,
                                                                      cont)
            if isinstance(array_with_elements, LeafNode):
                array_with_elements.leaf_property.is_required = property_required
            tree = add_tracked_parameter_name(array_with_elements, property_name, is_readonly)
            return InternalNode(inner_property=inner_array_property, leaf_properties=[tree])
        elif array_type == "":
            if isinstance(property_payload_example_value, dict):
                property_payload_example_value = property_payload_example_value.values()
            elif not isinstance(property_payload_example_value, list):
                property_payload_example_value = [property_payload_example_value]

            array_with_elements = []
            for item in property_payload_example_value:
                array_with_element = generate_grammar_element_for_schema(swagger_doc,
                                                                         array_item,
                                                                         item,
                                                                         generate_fuzzable_payload,
                                                                         track_parameters,
                                                                         property_required,
                                                                         [property_schema] + parents,
                                                                         schema_cache,
                                                                         cont)
                if isinstance(array_with_element, InternalNode):
                    tree = add_tracked_parameter_name(array_with_element, property_name, is_readonly)
                    array_with_elements.append(tree)
            return InternalNode(inner_property=inner_array_property, leaf_properties=array_with_elements)

        if property_payload_example_value is None:
            array_with_elements = process_property(swagger_doc,
                                                   "",
                                                   array_item,
                                                   property_payload_example_value,
                                                   generate_fuzzable_payload,
                                                   track_parameters,
                                                   parents,
                                                   schema_cache,
                                                   cont)
            if isinstance(array_with_elements, LeafNode):
                array_with_elements.leaf_property.is_required = property_required
                if ConfigSetting().JsonPropertyMaxDepth is not None and ConfigSetting().JsonPropertyMaxDepth == 1:
                    array_with_elements.leaf_property.is_required = True
            tree = add_tracked_parameter_name(array_with_elements, property_name, is_readonly)
            return InternalNode(inner_property=inner_array_property, leaf_properties=[tree])
        else:
            if isinstance(property_payload_example_value, list) or isinstance(property_payload_example_value, dict):
                if isinstance(property_payload_example_value, dict):
                    property_payload_example_value = property_payload_example_value.values()
                array_with_elements = []
                for item in property_payload_example_value:
                    example_property_payload = GenerateGrammarElements.format_jtoken_property(array_type,
                                                                                              item)
                    item_value = SchemaUtilities.format_example_value(example_property_payload)
                    elements = process_property(swagger_doc,
                                                "",
                                                array_item,
                                                item_value,
                                                generate_fuzzable_payload,
                                                track_parameters,
                                                parents,
                                                schema_cache,
                                                cont)
                    if isinstance(elements, LeafNode):
                        elements.leaf_property.is_required = property_required
                        tree = add_tracked_parameter_name(elements, property_name, is_readonly)
                        array_with_elements.append(tree)
                return InternalNode(inner_property=inner_array_property, leaf_properties=array_with_elements)
            else:
                raise ValueError(f"example value: {property_payload_example_value} not match the array property")
    else:
        raise ValueError(f"Found unsupported type in body parameters: {property_type}")


# generateGrammarElementForSchema
def generate_grammar_element_for_schema(swagger_doc: SwaggerDoc,
                                        schema,
                                        example_value: Optional,
                                        generate_fuzzable_payloads_for_examples: bool,
                                        track_parameters: bool,
                                        is_required: bool,
                                        parents: list,
                                        schema_cache: SchemaCache,
                                        cont: Optional[Tree]
                                        ) -> Union[LeafNode, InternalNode]:
    print("Generate Grammar Element For Schema...")
    is_readonly = SchemaUtilities.get_property_read_only(schema)

    def get_actual_schema(s):
        if isinstance(s, Schema):
            return s
        elif isinstance(s, Parameter):
            child_schema = SchemaUtilities.get_property(s, "schema")
            if child_schema is not None:
                return get_actual_schema(child_schema)
            else:
                return s
        elif isinstance(s, Response):
            child_schema = SchemaUtilities.get_property(s, "schema")
            if child_schema is not None:
                return get_actual_schema(child_schema)
            else:
                child_schema = SchemaUtilities.get_property(s, "$ref")
                if child_schema is not None:
                    return get_actual_schema(child_schema)
                else:
                    return s

    def generate_grammar_element(final_schema: Schema, example_value_info: Optional, parents: list):
        all_of_parameter_schemas = []
        properties_of_parameter_schema = []
        reference_of_parameter_schema = []
        additional_properties_of_parameter_schema = []
        if (final_schema.is_set("allOf") and ((ConfigSetting().JsonPropertyMaxDepth is not None
                                               and len(parents) < ConfigSetting().JsonPropertyMaxDepth)
                                              or ConfigSetting().JsonPropertyMaxDepth is None)):
            all_of_param = getattr(final_schema, final_schema.get_private_name("allOf"))
            if len(all_of_param) > 0:
                for ao in all_of_param:
                    element = generate_grammar_element_for_schema(swagger_doc,
                                                                  ao,
                                                                  example_value_info,
                                                                  generate_fuzzable_payloads_for_examples,
                                                                  track_parameters,
                                                                  SchemaUtilities.get_property(final_schema,
                                                                                               "required"),
                                                                  parents,
                                                                  schema_cache,
                                                                  cont)
                    if isinstance(element, InternalNode):
                        all_of_parameter_schemas.extend(element.leaf_properties)

        if (final_schema.is_set("additionalProperties") and ((ConfigSetting().JsonPropertyMaxDepth is not None
                                                              and len(parents) < ConfigSetting().JsonPropertyMaxDepth)
                                                             or ConfigSetting().JsonPropertyMaxDepth is None)):
            additional_schema = SchemaUtilities.get_property(final_schema, "additionalProperties")
            if additional_schema is not None:
                additional_type = SchemaUtilities.get_property(additional_schema, 'type')
                if additional_type == "":
                    element = generate_grammar_element_for_schema(swagger_doc,
                                                                  additional_schema,
                                                                  example_value_info,
                                                                  generate_fuzzable_payloads_for_examples,
                                                                  track_parameters,
                                                                  SchemaUtilities.get_property(final_schema,
                                                                                               "required"),
                                                                  parents,
                                                                  schema_cache,
                                                                  cont)
                else:
                    element = process_property(swagger_doc=swagger_doc,
                                               property_name="",
                                               property_schema=additional_schema,
                                               property_payload_example_value=example_value_info,
                                               generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                               track_parameters=track_parameters,
                                               parents=parents,
                                               schema_cache=schema_cache,
                                               cont=id)
                additional_properties_of_parameter_schema.append(element)

        if final_schema.is_set("$ref"):
            reference = SchemaUtilities.get_property(final_schema, "$ref")
            ref = get_definition_ref(reference)
            print(f"{reference} start")
            if ref.ref_type == RefResolution.LocalDefinitionRef:
                ret_value = get_definition_reference(ref_location=ref.file_name, spec=swagger_doc.definitions)
                for key, value in ret_value.items():
                    properties_schema = SchemaUtilities.get_property(value, "properties")
                    additional_schema = SchemaUtilities.get_property(value, "additionalProperties")
                    if len(properties_schema) > 0 or additional_schema is not None:
                        if len(properties_schema) > 0:
                            schema_cache.add_definition_cache(ref_definition=reference, value=key)
                            element = (
                                generate_grammar_element_for_schema(swagger_doc=swagger_doc,
                                                                    schema=value,
                                                                    example_value=example_value_info,
                                                                    generate_fuzzable_payloads_for_examples=generate_fuzzable_payloads_for_examples,
                                                                    track_parameters=track_parameters,
                                                                    is_required=SchemaUtilities.get_property(final_schema,
                                                                                                 "required"),
                                                                    parents=[reference] + parents,
                                                                    schema_cache=schema_cache,
                                                                    cont=None))
                            reference_of_parameter_schema.append(element)
                            schema_cache.remove_definition_cache(ref_definition=reference)
                        if additional_schema is not None:
                            schema_cache.add_definition_cache(ref_definition=reference, value=key)
                            if additional_schema.is_set("$ref") or additional_schema.is_set("schema"):
                                element = (
                                    generate_grammar_element_for_schema(swagger_doc=swagger_doc,
                                                                        schema=additional_schema,
                                                                        example_value=example_value_info,
                                                                        generate_fuzzable_payloads_for_examples=
                                                                        generate_fuzzable_payloads_for_examples,
                                                                        track_parameters=track_parameters,
                                                                        is_required=
                                                                        SchemaUtilities.get_property(final_schema,
                                                                                                     "required"),
                                                                        parents=[reference] + parents,
                                                                        schema_cache=schema_cache,
                                                                        cont=None))
                            else:
                                element = process_property(swagger_doc=swagger_doc,
                                                           property_name=SchemaUtilities.get_property(additional_schema,
                                                                                                      "name"),
                                                           property_schema=additional_schema,
                                                           property_payload_example_value=example_value_info,
                                                           generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                           track_parameters=track_parameters,
                                                           parents=parents,
                                                           schema_cache=schema_cache,
                                                           cont=id)
                            reference_of_parameter_schema.append(element)
                            schema_cache.remove_definition_cache(ref_definition=reference)

                    else:
                        element = process_property(swagger_doc=swagger_doc,
                                                   property_name="",
                                                   property_schema=value,
                                                   property_payload_example_value=example_value_info,
                                                   generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                   track_parameters=track_parameters,
                                                   parents=parents,
                                                   schema_cache=schema_cache,
                                                   cont=id)
                        reference_of_parameter_schema.append(element)
            print(f"{reference} end")

        if final_schema.is_set("properties"):
            properties_schema = SchemaUtilities.get_property(final_schema, "properties")
            if len(properties_schema) > 0:
                required_field = None
                if final_schema.is_set("required"):
                    required_field = getattr(final_schema, final_schema.get_private_name("required"))

                for key, value in properties_schema.items():
                    prop_type = SchemaUtilities.get_property(value, "type")
                    required = SchemaUtilities.get_property(value, "required")
                    if isinstance(required_field, list):
                        required = True if key in required_field else False
                        if not value.is_set("required"):
                            value.update_field("required", required)
                    # schema includes field required, update the information into the sub-schema.
                    final_example = None
                    if (example_value_info is not None and isinstance(example_value_info, dict)
                            and len(example_value_info) > 0):
                        if key in example_value_info.keys():
                            property_payload_example_value = example_value_info[key]
                            final_example = SchemaUtilities.get_correct_example_value(property_payload_example_value,
                                                                                      prop_type)
                        else:
                            continue
                    if generate_fuzzable_payloads_for_examples and final_example is None:
                        continue
                    if not generate_fuzzable_payloads_for_examples:
                        spec_example_value = SchemaUtilities.try_get_schema_example_value(value)
                        if spec_example_value is not None:
                            final_example = spec_example_value
                    print(f"properties:{key} start")
                    sub_properties = SchemaUtilities.get_property(value, "properties")
                    if value.is_set("$ref") or value.is_set("schema") or len(sub_properties) > 0:
                        internal_property = InnerProperty(name=key,
                                                          payload=None,
                                                          property_type=NestedType.Property,
                                                          is_required=required,
                                                          is_readonly=False)
                        if (ConfigSetting().JsonPropertyMaxDepth is not None
                                and len(parents) >= ConfigSetting().JsonPropertyMaxDepth):
                            object_payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                                             default_value="{ }",
                                                             example_value=example_value,
                                                             parameter_name=SchemaUtilities.get_property(schema,
                                                                                                         "name"),
                                                             dynamic_object=None)
                            node = LeafNode(leaf_property=LeafProperty(name="",
                                                                       payload=object_payload,
                                                                       is_required=required,
                                                                       is_readonly=is_readonly))
                            element = InternalNode(inner_property=internal_property, leaf_properties=[node])
                            properties_of_parameter_schema.append(element)
                        else:
                            node = generate_grammar_element_for_schema(swagger_doc=swagger_doc,
                                                                       schema=value,
                                                                       example_value=final_example,
                                                                       generate_fuzzable_payloads_for_examples=
                                                                       generate_fuzzable_payloads_for_examples,
                                                                       track_parameters=track_parameters,
                                                                       is_required=required,
                                                                       parents=parents,
                                                                       schema_cache=schema_cache,
                                                                       cont=None)
                            if isinstance(node, InternalNode):
                                if value.is_set("$ref"):
                                    reference_name = SchemaUtilities.get_property(value, "$ref")
                                    ref_def = get_definition_ref(reference_name)
                                    if ref_def.ref_type == RefResolution.LocalDefinitionRef:
                                        ref_def_value = get_definition_reference(ref_location=ref_def.file_name,
                                                                                 spec=swagger_doc.definitions)
                                        for def_values in ref_def_value.values():
                                            properties_schema = SchemaUtilities.get_property(def_values, "properties")
                                            if len(properties_schema) > 0:
                                                element = InternalNode(inner_property=internal_property,
                                                                       leaf_properties=[node])
                                            else:
                                                element = InternalNode(inner_property=internal_property,
                                                                       leaf_properties=node.leaf_properties)
                                            properties_of_parameter_schema.append(element)
                            elif isinstance(node, LeafNode):
                                element = InternalNode(inner_property=internal_property, leaf_properties=[node])
                                properties_of_parameter_schema.append(element)
                    else:
                        element = process_property(swagger_doc=swagger_doc,
                                                   property_name=key,
                                                   property_schema=value,
                                                   property_payload_example_value=final_example,
                                                   generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                   track_parameters=track_parameters,
                                                   parents=parents,
                                                   schema_cache=schema_cache,
                                                   cont=id)

                        properties_of_parameter_schema.append(element)
                    print(f"properties:{key} end")

        # fix issue: test_schema, large_json_body.json for allof
        grammar_element = None
        final_parameter_schema = []
        if len(properties_of_parameter_schema) > 0:
            final_parameter_schema = final_parameter_schema + properties_of_parameter_schema
        if len(reference_of_parameter_schema) > 0:
            if len(reference_of_parameter_schema) == 1:
                grammar_element = reference_of_parameter_schema[0]
                if isinstance(grammar_element, InternalNode):
                    grammar_element.inner_property.is_required = is_required
            else:
                final_parameter_schema = final_parameter_schema + reference_of_parameter_schema
        if len(all_of_parameter_schemas) > 0:
            final_parameter_schema = final_parameter_schema + all_of_parameter_schemas

        if grammar_element is None:
            grammar_element = InternalNode(InnerProperty(name="", payload=None,
                                                         property_type=NestedType.Object,
                                                         is_required=is_required, is_readonly=False),
                                           final_parameter_schema)

        schema_cache.add(final_schema, parents, grammar_element, example_value_info)

        if final_schema in parents:
            schema_cache.add_cycle([final_schema] + parents)

        return grammar_element

    cached_property = schema_cache.try_get(schema)

    # If a property is recursive, stop processing and treat the child property as an object.
    # Dependencies will use the parent, and fuzzing nested properties may be implemented later as an optimization.
    # fix issue in test_schema, large_json_body.json #/definitions/Customer
    found_cycle = schema in parents
    if not found_cycle and schema.is_set("$ref"):
        reference = SchemaUtilities.get_property(schema, "$ref")
        schema_definition = schema_cache.try_get_definition_cache(ref_definition=reference)
        if schema_definition is not None:
            found_cycle = True

    parameter_name = SchemaUtilities.get_property(schema, "name")
    if found_cycle and example_value is not None:
        raise UnsupportedRecursiveExample(f"{example_value}")
    if found_cycle:
        payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                  default_value="{ }",
                                  example_value=example_value,
                                  parameter_name=parameter_name,
                                  dynamic_object=None)
        return LeafNode(leaf_property=LeafProperty(name="",
                                                   payload=payload,
                                                   is_required=is_required,
                                                   is_readonly=is_readonly))
    if (ConfigSetting().JsonPropertyMaxDepth is not None
            and len(parents) > ConfigSetting().JsonPropertyMaxDepth):
        return generate_grammar_element(schema, example_value, parents)

    if example_value is None and cached_property is not None:
        return cached_property.tree
    else:
        if isinstance(schema, Schema):
            return generate_grammar_element(schema, example_value, parents)
        elif isinstance(schema, Parameter) or isinstance(schema, Response):
            child = get_actual_schema(schema)
            p_properties = None
            if not generate_fuzzable_payloads_for_examples and example_value is None:
                example_value = SchemaUtilities.try_get_schema_example_value(child)
            # body local definition
            if isinstance(child, Schema):
                p_properties = SchemaUtilities.get_property(child, "properties")
                if not child.is_set("required"):
                    child_required = SchemaUtilities.get_property(schema, "required")
                    child.update_field("required", child_required)
            if child.is_set("type"):
                p_type = SchemaUtilities.get_property(child, "type")
                p_parameter_name = SchemaUtilities.get_property(schema, "name")
                if p_properties is not None and len(p_properties) > 0:
                    return generate_grammar_element_for_schema(swagger_doc=swagger_doc,
                                                               schema=child,
                                                               example_value=example_value,
                                                               generate_fuzzable_payloads_for_examples=
                                                               generate_fuzzable_payloads_for_examples,
                                                               track_parameters=track_parameters,
                                                               is_required=is_required,
                                                               parents=parents,
                                                               schema_cache=schema_cache,
                                                               cont=None)
                if p_type != "array":
                    leaf_node = process_property(swagger_doc=swagger_doc,
                                                 property_name=p_parameter_name,
                                                 property_schema=child,
                                                 property_payload_example_value=example_value,
                                                 generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                 track_parameters=track_parameters,
                                                 parents=parents,
                                                 schema_cache=schema_cache,
                                                 cont=id)
                    leaf_node.leaf_property.name = ""
                    return leaf_node
                else:
                    if not child.is_set("items"):
                        raise Exception("Invalid array schema: found array property without a declared element")
                    return process_property(swagger_doc=swagger_doc,
                                            property_name="",
                                            property_schema=child,
                                            property_payload_example_value=example_value,
                                            generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                            track_parameters=track_parameters,
                                            parents=parents,
                                            schema_cache=schema_cache,
                                            cont=id)

            else:
                if not generate_fuzzable_payloads_for_examples and example_value is None:
                    example_value = SchemaUtilities.try_get_schema_example_value(schema)
                return generate_grammar_element(child, example_value, parents)

        elif isinstance(schema, Header):
            if schema.is_set("type"):
                p_type = getattr(schema, schema.get_private_name("type"))

                if p_type != "array":
                    leaf_node = process_property(swagger_doc=swagger_doc,
                                                 property_name="",
                                                 property_schema=schema,
                                                 property_payload_example_value=example_value,
                                                 generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                 track_parameters=track_parameters,
                                                 parents=parents,
                                                 schema_cache=schema_cache,
                                                 cont=id)
                    leaf_node.leaf_property.name = ""
                    return leaf_node
                else:
                    if not schema.is_set("items"):
                        raise Exception("Invalid array schema: found array property without a declared element")
                    return process_property(swagger_doc=swagger_doc,
                                            property_name="",
                                            property_schema=schema,
                                            property_payload_example_value=example_value,
                                            generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                            track_parameters=track_parameters,
                                            parents=parents,
                                            schema_cache=schema_cache,
                                            cont=id)

            else:
                child = getattr(schema, schema.get_private_name("schema"))
                if child is not None:
                    schema.update_field("type", 'object')
                return process_property(swagger_doc=swagger_doc,
                                        property_name="",
                                        property_schema=schema,
                                        property_payload_example_value=example_value,
                                        generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                        track_parameters=track_parameters,
                                        parents=parents,
                                        schema_cache=schema_cache,
                                        cont=id)
