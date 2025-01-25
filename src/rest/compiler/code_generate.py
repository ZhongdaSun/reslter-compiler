# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from typing import Optional, Union, TypeAlias, List, Tuple
import enum
import json
import random

from rest.compiler.grammar import (
    ParameterPayloadSource,
    RequestParameter,
    RequestParametersPayload,
    Request,
    RequestElementType,
    Token,
    TokenKind,
    GrammarDefinition,
    Example,
    PrimitiveType,
    ParameterKind,
    CustomPayloadType,
    DynamicObjectNaming,
    ParameterList,
    PrimitiveTypeEnum,
    OrderingConstraintVariable,
    cata_ctx,
    Constant,
    DynamicObjectWriterVariable,
    DynamicObjectVariableKind,
    NestedType,
    StyleKind,
    DynamicObject,
    PayloadParts,
    RequestId,
    CustomPayload,
    FuzzablePayload)

from rest.restler.utils import restler_logger as logger
from rest.compiler.config import ConfigSetting, UninitializedError
from rest.compiler.access_paths import try_get_access_path_from_string

TAB = "\t"
RETURN = "\r\n"
SPACE = " "
SPACE_4 = 4 * f"{SPACE}"
SPACE_20 = 24 * f"{SPACE}"
BRACE = "{}"

class UnsupportedType(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class UnsupportedAccessPath(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RequestPrimitiveTypeData:
    def __init__(self, default_value: str, is_quoted: bool,
                 example_value: Union[str, None],
                 tracked_parameter_name: Union[str, None]):
        self.default_value = default_value
        self.is_quoted = is_quoted
        self.example_value = example_value
        self.tracked_parameter_name = tracked_parameter_name


DynamicObjectWriter: TypeAlias = str


# IMPORTANT ! All primitives must be supported in restler/engine/primitives.py
class RequestPrimitiveTypeEnum(enum.Enum):
    Restler_static_string_constant = 0,
    Restler_static_string_variable = 1,
    Restler_static_string_jtoken_delim = 2,
    Restler_fuzzable_string = 3,
    Restler_fuzzable_datetime = 4,
    Restler_fuzzable_date = 5,
    Restler_fuzzable_object = 6,
    # Restler_fuzzable_delim = 7,
    Restler_fuzzable_uuid4 = 8,
    Restler_fuzzable_group = 9,
    Restler_fuzzable_bool = 10,
    Restler_fuzzable_int = 11,
    Restler_fuzzable_number = 12,
    Restler_multipart_formdata = 13,
    Restler_custom_payload = 14,
    Restler_custom_payload_header = 15,
    Restler_custom_payload_query = 16,
    # Payload name, dynamic object writer name
    Restler_custom_payload_uuid4_suffix = 17,
    Restler_refreshable_authentication_token = 18,
    Restler_basepath = 19,
    Shadow_values = 20,
    Response_parser = 21,
    Delimiter = 22


class RequestPrimitiveType:
    primitive_data: RequestPrimitiveTypeData
    dynamic_object: Optional[DynamicObjectWriter]
    type: RequestPrimitiveTypeEnum

    def __init__(self, request_data: RequestPrimitiveTypeData,
                 dynamic_object: Union[DynamicObjectWriter, None]):
        self.primitive_data = request_data
        self.dynamic_object = dynamic_object
        self.type = RequestPrimitiveTypeEnum.Restler_static_string_constant

    @classmethod
    def static_string_constant(cls, value):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_static_string_constant
        return obj

    @classmethod
    def static_string_variable(cls, value: str, is_quoted: bool):
        data = RequestPrimitiveTypeData(value, is_quoted, None, None)
        obj = cls(request_data=data, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_static_string_variable
        return obj

    @classmethod
    def static_string_jtoken_delim(cls, value: str, is_quoted: bool):
        data = RequestPrimitiveTypeData(value, is_quoted, None, None)
        obj = cls(request_data=data, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_static_string_jtoken_delim
        return obj

    @classmethod
    def fuzzable_string(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_string
        return obj

    @classmethod
    def fuzzable_datetime(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_datetime
        return obj

    @classmethod
    def fuzzable_date(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_date
        return obj

    @classmethod
    def fuzzable_object(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_object
        return obj

    @classmethod
    def fuzzable_uuid4(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_uuid4
        return obj

    @classmethod
    def fuzzable_bool(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_bool
        return obj

    @classmethod
    def fuzzable_int(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_int
        return obj

    @classmethod
    def fuzzable_number(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_number
        return obj

    @classmethod
    def fuzzable_group(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_fuzzable_group
        return obj

    @classmethod
    def multipart_formdata(cls, value: str):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_multipart_formdata
        return obj

    @classmethod
    def custom_payload(cls, data: RequestPrimitiveTypeData, dynamic_object: DynamicObjectWriter):
        obj = cls(request_data=data, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_custom_payload
        return obj

    @classmethod
    def custom_payload_header(cls, value: str, dynamic_object: DynamicObjectWriter):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_custom_payload_header
        return obj

    @classmethod
    def custom_payload_query(cls, value: str, dynamic_object: DynamicObjectWriter):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_custom_payload_query
        return obj

    @classmethod
    def custom_payload_uuid4_suffix(cls, value: str, is_quoted: bool, dynamic_object: DynamicObjectWriter):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=is_quoted, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=dynamic_object)
        obj.type = RequestPrimitiveTypeEnum.Restler_custom_payload_uuid4_suffix
        return obj

    @classmethod
    def refreshable_authentication_token(cls, value: str):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_refreshable_authentication_token
        return obj

    @classmethod
    def basepath(cls, value: str):
        data = RequestPrimitiveTypeData(value, False, None, None)
        obj = cls(request_data=data, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Restler_basepath
        return obj

    @classmethod
    def shadow_values(cls, value: str):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Shadow_values
        return obj

    @classmethod
    def response_parser(cls, value: str):
        primitive_type = RequestPrimitiveTypeData(default_value=value, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Response_parser
        return obj

    @classmethod
    def delimiter(cls):
        primitive_type = RequestPrimitiveTypeData(default_value=RETURN, is_quoted=False, example_value=None,
                                                  tracked_parameter_name=None)
        obj = cls(request_data=primitive_type, dynamic_object=None)
        obj.type = RequestPrimitiveTypeEnum.Delimiter
        return obj


class NameGenerators:
    @staticmethod
    def generate_dynamic_object_ordering_constraint_variable_definition(source_request_id, target_request_id):
        var_name = DynamicObjectNaming.generate_ordering_constraint_variable_name(source_request_id,
                                                                                  target_request_id, "_")
        return f"{var_name} = dependencies.DynamicVariable(\"{var_name}\")\n"

    @staticmethod
    def generate_producer_endpoint_response_parser_function_name(request_id):
        return f"parse_{DynamicObjectNaming.generate_python_function_name_from_string(request_id, "")}"

    @staticmethod
    def generate_dynamic_object_variable_definition(response_access_path_parts, request_id):
        var_name = DynamicObjectNaming.generate_dynamic_object_variable_name(request_id,
                                                                             response_access_path_parts,
                                                                             "_")
        return f"{var_name} = dependencies.DynamicVariable(\"{var_name}\")\n"


def format_restler_static_string_constant(primitive_type: RequestPrimitiveType):
    if primitive_type.primitive_data and primitive_type.primitive_data.default_value != "":
        raw_value = primitive_type.primitive_data.default_value \
            if primitive_type.primitive_data.default_value else None
        s, delim = quote_string_for_python_grammar(raw_value)
        return f"primitives.restler_static_string({delim}{s}{delim})"
    return ""


def format_restler_static_string_variable(primitive_type: RequestPrimitiveType):
    return (f"primitives.restler_static_string({primitive_type.primitive_data.default_value}, "
            f"quoted={str(primitive_type.primitive_data.is_quoted)})")


def format_restler_static_string_jtoken_delim(primitive_type: RequestPrimitiveType):
    if primitive_type.primitive_data and primitive_type.primitive_data.default_value != "":
        s, delim = quote_string_for_python_grammar(primitive_type.primitive_data.default_value)
        return f"primitives.restler_static_string({delim}{s}{delim})"
    return ""


def format_restler_fuzzable_string(primitive_type: RequestPrimitiveType):
    # Implement the logic for Restler_fuzzable_string
    if primitive_type.primitive_data.default_value == "":
        print("ERROR: fuzzable strings should not be empty. Skipping.")
        return ""
    else:
        str_value, delim = quote_string_for_python_grammar(primitive_type.primitive_data.default_value)
        quoted_default_string = f"{delim}{str_value}{delim}"
        example_parameter = get_example_primitive_parameter(primitive_type.primitive_data.example_value)
        tracked_param_name = get_tracked_param_primitive_parameter(
            primitive_type.primitive_data.tracked_parameter_name)
        if primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_string:
            return (f"primitives.restler_fuzzable_string({quoted_default_string}, "
                    f"quoted={primitive_type.primitive_data.is_quoted}{example_parameter}{tracked_param_name})")
        elif primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_datetime:
            return (f"primitives.restler_fuzzable_datetime({quoted_default_string}, "
                    f"quoted={primitive_type.primitive_data.is_quoted}{example_parameter}{tracked_param_name})")
        elif primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_date:
            return (f"primitives.restler_fuzzable_date({quoted_default_string}, "
                    f"quoted={primitive_type.primitive_data.is_quoted}{example_parameter}{tracked_param_name})")
        elif primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_bool:
            if example_parameter or tracked_param_name:
                return (f"primitives.restler_fuzzable_bool({quoted_default_string}"
                        f"{example_parameter}{tracked_param_name})")
            else:
                return f"primitives.restler_fuzzable_bool({quoted_default_string})"
        elif primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_int:
            return (f"primitives.restler_fuzzable_int({quoted_default_string}"
                    f"{example_parameter}{tracked_param_name})")
        elif primitive_type.type == RequestPrimitiveTypeEnum.Restler_fuzzable_number:
            return (f"primitives.restler_fuzzable_number({quoted_default_string}"
                    f"{example_parameter}{tracked_param_name})")


def format_restler_fuzzable_datetime(primitive_type: RequestPrimitiveType):
    str_value, delim = quote_string_for_python_grammar(primitive_type.primitive_data.default_value)
    quoted_default_string = f"{delim}{str_value}{delim}"
    example_parameter = get_example_primitive_parameter(primitive_type.primitive_data.example_value)
    tracked_param_name = get_tracked_param_primitive_parameter(
        primitive_type.primitive_data.tracked_parameter_name)
    return (f"primitives.restler_fuzzable_datetime({quoted_default_string}, "
            f"quoted={primitive_type.primitive_data.is_quoted}{example_parameter}{tracked_param_name})")


def format_restler_fuzzable_object(primitive_type: RequestPrimitiveType):
    str_value, delim = quote_string_for_python_grammar(primitive_type.primitive_data.default_value)
    quoted_default_string = f"{delim}{str_value}{delim}"
    example_parameter = get_example_primitive_parameter(primitive_type.primitive_data.example_value)
    tracked_param_name = get_tracked_param_primitive_parameter(
        primitive_type.primitive_data.tracked_parameter_name)
    if example_parameter or tracked_param_name:
        return (f"primitives.restler_fuzzable_object({quoted_default_string}"
                f"{example_parameter}{tracked_param_name})")
    else:
        return f"primitives.restler_fuzzable_object({quoted_default_string})"


"""
def format_restler_fuzzable_delim(primitive_type: RequestPrimitiveType):
    raise "NotImplemented"
"""


def format_restler_fuzzable_uuid4(primitive_type: RequestPrimitiveType):
    raise "NotImplemented"


def format_restler_fuzzable_group(primitive_type: RequestPrimitiveType):
    # Implement the logic for Restler_fuzzable_group
    # Add conditions for other Restler primitives here
    return (f"primitives.restler_fuzzable_group("
            f"{primitive_type.primitive_data.default_value},"
            f"quoted={primitive_type.primitive_data.is_quoted}"
            f"{get_example_primitive_parameter(primitive_type.primitive_data.example_value)})")


def format_restler_fuzzable_int(primitive_type: RequestPrimitiveType):
    return (f"primitives.restler_fuzzable_int(\"{primitive_type.primitive_data.default_value}\""
            f"{get_example_primitive_parameter(primitive_type.primitive_data.example_value)}"
            f"{get_tracked_param_primitive_parameter(primitive_type.primitive_data.tracked_parameter_name)}"
            f"{format_dynamic_object_variable(primitive_type.dynamic_object)})")


def format_restler_fuzzable_number(primitive_type: RequestPrimitiveType):
    if primitive_type.primitive_data and primitive_type.primitive_data.default_value != "":
        raw_value = primitive_type.primitive_data.default_value \
            if primitive_type.primitive_data.default_value else None
        s, delim = quote_string_for_python_grammar(raw_value)
        return f"primitives.restler_fuzzable_number({delim}{s}{delim})"
    return ""


def format_restler_multipart_formdata(primitive_type: RequestPrimitiveType):
    raise "NotImplemented"


def format_restler_custom_payload(primitive_type: RequestPrimitiveType):
    return (f"primitives.restler_custom_payload(\"{primitive_type.primitive_data.default_value}\", "
            f"quoted={str(primitive_type.primitive_data.is_quoted)})")


def format_restler_custom_payload_header(primitive_type: RequestPrimitiveType):
    return (f"primitives.restler_custom_payload_header(\"{primitive_type.primitive_data.default_value}\""
            f"{format_dynamic_object_variable(primitive_type.dynamic_object)})")


def format_restler_custom_payload_uuid4_suffix(primitive_type: RequestPrimitiveType):
    return (f"primitives.restler_custom_payload_uuid4_suffix(\"{primitive_type.primitive_data.default_value}\", "
            f"quoted={str(primitive_type.primitive_data.is_quoted)})")


def format_restler_custom_payload_query(primitive_type: RequestPrimitiveType):
    return f"primitives.restler_custom_payload_query(\"{primitive_type.primitive_data.default_value}\")"


def format_restler_basepath(primitive_type: RequestPrimitiveType):
    return f"primitives.restler_basepath(\"{primitive_type.primitive_data.default_value}\")"


def format_restler_refreshable_authentication_token(primitive_type: RequestPrimitiveType):
    return f"primitives.restler_refreshable_authentication_token(\"{primitive_type.primitive_data.default_value}\")"


def format_restler_shadow_values(primitive_type: RequestPrimitiveType):
    raise "NotImplemented"


def format_restler_response_parser(primitive_type: RequestPrimitiveType):
    if primitive_type is not None:
        return primitive_type.primitive_data.default_value


def format_restler_response_delimiter(primitive_type: RequestPrimitiveType):
    return "\n"


DefaultRequestPrimitiveTypeEnum = {
    RequestPrimitiveTypeEnum.Restler_static_string_constant: format_restler_static_string_constant,
    RequestPrimitiveTypeEnum.Restler_static_string_variable: format_restler_static_string_variable,
    RequestPrimitiveTypeEnum.Restler_static_string_jtoken_delim: format_restler_static_string_jtoken_delim,
    RequestPrimitiveTypeEnum.Restler_fuzzable_string: format_restler_fuzzable_string,
    RequestPrimitiveTypeEnum.Restler_fuzzable_datetime: format_restler_fuzzable_datetime,
    RequestPrimitiveTypeEnum.Restler_fuzzable_date: format_restler_fuzzable_string,
    RequestPrimitiveTypeEnum.Restler_fuzzable_object: format_restler_fuzzable_object,
    # RequestPrimitiveTypeEnum.Restler_fuzzable_delim: format_restler_fuzzable_delim,
    RequestPrimitiveTypeEnum.Restler_fuzzable_uuid4: format_restler_fuzzable_uuid4,
    RequestPrimitiveTypeEnum.Restler_fuzzable_group: format_restler_fuzzable_group,
    RequestPrimitiveTypeEnum.Restler_fuzzable_bool: format_restler_fuzzable_string,
    RequestPrimitiveTypeEnum.Restler_fuzzable_int: format_restler_fuzzable_string,
    RequestPrimitiveTypeEnum.Restler_fuzzable_number: format_restler_fuzzable_string,
    RequestPrimitiveTypeEnum.Restler_multipart_formdata: format_restler_multipart_formdata,
    RequestPrimitiveTypeEnum.Restler_custom_payload: format_restler_custom_payload,
    RequestPrimitiveTypeEnum.Restler_custom_payload_header: format_restler_custom_payload_header,
    RequestPrimitiveTypeEnum.Restler_custom_payload_query: format_restler_custom_payload_query,
    # Payload name, dynamic object writer name
    RequestPrimitiveTypeEnum.Restler_custom_payload_uuid4_suffix: format_restler_custom_payload_uuid4_suffix,
    RequestPrimitiveTypeEnum.Restler_refreshable_authentication_token: format_restler_refreshable_authentication_token,
    RequestPrimitiveTypeEnum.Restler_basepath: format_restler_basepath,
    RequestPrimitiveTypeEnum.Shadow_values: format_restler_shadow_values,
    RequestPrimitiveTypeEnum.Response_parser: format_restler_response_parser,
    RequestPrimitiveTypeEnum.Delimiter: format_restler_response_delimiter
}


def format_restler_primitive(primitive_type: RequestPrimitiveType):
    logger.write_to_main(f"primitive_type={primitive_type.type}", ConfigSetting().LogConfig.code_generate)
    if isinstance(primitive_type.type, RequestPrimitiveTypeEnum):
        # Define the getExamplePrimitiveParameter and getTrackedParamPrimitiveParameter functions here
        format_func = DefaultRequestPrimitiveTypeEnum[primitive_type.type]
        return format_func(primitive_type=primitive_type)
    else:
        raise UnsupportedType("Primitive not yet implemented: {p}")


# getRestlerPythonPayload
# Gets the RESTler primitive that corresponds to the specified fuzzing payload
def get_restler_python_payload(payload, is_quoted):
    logger.write_to_main(f"payload={payload.__dict__()}, type(payload)={type(payload)}",
                         ConfigSetting().LogConfig.code_generate)
    if isinstance(payload, Constant):
        v = payload.variable_name
        return RequestPrimitiveType.static_string_constant(v)
    elif isinstance(payload, FuzzablePayload):
        v = payload.default_value
        exv = payload.example_value
        parameter_name = payload.parameter_name
        dynamic_object = DynamicObjectWriter(
            payload.dynamic_object.variable_name) if payload.dynamic_object is not None else None
        request_primitive_type = RequestPrimitiveTypeData(default_value=v, is_quoted=is_quoted, example_value=exv,
                                                          tracked_parameter_name=parameter_name)
        if payload.primitive_type == PrimitiveType.Bool:
            return RequestPrimitiveType.fuzzable_bool(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.DateTime:
            return RequestPrimitiveType.fuzzable_datetime(data=request_primitive_type,
                                                          dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Date:
            return RequestPrimitiveType.fuzzable_date(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.DateTime:
            return RequestPrimitiveType.fuzzable_datetime(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.String:
            return RequestPrimitiveType.fuzzable_string(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Object:
            return RequestPrimitiveType.fuzzable_object(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Int:
            return RequestPrimitiveType.fuzzable_int(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Number:
            return RequestPrimitiveType.fuzzable_number(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Uuid:
            return RequestPrimitiveType.fuzzable_uuid4(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.primitive_type == PrimitiveType.Enum:
            if isinstance(payload.default_value, PrimitiveTypeEnum):
                default_str = f", default_enum=\"{payload.default_value.default_value}\"" \
                    if payload.default_value.default_value is not None else ""
                value_str = ""
                length = len(payload.default_value.value)
                for index, item in enumerate(payload.default_value.value):
                    if index == 0:
                        value_str = f"\'{item}\'"
                    else:
                        value_str = value_str + f",\'{item}\'"
                group_value = f"\"{payload.default_value.name}\", [{value_str}]  "
                request_primitive_type = RequestPrimitiveTypeData(default_value=group_value,
                                                                  is_quoted=is_quoted,
                                                                  example_value=exv,
                                                                  tracked_parameter_name=parameter_name)
                return RequestPrimitiveType.fuzzable_group(data=request_primitive_type, dynamic_object=dynamic_object)
    elif type(payload) is CustomPayload:
        dynamic_object = DynamicObjectWriter(payload.dynamic_object.variable_name) \
            if payload.dynamic_object is not None else None
        request_primitive_type = RequestPrimitiveTypeData(default_value=payload.payload_value, is_quoted=is_quoted,
                                                          example_value=None, tracked_parameter_name=None)
        if payload.payload_type == CustomPayloadType.String:
            return RequestPrimitiveType.custom_payload(data=request_primitive_type, dynamic_object=dynamic_object)
        elif payload.payload_type == CustomPayloadType.UuidSuffix:
            return RequestPrimitiveType.custom_payload_uuid4_suffix(value=payload.payload_value,
                                                                    is_quoted=is_quoted,
                                                                    dynamic_object=dynamic_object)
        elif payload.payload_type == CustomPayloadType.Header:
            return RequestPrimitiveType.custom_payload_header(value=payload.payload_value,
                                                              dynamic_object=dynamic_object)
        elif payload.payload_type == CustomPayloadType.Query:
            return RequestPrimitiveType.custom_payload_query(value=payload.payload_value,
                                                             dynamic_object=dynamic_object)
    elif type(payload) is DynamicObject:
        return RequestPrimitiveType.static_string_variable(f"{payload.variable_name}.reader()", is_quoted)
    elif type(payload) is PayloadParts:
        raise Exception("Expected primitive payload")


def format_property_name(name, tab_seq, is_comma=True):
    if name is None or name == "":
        return RequestPrimitiveType.static_string_constant(value="")
    else:
        if is_comma:
            return RequestPrimitiveType.static_string_constant(value=f"{tab_seq}\"{name}\":")
        else:
            return RequestPrimitiveType.static_string_constant(value=f"{tab_seq}{name}")


def format_query_parameter_name(name):
    return RequestPrimitiveType.static_string_constant(value=f"{name}=")


def format_header_parameter_name(name):
    return RequestPrimitiveType.static_string_constant(value=f"{name}: ")


def get_tab_indented_line_start(level):
    if level > 0:
        tabs = SPACE_4 * level
        return "\n" + tabs
    else:
        return ""


def format_json_body_parameter(
        property_name: str,
        property_type: str,
        name_payload_seq: list | None,
        inner_properties: list[list],
        tab_level: int
):
    """
    Pretty-print a JSON property for a REST API body.

    Args:
        property_name (str): The name of the JSON property.
        property_type (str): The type of the property (e.g., "Object", "Array", "Property").
        name_payload_seq (list | None): Payload for the current property.
        inner_properties (list[list]): A list of payloads for nested properties.
        tab_level (int): Indentation level.

    Returns:
        list: The pretty-printed JSON as a list of parts.
    """
    logger.write_to_main(f"property_name={property_name}, property_type={property_type}, "
                         f"name_payload_seq={name_payload_seq}, inner_properties={inner_properties}"
                         f"tab_level={tab_level}", ConfigSetting().LogConfig.code_generate)
    tab_seq = ""
    tab_start = get_tab_indented_line_start(tab_level)
    if tab_start:
        # tab_seq.append(f"{tab_start}")
        tab_seq = tab_start

    if name_payload_seq:
        for item in name_payload_seq:
            if item.type == RequestPrimitiveTypeEnum.Restler_static_string_constant:
                raw_value = item.primitive_data.default_value
                item.primitive_data.default_value = tab_seq + raw_value
        logger.write_to_main(f"name_payload_seq={name_payload_seq}", ConfigSetting().LogConfig.code_generate)
        return name_payload_seq
    else:
        cs = []
        result = []
        # The payload is not specified at this level, so use the one specified at lower levels.
        # The inner properties must be comma separated
        start_second_item = 0
        need_new_line = 1
        for index, item in enumerate(inner_properties):
            # Filter empty elements, which are the result of filtered child properties
            for loop, inner in enumerate(item):
                logger.write_to_main(f"inner={inner.primitive_data.default_value}, type={inner.type}",
                                     ConfigSetting().LogConfig.code_generate)
                if start_second_item > 0 and inner and loop == 0:
                    if inner.type == RequestPrimitiveTypeEnum.Restler_static_string_constant:
                        raw_value = inner.primitive_data.default_value
                        s, delim = quote_string_for_python_grammar(raw_value)
                        str_value = s.split("\t")
                        if delim == '"""':
                            for str_index in str_value:
                                if str_index is not None and str_index != "" and str_index != "\n":
                                    s, delim = quote_string_for_python_grammar(s)
                        f_value = format_property_name(s, tab_level * SPACE_4, False)
                        logger.write_to_main(f"f_value={f_value.primitive_data.default_value}",
                                             ConfigSetting().LogConfig.code_generate)
                        if f_value.primitive_data.default_value == "":
                            if tab_level > 1:
                                f_value.primitive_data.default_value = tab_seq + ",\n"
                            else:
                                f_value.primitive_data.default_value = ",\n"
                        else:
                            if need_new_line == 0:
                                f_value.primitive_data.default_value = tab_seq + SPACE_4 + ", " + f_value.primitive_data.default_value
                            elif need_new_line == 1:
                                f_value.primitive_data.default_value = ", " + f_value.primitive_data.default_value
                            else:
                                if tab_level in [3, 4, 7, 8]:
                                    f_value.primitive_data.default_value = ", " + f_value.primitive_data.default_value
                                elif tab_level in [0, 1, 2, 5, 6]:
                                    f_value.primitive_data.default_value = "\n, " + f_value.primitive_data.default_value
                        cs.append(f_value)
                    else:
                        cs.append(inner)
                else:
                    cs.append(inner)
            if start_second_item == 0:
                if len(item) > 0:
                    start_second_item = 1
            if len(item) > 0:
                last_item = item[-1]
                if last_item.type == RequestPrimitiveTypeEnum.Restler_static_string_constant:
                    if "]" in last_item.primitive_data.default_value:
                        need_new_line = 1
                    else:
                        need_new_line = 0
                else:
                    need_new_line = 1
                """
                elif (last_item.type == RequestPrimitiveTypeEnum.Restler_fuzzable_object
                    and last_item.primitive_data.default_value == "{ }"):
                    need_new_line = 2
                """


        logger.write_to_main(f"cs={len(cs)}", ConfigSetting().LogConfig.code_generate)
        if property_type == NestedType.Object:
            if tab_level == 0:
                left = [RequestPrimitiveType.static_string_constant("{")]
                right = [RequestPrimitiveType.static_string_constant(f"{SPACE_4}" + "}")]
                if len(cs) == 0:
                    right = [RequestPrimitiveType.static_string_constant("}")]
                elif len(cs) > 1:
                    last_element = cs[-1]
                    value = last_element.primitive_data.default_value
                    if last_element.type == RequestPrimitiveTypeEnum.Restler_static_string_constant:
                        if "}" not in value and "]" not in value:
                            right = [RequestPrimitiveType.static_string_constant(f"\n{SPACE_4}" + "}")]
                        elif "]" in value:
                            right = [RequestPrimitiveType.static_string_constant("}")]
                    else:
                        right = [RequestPrimitiveType.static_string_constant("}")]
                result = left + cs + right
            else:
                left = [RequestPrimitiveType.static_string_constant(tab_level * SPACE_4 + "{")]
                right = [RequestPrimitiveType.static_string_constant(tab_seq + "}")]
                result = [format_property_name(property_name, tab_seq)] + left + cs + right
        elif property_type == NestedType.Array:
            right = [RequestPrimitiveType.static_string_constant(tab_seq + "]")]
            if tab_level == 0:
                left = [RequestPrimitiveType.static_string_constant(tab_seq + "[")]
                result = left + cs + right
            else:
                if len(cs) == 0:
                    restler_array = format_property_name(property_name, tab_seq)
                    restler_str = restler_array.primitive_data.default_value + tab_seq + "["
                    left = [RequestPrimitiveType.static_string_constant(restler_str)]
                else:
                    restler_array = format_property_name(property_name, tab_seq)
                    restler_str = restler_array.primitive_data.default_value + tab_seq + "[\n"
                    left = [RequestPrimitiveType.static_string_constant(restler_str)]
                logger.write_to_main(f"cs={len(left + cs + right)}", ConfigSetting().LogConfig.code_generate)
                result = left + cs + right
        elif property_type == NestedType.Property:
            # test_path_annotation:
            # primitives.restler_static_string(""",
            # "storeProperties":
            #    {
            #        "tags":"""),
            # primitives.restler_static_string(_stores_post_metadata.reader(), quoted=False),
            # primitives.restler_static_string("""
            #    }
            #    ,
            # the comma will be start in a new line.
            if len(cs) > 1:
                last_element = cs[-1]
                value = last_element.primitive_data.default_value
                if last_element.type == RequestPrimitiveTypeEnum.Restler_static_string_constant and "}" in value:
                    if tab_level == 1:
                        last_element.primitive_data.default_value = last_element.primitive_data.default_value + "\n"
                    else:
                        last_element.primitive_data.default_value = last_element.primitive_data.default_value

            result = [RequestPrimitiveType.static_string_constant(value=f"{tab_seq}\"{property_name}\":\n{SPACE_4*2}")] + cs
        else:
            result = cs
        logger.write_to_main(f"result={len(result)}", ConfigSetting().LogConfig.code_generate)
        return result


# formatQueryObjectParameters
def format_query_object_parameters(parameter_name, inner_properties):
    raise NotImplementedError("Objects in query parameters are not supported yet.")


# formatHeaderObjectParameters
def format_header_object_parameters(parameter_name, inner_properties):
    # The default is "style: simple, explode: false"
    raise NotImplementedError("Objects in header parameters are not supported yet.")


# formatHeaderArrayParameters
def format_header_array_parameters(parameter_name, inner_properties):
    all_list_param: List[RequestPrimitiveType] = []
    cs = []
    for array_item_primitives in inner_properties:
        for item in array_item_primitives:
            if (item.type == RequestPrimitiveTypeEnum.Restler_static_string_constant
                    and item.primitive_data.default_value != parameter_name):
                pass
            else:
                all_list_param.append(item)
    tail = len(all_list_param)

    for i, array_item_primitives in enumerate(all_list_param):
        if i == 0:
            cs.append(format_header_parameter_name(parameter_name))
            cs.append(array_item_primitives)
        elif 0 < i < tail:
            cs.append(RequestPrimitiveType.static_string_constant(value=","))
            cs.append(array_item_primitives)
        else:
            cs.append(array_item_primitives)

    return cs


# formatQueryArrayParameters
def format_query_array_parameters(parameter_name: str, inner_properties: List[List[RequestPrimitiveType]],
                                  request_parameter: Optional[RequestParameter]) -> List[RequestPrimitiveType]:
    # The default is "style: form, explode: true"
    exp_option = request_parameter.serialization.explode \
        if request_parameter and request_parameter.serialization else True
    style = request_parameter.serialization.style \
        if request_parameter and request_parameter.serialization else StyleKind.Simple
    all_list_param: List[RequestPrimitiveType] = []
    cs = []
    if len(inner_properties) == 0:
        cs.append(format_query_parameter_name(parameter_name))
        return cs

    for array_item_primitives in inner_properties:
        for item in array_item_primitives:
            if (item.type == RequestPrimitiveTypeEnum.Restler_static_string_constant
                    and item.primitive_data.default_value != parameter_name):
                pass
            else:
                all_list_param.append(item)
    tail = len(all_list_param)
    for i, array_item_primitives in enumerate(all_list_param):
        # If 'explode': true is specified, the array name is printed before each array item
        if exp_option:
            if i == 0:
                cs.append(format_query_parameter_name(parameter_name))
                cs.append(array_item_primitives)
            elif 0 < i < tail:
                cs.append(RequestPrimitiveType.static_string_constant(value="&"))
                cs.append(array_item_primitives)
            else:
                cs.append(array_item_primitives)
        else:
            if style == StyleKind.Form:
                if i == 0:
                    cs.append(format_query_parameter_name(parameter_name))
                    cs.append(array_item_primitives)
                elif 0 < i < tail:
                    cs.append(RequestPrimitiveType.static_string_constant(value=","))
                    cs.append(array_item_primitives)
                else:
                    cs.append(array_item_primitives)
            elif style == StyleKind.Simple:
                if i < tail - 1:
                    cs.append(format_query_parameter_name(parameter_name))
                    cs.append(array_item_primitives)
                    cs.append(RequestPrimitiveType.static_string_constant(value="&"))
                else:
                    cs.append(format_query_parameter_name(parameter_name))
                    cs.append(array_item_primitives)

            else:
                raise NotImplementedError(f"Serialization type {style} is not implemented yet.")

    # Handle if `exp_option` is false or cs is empty
    # if not exp_option or not cs:
    #    return [format_query_parameter_name(parameter_name)] + cs

    return cs


# Format a header parameter that is either an array or object
# See https://swagger.io/docs/specification/serialization/#query.
# Any other type of serialization (e.g. encoding and passing complex json objects)
# will need to be added as a config option for RESTler.
def format_nested_header_parameter(parameter_name,
                                   property_type,
                                   name_payload_seq,
                                   inner_properties):
    if name_payload_seq:
        return name_payload_seq
    else:
        if property_type == NestedType.Object:
            return format_header_object_parameters(parameter_name, inner_properties)
        elif property_type == NestedType.Array:
            return format_header_array_parameters(parameter_name, inner_properties)
        elif property_type == NestedType.Property:
            raise ValueError("Invalid context for property type.")


# Format a query parameter that is either an array or object
# See https://swagger.io/docs/specification/serialization/#query.
# Any other type of serialization (e.g. encoding and passing complex json objects)
# will need to be added as a config option for RESTler.
def format_nested_query_parameter(parameter_name,
                                  property_type: NestedType,
                                  name_payload_seq,
                                  inner_properties,
                                  request_parameter):
    if name_payload_seq:
        return name_payload_seq
    else:
        if property_type == NestedType.Object:
            return format_query_object_parameters(parameter_name, inner_properties)
        elif property_type == NestedType.Array:
            return format_query_array_parameters(parameter_name, inner_properties, request_parameter)
        elif property_type == NestedType.Property:
            message = "Nested properties in query parameters are not supported yet. Property name: {}.".format(
                parameter_name)
            raise NotImplementedError(message)


# generatePythonParameter
# Generate the RESTler grammar for a request parameter
def generate_python_parameter(parameter_source,
                              parameter_kind,
                              request_parameter: RequestParameter):
    parameter_name = request_parameter.name
    parameter_payload = request_parameter.payload
    # Just for test_code_generated cases: test_python_grammar_parameter_sanity to initialize the log config.
    try:
        logger.write_to_main(f"parameter_name={parameter_name}, parameter_payload={parameter_payload.__dict__()}",
                             ConfigSetting().LogConfig.code_generate)
    except UninitializedError:
        from rest.compiler.workflow import load_log_config
        from rest.compiler.config import Config
        config = Config()
        load_log_config(config)
        logger.write_to_main(f"parameter_name={parameter_name}, parameter_payload={parameter_payload.__dict__()}",
                             ConfigSetting().LogConfig.code_generate)

    def get_tree_level(parent_level, p):
        return parent_level + 1

    def visit_leaf(level, p):
        def is_primitive_type_quoted(primitive_type, is_null_value):
            if is_null_value:
                return False
            elif primitive_type in [PrimitiveType.String, PrimitiveType.DateTime, PrimitiveType.Date,
                                    PrimitiveType.Uuid]:
                return True
            elif primitive_type in [PrimitiveType.Object, PrimitiveType.Int, PrimitiveType.Bool, PrimitiveType.Number]:
                return False
            elif isinstance(primitive_type, PrimitiveTypeEnum):
                return is_primitive_type_quoted(primitive_type.primitive_type, False)


        # Exclude 'readonly' parameters

        include_property = not p.is_readonly and (p.is_required or ConfigSetting().IncludeOptionalParameters)
        # include_property = (p.is_required or ConfigSetting().IncludeOptionalParameters)
        logger.write_to_main(f"p={p}, parameter_source={parameter_source}，include_property={include_property}",
                             ConfigSetting().LogConfig.code_generate)
        # Parameters from an example payload are always included
        if parameter_source == ParameterPayloadSource.Examples or include_property:
            name_seq = []
            tab_seq = get_tab_indented_line_start(level)
            if parameter_kind == ParameterKind.Query:
                name_seq.append(format_query_parameter_name(request_parameter.name))
            elif parameter_kind == ParameterKind.Header:
                name_seq.append(format_header_parameter_name(request_parameter.name))
            else:
                name_seq.append(format_property_name(p.name, tab_seq))
            logger.write_to_main("name_seq={}".format(name_seq), ConfigSetting().LogConfig.code_generate)
            # 'needQuotes' must be based on the underlying type of the payload.
            need_quotes, is_fuzzable, is_dynamic_object = False, False, False
            payload = p.payload
            logger.write_to_main("payload={}".format(payload), ConfigSetting().LogConfig.code_generate)
            if type(payload) is CustomPayload:
                is_fuzzable = True
                if not payload.is_object:
                    need_quotes = is_primitive_type_quoted(payload.primitive_type, False)
            elif type(payload) is Constant:
                # TODO: improve the metadata of FuzzingPayload.Constant to capture whether
                # the constant represents an object,
                # rather than relying on the formatting behavior of JToken.ToString.
                if payload.primitive_type == "String" and payload.variable_name and "\n" not in payload.variable_name:
                    need_quotes = True
            elif type(payload) is FuzzablePayload:
                # Note: this is a current RESTler limitation -
                # fuzzable values may not be set to null without changing the grammar.
                if payload.primitive_type == PrimitiveType.Enum:
                    need_quotes = is_primitive_type_quoted(payload.default_value, False)
                else:
                    need_quotes = is_primitive_type_quoted(payload.primitive_type, False)
                is_fuzzable = True
            elif type(payload) is DynamicObject:
                need_quotes = is_primitive_type_quoted(payload.primitive_type, False)
                is_dynamic_object = True
            logger.write_to_main(f"need_quotes={need_quotes}", ConfigSetting().LogConfig.code_generate)

            payload_seq = []
            # If the value is a constant, quotes are inserted at compile time.
            # If the value is a fuzzable, quotes are inserted at run time, because
            # the user may choose to fuzz with quoted or unquoted values.
            if need_quotes and not is_fuzzable and not is_dynamic_object:
                payload_seq = [RequestPrimitiveType.static_string_constant(value="\"")]
                logger.write_to_main("payload_seq={}".format(payload_seq), ConfigSetting().LogConfig.code_generate)
            is_quoted = parameter_kind == ParameterKind.Body and need_quotes and (is_fuzzable or is_dynamic_object)
            logger.write_to_main(f"is_quoted={is_quoted}", ConfigSetting().LogConfig.code_generate)
            grammar = get_restler_python_payload(payload, is_quoted)
            logger.write_to_main("grammar={}".format(grammar), ConfigSetting().LogConfig.code_generate)
            payload_seq = payload_seq + [grammar]

            if need_quotes and not is_fuzzable and not is_dynamic_object:
                payload_seq = payload_seq + [RequestPrimitiveType.static_string_constant(value="\"")]
            return name_seq + payload_seq
        else:
            return []

    def visit_inner(level, p, inner_properties):
        logger.write_to_main(
            f"p={p.__dict__()}, inner_properties={len(inner_properties)}", ConfigSetting().LogConfig.code_generate)
        # Exclude 'readonly' parameters
        include_property = not p.is_readonly and (p.is_required or ConfigSetting().IncludeOptionalParameters)
        # Parameters from an example payload are always included
        if parameter_source == ParameterPayloadSource.Examples or include_property:
            # check for the custom payload
            name_and_custom_payload_seq = None
            tab_seq = get_tab_indented_line_start(level)
            if p.payload:
                logger.write_to_main(f"p.payload={p.payload}", ConfigSetting().LogConfig.code_generate)
                # custom payload should not be quoted
                # Use the payload specified at this level.
                name_payload_seq = [format_property_name(p.name, "", True),
                                    # Because this is a custom payload for an object, it should not be quoted.
                                    get_restler_python_payload(p.payload, False)]
                name_and_custom_payload_seq = name_payload_seq

            if parameter_kind == ParameterKind.Body:
                return format_json_body_parameter(p.name, p.property_type, name_and_custom_payload_seq,
                                                  inner_properties,
                                                  level)
            elif parameter_kind == ParameterKind.Query:
                return format_nested_query_parameter(parameter_name, p.property_type, name_and_custom_payload_seq,
                                                     inner_properties, request_parameter)
            elif parameter_kind == ParameterKind.Header:
                return format_nested_header_parameter(parameter_name, p.property_type, name_and_custom_payload_seq,
                                                      inner_properties)
            elif parameter_kind == ParameterKind.Path:
                raise RuntimeError("Path parameters must not be formatted here.")
        else:
            return []

    payload_primitives = cata_ctx(f_leaf=visit_leaf, f_node=visit_inner, f_ctx=get_tree_level, ctx=0,
                                  tree=parameter_payload)
    logger.write_to_main(f"payload_primitives={payload_primitives}", ConfigSetting().LogConfig.code_generate)
    return payload_primitives


def generate_writer_statement(var):  # generateWriterStatement
    return f"{var}.writer()"


def generate_reader_statement(var):  # generateReaderStatement
    return f"{var}.reader()"


def generate_python_comment():
    pass


# quoteStringForPythonGrammar
def quote_string_for_python_grammar(s):
    if s is None:
        return ""
    if '\n' in s:
        return s, '"""'
    elif s.startswith('"'):
        # For grammar readability, a double-quoted string or single double quote
        # is enclosed in single quotes rather than escaped.
        # Escape single quotes
        if len(s) > 1:
            return s.replace("'", "\\'"), "'"
        else:
            return s, "'"
    # Special case already escaped quoted strings (this will be the case for example values).
    # Assume the entire string is quoted in this case.
    elif '\\\"' in s:
        return s, '"""'
    elif '"' in s:
        return s.replace('"', '\\"'), '"'
    else:
        return s, '"'


# getExamplePrimitiveParameter
def get_example_primitive_parameter(exv):
    if exv is None:
        return ""
    else:
        if exv == "None" or exv == {"Some": None}:
            return ", examples=[None]"
        else:
            from rest.compiler.swagger_visitor import SchemaUtilities
            exv = SchemaUtilities.format_example_value(exv)
            ex_str, ex_delim = quote_string_for_python_grammar(exv)
            quoted_str = f"{ex_delim}{ex_str}{ex_delim}"
            return f", examples=[{quoted_str}]"


# getTrackedParamPrimitiveParameter
def get_tracked_param_primitive_parameter(param_name):
    if ConfigSetting().TrackFuzzedParameterNames:
        if param_name is None:
            return ""
        else:
            ex_str, ex_delim = quote_string_for_python_grammar(param_name)
            quoted_str = f"{ex_delim}{ex_str}{ex_delim}"
            return f", param_name={quoted_str}"
    else:
        return ""


# formatDynamicObjectVariable
def format_dynamic_object_variable(dynamic_object):
    if dynamic_object is None:
        return ""
    else:
        if isinstance(dynamic_object, DynamicObjectWriter):
            return f", writer={dynamic_object.v}.writer()"


# Gets either the schema or examples payload present in the list
# getParameterPayload
def get_parameter_payload(query_or_body_parameters: list[tuple[ParameterPayloadSource, RequestParametersPayload]]) -> (
        tuple)[ParameterPayloadSource, list[RequestParametersPayload]]:
    payload_source = ParameterPayloadSource.Schema
    p_list = []
    for payload_source_, payload_value in query_or_body_parameters:
        if payload_source_ == ParameterPayloadSource.Examples or payload_source_ == ParameterPayloadSource.Schema \
                or payload_source_ == ParameterPayloadSource.DictionaryCustomPayload:
            payload_source = payload_source_
            p_list = payload_value
            break
    logger.write_to_main(f"p_list={p_list}", ConfigSetting().LogConfig.code_generate)
    return payload_source, p_list


# Merges all the dictionary custom payloads present in the list and returns them
# getCustomParameterPayload
def get_custom_parameter_payload(
        query_or_body_parameters: list[tuple[ParameterPayloadSource, RequestParametersPayload]]) -> (
        list)[RequestParametersPayload]:
    custom_payload = []
    for payload_source, p_list in query_or_body_parameters:
        if payload_source == ParameterPayloadSource.DictionaryCustomPayload:
            if isinstance(p_list, ParameterList):
                custom_payload.append(p_list)
    return custom_payload


# Gets the parameter list payload for query, header, or body parameters
# getParameterListPayload
def get_parameter_list_payload(parameters: list[tuple[ParameterPayloadSource, RequestParametersPayload]]) -> (
        tuple)[ParameterPayloadSource, ParameterList]:
    declared_payload_source, declared_payload = get_parameter_payload(parameters)
    logger.write_to_main(f"declared_payload={declared_payload} "
                         f"declared_payload_source={declared_payload_source}", ConfigSetting().LogConfig.code_generate)
    if isinstance(declared_payload, ParameterList):
        logger.write_to_main("parameters={}".format(type(declared_payload)), ConfigSetting().LogConfig.code_generate)
        injected_payload = get_custom_parameter_payload(parameters)
        return declared_payload_source, declared_payload


# getExamplePayload
def get_example_payload(query_or_body_parameters: list[tuple[ParameterPayloadSource, RequestParametersPayload]]) -> (
        Optional)[ParameterList]:
    example_payload = None
    for payload_source, payload_value in query_or_body_parameters:
        if payload_source == ParameterPayloadSource.DictionaryCustomPayload:
            if isinstance(payload_value, ParameterList):
                example_payload = payload_value
                break
    return example_payload


# getMergedStaticStringSeq
def get_merged_static_string_seq(str_list: list[str]):
    merged_string = "".join([s if s is not None else "null" for s in str_list])
    # Special handling is needed for the ending quote, because
    # it cannot appear in the last line of a triple-quoted Python multi-line string.
    # Example:
    #  Not valid: "id":"""");
    #  Transformed below to valid:
    #              "id":""");
    #     static_string('"');
    mapped_str = [
        "null" if s is None else s
        for s in str_list
    ]

    # Apply the mapi logic
    result = []
    for i, line in enumerate(mapped_str):
        if i < len(mapped_str) - 1 and line.startswith("\n") and str_list[i + 1].isspace():
            result.append("")  # Remove unnecessary lines
        else:
            result.append(line)

    # Concatenate the results into a single string
    merged_str = "".join(result)

    # Handle the special case where the string ends with a double quote
    if merged_str.endswith('"'):
        return [
            RequestPrimitiveType.static_string_constant(merged_str[:-1]),
            RequestPrimitiveType.static_string_constant('\"')
        ]
    else:
        return [RequestPrimitiveType.static_string_constant(merged_str)]


# Generates the python restler grammar definitions corresponding to the request
# generatePythonFromRequestElement
def generate_python_from_request_element(request_element,
                                         request_id: RequestId) -> [RequestPrimitiveType]:
    global len
    logger.write_to_main(f"request_element={request_element}", ConfigSetting().LogConfig.code_generate)
    if request_element[0] == RequestElementType.Method:
        return [RequestPrimitiveType.static_string_constant(value=f"{str(request_element[1]).upper()}{SPACE}")]
    elif request_element[0] == RequestElementType.BasePath:
        return [RequestPrimitiveType.basepath(request_element[1])]
    elif request_element[0] == RequestElementType.Path:
        value = request_element[1]
        logger.write_to_main(f"value={value}, type(value)={type(value)}", ConfigSetting().LogConfig.code_generate)
        if value is not None:
            query_start_index = len(
                value)  # todo \if requestId.xMsPath is None else value.index(Constant(PrimitiveType.String, "?"))
            # for item in value:
            result = []
            for payload_parts in value:
                result.append(get_restler_python_payload(payload_parts, False))

            # x = [RequestPrimitiveType.restler_static_string_constant("/") if not x or query_start_index == 0 else x]
            # if x and not x[0]:
            #    x = x[1:]
            logger.write_to_main(f"result = {result}", ConfigSetting().LogConfig.code_generate)
            return result
        else:
            return None

    elif request_element[0] == RequestElementType.HeaderParameters:
        if request_element[1]:
            filter_out = []
            for item in request_element[1]:
                logger.write_to_main(f"request_element[1]={type(request_element[1])},  item={item}",
                                     ConfigSetting().LogConfig.code_generate)
                for parameter_source, parameter_list in item:
                    if isinstance(parameter_list, ParameterList):
                        if parameter_list.request_parameters:
                            parameters = [
                                generate_python_parameter(parameter_source,
                                                          ParameterKind.Header,
                                                          request)
                                for request in parameter_list.request_parameters]
                            for primitives in parameters:
                                if primitives:
                                    filter_out = (filter_out + primitives +
                                                  [RequestPrimitiveType.static_string_constant(r"\r\n")])
                            logger.write_to_main("filter_out={}".format(filter_out),
                                                 ConfigSetting().LogConfig.code_generate)
                    else:
                        raise UnsupportedType(
                            f"This request parameters payload type is not supported: {request_element[0]}")
            return filter_out
        else:
            return []
    elif request_element[0] == RequestElementType.QueryParameters:
        if request_element[1]:
            parameter_source, parameter_list = request_element[1][0], request_element[1][1]
            if isinstance(parameter_list, ParameterList):
                parameters = []
                tail = len(parameter_list.request_parameters)
                query_start = 0
                for request in parameter_list.request_parameters:
                    current_parameter = generate_python_parameter(parameter_source, ParameterKind.Query, request)
                    if len(current_parameter) > 0:
                        if 0 < query_start < tail:
                            parameters = parameters + [RequestPrimitiveType.static_string_constant("&")]
                        parameters = parameters + current_parameter
                        query_start = 1

                if not parameters:
                    return []
                else:
                    # Special case: if the path of this request already contains a query (for example,
                    # if the endpoint source is from x-ms-paths), then append rather than start the query list
                    #
                    if request_id.xMsPath:
                        return [RequestPrimitiveType.static_string_constant("&")] + parameters
                    else:
                        return [RequestPrimitiveType.static_string_constant("?")] + parameters
            else:
                raise UnsupportedType(f"This request parameters payload type is not supported: {type(parameter_list)}")
        return []
    elif request_element[0] == RequestElementType.Body:
        logger.write_to_main(f"request_element[1]={request_element[1]}"
                             f"request_element[0]={request_element[0]}", ConfigSetting().LogConfig.code_generate)
        if request_element[1]:
            parameter_source, parameter_list = request_element[1][0], request_element[1][1]
            logger.write_to_main(f"parameter_list={parameter_list.__dict__()}", ConfigSetting().LogConfig.code_generate)
            if isinstance(parameter_list, ParameterList):
                parameters = []
                for request in parameter_list.request_parameters:
                    parameters = parameters + generate_python_parameter(parameter_source,
                                                                        ParameterKind.Body,
                                                                        request)
                # parameters = parameters + [RequestPrimitiveType.static_string_constant(r"\r\n")]
                logger.write_to_main(f"parameters={parameters}, "
                                     f"len(parameter_list.request_parameters)={len(parameter_list.request_parameters)}",
                                     ConfigSetting().LogConfig.code_generate)
                return parameters
            # todo
            # elif e == "Example" and isinstance(e.customBodyPayload, FuzzingPayload.Custom):
            #    return [Restler_static_string_constant(RETURN),
            #    *get_restler_python_payload(FuzzingPayload.Custom(e.customBodyPayload), False)]
            else:
                raise UnsupportedType(f"This request parameters payload type is not supported: {request_element[0]}")
        else:
            return []
    elif request_element[0] == RequestElementType.Token:
        return [RequestPrimitiveType.static_string_constant(f"{request_element[1]} {RETURN}")]
    elif request_element[0] == RequestElementType.RefreshableToken:
        return ([RequestPrimitiveType.refreshable_authentication_token("authentication_token_tag")] +
                [RequestPrimitiveType.static_string_constant(r"\r\n")])
    elif request_element[0] == RequestElementType.Headers:
        return [RequestPrimitiveType.static_string_constant(f"{name}: {content}" + r"\r\n")
                if content is not None else RequestPrimitiveType.static_string_constant(f"{name}: " + r"\r\n")
                for name, content in request_element[1] ]
    elif request_element[0] == RequestElementType.HttpVersion:
        string_value = f"{SPACE}HTTP/{request_element[1]}" + r"\r\n"
        return [RequestPrimitiveType.static_string_constant(value=string_value)]
    elif request_element[0] == RequestElementType.RequestDependencyDataItem:
        if request_element[1]:
            response_parser = request_element[1].response_parser
            if response_parser is not None:
                variables_referenced_in_parser = (response_parser.writer_variables +
                                                  response_parser.header_writer_variables)
            else:
                variables_referenced_in_parser = []

            parser_statement = ""
            if variables_referenced_in_parser:
                writer_variable = variables_referenced_in_parser[0]
                parser_statement = f"{NameGenerators.generate_producer_endpoint_response_parser_function_name(
                    writer_variable.request_id)},"

            # Post send preparation
            all_writer_variable_statements = []

            # Handle writer variables
            writer_variable_statements = [
                generate_writer_statement(DynamicObjectNaming.generate_dynamic_object_variable_name(
                    producer_writer.request_id, producer_writer.access_path_parts, "_"))
                for producer_writer in variables_referenced_in_parser
            ]
            all_writer_variable_statements.extend(writer_variable_statements)

            # Handle ordering constraint variables
            ordering_constraint_variable_statements = [
                generate_writer_statement(DynamicObjectNaming.generate_ordering_constraint_variable_name(
                    constraint_variable.source_request_id,
                    constraint_variable.target_request_id, "_"))
                for constraint_variable in request_element[1].ordering_constraint_writer_variables
            ]
            all_writer_variable_statements.extend(ordering_constraint_variable_statements)

            # Reader variables
            reader_variables_list = [
                generate_reader_statement(DynamicObjectNaming.generate_ordering_constraint_variable_name(
                    constraint_variable.source_request_id,
                    constraint_variable.target_request_id, "_"))
                for constraint_variable in request_element[1].ordering_constraint_reader_variables
            ]

            # Prepare output
            primitive_element = []
            if len(reader_variables_list) > 0 and len(all_writer_variable_statements) > 0:
                pre_send_element = """
        'pre_send':
        {
            'dependencies':
            [
                %s
            ]
        }
""" % "".join([' ' + stmt for stmt in reader_variables_list])
                if parser_statement != "":
                    post_send_element = """
        'post_send':
        {
            'parser': %s
            'dependencies':
            [
                %s
            ]
        }
    """ % (parser_statement, f",\n{SPACE_20}".join([stmt for stmt in all_writer_variable_statements]))
                else:
                    post_send_element = """
        'post_send':
        {
            
            'dependencies':
            [
                %s
            ]
        }
    """ % (f",\n{SPACE_20}".join([stmt for stmt in all_writer_variable_statements]))
                response_parser_element = """{
        %s,
        %s
    },\n""" % (pre_send_element, post_send_element)
                primitive_element = primitive_element + [RequestPrimitiveType.response_parser(response_parser_element)]
                logger.write_to_main(f"pre_send_element={pre_send_element}", ConfigSetting().LogConfig.code_generate)
            elif len(reader_variables_list) > 0 or len(all_writer_variable_statements) > 0:
                if len(reader_variables_list) > 0:
                    pre_send_element = """{
                
        'pre_send':
        {
            'dependencies':
            [
                %s
            ]
        }
        
    },
""" % "".join([' ' + stmt for stmt in reader_variables_list])
                    primitive_element = primitive_element + [RequestPrimitiveType.response_parser(pre_send_element)]
                    logger.write_to_main(f"pre_send_element={pre_send_element}", ConfigSetting().LogConfig.code_generate)
                if len(all_writer_variable_statements) > 0:
                    if parser_statement != "":
                        post_send_element = """{

        'post_send':
        {
            'parser': %s
            'dependencies':
            [
                %s
            ]
        }

    },
    """ % (parser_statement, f",\n{SPACE_20}".join([stmt for stmt in all_writer_variable_statements]))
                    else:
                        post_send_element = """{

        'post_send':
        {
            
            'dependencies':
            [
                %s
            ]
        }

    },
    """ % (f",\n{SPACE_20}".join([stmt for stmt in all_writer_variable_statements]))
                # post_send_element, _ = quote_string_for_python_grammar(post_send_element)
                # post_send_element = "".join([stmt for stmt in all_writer_variable_statements])
                    primitive_element = primitive_element + [RequestPrimitiveType.response_parser(post_send_element)]
                    logger.write_to_main(f"post_send_element={post_send_element}", ConfigSetting().LogConfig.code_generate)
            return primitive_element
        else:
            return []

    elif request_element[0] == RequestElementType.Delimiter:
        # string_value = r"\r\n"
        return [RequestPrimitiveType.delimiter()]
    else:
        return []


def get_dynamic_object_definitions(writer_variables: List[DynamicObjectWriterVariable]):
    return [NameGenerators.generate_dynamic_object_variable_definition(writer_variable.access_path_parts,
                                                                       writer_variable.request_id)

            for writer_variable in writer_variables
            ]


def get_ordering_constraint_dynamic_object_definitions(writer_variables: List[OrderingConstraintVariable]):
    return [NameGenerators.generate_dynamic_object_ordering_constraint_variable_definition(
        writer_variable.source_request_id, writer_variable.target_request_id)
        for writer_variable in writer_variables]


# generatePythonRequest
# Generates the python restler grammar definitions corresponding to the request
def generate_python_request(request: Request):
    definition = generate_python_from_request(request, True)
    logger.write_to_main("definition={}".format(definition), ConfigSetting().LogConfig.code_generate)
    format_str = ""
    for index, item in enumerate(definition):
        if isinstance(item, list):
            for item_list in item:
                raise Exception(f"Exception:{format_restler_primitive(item_list)}")
        str_value = format_restler_primitive(item)
        logger.write_to_main(f"str_value={str_value}", ConfigSetting().LogConfig.code_generate)
        if str_value:
            if item.type == RequestPrimitiveTypeEnum.Response_parser:
                format_str = format_str + 4 * f"{SPACE}" + f"{str_value}\n"
            elif item.type == RequestPrimitiveTypeEnum.Delimiter:
                format_str = format_str + f"{str_value}"
            else:
                format_str = format_str + 4 * f"{SPACE}" + f"{str_value},\n"
        logger.write_to_main(f"item={item} type(item)={type(item)} str_value={str_value}",
                             ConfigSetting().LogConfig.code_generate)
    definition = format_str

    request_id_comment = (f"# Endpoint: {request.id.endpoint}, "
                          f"method: {request.id.method.name}\n")
    grammar_request_id = f"requestId=\"{request.id.endpoint}\""

    assign_and_add = (request_id_comment +
                      "request = requests.Request([\n" +
                      definition +
                      "],\n" +
                      f"{grammar_request_id}\n)\n" +
                      "req_collection.add_request(request)\n")
    return assign_and_add


# getResponseParsers
def get_response_parsers(requests: List[Request]):
    random.seed(0)

    dependency_data = []
    response_parsers = []

    for request in requests:
        if request.dependencyData is not None:
            dependency_data.append(request.dependencyData)

    for dependency in dependency_data:
        if dependency.response_parser is not None:
            response_parsers.append(dependency.response_parser)

    # First, define the dynamic variables initialized by the response parser
    dynamic_objects_from_body = []
    dynamic_objects_from_headers = []
    dynamic_objects_from_input = []
    dynamic_objects_from_ordering_constraints = []
    dynamic_object_variables = []
    for rp in response_parsers:
        if len(rp.writer_variables) > 0:
            variables = get_dynamic_object_definitions(rp.writer_variables)

            for item in variables:
                if item is not None:
                    # fix issue: duplicate the dependencies issue
                    found = False
                    for definition, target_item in dynamic_objects_from_body:
                        if target_item == item:
                            found = True
                    if not found:
                        dynamic_objects_from_body.append((PythonGrammarElementType.DynamicObjectDefinition, item))
        if len(rp.header_writer_variables) > 0:
            variables = get_dynamic_object_definitions(rp.header_writer_variables)
            for item in variables:
                if item is not None:
                    dynamic_objects_from_headers.append((PythonGrammarElementType.DynamicObjectDefinition, item))

    for d in dependency_data:
        variables = get_ordering_constraint_dynamic_object_definitions(d.ordering_constraint_writer_variables)
        for item in variables:
            if item is not None:
                if item not in dynamic_object_variables:
                    dynamic_object_variables.append(item)
                    dynamic_objects_from_input.append((PythonGrammarElementType.DynamicObjectDefinition, item))
        variables = get_ordering_constraint_dynamic_object_definitions(d.ordering_constraint_reader_variables)
        for item in variables:
            if item is not None:
                if item not in dynamic_object_variables:
                    dynamic_object_variables.append(item)
                    dynamic_objects_from_ordering_constraints.append(
                        (PythonGrammarElementType.DynamicObjectDefinition, item))

    dynamic_objects_from_body = list(dynamic_objects_from_body)
    dynamic_objects_from_headers = list(dynamic_objects_from_headers)
    dynamic_objects_from_input = list(dynamic_objects_from_input)
    dynamic_objects_from_ordering_constraints = list(dynamic_objects_from_ordering_constraints)

    # Go through the producer fields and parse them all out of the response
    # STOPPED HERE:
    # also do 'if true' for header parsing and body parsing where 'true' is
    # if there are actually variables to parse out of there.
    def format_parser_function(parser, index_func):
        function_name = ""
        if len(parser.writer_variables) > 0:
            function_name = NameGenerators.generate_producer_endpoint_response_parser_function_name(
                parser.writer_variables[0].request_id)
        elif len(parser.header_writer_variables) > 0:
            function_name = NameGenerators.generate_producer_endpoint_response_parser_function_name(
                parser.header_writer_variables[0].request_id)

        # getResponseParsers
        def get_response_parsing_statements(writer_variables, variable_kind: DynamicObjectVariableKind):
            statements = []
            for index, w in enumerate(writer_variables):
                access_path = w.access_path_parts
                # dynamic_variable_name = f"{w.request_id.endpoint}_{'_'.join(access_path.path)}"  # todo
                dynamic_variable_name = DynamicObjectNaming.generate_dynamic_object_variable_name(
                    w.request_id, access_path, "_")
                temp_variable_name = f"temp_{random.randint(1000, 9999)}"
                empty_init_statement = f"{temp_variable_name} = None"
                parsing_statement = ""
                if variable_kind == DynamicObjectVariableKind.BodyResponsePropertyKind:
                    data_source = "data"
                    extract_data = "".join(
                        [f'["{part}"]' if not part.startswith("[") else "[0]" for part in access_path.path])
                    parsing_statement = f"{temp_variable_name} = str({data_source}{extract_data})"
                elif variable_kind == DynamicObjectVariableKind.HeaderKind:
                    data_source = access_path.path[-1]
                    extract_data = "".join(
                        [f'["{part}"]' if not part.startswith("[") else "[0]" for part in access_path.path[0:-1]])
                    parsing_statement = f"{temp_variable_name} = str(headers{extract_data})"

                init_check = f"if {temp_variable_name}:"
                init_statement = f"dependencies.set_variable(\"{dynamic_variable_name}\", {temp_variable_name})"

                boolean_conversion_statement = f"{temp_variable_name} = {temp_variable_name}.lower()" \
                    if hasattr(w, 'primitive_type') and w.primitive_type == PrimitiveType.Bool else None

                statements.append(
                    (empty_init_statement, parsing_statement, init_check, init_statement, temp_variable_name,
                     boolean_conversion_statement))
            return statements

        def parsing_statement_with_try_except(parsing_statement, boolean_conversion_statement):
            return f"""
        try:
            {parsing_statement}
            {boolean_conversion_statement or ""}
        except Exception as error:
            # This is not an error, since some properties are not always returned
            pass
        """

        response_body_parsing_statements = get_response_parsing_statements(
            parser.writer_variables, variable_kind=DynamicObjectVariableKind.BodyResponsePropertyKind)
        response_header_parsing_statements = get_response_parsing_statements(
            parser.header_writer_variables, variable_kind=DynamicObjectVariableKind.HeaderKind)

        body_parsing_statements = "\n".join(parsing_statement_with_try_except(ps[1], ps[5])
                                          for ps in response_body_parsing_statements)
        header_parsing_statements = "".join(parsing_statement_with_try_except(ps[1], ps[5])
                                              for ps in response_header_parsing_statements)

        if len(response_body_parsing_statements + response_header_parsing_statements) == 1:
            body_parser_info = "if not (" + ', '.join(
                ps[4] for ps in response_body_parsing_statements + response_header_parsing_statements) + "):"
        else:
            body_parser_info = "if not (" + ' or '.join(
                ps[4] for ps in response_body_parsing_statements + response_header_parsing_statements) + "):"

        header_parser_info = """
        
    if headers:
        # Try to extract dynamic objects from headers
        %s
        pass""" % header_parsing_statements

        data_parser_info = """
        try:
            data = json.loads(data)
        except Exception as error:
            raise ResponseParsingException("Exception parsing response, data was not valid json: {}".format(error))"""

        function_definition = f"""
def {function_name}(data, **kwargs):
    \"\"\" Automatically generated response parser \"\"\"
    # Declare response variables
    {'\n    '.join(ps[0] for ps in response_body_parsing_statements)}
    {'\n    '.join(ps[0] for ps in response_header_parsing_statements)}
    if 'headers' in kwargs:      
        headers = kwargs['headers']


    # Parse body if needed
    if data:
        {data_parser_info if len(response_body_parsing_statements) > 0 else ""}
        pass

    # Try to extract each dynamic object
        {body_parsing_statements if len(response_body_parsing_statements) > 0 else ""}
    {header_parser_info if len(response_header_parsing_statements) > 0 else ""}
    
    # If no dynamic objects were extracted, throw.
    {body_parser_info}
        raise ResponseParsingException("Error: all of the expected dynamic objects were not present in the response.")

    # Set dynamic variables
    {'\n    '.join(ps[2] + "\n        " + ps[3]
                   for ps in response_body_parsing_statements + response_header_parsing_statements)}\n"""
        if index > 0:
            function_definition = "\n" + function_definition
        return PythonGrammarElementType.ResponseParserDefinition, function_definition  # 返回创建的函数定义

    response_parsers_with_parser_function = [rp for rp in response_parsers
                                             if len(rp.writer_variables) + len(rp.header_writer_variables) > 0]

    result = (dynamic_objects_from_body + dynamic_objects_from_headers + dynamic_objects_from_input +
              dynamic_objects_from_ordering_constraints)

    for index, rp in enumerate(response_parsers_with_parser_function):
        result = result + [format_parser_function(rp, index)]

    return result


# getRequests
def get_requests(requests: list[Request]) -> str:
    generated_requests_str = ""
    for index, request in enumerate(requests):
        print(f"Generated Grammar Python:{request.id.endpoint}")
        generated_requests_str = generated_requests_str + generate_python_request(request)
        if index < len(requests) - 1:
            generated_requests_str = generated_requests_str + "\n"

    return generated_requests_str


# generatePythonFromRequest
# Generates the python restler grammar definitions corresponding to the request
def generate_python_from_request(request: Request, merge_static_strings):
    """
    Generate Python code for a given request.
    Args:
        request (Request): The request to process.
        merge_static_strings (bool): Whether to merge static strings in the body.

    Returns:
        list: A list of Python representations for the request.
    """

    request_header_elements = []

    for i, item in enumerate(request.headerParameters):
        return_value = get_parameter_list_payload(item)
        if return_value is not None:
            request_header_elements.append([return_value])

    # Gets either the schema or examples payload present in the list
    def process_request(body_parameters) -> Tuple[ParameterPayloadSource, Union[ParameterList, Example]]:
        payload_source, parameter_list_payload = get_parameter_list_payload(body_parameters)
        example_payload = get_example_payload(body_parameters)

        if example_payload is not None:
            return payload_source, example_payload
        else:
            return payload_source, parameter_list_payload

    logger.write_to_main(f"request_header_elements={request_header_elements}", ConfigSetting().LogConfig.code_generate)
    """
        
        """
    request_elements = [
        [RequestElementType.Method, request.method.name],
        [RequestElementType.BasePath, request.basePath],
        [RequestElementType.Path, request.path],
        [RequestElementType.QueryParameters, get_parameter_list_payload(request.queryParameters)],
        [RequestElementType.HttpVersion, request.httpVersion],
        [RequestElementType.Headers, request.headers],
        [RequestElementType.HeaderParameters, request_header_elements],
        [RequestElementType.RefreshableToken, None
        if request.token == TokenKind.Refreshable else RequestElementType.Token, Token(request.token)
         if request.token == TokenKind.Static else None, ''],
        [RequestElementType.Body, process_request(request.bodyParameters) if request.bodyParameters else None],
        [RequestElementType.Delimiter, None],
        [RequestElementType.RequestDependencyDataItem, request.dependencyData]
    ]

    result = []
    # Process request elements
    processed_elements = []

    for request_element in request_elements:
        primitives = generate_python_from_request_element(request_element, request.id)
        logger.write_to_main(f"request_element={len(request_element)}", ConfigSetting().LogConfig.code_generate)

        if request_element[0] == RequestElementType.Body and merge_static_strings and len(primitives) > 1:
            filtered_primitives = [
                p
                for p in primitives
                if not (p.type == RequestPrimitiveTypeEnum.Restler_static_string_jtoken_delim and
                        not p.primitive_data.default_value) and
                   not (p.type == RequestPrimitiveTypeEnum.Restler_static_string_constant and
                        (p.primitive_data.default_value is None or not p.primitive_data.default_value.strip()))
            ]

            new_primitive_seq = []
            next_list = []

            for primitive in filtered_primitives[1:]:
                if primitive.type == RequestPrimitiveTypeEnum.Restler_static_string_constant:
                    next_list.append(primitive.primitive_data.default_value)
                else:
                    if next_list:
                        new_primitive_seq.extend(get_merged_static_string_seq(next_list))
                        next_list = []
                    new_primitive_seq.append(primitive)

            if next_list:
                new_primitive_seq.extend(get_merged_static_string_seq(next_list))

            processed_elements.extend(filtered_primitives[:1] + new_primitive_seq)
            processed_elements.append(RequestPrimitiveType.static_string_constant(r"\r\n"))
        else:
            processed_elements.extend(primitives)

    return processed_elements


# list of string todo

# The definitions required for the RESTler python grammar.
# Note: the purpose of this type is to aid in generating the grammar file.
# This is not intended to be able to represent arbitrary python.
class PythonGrammarElementType(enum.Enum):
    # Definition of a python import statement
    # from <A> import <B>
    Import = 0,

    # Definitions of the dynamic objects
    # _api_blog_posts_id = dependencies.DynamicVariable("_api_blog_posts_id")
    DynamicObjectDefinition = 1,
    # The response parsing functions
    ResponseParserDefinition = 2,
    # Definition of the request collection
    RequestCollectionDefinition = 3,
    # Requests that will be fuzzed
    Requests = 4,
    # Comment
    Comment = 5,


Unsupported = 6


class PythonGrammarElement:

    @staticmethod
    def import_func(from_str, import_str):
        return PythonGrammarElementType.Import, (from_str, import_str)

    @staticmethod
    def comment_func(comment_str):
        return PythonGrammarElementType.Comment, comment_str

    @staticmethod
    def request_collection_definition_func(def_str):
        return PythonGrammarElementType.RequestCollectionDefinition, def_str

    @staticmethod
    def requests_func(requests_str: str):
        return PythonGrammarElementType.Requests, requests_str

    @staticmethod
    def dynamic_object_fun(dynamic: str):
        return PythonGrammarElementType.DynamicObjectDefinition, dynamic


def generate_python_grammar(grammar_definition: GrammarDefinition):
    import_statements = [PythonGrammarElement.import_func("__future__", "print_function\n"),
                         PythonGrammarElement.import_func(None, "json\n"),
                         PythonGrammarElement.import_func("rest.restler.engine", "primitives\n"),
                         PythonGrammarElement.import_func("rest.restler.engine.core", "requests\n"),
                         PythonGrammarElement.import_func("rest.restler.engine.errors", "ResponseParsingException\n"),
                         PythonGrammarElement.import_func("rest.restler.engine", "dependencies\n")
                         ]

    response_parsers = get_response_parsers(grammar_definition.Requests)

    requests = get_requests(grammar_definition.Requests)
    requests_list = PythonGrammarElement.requests_func(requests)
    logger.write_to_main(f"result={requests_list}, type(result)={requests_list}",
                         ConfigSetting().LogConfig.code_generate)
    result = (([PythonGrammarElement.comment_func("\"\"\" THIS IS AN AUTOMATICALLY GENERATED FILE!\"\"\"\n"),
                *import_statements]) + response_parsers +
              [PythonGrammarElement.request_collection_definition_func(
                  "req_collection = requests.RequestCollection([])\n")]
              + [requests_list])
    return result


def code_gen_element(element):
    if element[0] == PythonGrammarElementType.Comment:
        return element[1]
    elif element[0] == PythonGrammarElementType.Import:
        import_source = element[1][0]
        import_target = element[1][1]
        from_import = f"from {import_source} " if import_source else ""
        return f"{from_import}import {import_target}"
    elif element[0] == PythonGrammarElementType.DynamicObjectDefinition:
        return "\n" + element[1]
    elif element[0] == PythonGrammarElementType.RequestCollectionDefinition:
        return "\n" + element[1]
    elif element[0] == PythonGrammarElementType.ResponseParserDefinition:
        return element[1]
    elif element[0] == PythonGrammarElementType.Requests:
        logger.write_to_main(f"element[1]={element[1]}", ConfigSetting().LogConfig.code_generate)
        return element[1]


def generate_code(grammar_definition: GrammarDefinition, write_function):
    grammar = generate_python_grammar(grammar_definition)
    logger.write_to_main(f"grammar={grammar}, type(grammar)={type(grammar)}", ConfigSetting().LogConfig.code_generate)
    for i, element in enumerate(grammar):
        code_element = code_gen_element(element)
        logger.write_to_main(f"code_element={code_element}, type(code_element)={type(code_element)}",
                             ConfigSetting().LogConfig.code_generate)
        write_function(code_element)
        """
        if i == (len(grammar)):
            write_function(code_element)
        else:
            write_function(code_element + "\n")
        """


def generate_custom_value_gen_template(dictionary_text):
    imports = ["typing", "random", "time", "string", "itertools"]
    constants = """
EXAMPLE_ARG = "examples"
    """

    dictionary_json = json.loads(dictionary_text)
    dictionary_lines = []
    function_names = []

    dictionary_lines.append("value_generators = {")
    for name, value in dictionary_json.items():
        if '_fuzzable_' in name:
            function_name = "gen_" + name
            referenced_function = function_name if name == "restler_fuzzable_string" else "None"
            dictionary_lines.append(f"\t\"{name}\": {referenced_function},")
            function_names.append(function_name)
        elif '_custom_payload' in name and 'suffix' not in name:
            dictionary_lines.append(f"\t\"{name}\": {{")

            custom_payloads = value
            if custom_payloads is not None:
                # todo checking for not none if it is an real issues
                for cp in custom_payloads:
                    function_name = "gen_" + name + "_" + cp
                    dictionary_lines.append(f"\t\t\"{cp}\": \"None\",")
                    function_names.append(function_name)

            dictionary_lines.append("\t},")

    dictionary_lines.append("}")
    dictionary_text = "\n".join(dictionary_lines)

    function_names.remove("gen_restler_fuzzable_string")

    sample_function = """
def gen_restler_fuzzable_string(**kwargs):
    example_values=None
    if EXAMPLE_ARG in kwargs:
        example_values = kwargs[EXAMPLE_ARG]

    if example_values:
        for exv in example_values:
            yield exv
        example_values = itertools.cycle(example_values)

    i = 0
    while True:
        i = i + 1
        size = random.randint(i, i + 10)
        if example_values:
            ex = next(example_values)
            ex_k = random.randint(1, len(ex) - 1)
            new_values=''.join(random.choices(ex, k=ex_k))
            yield ex[:ex_k] + new_values + ex[ex_k:]

        yield ''.join(random.choices(string.ascii_letters + string.digits, k=size))
        yield ''.join(random.choices(string.printable, k=size)).replace("\\r\\n", "")

def placeholder_value_generator():
    while True:
        yield str(random.randint(-10, 10))
        yield ''.join(random.choices(string.ascii_letters + string.digits, k=1))
    """

    def get_function_text(function_name_text):
        return f"""
def {function_name_text}(**kwargs):
    example_value=None
    if EXAMPLE_ARG in kwargs:
        example_value = kwargs[EXAMPLE_ARG]

    # Add logic here to generate values
    return placeholder_value_generator()
    """ + "\n"

    function_definitions = [get_function_text(function_name) for function_name in function_names]

    result = []
    for i in imports:
        result.append(f"import {i}\n")

    result.append("random_seed=time.time()\n")
    result.append(f"""print(f"Value generator random seed: {" + ""random_seed"" + "}")""" + "\n")
    result.append("random.seed(random_seed)\n")
    result.append(constants)

    result.append(sample_function)
    result.append(function_definitions)
    result.append(dictionary_text)

    return result
