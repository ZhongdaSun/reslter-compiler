# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
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
    Fuzzable,
    Constant,
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
    Response)

from restler.utils import restler_logger as logger


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
    def get_correct_example_value(example_object, param_type):
        if param_type is None or param_type == "" or example_object is None:
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
            return f"\"{example_object}\""
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
                def str_to_bool(s):
                    return s.lower() in ['true', '1', 'yes', 'y', 't']
                if isinstance(example_object, bool):
                    return example_object
                elif isinstance(example_object, str):
                    return f"\"{example_object}\""
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
            return JsonSerialization.serialize(example_object)

    # Get an example value as a string, either directly from the 'example' attribute or
    # from the extension 'Examples' property.
    @staticmethod
    def try_get_schema_example_value(schema: Schema):
        if schema.is_set("example"):
            value = getattr(schema, schema.get_private_name("example"))
            return SchemaUtilities.format_example_value(value)
        elif schema.is_set("examples"):
            extension_data_example = getattr(schema, schema.get_private_name("examples"))

            if extension_data_example:
                examples = extension_data_example if isinstance(extension_data_example, dict) else {}
                spec_example_values = [SchemaUtilities.format_example_value(example_value) for example_value in
                                       examples.values()]
                return spec_example_values[0]
        return None

    #  Get the example from the schema.
    # 'None' will be returned if the example for an
    #  object or array cannot be successfully parsed.
    # tryGetSchemaExampleAsString
    @staticmethod
    def try_get_schema_example_as_string(schema: Schema) -> Optional[str]:
        return SchemaUtilities.try_get_schema_example_value(schema)

    """
    # tryParseJToken
    @staticmethod
    def try_parse_jtoken(example_value: str) -> Optional[Any]:
        try:
            # return JToken.Parse(example_value)
            return None
        except Exception as ex:
            return None
    """

    # tryGetSchemaExampleAsJToken
    @staticmethod
    def try_get_schema_example_as_jtoken(schema: Schema) -> Optional[Any]:
        value_as_string = SchemaUtilities.try_get_schema_example_value(schema)
        if value_as_string:
            return value_as_string  # todo SchemaUtilities.try_parse_jtoken(value_as_string)
        else:
            return None

    @staticmethod
    def get_grammar_primitive_type_with_default_value(object_type: str,
                                                      json_format: str,
                                                      example_value: Optional[str],
                                                      property_name: Optional[str]) \
            -> Tuple[PrimitiveType, str, str, Optional[str]]:
        track_parameters = ConfigSetting().TrackFuzzedParameterNames

        logger.write_to_main(f"track_parameters={track_parameters}, property_name={property_name}",
                             ConfigSetting().LogConfig.swagger_visitor)
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
        logger.write_to_main(f"primitive_type={primitive_type}, default_value={default_value},"
                             f"example_value={example_value}, property_name={property_name}",
                             ConfigSetting().LogConfig.swagger_visitor)
        fuzzable_value = FuzzablePayload(
            primitive_type=primitive_type,
            default_value=default_value,
            example_value=example_value,
            parameter_name=property_name,
            dynamic_object=None)
        logger.write_to_main(f"return value = {fuzzable_value}", ConfigSetting().LogConfig.swagger_visitor)
        return fuzzable_value

    @staticmethod
    def get_extension_data_boolean_property_value(extension_data: dict,
                                                  extension_data_key_name: str) -> Optional[bool]:
        logger.write_to_main(f"extension_data={extension_data}, extension_data_key_name={extension_data_key_name}",
                             ConfigSetting().LogConfig.swagger_visitor)
        if not extension_data:
            return None
        else:
            if extension_data_key_name in extension_data:
                value = extension_data[extension_data_key_name]
                logger.write_to_main(f"value={value}", ConfigSetting().LogConfig.swagger_visitor)
                if isinstance(value, bool):
                    return value
                else:
                    try:
                        bool_value = bool(value)
                        return bool_value
                    except ValueError:
                        print(
                            f"WARNING: property {extension_data_key_name} has invalid value for field {value}, "
                            f"expected boolean")
                        return None
            else:
                return None

    @staticmethod
    def get_property_bool(schema: Union[Schema, Parameter, Response], name: str) -> bool:
        if name in ["readonly", "required", "explode", "readOnly"]:
            return bool(getattr(schema, schema.get_private_name(name))) if schema.is_set(name) else False
        else:
            raise Exception(f"property name: {name} is wrong!")

    @staticmethod
    def get_property_read_only(schema: Union[Schema, Parameter, Response]) -> bool:
        return (SchemaUtilities.get_property_bool(schema, "readonly") or
                SchemaUtilities.get_property_bool(schema, "readOnly"))

    @staticmethod
    def get_property_string(schema: Union[Schema, Parameter, Response], name: str) -> str:
        if name in ["type", "name", "format", "in", "style"]:
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

    @staticmethod
    def get_property_schema(schema: Union[Schema, Parameter, Response], name: str) -> Optional[Schema]:
        if name in ["$ref", "schema", "items"]:
            if schema.is_set(name):
                return getattr(schema, schema.get_private_name(name))
            else:
                return None
        else:
            raise Exception(f"property name: {name} is wrong!")

    @staticmethod
    def get_examples_from_parameter(p):
        def get_schema_example():
            if p is None:
                return None
            else:
                return SchemaUtilities.try_get_schema_example_as_jtoken(p)

        def get_parameter_example():

            example_value = None
            if p.is_set("examples"):
                example_value = SchemaUtilities.get_property_dict(p, "examples")
            elif p.is_set("example"):
                example_value = SchemaUtilities.get_property_dict(p, "example")
            return example_value

        parameter_example = get_parameter_example()
        if parameter_example:
            return parameter_example
        else:
            return get_schema_example()

    @staticmethod
    def get_property_dict(schema: Union[Schema, Parameter, Response], name: str) -> Optional[dict]:
        if name in ["properties", "examples", "example"]:
            if schema.is_set(name):
                return getattr(schema, schema.get_private_name(name))
            else:
                return None
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
    cache = defaultdict(CachedGrammarTree)  # Python 中的字典不需要指定线程安全性，但可以使用 threading 模块实现

    # 用于跟踪循环引用的集合
    cycles = set()

    def __init__(self):
        self.cache = {}
        self.cycles = set()

    def add_cycle(self, schema_list):
        logger.write_to_main(f"schema_list={schema_list}", ConfigSetting().LogConfig.swagger_visitor)
        root = schema_list[0]
        members = [x for x in schema_list[1:] if x != root]
        members = [root] + members
        parents = schema_list[len(members) + 1:]
        cycle = Cycle(root, parents, members)
        self.cycles.add(cycle)

    def try_get(self, schema):
        return self.cache.get(schema, None)

    def add(self, schema, parents, grammar_element, is_example):
        logger.write_to_main(f"schema={schema}, grammar_element={grammar_element.__dict__()}",
                             ConfigSetting().LogConfig.swagger_visitor)
        cycles_with_schema = [cycle for cycle in self.cycles if schema in cycle.members]
        cycle_root = next((cycle for cycle in cycles_with_schema if cycle.root == schema and cycle.parents == parents),
                          None)

        should_cache = not is_example and (not cycles_with_schema or cycle_root is not None)

        if should_cache:
            self.cache[schema] = CachedGrammarTree(grammar_element)
        # 如果是循环的根，移除循环跟踪
        if cycle_root is not None:
            self.cycles.remove(cycle_root)


class GenerateGrammarElements:
    @staticmethod
    def format_jtoken_property(primitive_type, raw_value):
        if primitive_type in ['array']:
            if raw_value is None:
                return None
            try:
                if len(raw_value) > 1 and (raw_value[0] == "'" or raw_value[0] == '"'):
                    if raw_value[0] == '"' and raw_value[-1] == '"':
                        return raw_value[1:-1]
                    else:
                        print(
                            f"WARNING: example file contains malformed value in property {primitive_type}. "
                            f"The compiler does not currently support this. Please modify the grammar manually "
                            f"to send the desired payload.")
                        return raw_value
            except:
                return raw_value
        elif primitive_type in ["number", "int", "boolean", "integer", "bool", "object"]:
            if isinstance(raw_value, str):
                def is_in_correct_format(value):
                    # Check if the string starts and ends with escaped double quotes
                    return value.startswith('\"') and value.endswith('\"')

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

    @staticmethod
    def extract_property_from_object(property_name, object_type, example_obj, parents=None):
        logger.write_to_main(f"property_name={property_name}, object_type={object_type}, "
                             f"example_obj={example_obj}, parents={parents}", ConfigSetting().LogConfig.swagger_visitor)
        if not property_name and object_type != "array":
            message = f"non-array should always have a property name. Property type: {object_type}"
            parent_property_names = ".".join([p.Name for p in parents]) if parents else ""
            property_info = f"Property name: {property_name}, parent properties: {parent_property_names}"
            raise Exception(f"{message} {property_info}")

        if example_obj:
            if object_type == "array":
                pv = example_obj
                include_property = True
            else:
                example_value = example_obj.get(property_name)
                if example_value is None:
                    pv = None
                    include_property = False
                else:
                    pv = example_value
                    include_property = True
        else:
            pv = None
            include_property = True

        return pv, include_property

    @staticmethod
    def extract_property_from_array(example_obj):
        return GenerateGrammarElements.extract_property_from_object("", "array", example_obj)


# getFuzzableValueForProperty
def get_fuzzable_value_for_property(property_name: str,
                                    property_schema: Schema,
                                    enumeration,
                                    example_value: Optional):
    property_type = SchemaUtilities.get_property_string(property_schema, "type").lower()
    property_format = SchemaUtilities.get_property_string(property_schema, "format")

    if property_type in ["string", "number", "int", "boolean", "integer", "bool"]:
        if enumeration is None:
            fuzzable_value = SchemaUtilities.get_fuzzable_value_for_object_type(property_type,
                                                                                property_format,
                                                                                example_value,
                                                                                property_name)
            logger.write_to_main(f"property_name={property_name}, property_type={property_type}, "
                                 f"property_format={property_format}, fuzzable_value={fuzzable_value.__dict__()}",
                                 ConfigSetting().LogConfig.swagger_visitor)
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
                                             default_value=
                                             PrimitiveTypeEnum(name=property_name,
                                                               primitive_type=
                                                               get_primitive_type_from_string(property_type),
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
        if isinstance(payload, Fuzzable):
            # 更新 parameter_name
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
        schema_example_value = SchemaUtilities.try_get_schema_example_as_jtoken(schema)
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
    def get_property_example_value(property_example):
        # Currently, only one example value is available in NJsonSchema
        # TODO: check if multiple example values are supported through
        # extension properties.
        return SchemaUtilities.try_get_schema_example_as_jtoken(property_example)

    # If an example value was not specified, also check for a locally defined example
    # in the Swagger specification.
    property_type = SchemaUtilities.get_property_string(property_schema, "type").lower()
    property_required = SchemaUtilities.get_property_bool(property_schema, "required")
    is_readonly = SchemaUtilities.get_property_read_only(property_schema)
    if len(ConfigSetting().ExampleConfigFiles) > 0 or ConfigSetting().ExampleConfigFilePath is not None:
        if (property_payload_example_value is None and
                property_schema.is_set("example") or property_schema.is_set("examples")):
            property_payload_example_value = SchemaUtilities.get_examples_from_parameter(property_schema)
    else:
        if property_schema.is_set("example") or property_schema.is_set("examples"):
            property_payload_example_value = SchemaUtilities.get_examples_from_parameter(property_schema)
            logger.write_to_main(f"property_payload_example_value={property_payload_example_value}",
                                 ConfigSetting().LogConfig.swagger_visitor)
            property_payload_example_value = SchemaUtilities.get_correct_example_value(property_payload_example_value,
                                                                                       property_type)
            logger.write_to_main(f"property_payload_example_value={property_payload_example_value}",
                                 ConfigSetting().LogConfig.swagger_visitor)

    if property_type in ["string", "number", "int", "boolean", "integer", "bool", "object"]:
        fuzzable_property_payload = get_fuzzable_value_for_property(property_name,
                                                                    property_schema,
                                                                    try_get_enumeration(property_schema),
                                                                    get_property_example_value(property_schema))
        if property_payload_example_value is not None:
            property_payload_example_value = GenerateGrammarElements.format_jtoken_property(property_type,
                                                                                            property_payload_example_value)

            example_property_payload = SchemaUtilities.format_example_value(property_payload_example_value)

            logger.write_to_main(f"property_type={property_type}, property_required={property_required} "
                                 f"property_payload_example_value={property_payload_example_value} "
                                 f"generate_fuzzable_payload={generate_fuzzable_payload} ",
                                 ConfigSetting().LogConfig.swagger_visitor)

            if generate_fuzzable_payload:
                fuzzable_property_payload.example_value = example_property_payload
            else:
                fuzzable_property_payload = Constant(primitive_type=get_primitive_type_from_string(property_type),
                                                     variable_name=example_property_payload)
        else:
            fuzzable_property_payload.example_value = property_payload_example_value
        logger.write_to_main(f"property_payload={fuzzable_property_payload}", ConfigSetting().LogConfig.swagger_visitor)
        return LeafNode(leaf_property=LeafProperty(name=property_name,
                                                   payload=fuzzable_property_payload,
                                                   is_required=property_required,
                                                   is_readonly=is_readonly))
    elif property_type is None:
        logger.write_to_main(f"property_type={property_type}, property_required={property_required} "
                             f"property_payload_example_value={property_payload_example_value} "
                             f"generate_fuzzable_payload={generate_fuzzable_payload} ",
                             ConfigSetting().LogConfig.swagger_visitor)
        obj_tree = generate_grammar_element_for_schema(swagger_doc,
                                                       property_schema,
                                                       property_payload_example_value,
                                                       generate_fuzzable_payload,
                                                       track_parameters,
                                                       property_required,
                                                       parents,
                                                       schema_cache,
                                                       cont)
        logger.write_to_main(f"obj_tree={obj_tree}", ConfigSetting().LogConfig.swagger_visitor)
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
        logger.write_to_main(f"property_type={property_type}, property_required={property_required} "
                             f"property_payload_example_value={property_payload_example_value} "
                             f"generate_fuzzable_payload={generate_fuzzable_payload} ",
                             ConfigSetting().LogConfig.swagger_visitor)
        if not property_schema.is_set("items"):
            raise Exception("Invalid array schema: found array property without a declared element")
        array_item = getattr(property_schema, property_schema.get_private_name("items"))
        array_type = SchemaUtilities.get_property_string(array_item, "type").lower()
        inner_array_property = InnerProperty(name=property_name,
                                             payload=None,
                                             property_type=NestedType.Array,
                                             is_required=property_required,
                                             is_readonly=is_readonly)

        if array_type == "":
            if property_payload_example_value is None:
                array_with_elements = generate_grammar_element_for_schema(swagger_doc,
                                                                          array_item,
                                                                          property_payload_example_value,
                                                                          generate_fuzzable_payload,
                                                                          track_parameters,
                                                                          property_required,
                                                                          [property_schema] + parents,
                                                                          schema_cache,
                                                                          cont)
                logger.write_to_main(f"array_with_elements={array_with_elements.__dict__()}",
                                     ConfigSetting().LogConfig.swagger_visitor)
                tree = add_tracked_parameter_name(array_with_elements, property_name, is_readonly)
                return InternalNode(inner_property=inner_array_property, leaf_properties=[tree])

            else:
                if isinstance(property_payload_example_value, list):
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
        else:
            if property_payload_example_value is None:
                if array_type in ["array", "object"]:
                    array_with_elements = generate_grammar_element_for_schema(swagger_doc,
                                                                              array_item,
                                                                              property_payload_example_value,
                                                                              generate_fuzzable_payload,
                                                                              track_parameters,
                                                                              property_required,
                                                                              [property_schema] + parents,
                                                                              schema_cache,
                                                                              cont)
                    if isinstance(array_with_elements, InternalNode):
                        tree = add_tracked_parameter_name(array_with_elements, property_name, is_readonly)
                        return InternalNode(inner_property=inner_array_property, leaf_properties=[tree])
                    else:
                        raise ValueError("An array should be an internal node.")
                else:
                    array_with_elements = process_property(swagger_doc,
                                                           "",
                                                           array_item,
                                                           property_payload_example_value,
                                                           generate_fuzzable_payload,
                                                           track_parameters,
                                                           [property_schema] + parents,
                                                           schema_cache,
                                                           cont)
                    if isinstance(array_with_elements, LeafNode):
                        array_with_elements.leaf_property.is_required = property_required
                        tree = add_tracked_parameter_name(array_with_elements, property_name, is_readonly)
                        return InternalNode(inner_property=inner_array_property, leaf_properties=[tree])
                    else:
                        raise ValueError("An array should be an internal node.")
            else:
                if isinstance(property_payload_example_value, list):
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
                    raise ValueError("An array should be an internal node.")
    elif property_type == "object":
        logger.write_to_main(f"property_type={property_type}, property_required={property_required} "
                             f"property_payload_example_value={property_payload_example_value} "
                             f"generate_fuzzable_payload={generate_fuzzable_payload} ",
                             ConfigSetting().LogConfig.swagger_visitor)
        obj_tree = generate_grammar_element_for_schema(swagger_doc,
                                                       property_schema,
                                                       property_payload_example_value,
                                                       generate_fuzzable_payload,
                                                       track_parameters,
                                                       property_required,
                                                       parents,
                                                       schema_cache,
                                                       cont)
        logger.write_to_main(f"obj_tree={obj_tree}", ConfigSetting().LogConfig.swagger_visitor)
        if isinstance(obj_tree, LeafNode):
            return cont(obj_tree)
        elif isinstance(obj_tree, InternalNode):
            inner_property = InnerProperty("",
                                           payload=None,
                                           property_type=NestedType.Object,
                                           is_required=property_required,
                                           is_readonly=is_readonly)
            return InternalNode(inner_property, obj_tree.leaf_properties)

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
    logger.write_to_main(f"Generate Grammar Element For Schema: {schema}", ConfigSetting().LogConfig.swagger_visitor)
    is_readonly = SchemaUtilities.get_property_read_only(schema)

    def get_actual_schema(s):
        if isinstance(s, Schema):
            logger.write_to_main(f"p={SchemaUtilities.get_property_string(s, "name")}, "
                                 f"s.$ref={SchemaUtilities.get_property_schema(s, "$ref")}, "
                                 f"s.type={SchemaUtilities.get_property_string(s, "type")}",
                                 ConfigSetting().LogConfig.swagger_visitor)
            return s
        elif isinstance(s, Parameter):
            child_schema = SchemaUtilities.get_property_schema(s, "schema")
            if child_schema is not None:
                logger.write_to_main(f"p={SchemaUtilities.get_property_string(s, "name")}, "
                                     f"s.$ref={SchemaUtilities.get_property_string(s, "in")}, "
                                     f"s.type={SchemaUtilities.get_property_string(s, "type")}"
                                     f"s.schema={SchemaUtilities.get_property_schema(s, "schema")}",
                                     ConfigSetting().LogConfig.swagger_visitor)
                return get_actual_schema(child_schema)
            else:
                return s
        elif isinstance(s, Response):
            child_schema = SchemaUtilities.get_property_schema(s, "schema")
            if child_schema is not None:
                return get_actual_schema(child_schema)
            else:
                child_schema = SchemaUtilities.get_property_schema(s, "$ref")
                if child_schema is not None:
                    return get_actual_schema(child_schema)
                else:
                    return s

    def generate_grammar_element(final_schema: Schema, example_value_info: Optional, parents: list):
        schema_example = None
        if example_value_info is not None:
            schema_example = example_value_info
        elif final_schema.is_set("example") or final_schema.is_set("examples"):
            schema_example = SchemaUtilities.get_examples_from_parameter(final_schema)
        all_of_parameter_schemas = []
        properties_of_parameter_schema = []
        reference_of_parameter_schema = []

        if final_schema.is_set("allOf"):
            all_of_param = getattr(final_schema, final_schema.get_private_name("allOf"))
            logger.write_to_main(f"all_of_param={all_of_param}", ConfigSetting().LogConfig.swagger_visitor)
            if len(all_of_param) > 0:
                for ao in all_of_param:
                    element = generate_grammar_element_for_schema(swagger_doc,
                                                                  ao,
                                                                  schema_example,
                                                                  generate_fuzzable_payloads_for_examples,
                                                                  track_parameters,
                                                                  True,
                                                                  parents,
                                                                  schema_cache,
                                                                  cont)
                    if isinstance(element, InternalNode):
                        all_of_parameter_schemas.extend(element.leaf_properties)

                    logger.write_to_main(f"ao={ao}, element ={element.__dict__()}",
                                         ConfigSetting().LogConfig.swagger_visitor)
                logger.write_to_main(f"len(all_of_parameter_schemas)={len(all_of_parameter_schemas)} "
                                     f" all_of_parameter_schemas={all_of_parameter_schemas}",
                                     ConfigSetting().LogConfig.swagger_visitor)

        if final_schema.is_set("$ref"):
            reference = SchemaUtilities.get_property_schema(final_schema, "$ref")
            ref = get_definition_ref(reference)
            required_field = SchemaUtilities.get_property_bool(final_schema, "required")
            logger.write_to_main(f"reference={reference} ", ConfigSetting().LogConfig.swagger_visitor)
            print(f"{reference} start")
            if ref.ref_type == RefResolution.LocalDefinitionRef:
                ret_value = get_definition_reference(ref_location=ref.file_name, spec=swagger_doc.definitions)
                for key, value in ret_value.items():
                    properties_schema = SchemaUtilities.get_property_dict(value, "properties")
                    if len(properties_schema) > 0:
                        logger.write_to_main(f"key={key}", ConfigSetting().LogConfig.swagger_visitor)
                        element = generate_grammar_element_for_schema(swagger_doc=swagger_doc,
                                                                      schema=value,
                                                                      example_value=schema_example,
                                                                      generate_fuzzable_payloads_for_examples=
                                                                      generate_fuzzable_payloads_for_examples,
                                                                      track_parameters=track_parameters,
                                                                      is_required=required_field,
                                                                      parents=[final_schema] + parents,
                                                                      schema_cache=schema_cache,
                                                                      cont=None)
                        if isinstance(element, InternalNode):
                            reference_of_parameter_schema.extend(element.leaf_properties)
                        elif isinstance(element, LeafNode):
                            reference_of_parameter_schema.append(element)
                    else:
                        element = process_property(swagger_doc=swagger_doc,
                                                   property_name="",
                                                   property_schema=value,
                                                   property_payload_example_value=schema_example,
                                                   generate_fuzzable_payload=generate_fuzzable_payloads_for_examples,
                                                   track_parameters=track_parameters,
                                                   parents=parents,
                                                   schema_cache=schema_cache,
                                                   cont=id)
                        reference_of_parameter_schema.append(element)
                    logger.write_to_main(f"key={key}, reference={reference} "
                                         f"element={element}", ConfigSetting().LogConfig.swagger_visitor)
                logger.write_to_main(f"len(reference_of_parameter_schema)={len(reference_of_parameter_schema)} "
                                     f" reference_of_parameter_schema={reference_of_parameter_schema}",
                                     ConfigSetting().LogConfig.swagger_visitor)
            print(f"{reference} end")

        if final_schema.is_set("properties"):
            properties_schema = SchemaUtilities.get_property_dict(final_schema, "properties")
            if len(properties_schema) > 0:
                logger.write_to_main(f"properties_schema={properties_schema} ",
                                     ConfigSetting().LogConfig.swagger_visitor)
                required_field = None
                if final_schema.is_set("required"):
                    required_field = getattr(final_schema, final_schema.get_private_name("required"))

                for key, value in properties_schema.items():
                    readonly = SchemaUtilities.get_property_read_only(value)
                    prop_type = SchemaUtilities.get_property_string(value, "type")
                    required = SchemaUtilities.get_property_bool(value, "required")
                    if isinstance(required_field, list):
                        required = True if key in required_field else False
                        if not value.is_set("required"):
                            value.update_field("required", required)
                    # schema includes field required, update the information into the sub-schema.
                    final_example = None
                    if schema_example is not None and isinstance(schema_example, dict):
                        if key in schema_example.keys():
                            property_payload_example_value = schema_example[key]
                            final_example = SchemaUtilities.get_correct_example_value(property_payload_example_value,
                                                                                      prop_type)
                            logger.write_to_main(f"property_payload_example_value={final_example}",
                                                 ConfigSetting().LogConfig.swagger_visitor)
                        else:
                            continue
                    logger.write_to_main(f"key={key}", ConfigSetting().LogConfig.swagger_visitor)
                    print(f"properties:{key} start")
                    sub_properties = SchemaUtilities.get_property_dict(value, "properties")
                    if value.is_set("$ref") or value.is_set("schema") or len(sub_properties) > 0:
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
                        internal_property = InnerProperty(name=key,
                                                          payload=None,
                                                          property_type=NestedType.Property,
                                                          is_required=required,
                                                          is_readonly=False)
                        if isinstance(node, InternalNode):
                            if value.is_set("$ref"):
                                reference_name = SchemaUtilities.get_property_schema(value, "$ref")
                                ref_def = get_definition_ref(reference_name)
                                if ref_def.ref_type == RefResolution.LocalDefinitionRef:
                                    ref_def_value = get_definition_reference(ref_location=ref_def.file_name,
                                                                         spec=swagger_doc.definitions)
                                    for def_values in ref_def_value.values():
                                        properties_schema = SchemaUtilities.get_property_dict(def_values, "properties")
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
                            logger.write_to_main(f"key={key}, properties_schema[key]={properties_schema[key]} "
                                                 f"element={node.__dict__()}",
                                                 ConfigSetting().LogConfig.swagger_visitor)
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
            logger.write_to_main(f"len(properties_of_parameter_schema)={len(properties_of_parameter_schema)} "
                                 f" properties_of_parameter_schema={properties_of_parameter_schema}",
                                 ConfigSetting().LogConfig.swagger_visitor)

        # fix issue: test_schema, large_json_body.json for allof
        grammar_element = None
        final_parameter_schema = []
        if len(properties_of_parameter_schema) > 0:
            final_parameter_schema = final_parameter_schema + properties_of_parameter_schema
        if len(reference_of_parameter_schema) > 0:
            final_parameter_schema = final_parameter_schema + reference_of_parameter_schema
        if len(all_of_parameter_schemas) > 0:
            final_parameter_schema = final_parameter_schema + all_of_parameter_schemas

        if len(final_parameter_schema) > 0:
            grammar_element = InternalNode(InnerProperty(name="", payload=None,
                                                         property_type=NestedType.Object,
                                                         is_required=is_required, is_readonly=False),
                                           final_parameter_schema)

        schema_cache.add(final_schema, parents, grammar_element, schema_example)

        if final_schema in parents:
            schema_cache.add_cycle([final_schema] + parents)

        return grammar_element

    cached_property = schema_cache.try_get(schema)

    # If a property is recursive, stop processing and treat the child property as an object.
    # Dependencies will use the parent, and fuzzing nested properties may be implemented later as an optimization.
    logger.write_to_main(f"parents={parents}", ConfigSetting().LogConfig.swagger_visitor)
    # fix issue in test_schema, large_json_body.json #/definitions/Customer
    found_cycle = schema in parents
    if not found_cycle and schema.is_set("$ref"):
        reference = SchemaUtilities.get_property_schema(schema, "$ref")
        ref = get_definition_ref(reference)
        logger.write_to_main(f"reference={reference} ", ConfigSetting().LogConfig.swagger_visitor)
        if ref.ref_type == RefResolution.LocalDefinitionRef:
            ret_value = get_definition_reference(ref_location=ref.file_name, spec=swagger_doc.definitions)
            for values in ret_value.values():
                found_cycle = values in parents
                if found_cycle:
                    break
    if found_cycle or (ConfigSetting().JsonPropertyMaxDepth is not None
                       and len(parents) > ConfigSetting().JsonPropertyMaxDepth):
        logger.write_to_main(f"found_cycle={found_cycle}, len(parents)={len(parents)}, "
                             f"json_property_max_depth={ConfigSetting().JsonPropertyMaxDepth}",
                             ConfigSetting().LogConfig.swagger_visitor)
        parameter_name = SchemaUtilities.get_property_string(schema, "name")
        if found_cycle and example_value is not None:
            raise UnsupportedRecursiveExample(f"{example_value}")
        if schema.is_set("type"):
            p_type = SchemaUtilities.get_property_string(schema, "type")
            if p_type == "array":
                payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                          default_value="{}",
                                          example_value=example_value,
                                          parameter_name=parameter_name,
                                          dynamic_object=None)
                if schema.is_set('items'):
                    p_item = getattr(schema, "items")
                    if p_item.is_set("type"):
                        p_item_type = SchemaUtilities.get_property_string(p_item, "type")
                        if p_item_type != "array":
                            payload = get_fuzzable_value_for_property(
                                SchemaUtilities.get_property_string(p_item, "name"),
                                p_item,
                                try_get_enumeration(p_item),
                                SchemaUtilities.try_get_schema_example_as_jtoken(p_item))
                leaf_properties = [LeafProperty("",
                                                payload,
                                                is_required=is_required,
                                                is_readonly=is_readonly)] if payload else []
                inner_property = InnerProperty(name="",
                                               payload=None,
                                               property_type=NestedType.Array,
                                               is_required=is_required,
                                               is_readonly=is_readonly)
                return InternalNode(inner_property=inner_property, leaf_properties=leaf_properties)
            else:
                payload = get_fuzzable_value_for_property(
                    property_name=parameter_name,
                    property_schema=schema,
                    enumeration=try_get_enumeration(schema),
                    example_value=SchemaUtilities.try_get_schema_example_as_jtoken(schema))
        else:
            payload = FuzzablePayload(primitive_type=PrimitiveType.Object,
                                      default_value="{}",
                                      example_value=example_value,
                                      parameter_name=parameter_name,
                                      dynamic_object=None)
        return LeafNode(leaf_property=LeafProperty(name="",
                                                   payload=payload,
                                                   is_required=is_required,
                                                   is_readonly=is_readonly))
    elif example_value is None and cached_property is not None:
        logger.write_to_main(f"cached_property.tree={type(cached_property.tree)}",
                             ConfigSetting().LogConfig.swagger_visitor)
        return cached_property.tree
    else:
        if isinstance(schema, Schema):
            logger.write_to_main(f"isinstance(schema, Schema)={isinstance(schema, Schema)}",
                                 ConfigSetting().LogConfig.swagger_visitor)
            return generate_grammar_element(schema, example_value, parents)
        elif isinstance(schema, Parameter) or isinstance(schema, Response):
            child = get_actual_schema(schema)
            logger.write_to_main(f"child={child}， type(child)={type(child)}", ConfigSetting().LogConfig.swagger_visitor)
            p_properties = None
            # body local definition
            if isinstance(child, Schema):
                p_properties = getattr(child, "properties")
                if not child.is_set("required"):
                    child_required = SchemaUtilities.get_property_bool(schema, "required")
                    child.update_field("required", child_required)
            if child.is_set("type"):
                p_type = SchemaUtilities.get_property_string(child, "type")
                p_parameter_name = SchemaUtilities.get_property_string(schema, "name")
                example_value = SchemaUtilities.get_correct_example_value(example_value, p_type)
                logger.write_to_main(f"example_value={example_value}", ConfigSetting().LogConfig.swagger_visitor)
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
                    if child.is_set("items") is None:
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
                return generate_grammar_element(child, example_value, parents)