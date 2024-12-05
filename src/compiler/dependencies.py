# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from typing import Tuple, Optional, List, Dict, Union
import os
from compiler.config import ConfigSetting
from compiler.utilities import JsonSerialization
from collections import defaultdict

from compiler.grammar import (
    DynamicObjectNaming,
    FuzzingPayload,
    InnerProperty,
    Fuzzable,
    Constant,
    DynamicObject,
    PrimitiveType,
    RequestParameter,
    ParameterList,
    LeafProperty,
    CustomPayloadType,
    cata_ctx,
    fold,
    iter_ctx,
    Tree,
    OrderingConstraintVariable,
    OperationMethod,
    RequestId,
    ProducerConsumerAnnotation,
    AnnotationResourceReference,
    Custom,
    ParameterPayloadSource,
    LeafNode,
    InternalNode)
from compiler.apiresource import (
    Consumer,
    ParameterKind,
    ProducerConsumerDependency,
    InputParameter,
    ApiResource,
    OrderingConstraintProducer,
    NamingConvention,
    HeaderResource,
    PathResource,
    QueryResource,
    BodyResource,
    ResponseProducer,
    DictionaryPayload,
    InputOnlyProducer,
    BodyPayloadInputProducer)
from compiler.access_paths import (
    AccessPath,
    EmptyAccessPath)
from compiler.dependency_analysis_types import (
    Producers,
    RequestData,
    ProducerKind,
    get_path_from_string,
    sort_by_parameter_kind,
    debug_inferred_match_sort_order)
from compiler.dictionary import MutationsDictionary, DictionarySetting

from restler.utils import restler_logger as logger


class UnsupportedType(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class InvalidSwaggerEndpoint(Exception):
    pass


# Determines whether a producer is valid for a given consumer
def is_valid_producer(p: ResponseProducer, consumer: Consumer, allow_get_producers: bool):
    consumer_endpoint, consumer_method = (consumer.consumer_id.request_id.endpoint,
                                          consumer.consumer_id.request_id.method)
    producer_endpoint, producer_method = (p.request_id.endpoint,
                                          p.request_id.method)
    logger.write_to_main(f"consumer_endpoint={consumer_endpoint}, producer_endpoint={producer_endpoint}",
                         ConfigSetting().LogConfig.dependencies)
    logger.write_to_main(f"consumer_method={consumer_method}, producer_method={producer_method} "
                         f"allow_get_producers={allow_get_producers}", ConfigSetting().LogConfig.dependencies)
    is_valid_method = producer_method in [OperationMethod.Put, OperationMethod.Post] or allow_get_producers
    if not is_valid_method:
        logger.write_to_main(f"is_valid_method == {is_valid_method}", ConfigSetting().LogConfig.dependencies)
        return False
    elif consumer_endpoint == producer_endpoint:
        if consumer_method == producer_method:
            logger.write_to_main(f"consumer_method == producer_method and consumer_endpoint == producer_endpoint",
                                 ConfigSetting().LogConfig.dependencies)
            return False
        else:
            if producer_method == OperationMethod.Post:
                logger.write_to_main(f"producer_method == OperationMethod.Post", ConfigSetting().LogConfig.dependencies)
                return True
            elif producer_method == OperationMethod.Put:
                logger.write_to_main(f"producer_method == OperationMethod.Put", ConfigSetting().LogConfig.dependencies)
                return consumer_method != OperationMethod.Post
            elif producer_method == OperationMethod.Patch:
                logger.write_to_main(
                    f"producer_method == OperationMethod.Patch="
                    f"{consumer_method != OperationMethod.Post and consumer_method != OperationMethod.Put}",
                    ConfigSetting().LogConfig.dependencies)
                return consumer_method != OperationMethod.Post and consumer_method != OperationMethod.Put
            elif producer_method == OperationMethod.Get:
                logger.write_to_main(f"producer_method == OperationMethod.Get",
                                     ConfigSetting().LogConfig.dependencies)
                return (consumer_method != OperationMethod.Post
                        and consumer_method != OperationMethod.Put
                        and consumer_method != OperationMethod.Patch)
            else:
                logger.write_to_main(f"producer_method == OperationMethod.Get",
                                     ConfigSetting().LogConfig.dependencies)
                return False
    else:
        logger.write_to_main(f"result={not producer_endpoint.startswith(consumer_endpoint)}",
                             ConfigSetting().LogConfig.dependencies)
        return not producer_endpoint.startswith(consumer_endpoint)


# Handles the pattern of a PUT 'CreateOrUpdate'
# Precondition: the consumer resource name is the last (right-most) path parameter.
# 'CreateOrUpdate' PUT requests are handled as follows:
# If the request is a PUT, update the mutation dictionary with a 'compiler_custom_payload_uuid_suffix' entry
# The naming schema is 'consumerResourceName' followed by a dash.
# This is required to generate a new name on every PUT.
# Otherwise, make the PUT request the producer.
# TODO: there is currently a gap in coverage: only the create version of PUT will be executed by RESTler.
#
# For reference, below is the corresponding PUT annotation that causes the same producer-consumer
# to be identified as this function.
# {
#    "producer_resource_name": "name",
#    "producer_method": "PUT",
#    "consumer_param": "applicationGatewayName",
#    "producer_endpoint": "/subscriptions/{subscriptionId}/applicationGateways/{applicationGatewayName}",
#    "except": {
#        "consumer_endpoint":"/subscriptions/{subscriptionId}/applicationGateways/{applicationGatewayName}",
#        "consumer_method": "PUT"
# }
# }
def add_uuid_suffix_entry_for_consumer(
        consumer_resource_name: str,
        dictionary: MutationsDictionary,
        consumer_id: ApiResource) -> Tuple[MutationsDictionary, Optional[str]]:
    if (len(dictionary.restler_custom_payload_uuid4_suffix) > 0 and
            consumer_resource_name in dictionary.restler_custom_payload_uuid4_suffix.keys()):
        return dictionary, dictionary.get_parameter_for_custom_payload_uuid_suffix(consumer_resource_name,
                                                                                   consumer_id.access_path_parts,
                                                                                   consumer_id.primitive_type)
    else:
        prefix_value = DynamicObjectNaming.generate_prefix_for_custom_uuid_suffix_payload(consumer_resource_name)
        if dictionary.restler_custom_payload_uuid4_suffix is None:
            dictionary.restler_custom_payload_uuid4_suffix = {}
        dictionary.restler_custom_payload_uuid4_suffix[consumer_resource_name] = prefix_value

        parameter = dictionary.get_parameter_for_custom_payload_uuid_suffix(consumer_resource_name,
                                                                            consumer_id.access_path_parts,
                                                                            consumer_id.primitive_type)

        return dictionary, parameter


# Create a producer that is identified by its path in the body only.
# For example, an API 'POST /products  { "tables": [{ "name": "ergoDesk" } ], "chairs": [{"name": "ergoChair"}]  }'
# that returns the same body.
# Here, the producer resource name is 'name', and the producer container is 'tables'
def create_body_payload_input_producer(consumer_resource_id):
    return BodyPayloadInputProducer(request_id=consumer_resource_id.request_id,
                                    resource_reference=consumer_resource_id.resource_reference,
                                    naming_convention=consumer_resource_id.naming_convention,
                                    primitive_type=consumer_resource_id.primitive_type)


# that is the result of invoking an API endpoint, which
# is identified by the last part of the endpoint.
# For example: POST /customers, or PUT /product/{productName}
def create_path_producer(request_id, access_path, naming_convention, primitive_type):
    """
    Creates a ResponseProducer instance.

    Parameters:
        request_id: The ID of the request.
        access_path: An object with 'Name' and 'Path' attributes.
        naming_convention: Optional naming convention.
        primitive_type: The primitive type.

    Returns:
        ResponseProducer instance.
    """
    body_resource = BodyResource(
        name=access_path.name,
        full_path=access_path.path.path
    )
    return ResponseProducer(request_id=request_id,
                            resource_reference=body_resource,
                            naming_convention=naming_convention,
                            primitive_type=primitive_type)


# createHeaderResponseProducer
def create_header_response_producer(request_id, header_parameter_name, naming_convention, primitive_type):
    """
    Creates a ResponseProducer instance based on a header parameter.

    Parameters:
        request_id: The ID of the request.
        header_parameter_name: The name of the header parameter.
        naming_convention: Optional naming convention.
        primitive_type: The primitive type.

    Returns:
        ResponseProducer instance.
    """
    header_resource = HeaderResource(header_parameter_name)

    return ResponseProducer(request_id=request_id,
                            resource_reference=header_resource,
                            naming_convention=naming_convention,
                            primitive_type=primitive_type)


# Given an annotation, create an input-only producer for the specified producer.
def create_input_only_producer_from_annotation(annotation: ProducerConsumerAnnotation,
                                               path_consumers,
                                               query_consumers,
                                               body_consumers,
                                               header_consumers):
    def find_consumer(candidate_consumers, resource_name):
        """
        Find a consumer matching a specific resource_name from the list of candidate consumers.

        Parameters:
        - candidate_consumers: List of tuples (req_id, consumer_list)
        - resource_name: The name of the resource to match
        - consumers: A collection of consumer objects
        - producer_id: The ID of the producer to locate in candidate_consumers

        Returns:
        - The matching consumer object if found, otherwise None
        """
        # Step 1: Search for the producer_id in candidate_consumers
        for req_id, consumer_list in candidate_consumers:
            if req_id == annotation.producer_id:
                logger.write_to_main(f"req_id={req_id.__dict__()}, producer_id={annotation.producer_id.__dict__()}",
                                     ConfigSetting().LogConfig.dependencies)
                # Step 2: Iterate over the consumer list
                for consumer in consumer_list:
                    if consumer.consumer_id.resource_name == resource_name:
                        return consumer
                # If no consumer with the resource_name is found in this group, continue the loop
                break

        # If no matching consumer is found, return None
        return None

    logger.write_to_main(f"annotation={annotation.__dict__()}", ConfigSetting().LogConfig.dependencies)
    if annotation.producer_parameter.resource_name:
        rn = annotation.producer_parameter.resource_name
        if f"{{{rn}}}" in annotation.producer_id.endpoint:
            parameter_kind = ParameterKind.Path
            consumer = find_consumer(path_consumers, rn)
        else:
            query_consumer = find_consumer(query_consumers, rn)
            if query_consumer:
                parameter_kind = ParameterKind.Query
                consumer = query_consumer
            else:
                parameter_kind = ParameterKind.Header
                consumer = find_consumer(header_consumers, rn)

        if not consumer:
            return None, None

        input_only_producer = InputOnlyProducer(request_id=consumer.consumer_id.request_id,
                                                resource_reference=consumer.consumer_id.resource_reference,
                                                naming_convention=consumer.consumer_id.naming_convention,
                                                primitive_type=consumer.consumer_id.primitive_type,
                                                parameter_kind=parameter_kind)

        return rn, input_only_producer

    elif annotation.producer_parameter.resource_path:
        access_path = annotation.consumer_parameter.resource_path
        logger.write_to_main(f"access_path={access_path}", ConfigSetting().LogConfig.dependencies)
        for req_id, consumers in body_consumers:
            logger.write_to_main(f"req_id={req_id.__dict__()}, "
                                 f"annotation.producer_id={annotation.producer_id.__dict__()}",
                                 ConfigSetting().LogConfig.dependencies)
            for body_consumer in consumers:
                logger.write_to_main(f"body_consumer.consumer_id.get_access_path_parts="
                                     f"{body_consumer.consumer_id.access_path_parts}",
                                     ConfigSetting().LogConfig.dependencies)
                if body_consumer.consumer_id.access_path_parts == access_path:
                    logger.write_to_main(f"body_consumer.consumer_id.get_access_path_parts="
                                         f"{body_consumer.consumer_id.access_path_parts}",
                                         ConfigSetting().LogConfig.dependencies)
                    if body_consumer.annotation is not None:
                        resource_name = body_consumer.annotation.producer_parameter.resource_path.get_name_part()
                        resource_access_path = body_consumer.annotation.producer_parameter.resource_path
                        logger.write_to_main(f"resource_name={resource_name} "
                                             f"resource_access_path={resource_access_path}",
                                             ConfigSetting().LogConfig.dependencies)
                        resource_reference = BodyResource(name=resource_name, full_path=resource_access_path.path)
                        input_only_producer = (
                            InputOnlyProducer(request_id=body_consumer.annotation.producer_id,
                                              resource_reference=resource_reference,
                                              naming_convention=body_consumer.consumer_id.naming_convention,
                                              primitive_type=body_consumer.consumer_id.primitive_type,
                                              parameter_kind=ParameterKind.Body))
                        if body_consumer.annotation.producer_parameter.resource_name is not None:
                            return body_consumer.annotation.producer_parameter.resource_name, input_only_producer
                        elif body_consumer.annotation.producer_parameter.resource_path is not None:
                            return (body_consumer.annotation.producer_parameter.resource_path.get_name_part(),
                                    input_only_producer)
                    else:
                        return None, None
        return None, None
    else:
        return None, None


def get_create_or_update_producer(consumer: Consumer,
                                  dictionary,
                                  producers: Producers,
                                  consumer_resource_name,
                                  producer_parameter_name,
                                  path_parameter_index,
                                  bracketed_consumer_resource_name: str):
    def match_producer(producer_param_name, producer_endpoint_name):
        return producers.get_indexed_by_endpoint_producers(producer_param_name, producer_endpoint_name)

    # Find the producer endpoint
    consumer_endpoint = consumer.consumer_id.request_id.endpoint
    producer_endpoint = consumer_endpoint[:path_parameter_index + len(bracketed_consumer_resource_name) + 1]
    logger.write_to_main(f"consumer_endpoint={consumer_endpoint}, producer_endpoint={producer_endpoint}",
                         ConfigSetting().LogConfig.dependencies)
    # Pattern with ending path parameter - the producer
    if (consumer_endpoint == producer_endpoint and
            consumer.consumer_id.request_id.method.lower() == OperationMethod.Put.lower()):
        # WARNING: the code below creates an uuid suffix, but does not check that a dynamic object is
        # actually produced by the response.  The reasoning for this is that, if no dynamic object is
        # found, then it is possible one is not produced and resources will not be leaked.
        # If this turns out not to be the case, a fix is to check that the producer parameter name
        # exists (similar to the check in the 'else' branch below), and only use an uuid suffix if found, otherwise
        # use a static value.
        dictionary, suffix_producer = add_uuid_suffix_entry_for_consumer(consumer_resource_name, dictionary,
                                                                         consumer.consumer_id)
        logger.write_to_main(f"suffix_producer={suffix_producer}", ConfigSetting().LogConfig.dependencies)
        # The producer is a dictionary payload.  The code below makes sure the new dictionary is correctly
        # updated above for this resource.
        return dictionary, suffix_producer
    else:
        # Find the corresponding PUT request, which is the producer, if it exists.
        if path_parameter_index < 1:
            raise Exception("This heuristic should only execute for path parameters.")

        # When the naming convention is not strictly compliant to the OpenAPI spec guidelines,
        # the name of the producer may be omitted from the path, e.g.
        # PUT /slots/{slot} returning a response with "id" or "name" as the dynamic object, instead of
        # more strict /slots/slotId returning "id".
        # Use the above heuristic when the inferred producer resource name is not present.
        inferred_resource_name_producers = match_producer(producer_parameter_name, producer_endpoint)
        logger.write_to_main(f"inferred_resource_name_producers={inferred_resource_name_producers}",
                             ConfigSetting().LogConfig.dependencies)
        possible_producers = []
        if not inferred_resource_name_producers:
            common_producer_names = ["id", "name"]
            for name in common_producer_names:
                for producer in match_producer(name, producer_endpoint):
                    possible_producers.append(producer)
        else:
            possible_producers = inferred_resource_name_producers

        # HACK: sort the producers by increasing access path length.
        # This will fix a particular case in logic apps.
        # The proper way for users to fix this
        # is to provide an exact path-based annotation.
        resource_producer = None
        if possible_producers is None:
            raise (Exception("Invalid case"))
        else:
            if len(possible_producers) > 0:
                sorted_producers = sorted(
                    possible_producers,
                    key=lambda p: len(p.resource_reference.get_access_path())
                    if p.resource_reference.get_access_path() else None
                )
                resource_producer = sorted_producers[0]
                # todo issue fix test_dependencies_inferred_for_lowercase_container_and_object just because there are
                # two producers "Get" and "Put". Try to use Put producers based on sort by method.
                if len(possible_producers) > 1:
                    backup_resource_producer = sorted_producers[1]
                    from compiler.dependency_analysis_types import sort_by_method
                    if (resource_producer.resource_reference.get_access_path() is not None and
                        backup_resource_producer.resource_reference.get_access_path() is not None) or (
                            len(resource_producer.resource_reference.get_access_path()) ==
                            len(backup_resource_producer.resource_reference.get_access_path())):
                        if sort_by_method(sorted_producers[0]) > sort_by_method(sorted_producers[1]):
                            resource_producer = sorted_producers[1]

        for item in possible_producers:
            logger.write_to_main(f"item={item.__dict__()}", ConfigSetting().LogConfig.dependencies)
        return dictionary, resource_producer


# getSameBodyInputProducer
def get_same_body_input_producer(consumer: Consumer,
                                 producers: Producers):
    """
    Determines the same body input producer for a given consumer.

    Args:
        consumer (Consumer): The consumer object.
        dictionary (dict): A dictionary to be updated with the producer information.
        producers (Producers): A collection of producers.

    Returns:
        tuple: Updated dictionary and the matched producer (if any).
    """

    def is_self_referencing():
        return p.id.get_parent_access_path() == consumer.consumer_id.access_path_parts

    consumer_resource_name = consumer.consumer_id.resource_name
    producer_resource_name = "name"

    if consumer.parameter_kind == ParameterKind.Body and consumer_resource_name == "id":
        # ID is passed at the root of the payload in a PUT statement, nothing to do.
        producer = None
        if consumer.consumer_id.body_container_name is not None:
            candidate_input_producers = producers.get_same_payload_producers(producer_resource_name,
                                                                             consumer.consumer_id.request_id)

            for p in candidate_input_producers:
                if p.container_name is None:
                    raise ValueError("The producer container must always exist in same payload producers.")

                if p.request_id.endpoint != consumer.consumer_id.request_id.endpoint:
                    raise ValueError(
                        f"The endpoints should be identical: producer: {p.id.request_id.endpoint} "
                        f"consumer: {consumer.consumer_id.request_id.endpoint}")

                matching_producer_type_names = [consumer_name
                                                for consumer_name in consumer.consumer_id.candidate_type_names
                                                if consumer_name in p.candidate_type_names]
                # Use the longest matching word
                matching_producer_type_names.sort(key=len, reverse=True)

                matching_type_name = next(iter(matching_producer_type_names))

                if matching_type_name is not None:
                    # Heuristic: only infer a producer if it is higher in the tree than the consumer
                    # This helps avoid incorrectly assigned producers from child properties of
                    # this payload
                    is_producer_higher = (len(p.access_path_parts.path) <
                                          len(consumer.consumer_id.access_path_parts.path))
                    if is_producer_higher and not is_self_referencing():
                        producer = (matching_type_name, p)

        return producer if producer else None

    else:
        return None


# Gets the producer for a consumer that is a nested object ID, as follows:
# { "Subnet": { "id" : <dynamic object> } }
# For each property of a body parameter that has a parent object, this
# function searches for a request with an endpoint that has the
# parent object name as a prefix of its container.
# For example, for the above subnet id, the matching producer
# will be /api/subnets/{subnetName}.
# When several matches are found, the shortest endpoint is chosen.
def get_nested_object_producer(consumer: Consumer,
                               producers: Producers,
                               producer_parameter_name,
                               allow_get_producers):
    if consumer.consumer_id.container_name is None:
        return None

    # Find producers with container name whose type matches the consumer parent type.
    # Example 1: a path container
    # with the same primary name (without suffix), e.g. 'virtualNetworks/{virtualNetworkName}'
    # Example 2: a body
    # container where the path is a valid producer relative to the current path. e.g. PUT /some/resource that returns
    # { ... 'virtualNetwork' : { 'id' : ...}}
    def find_matching_producers(type_names):
        matching_producers = []
        for type_name in type_names:
            producers_by_type = producers.get_indexed_by_type_name_producers(producer_parameter_name, type_name)
            matching_producers.extend([p for p in producers_by_type if
                                       not p.is_nested_body_resource and p.request_id.method in [
                                           OperationMethod.Put, OperationMethod.Post]])

        endpoints_count = len(set([p.request_id.endpoint for p in matching_producers]))
        return matching_producers, endpoints_count

    logger.write_to_main(f"consumer.consumer_id.candidate_type_names[0]="
                         f"{consumer.consumer_id.candidate_type_names[0]}",
                         ConfigSetting().LogConfig.dependencies)
    exact_matching_producers, exact_matching_producer_endpoints_count = find_matching_producers(
        [consumer.consumer_id.candidate_type_names[0]])
    logger.write_to_main(f"exact_matching_producers={exact_matching_producers}",
                         ConfigSetting().LogConfig.dependencies)
    # In some cases, multiple matches may be found (including the current endpoint+method)
    # This may cause circular dependencies if the other requests also consume the same object
    # (for example, multiple requests have a 'VirtualNetwork' type parameter, which is
    # also returned in the response, but is pre-provisioned by a separate API).
    # When multiple POST or PUT matches exist (possibly including the current request),
    # do not assign a dependency because whether a new dynamic object is being created
    # cannot be reliably determined (and arbitrarily breaking cycles is more confusing).
    # Note: when GET producers are used, this is not an issue because the body of a GET will not
    # contain consumers of this resource type.
    candidate_producers = None
    if exact_matching_producer_endpoints_count == 0:
        approximate_producers, approximate_producer_endpoints_count = find_matching_producers(
            consumer.consumer_id.candidate_type_names[1:])
        if approximate_producer_endpoints_count == 1:
            candidate_producers = approximate_producers
    elif exact_matching_producer_endpoints_count == 1:
        candidate_producers = exact_matching_producers
    logger.write_to_main(f"candidate_producers={candidate_producers}",
                         ConfigSetting().LogConfig.dependencies)
    if candidate_producers:
        filtered_producers = [p for p in candidate_producers if is_valid_producer(p, consumer, allow_get_producers)]
        logger.write_to_main(f"filtered_producers={filtered_producers}", ConfigSetting().LogConfig.dependencies)
        return filtered_producers[0] if filtered_producers else None
    else:
        return None


# Find producer given a candidate producer resource name
# Returns a producer matching the specified consumer.
# May also return an updated dictionary.
# findProducerWithResourceName
def find_producer_with_resource_name(producers: Producers,
                                     consumer: Consumer,
                                     dictionary: MutationsDictionary,
                                     allow_get_producers: bool,
                                     per_request_dictionary: MutationsDictionary,
                                     producer_parameter_name: str):
    consumer_resource_name = consumer.consumer_id.resource_reference.get_resource_name()
    consumer_endpoint = consumer.consumer_id.request_id.endpoint

    # bracketed_consumer_resource_name = consumer_resource_name
    # if consumer.parameter_kind == ParameterKind.Path else None
    if consumer.parameter_kind == ParameterKind.Path:
        bracketed_consumer_resource_name = f"{{{consumer_resource_name}}}"
    else:
        bracketed_consumer_resource_name = None

    logger.write_to_main(f"enter  producer_parameter_name={producer_parameter_name}\n"
                         f"consumer_resource_name={consumer_resource_name}\n"
                         f"consumer_endpoint={consumer_endpoint}\n"
                         f"bracketed_consumer_resource_name={bracketed_consumer_resource_name}"
                         f"allow_get_producers={allow_get_producers}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    logger.write_to_main(f"restler_custom_payload={dictionary.restler_custom_payload}, "
                         f"restler_custom_payload_uuid4_suffix={dictionary.restler_custom_payload_uuid4_suffix}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    logger.write_to_main(f"producers={producers.__dict__()}", ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    # path_parameter_index = consumer_endpoint.index(
    #    bracketed_consumer_resource_name) if bracketed_consumer_resource_name else None
    if bracketed_consumer_resource_name:
        path_parameter_index = consumer_endpoint.find(bracketed_consumer_resource_name)
    else:
        path_parameter_index = None

    producer_endpoint = None
    producer_container = None
    if consumer.parameter_kind == ParameterKind.Path:
        # Search according to the path
        # producerEndpoint contains everything including the container
        if path_parameter_index is not None:
            if path_parameter_index == 0:
                raise Exception("Invalid Swagger Endpoint")
            else:
                producer_endpoint = consumer_endpoint[:path_parameter_index - 1]  # Subtract one to remove the slash
        # We need to find the container (here, "accounts") to filter a particular API structure that does not
        # fully conform to the OpenAPI spec (see below).
        producer_container = producer_endpoint.split('/')[-1] if producer_endpoint else None

        logger.write_to_main(f"producer_container={producer_container}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    logger.write_to_main(f"path_parameter_index={path_parameter_index}, "
                         f"producer_endpoint={producer_endpoint} producer_container={producer_container}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    # The logic below guards against including cases where the container returns a
    # matching field which belongs to a different class. For example, imagine
    # the following problematic path: dnsZones/{zoneName}/{recordType} and that
    # we are looking for "recordType", i.e., "type". This field should ideally
    # be in the following container "dnsZones/{zoneName}/records/. However,
    # because the structure is strange, without the following check, we will
    # match a field named "type" returned by  dnsZones/{zoneName} which will
    # be a zone type and not a record-type.
    # accounts starts with 'account'
    matching_resource_producers, matching_resource_producers_by_endpoint = [], []
    if producer_container and not producer_container.startswith("{"):
        matching_resource_producers = producers.get_sorted_by_match_producers(producer_parameter_name,
                                                                              True),
        logger.write_to_main(f"matching_resource_producers={matching_resource_producers}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        if producer_endpoint:
            matching_resource_producers_by_endpoint = (producers.get_indexed_by_endpoint_producers(
                producer_resource_name=producer_parameter_name, endpoint=producer_endpoint))
            logger.write_to_main(
                f"len(matching_resource_producers_by_endpoint)={len(matching_resource_producers_by_endpoint)}",
                ConfigSetting().LogConfig.dependencies or
                ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    annotation_producer = None

    if consumer.annotation:
        annotation_producer_resource_name = None
        ann = consumer.annotation
        producer_parameter = ann.producer_parameter
        if producer_parameter:
            if producer_parameter.resource_name is not None:
                annotation_producer_resource_name = producer_parameter.resource_name
                logger.write_to_main(f"annotation_producer_resource_name={annotation_producer_resource_name}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            elif producer_parameter.resource_path is not EmptyAccessPath:
                annotation_producer_resource_name = producer_parameter.resource_path.get_path_property_name_parts()
                logger.write_to_main(f"annotation_producer_resource_name={annotation_producer_resource_name}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                if annotation_producer_resource_name is not None:
                    annotation_producer_resource_name = \
                        annotation_producer_resource_name[len(annotation_producer_resource_name) - 1]
        response_producers_with_matching_resource_ids = []
        logger.write_to_main(f"annotation_producer_resource_name={annotation_producer_resource_name}, "
                             f"ann.producer_id.endpoint={ann.producer_id.endpoint}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        # Get response producers with matching resource IDs
        if annotation_producer_resource_name:
            # When the annotation has a path, the producer can be matched exactly
            # TODO: an unnamed resource, such as an array element, cannot be currently assigned as a producer, because
            # its name will be the array name.
            response_producers_with_matching_resource_ids = producers.get_indexed_by_endpoint_producers(
                annotation_producer_resource_name, ann.producer_id.endpoint)
            logger.write_to_main(f"response_producers_with_matching_resource_ids="
                                 f"{response_producers_with_matching_resource_ids}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        annotation_response_producer = None
        # Match on the path, if it exists,
        # otherwise match on the ID only
        for rp in response_producers_with_matching_resource_ids:
            if is_valid_producer(rp, consumer, allow_get_producers):
                logger.write_to_main(f"rp={rp.__dict__()}\n, rp.request_id={rp.request_id.__dict__()}"
                                     f"ann.producer_id={ann.producer_id.__dict__()}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                if rp.request_id == ann.producer_id:
                    logger.write_to_main(f"ann.producer_parameter.resource_path="
                                         f"{ann.producer_parameter.resource_path}",
                                         ConfigSetting().LogConfig.dependencies or
                                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                    if producer_parameter.resource_path is EmptyAccessPath:
                        resource_name = "/".join(rp.access_path_parts.path) if rp.access_path is not None else ""
                        logger.write_to_main(f"resource_name={resource_name}\n"
                                             f"resource_name={ann.producer_parameter.resource_name}",
                                             ConfigSetting().LogConfig.dependencies or
                                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                        if resource_name == producer_parameter.resource_name:
                            annotation_response_producer = rp
                    else:
                        logger.write_to_main(f"rp.access_path_parts={rp.access_path_parts}\n"
                                             f"ann.producer_parameter.resource_path={ann.producer_parameter.resource_path}",
                                             ConfigSetting().LogConfig.dependencies or
                                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                        if producer_parameter.resource_path == rp.access_path_parts:
                            annotation_response_producer = rp
        logger.write_to_main(f"annotation_response_producer={annotation_response_producer}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        response_producers = None

        # Handle matching producer
        if annotation_response_producer is not None:
            if ann.except_consumer_id is None or consumer.consumer_id.request_id not in ann.except_consumer_id:
                response_producers = ResponseProducer(
                    request_id=annotation_response_producer.request_id,
                    resource_reference=annotation_response_producer.resource_reference,
                    naming_convention=annotation_response_producer.naming_convention,
                    primitive_type=annotation_response_producer.primitive_type)

        logger.write_to_main(f"response_producers={response_producers}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        # Check for input-only producers if there are no response producers
        input_only_producer = None
        if response_producers is None:
            matching_input_only_producers = []
            if annotation_producer_resource_name is not None:
                matching_input_only_producers = producers.get_input_only_producers(
                    annotation_producer_resource_name
                )
                logger.write_to_main(f"matching_input_only_producers={matching_input_only_producers}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            # Filter input-only producers
            annotation_producer = None
            for rp in matching_input_only_producers:
                if ann.producer_parameter is not None:
                    if rp.request_id == ann.producer_id:
                        logger.write_to_main(f"ann.producer_parameter.resource_path="
                                             f"{ann.producer_parameter.resource_path}",
                                             ConfigSetting().LogConfig.dependencies or
                                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                        if producer_parameter.resource_path is EmptyAccessPath:
                            resource_name = rp.resource_reference.get_resource_name() \
                                if rp.resource_reference.get_resource_name() is not None else ""
                            logger.write_to_main(f"resource_name={resource_name}"
                                                 f"ann.producer_parameter.resource_name="
                                                 f"{ann.producer_parameter.resource_name}",
                                                 ConfigSetting().LogConfig.dependencies or
                                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                            if resource_name == producer_parameter.resource_name:
                                annotation_producer = rp
                        else:
                            logger.write_to_main(f"rp.access_path_parts={rp.access_path_parts}"
                                                 f"producer_parameter.resource_path={producer_parameter.resource_path}",
                                                 ConfigSetting().LogConfig.dependencies or
                                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                            if producer_parameter.resource_path == rp.access_path_parts:
                                annotation_producer = rp

            logger.write_to_main(f"annotation_producer={annotation_producer}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

            # Handle matching input-only producer
            if annotation_producer is not None:
                if ann.except_consumer_id is None or consumer.consumer_id.request_id not in ann.except_consumer_id:
                    input_only_producers = [annotation_producer]
                    logger.write_to_main(f"input_only_producers={input_only_producers}",
                                         ConfigSetting().LogConfig.dependencies or
                                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                    # Determine dictionary and input-only producer
                    if input_only_producers:
                        iop = input_only_producers[0]
                        # Read the value - no associated dictionary payload
                        input_only_producer = InputParameter(iop, None, False)
                        logger.write_to_main(f"input_only_producer={input_only_producer}",
                                             ConfigSetting().LogConfig.dependencies or
                                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        # Combine response producers and input-only producer
        all_producers = []
        if response_producers is not None:
            all_producers.append(response_producers)
        if input_only_producer is not None:
            all_producers.append(input_only_producer)
        annotation_producer = all_producers[0] if all_producers else None
        logger.write_to_main(f"annotation_producer={annotation_producer}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    logger.write_to_main(f"annotation_producer={annotation_producer}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    dictionary_matches = []
    # TODO: error handling.  only one should match.
    if per_request_dictionary:
        per_request_dictionary_matches = per_request_dictionary.get_parameter_for_custom_payload(
            consumer.consumer_id.resource_name,
            consumer.consumer_id.access_path_parts,
            consumer.consumer_id.primitive_type,
            consumer.parameter_kind) if per_request_dictionary else []
        dictionary_matches.extend(per_request_dictionary_matches)
        logger.write_to_main(f"per_request_dictionary_matches={per_request_dictionary_matches}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    global_dictionary_matches = dictionary.get_parameter_for_custom_payload(
        consumer_resource_name=consumer.consumer_id.resource_name,
        access_path_parts=consumer.consumer_id.access_path_parts,
        primitive_type=consumer.consumer_id.primitive_type,
        parameter_kind=consumer.parameter_kind)
    dictionary_matches.extend(global_dictionary_matches)
    logger.write_to_main(f"global_dictionary_matches={global_dictionary_matches}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    uuid_suffix_dictionary_matches = []
    # TODO: error handling.  only one should match.
    if per_request_dictionary:
        per_request_uuid_suffix_matches = per_request_dictionary.get_parameter_for_custom_payload_uuid_suffix(
            consumer.consumer_id.resource_name, consumer.consumer_id.access_path_parts,
            consumer.consumer_id.primitive_type) if per_request_dictionary else []
        if per_request_uuid_suffix_matches:
            uuid_suffix_dictionary_matches.append(per_request_uuid_suffix_matches)
        logger.write_to_main(f"per_request_uuid_suffix_matches={per_request_uuid_suffix_matches}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    global_uuid_suffix_matches = dictionary.get_parameter_for_custom_payload_uuid_suffix(
        consumer.consumer_id.resource_name,
        consumer.consumer_id.access_path_parts,
        consumer.consumer_id.primitive_type)
    if global_uuid_suffix_matches is not None:
        uuid_suffix_dictionary_matches.append(global_uuid_suffix_matches)
        logger.write_to_main(f"global_uuid_suffix_matches={global_uuid_suffix_matches} ",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    # Check if this consumer is a writer for an input-only producer.
    # If yes, this information must be added to the dictionary matches (if any).
    input_producer_matches = []
    if annotation_producer is not None:
        # Find the input-only producer corresponding to this consumer
        matching_input_only_producers = producers.get_input_only_producers(consumer.consumer_id.resource_name)
        logger.write_to_main(f"matching_input_only_producers={matching_input_only_producers} "
                             f"resource_name={consumer.consumer_id.resource_name}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        input_only_producers = [p for p in matching_input_only_producers if
                                p.request_id == consumer.consumer_id.request_id
                                and p.resource_reference == consumer.consumer_id.resource_reference]
        if input_only_producers:
            iop = input_only_producers[0]
            logger.write_to_main(f"dictionary_matches={dictionary_matches}, "
                                 f"uuid_suffix_dictionary_matches={uuid_suffix_dictionary_matches}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name or True)
            for p in dictionary_matches + uuid_suffix_dictionary_matches:
                # Add the dictionary payload
                if isinstance(p, DictionaryPayload):
                    input_producer_matches.append(InputParameter(iop, p, True))
                    break
                else:
                    # By default, create a custom_payload_uuid_suffix, so a different ID will be
                    # generated each time the value is written.
                    # TODO: This logic will only work for string types (e.g. names).
                    #  It does not currently work for other types that
                    # need a unique value assigned (e.g. GUIDs and integers).
                    # Once a type is introduced for unique GUIDs and integers,
                    # this logic should be modified to create an
                    # appropriate dictionary entry that will direct RESTler to automatically generate unique values.
                    #
                    # If a dictionary payload is not returned below,
                    # a fuzzable payload will be generated as usual, and the
                    # fuzzed value will be assigned to the producer (writer variable).
                    if consumer.consumer_id.primitive_type == PrimitiveType.String:
                        dictionary, suffix_producer = add_uuid_suffix_entry_for_consumer(consumer_resource_name,
                                                                                         dictionary,
                                                                                         consumer.consumer_id)
                        if isinstance(suffix_producer, DictionaryPayload):
                            dictionary_payload = suffix_producer
                            input_producer_matches.append(InputParameter(iop, dictionary_payload, True))
                        else:
                            raise ValueError("A suffix entry must be a dictionary payload")
                    else:
                        input_producer_matches.append(InputParameter(iop, None, True))

    # Here the producers just match on the resource name.  If the container also matches,
    # it will match fully.
    inferred_exact_matches = [p for p in matching_resource_producers_by_endpoint if
                              is_valid_producer(p, consumer, allow_get_producers)]
    for item in inferred_exact_matches:
        logger.write_to_main(f"inferred_exact_matches={item.__dict__()}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    inferred_approximate_matches = []
    for item in matching_resource_producers:
        for p in item:
            if not p.producer.request_id.endpoint.strip():
                continue
            # Everything up to the next dependency
            # e.g. producerEndpoint = "/api/webhooks/account/{accountId}/blah/id"
            # look for /api/webhooks/account/{accountId}/blah, /api/webhooks/account/{accountId}

            logger.write_to_main(f"p.request_id.endpoint={p.producer.request_id.endpoint}, "
                                 f"consumer_endpoint={consumer_endpoint} ",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            logger.write_to_main(f"producer_endpoint.startswith(p.producer.request_id.endpoint)="
                                 f"{producer_endpoint.startswith(p.producer.request_id.endpoint)}  ",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            # Check producer match
            endpoint_matches = consumer_endpoint.startswith(p.producer.request_id.endpoint)
            # endpoint_matches = producer_endpoint.startswith(p.producer.request_id.endpoint)
            if not producer_endpoint or not endpoint_matches:
                continue
            no_additional_path_params = producer_endpoint.replace(p.producer.request_id.endpoint, "")
            logger.write_to_main(f"replace={producer_endpoint.replace(p.producer.request_id.endpoint, '')} ",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            if "{" in no_additional_path_params:
                if p.producer.resource_name != producer_parameter_name:
                    continue

            if p.producer.resource_name != producer_parameter_name:
                continue
            logger.write_to_main(f"resource_name={p.producer.resource_name} "
                                 f"producer_parameter_name={producer_parameter_name}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
            # Check container match
            logger.write_to_main(f"isinstance(p.producer.resource_reference, BodyResource)="
                                 f"{isinstance(p.producer.resource_reference, BodyResource)} "
                                 f"producer_container={producer_container}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

            if isinstance(p.producer.resource_reference, BodyResource) and producer_container is not None:

                logger.write_to_main(f"p.producer.container_name ={p.producer.container_name} ="
                                     f"producer_container={producer_container}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                if p.producer.container_name == producer_container:
                    valid_producer = is_valid_producer(p.producer, consumer, allow_get_producers)
                    logger.write_to_main(f"valid_producer={valid_producer}",
                                         ConfigSetting().LogConfig.dependencies or
                                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                    # Check if the producer is valid
                    if valid_producer:
                        inferred_approximate_matches.append(p.producer)
                        for item in inferred_approximate_matches:
                            # Check producer match
                            logger.write_to_main(f"inferred_approximate_matches={item.__dict__()}",
                                                 ConfigSetting().LogConfig.dependencies or
                                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    # Check for special case: PUT request that is both a producer and a consumer.
    # Conditions:
    # 1. There are no exact, annotation or dictionary matches (if there are, they should not be overridden).
    # 2. The consumer endpoint ends with 'consumerResourceName'.
    # 3. There is no POST request in exact producer matches.
    # 4. The consumer is a PUT request or there exists a PUT request with the same endpoint id.
    # Note: it's possible that a PUT parameter is specified in the body.
    # This case is not handled here, as it is not obvious which body parameter to use in such cases.
    producer = None
    logger.write_to_main(f"put_request ={consumer.parameter_kind == ParameterKind.Path
                                         and annotation_producer is None
                                         and not global_dictionary_matches and not inferred_exact_matches}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    if (consumer.parameter_kind == ParameterKind.Path
            and annotation_producer is None
            and not global_dictionary_matches and not inferred_exact_matches):
        logger.write_to_main(f"consumer_resource_name={consumer_resource_name}, "
                             f"producer_parameter_name={producer_parameter_name} "
                             f"path_parameter_index={path_parameter_index} "
                             f"bracketed_consumer_resource_name={bracketed_consumer_resource_name}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        new_dictionary, producer = get_create_or_update_producer(consumer,
                                                                 dictionary,
                                                                 producers,
                                                                 consumer_resource_name,
                                                                 producer_parameter_name,
                                                                 path_parameter_index,
                                                                 bracketed_consumer_resource_name)
        logger.write_to_main(f"producer={producer}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        if producer is not None:
            if isinstance(producer, ResponseProducer):
                if (producer.request_id.method == OperationMethod.Patch
                        or producer.request_id == consumer.consumer_id.request_id):
                    producer = None
            else:
                if input_producer_matches:
                    input_producer = input_producer_matches[0]  # Get the first match (equivalent to `Seq.tryHead`)
                    if isinstance(input_producer, InputParameter) and input_producer.is_writer:
                        if producer and isinstance(producer, DictionaryPayload):
                            # 'isWriter' should always be true (this case only applies to producer variables).
                            producer = InputParameter(producer=input_producer_matches[0].input_only_producer,
                                                      dictionary_payload=producer,
                                                      is_writer=True)
        logger.write_to_main(f"producer={producer}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    if producer is None:
        # Try to find a producer based on the container property name of the consumer in the body.
        if (consumer.consumer_id.access_path is not None and annotation_producer is None and not dictionary_matches
                and not any(
                    p.request_id.method in [OperationMethod.Put, OperationMethod.Post] for p in
                    inferred_exact_matches)):
            # If there is a dictionary entry for a static value, it should override the inferred dependency
            producer = get_nested_object_producer(consumer, producers, producer_parameter_name, allow_get_producers)
            logger.write_to_main(f"producer={producer}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

    if producer is None:
        producers_to_check = []
        if input_producer_matches is not None and len(input_producer_matches) > 0:
            producers_to_check = producers_to_check + input_producer_matches
            logger.write_to_main(f"input_producer_matches: producers_to_check={input_producer_matches}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        if annotation_producer is not None:
            producers_to_check.append(annotation_producer)
            logger.write_to_main(f"annotation_producer: producers_to_check={annotation_producer}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        if dictionary_matches is not None and len(dictionary_matches):
            producers_to_check = producers_to_check + dictionary_matches
            logger.write_to_main(f"dictionary_matches: producers_to_check={dictionary_matches}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        if uuid_suffix_dictionary_matches is not None and len(uuid_suffix_dictionary_matches):
            producers_to_check = producers_to_check + uuid_suffix_dictionary_matches
            for item in uuid_suffix_dictionary_matches:
                logger.write_to_main(f"uuid_suffix_dictionary_matches: producers_to_check={item.__dict__}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        if inferred_exact_matches is not None and len(inferred_exact_matches):
            producers_to_check = producers_to_check + inferred_exact_matches
            logger.write_to_main(f"inferred_exact_matches: producers_to_check={inferred_exact_matches}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)

        if inferred_approximate_matches is not None and len(inferred_approximate_matches):
            producers_to_check = producers_to_check + inferred_approximate_matches
            logger.write_to_main(f"inferred_approximate_matches: producers_to_check={inferred_approximate_matches}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        logger.write_to_main(f"Exit  producers_to_check={producers_to_check}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        return dictionary, producers_to_check
    else:
        logger.write_to_main(f"producer={producer}",
                             ConfigSetting().LogConfig.dependencies or
                             ConfigSetting().LogConfig.log_find_producer_with_resource_name)
        return dictionary, [producer]


def find_annotation(global_annotations: List[ProducerConsumerAnnotation],
                    link_annotations: List[ProducerConsumerAnnotation],
                    local_annotations: List[ProducerConsumerAnnotation],
                    consumer_id: ApiResource):
    found_global_annotation = []
    for a in global_annotations:
        logger.write_to_main(f"global_annotations: {a.__dict__()}", ConfigSetting().LogConfig.dependencies)
        if annotation_matches(a, consumer_id):
            found_global_annotation.append(a)
    logger.write_to_main(f"found_global_annotation={len(found_global_annotation)}",
                         ConfigSetting().LogConfig.dependencies)
    if found_global_annotation is not None and len(found_global_annotation) > 1:
        print("WARNING: found more than one matching annotation. Only the first found will be used.")

    found_local_annotation = []
    if local_annotations is not None:
        for a in local_annotations:
            if annotation_matches(a, consumer_id):
                found_local_annotation.append(a)
        if found_local_annotation is not None and len(found_local_annotation) > 1:
            print("WARNING: found more than one matching annotation. Only the first found will be used.")
    logger.write_to_main(f"found_local_annotation={len(found_local_annotation)}",
                         ConfigSetting().LogConfig.dependencies)
    found_link_annotation = []
    if link_annotations is not None:
        for a in link_annotations:
            if annotation_matches(a, consumer_id):
                found_global_annotation.append(a)
        if found_link_annotation is not None and len(found_link_annotation) > 1:
            print("WARNING: found more than one matching annotation. Only the first found will be used.")
    logger.write_to_main(f"found_link_annotation={len(found_link_annotation)}",
                         ConfigSetting().LogConfig.dependencies)
    # Local annotation takes precedence, then global, then link
    if len(found_local_annotation) > 0:
        return found_local_annotation[0]
    elif len(found_global_annotation) > 0:
        return found_global_annotation[0]
    elif len(found_link_annotation) > 0:
        return found_link_annotation[0]


def find_producer(producers: Producers,
                  consumer: Consumer,
                  dictionary: MutationsDictionary,
                  allow_get_producers: bool,
                  per_request_dictionary: MutationsDictionary):
    possible_producer_parameter_names = [consumer.consumer_id.producer_parameter_name,
                                         consumer.consumer_id.resource_name]
    logger.write_to_main(f"possible_producer_parameter_names={possible_producer_parameter_names}",
                         ConfigSetting().LogConfig.dependencies or
                         ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    possible_producers = []
    for producer_parameter_name in possible_producer_parameter_names:
        mutations_dictionary, producer = find_producer_with_resource_name(producers, consumer, dictionary,
                                                                          allow_get_producers,
                                                                          per_request_dictionary,
                                                                          producer_parameter_name)
        if producer:
            for item in producer:
                # Workaround: prefer a response over a dictionary payload.
                # TODO: this workaround should be removed when the
                # producer-consumer dependency algorithm is improved to process
                # dependencies grouped by paths, rather than independently.

                # fix cases: test_path_and_body_parameter_set_to_same_uuid_suffix_payload in test_dictionary.py.
                # double-checked with two conditions: with dictionary or without  dictionary. finally,
                # the DictionaryPayload is high priority than ResponseProducer
                logger.write_to_main(f"producer={item.__dict__()}",
                                     ConfigSetting().LogConfig.dependencies or
                                     ConfigSetting().LogConfig.log_find_producer_with_resource_name)
                if isinstance(item, ResponseProducer):
                    # if isinstance(item, DictionaryPayload):
                    possible_producers.insert(0, (mutations_dictionary, item))
                else:
                    possible_producers.append((mutations_dictionary, item))
            logger.write_to_main(f"producer={possible_producers}",
                                 ConfigSetting().LogConfig.dependencies or
                                 ConfigSetting().LogConfig.log_find_producer_with_resource_name)
    if possible_producers:
        return possible_producers[0][0], possible_producers[0][1]
    else:
        return dictionary, None


# Define PropertyAccessPath as a namedtuple
class PropertyAccessPaths:
    name: str
    path: AccessPath
    primitive_type: PrimitiveType

    def __init__(self, name, path, primitive_type):
        self.name = name
        self.path = path
        self.primitive_type = primitive_type

    @staticmethod
    def get_leaf_property_access_path(property_name) -> list:
        if not property_name or property_name.isspace():
            return []
        else:
            return [property_name]

    @staticmethod
    def get_inner_property_access_path_parts(inner_property: InnerProperty):
        logger.write_to_main(f"inner_property={inner_property.__dict__()}", ConfigSetting().LogConfig.dependencies)
        if not inner_property.name or inner_property.name.isspace():
            name_part = []
        else:
            name_part = [inner_property.name]

        if inner_property.property_type == PrimitiveType.Array:
            array_element_part = ["[0]"]
        else:
            array_element_part = []

        return name_part + array_element_part

    @staticmethod
    def get_inner_property_access_path(inner_property) -> AccessPath:
        path_parts = PropertyAccessPaths.get_inner_property_access_path_parts(inner_property)
        if len(path_parts) == 0:
            return EmptyAccessPath
        else:
            return AccessPath(path_parts)

    @staticmethod
    def get_leaf_access_path(parent_access_path, leaf_property) -> AccessPath:
        leaf_access_path = parent_access_path + PropertyAccessPaths.get_leaf_property_access_path(leaf_property.name)
        if len(leaf_access_path) == 0:
            return EmptyAccessPath
        else:
            return AccessPath(leaf_access_path)

    @staticmethod
    def get_inner_access_path(parent_access_path, inner_property: InnerProperty):
        return parent_access_path + PropertyAccessPaths.get_inner_property_access_path_parts(inner_property)

    @staticmethod
    def get_leaf_access_path_parts(parent_access_path, leaf_property):
        return parent_access_path + PropertyAccessPaths.get_leaf_property_access_path(leaf_property.name)

    @staticmethod
    def get_inner_access_path_parts(parent_access_path, inner_property):
        return parent_access_path + PropertyAccessPaths.get_inner_property_access_path_parts(inner_property)


def annotation_matches(annotation: ProducerConsumerAnnotation,
                       consumer_id: ApiResource):
    logger.write_to_main(f"annotation={annotation.__dict__()}. consumer_id={consumer_id.__dict__()}",
                         ConfigSetting().LogConfig.dependencies)
    consumer_id_matches = annotation.consumer_id is None or annotation.consumer_id == consumer_id.request_id
    consumer_parameter_matches = False
    if annotation.consumer_parameter is not None:
        if consumer_id.access_path is not None:
            consumer_parameter_matches = annotation.consumer_parameter.resource_path == consumer_id.access_path_parts
        elif consumer_id.resource_name != "" and annotation.consumer_parameter.resource_name != "":
            consumer_parameter_matches = (
                    annotation.consumer_parameter.resource_name.lower() == consumer_id.resource_name.lower())
    request_id_matches = (annotation.except_consumer_id is None or
                          consumer_id.request_id not in annotation.except_consumer_id)
    logger.write_to_main(f"consumer_id_matches={consumer_id_matches}, "
                         f"consumer_parameter_matches={consumer_parameter_matches}, "
                         f"request_id_matches={request_id_matches}", ConfigSetting().LogConfig.dependencies)
    return consumer_id_matches and consumer_parameter_matches and request_id_matches


def get_payload_primitive_type(payload):
    if isinstance(payload, Constant):
        return payload.primitive_type
    elif isinstance(payload, Fuzzable):
        if payload.primitive_type == PrimitiveType.Enum:
            return payload.default_value
        else:
            return payload.primitive_type
    elif isinstance(payload, Custom):
        return payload.primitive_type
    elif isinstance(payload, DynamicObject):
        return payload.primitive_type
    elif isinstance(payload, list):
        return PrimitiveType.String


def get_producer(request, response):
    # All possible properties in this response
    access_paths = []

    def visit_leaf(parent_access_path, p):
        resource_access_path = PropertyAccessPaths.get_leaf_access_path_parts(parent_access_path, p)
        name = p.name if p.name else next(
            (elem for elem in reversed(parent_access_path) if elem and not elem.startswith("[")), None)

        access_path = list(resource_access_path)
        logger.write_to_main(f"access_path={access_path}", ConfigSetting().LogConfig.dependencies)
        if name:
            access_paths.append(
                PropertyAccessPaths(name=name,
                                    path=AccessPath(access_path),
                                    primitive_type=get_payload_primitive_type(p.payload)))

            # Check if the item is an array
            if len(access_path) > 1 and access_path[-1] == "[0]":
                logger.write_to_main(f"access_path={access_path}", ConfigSetting().LogConfig.dependencies)
                access_paths.append(PropertyAccessPaths(name=name,
                                                        path=AccessPath(access_path[:-1]),
                                                        primitive_type=get_payload_primitive_type(p.payload)))

    def visit_inner(parent_access_path, p):
        pass

    if request.method in [OperationMethod.Post, OperationMethod.Put, OperationMethod.Patch, OperationMethod.Get]:
        iter_ctx(visit_leaf, visit_inner, PropertyAccessPaths.get_inner_access_path_parts, [], response)

    return access_paths


def get_parameter_dependencies(parameter_kind: ParameterKind,
                               global_annotations: List[ProducerConsumerAnnotation],
                               request_id: RequestId,
                               request_data: RequestData,
                               request_parameter: RequestParameter,
                               naming_convention):
    logger.write_to_main(f"parameter_kind={parameter_kind}, global_annotations={len(global_annotations)}",
                         ConfigSetting().LogConfig.dependencies)
    annotated_requests = None
    link_annotations = None
    if request_data is not None:
        if request_data.local_annotations is not None and len(request_data.local_annotations) > 0:
            annotated_requests = request_data.local_annotations
        if request_data.link_annotations is not None and len(request_data.link_annotations) > 0:
            link_annotations = request_data.link_annotations

    def get_consumer(resource_name, resource_access_path, primitive_type=None):
        if not resource_name:
            raise ValueError("[get_consumer] invalid usage")
        logger.write_to_main(f"resource_name={resource_name}", ConfigSetting().LogConfig.dependencies)
        resource_reference = None

        if parameter_kind == ParameterKind.Header:
            resource_reference = HeaderResource(resource_name)
        elif parameter_kind == ParameterKind.Path:
            path_obj = get_path_from_string(request_id.endpoint, False)
            path_to_parameter = path_obj.get_path_parts_before_parameter(resource_name)
            resource_reference = PathResource(name=resource_name,
                                              path_to_parameter=path_to_parameter,
                                              response_path=EmptyAccessPath)
        elif parameter_kind == ParameterKind.Query:
            resource_reference = QueryResource(resource_name)
        elif parameter_kind == ParameterKind.Body:
            resource_reference = BodyResource(name=resource_name, full_path=resource_access_path)
        default_primitive_type = primitive_type
        if default_primitive_type is None:
            default_primitive_type = PrimitiveType.String

        consumer_id = ApiResource(request_id, resource_reference, naming_convention,
                                  default_primitive_type)
        annotation = find_annotation(global_annotations=global_annotations,
                                     link_annotations=link_annotations,
                                     local_annotations=annotated_requests,
                                     consumer_id=consumer_id)

        return Consumer(consumer_id=consumer_id,
                        annotation=annotation,
                        parameter_kind=parameter_kind)

    def visit_leaf(parent_access_path, p):
        if p.name:
            resource_access_path = PropertyAccessPaths.get_leaf_access_path(parent_access_path, p)
            payload_primitive_type = get_payload_primitive_type(p.payload)
            c = get_consumer(p.name, resource_access_path.path, payload_primitive_type)
            consumer_list.append(c)

    def visit_inner(parent_access_path, p):
        if p.name:
            resource_access_path = PropertyAccessPaths.get_inner_access_path(parent_access_path, p)
            c = get_consumer(p.name, resource_access_path)
            consumer_list.append(c)

    def get_primitive_type_from_leaf_node(leaf_node_payload):
        if isinstance(leaf_node_payload, LeafNode):
            return get_payload_primitive_type(leaf_node_payload.leaf_property.payload)
        else:
            return None

    parameter_name, parameter_payload = request_parameter.name, request_parameter.payload
    consumer_list = []
    primitive_type = get_primitive_type_from_leaf_node(parameter_payload)

    if parameter_kind == ParameterKind.Header:
        c = get_consumer(parameter_name, [], primitive_type)
        consumer_list.append(c)
    elif parameter_kind == ParameterKind.Path:
        primitive_type = PrimitiveType.String if primitive_type is not None else primitive_type
        c = get_consumer(parameter_name, [], primitive_type)
        consumer_list.append(c)
    elif parameter_kind == ParameterKind.Query:
        if not parameter_name:
            iter_ctx(visit_leaf, visit_inner, PropertyAccessPaths.get_inner_access_path, [], parameter_payload)
        else:
            parameter_dependency = get_consumer(parameter_name, [], primitive_type)
            logger.write_to_main(f"parameter_name={parameter_name} parameter_dependency={type(parameter_dependency)}",
                                 ConfigSetting().LogConfig.dependencies)
            consumer_list.append(parameter_dependency)
    elif parameter_kind == ParameterKind.Body:
        iter_ctx(visit_leaf, visit_inner, PropertyAccessPaths.get_inner_access_path, [], parameter_payload)

    return consumer_list


# Input: the requests in the RESTler grammar, without dependencies, the dictionary,
# and any available annotations or examples.
# Returns: the producer-consumer dependencies, and a new dictionary, augmented if required after inferring dependencies.
# extractDependencies
def extract_dependencies(request_data_list: list[(RequestId, RequestData)],
                         global_annotations: List[ProducerConsumerAnnotation],
                         custom_dictionary: MutationsDictionary,
                         query_dependencies: bool,
                         body_dependencies: bool,
                         header_dependencies: bool,
                         allow_get_producers: bool,
                         data_fuzzing: bool,
                         per_resource_dictionaries: {},
                         naming_convention: Optional[NamingConvention]) -> Tuple[
    Dict[Union[AccessPath, str], List[ProducerConsumerDependency]], List[
        OrderingConstraintVariable], MutationsDictionary]:
    logger.write_to_main(
        f"custom_dictionary={custom_dictionary.__dict__()}\n, query_dependencies={query_dependencies}, "
        f"body_dependencies={body_dependencies}, header_dependencies={header_dependencies} "
        f"allow_get_producers={allow_get_producers}, allow_get_producers={data_fuzzing} "
        f"per_resource_dictionaries={per_resource_dictionaries}, "
        f"naming_convention={naming_convention}",
        ConfigSetting().LogConfig.dependencies)

    def get_parameter_consumers(request_id: RequestId,
                                parameter_kind: ParameterKind,
                                parameters: ParameterList,
                                request_data: RequestData,
                                resolve_dependencies: bool):
        logger.write_to_main(f"begin--> request_id={request_id.endpoint}, parameters={parameters}, "
                             f"request_data={request_data.__dict__()}, resolve_dependencies={resolve_dependencies}",
                             ConfigSetting().LogConfig.dependencies)
        if isinstance(parameters, ParameterList) and resolve_dependencies:
            consumer_list = []
            if parameters.request_parameters is not None:
                for p in parameters.request_parameters:
                    if p is not None:
                        consumers_info = get_parameter_dependencies(parameter_kind=parameter_kind,
                                                                    global_annotations=global_annotations,
                                                                    request_id=request_id,
                                                                    request_data=request_data,
                                                                    request_parameter=p,
                                                                    naming_convention=naming_convention)
                        for item in consumers_info:
                            logger.write_to_main(f"request_id={request_id.endpoint}, "
                                                 # f"parameters={parameters}, "
                                                 f"request_data={request_data.__dict__()}, "
                                                 # f"resolve_dependencies={resolve_dependencies}, "
                                                 f"consumers={item.parameter_kind}",
                                                 ConfigSetting().LogConfig.dependencies)

                            consumer_list.append(item)

            logger.write_to_main(f"end request_id={request_id.endpoint} consumer_list={len(consumer_list)}",
                                 ConfigSetting().LogConfig.dependencies)
            return consumer_list
        else:
            return []

    def find_dependencies(consumer_info: Consumer,
                          dependencies_param):
        consumer_key = consumer_info.consumer_id.access_path if consumer_info.consumer_id.access_path \
            else consumer_info.consumer_id.resource_name
        # If the exact same dependency already appears, do not add it.
        # This covers the case where the same uuid suffix is referred to in
        # multiple locations
        if consumer_key not in dependencies_param.keys() or any(
                dep.consumer.consumer_id.request_id == consumer_info.consumer_id.request_id and
                dep.consumer.consumer_id.resource_name == consumer_info.consumer_id.resource_name and
                dep.consumer.consumer_id.access_path == consumer_info.consumer_id.access_path
                and dep.producer is not None
                for dep in dependencies_param[consumer_key]):
            return None
        return next((dep for dep in dependencies_param[consumer_key] if
                     dep.consumer.consumer_id.request_id == consumer_info.consumer_id.request_id
                     and dep.consumer.consumer_id.resource_name == consumer_info.consumer_id.resource_name
                     and dep.consumer.consumer_id.access_path == consumer_info.consumer_id.access_path
                     and dep.producer is not None),
                    None)

    def add_dependency(d, dependencies_param):
        consumer_key = "".join(d.consumer.consumer_id.access_path_parts.path) \
            if d.consumer.consumer_id.access_path else d.consumer.consumer_id.resource_name
        if consumer_key not in dependencies_param.keys():
            return consumer_key, False
        existed_dependency = find_dependencies(d.consumer, dependencies_param)
        # If the exact same dependency already appears, do not add it.
        # This covers the case where the same uuid suffix is referred to in
        # multiple locations
        if existed_dependency is None:
            return consumer_key, False
        elif existed_dependency.producer != d.producer:
            raise Exception(
                f"Multiple producers for the same consumer should not exist. Consumer ID:"
                f" {existing_dep.consumer.consumer_id.request_id} "
                f"{existing_dep.consumer.consumer_id.resource_name} "
                f"{existing_dep.consumer.consumer_id.access_path}, "
                f"producers: {existing_dep.producer} (existing) <> {d.producer} (current)")

    # Gets dependencies for this consumer.
    # Returns an updated mutations dictionary
    # getDependenciesForConsumer
    def get_dependencies_for_consumer(request_consumer: Consumer, all_producers: Producers):

        endpoint = request_consumer.consumer_id.request_id.endpoint

        per_resource_dict = None
        if endpoint in per_resource_dictionaries.keys():
            per_resource_dict = per_resource_dictionaries[endpoint][0][1]
            logger.write_to_main(f"{endpoint}: dictionary:{per_resource_dict.__dict__()}",
                                 ConfigSetting().LogConfig.dependencies)

        logger.write_to_main(f"request_consumer={type(request_consumer)}", ConfigSetting().LogConfig.dependencies)
        new_dict_info, p = find_producer(producers=all_producers,
                                         consumer=request_consumer,
                                         dictionary=custom_dictionary,
                                         allow_get_producers=allow_get_producers,
                                         per_request_dictionary=per_resource_dict)
        if p is not None:
            logger.write_to_main(f"producer={type(p)} "
                                 f"mutations_dictionary={new_dict_info.restler_custom_payload_uuid4_suffix}",
                                 ConfigSetting().LogConfig.dependencies)
        return new_dict_info, ProducerConsumerDependency(consumer=request_consumer, producer=p)

    print("Getting path consumers...")
    producers = Producers()
    path_consumers = []
    for request_id, request_data in request_data_list:
        path_consumer = get_parameter_consumers(request_id=request_id,
                                                parameter_kind=ParameterKind.Path,
                                                parameters=request_data.request_parameters.path,
                                                request_data=request_data,
                                                resolve_dependencies=True)
        path_consumers.append((request_id, path_consumer))

    print("Getting query consumers...")
    query_consumers = []
    query_consumers_example = []
    for request_id, request_data in request_data_list:
        for x, qp in request_data.request_parameters.query:
            # IMPORTANT: when data fuzzing, the schema must be used when analyzing
            # producer-consumer dependencies, because this includes all the
            # possible parameters that may be passed in the query.
            query_consumer = get_parameter_consumers(request_id=request_id,
                                                     parameter_kind=ParameterKind.Query,
                                                     parameters=qp,
                                                     request_data=request_data,
                                                     resolve_dependencies=query_dependencies)
            if data_fuzzing:
                if x == ParameterPayloadSource.Schema:
                    # 筛选出 schema 来源的查询参数
                    query_consumers.append((request_id, query_consumer))
            else:
                # This list should only contain examples, or only the schema.
                if x == ParameterPayloadSource.Examples:
                    query_consumers_example.append((request_id, query_consumer))
                elif x == ParameterPayloadSource.Schema:
                    query_consumers.append((request_id, query_consumer))
    if len(query_consumers) == 0:
        query_consumers = query_consumers_example

    print("Getting header consumers...")
    header_consumers = []
    header_consumers_example = []
    for request_id, request_data in request_data_list:
        for x, hp in request_data.request_parameters.header:
            header_consumer = get_parameter_consumers(request_id=request_id,
                                                      parameter_kind=ParameterKind.Header,
                                                      parameters=hp,
                                                      request_data=request_data,
                                                      resolve_dependencies=header_dependencies)
            if data_fuzzing:
                if x == ParameterPayloadSource.Schema:
                    header_consumers.append((request_id, header_consumer))
            else:
                # This list should only contain examples, or only the schema.
                if x == ParameterPayloadSource.Examples:
                    header_consumers_example.append((request_id, header_consumer))
                elif x == ParameterPayloadSource.Schema:
                    header_consumers.append((request_id, header_consumer))

    if len(header_consumers) == 0:
        header_consumers = header_consumers_example

    print("Getting body consumers...")

    body_consumers = []
    body_consumers_example = []
    for request_id, request_data in request_data_list:
        for x, bp in request_data.request_parameters.body:
            body_consumer = get_parameter_consumers(request_id=request_id,
                                                    parameter_kind=ParameterKind.Body,
                                                    parameters=bp,
                                                    request_data=request_data,
                                                    resolve_dependencies=body_dependencies)
            if data_fuzzing:
                if x == ParameterPayloadSource.Schema:
                    body_consumers.append((request_id, body_consumer))
            else:
                # This list should only contain examples, or only the schema.
                if x == ParameterPayloadSource.Examples:
                    body_consumers_example.append((request_id, body_consumer))
                elif x == ParameterPayloadSource.Schema:
                    body_consumers.append((request_id, body_consumer))
    if len(body_consumers) == 0:
        body_consumers = body_consumers_example

    # Remove duplicate consumers based on their ID, resource name, and access path parts
    distinct_consumers_dict = {}
    for request_id, consumers in body_consumers:
        for consumer in consumers:
            access_path_parts = ""
            resource_name = ""
            if len(consumer.consumer_id.access_path_parts.path) > 0:
                access_path_parts = consumer.consumer_id.access_path_parts.get_json_pointer()
            if consumer.consumer_id.resource_name is not None:
                resource_name = consumer.consumer_id.resource_name
            distinct_consumers_dict = {(consumer.consumer_id.request_id.endpoint,
                                        resource_name,
                                        access_path_parts): consumer}
    distinct_consumers = list(distinct_consumers_dict.values())
    # Create producers for specific parameter properties
    producer_property_names = ["name"]
    for consumer in distinct_consumers:
        resource_name = consumer.consumer_id.resource_name
        if resource_name in producer_property_names and consumer.consumer_id.container_name:
            producer = create_body_payload_input_producer(consumer.consumer_id)
            producers.add_same_payload_producer(resource_name, producer)

    print("Getting producers...")

    # Only include POST, PUT, PATCH, and GET requests.  Others are never producers.
    for (request_id, request_data) in request_data_list:
        if request_data.response_properties is not None:
            print(f"request_id={request_id.endpoint}, method={request_id.method}")
            logger.write_to_main(f"response_properties={request_data.response_properties.__dict__()}"
                                 f"type(response)={type(request_data.response_properties)}",
                                 ConfigSetting().LogConfig.dependencies)
            response_producer_access_paths = get_producer(request_id, request_data.response_properties)

            for ap in response_producer_access_paths:
                logger.write_to_main(f"path={ap.path.path}", ConfigSetting().LogConfig.dependencies)
                producer = create_path_producer(request_id, ap, naming_convention, ap.primitive_type)
                logger.write_to_main(f"producer={producer.__dict__()}", ConfigSetting().LogConfig.dependencies)
                resource_name = ap.name
                producers.add_response_producer(resource_name, producer)
        # Add the header name as a producer only
        for header in request_data.response_headers:
            resource_name = header[0]
            header_payload = header[1]
            if isinstance(header_payload, LeafNode):
                primitive_type = get_payload_primitive_type(header_payload.leaf_property.payload)
            elif isinstance(header_payload, InternalNode):
                primitive_type = PrimitiveType.Object
            else:
                primitive_type = PrimitiveType.Unknown

            producer = create_header_response_producer(
                request_id=request_id,
                header_parameter_name=resource_name,
                naming_convention=naming_convention,
                primitive_type=primitive_type
            )
            producers.add_response_producer(resource_name, producer)

        # Also check for input-only producers that should be added for this request.
        # At this time, only producers specified in annotations are supported.
        # Find the corresponding parameter and add it as a producer.
        for a in request_data.local_annotations:
            if a.producer_parameter is not None:
                resource_name, producer = create_input_only_producer_from_annotation(a, path_consumers,
                                                                                     query_consumers,
                                                                                     body_consumers,
                                                                                     header_consumers)
                if producer is not None:
                    logger.write_to_main(f"producer={producer}", ConfigSetting().LogConfig.dependencies)
                    producers.add_input_only_producer(resource_name, producer)

    # TODO: remove this filter when we figure out how to handle delete producers.
    for (r, rd) in request_data_list:
        if r.method in [OperationMethod.Post, OperationMethod.Put, OperationMethod.Patch, OperationMethod.Get]:
            if rd.link_annotations:
                for a in rd.link_annotations:
                    if a.producer_parameter is not None:
                        resource_name, producer = create_input_only_producer_from_annotation(a,
                                                                                             path_consumers,
                                                                                             query_consumers,
                                                                                             body_consumers,
                                                                                             header_consumers)
                        if producer is not None:
                            logger.write_to_main(f"producer={producer}", ConfigSetting().LogConfig.dependencies)
                            producers.add_input_only_producer(resource_name, producer)

    # Also check for input-only producers that should be added for this request.
    # At this time, only producers specified in annotations are supported.
    # Find the corresponding parameter and add it as a producer.
    for a in global_annotations:
        if a.producer_parameter is not None:
            resource_name, producer = create_input_only_producer_from_annotation(a,
                                                                                 path_consumers,
                                                                                 query_consumers,
                                                                                 body_consumers,
                                                                                 header_consumers)
            if producer is not None:
                logger.write_to_main(f"producer={producer}", ConfigSetting().LogConfig.dependencies)
                producers.add_input_only_producer(resource_name, producer)

    print("Done processing producers")
    print("Compute dependencies")
    consumers = path_consumers + query_consumers + body_consumers + header_consumers
    debug_file_log("consumer", consumers=consumers, producers=None, dependencies=None)
    debug_file_log("producer", consumers=None, producers=producers, dependencies=None)
    dependencies = dict()

    generated_suffixes = []
    for request_id, request_consumers in consumers:
        logger.write_to_main(f"begin request_id={request_id.endpoint}, "
                             f"request_consumers={len(request_consumers)}",
                             ConfigSetting().LogConfig.dependencies)
        new_uuid_suffixes = []
        # First, look for producers in a different payload
        for cx in request_consumers:
            logger.write_to_main(f"cx = {cx}, cx={cx.__dict__()}", ConfigSetting().LogConfig.dependencies)
            new_dict, dependencies_result = get_dependencies_for_consumer(cx, producers)
            new_uuid = list(new_dict.restler_custom_payload_uuid4_suffix.items())
            logger.write_to_main(f"new_uuid={new_uuid}", ConfigSetting().LogConfig.dependencies)
            new_uuid_suffixes = list(set(new_uuid_suffixes + new_uuid))
            # new_uuid_suffixes.extend(new_dict.restler_custom_payload_uuid4_suffix.items())
            logger.write_to_main(f"new_uuid_suffixes={new_uuid_suffixes}", ConfigSetting().LogConfig.dependencies)

            if dependencies_result.producer is not None:
                logger.write_to_main(f"dependencies={dependencies_result.__dict__()}",
                                     ConfigSetting().LogConfig.dependencies)
                key, found = add_dependency(dependencies_result, dependencies)
                logger.write_to_main(f"key={key}, found={found}",
                                     ConfigSetting().LogConfig.dependencies)
                if not found:
                    dependencies.setdefault(key, []).append(dependencies_result)
                    logger.write_to_main(f"dependencies={dependencies}",
                                         ConfigSetting().LogConfig.dependencies)

        print(f"Second pass dependencies for request {request_id.endpoint}")
        # Then do a second pass for producers in the same payload.  Two passes are required because the
        # same payload body producer's dependency needs to be known.
        new_uuid_suffixes_2 = []
        for cx in request_consumers:
            existing_dep = find_dependencies(cx, dependencies)
            if existing_dep is None:
                body_input_producer = get_same_body_input_producer(producers=producers, consumer=cx)
                if body_input_producer is not None:
                    if isinstance(producers, BodyPayloadInputProducer):
                        consumer_resource_name = producers.resource_name
                        logger.write_to_main(f"consumer_resource_name={consumer_resource_name}",
                                             True)
                        prefix_name = DynamicObjectNaming.generate_id_for_custom_uuid_suffix_payload(
                            producers.container_name, consumer_resource_name)

                        suffix_producer_dict_payload = DictionaryPayload(payload_type=CustomPayloadType.UuidSuffix,
                                                                         primitive_type=PrimitiveType.String,
                                                                         name=prefix_name,
                                                                         is_object=False)
                        api_resource = ApiResource(producers.request_id,
                                                   producers.resource_reference,
                                                   producers.naming_convention,
                                                   PrimitiveType.String)
                        suffix_consumer = Consumer(consumer_id=api_resource, parameter_kind=ParameterKind.Body,
                                                   annotation=None)

                        suffix_dep = ProducerConsumerDependency(consumer=suffix_consumer,
                                                                producer=suffix_producer_dict_payload)

                        logger.write_to_main(f"suffix_dep={suffix_dep}", ConfigSetting().LogConfig.dependencies)

                        if not find_dependencies(suffix_consumer, dependencies):
                            dep = ProducerConsumerDependency(consumer=cx, producer=producers)

                            key, found = add_dependency(dep, dependencies)
                            logger.write_to_main(f"key={key}, found={found}", ConfigSetting().LogConfig.dependencies)
                            if not found:
                                dependencies.setdefault(key, []).append(dep)

                            key, found = add_dependency(suffix_dep, dependencies)
                            logger.write_to_main(f"key={key}, found={found}", ConfigSetting().LogConfig.dependencies)
                            if not found:
                                dependencies.setdefault(key, []).append(suffix_dep)

                            logger.write_to_main(f"dependencies={dependencies}",
                                                 ConfigSetting().LogConfig.dependencies)
                        if prefix_name not in custom_dictionary.restler_custom_payload_uuid4_suffix.keys():
                            prefix_value = (DynamicObjectNaming.
                                            generate_prefix_for_custom_uuid_suffix_payload(prefix_name))
                            if prefix_name not in new_uuid_suffixes:
                                new_uuid_suffixes.append((prefix_name, prefix_value))
                            logger.write_to_main(f"prefix_name={prefix_name}, prefix_value={prefix_value}",
                                                 ConfigSetting().LogConfig.dependencies)
        print(f"Done dependencies for request {request_id.endpoint}")
        # Merge results and ensure no duplicates
        combined_suffixes = new_uuid_suffixes + new_uuid_suffixes_2
        generated_suffixes.append((request_id, combined_suffixes))

    logger.write_to_main(f"len(dependencies)={len(dependencies)}, "
                         f"generated_suffixes={generated_suffixes}", ConfigSetting().LogConfig.dependencies)

    final_suffixes = defaultdict(set)
    for request_id, suffixes in generated_suffixes:
        for suffix in suffixes:
            final_suffixes[suffix[0]].add(suffix[1])

    # Add custom dictionary suffixes
    custom_suffixes = custom_dictionary.restler_custom_payload_uuid4_suffix
    for key, value in custom_suffixes.items():
        final_suffixes[key].add(value)

    print("Assigning equality constraints...")
    for request_id, request_consumers in consumers:
        for consumer in request_consumers:
            consumer_id = consumer.consumer_id
            if (consumer.annotation and consumer.annotation.consumer_id and
                    consumer.annotation.consumer_id == consumer.annotation.producer_id):
                existing_dependency = find_dependencies(consumer, dependencies_param=dependencies)
                if existing_dependency:
                    print("Cannot apply equality constraint since the consumer already has a dependency.")
                else:
                    possible_resource_references = []
                    if isinstance(consumer.annotation.producer_parameter, AnnotationResourceReference):
                        body_resource = BodyResource(
                            name=consumer.annotation.producer_parameter.resource_name,
                            full_path=consumer.annotation.producer_parameter.resource_path.path)
                        possible_resource_references.append((ParameterKind.Body, body_resource))
                    elif isinstance(consumer.annotation.producer_parameter, str):
                        path_resource = PathResource(name=consumer.annotation.producer_parameter,
                                                     path_to_parameter=[],
                                                     response_path=EmptyAccessPath)
                        query_resource = QueryResource(name=consumer.annotation.producer_parameter)
                        header_resource = HeaderResource(consumer.annotation.producer_parameter)
                        possible_resource_references.extend([
                            (ParameterKind.Path, path_resource),
                            (ParameterKind.Query, query_resource),
                            (ParameterKind.Header, header_resource)])

                    existing_dep = None
                    for parameter_kind, resource_reference in possible_resource_references:
                        api_id = ApiResource(request_id=consumer_id.request_id,
                                             resource_reference=resource_reference,
                                             naming_convention=naming_convention,
                                             primitive_type=PrimitiveType.String)
                        search_consumer = Consumer(consumer_id=api_id, parameter_kind=parameter_kind, annotation=None)
                        existing_dep = find_dependencies(search_consumer, dependencies)

                        if existing_dep:
                            dep = ProducerConsumerDependency(consumer=consumer, producer=existing_dep.producer)
                            key, found = add_dependency(dep, dependencies)
                            if found:
                                dependencies[key].append(dep)
                            else:
                                dependencies[key] = []
                        else:
                            print("Cannot apply equality constraint since the producer does not have a dependency")

    debug_file_log("dependencies", consumers=consumers, producers=producers, dependencies=dependencies)

    print("Getting ordering constraints...")
    ordering_constraints = [OrderingConstraintVariable(source_request_id=a.producer_id,
                                                       target_request_id=a.consumer_id)
                            for a in global_annotations
                            if a.consumer_id is not None and a.producer_parameter is None
                            and a.consumer_parameter is None]
    print("Dependency analysis completed.")
    return dependencies, ordering_constraints, custom_dictionary


class DependencyLookup:
    # getConsumerPayload
    @staticmethod
    def get_consumer_payload(dependencies: Dict[Union[AccessPath, str], List[ProducerConsumerDependency]],
                             path_payload: list[FuzzingPayload],
                             request_id: RequestId,
                             consumer_resource_name,
                             consumer_resource_access_path: AccessPath,
                             default_payload):

        logger.write_to_main(f"request_id={request_id.__dict__()}, "
                             f"consumer_resource_name={consumer_resource_name} "
                             f"consumer_resource_access_path={consumer_resource_access_path.path}",
                             ConfigSetting().LogConfig.dependencies)

        if not consumer_resource_name:
            raise Exception("Empty consumer name is not valid")

        # Find the producer
        def find_producer(dependency_list: list[ProducerConsumerDependency]):
            # Note: in some cases, two dependencies will appear - one that was inserted
            # analyzing same-body dependencies, and one that was computer as usual.
            # Make sure there is only one producer.
            producers = [dep.producer for dep in dependency_list
                         if dep.producer and dep.consumer.consumer_id.request_id == request_id
                         and dep.consumer.consumer_id.resource_name == consumer_resource_name
                         and dep.consumer.consumer_id.access_path_parts == consumer_resource_access_path]

            if len(producers) > 1:
                raise Exception("Multiple producer-consumer dependencies detected for the same producer.")

            return producers[0] if producers else None

        producer = None
        if consumer_resource_access_path.length() < 1:
            resource_access_path = consumer_resource_access_path.get_json_pointer()
        else:
            # resource_access_path = "/" + ("/".join(consumer_resource_access_path.path))
            resource_access_path = "".join(consumer_resource_access_path.path)

        if resource_access_path is None:
            values = dependencies.get(consumer_resource_name, None)
            if values is not None:
                producer = find_producer(values)
        else:
            values = dependencies.get(resource_access_path, None)
            if values is not None:
                producer = find_producer(values)

        if producer is None:
            return default_payload
        else:
            if isinstance(producer, OrderingConstraintProducer):
                raise Exception("Ordering constraint parameters should not be part of payloads")

            elif isinstance(producer, ResponseProducer):
                if isinstance(producer.resource_reference, HeaderResource):
                    hr = producer.resource_reference
                    access_path = AccessPath(path=[hr, "header"])
                    variable_name = DynamicObjectNaming.generate_dynamic_object_variable_name(
                        producer.request_id, access_path, "_")
                else:
                    variable_name = DynamicObjectNaming.generate_dynamic_object_variable_name(
                        producer.request_id, producer.resource_reference.get_access_path_parts(), "_")

                primitive_type = default_payload.primitive_type
                if primitive_type is None:
                    print(
                        f"Warning: primitive type not available for {request_id} [resource: {consumer_resource_name}]")
                    primitive_type = producer.primitive_type
                return DynamicObject(primitive_type, variable_name, is_writer=False)

            elif isinstance(producer, InputParameter):
                access_path = producer.input_only_producer.get_input_parameter_access_path()
                variable_name = DynamicObjectNaming.generate_dynamic_object_variable_name(
                    producer.input_only_producer.request_id, access_path, "_")

                if isinstance(default_payload, Fuzzable):
                    primitive_type = default_payload.primitive_type
                else:
                    primitive_type = producer.dictionary_payload.primitive_type
                if producer.input_only_producer.parameter_kind == ParameterKind.Path:
                    dynamic_object = DynamicObject(primitive_type=PrimitiveType.Object,
                                                   variable_name=variable_name,
                                                   is_writer=False)
                else:
                    dynamic_object = DynamicObject(primitive_type=primitive_type,
                                                   variable_name=variable_name,
                                                   is_writer=False)

                if producer.dictionary_payload is None:
                    if producer.is_writer:
                        if isinstance(default_payload, Fuzzable):
                            return Fuzzable(primitive_type=primitive_type,
                                            default_value="",
                                            example_value=None,
                                            parameter_name=variable_name,
                                            dynamic_object=dynamic_object)
                        elif isinstance(default_payload, Custom):
                            return Custom(
                                payload_type=default_payload.payload_type,
                                primitive_type=default_payload.primitive_type,
                                payload_value=default_payload.payload_value,
                                is_object=default_payload.is_object,
                                dynamic_object=dynamic_object)
                        else:
                            raise Exception("Input producers are not supported for this payload type.")
                    else:
                        default_payload.dynamic_object = dynamic_object
                        return default_payload
                else:
                    dp = producer.dictionary_payload
                    return Custom(payload_type=dp.payload_type,
                                  primitive_type=dp.primitive_type,
                                  payload_value=dp.name,
                                  is_object=dp.is_object,
                                  dynamic_object=dynamic_object)

            elif isinstance(producer, DictionaryPayload):
                dp = producer
                return Custom(payload_type=dp.payload_type,
                              primitive_type=dp.primitive_type,
                              payload_value=dp.name,
                              is_object=dp.is_object,
                              dynamic_object=None)
            elif isinstance(producer, BodyPayloadInputProducer):
                # The producer is a property in the same input payload body.
                # The consumer should consist of a set of payload parts, creating the full URI
                # (with resolved dependencies)  to that property.

                if path_payload is None:
                    raise Exception(f"Same body payload cannot be created without a path payload: "
                                    f"{producer}")

                uri_parts = producer.access_path_parts.get_path_property_name_parts()

                container_name = producer.container_name

                # Skip 'properties' container, which is typically not part of the URI
                uri_parts = [part for part in uri_parts if part != "properties"]

                payload_value = "/" + "/".join(uri_parts[:-1])

                child_payload_except_name = FuzzingPayload.Constant(PrimitiveType.String, payload_value)

                name_prefix = DynamicObjectNaming.generate_id_for_custom_uuid_suffix_payload(container_name,
                                                                                             producer.resource_name)
                name_payload = Custom(payload_type=CustomPayloadType.UuidSuffix,
                                      primitive_type=PrimitiveType.String,
                                      payload_value=name_prefix,
                                      is_object=False,
                                      dynamic_object=None)

                # Add the endpoint (path) payload with resolved dependencies
                pp = [FuzzingPayload.Constant(PrimitiveType.String, "/") + x for x in path_payload] + [
                    child_payload_except_name] + [name_payload]
                FuzzingPayload.PayloadParts(pp)
                return pp

    # mergeDynamicObjects
    @staticmethod
    def merge_dynamic_objects(dependencies_index: Dict[Union[AccessPath, str], List[ProducerConsumerDependency]],
                              ordering_constraints: List[OrderingConstraintVariable]) -> (
            Tuple)[Dict[Union[AccessPath, str], List[ProducerConsumerDependency]], List[OrderingConstraintVariable]]:
        producer_dict = {}
        keys = dependencies_index.keys()
        for key in keys:
            for dep in dependencies_index[key]:
                producer = dep.producer
                consumer_id = (dep.consumer.consumer_id.request_id.endpoint,
                               dep.consumer.consumer_id.resource_reference.get_resource_name())
                if (isinstance(producer, DictionaryPayload) or
                        isinstance(producer, BodyPayloadInputProducer)
                        or isinstance(producer, OrderingConstraintProducer)):
                    pass
                elif isinstance(producer, ResponseProducer):
                    if consumer_id not in producer_dict.keys():
                        producer_dict[consumer_id] = []
                    producer_dict[consumer_id].append((ProducerKind.Response, producer))
                elif isinstance(producer, InputParameter):
                    if consumer_id not in producer_dict.keys():
                        producer_dict[consumer_id] = []
                    producer_dict[consumer_id].append((ProducerKind.Input, producer))

        new_dep_list = dict()
        new_ordering_constraints = []

        for item in dependencies_index:
            for dep in dependencies_index[item]:
                ordering_constraints = []

                if dep.producer is None:
                    new_dep_list.setdefault(item, []).append(dep)
                else:
                    consumer_id = (
                        dep.consumer.consumer_id.request_id.endpoint, dep.consumer.consumer_id.resource_reference)

                    if consumer_id in producer_dict.keys():
                        input_producer = next(
                            ((dep_kind, input_producer_api_resource) for dep_kind, input_producer_api_resource in
                             producer_dict[consumer_id] if dep_kind == ProducerKind.Input), None)

                        if input_producer:
                            input_producer_resource_id = (
                                input_producer[1].request_id, input_producer[1].resource_reference)

                            if input_producer_resource_id in producer_dict:
                                response_producer = next(
                                    ((dep_kind, response_producer_api_resource, response_producer) for
                                     dep_kind, response_producer_api_resource, response_producer in
                                     producer_dict[input_producer_resource_id] if
                                     dep_kind == ProducerKind.Response), None)

                                if response_producer:
                                    new_ordering_constraint = (input_producer_resource_id[0], consumer_id[0])
                                    new_dep = dep if response_producer is None else None
                                    new_dep_list.setdefault(item, []).append(new_dep)
                                    ordering_constraints.append(new_ordering_constraint)
                            else:
                                new_dep_list.setdefault(item, []).append(dep)
                        else:
                            new_dep_list.setdefault(item, []).append(dep)
                    else:
                        new_dep_list.setdefault(item, []).append(dep)

                new_ordering_constraints.extend(ordering_constraints)

        return new_dep_list, ordering_constraints

    # getDependencyPayload
    @staticmethod
    def get_dependency_payload(dependencies: Dict[Union[AccessPath, str], List[ProducerConsumerDependency]],
                               path_payload,
                               request_id: RequestId,
                               request_parameter: RequestParameter,
                               dictionary: MutationsDictionary):
        # First, pre-compute producer-consumer relationships within the same body payload.
        # These then need to be passed through each property in order to substitute dynamic objects.
        parameter_payload = request_parameter.payload
        logger.write_to_main(f"parameter_payload={parameter_payload}", ConfigSetting().LogConfig.dependencies)

        def visit_leaf(resource_access_path: list[str], p: LeafProperty):
            logger.write_to_main(f"p={p.__dict__()}", ConfigSetting().LogConfig.dependencies)
            if p.name is not None and not p.name.isspace() and p.name != "":
                leaf_access_path = PropertyAccessPaths.get_leaf_access_path(resource_access_path, p)

                payload = DependencyLookup.get_consumer_payload(dependencies=dependencies,
                                                                path_payload=path_payload,
                                                                request_id=request_id,
                                                                consumer_resource_name=p.name,
                                                                consumer_resource_access_path=leaf_access_path,
                                                                default_payload=p.payload)
            else:
                payload = p.payload
                print("Warning: leaf property should always have a name unless it's an array element.")

            leaf_node = LeafNode(leaf_property=LeafProperty(name=p.name,
                                                            payload=payload,
                                                            is_required=p.is_required,
                                                            is_readonly=p.is_readonly))
            return leaf_node

        def visit_inner(resource_access_path: list[str], inner_properties: InnerProperty, subtree: list[Tree]):
            logger.write_to_main(f"inner_properties={inner_properties.__dict__()}, subtree={subtree}",
                                 ConfigSetting().LogConfig.dependencies)
            if inner_properties.name is None or inner_properties.name == "":
                return InternalNode(inner_property=inner_properties, leaf_properties=subtree)
            else:
                default_value = Fuzzable(primitive_type=PrimitiveType.String,
                                         default_value="",
                                         example_value=None,
                                         parameter_name=None,
                                         dynamic_object=None) \
                    if inner_properties.payload is None else inner_properties

                property_access_path = PropertyAccessPaths.get_inner_access_path(resource_access_path, inner_properties)
                logger.write_to_main(f"property_access_path={property_access_path}, "
                                     f"resource_access_path={resource_access_path}",
                                     ConfigSetting().LogConfig.dependencies)
                payload = DependencyLookup.get_consumer_payload(dependencies,
                                                                path_payload,
                                                                request_id,
                                                                inner_properties.name,
                                                                AccessPath(property_access_path),
                                                                inner_properties.payload) \
                    if inner_properties.name else None
                if payload != default_value:
                    print(f"Found dependency or dictionary entry on inner property of query or body: "
                          f"{inner_properties.name}")
                    inner_properties.payload = payload
                    return InternalNode(inner_property=inner_properties, leaf_properties=subtree)
                else:
                    return InternalNode(inner_property=inner_properties, leaf_properties=subtree)

        # First, check if the parameter itself has a dependency
        logger.write_to_main("request_parameter={}".format(type(request_parameter)),
                             ConfigSetting().LogConfig.dependencies)
        parameter_name, properties = request_parameter.name, request_parameter.payload

        logger.write_to_main(f"properties={type(properties)}", ConfigSetting().LogConfig.dependencies)
        # The type of the payload gets substituted into the producer, so this must match the earlier declared type.
        # TODO: check correctness for nested type (array vs. obj vs. property...)
        default_payload = None
        is_required = False
        is_read_only = False
        if isinstance(properties, LeafNode):
            default_payload = properties.leaf_property.payload
            is_required = properties.leaf_property.is_required
            is_read_only = properties.leaf_property.is_readonly
        elif isinstance(properties, InternalNode):
            is_required = properties.inner_property.is_required
            is_read_only = properties.inner_property.is_readonly
            payload_data = Fuzzable(primitive_type=PrimitiveType.String,
                                    default_value="",
                                    example_value=None,
                                    parameter_name=None,
                                    dynamic_object=None)
            if properties.inner_property.property_type == PrimitiveType.Object:
                payload_data.primitive_type = PrimitiveType.Object
                payload_data.default_value = {}
            elif properties.inner_property.property_type == PrimitiveType.Array:
                payload_data.primitive_type = PrimitiveType.Array
                payload_data.default_value = []

            default_payload = payload_data

        dependency_payload = DependencyLookup.get_consumer_payload(dependencies,
                                                                   path_payload,
                                                                   request_id,
                                                                   parameter_name,
                                                                   EmptyAccessPath,
                                                                   default_payload)

        if dependency_payload != default_payload:
            payload_with_dependencies = LeafNode(leaf_property=LeafProperty(name="",
                                                                            payload=dependency_payload,
                                                                            is_required=is_required,
                                                                            is_readonly=is_read_only))
        else:
            payload_with_dependencies = cata_ctx(f_leaf=visit_leaf,
                                                 f_node=visit_inner,
                                                 f_ctx=PropertyAccessPaths.get_inner_access_path,
                                                 ctx=[],
                                                 tree=properties)
            logger.write_to_main(f"payload_with_dependencies={payload_with_dependencies.__dict__()}",
                                 ConfigSetting().LogConfig.dependencies)

        def add_dictionary_entries(custom_payloads, p):
            def get_dictionary_entry(entries, payload):
                if isinstance(payload, Custom):
                    if payload.payload_value in entries.keys():
                        logger.write_to_main(f"entries={entries}", ConfigSetting().LogConfig.dependencies)
                    else:
                        prefix_value = DynamicObjectNaming.generate_prefix_for_custom_uuid_suffix_payload(
                            payload.payload_value)
                        entries[payload.payload_value] = prefix_value
                        logger.write_to_main(f"keys={payload.payload_value} entries={prefix_value}",
                                             ConfigSetting().LogConfig.dependencies)
                elif isinstance(payload, list):
                    for payload_part in payload:
                        get_dictionary_entry(entries, payload_part)
                        logger.write_to_main(f"payload_part={payload_part}", ConfigSetting().LogConfig.dependencies)
                    logger.write_to_main(f"entries={entries}", ConfigSetting().LogConfig.dependencies)
                return entries

            return get_dictionary_entry(custom_payloads, p.payload)

        def id_inner_visitor(entries, p):
            return entries

        new_custom_payloads = fold(f_leaf=add_dictionary_entries,
                                   f_node=id_inner_visitor,
                                   acc=dictionary.restler_custom_payload_uuid4_suffix,
                                   tree=payload_with_dependencies)
        sorted_dict = {key: new_custom_payloads[key] for key in sorted(new_custom_payloads.keys())}
        DictionarySetting().custom_payload_uuid4_suffix(sorted_dict)

        new_request_parameter = RequestParameter(name=parameter_name,
                                                 payload=payload_with_dependencies,
                                                 serialization=request_parameter.serialization)

        return new_request_parameter, DictionarySetting()


# The dependencies file contains a brief summary of all parameters and
# body properties for which a producer-consumer dependency was not inferred.  This
# means that the input value for this property is either going to be from an enumeration
# or a fuzzable value specified in the dictionary.
# When parameters are present in this file, it does not necessarily mean
# the API cannot be successfully executed (though, it is often the case for path
# parameters).
# The output format is intended to be easily transformed to an annotation that can be
# specified in annotations.json to resolve the dependency.
# Output format example:
# {
#   "/api/doc" : {
#       "get": {
#               "path": [ <list of dependencies in annotation format> ],
#               "body": [ <list of dependencies in annotation format> ]
#         }
def write_dependencies(dependencies_file_path, dependencies, unresolved_only):
    if unresolved_only:
        dependencies = [d for d in dependencies if d.producer is None]
        if len(dependencies) == 0:
            return

    def get_method(api_resource):
        return api_resource.request_id.method.name.upper()

    def get_parameter(api_resource):
        if isinstance(api_resource.resource_reference, PathResource):
            return api_resource.resource_reference.get_resource_name()
        elif isinstance(api_resource.resource_reference, QueryResource):
            return api_resource.resource_reference.get_resource_name()
        elif isinstance(api_resource.resource_reference, HeaderResource):
            return api_resource.resource_reference.get_resource_name()
        elif isinstance(api_resource.resource_reference, BodyResource):
            if api_resource.resource_reference.full_path.length() > 1:
                # api_resource.resource_reference.full_path.get_json_pointer()
                return "/".join(api_resource.resource_reference.full_path.path)

            else:
                return "".join(api_resource.resource_reference.full_path.path)

    def serialize_dependency(d):
        consumer = d.consumer
        consumer_parameter = get_parameter(consumer.consumer_id)
        if isinstance(d.producer, DictionaryPayload):
            producer = d.producer
            custom_payload_desc = ""
            if producer.payload_type == CustomPayloadType.String:
                custom_payload_desc = ""
            elif producer.payload_type == CustomPayloadType.UuidSuffix:
                custom_payload_desc = "_uuid_suffix"
            elif producer.payload_type == CustomPayloadType.Header:
                custom_payload_desc = "_header"
            elif producer.payload_type == CustomPayloadType.Query:
                custom_payload_desc = "_query"
            pr = f"restler_custom_payload{custom_payload_desc}__{producer.name}"
            pe = ""
            pm = ""
        else:
            pe = ""
            pm = ""
            pr = ""
            if isinstance(d.producer, ResponseProducer) or isinstance(d.producer, BodyPayloadInputProducer):
                producer = d.producer
                pe = producer.request_id.endpoint
                pm = producer.request_id.method
                pr = get_parameter(producer)
            elif isinstance(d.producer, InputParameter):
                producer = d.producer.input_only_producer
                pe = producer.request_id.endpoint
                pm = producer.request_id.method
                pr = get_parameter(producer)
            elif isinstance(d.producer, OrderingConstraintProducer):
                producer = d.producer
                pe = producer.request_id.endpoint
                pm = producer.request_id.method
                pr = ""

        return {
            "endpoint": consumer.consumer_id.request_id.endpoint,
            "method": get_method(consumer.consumer_id),
            "producer_endpoint": pe,
            "producer_method": pm,
            "producer_resource_name": pr,
            "consumer_param": consumer_parameter,
            "parameterKind": consumer.parameter_kind
        }

    serialized_dependencies = list(map(serialize_dependency, dependencies))
    # sorted_group = sorted(serialized_dependencies, key=lambda x: (x['endpoint'], x['consumer_param']))
    grouped = {}
    for d in serialized_dependencies:
        endpoint = d["endpoint"]
        method = d["method"]
        parameter_kind = d["parameterKind"].name
        if endpoint not in grouped:
            grouped[endpoint] = {}

        if method not in grouped[endpoint]:
            grouped[endpoint][method] = {}
        dict_annaotation = {
            "producer_endpoint": d["producer_endpoint"],
            "producer_method": d["producer_method"].upper(),
            "producer_resource_name": d["producer_resource_name"],
            "consumer_param": d["consumer_param"],
        }
        grouped[endpoint][method].setdefault(parameter_kind, []).append(dict_annaotation)
    from compiler.utilities import JsonSerialization
    JsonSerialization.serialize_to_file(dependencies_file_path, grouped)


def debug_file_log(file_info: str, consumers: Optional[list[tuple[RequestId, list[Consumer]]]],
                   producers: Optional[Producers],
                   dependencies: Optional[dict[Union[AccessPath, str], list[ProducerConsumerDependency]]]):
    dependencies_debug_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                file_info + ".json", )
    str_value = []
    resource_consumers_sorted = []
    keys = {}
    resource_consumer = {}
    if consumers is not None:
        for request_id, request_data in consumers:
            for cx in request_data:
                sorted_key_by_method, sorted_key_by_access_path, sorted_key_by_request_id, _ = (
                    debug_inferred_match_sort_order(cx.consumer_id))
                param = sort_by_parameter_kind(cx.parameter_kind)
                key = cx.consumer_id.access_path if cx.consumer_id.access_path \
                    else cx.consumer_id.resource_name
                resource_consumer.setdefault(cx.consumer_id.request_id.endpoint, []).append(
                    (sorted_key_by_method, param, key, sorted_key_by_access_path, cx))
                if cx.consumer_id.request_id.endpoint not in keys.keys():
                    keys[cx.consumer_id.request_id.endpoint] = (sorted_key_by_request_id, cx.consumer_id.request_id)
                else:
                    if keys[cx.consumer_id.request_id.endpoint][0] > sorted_key_by_request_id:
                        keys[cx.consumer_id.request_id.endpoint] = (sorted_key_by_request_id, cx.consumer_id.request_id)

    sorted_keys = {key: keys[key] for key in sorted(keys.keys())}

    for endpoint_item in sorted_keys:
        values = resource_consumer[endpoint_item]
        sorted_by_first = sorted(values, key=lambda x: (x[0], x[1], x[2], x[3]))
        resource_consumers_sorted = resource_consumers_sorted + sorted_by_first

    if file_info == "consumer":
        for item in resource_consumers_sorted:
            str_value.append({"consumer": item[4].__dict__()})
        JsonSerialization.serialize_to_file(file=dependencies_debug_file_path, obj=str_value)

    elif file_info == "producer":
        if producers is not None:
            JsonSerialization.serialize_to_file(file=dependencies_debug_file_path, obj=producers.__dict__())
    else:
        from compiler.workflow import Constants
        from compiler.dependency_analysis_types import sort_by_parameter_kind_debug
        resource_consumers_sorted_debug = []
        keys_debug = {}
        resource_consumer_debug = {}
        if consumers is not None:
            for request_id, request_data in consumers:
                for cx in request_data:
                    sorted_key_by_method, _, sorted_key_by_request_id, _ = (
                        debug_inferred_match_sort_order(cx.consumer_id))
                    param = sort_by_parameter_kind_debug(cx.parameter_kind)
                    key = cx.consumer_id.access_path if cx.consumer_id.access_path \
                        else cx.consumer_id.resource_name
                    resource_consumer_debug.setdefault(cx.consumer_id.request_id.endpoint, []).append(
                        (sorted_key_by_method, param, key, cx.consumer_id.resource_reference.get_resource_name(), cx))
                    if cx.consumer_id.request_id.endpoint not in keys_debug.keys():
                        keys_debug[cx.consumer_id.request_id.endpoint] = (
                            sorted_key_by_request_id, cx.consumer_id.request_id)
                    else:
                        if keys_debug[cx.consumer_id.request_id.endpoint][0] > sorted_key_by_request_id:
                            keys_debug[cx.consumer_id.request_id.endpoint] = (
                                sorted_key_by_request_id, cx.consumer_id.request_id)

        sorted_keys_debug = {key: keys_debug[key] for key in sorted(keys_debug.keys())}

        for endpoint_item in sorted_keys_debug:
            values = resource_consumer_debug[endpoint_item]
            sorted_by_first = sorted(values, key=lambda x: (x[0], x[1], x[2], x[3]))
            resource_consumers_sorted_debug = resource_consumers_sorted_debug + sorted_by_first

        dependencies_debug_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                    Constants.DependenciesDebugFileName)

        depends = [value for value in dependencies.values()]
        depend_total = [item for sublist in depends for item in sublist]

        for item in resource_consumers_sorted_debug:
            dep = {}
            found = False
            for deps in depend_total:
                if deps.consumer == item[4]:
                    found = True
                    dep = {"consumer": item[4].__dict__(),
                           "producer": deps.producer.__dict__()}
            if found:
                str_value.append(dep)
            else:
                str_value.append({"consumer": item[4].__dict__()})

        JsonSerialization.serialize_to_file(file=dependencies_debug_file_path, obj=str_value)

        dependencies_debug_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                    Constants.DependenciesFileName)
        unresolved_dependencies_debug_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                               Constants.UnresolvedDependenciesFileName)
        deps_all = []
        for item in resource_consumers_sorted:
            dep = ProducerConsumerDependency(consumer=item[4], producer=None)
            for deps in depend_total:
                if deps.consumer == item[4]:
                    dep.producer = deps.producer
            deps_all.append(dep)

        write_dependencies(dependencies_debug_file_path, deps_all, False)
        write_dependencies(unresolved_dependencies_debug_file_path, deps_all, True)
