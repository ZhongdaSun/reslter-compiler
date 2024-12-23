# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import enum
from enum import auto
import json
import re
import copy
from abc import abstractmethod
import hashlib
from typing import Callable, List, TypeVar, Union, Optional, TypeAlias

from compiler.xms_paths import XMsPath
from compiler.access_paths import AccessPath, EmptyAccessPath
from compiler.config import ConfigSetting
from dataclasses import dataclass
from restler.utils import restler_logger as logger

T = TypeVar('T')  # Leaf data type
U = TypeVar('U')  # Internal node data type
R = TypeVar('R')  # Result type
UTF8 = 'utf-8'


def str_to_hex_def(val_str):
    """ Creates a hex definition from a specified string

    @param val_str: The string to convert to a hex definition
    @type  val_str: Str

    @return: The hex definition of the string
    @rtype : Int

    """
    return hashlib.sha1(val_str.encode(UTF8)).hexdigest()


class Tree:

    def __init__(self):
        pass

    def __dict__(self):
        return NotImplemented

    @abstractmethod
    def example_dict(self):
        return NotImplemented


def cata_ctx(f_leaf: Callable[[R, T], R],
             f_node: Callable[[R, U, List[R]], R],
             f_ctx: Callable[[Optional[R], U], R],
             ctx: Optional[R],
             tree: Tree) -> R:
    def process_tree(current_tree: Tree, context: Optional[R]) -> R:
        if isinstance(current_tree, LeafNode):
            return f_leaf(context, current_tree.leaf_property)
        elif isinstance(current_tree, InternalNode):
            new_context = f_ctx(context, current_tree.inner_property)
            subtree_results = [process_tree(subtree, new_context) for subtree in current_tree.leaf_properties]
            return f_node(context, current_tree.inner_property, subtree_results)

    return process_tree(tree, ctx)


def cata(f_leaf: Callable[[R, T], R],
         f_node: Callable[[R, U, List[R]], R],
         tree: Tree) -> R:
    return cata_ctx(f_leaf, f_node, lambda ctx, node: ctx, None, tree)


def fold(f_leaf: Callable[[R, T], R],
         f_node: Callable[[R, U], R],
         acc: R,
         tree: Tree) -> R:
    if isinstance(tree, LeafNode):
        return f_leaf(acc, tree.leaf_property)
    elif isinstance(tree, InternalNode):
        local_acc = f_node(acc, tree.inner_property)
        for subtree in tree.leaf_properties:
            local_acc = fold(f_leaf, f_node, local_acc, subtree)
        return local_acc


def iter_ctx(f_leaf: Callable[[Optional[R], T], None],
             f_node: Callable[[Optional[R], U], None],
             f_ctx: Callable[[Optional[R], U], Optional[R]],
             ctx: Optional[R],
             tree: Tree) -> None:
    if isinstance(tree, LeafNode):
        f_leaf(ctx, tree.leaf_property)
    elif isinstance(tree, InternalNode):
        new_context = f_ctx(ctx, tree.inner_property)
        for subtree in tree.leaf_properties:
            iter_ctx(f_leaf, f_node, f_ctx, new_context, subtree)
            f_node(ctx, tree.inner_property)


def iter_tree(f_node: Callable[[Tree], None], tree: Tree) -> None:
    if isinstance(tree, LeafNode):
        f_node(tree)
    elif isinstance(tree, InternalNode):
        for subtree in tree.leaf_properties:
            iter_tree(f_node, subtree)
        f_node(tree)


class OperationMethod(enum.StrEnum):
    Get = auto()
    Put = auto()
    Post = auto()
    Delete = auto()
    Options = auto()
    Head = auto()
    Patch = auto()
    Trace = auto()
    NOT_SUPPORT = auto()


def get_operation_method_from_string(m):
    m_upper = m.upper()
    if m_upper == "GET":
        return OperationMethod.Get
    elif m_upper == "POST":
        return OperationMethod.Post
    elif m_upper == "PUT":
        return OperationMethod.Put
    elif m_upper == "DELETE":
        return OperationMethod.Delete
    elif m_upper == "PATCH":
        return OperationMethod.Patch
    elif m_upper == "OPTIONS":
        return OperationMethod.Options
    elif m_upper == "HEAD":
        return OperationMethod.Head
    elif m_upper == "TRACE":
        return OperationMethod.Trace
    else:
        return OperationMethod.NOT_SUPPORT


SupportedOperationMethods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']


class ParameterKind(enum.StrEnum):
    Path = auto()
    Query = auto()
    Header = auto()
    Body = auto()


# The primitive types supported by RESTler
class PrimitiveType(enum.StrEnum):
    String = auto()
    Array = auto()
    Object = auto()
    Number = auto()
    Int = auto()
    Uuid = auto()
    Bool = auto()
    DateTime = auto()
    Date = auto()
    Enum = auto()  # 需要进一步处理
    File = auto()
    NONE = auto()
    Unknown = auto()


def get_primitive_type_from_string(m):
    m_upper = m.lower()
    if m_upper == "string":
        return PrimitiveType.String
    elif m_upper == "array":
        return PrimitiveType.Array
    elif m_upper == "object":
        return PrimitiveType.Object
    elif m_upper == "number":
        return PrimitiveType.Number
    elif m_upper == "int" or m_upper == "integer":
        return PrimitiveType.Int
    elif m_upper == "uuid" or m_upper == "guid":
        return PrimitiveType.Uuid
    elif m_upper == "bool":
        return PrimitiveType.Bool
    elif m_upper == "datetime" or m_upper == "date-time":
        return PrimitiveType.DateTime
    else:
        return PrimitiveType.Date


class NestedType(enum.StrEnum):
    Object = auto()
    Array = auto()
    Property = auto()


# The enum type specifies the list of possible enum values
# and the default value, if specified.
# (tag, data type, possible values, default value if present)
# | Enum of string * PrimitiveType * string list * string option
class PrimitiveTypeEnum:
    name: str
    primitive_type: PrimitiveType
    value: list[str]
    default_value: str

    def __init__(self, name: str, primitive_type: PrimitiveType, value: list[str], default_value: Optional[str]):
        self.name = name
        self.primitive_type = primitive_type
        self.value = value
        self.default_value = default_value

    def __dict__(self):
        null_value = None
        return {
            "primitiveType": {
                "Enum": [
                    self.name,
                    self.primitive_type.name,
                    self.value,
                    null_value,
                ],
            },
            "defaultValue": self.default_value
        }

    def example_dict(self):
        return self.__dict__()

    def api_resource_dict(self):
        null_value = None
        return {
            "Enum": [
                self.name,
                self.primitive_type.name,
                self.value,
                null_value,
            ],
        }


# Define CustomPayloadType enum values here if needed
class CustomPayloadType(enum.StrEnum):
    String = auto(),
    UuidSuffix = auto(),
    Header = auto(),
    Query = auto()  # Used to inject query parameters that are not part of the specification.


@dataclass
class DynamicObject:
    # The primitive type of the parameter, as declared in the specification
    # The primitive type is assigned to be the type of the initially written value whenever possible.\
    def __init__(self, primitive_type: PrimitiveType, variable_name: str, is_writer: bool):
        self.primitive_type = primitive_type
        self.variable_name = variable_name  # The variable name of the dynamic object
        self.is_writer = is_writer  # 'True' if this is an assignment, otherwise a read of the dynamic object

    def __dict__(self) -> dict:
        return {"DynamicObject": {"primitiveType": self.primitive_type.name,
                                  "variableName": self.variable_name,
                                  "isWriter": self.is_writer
                                  }}

    def example_dict(self) -> dict:
        return self.__dict__()


# Example: (Int "1")
class Constant:
    primitive_type: PrimitiveType
    variable_name: str

    def __init__(self, primitive_type: PrimitiveType, variable_name: str):
        self.primitive_type = primitive_type
        self.variable_name = variable_name

    def data_value(self):
        return self.variable_name

    def __dict__(self):
        dict_value = dict()
        dict_value["Constant"] = [self.primitive_type.name, self.variable_name]
        return dict_value

    def example_dict(self):
        return self.__dict__()


@dataclass
# (data type, default value, example value, parameter name)
# Example: (Int "1", "2")
class FuzzablePayload:
    primitive_type: PrimitiveType
    default_value: Union[dict, str]
    example_value: Optional[str]
    parameter_name: Optional[str]
    dynamic_object: Optional[DynamicObject]

    def __init__(self, primitive_type: PrimitiveType,
                 default_value: Union[dict, str, PrimitiveTypeEnum],
                 example_value: Optional[str],
                 parameter_name: Optional[str],
                 dynamic_object: Optional[DynamicObject]):
        # The primitive type of the payload, as declared in the specification
        self.primitive_type = primitive_type
        # The default value of the payload
        self.default_value = default_value
        # The example value specified in the spec, if any
        self.example_value = example_value
        # The parameter name, if available.
        self.parameter_name = parameter_name
        # The associated dynamic object, whose value should be
        # assigned to the value generated from this payload.
        # For example, an input value from a request body property.
        self.dynamic_object = dynamic_object

    def __dict__(self):
        dict_value = dict()
        if self.primitive_type != PrimitiveType.Enum:
            dict_value["primitiveType"] = self.primitive_type.name
            dict_value["defaultValue"] = self.default_value
            if self.example_value is not None:
                if self.example_value == "None":
                    dict_value["exampleValue"] = {"Some": None}
                else:
                    dict_value["exampleValue"] = self.example_value

            if self.dynamic_object is not None:
                dynamic_dict = self.dynamic_object.__dict__()
                dict_value["dynamicObject"] = dynamic_dict["DynamicObject"]
            if ConfigSetting().TrackFuzzedParameterNames:
                dict_value["parameterName"] = self.parameter_name
            return {"Fuzzable": dict_value}
        else:
            if isinstance(self.default_value, PrimitiveTypeEnum):
                dict_value = self.default_value.__dict__()
                if self.example_value is not None:
                    dict_value["exampleValue"] = self.example_value
                return {"Fuzzable": dict_value}

    def path_dict(self):
        dict_value = dict()
        if self.dynamic_object is not None:
            return self.dynamic_object.__dict__()
        else:

            if isinstance(self.primitive_type, PrimitiveType):
                dict_value["primitiveType"] = self.primitive_type.name
            elif isinstance(self.primitive_type, PrimitiveTypeEnum):
                dict_value["primitiveType"] = self.primitive_type.__dict__()
            dict_value["defaultValue"] = self.default_value
            if self.example_value is not None:
                dict_value["exampleValue"] = self.example_value
            return {"Fuzzable": dict_value}

    def example_dict(self):
        dict_value = dict()
        if self.primitive_type != PrimitiveType.Enum:
            dict_value["primitiveType"] = self.primitive_type.name
            dict_value["defaultValue"] = self.default_value
            dict_value["exampleValue"] = self.example_value
            if self.primitive_type == PrimitiveType.Object:
                if self.example_value is None:
                    dict_value["exampleValue"] = {"Some": self.example_value}
            else:  # if self.example_value and self.example_value != "":
                dict_value["exampleValue"] = self.example_value
            if self.dynamic_object is not None:
                dynamic_dict = self.dynamic_object.example_dict()
                dict_value.update(dynamic_dict)
            return {"Fuzzable": dict_value}
        else:
            if isinstance(self.default_value, PrimitiveTypeEnum):
                dict_value = self.default_value.example_dict()
                return {"Fuzzable": dict_value}
            else:
                return {"Fuzzable": dict_value}


# The custom payload, as specified in the fuzzing dictionary

class CustomPayload:
    payload_type: CustomPayloadType
    payload_value: str
    dynamic_object: Optional[DynamicObject]

    def __init__(self,
                 payload_type: CustomPayloadType,
                 primitive_type: PrimitiveType,
                 payload_value: str,
                 is_object: bool,
                 dynamic_object: Optional[DynamicObject]):
        self.payload_type = payload_type  # The type of custom payload
        self.primitive_type = primitive_type  # The primitive type of the payload, as declared in the specification
        self.payload_value = payload_value  # The value of the payload
        self.is_object = is_object  # 'True' if the value is an object
        # This identifier may have an associated dynamic object, whose value should be
        # assigned to the value generated from this payload
        self.dynamic_object = dynamic_object

    def __dict__(self):
        dict_value = dict()
        dict_value["payloadType"] = self.payload_type.name
        dict_value["primitiveType"] = self.primitive_type.name
        dict_value["payloadValue"] = self.payload_value
        dict_value["isObject"] = self.is_object
        if self.dynamic_object is not None:
            dynamic_dict = self.dynamic_object.__dict__()
            dict_value["dynamicObject"] = dynamic_dict["DynamicObject"]
        return {"Custom": dict_value}

    def example_dict(self):
        dict_value = dict()
        dict_value["payloadType"] = self.payload_type.name
        dict_value["primitiveType"] = self.primitive_type.name
        dict_value["payloadValue"] = self.payload_value
        dict_value["isObject"] = self.is_object
        if self.dynamic_object is not None:
            dynamic_dict = self.dynamic_object.example_dict()
            dict_value["dynamicObject"] = dynamic_dict["DynamicObject"]
        return {"Custom": dict_value}


Fuzzable: TypeAlias = FuzzablePayload
Custom: TypeAlias = CustomPayload

# In some cases, a payload may need to be split into multiple payload parts
PayloadParts: TypeAlias = list[Union[Constant, Fuzzable, Custom, DynamicObject]]

# The payload for a property specified in as a request parameter
FuzzingPayload = Union[Constant, Fuzzable, Custom, DynamicObject, PayloadParts]


# The unique ID of a request.
class RequestId:
    def __init__(self,
                 endpoint: str,
                 method: OperationMethod,
                 xms_path: Union[XMsPath, None],
                 has_example: bool):
        self.endpoint = endpoint
        # If a request is declared with an x-ms-path, 'xMsPath' contains the original path
        # from the specification.  The 'endpoint' above contains a transformed path for
        # so that the OpenAPI specification can be compiled with standard 'paths'.
        # todo
        self.xMsPath = xms_path
        self.method = method

        self.has_example = has_example
        self.has_schema = False
        self.hex_hash = str_to_hex_def(get_operation_method_from_string(method) + self.endpoint)

    def __dict__(self):
        dict_value = dict()
        dict_value["endpoint"] = self.endpoint
        if self.xMsPath is not None:
            dict_value["xMsPath"] = self.xMsPath.__dict__()
        dict_value["method"] = self.method.name
        return dict_value

    def __eq__(self, other):
        if isinstance(other, RequestId):
            if self.endpoint == other.endpoint and self.method == other.method:
                return True
            else:
                return False
        else:
            return False


class AnnotationResourceReference:
    # A resource parameter must be obtained in context, via its full path.
    def __init__(self, resource_name: Optional[str], resource_path: AccessPath):
        # A resource parameter may be obtained by name only
        # The producer resource name and consumer parameter
        # These may be omitted in the case of an ordering constraint
        # specification between methods
        self.resource_name = resource_name
        # A resource parameter must be obtained in context, via its full path.
        self.resource_path = resource_path

    def get_param(self):
        if self.resource_path == EmptyAccessPath:
            return self.resource_name
        else:
            if self.resource_name is None or self.resource_name == "":
                return "/" + ("/".join(self.resource_path.path))
            else:
                return self.resource_name

    def __dict__(self):
        if self.resource_path is not EmptyAccessPath:
            return {"ResourcePath": {
                "path": self.resource_path.path}}
        else:
            return {"ResourceName": self.resource_name}


class ProducerConsumerAnnotation:
    def __init__(self,
                 producer_id: RequestId,
                 consumer_id: Optional[RequestId],
                 producer_parameter: AnnotationResourceReference,
                 consumer_parameter: Optional[AnnotationResourceReference],
                 except_consumer_id: [RequestId]):
        # The endpoint and method of the producer saved in RequestId
        self.producer_id = producer_id
        self.consumer_id = consumer_id

        # The producer resource name and consumer parameter
        # These may be omitted in the case of an ordering constraint
        # specification between methods
        self.producer_parameter = producer_parameter
        self.consumer_parameter = consumer_parameter
        self.except_consumer_id = except_consumer_id

    def __dict__(self):
        dict_value = {
            "producerId": self.producer_id.__dict__(),
            "producerParameter": self.producer_parameter.__dict__()}
        if self.consumer_parameter is not None:
            dict_value["consumerParameter"] = self.consumer_parameter.__dict__()
        return dict_value


# A property that does not have any nested properties
class LeafProperty:
    name: str
    payload: FuzzingPayload
    is_required: bool
    is_readonly: bool

    def __init__(self, name: str,
                 payload: FuzzingPayload,
                 is_required: bool,
                 is_readonly: bool):
        self.name = name
        self.payload = payload
        self.is_required = is_required
        self.is_readonly = is_readonly

    def __dict__(self):
        return {
            "name": self.name,
            "payload": self.payload.__dict__(),
            "isRequired": self.is_required,
            "isReadOnly": self.is_readonly
        }

    def example_dict(self):
        return {
            "name": self.name,
            "payload": self.payload.example_dict(),
            "isRequired": self.is_required,
            "isReadOnly": self.is_readonly
        }


class LeafNode(Tree):
    leaf_property: LeafProperty

    def __init__(self, leaf_property):
        super().__init__()
        self.leaf_property = leaf_property

    def __dict__(self):
        return {"LeafNode": self.leaf_property.__dict__()}

    def example_dict(self):
        return {"LeafNode": self.leaf_property.example_dict()}

    def __deepcopy__(self, memo):
        copied_instance = LeafNode(copy.deepcopy(self.leaf_property, memo))
        return copied_instance


# A property that has nested properties
# Such an inner property can have a fuzzing payload (e.g., an entire json object, specified
# directly or as a reference to the custom dictionary) or instead specify
# individual elements for fuzzing (concrete values will be specified later, e.g. at the leaf level)
class InnerProperty:
    def __init__(self, name: str, payload: Optional[FuzzingPayload],
                 property_type: NestedType, is_required: bool, is_readonly: bool):
        self.name = name
        self.payload = payload
        self.property_type = property_type
        self.is_required = is_required
        self.is_readonly = is_readonly

    def __dict__(self):
        result = {"name": self.name}
        if self.payload is not None:
            result["payload"] = self.payload.__dict__()
        result["propertyType"] = self.property_type.name
        result["isRequired"] = self.is_required
        result["isReadOnly"] = self.is_readonly

        return result


class InternalNode(Tree):
    inner_property: InnerProperty
    leaf_properties: list[Tree]

    def __init__(self, inner_property: InnerProperty, leaf_properties: list[Tree]):
        super().__init__()
        self.inner_property = inner_property
        self.leaf_properties = leaf_properties

    def __dict__(self):
        leaf_prop = []
        for item in self.leaf_properties:
            leaf_prop.append(item.__dict__())

        ret_dict = [self.inner_property.__dict__(), leaf_prop]
        return {"InternalNode": ret_dict}

    def example_dict(self):
        leaf_prop = []
        if self.inner_property.property_type == NestedType.Array:
            if len(self.leaf_properties) > 0:
                for item in self.leaf_properties:
                    if isinstance(item, LeafNode) and isinstance(item.leaf_property.payload, FuzzablePayload):
                        exv = item.leaf_property.payload.example_value
                        if exv is not None:
                            leaf_prop.append(item.example_dict())
                        # there is no example value, just skip.
                    else:
                        leaf_prop.append(item.example_dict())
                if len(leaf_prop) > 0:
                    return {"InternalNode": [self.inner_property.__dict__(), leaf_prop]}
                else:
                    return None
            else:
                return {"InternalNode": [self.inner_property.__dict__(), []]}

        else:
            for item in self.leaf_properties:
                if isinstance(item, LeafNode) and isinstance(item.leaf_property.payload, FuzzablePayload):
                    if item.leaf_property.payload.primitive_type == PrimitiveType.Object:
                        leaf_prop.append(item.example_dict())
                    elif item.leaf_property.payload.primitive_type == PrimitiveType.Enum:
                        leaf_prop.append(item.example_dict())
                    else:
                        if item.leaf_property.payload.example_value is not None:
                            leaf_prop.append(item.example_dict())
                else:
                    item_dict = item.example_dict()
                    if item_dict is not None:
                        leaf_prop.append(item_dict)

            return {"InternalNode": [self.inner_property.__dict__(), leaf_prop]}


# The source of parameters for this grammar element.
class ParameterPayloadSource(enum.Enum):
    # Parameters were defined in the Swagger definition schema
    Schema = 0
    # Parameters were defined in a payload example
    Examples = 1
    # Parameters were defined as a custom payload
    DictionaryCustomPayload = 2


# The parameter serialization style
class StyleKind(enum.StrEnum):
    Form = auto(),
    Simple = auto(),
    Undefined = auto()


# Information related to how to serialize the parameter
class ParameterSerialization:
    def __init__(self, style: StyleKind, explode: bool, has_setting=False):
        # Defines how multiple values are delimited
        self.style = style
        # Specifies whether arrays and objects should generate
        # separate parameters for each array item or object property
        self.explode = explode
        self.has_setting = has_setting

    def __dict__(self):
        return {
            "style": self.style.name,
            "explode": self.explode
        }


class ResponseInfo:
    # The response properties
    # # The object assigned to a parameter (which may include nested properties)
    body_response_schema: Union[LeafNode, InternalNode]
    header_response_schema: Union[LeafNode, InternalNode]
    link_annotations: []

    def __init__(self, body_response_schema: Union[LeafNode, InternalNode],
                 header_response_schema: Union[LeafNode, InternalNode],
                 link_annotations):
        self.body_response_schema = body_response_schema
        self.header_response_schema = header_response_schema
        self.link_annotations = link_annotations


class RequestParameter:
    def __init__(self, name: str, payload: Union[LeafNode, InternalNode],
                 serialization: Optional[ParameterSerialization]):
        self.name = name
        self.payload = payload
        self.serialization = serialization

    def __dict__(self):
        dict_value = dict()
        dict_value["name"] = self.name
        dict_value["payload"] = self.payload.__dict__()
        if self.serialization is not None and self.serialization.has_setting:
            dict_value["serialization"] = self.serialization.__dict__()
        logger.write_to_main("json_str={}".format(json.dumps(dict_value)), ConfigSetting().LogConfig.grammar)
        return dict_value

    def example_dict(self):
        dict_value = dict()
        dict_value["name"] = self.name
        payload_dict = self.payload.example_dict()

        dict_value["payload"] = payload_dict
        if self.serialization is not None and self.serialization.has_setting:
            dict_value["serialization"] = self.serialization.__dict__()

        logger.write_to_main("json_str={}".format(json.dumps(payload_dict)), ConfigSetting().LogConfig.grammar)
        if payload_dict is not None:
            return dict_value
        else:
            return None


class ParameterList:
    request_parameters: list[RequestParameter]

    def __init__(self, request_parameters: Optional[list[RequestParameter]]):
        self.request_parameters = request_parameters

    def __dict__(self):
        dict_list = []
        if self.request_parameters is not None:
            for item in self.request_parameters:
                if item is not None:
                    logger.write_to_main(f"item={type(item)}, item={json.dumps(item.__dict__())}",
                                         ConfigSetting().LogConfig.grammar)
                    item_dict = item.__dict__()
                    if item_dict is not None:
                        dict_list.append(item_dict)
            logger.write_to_main(f"dict_list={dict_list}, json_str={json.dumps(dict_list)}",
                                 ConfigSetting().LogConfig.grammar)
        return dict_list

    def example_dict(self):
        dict_list = []
        if self.request_parameters is not None:
            for item in self.request_parameters:
                if item is not None:
                    logger.write_to_main(f"item={type(item)}", ConfigSetting().LogConfig.grammar)
                    dict_list.append(item.example_dict())
            logger.write_to_main(f"dict_list={dict_list}, json_str={json.dumps(dict_list)}",
                                 ConfigSetting().LogConfig.grammar)
        return dict_list


# ParameterList: TypeAlias = list[RequestParameter]
Example: TypeAlias = FuzzingPayload
# The payload for request parameters
RequestParametersPayload = Union[ParameterList, Example]
RequestParameterType = (ParameterPayloadSource, RequestParametersPayload)
RequestParameterList = list[RequestParameterType]


class RequestParameters:

    def __init__(self, path: RequestParametersPayload, header: RequestParameterList, query: RequestParameterList,
                 body: RequestParameterList):
        self.path = path

        # header: (ParameterPayloadSource * RequestParametersPayload) list
        self.header = header

        # List of several possible parameter sets that may be used to invoke a request.
        # The payload source is not expected to be unique. For example, there may be several schemas
        # from different examples.
        # query: (ParameterPayloadSource * RequestParametersPayload) list
        self.query = query

        # List of several possible parameter sets that may be used to invoke a request. The payload source is not
        # expected to be unique. For example, there may be several schemas
        # from different examples. body: (ParameterPayloadSource * RequestParametersPayload) list
        self.body = body


# The type of token required to access the API
class TokenKind(enum.Enum):
    Static = 1
    Refreshable = 2


# The type of dynamic object variable
class DynamicObjectVariableKind:
    # Dynamic object assigned from a body response property
    BodyResponsePropertyKind = 1
    # Dynamic object assigned from a response header
    HeaderKind = 2
    # Dynamic object assigned from an input parameter or property value
    InputParameterKind = 3

    # A variable specifically created for an ordering constraint,
    # which is not included as part of the payload.  (TODO: maybe this is not needed?)
    OrderingConstraintKind = 4


class DynamicObjectWriterVariable:

    def __init__(self, request_id: RequestId,
                 access_path_parts: AccessPath,
                 primitive_type: PrimitiveType,
                 kind: DynamicObjectVariableKind):
        # The ID of the request
        self.request_id = request_id
        # The access path to the parameter associated with this dynamic object
        self.access_path_parts = access_path_parts
        # The type of the variable
        self.primitive_type = primitive_type
        # The kind of the variable (e.g. header or response property)
        self.kind = kind

    def __dict__(self):
        dict_value = dict()
        dict_value["requestId"] = self.request_id.__dict__()
        dict_value["accessPathParts"] = self.access_path_parts.__dict__()
        dict_value["primitiveType"] = self.primitive_type.name
        if self.kind == DynamicObjectVariableKind.HeaderKind:
            dict_value["kind"] = "Header"
        elif self.kind == DynamicObjectVariableKind.BodyResponsePropertyKind:
            dict_value["kind"] = "BodyResponseProperty"
        elif self.kind == DynamicObjectVariableKind.InputParameterKind:
            dict_value["kind"] = "InputParameter"
        else:
            dict_value["kind"] = "OrderingConstraint"
        return dict_value

    def __eq__(self, other):
        if isinstance(other, DynamicObjectWriterVariable):
            if (self.kind == other.kind and self.primitive_type == other.primitive_type
                    and self.request_id == other.request_id and self.access_path_parts == other.access_path_parts):
                return True
            else:
                return False
        else:
            return False


class OrderingConstraintVariable:
    def __init__(self, source_request_id: RequestId, target_request_id: RequestId):
        # The ID of the producer request
        self.source_request_id = source_request_id
        self.target_request_id = target_request_id


# Information needed to generate a response parser
class ResponseParser:
    writer_variables: list[DynamicObjectWriterVariable]
    header_writer_variables: list[DynamicObjectWriterVariable]

    def __init__(self, writer_variables: [], header_writer_variables: []):
        # The writer variables returned in the response
        # writerVariables : DynamicObjectWriterVariable list
        self.writer_variables = writer_variables
        # The writer variables returned in the response headers
        # headerWriterVariables : DynamicObjectWriterVariable list
        self.header_writer_variables = header_writer_variables

    def __dict__(self):
        writer_variables_list = []
        header_writer_variable_list = []
        for item in self.writer_variables:
            writer_variables_list.append(item.__dict__())
        for item in self.header_writer_variables:
            header_writer_variable_list.append(item.__dict__())
        dict_value = dict()
        dict_value["writerVariables"] = writer_variables_list
        dict_value["headerWriterVariables"] = header_writer_variable_list
        return dict_value


# Information needed for dependency management
class RequestDependencyData:
    response_parser: Optional[ResponseParser]
    input_writer_variables: list[DynamicObjectWriterVariable]
    ordering_constraint_writer_variables: list[OrderingConstraintVariable]
    ordering_constraint_reader_variables: list[OrderingConstraintVariable]

    # The generated response parser.  This is only present if there is at least
    # one consumer for a property of the response.
    def __init__(self,
                 response_parser: Optional[ResponseParser],
                 input_writer_variables: [DynamicObjectWriterVariable],
                 ordering_constraint_writer_variables: [],
                 ordering_constraint_reader_variables: []):
        # The writer variables that are written when the request is sent, and which
        # are not returned in the response
        self.response_parser = response_parser
        # inputWriterVariables : DynamicObjectWriterVariable list
        self.input_writer_variables = input_writer_variables
        # The writer variables used for ordering constraints
        # orderingConstraintWriterVariables : OrderingConstraintVariable list
        self.ordering_constraint_writer_variables = ordering_constraint_writer_variables
        # The reader variables used for ordering constraints
        # orderingConstraintReaderVariables : OrderingConstraintVariable list
        self.ordering_constraint_reader_variables = ordering_constraint_reader_variables

    @classmethod
    def init_json(cls, json_str):
        response_parser = json_str["responseParser"]
        input_writer_variables = json_str["inputWriterVariables"]
        ordering_constraint_writer_variables = json_str["orderingConstraintWriterVariables"]
        ordering_constraint_reader_variables = json_str["orderingConstraintReaderVariables"]
        return cls(response_parser=response_parser,
                   input_writer_variables=input_writer_variables,
                   ordering_constraint_writer_variables=ordering_constraint_writer_variables,
                   ordering_constraint_reader_variables=ordering_constraint_reader_variables)

    def __dict__(self):
        input_writer = []
        for item in self.input_writer_variables:
            input_writer.append(item.__dict__())
            logger.write_to_main(f"{input_writer}", ConfigSetting().LogConfig.grammar)
        dict_value = {"responseParser": self.response_parser.__dict__(),
                      "inputWriterVariables": input_writer,
                      "orderingConstraintWriterVariables": self.ordering_constraint_writer_variables,
                      "orderingConstraintReaderVariables": self.ordering_constraint_reader_variables}
        return dict_value


class RequestElementType(enum.Enum):
    Method = 0,
    BasePath = 1,
    Path = 2,
    QueryParameters = 3,
    HeaderParameters = 4,
    Body = 5,
    Token = 6,
    RefreshableToken = 7,
    Headers = 8,
    HttpVersion = 9,
    RequestDependencyDataItem = 10,
    Delimiter = 11


# The parts of a request
Method: TypeAlias = OperationMethod
BasePath: TypeAlias = str
PathParameters: TypeAlias = list[FuzzingPayload]
QueryParameters: TypeAlias = RequestParameterList
HeaderParameters: TypeAlias = RequestParameterList
Body: TypeAlias = RequestParameterList
Token: TypeAlias = TokenKind
RefreshableToken: TypeAlias = str
Headers: TypeAlias = list[(str, Optional[str])]
HttpVersion: TypeAlias = str
Delimiter: TypeAlias = str


# RequestElement = Union[Method, BasePath, Path, QueryParameters, HeaderParameters, Body, Token, RefreshableToken,
# Headers, HttpVersion, RequestDependencyDataItem, Delimiter]


# The additional metadata of a request that may be used during fuzzing.
class RequestMetadata:
    # Request is declared as a long-running operation via x-ms-long-running-operation
    is_long_running_operation: bool

    def __init__(self, is_long_running_operation):
        self.is_long_running_operation = is_long_running_operation

    def __dict__(self):
        dict_value = dict()
        dict_value["isLongRunningOperation"] = self.is_long_running_operation
        return dict_value


# Definition of a request according to how it should be fuzzed and
# how to parse the response
# Note: this does not match the paper, where a request type does not
# include any information about the response, but it seems appropriate here.
class Request:
    def __init__(self, request_id: RequestId,
                 method: OperationMethod, base_path: BasePath, path: PathParameters,
                 query_parameters: QueryParameters,
                 body_parameters: Body, header_parameters: HeaderParameters,
                 token: Token, headers: Headers, http_version: HttpVersion,
                 dependency_data: RequestDependencyData,
                 request_metadata: RequestMetadata
                 ):
        # The request ID.  This is used to associate requests in the grammar with
        # per-request definitions in the RESTler engine configuration.
        self.id = request_id
        self.method = method
        self.basePath = base_path
        self.path = path

        self.queryParameters = query_parameters
        self.bodyParameters = body_parameters
        self.headerParameters = header_parameters
        self.token = token
        self.headers = headers
        self.httpVersion = http_version
        self.dependencyData = dependency_data
        # The additional properties of a request
        self.requestMetadata = request_metadata

    def pathtoJson(self):
        dict_list = []
        if self.path is not None:
            for item in self.path:
                logger.write_to_main(f"type={type(item)}", ConfigSetting().LogConfig.grammar)
                if isinstance(item, Constant):
                    if item.variable_name != "/":
                        dict_list.append(item.__dict__())
                elif isinstance(item, FuzzablePayload):
                    if ConfigSetting().UsePathExamples:
                        if self.id.has_example:
                            dict_list.append(item.example_dict())
                    else:
                        dict_list.append(item.path_dict())
                else:
                    dict_list.append(item.__dict__())
        return dict_list

    def query_body_to_json(self, parameters):
        schema_dict_list = []
        example_dict_list = []
        if parameters is not None:
            for parameter in parameters:
                logger.write_to_main(f"item[0]={type(parameter[0])}, item[1]={type(parameter[1])}",
                                     ConfigSetting().LogConfig.grammar)
                logger.write_to_main(f"json_str={json.dumps(parameter[1].__dict__())}",
                                     ConfigSetting().LogConfig.grammar)
                if (parameter[0] == ParameterPayloadSource.Schema
                        or parameter[0] == ParameterPayloadSource.DictionaryCustomPayload):
                    schema_dict_list = schema_dict_list + parameter[1].__dict__()
                elif parameter[0] == ParameterPayloadSource.Examples:
                    example_dict_list = example_dict_list + parameter[1].example_dict()
                    self.id.has_example = True

        return_value = []
        if self.id.has_example:
            example_schema = {"ParameterList": example_dict_list}
            return_value.append(("Examples", example_schema))
            if self.id.has_schema:
                param_schema = {"ParameterList": schema_dict_list}
                return_value.append(("Schema", param_schema))
        else:
            param_schema = {"ParameterList": schema_dict_list}
            return_value.append(("Schema", param_schema))
        return return_value

    def header_to_json(self, param):
        schema_dict_list = []
        examples_dict_list = []
        dict_list = []
        return_value = []
        for parameter in param:
            if parameter is not None:
                for item in parameter:
                    logger.write_to_main(f"item[0]={type(item[0])}, item[1]={type(item[1])}",
                                         ConfigSetting().LogConfig.grammar)
                    logger.write_to_main(f"json_str={json.dumps(item[1].__dict__())}",
                                         ConfigSetting().LogConfig.grammar)
                    if item[0] == ParameterPayloadSource.Schema:
                        schema_dict_list = schema_dict_list + item[1].__dict__()
                    elif item[0] == ParameterPayloadSource.DictionaryCustomPayload:
                        dict_list = dict_list + item[1].__dict__()
                    elif item[0] == ParameterPayloadSource.Examples:
                        examples_dict_list = examples_dict_list + item[1].example_dict()

        logger.write_to_main(f"len(schema_dict_list)={len(schema_dict_list)}"
                             f", len(dict_list)={len(dict_list)}", ConfigSetting().LogConfig.grammar)

        if self.id.has_example:
            param_examples = dict()
            param_examples["ParameterList"] = examples_dict_list
            return_value.append(("Examples", param_examples))
            if self.id.has_schema:
                param_schema = {"ParameterList": schema_dict_list}
                return_value.append(("Schema", param_schema))
        else:
            param_schema = {"ParameterList": schema_dict_list}
            return_value.append(("Schema", param_schema))
        param_dict = {"ParameterList": dict_list}
        return_value.append(["DictionaryCustomPayload", param_dict])
        return return_value

    def __dict__(self):
        print(f"Generate Grammar Json: endpoint={self.id.endpoint}")
        request_dict = {
            "id": {
                "endpoint": self.id.endpoint,
                "method": self.id.method.name},
            "method": self.id.method.name,
            "basePath": self.basePath,
            "path": self.pathtoJson(),
            "queryParameters": self.query_body_to_json(self.queryParameters),
            "bodyParameters": self.query_body_to_json(self.bodyParameters),
            "headerParameters": self.header_to_json(self.headerParameters),
            "token": "Refreshable" if self.token == TokenKind.Refreshable else "Static",
            "headers": self.headers,
            "httpVersion": f"{self.httpVersion}",
        }
        if self.dependencyData is not None:
            request_dict["dependencyData"] = self.dependencyData.__dict__()
        request_dict["requestMetadata"] = self.requestMetadata.__dict__()
        return request_dict


# todo
REPLACE_TARGETS = ["/", ".", "__", "{", "}", "$", "-", ":"]


def split_string_iterative(s: str) -> list:
    result = []
    current = []

    for char in s:
        if char in REPLACE_TARGETS:
            if current:
                result.append(''.join(current))
            current = []
        else:
            current.append(char)

    if current:
        result.append(''.join(current))

    return result


class DynamicObjectNaming:
    ReplaceTargets = ["/", ".", "__", "{", "}", "$", "-", ":"]

    @staticmethod
    def generate_python_function_name_from_string(request_id, delimiter):
        # pattern = "|".join(map(re.escape, DynamicObjectNaming.ReplaceTargets))
        endpoint_parts = re.split('|'.join(map(re.escape, DynamicObjectNaming.ReplaceTargets)), request_id.endpoint)
        parts = endpoint_parts + [request_id.method.lower()]
        return delimiter.join(parts)

    @staticmethod
    def generate_dynamic_object_variable_name(request_id, access_path, delimiter):
        endpoint_parts = re.split('|'.join(map(re.escape, DynamicObjectNaming.ReplaceTargets)), request_id.endpoint)

        obj_id_parts = []
        if access_path is not None:
            obj_id_parts = [part for path in access_path.get_path_parts_for_name()
                            for part in re.split('|'.join(map(re.escape, DynamicObjectNaming.ReplaceTargets)), path)]

        parts = endpoint_parts + [request_id.method.lower()] + obj_id_parts
        return delimiter.join(parts)

    @staticmethod
    def generate_ordering_constraint_variable_name(source_request_id, target_request_id, delimiter: str) -> str:
        source_endpoint_parts = re.split('|'.join(map(re.escape, DynamicObjectNaming.ReplaceTargets)),
                                         source_request_id.endpoint)
        target_endpoint_parts = re.split('|'.join(map(re.escape, DynamicObjectNaming.ReplaceTargets)),
                                         target_request_id.endpoint)

        # 找到共同部分
        common_parts = []
        distinct_source_parts = []
        distinct_target_parts = []

        zipped = zip(source_endpoint_parts, target_endpoint_parts)

        for x, y in zipped:
            if x == y:
                common_parts.append(x)
            else:
                distinct_source_parts.append(x)
                distinct_target_parts.append(y)

        # 拼接结果
        result = ["__ordering__"] + common_parts + distinct_source_parts + distinct_target_parts
        return delimiter.join(result)

    @staticmethod
    def generate_id_for_custom_uuid_suffix_payload(container_name: str, property_name: str) -> str:
        if container_name:
            return f"{container_name}_{property_name}"
        return property_name

    # Because some services have a strict naming convention on identifiers,
    # this function attempts to generate a variable name to avoid violating such constraints
    # Note: the unique UUID suffix may still cause problems, which will need to be addressed
    # differently in the engine.
    @staticmethod
    def generate_prefix_for_custom_uuid_suffix_payload(suffix_payload_id):
        suffix_payload_id_restricted = "".join([ch.lower() for ch in suffix_payload_id if ch.isalpha()])[:10]
        if not suffix_payload_id_restricted:
            return suffix_payload_id
        return suffix_payload_id_restricted


# Definitions necessary for the RESTler algorithm
class GrammarDefinition:
    Requests: list[Request]

    def __init__(self, requests=None):
        if requests is None:
            requests = []
        # Request list
        self.Requests = requests

    def add(self, new_request: Request):
        self.Requests.append(new_request)

    def __dict__(self):
        json_dict = []
        for item in self.Requests:
            json_dict.append(item.__dict__())
        logger.write_to_main(f"json_dict={json_dict}", ConfigSetting().LogConfig.grammar)
        return {"Requests": json_dict}


DefaultPrimitiveValues = {
    PrimitiveType.String: "fuzzstring",  # Note: quotes are intentionally omitted.
    PrimitiveType.Uuid: "566048da-ed19-4cd3-8e0a-b7e0e1ec4d72",  # Note: quotes are intentionally omitted.
    PrimitiveType.DateTime: "2019-06-26T20:20:39+00:00",  # Note: quotes are intentionally omitted.
    PrimitiveType.Date: "2019-06-26",  # Note: quotes are intentionally omitted.
    PrimitiveType.Number: "1.23",  # Note: quotes are intentionally omitted.
    PrimitiveType.Int: "1",  # PrimitiveType.Int,
    PrimitiveType.Bool: "true",  #
    PrimitiveType.Object: "{ \"fuzz\": false }"  # PrimitiveType.Object,
}


def get_default_primitive_value(primitive_type: str):
    logger.write_to_main("DefaultPrimitiveValues={}".format(DefaultPrimitiveValues), ConfigSetting().LogConfig.grammar)
    primitive = primitive_type.lower()
    if primitive == "string":
        return DefaultPrimitiveValues[PrimitiveType.String]
    elif primitive == "uuid":
        return DefaultPrimitiveValues[PrimitiveType.Uuid]
    elif primitive == "datatime":
        return DefaultPrimitiveValues[PrimitiveType.DateTime]
    elif primitive == "date":
        return DefaultPrimitiveValues[PrimitiveType.Date]
    elif primitive == "number":
        return DefaultPrimitiveValues[PrimitiveType.Number]
    elif primitive == "int":
        return DefaultPrimitiveValues[PrimitiveType.Int]
    elif primitive == "bool":
        return DefaultPrimitiveValues[PrimitiveType.Bool]
    elif primitive == "object":
        return DefaultPrimitiveValues[PrimitiveType.Object]
