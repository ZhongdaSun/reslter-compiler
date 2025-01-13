# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Generates the fuzzing grammar required for the main RESTler algorithm
# Note: the grammar should be self-contained, i.e. using it should not require the Swagger
# definition for further analysis or to generate code.
# This module should not implement any code generation to the target language (currently python); code
# generation logic should go into separate modules and take the grammar as a parameter.
from typing import List, Dict, Optional
from collections import defaultdict
import os
import shutil

from compiler.config import ConfigSetting
from compiler.swagger import SwaggerDoc
from compiler.access_paths import AccessPath
from compiler.grammar import (
    OperationMethod,
    DynamicObjectVariableKind,
    PrimitiveType,
    ParameterPayloadSource,
    RequestParameter,
    SupportedOperationMethods,
    GrammarDefinition,
    RequestId,
    OrderingConstraintVariable,
    Request,
    RequestParameterList,
    Example,
    ResponseInfo,
    ParameterKind,
    LeafProperty,
    InnerProperty,
    InternalNode,
    NestedType,
    LeafNode,
    Fuzzable,
    ParameterSerialization,
    StyleKind,
    PrimitiveTypeEnum,
    ParameterList,
    CustomPayloadType,
    RequestDependencyData,
    RequestParameters,
    CustomPayload,
    ProducerConsumerAnnotation,
    FuzzingPayload,
    Constant,
    RequestMetadata,
    TokenKind,
    get_primitive_type_from_string,
    ResponseParser,
    DynamicObjectWriterVariable)
from compiler.annotations import (
    get_annotations_from_json,
    GlobalAnnotationKey)
from compiler.apiresource import (
    Producer,
    ResponseProducer,
    InputParameter,
    ProducerConsumerDependency,
    HeaderResource)
from compiler.dependency_analysis_types import (
    get_path_from_string,
    PathPartType,
    try_get_path_parameter_name,
    format_path_parameter,
    parameter_names_equal,
    RequestData,
    is_path_parameter)
from compiler.swagger_visitor import (
    SchemaUtilities,
    SchemaCache,
    generate_grammar_element_for_schema)
from compiler.swagger import RequestInfo
from compiler.dictionary import (
    MutationsDictionary,
    DictionarySetting,
    get_request_type_payload_prefix,
    get_request_type_payload_name)

from compiler.example import (
    FileExamplePayload,
    ExamplePath,
    get_example_config,
    ExampleConfigFile,
    ExampleMethod,
    ExampleRequestPayload)
from compiler.xms_paths import (
    XMsPath,
    get_x_ms_path)
from compiler.dependencies import (
    DependencyLookup,
    extract_dependencies)
from swagger.objects import Parameter

from restler.utils import restler_logger as logger


class UnsupportedParameterSerialization(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class UnsupportedType(Exception):
    def __init__(self, msg):
        super().__init__(msg)


# A configuration associated with a single Swagger document
class ApiSpecFuzzingConfig:
    swaggerDoc: SwaggerDoc

    dictionary: MutationsDictionary

    globalAnnotations: list[ProducerConsumerAnnotation]

    xMsPathsMapping: Optional[Dict[str, str]]


# Define UserSpecifiedRequestConfig type
# Configuration allowed on a per-request basis
class UserSpecifiedRequestConfig:
    def __init__(self, dictionary=None, annotations=None):
        # Per-request dictionaries are only allowed to contain values in the custom payload section.
        self.dictionary = dictionary
        self.annotations = annotations


ValidResponseCodes = [200, 201, 202, 203, 204, 205, 206, 207]

ReaderMethods = [OperationMethod.Get, OperationMethod.Trace, OperationMethod.Head, OperationMethod.Options]


# getWriterVariable
# Generate the parser for all the consumer variables (Note this means we need both producer
# and consumer pairs.  A response parser is only generated if there is a consumer for one or more of the
# response properties.)

# Make sure the grammar will be stable by sorting the variables.
def get_writer_variable(producer: Producer,
                        kind: DynamicObjectVariableKind) -> DynamicObjectWriterVariable:
    if isinstance(producer, InputParameter):
        input_parameter = producer
        access_path_parts = input_parameter.input_only_producer.get_input_parameter_access_path()
        primitive_type = producer.input_only_producer.parameter_kind
        request_id = producer.input_only_producer.request_id
    elif isinstance(producer, ResponseProducer):
        rp = producer
        if isinstance(producer.resource_reference, HeaderResource):
            access_path_parts = AccessPath([rp.resource_reference, "header"])  # handle ambiguity with body
        else:
            access_path_parts = rp.access_path_parts
        primitive_type = rp.primitive_type
        request_id = rp.request_id
    else:
        raise ValueError("Only input parameter and response producers have an associated dynamic object")

    return DynamicObjectWriterVariable(request_id=request_id,
                                       access_path_parts=access_path_parts,
                                       primitive_type=primitive_type,
                                       kind=kind)


# Generate the parser for all the consumer variables (Note this means we need both producer
# and consumer pairs.  A response parser is only generated if there is a consumer for one or more of the
# response properties.)

# Make sure the grammar will be stable by sorting the variables.
# getVariables
def get_variables(variable_map, variable_kind):
    variables = variable_map.get(variable_kind, [])
    return sorted(variables, key=lambda writer_variable: (writer_variable.request_id.endpoint,
                                                          writer_variable.request_id.method,
                                                          writer_variable.access_path_parts.get_json_pointer()))


# getOrderingConstraintVariables
def get_ordering_constraint_variables(constraints) -> list[OrderingConstraintVariable]:
    ordering_constraint_list = []
    for source, target in constraints:
        order = OrderingConstraintVariable(source_request_id=source, target_request_id=target)
        ordering_constraint_list.append(order)
    return ordering_constraint_list


# getResponseParsers
def get_response_parsers(dependencies: List[ProducerConsumerDependency],
                         ordering_constraints: List[OrderingConstraintVariable]):
    # Step 1: Index the dependencies by request ID
    parsers = {}
    variable_map = {}
    # First, add all the requests for which an ordering constraint exists
    # Step 2: Add all requests for which an ordering constraint exists
    for source, target in ordering_constraints:
        parsers[source.request_id.hex_hash] = RequestDependencyData(None,
                                                                    [],
                                                                    [],
                                                                    [])
        parsers[target.request_id.hex_hash] = RequestDependencyData(None,
                                                                    [],
                                                                    [],
                                                                    [])
        parsers[source.request_id.hex_hash].ordering_constraint_writer_variables = get_ordering_constraint_variables(
            list(filter(lambda x: x[0] == source, ordering_constraints)))
        parsers[source.request_id.hex_hash].ordering_constraint_reader_variables = get_ordering_constraint_variables(
            list(filter(lambda x: x[1] == target, ordering_constraints)))

    # Step 3: Process dependencies with producers
    for dep in dependencies:
        if dep.producer:
            logger.write_to_main(f"dep.consumer={dep.consumer.__dict__()}", ConfigSetting().LogConfig.compiler)
            logger.write_to_main(f"dep.producer={dep.producer.__dict__()}", ConfigSetting().LogConfig.compiler)
            writer_variable_kind = None
            producer_value = dep.producer
            if isinstance(producer_value, ResponseProducer):
                # Assuming ResponseObject has an 'id' attribute with 'ResourceReference'
                if isinstance(producer_value.resource_reference, HeaderResource):
                    writer_variable_kind = DynamicObjectVariableKind.HeaderKind
                else:
                    writer_variable_kind = DynamicObjectVariableKind.BodyResponsePropertyKind
            elif isinstance(producer_value, InputParameter):
                writer_variable_kind = DynamicObjectVariableKind.InputParameterKind

            if writer_variable_kind:
                writer_variable = get_writer_variable(dep.producer, writer_variable_kind)
                variable_map.setdefault(writer_variable_kind, []).append(writer_variable)
                logger.write_to_main(f"variable_map={variable_map}", ConfigSetting().LogConfig.compiler)
    if not ConfigSetting().LogConfig.compiler:
        for key, value in variable_map.items():
            for item in value:
                logger.write_to_main(f"item={item.__dict__()}", ConfigSetting().LogConfig.compiler)
    # Step 4: Remove duplicates and group by requestId
    grouped_writer_variables = {}
    for keys in variable_map.keys():
        var = variable_map[keys]
        for writer_variable in var:
            logger.write_to_main(f"writer_variable={writer_variable.__dict__()}",
                                 ConfigSetting().LogConfig.compiler)
            if writer_variable.request_id.hex_hash not in grouped_writer_variables.keys():
                # fixed issue with two duplicated write variable
                grouped_writer_variables.setdefault(writer_variable.request_id.hex_hash, []).append(writer_variable)
            else:
                write_info = grouped_writer_variables.get(writer_variable.request_id.hex_hash)
                found = False
                for write_item in write_info:
                    if writer_variable.__eq__(write_item):
                        found = True
                        break
                if not found:
                    grouped_writer_variables[writer_variable.request_id.hex_hash].append(writer_variable)
                logger.write_to_main(f"grouped_writer_variables="
                                     f"{len(grouped_writer_variables[writer_variable.request_id.hex_hash])}",
                                     ConfigSetting().LogConfig.compiler)
    # Step 5: Create parsers for each unique requestId
    for request_id, all_writer_variables in grouped_writer_variables.items():
        logger.write_to_main(f"request_id={request_id}", ConfigSetting().LogConfig.compiler)
        prev_dependency_info = parsers.get(request_id, None)

        local_grouped_writer_variables = {}
        for x in all_writer_variables:
            logger.write_to_main(f"x={x.__dict__()}", ConfigSetting().LogConfig.compiler)
            local_grouped_writer_variables.setdefault(x.kind, []).append(x)

        response_variable = get_variables(variable_map=local_grouped_writer_variables,
                                          variable_kind=DynamicObjectVariableKind.BodyResponsePropertyKind)
        header_variable = get_variables(variable_map=local_grouped_writer_variables,
                                        variable_kind=DynamicObjectVariableKind.HeaderKind)
        response_parser = ResponseParser(writer_variables=response_variable,
                                         header_writer_variables=header_variable)

        input_variable = get_variables(variable_map=local_grouped_writer_variables,
                                       variable_kind=DynamicObjectVariableKind.InputParameterKind)

        dependency_info = RequestDependencyData(
            response_parser=response_parser,
            input_writer_variables=input_variable,
            ordering_constraint_writer_variables=prev_dependency_info.ordering_constraint_writer_variables
            if prev_dependency_info else [],
            ordering_constraint_reader_variables=prev_dependency_info.ordering_constraint_reader_variables
            if prev_dependency_info else [])

        if request_id in parsers.keys():
            parsers.pop(request_id)

        parsers[request_id] = dependency_info

    return parsers


class ResourceUriInferenceFromExample:

    @staticmethod
    def try_get_example_payload(payload: FuzzingPayload):
        if isinstance(payload, Constant):
            if isinstance(payload.primitive_type, str):
                # TODO: when this supports fuzzable strings as a constant, add
                # FuzzingPayload.Fuzzable x -> Some x
                return payload.variable_name.strip()
        return None

    # Note: this method is not currently used.  It is left here in case the URI format of resources
    # turns out to be inconsistent and cannot be inferred via the general mechanism below.
    # (* Usage:Some exValue when exValue.StartsWith("/") && Uri.IsWellFormedUriString(exValue, UriKind.Relative) ->
    # match tryGetUriIdPayloadFromExampleValue requestId exValue endpointPayload with
    # | None -> defaultPayload
    # | Some p -> p
    # *)
    @staticmethod
    def try_get_uri_id_payload_from_example_value(request_id: RequestId, ex_value: str, endpoint_payload):
        consumer_endpoint_parts = request_id.endpoint.split("/")
        example_parts = ex_value.split("/")

        def is_child(parent_path_parts, child_path_parts):
            if not parent_path_parts:
                return True, child_path_parts
            if child_path_parts and (
                    parent_path_parts[0].startswith("{") or parent_path_parts[0] == child_path_parts[0]):
                return is_child(parent_path_parts[1:], child_path_parts[1:])
            return False, None

        is_child, child_parts = is_child(consumer_endpoint_parts, example_parts)

        if is_child:
            child_payload = ["Constant", ["String", f"/{('/'.join(child_parts))}"]]
            pp = sum([[["Constant", ["String", "/"]], x] for x in endpoint_payload], [])
            return ["PayloadParts", pp + [child_payload]]
        else:
            print(f"WARNING: found external resource id, this needs to be pre-provisioned: {ex_value}")
            return None


class Parameters:
    # getParameterSerialization
    @staticmethod
    def get_parameter_serialization(p: Parameter):
        parameter_serialization = ParameterSerialization(style=StyleKind.Simple, explode=False, has_setting=False)
        if p.is_set("style") and p.is_set("explode"):
            parameter_serialization.has_setting = True

        style = SchemaUtilities.get_property(p, "style")
        explode = SchemaUtilities.get_property(p, "explode")
        if style is not None:
            if style.lower() == "form":
                parameter_serialization.style = StyleKind.Form
                parameter_serialization.explode = explode
            elif style.lower() == "simple":
                parameter_serialization.style = StyleKind.Simple
                parameter_serialization.explode = explode
            elif style.lower() == "undefined":
                parameter_serialization = None
            elif style.lower() == "":
                pass
            else:
                raise Exception(f"Unsupported Parameter Serialization: {style}")
        return parameter_serialization

    # Determine whether a parameter is declared as 'readOnly'
    # 'isReadOnly' is not exposed in NJsonSchema.  Instead, it appears
    # in ExtensionData
    # OPEN API 3.0
    """"
    @staticmethod
    def parameter_is_readonly(parameter):
        if isinstance(parameter, Parameter):
            schema = getattr(parameter, parameter.get_private_name("schema")) if parameter.is_set("schema") else None
            if schema is not None and isinstance(schema, Schema):
                return bool(getattr(schema, schema.get_private_name("readOnly"))) if parameter.is_set(
                    "readOnly") else False
            else:
                return False
        else:
            return False
    """

    @staticmethod
    def get_path_parameter_payload(payload):
        if isinstance(payload, LeafNode):
            logger.write_to_main(f"type(payload.payload={type(payload.leaf_property.payload)}",
                                 ConfigSetting().LogConfig.compiler)
            return payload.leaf_property.payload
        else:
            raise UnsupportedType("Complex path parameters are not supported")

    # Given an example payload, go through the list of declared parameters and only retain the
    # ones that are declared in the example.
    # At the end, print some diagnostic information about which parameters in the example were
    # not found in the specification.
    @staticmethod
    def get_parameters_from_example(swagger_doc: SwaggerDoc,
                                    example_payload: ExampleRequestPayload,
                                    parameter: Parameter,
                                    schema_cache):
        body_name = "__body__"
        parameter_name = SchemaUtilities.get_property(parameter, "name")
        parameter_in = SchemaUtilities.get_property(parameter, "in")
        parameter_type = SchemaUtilities.get_property(parameter, "type")
        is_required = SchemaUtilities.get_property(parameter, "required")
        found_parameter = None

        for r in example_payload.parameter_examples:
            if r.parameter_name == parameter_name:
                found_parameter = r
                break

        if found_parameter is None and parameter_in.lower() == ParameterKind.Body.name.lower():
            for r in example_payload.parameter_examples:
                if r.parameter_name == body_name:
                    found_parameter = r
                    break

        if found_parameter is not None:
            payload_value = found_parameter.payload

            if example_payload.exact_copy:
                if parameter_in == ParameterKind.Body.name.lower():
                    primitive_type = PrimitiveType.Object
                else:
                    if parameter_type in ['array', 'object']:
                        primitive_type = PrimitiveType.Object
                    else:
                        primitive_type = get_primitive_type_from_string(parameter_type)

                formatted_payload_value = SchemaUtilities.format_example_value(payload_value)
                constant_payload = Constant(primitive_type=primitive_type,
                                            variable_name=formatted_payload_value)

                payload = LeafNode(LeafProperty(name="",
                                                payload=constant_payload,
                                                is_readonly=SchemaUtilities.get_property_read_only(parameter),
                                                is_required=is_required))

            else:
                payload = generate_grammar_element_for_schema(
                    swagger_doc=swagger_doc,
                    schema=parameter,
                    example_value=payload_value,
                    generate_fuzzable_payloads_for_examples=True,
                    track_parameters=ConfigSetting().TrackFuzzedParameterNames,
                    is_required=is_required,
                    parents=[],
                    schema_cache=schema_cache,
                    cont=None)

            return RequestParameter(name=parameter_name,
                                    payload=payload,
                                    serialization=Parameters.get_parameter_serialization(parameter))

    @staticmethod
    def get_spec_parameters(swagger_method_definition, parameter_kind):
        def get_shared_parameters(parameters, parameter_kind):
            if not parameters:
                return []
            return [p for p in parameters if p["Kind"] == parameter_kind]

        local_parameters = [p for p in swagger_method_definition["ActualParameters"] if p["Kind"] == parameter_kind]
        declared_shared_parameters = get_shared_parameters(swagger_method_definition["Parent"]["Parameters"],
                                                           parameter_kind)
        declared_global_parameters = []
        if parameter_kind == "Path":
            if (swagger_method_definition["Parent"]["Parent"] and
                    swagger_method_definition["Parent"]["Parent"]["Parameters"]):
                global_parameter_collection = [v for k, v in
                                               swagger_method_definition["Parent"]["Parent"]["Parameters"].items()
                                               if v["IsRequired"]]
                declared_global_parameters = get_shared_parameters(global_parameter_collection, parameter_kind)

        all_parameters = local_parameters + declared_shared_parameters + declared_global_parameters
        all_parameters = list({p["Name"]: p for p in all_parameters}.values())
        return all_parameters

    # pathParameters
    @staticmethod
    def path_parameters(swagger_doc,
                        swagger_method_definition: RequestInfo,
                        endpoint,
                        example_config,
                        schema_cache) -> ParameterList:
        logger.write_to_main(f"{swagger_method_definition.__str__()}", ConfigSetting().LogConfig.compiler)
        all_declared_path_parameters = swagger_method_definition.path
        logger.write_to_main(f"path_parameter={all_declared_path_parameters}, type={len(all_declared_path_parameters)}",
                             ConfigSetting().LogConfig.compiler)
        if all_declared_path_parameters is None or len(all_declared_path_parameters) == 0:
            return ParameterList(request_parameters=None)

        path = get_path_from_string(endpoint, False)
        logger.write_to_main(f"path={path}", ConfigSetting().LogConfig.compiler)
        parameter_list = []
        for parameter in all_declared_path_parameters:
            logger.write_to_main(f"parameters={parameter.name}, schema={parameter.schema}"
                                 f"path.contains_parameter(parameter.name)="
                                 f"{path.contains_parameter(parameter.name)}", ConfigSetting().LogConfig.compiler)
            if path.contains_parameter(parameter.name):
                parameter_value_from_example = None

                if example_config and example_config[0]:
                    parameter_value_from_example = Parameters.get_parameters_from_example(
                        swagger_doc,
                        example_config[0],
                        parameter,
                        schema_cache)

                if parameter_value_from_example:
                    swagger_method_definition.request_id.has_example = True
                    parameter_list.append(parameter_value_from_example)
                else:
                    if parameter.type == "array":
                        raise Exception("Arrays in path examples are not supported yet.")
                    else:
                        spec_example_value = SchemaUtilities.try_get_schema_example_value(parameter)
                        logger.write_to_main(f"spec_example_value={spec_example_value}",
                                             ConfigSetting().LogConfig.compiler)
                        property_payload = generate_grammar_element_for_schema(
                            swagger_doc=swagger_doc,
                            schema=parameter,
                            example_value=spec_example_value,
                            generate_fuzzable_payloads_for_examples=True,
                            track_parameters=ConfigSetting().TrackFuzzedParameterNames,
                            is_required=True,
                            parents=[],
                            schema_cache=schema_cache,
                            cont=id)
                        logger.write_to_main(f"property_payload={property_payload.__dict__()}",
                                             ConfigSetting().LogConfig.compiler)
                        if property_payload is not None:
                            if isinstance(property_payload, LeafNode):
                                fp = property_payload.leaf_property.payload
                                serial = Parameters.get_parameter_serialization(parameter)
                                if isinstance(fp, Fuzzable):
                                    if parameter.is_set("enum"):
                                        logger.write_to_main(f"fp={type(fp)}", ConfigSetting().LogConfig.compiler)
                                        primitive_type = PrimitiveTypeEnum(name=parameter.name,
                                                                           primitive_type=PrimitiveType.String,
                                                                           value=[fp.example_value],
                                                                           default_value=fp.default_value)
                                        fp.primitive_type = primitive_type
                                        fp.name = parameter.name if ConfigSetting().TrackFuzzedParameterNames else None
                                        leaf_property = LeafProperty(name=fp.name, payload=fp,
                                                                     is_required=True,
                                                                     is_readonly=False)
                                        leaf_node = LeafNode(leaf_property=leaf_property)
                                        request_parameters = RequestParameter(name=parameter.name,
                                                                              payload=leaf_node,
                                                                              serialization=serial)
                                        parameter_list.append(request_parameters)
                                    else:
                                        logger.write_to_main(f"property_payload={property_payload.__dict__()}",
                                                             ConfigSetting().LogConfig.compiler)
                                        request_parameters = RequestParameter(name=parameter.name,
                                                                              payload=property_payload,
                                                                              serialization=serial)
                                        parameter_list.append(request_parameters)
                            else:
                                raise Exception("Path parameters with nested object types are not supported")

        parameter_lists = ParameterList(parameter_list)
        logger.write_to_main(f"len(parameter_lists)={parameter_lists}", ConfigSetting().LogConfig.compiler)
        return parameter_lists

    @staticmethod
    def get_parameters(swagger_doc: SwaggerDoc,
                       swagger_method_definition: RequestInfo,
                       parameter_list: list[Parameter],
                       example_config,
                       schema_cache: SchemaCache) -> RequestParameterList:

        def generate_parameter_payload(parameter: Parameter):
            parameter_name = SchemaUtilities.get_property(parameter, "name")

            parameter_payload = generate_grammar_element_for_schema(
                swagger_doc=swagger_doc,
                schema=parameter,
                example_value=None,
                generate_fuzzable_payloads_for_examples=False,
                track_parameters=ConfigSetting().TrackFuzzedParameterNames,
                is_required=SchemaUtilities.get_property(parameter, "required"),
                parents=[],
                schema_cache=schema_cache,
                cont=None)
            logger.write_to_main("parameter_payload={}".format(parameter_payload.__dict__()),
                                 ConfigSetting().LogConfig.compiler)
            payload = None
            if isinstance(parameter_payload, LeafNode):
                fp = parameter_payload.leaf_property.payload
                if isinstance(fp, Fuzzable):
                    logger.write_to_main(f"fp={fp}", ConfigSetting().LogConfig.compiler)
                    leaf_property = parameter_payload.leaf_property
                    fp.parameter_name = parameter_name if ConfigSetting().TrackFuzzedParameterNames else None
                else:
                    leaf_property = parameter_payload
                leaf_node = LeafNode(leaf_property=leaf_property)
                payload = leaf_node
            elif isinstance(parameter_payload, InternalNode):
                payload = parameter_payload

            return RequestParameter(name=parameter_name,
                                    payload=payload,
                                    serialization=Parameters.get_parameter_serialization(parameter))

        example_payloads = []
        print("Get Parameters")
        rest_of_payloads = []
        if example_config and example_config[0]:
            for parameter in parameter_list:
                first_payload = Parameters.get_parameters_from_example(
                    swagger_doc,
                    example_config[0],
                    parameter,
                    schema_cache)
                logger.write_to_main(f"first_payload={first_payload}", ConfigSetting().LogConfig.compiler)
                if first_payload is not None:
                    example_payloads.append(first_payload)
                for e in example_config[1:]:
                    rest_of_payload = Parameters.get_parameters_from_example(swagger_doc,
                                                                             e,
                                                                             parameter,
                                                                             schema_cache)
                    if rest_of_payload is not None:
                        rest_of_payloads.append(rest_of_payload)

        schema_payload = []
        if len(example_payloads) == 0:
            schema_payload = [generate_parameter_payload(parameter=p)
                              for p in parameter_list]
        else:
            if ConfigSetting().DataFuzzing:
                schema_payload = [generate_parameter_payload(parameter=p)
                                  for p in parameter_list]

        logger.write_to_main(f"len(schema_payload)={len(schema_payload)}, "
                             f"len(example_payloads)={len(example_payloads)}", ConfigSetting().LogConfig.compiler)

        if len(example_payloads) > 0 and len(schema_payload) > 0:
            example_payloads_list = [(ParameterPayloadSource.Examples, ParameterList(example_payloads))]
            result = example_payloads_list + [(ParameterPayloadSource.Schema, ParameterList(schema_payload))]
        elif len(example_payloads) > 0 and len(schema_payload) == 0:
            result = [(ParameterPayloadSource.Examples, ParameterList(example_payloads))]
        elif len(example_payloads) == 0 and len(schema_payload) > 0:
            logger.write_to_main(f"schema_payload={schema_payload}", ConfigSetting().LogConfig.compiler)
            result = [(ParameterPayloadSource.Schema, ParameterList(schema_payload))]
        else:
            raise ValueError("Invalid combination")
        for item in result:
            logger.write_to_main(f"result={type(item)}", ConfigSetting().LogConfig.compiler)
        return result


class XMsPaths:
    @staticmethod
    def replace_with_original_paths(req: RequestId):
        x_ms_path = req.xMsPath
        x_ms_path_endpoint = x_ms_path.get_endpoint()

        query_part_split = x_ms_path.query_part.split('=|&')

        path_part_length = len(x_ms_path.path_part) - (len(query_part_split) * 2)
        path_part = x_ms_path.path_part
        query_part = x_ms_path.query_part

        path_parameters_in_query_part = [(idx * 2 + 1, p) for idx, p in enumerate(query_part_split) if
                                         is_path_parameter(p)]
        query_param_payloads = [(Constant(PrimitiveType.String, ""), x_ms_path.query_part)]
        for param_index, param_name in path_parameters_in_query_part:
            _, remaining_query_part = query_param_payloads[-1]
            param_index_in_query = remaining_query_part.index(param_name)
            constant_payload = remaining_query_part[:param_index_in_query]
            param_payload = query_part[param_index]
            new_remaining_query_part = remaining_query_part[param_index_in_query + len(param_name):]
            query_param_payloads.append(((Constant(PrimitiveType.String, constant_payload), ""),
                                         new_remaining_query_part))

        x_ms_path_query_load = [[Constant(PrimitiveType.String, "?")]]
        x_ms_path_query_load.extend([fp for fp, _ in query_param_payloads])

        return {"id": {"endpoint": x_ms_path_endpoint, "method": req.method, "xMsPath": req.xMsPath},
                "path": path_part + x_ms_path_query_load}

    @staticmethod
    def filter_xms_path_query_parameters(all_query_parameters, endpoint_query_part):
        endpoint_query_parameter_names = [param if is_path_parameter(param) else
                                          try_get_path_parameter_name(param)
                                          for param in endpoint_query_part.split("&")]

        query_parameters_filtered = []
        for payload_source, request_parameter_payload in all_query_parameters:
            if request_parameter_payload == "ParameterList" and payload_source == "Schema":
                query_parameters_not_in_path = [request_parameter for request_parameter in request_parameter_payload if
                                                request_parameter.name not in endpoint_query_parameter_names]
                query_parameters_filtered.append((payload_source, "ParameterList", query_parameters_not_in_path))
            elif request_parameter_payload == "ParameterList":
                query_parameters_filtered.append((payload_source, request_parameter_payload))
            elif request_parameter_payload == "Example":
                print("Warning: example found with x-ms-paths query parameters.")
                query_parameters_filtered.append((payload_source, request_parameter_payload))

        return query_parameters_filtered


# getInjectedCustomPayloadParameters
def get_injected_custom_payload_parameters(dictionary: MutationsDictionary,
                                           custom_payload_type: CustomPayloadType,
                                           excluded_parameters: list):
    """
    Given a list of parameters from the spec and dictionary,
    determines which additional injected parameters are specified in the dictionary
    and creates the corresponding payloads.

    Args:
        dictionary (MutationsDictionary): Dictionary containing custom payload parameter names.
        custom_payload_type (CustomPayloadType): The type of custom payload, either 'Header' or 'Query'.
        excluded_parameters (list): List of parameters to exclude from injection.

    Returns:
        list: List of injected custom payload parameters with their payload details.
    """
    logger.write_to_main(f"custom_payload_type={custom_payload_type}", ConfigSetting().LogConfig.compiler)
    if custom_payload_type == CustomPayloadType.Header:
        parameter_names_specified_as_custom_payloads = dictionary.get_custom_payload_header_parameter_names()
    elif custom_payload_type == CustomPayloadType.Query:
        parameter_names_specified_as_custom_payloads = dictionary.get_custom_payload_query_parameter_names()
    else:
        raise ValueError(f"{custom_payload_type} is not supported in this context.")

    parameter_names = [name for name in parameter_names_specified_as_custom_payloads if
                       name not in excluded_parameters]
    headers = []
    for header_name in parameter_names:
        custom_payload = CustomPayload(payload_type=custom_payload_type,
                                       primitive_type=PrimitiveType.String,
                                       payload_value=header_name,
                                       is_object=False,
                                       dynamic_object=None)
        leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                        payload=custom_payload,
                                                        is_required=True,
                                                        is_readonly=False))
        new_parameter = RequestParameter(name=header_name,
                                         payload=leaf_node,
                                         serialization=None)
        headers.append(new_parameter)

    return headers


# getContentLengthCustomPayload
def get_content_length_custom_payload(payload_type: CustomPayloadType,
                                      primitive_type: PrimitiveType,
                                      payload_value: str):
    header_name = "Content-Length"
    custom_payload_obj = CustomPayload(payload_type=payload_type,
                                       primitive_type=primitive_type,
                                       payload_value=payload_value,
                                       is_object=False,
                                       dynamic_object=None)
    leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                    payload=custom_payload_obj,
                                                    is_required=True,
                                                    is_readonly=False))

    return [RequestParameter(name=payload_value,
                             payload=leaf_node,
                             serialization=None)]


def replace_custom_payloads(custom_payload_type,
                            custom_payload_parameter_names,
                            request_parameter: RequestParameter):
    if request_parameter.name in custom_payload_parameter_names:
        is_required, is_read_only = (request_parameter.payload.leaf_property.is_required,
                                     request_parameter.payload.leaf_property.is_readonly)
        if isinstance(request_parameter.payload, LeafNode):
            custom_payload = CustomPayload(payload_type=custom_payload_type,
                                           primitive_type=PrimitiveType.String,
                                           payload_value=request_parameter.name,
                                           is_object=False,
                                           dynamic_object=None)
            leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                            payload=custom_payload,
                                                            is_required=is_required,
                                                            is_readonly=is_read_only))
            new_parameter = RequestParameter(name=request_parameter.name,
                                             payload=leaf_node,
                                             serialization=None)
            return new_parameter, True
        else:
            return request_parameter, False
    else:
        return request_parameter, False


# getInjectedHeaderOrQueryParameters
def get_injected_header_or_query_parameters(request_id: RequestId,
                                            dictionary: MutationsDictionary,
                                            spec_parameters: list,
                                            custom_payload_type: CustomPayloadType):
    """
    Get the injected parameters for the request.
    These are the parameters that are specified in the dictionary,
    which are not part of the Swagger/OpenAPI spec.

    Args:
        spec_parameters (list): List of parameters specified in the Swagger/OpenAPI spec.
        custom_payload_type (CustomPayloadType): Type of custom payload, either 'Header' or 'Query'.
        request_id (RequestId): The request identifier with endpoint and method attributes.
        dictionary (Dictionary): Custom dictionary with methods for retrieving payload names.

    Returns:
        list: List of injected custom payload parameters.
    """
    logger.write_to_main(f"spec_parameters={spec_parameters}", ConfigSetting().LogConfig.compiler)

    def is_request_specific_name(name):
        # Request-specific custom payloads are of the form <endpoint>/<method>/<parameter name>
        return name.startswith('/') and any(
            f"/{method.lower()}/" in name.lower() for method in SupportedOperationMethods)

    # Get the prefix for the request type payload
    prefix = get_request_type_payload_prefix(request_id.endpoint, request_id.method)

    # Get the parameters specified as custom payloads based on the payload type
    if custom_payload_type == CustomPayloadType.Header:
        parameters_specified_as_custom_payloads = dictionary.get_custom_payload_header_parameter_names()
    elif custom_payload_type == CustomPayloadType.Query:
        parameters_specified_as_custom_payloads = dictionary.get_custom_payload_query_parameter_names()
        logger.write_to_main(f"parameters_specified_as_custom_payloads={parameters_specified_as_custom_payloads}",
                             ConfigSetting().LogConfig.compiler)
    else:
        raise ValueError(f"{custom_payload_type} is not supported in this context.")
    # Filter out any parameters that are request-specific and refer to a different request
    excluded_request_specific_parameters = \
        [name for name in parameters_specified_as_custom_payloads
         if is_request_specific_name(name) and not name.startswith(prefix)]

    # Filter out the spec parameters
    # Filter out Content-Type, because this is handled separately later, in order to
    # be able to fuzz or replace the content type Filter both the global content-type and the one for this specific
    # request.
    # Exclude Content-Type parameters (both global and request-specific)
    excluded_content_type_parameter_names_in_custom_payload = [
        "Content-Type",
        get_request_type_payload_name(request_id.endpoint, request_id.method, "Content-Type")]

    # Combine excluded parameters and spec parameters
    excluded_parameters = (spec_parameters + excluded_content_type_parameter_names_in_custom_payload +
                           excluded_request_specific_parameters)

    injected_custom_payload_parameters = get_injected_custom_payload_parameters(dictionary,
                                                                                custom_payload_type,
                                                                                excluded_parameters)

    logger.write_to_main(f"injected_custom_payload_parameters={injected_custom_payload_parameters}",
                         ConfigSetting().LogConfig.compiler)
    return injected_custom_payload_parameters


def get_content_type_header(request_parameters: RequestParameters,
                            dictionary: MutationsDictionary,
                            request_id: RequestId):
    request_has_body = False
    result = []
    if request_parameters.body:
        if isinstance(request_parameters.body[0][1], ParameterList):
            request_has_body = len(request_parameters.body[0][1].request_parameters) > 0
        elif (isinstance(request_parameters.body[0][1], Example) and
              isinstance(request_parameters.body[0][1].payload, Constant)):
            request_has_body = not str.isspace(request_parameters.body[0][1].payload.payload)
        else:
            raise UnsupportedType("unsupported body parameter type")

    if request_has_body:
        content_type_header_name = "Content-Type"

        endpoint = request_id.endpoint if not request_id.xMsPath else request_id.xMsPath.get_endpoint()

        found_custom_payload = dictionary.find_request_type_custom_payload(endpoint,
                                                                           request_id.method,
                                                                           content_type_header_name,
                                                                           ParameterKind.Header)

        if found_custom_payload:
            payload_value = found_custom_payload[0]
            payload_type = found_custom_payload[1]
            custom_payload_obj = CustomPayload(payload_type=payload_type,
                                               primitive_type=PrimitiveType.String,
                                               payload_value=payload_value,
                                               is_object=False,
                                               dynamic_object=None)
            leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                            payload=custom_payload_obj,
                                                            is_required=True,
                                                            is_readonly=False))
            request_param = [RequestParameter(name=content_type_header_name,
                                              payload=leaf_node,
                                              serialization=None)]
            result.append((ParameterPayloadSource.DictionaryCustomPayload, ParameterList(request_param)))
        else:
            custom_payload_obj = Constant(primitive_type=PrimitiveType.String,
                                          variable_name="application/json")
            leaf_node = LeafNode(leaf_property=LeafProperty(name="",
                                                            payload=custom_payload_obj,
                                                            is_required=True,
                                                            is_readonly=False))
            request_param = [RequestParameter(name=content_type_header_name,
                                              payload=leaf_node,
                                              serialization=None)]
            result.append((ParameterPayloadSource.DictionaryCustomPayload, ParameterList(request_param)))

    return [result]


# Generate header parameters.
# Do not compute dependencies for header parameters unless resolveHeaderDependencies (from config) is true.
def generate_request_header_primitives(request_parameters: RequestParameters,
                                       dependencies,
                                       dictionary: MutationsDictionary,
                                       request_id: RequestId):
    logger.write_to_main(f"endpoint={request_id.endpoint}", ConfigSetting().LogConfig.compiler)
    headers_specified_as_custom_payloads = dictionary.get_custom_payload_header_parameter_names()
    logger.write_to_main(f"headers_specified_as_custom_payloads={headers_specified_as_custom_payloads}",
                         ConfigSetting().LogConfig.compiler)
    # No headers in Swagger
    if request_parameters.header is None:
        logger.write_to_main(f"call get_injected_header_or_query_parameters", ConfigSetting().LogConfig.compiler)
        injected_custom_payload_header_parameters = get_injected_header_or_query_parameters(
            request_id=request_id,
            dictionary=dictionary,
            spec_parameters=[],
            custom_payload_type=CustomPayloadType.Header)
        request_header_parameters = [(ParameterPayloadSource.DictionaryCustomPayload,
                                      ParameterList(request_parameters=injected_custom_payload_header_parameters))]

        return [request_header_parameters]

    elif (request_parameters.header and request_parameters.header[0][0] == ParameterPayloadSource.Schema and
          request_parameters.header[0][1] is None):
        # ParameterList is None
        # No headers in Swagger
        injected_custom_payload_header_parameters = get_injected_header_or_query_parameters(
            request_id=request_id,
            dictionary=dictionary,
            spec_parameters=[],
            custom_payload_type=CustomPayloadType.Header)

        if not injected_custom_payload_header_parameters:
            # TODO：删除此分支并更新grammar.py测试基线
            request_header_parameters = [(ParameterPayloadSource.Schema, ParameterList([]))]
        else:
            request_header_parameters = [ParameterPayloadSource.DictionaryCustomPayload,
                                         ParameterList(injected_custom_payload_header_parameters)]

        return [request_parameters.header + request_header_parameters]
    else:

        def is_content_length_param(name):
            return name == "Content-Length"

        result = []
        for payload_source, request_headers in request_parameters.header:
            parameter_list = []
            if isinstance(request_headers, ParameterList):
                if ConfigSetting().ResolveHeaderDependencies:
                    for p in request_headers.request_parameters:
                        new_payload, _ = DependencyLookup.get_dependency_payload(dependencies,
                                                                                 None,
                                                                                 request_id,
                                                                                 p,
                                                                                 dictionary)
                        parameter_list.append(new_payload)
                else:
                    parameter_list = request_headers.request_parameters
            else:
                raise UnsupportedType("Only a list of header parameters is supported.")

            spec_contains_content_length = any(is_content_length_param(p.name)
                                               for p in parameter_list)
            dictionary_contains_content_length = any(
                is_content_length_param(name) for name in dictionary.get_custom_payload_names())

            add_content_length_custom_payload = spec_contains_content_length and dictionary_contains_content_length
            logger.write_to_main(f"spec_contains_content_length={spec_contains_content_length},"
                                 f"dictionary_contains_content_length={dictionary_contains_content_length}"
                                 f"add_content_length_custom_payload={add_content_length_custom_payload}",
                                 ConfigSetting().LogConfig.compiler)

            if spec_contains_content_length and dictionary_contains_content_length:
                parameter_list = [rp for rp in parameter_list if
                                  rp.name != "Content-Length" and rp.name != "Content-Type"]

            replaced_param = []
            for request_parameter in parameter_list:
                header_param, replaced = replace_custom_payloads(CustomPayloadType.Header,
                                                                 headers_specified_as_custom_payloads,
                                                                 request_parameter)

                replaced_param.append(header_param)

            spec_header_parameter_names = [p.name for p in parameter_list]
            logger.write_to_main(f"call get_injected_header_or_query_parameters", ConfigSetting().LogConfig.compiler)
            # Get the additional custom payload header parameters that should be injected
            injected_custom_payload_header_parameters = get_injected_header_or_query_parameters(
                request_id=request_id,
                dictionary=dictionary,
                spec_parameters=spec_header_parameter_names,
                custom_payload_type=CustomPayloadType.Header)

            all_header_parameters = replaced_param + list(injected_custom_payload_header_parameters) + (
                get_content_length_custom_payload(payload_type=CustomPayloadType.String,
                                                  primitive_type=PrimitiveType.String,
                                                  payload_value="Content-Length")
                if add_content_length_custom_payload else [])

            result = result + [(payload_source, ParameterList(all_header_parameters))]

        return [result]


def generate_request_query_primitives(request_parameters: RequestParameters,
                                      dependencies,
                                      dictionary: MutationsDictionary,
                                      request_id: RequestId):
    all_query_parameters_list = []
    logger.write_to_main(f"{all_query_parameters_list}", ConfigSetting().LogConfig.compiler)
    if not request_id.xMsPath:
        request_query_parameters = request_parameters.query
    else:
        request_query_parameters = XMsPaths.filter_xms_path_query_parameters(request_parameters.query,
                                                                             request_id.xMsPath.query_part)

    if request_query_parameters is None or len(request_query_parameters) == 0:
        injected_custom_payload_query_parameters = get_injected_header_or_query_parameters(
            request_id=request_id,
            dictionary=dictionary,
            spec_parameters=[],
            custom_payload_type=CustomPayloadType.Query)

        all_query_parameters_list.append(
            (ParameterPayloadSource.DictionaryCustomPayload,
             ParameterList(injected_custom_payload_query_parameters)))

        return all_query_parameters_list
    elif (len(request_query_parameters) == 1 and request_query_parameters[0][
        0] == ParameterPayloadSource.Schema and
          not request_query_parameters[0][1]):
        all_query_parameters_list = request_query_parameters
        injected_custom_payload_query_parameters = get_injected_header_or_query_parameters(
            request_id=request_id,
            dictionary=dictionary,
            spec_parameters=[],
            custom_payload_type=CustomPayloadType.Query)

        if not injected_custom_payload_query_parameters:
            all_query_parameters_list.append((ParameterPayloadSource.Schema, ParameterList([])))
        else:
            all_query_parameters_list.append((ParameterPayloadSource.DictionaryCustomPayload,
                                              ParameterList(injected_custom_payload_query_parameters)))

        return all_query_parameters_list
    else:
        for payload_source, request_query in request_query_parameters:
            parameter_list = []
            if ConfigSetting().ResolveQueryDependencies and dependencies is not None:
                for p in request_query.request_parameters:
                    new_payload, _ = DependencyLookup.get_dependency_payload(dependencies,
                                                                             None,
                                                                             request_id,
                                                                             p,
                                                                             dictionary)
                    parameter_list.append(new_payload)

            spec_query_parameter_names = [p.name for p in parameter_list]
            logger.write_to_main(f"{spec_query_parameter_names}", ConfigSetting().LogConfig.compiler)
            injected_custom_payload_query_parameters = get_injected_header_or_query_parameters(
                request_id=request_id,
                dictionary=dictionary,
                spec_parameters=spec_query_parameter_names,
                custom_payload_type=CustomPayloadType.Query)

            all_query_parameters = parameter_list + injected_custom_payload_query_parameters

            all_query_parameters_list.append((payload_source, ParameterList(all_query_parameters)))

        return all_query_parameters_list


def generate_request_body_primitives(request_parameters: RequestParameters,
                                     dependencies,
                                     dictionary: MutationsDictionary,
                                     request_id: RequestId):
    endpoint = request_id.endpoint if not request_id.xMsPath else request_id.xMsPath.get_endpoint()
    # Check if the body is being replaced by a custom payload
    found_entry = dictionary.find_body_custom_payload(endpoint, request_id.method)
    current_dict = dictionary
    if found_entry:
        custom_payload_obj = CustomPayload(payload_type=CustomPayloadType.String,
                                           primitive_type=PrimitiveType.String,
                                           payload_value=found_entry,
                                           is_object=False,
                                           dynamic_object=None)
        return [(ParameterPayloadSource.DictionaryCustomPayload, custom_payload_obj)], dictionary
    else:
        request_body_list = []

        for payload_source, request_body in request_parameters.body:
            parameter_list = []
            if ConfigSetting().ResolveBodyDependencies and dependencies is not None:
                for p in request_body.request_parameters:
                    new_payload, result_dict = DependencyLookup.get_dependency_payload(
                        dependencies=dependencies,
                        path_payload=None,
                        request_id=request_id,
                        request_parameter=p,
                        dictionary=current_dict)
                    logger.write_to_main(f"result_dict={result_dict}", ConfigSetting().LogConfig.compiler)
                    current_dict = current_dict.combine_custom_payload_suffix(result_dict)

                    parameter_list.append(new_payload)
            else:
                parameter_list = request_body.request_parameters
            request_body_list.append((payload_source, ParameterList(parameter_list)))
        logger.write_to_main(f"dictionary={current_dict.restler_custom_payload}", ConfigSetting().LogConfig.compiler)
        return request_body_list, current_dict


def generate_request_path_primitives(request_id: RequestId,
                                     dependencies: dict[str, List[ProducerConsumerDependency]],
                                     request_parameters: RequestParameters,
                                     dictionary: MutationsDictionary,
                                     query_parameter_list) -> Optional[FuzzingPayload]:
    path_parameters = {}
    query_parameters = {}
    logger.write_to_main(f"request_parameters.path.request_parameters={request_parameters.path.request_parameters}",
                         ConfigSetting().LogConfig.compiler)
    if isinstance(request_parameters.path, ParameterList):
        if request_parameters.path.request_parameters and len(request_parameters.path.request_parameters) > 0:
            path_parameters = {p.name: p for p in request_parameters.path.request_parameters}
            logger.write_to_main(f"path_parameters={path_parameters}", ConfigSetting().LogConfig.compiler)
        else:
            path_parts = get_path_from_string(request_id.endpoint, True)
            path = []
            for part in path_parts.path:
                if part.part_type == PathPartType.Constant:
                    path.append(Constant(PrimitiveType.String, part.value))
                elif part.part_type == PathPartType.Separator:
                    path.append(Constant(PrimitiveType.String, "/"))
            return path
    else:
        raise Exception("Only a list of path parameters is supported {}.".format(request_id.endpoint))

    for item in request_parameters.query:
        if item[0] == ParameterPayloadSource.Schema:
            query_parameter_list = item[1]
            if isinstance(query_parameter_list, ParameterList):
                if query_parameter_list.request_parameters and len(query_parameter_list.request_parameters) > 0:
                    query_parameters = {p.name: p for p in query_parameter_list.request_parameters}
                    logger.write_to_main(f"query_parameters={path_parameters}", ConfigSetting().LogConfig.compiler)
            else:
                raise Exception("Only a list of query parameters is supported.")
    if request_id.xMsPath is None:
        path_parts = get_path_from_string(request_id.endpoint, True)
    else:
        path_parts = get_path_from_string(request_id.xMsPath.get_normalized_endpoint(), True)
        logger.write_to_main(f"path_parts={path_parts}", ConfigSetting().LogConfig.compiler)
    path = []
    for part in path_parts.path:
        logger.write_to_main("path.part_type={}, {}".format(part.value, part.part_type),
                             ConfigSetting().LogConfig.compiler)
        if part.part_type == PathPartType.Parameter:
            declared_parameter = next((dp for dp in path_parameters if parameter_names_equal(dp, part.value)),
                                      None)
            logger.write_to_main(f"declared_parameter={declared_parameter}, "
                                 f"request_id.xMsPath={request_id.xMsPath}", ConfigSetting().LogConfig.compiler)

            if declared_parameter is None and request_id.xMsPath:
                # Swagger bug: parameter is not declared
                # Avoid failing to compile, since other requests may still be fuzzed successfully
                declared_parameter = next(
                    (dp.name for dp in query_parameters if parameter_names_equal(dp.name, part.value)), None)
                if declared_parameter:
                    new_request_parameter, _ = DependencyLookup.get_dependency_payload(dependencies,
                                                                                       None,
                                                                                       request_id,
                                                                                       declared_parameter,
                                                                                       dictionary)
                    logger.write_to_main("new_request_parameter={}".format(type(new_request_parameter)),
                                         ConfigSetting().LogConfig.compiler)
                    path.append(Parameters.get_path_parameter_payload(new_request_parameter.payload))
                else:
                    path.append(Constant(PrimitiveType.String, format_path_parameter(part.value)))
            elif declared_parameter is None and request_id.xMsPath is None:
                continue
            else:
                logger.write_to_main(f"path_parameters={path_parameters}, "
                                     f"declared_parameter={path_parameters[declared_parameter]}",
                                     ConfigSetting().LogConfig.compiler)
                new_request_parameter, _ = DependencyLookup.get_dependency_payload(dependencies,
                                                                                   None,
                                                                                   request_id,
                                                                                   path_parameters[declared_parameter],
                                                                                   dictionary)
                logger.write_to_main(f"new_request_parameter={new_request_parameter.payload}",
                                     ConfigSetting().LogConfig.compiler)
                path.append(Parameters.get_path_parameter_payload(new_request_parameter.payload))

        elif part.part_type == PathPartType.Constant:
            path.append(Constant(PrimitiveType.String, part.value))
        elif part.part_type == PathPartType.Separator:
            current_element = Constant(PrimitiveType.String, "/")
            if len(path) > 0:
                last_element = path[-1]
                if not current_element.__eq__(last_element):
                    path.append(current_element)
            else:
                path.append(current_element)
    return path


# generateRequestPrimitives
def generate_request_primitives(request_id: RequestId,
                                dependency_data: RequestDependencyData,
                                request_parameters: RequestParameters,
                                dependencies: dict[str, List[ProducerConsumerDependency]],
                                base_path: str,
                                host: Optional[str],
                                dictionary: MutationsDictionary,
                                request_metadata: RequestMetadata) -> (MutationsDictionary, Request):
    method = request_id.method
    path_parameter = []
    query_parameter_list = None
    if request_parameters and request_parameters.path:
        path_parameter = generate_request_path_primitives(request_id, dependencies, request_parameters, dictionary,
                                                          query_parameter_list)

    logger.write_to_main(f"path_parameter={path_parameter}", ConfigSetting().LogConfig.compiler)
    header_param = generate_request_header_primitives(request_parameters=request_parameters,
                                                      dependencies=dependencies,
                                                      dictionary=dictionary,
                                                      request_id=request_id)

    logger.write_to_main(f"header_param={header_param}", ConfigSetting().LogConfig.compiler)
    query_param = generate_request_query_primitives(request_parameters=request_parameters,
                                                    dependencies=dependencies,
                                                    dictionary=dictionary,
                                                    request_id=request_id)
    logger.write_to_main(f"query_param={query_param}", ConfigSetting().LogConfig.compiler)

    body_param, dictionary = generate_request_body_primitives(request_parameters=request_parameters,
                                                              dependencies=dependencies,
                                                              dictionary=dictionary,
                                                              request_id=request_id)
    content_type_param = get_content_type_header(request_parameters=request_parameters,
                                                 dictionary=dictionary,
                                                 request_id=request_id)

    logger.write_to_main(f"dictionary={DictionarySetting().restler_custom_payload}", ConfigSetting().LogConfig.compiler)
    logger.write_to_main(f"body={body_param}", ConfigSetting().LogConfig.compiler)
    headers = [("Accept", "application/json"), ("Host", host)]
    request = Request(request_id=request_id, method=method, base_path=base_path, path=path_parameter,
                      query_parameters=query_param, body_parameters=body_param,
                      header_parameters=header_param + content_type_param,
                      token=TokenKind.Refreshable, headers=headers, http_version="1.1",
                      dependency_data=dependency_data, request_metadata=request_metadata)
    return request, dictionary


def process_ordered_swagger_docs(swagger_docs: List[SwaggerDoc],
                                 user_specified_examples: List[ExampleConfigFile]):
    processed = []
    per_resource_dictionaries_seq = []
    # 构建 perResourceDictionaries
    per_resource_dictionaries = defaultdict(list)
    # When multiple Swagger files are used, the request data is the union of all requests.
    for i, swagger_doc in enumerate(swagger_docs):

        result = get_request_data(swagger_doc=swagger_doc,
                                  user_specified_examples=user_specified_examples)
        logger.write_to_main(f"i={i}, swagger_doc={swagger_doc}, {result}", ConfigSetting().LogConfig.compiler)
        processed.append((result, i, swagger_doc.dictionary))

        if swagger_doc.dictionary:
            dictionary_name = f"dict_{i}"
            for req_id, _ in result:
                per_resource_dictionaries[req_id.hex_hash].append((dictionary_name, swagger_doc.dictionary))
                logger.write_to_main(f"{per_resource_dictionaries}", ConfigSetting().LogConfig.compiler)

    # Remove duplicates
    multiple_endpoints = {key: len(val) for key, val in per_resource_dictionaries.items() if len(val) > 1}
    # Check for multiple instances of the same endpoint across Swagger files
    # Fail if there are multiple instances of the same endpoint across Swagger files
    # This detects when two different dictionaries are requested for the same endpoint.
    if multiple_endpoints:
        raise ValueError(f"Endpoints were specified twice in two different Swagger files: {multiple_endpoints}")
    per_resource_dictionaries_final = {key: list(set(value)) for key, value in per_resource_dictionaries.items()}
    logger.write_to_main(f"per_resource_dictionaries_final={per_resource_dictionaries_final}, "
                         f"len(per_resource_dictionaries_final)={len(per_resource_dictionaries_final)}",
                         ConfigSetting().LogConfig.compiler)
    request_data = [req_list for req_list, _, _ in processed]
    request_data = [item for sublist in request_data for item in sublist]
    return request_data, per_resource_dictionaries_final


# When multiple Swagger files are used, global annotations are applied across all Swagger files.
def get_global_annotations(swagger_doc: list[SwaggerDoc],
                           global_external_annotations: List[Dict]):
    per_swagger_annotations = []

    for doc in swagger_doc:
        # todo removed for test_config.py test_swagger_config_custom_annotations_sanity
        inline_annotations = doc.inline_annotations if doc.inline_annotations else []
        external_annotations = doc.global_annotations if doc.global_annotations else []
        per_swagger_annotations.append(inline_annotations + external_annotations)

    global_annotations = [annotation for annotations in per_swagger_annotations for annotation in annotations]
    annotations_obj = []

    annotations_obj = get_annotations_from_json(global_annotations)
    global_annotations_obj = get_annotations_from_json(global_external_annotations)
    annotations_obj += global_annotations_obj

    return annotations_obj


# getRequestData in generateRequestGrammar
def get_request_data(swagger_doc: SwaggerDoc,
                     user_specified_examples: List[ExampleConfigFile]) -> list[tuple[RequestId, RequestData]]:
    logger.write_to_main(f"Get Request Data: swagger_doc)={swagger_doc}, "
                         f"len(user_specified_examples)={len(user_specified_examples)}",
                         ConfigSetting().LogConfig.compiler)
    schema_cache = SchemaCache()
    request_data_seq = []
    if swagger_doc.paths is None:
        return []

    for item in swagger_doc.paths:
        if isinstance(item, RequestInfo):
            ep = item.request_id.endpoint.rstrip('/')
            logger.write_to_main(f"endpoint={ep}", ConfigSetting().LogConfig.compiler)
            print(f"{ep} start")
            x_ms_path = None
            if swagger_doc.xMsPathsMapping:
                x_ms_path = get_x_ms_path(ep)
                if x_ms_path is None:
                    raise ValueError("get_x_ms_path should have returned a value")

            request_id = RequestId(endpoint=ep,
                                   method=item.method,
                                   xms_path=x_ms_path,
                                   has_example=item.request_id.has_example)
            # Extract example configuration for the endpoint+method
            example_config = None
            # If there are examples for this endpoint+method, extract the example file using the example options.
            if (ConfigSetting().UseBodyExamples or ConfigSetting().UseQueryExamples or
                    ConfigSetting().UseHeaderExamples or ConfigSetting().UsePathExamples or
                    ConfigSetting().DiscoverExamples):
                # The original endpoint must be used to find the example
                if x_ms_path is not None:
                    xms_path_obj = XMsPath(query_part=ep, path_part=ep)
                    xms_path_obj.get_endpoint()

                example_request_payloads = get_example_config(endpoint=item.request_id.endpoint,
                                                              method=item.method.name.lower(),
                                                              swagger_method_definition=swagger_doc.specification,
                                                              discover_examples=ConfigSetting().DiscoverExamples,
                                                              user_specified_payloads=user_specified_examples,
                                                              use_all_examples=ConfigSetting().UseAllExamplePayloads)

                # If 'discoverExamples' is specified, create a local copy in the specified examples directory for
                # all the examples found.
                if ConfigSetting().DiscoverExamples is not None:
                    for count, req_payload in enumerate(example_request_payloads):
                        if req_payload.example_file_path != "":
                            source_file_path = req_payload.example_file_path
                            file_name = os.path.splitext(os.path.basename(source_file_path))[0]
                            ext = os.path.splitext(source_file_path)[-1]
                            local_example_file_name = f"{file_name}{count}{ext}"
                            # Append a suffix in case there are collisions
                            target_file_path = os.path.join(ConfigSetting().ExamplesDirectory, local_example_file_name)
                            try:
                                shutil.copyfile(source_file_path, target_file_path)
                            except Exception as e:
                                print(
                                    f"ERROR copying example file ({source_file_path}) to target directory "
                                    f"({ConfigSetting().ExamplesDirectory}): {e}")
                    example_config = example_request_payloads

            # If examples are being discovered, output them in the 'Examples' directory
            if not ConfigSetting().ReadOnlyFuzz or request_id.method in ReaderMethods:
                print(f"{ep} path parameter start")
                path_parameters = (
                    Parameters.path_parameters(swagger_doc,
                                               item,
                                               ep,
                                               example_config if ConfigSetting().UsePathExamples else None,
                                               schema_cache))

                all_query_parameters = []
                logger.write_to_main(f"item.queryParameters={len(item.queryParameters)}",
                                     ConfigSetting().LogConfig.compiler)
                if len(item.queryParameters) > 0:
                    print(f"{ep} query parameter.")
                    all_query_parameters = (
                        Parameters.get_parameters(swagger_doc,
                                                  item,
                                                  item.queryParameters,
                                                  example_config if ConfigSetting().UseQueryExamples else None,
                                                  schema_cache))

                body = []

                if len(item.bodyParameters) > 0:
                    logger.write_to_main(f"item.bodyParameters={item.bodyParameters}",
                                         ConfigSetting().LogConfig.compiler)
                    print(f"{ep} body parameter.")
                    body = Parameters.get_parameters(swagger_doc,
                                                     item,
                                                     item.bodyParameters,
                                                     example_config if ConfigSetting().UseBodyExamples else None,
                                                     schema_cache)

                    # Call the get_body function and assign the result to the body variable

                headers = []
                if item.headerParameters and len(item.headerParameters) > 0:
                    print(f"{ep} header parameter.")
                    headers = Parameters.get_parameters(swagger_doc,
                                                        item,
                                                        item.headerParameters,
                                                        example_config if ConfigSetting().UseHeaderExamples else None,
                                                        schema_cache)

                request_parameters = RequestParameters(path=path_parameters,
                                                       header=headers,
                                                       query=all_query_parameters,
                                                       body=body)

                all_responses = []
                logger.write_to_main(f"list(item.Responses) = {list(item.Responses)}",
                                     ConfigSetting().LogConfig.compiler)
                print(f"{ep} response")
                for response_code in list(item.Responses):
                    if int(response_code) in ValidResponseCodes:
                        logger.write_to_main(f"item.Responses[response_code]= {item.Responses[response_code]}"
                                             f", response_code = {response_code}", ConfigSetting().LogConfig.compiler)
                        response_value = item.Responses[response_code]
                        header_response = None
                        if response_value.is_set("header"):
                            header_response_schema = []
                            h_value = getattr(response_value, response_value.get_private_name("header"))
                            if h_value is not None:
                                for h_value_item in h_value.items():
                                    print("Generate Response Headers Schema....")
                                    header_schema = (
                                        generate_grammar_element_for_schema(swagger_doc,
                                                                            h_value_item,
                                                                            None,
                                                                            False,
                                                                            False,
                                                                            True,
                                                                            [],
                                                                            schema_cache,
                                                                            None))
                                    header_response_schema.append(header_schema)
                                    # todo NestedType
                                header_response = InternalNode(
                                    inner_property=InnerProperty(name="",
                                                                 payload=None,
                                                                 property_type=NestedType.Property,
                                                                 is_required=True,
                                                                 is_readonly=False),
                                    leaf_properties=header_response_schema)

                        print("Generate Response Body Schema....")
                        body_response_schema = None
                        if (response_value.is_set("type") or response_value.is_set("$ref")
                                or response_value.is_set("schema")):
                            body_response_schema = (
                                generate_grammar_element_for_schema(swagger_doc,
                                                                    response_value,
                                                                    None,
                                                                    False,
                                                                    False,
                                                                    True,
                                                                    [],
                                                                    schema_cache,
                                                                    None))
                            logger.write_to_main(f"body_response_schema={body_response_schema.__dict__()} "
                                                 f"type(body)={type(body_response_schema)}",
                                                 ConfigSetting().LogConfig.compiler)

                        # Convert links in the response to annotations
                        # todo Remove this source code because these functionalities are only supported in openapi3
                        link_annotations = None

                        response_info = ResponseInfo(body_response_schema=body_response_schema,
                                                     header_response_schema=header_response,
                                                     link_annotations=link_annotations)
                        all_responses.append(response_info)

                response = all_responses[0] if all_responses else None

                local_annotations = get_annotations_from_json(item.local_annotation)

                request_metadata = RequestMetadata(is_long_running_operation=False)
                is_long_running_operation = item.long_running_operation
                logger.write_to_main(f"is_long_running_operation={is_long_running_operation}",
                                     ConfigSetting().LogConfig.compiler)
                if is_long_running_operation is not None:
                    request_metadata = RequestMetadata(is_long_running_operation=is_long_running_operation)

                request_data = RequestData(request_parameters=request_parameters,
                                           local_annotations=local_annotations,
                                           link_annotations=response.link_annotations if response else [],
                                           response_properties=response.body_response_schema
                                           if response and response.body_response_schema else None,
                                           response_headers=response.header_response_schema
                                           if response and response.header_response_schema else [],
                                           request_metadata=request_metadata,
                                           example_config=example_config)
                request_data_seq.append((request_id, request_data))
            print(f"{ep} end")

    return request_data_seq


# generateRequestGrammar
# Generates the requests, dynamic objects, and response parsers required for the main RESTler algorithm
def generate_request_grammar(swagger_docs: list[SwaggerDoc],
                             dictionary: MutationsDictionary,
                             global_external_annotations: List[Dict],
                             user_specified_examples: List[ExampleConfigFile]):
    print("Getting requests...")
    request_data, per_resource_dictionaries = process_ordered_swagger_docs(swagger_docs, user_specified_examples)
    # When multiple Swagger files are used, the request data is the union of all requests.
    global_annotations = get_global_annotations(swagger_docs, global_external_annotations)

    logger.write_to_main(f"dictionary={dictionary.restler_custom_payload_uuid4_suffix}",
                         ConfigSetting().LogConfig.compiler)
    print("Getting dependencies...")
    dependencies_index, ordering_constraints, new_dictionary = (
        extract_dependencies(request_data,
                             global_annotations,
                             dictionary,
                             ConfigSetting().ResolveQueryDependencies,
                             ConfigSetting().ResolveBodyDependencies,
                             ConfigSetting().ResolveHeaderDependencies,
                             ConfigSetting().AllowGetProducers,
                             ConfigSetting().DataFuzzing,
                             per_resource_dictionaries,
                             ConfigSetting().ApiNamingConvention))
    # The dependencies above are analyzed on a per-request basis.
    # This can lead to missing dependencies (for example, an input producer writer
    # may be missing because the same parameter already refers to a reader).
    # As a workaround, the function below handles such issues by finding and fixing up the
    # problematic cases.
    dependencies_index, ordering_constraints = DependencyLookup.merge_dynamic_objects(dependencies_index,
                                                                                      ordering_constraints)

    dependencies = [value for value in dependencies_index.values()]
    dependencies = [item for sublist in dependencies for item in sublist]

    dependency_info = get_response_parsers(dependencies, ordering_constraints)

    # Remove the ending slash if present, since a static slash will
    # be inserted in the grammar
    # Note: this code is not sufficient, and the same logic must be added in the engine,
    # since the user may specify their own base path through a custom payload.
    # However, this is included here as well so reading the grammar is not confusing and for any
    # other tools that may process the grammar separately from the engine.

    base_path = swagger_docs[0].base_path.rstrip('/') if swagger_docs and swagger_docs[0].base_path else ""
    # issue fix for atest/swagger_only/simple_swagger_all_param_data_types.json
    # output :
    # host: null
    host = swagger_docs[0].host if swagger_docs and swagger_docs[0].host else None
    # todo
    # Get the request primitives for each request
    grammar = GrammarDefinition()
    print("Compiler--Generating request primitives...")
    for requestId, request_data_item in request_data:
        print(f"path={requestId.endpoint} method={requestId.method}")
        dependencies_item = dependency_info[
            requestId.hex_hash] if requestId.hex_hash in dependency_info.keys() else None
        if dependencies_item is not None:
            logger.write_to_main(f"dependencies_item={dependencies_item}", ConfigSetting().LogConfig.compiler)
        logger.write_to_main(f"new_dictionary={new_dictionary.restler_custom_payload}",
                             ConfigSetting().LogConfig.compiler)
        primitive, new_dictionary = generate_request_primitives(requestId,
                                                                dependencies_item,
                                                                request_data_item.request_parameters,
                                                                dependencies_index,
                                                                base_path,
                                                                host,
                                                                new_dictionary,
                                                                request_data_item.request_metadata)
        logger.write_to_main(f"new_dictionary={new_dictionary.restler_custom_payload}",
                             ConfigSetting().LogConfig.compiler)
        grammar.add(primitive)

    print(f"Compiler--Done Generating request primitives... len(grammar)={len(grammar.Requests)}")
    # If discoverExamples was specified, return the newly discovered examples
    examples = []

    for request_id, request_parameter in request_data:
        if request_parameter.example_config is not None:
            example_payloads = [FileExamplePayload(name=str(i), file_path=x.example_file_path)
                                for i, x in enumerate(request_parameter.example_config) if x.example_file_path]
            example_method = ExampleMethod(name=request_id.method, example_payloads=example_payloads)

            examples.append((request_id.endpoint, example_method))

    # Grouping examples by endpoint
    grouped_examples = {}
    for endpoint, method in examples:
        if endpoint not in grouped_examples:
            grouped_examples[endpoint] = []
        grouped_examples[endpoint].append(method)

    example_paths = []
    # Create a final structure for examples
    for endpoint, methods in grouped_examples.items():
        example_paths = [ExamplePath(path=endpoint, methods=methods)]

    requests = [request_id if request_id.xMsPath is None else XMsPaths.replace_with_original_paths(request_id)
                for request_id, request_parameter in request_data]

    return grammar, dependencies, new_dictionary, per_resource_dictionaries, examples
