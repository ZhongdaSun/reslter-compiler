# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import re
import enum
from typing import Union, Optional, Dict, List
import threading

from compiler.grammar import (
    RequestParameters,
    ProducerConsumerAnnotation,
    RequestMetadata, LeafNode,
    InternalNode,
    ParameterKind,
    OperationMethod,
    RequestId)
from compiler.example import ExampleRequestPayload
from compiler.apiresource import (
    ApiResource,
    InputOnlyProducer,
    ResponseProducer,
    BodyPayloadInputProducer,
    Producer,
    Consumer)


class RequestData:
    request_parameters: RequestParameters
    local_annotations: list[ProducerConsumerAnnotation]
    link_annotations: list[ProducerConsumerAnnotation]
    response_properties: Optional[Union[LeafNode, InternalNode]]
    response_headers: list[tuple[str, Union[LeafNode, InternalNode]]]
    request_metadata: RequestMetadata
    example_config: Optional[list[ExampleRequestPayload]]

    def __init__(self, request_parameters,
                 local_annotations: list[ProducerConsumerAnnotation],
                 link_annotations: list[ProducerConsumerAnnotation],
                 response_properties: Optional[Union[LeafNode, InternalNode]],
                 response_headers: list[tuple[str, Union[LeafNode, InternalNode]]],
                 request_metadata,
                 example_config: Optional[list[ExampleRequestPayload]]):
        self.request_parameters = request_parameters
        self.local_annotations = local_annotations
        self.link_annotations = link_annotations
        self.response_properties = response_properties
        self.response_headers = response_headers
        self.request_metadata = request_metadata
        self.example_config = example_config

    def __dict__(self):
        return {"RequestProperties": self.response_properties,
                "ResponseHeader": self.response_headers}


# When choosing among several producers, the order in which they should be
# chosen according to the method.
def sort_by_method(resource: ApiResource):
    method = resource.request_id.method.name.upper()
    if method == "Get".upper():
        return 5
    elif method == "Patch".upper():
        return 4
    elif method == "Put".upper():
        return 3
    elif method == "Post".upper():
        return 2
    elif method == "Delete".upper():
        return 1
    else:
        return 6


def sort_by_order(resource: ApiResource):
    method = resource.request_id.method.name.upper()
    if method == "Get".upper():
        return 2
    elif method == "Patch".upper():
        return 3
    elif method == "Put".upper():
        return 5
    elif method == "Post".upper():
        return 4
    elif method == "Delete".upper():
        return 1
    else:
        return 6


def sort_by_parameter_kind(param_kind: ParameterKind):
    if param_kind == ParameterKind.Path:
        return 1
    elif param_kind == ParameterKind.Query:
        return 3
    elif param_kind == ParameterKind.Header:
        return 4
    elif param_kind == ParameterKind.Body:
        return 2


def sort_by_parameter_kind_debug(param_kind: ParameterKind):
    if param_kind == ParameterKind.Path:
        return 2
    elif param_kind == ParameterKind.Query:
        return 1
    elif param_kind == ParameterKind.Header:
        return 4
    elif param_kind == ParameterKind.Body:
        return 3


# When choosing among several producers, the order in which
# they should be chosen.
inferred_match_sort_unique_sort_index = 0


def inferred_match_sort(resource: ApiResource):
    global inferred_match_sort_unique_sort_index
    inferred_match_sort_unique_sort_index += 1
    return (sort_by_method(resource),
            get_producers_sort_id(resource),
            0 if resource.access_path is None else len(resource.resource_reference.get_access_path_parts().path),
            threading.get_ident())  # For tuple uniqueness


def debug_inferred_match_sort_order(resource: ApiResource):
    global inferred_match_sort_unique_sort_index
    inferred_match_sort_unique_sort_index += 1
    return (sort_by_order(resource),
            get_producers_sort_id(resource),
            0 if resource.access_path is None else len(resource.resource_reference.get_access_path_parts().path),
            threading.get_ident())


def get_producers_sort_id(resource_info: ApiResource):
    if resource_info.request_id.method == OperationMethod.Get:
        # When choosing a GET producer, pick the one with a path parameter
        # at the end. This attempts to avoid GET requests that always succeed,
        # but may return an empty list of results.
        if resource_info.request_id.endpoint.endswith("}"):
            return 2
        else:
            return 3
    else:
        return 1


class SortedMatchProducer:
    sorted_by_method: int
    sorted_by_request_id: int
    sorted_by_access_path: int
    producer: Union[Producer, Consumer]

    def __init__(self, sorted_by_method: int,
                 sorted_by_request_id: int,
                 sorted_by_access_path: int,
                 producer: Union[Producer, Consumer]):
        self.sorted_by_method = sorted_by_method
        self.sorted_by_request_id = sorted_by_request_id
        self.sorted_by_access_path = sorted_by_access_path
        self.producer = producer

    def __dict__(self):
        return {"SortedByMethod": self.sorted_by_method,
                "SortedByRequestID": self.sorted_by_request_id,
                "SortedByAccessPath": self.sorted_by_access_path,
                "Producer": self.producer.__dict__()}


class ProducerIndexes:
    sorted_by_match: List[SortedMatchProducer]
    sorted_by_match_non_nested: List[SortedMatchProducer]
    indexed_by_endpoint: Dict[RequestId, List[Producer]]
    same_payload_producers: Dict[RequestId, List[BodyPayloadInputProducer]]
    indexed_by_type_name: Dict[RequestId, List[ResponseProducer]]
    input_only_producers: List[InputOnlyProducer]

    def __init__(self):
        self.sorted_by_match = []
        self.sorted_by_match_non_nested = []
        self.indexed_by_endpoint = {}
        self.same_payload_producers = {}
        self.indexed_by_type_name = {}
        self.input_only_producers = []

    def __dict__(self):
        dict_value = {}
        sorted_by_match = []
        if len(self.sorted_by_match) > 0:
            for item in self.sorted_by_match:
                sorted_by_match.append(item.__dict__())
            if len(sorted_by_match) > 0:
                dict_value["SortedByMatch"] = sorted_by_match

        if len(self.sorted_by_match_non_nested) > 0:
            sorted_by_match_non_nested = []
            for item in self.sorted_by_match_non_nested:
                sorted_by_match_non_nested.append(item.__dict__())
            if len(sorted_by_match_non_nested) > 0:
                dict_value["SortedByMatchNonNested"] = sorted_by_match_non_nested

        if len(self.indexed_by_endpoint) > 0:
            endpoint_list = []
            for keys, values in self.indexed_by_endpoint.items():
                by_endpoint_list = []
                endpoint_dict = {}
                for item in values:
                    by_endpoint_list.append(item.__dict__())
                endpoint_dict[keys] = by_endpoint_list
                endpoint_list.append(endpoint_dict)
            dict_value["IndexByEndpoint"] = endpoint_list

        if len(self.indexed_by_type_name) > 0:
            index_by_type_name = []
            for keys, values in self.indexed_by_type_name.items():
                by_index_list = []
                endpoint_dict = {}
                for item in values:
                    by_index_list.append(item.__dict__())
                endpoint_dict[keys] = {"ResponseProducer": by_index_list}
                index_by_type_name.append(endpoint_dict)
            dict_value["IndexByTypeName"] = index_by_type_name

        if len(self.same_payload_producers) > 0:
            same_payload_dict = {}
            for keys, values in self.same_payload_producers.items():
                by_endpoint_list = []
                for item in values:
                    by_endpoint_list.append(item.__dict__())
                same_payload_dict[keys] = by_endpoint_list
            dict_value["SamePayloadProducers"] = same_payload_dict

        if len(self.input_only_producers) > 0:
            input_only_producers = []
            for item in self.input_only_producers:
                if item is not None:
                    input_only_producers.append(item.__dict__())
            if len(input_only_producers) > 0:
                dict_value["InputOnlyProducers"] = input_only_producers

        return dict_value


class Producers:
    def __init__(self):
        self.producers = {}

    def __dict__(self):
        dict_value = {}
        for keys, values in self.producers.items():
            if isinstance(values, ProducerIndexes):
                dict_value[keys] = values.__dict__()
            else:
                dict_value[keys] = values
        return dict_value

    def try_add(self, resource_name):
        if resource_name not in self.producers.keys():
            self.producers[resource_name] = ProducerIndexes()

        return self.producers[resource_name]

    def try_get(self, resource_name):
        return self.producers.get(resource_name, None)

    def add_response_producer(self, resource_name, producer: Producer):
        resource_producers = self.try_add(resource_name)
        sorted_key_by_method = sort_by_method(producer)
        sorted_key_by_request_id = get_producers_sort_id(producer)
        sorted_key_by_access_path = 0
        if producer.access_path is not None:
            sorted_key_by_access_path = len(producer.access_path_parts.path)

        resource_producers.sorted_by_match.append(SortedMatchProducer(sorted_by_method=sorted_key_by_method,
                                                                      sorted_by_request_id=sorted_key_by_request_id,
                                                                      sorted_by_access_path=sorted_key_by_access_path,
                                                                      producer=producer))

        if not producer.is_nested_body_resource:
            resource_producers.sorted_by_match_non_nested.append(
                SortedMatchProducer(sorted_by_method=sorted_key_by_method,
                                    sorted_by_request_id=sorted_key_by_request_id,
                                    sorted_by_access_path=sorted_key_by_access_path,
                                    producer=producer))

        resource_producers.indexed_by_endpoint.setdefault(producer.request_id.endpoint, []).append(producer)

        for tn in producer.candidate_type_names:
            resource_producers.indexed_by_type_name.setdefault(tn, []).append(producer)

    def add_same_payload_producer(self, resource_name, producer):
        resource_producers = self.try_add(resource_name)
        resource_producers.same_payload_producers.setdefault(producer.request_id.endpoint, []).append(producer)
        resource_producers.indexed_by_endpoint.setdefault(producer.request_id.endpoint, []).append(producer)

    def get_same_payload_producers(self, producer_resource_name, request_id):
        p = self.try_get(producer_resource_name)
        if p is None:
            return None
        return p.same_payload_producers.get(request_id.endpoint, [])

    def add_input_only_producer(self, resource_name, producer: Producer):
        resource_producers = self.try_add(resource_name)
        for item in resource_producers.input_only_producers:
            if item == producer:
                return
        resource_producers.input_only_producers.append(producer)
        resource_producers.indexed_by_endpoint.setdefault(producer.request_id.endpoint, []).append(producer)

    def get_input_only_producers(self, producer_resource_name):
        p = self.try_get(producer_resource_name)
        if p is None:
            return []

        return p.input_only_producers

    def get_indexed_by_endpoint_producers(self, producer_resource_name: str, endpoint: str, operations: list):
        p = self.try_get(producer_resource_name)
        if p is None:
            return []
        index_endpoint_producers = p.indexed_by_endpoint.get(endpoint, [])

        result = []
        for m in operations:
            for item in index_endpoint_producers:
                if isinstance(item, ResponseProducer) and item.request_id.method == m:
                    result.append(item)
        return result

    def get_indexed_by_type_name_producers(self, producer_resource_name, type_name):
        p = self.try_get(producer_resource_name)
        if p is None:
            return []

        return p.indexed_by_type_name.get(type_name, [])

    def get_sorted_by_match_producers(self, producer_resource_name, include_nested_producers):
        p = self.try_get(producer_resource_name)
        if p is None:
            return []

        if include_nested_producers:
            return list(p.sorted_by_match)
        else:
            return list(p.sorted_by_match_non_nested)


class ProducerKind(enum.Enum):
    Input = 1
    Response = 2


def is_path_parameter(p):
    return p.startswith("{")


def try_get_path_parameter_name(p):
    if is_path_parameter(p):
        return p[1:-1]
    return None


def format_path_parameter(name):
    return "{{{}}}".format(name)


def parameter_names_equal(name1, name2):
    return name1.lower() == name2.lower()


class PathPartType(enum.Enum):
    Constant = 0
    Separator = 1
    Parameter = 2


class PathPart:
    part_type: PathPartType
    value: str

    def __init__(self, part_type: PathPartType, value: str):
        self.part_type = part_type
        self.value = value


def get_path_parts(path_parts: list[PathPart]):
    return [part.value if part.part_type == PathPartType.Constant else format_path_parameter(
        part.value) if part.part_type == PathPartType.Parameter else "/" for part in path_parts]


class Path:
    path: list[PathPart]

    def __init__(self, path: list[PathPart]):
        self.path = path

    def get_path(self):
        return "".join(get_path_parts(self.path))

    def contains_parameter(self, name):
        return any(part.value.lower() == name.lower() for part in self.path if part.part_type == PathPartType.Parameter)

    def get_path_parts_before_parameter(self, name):
        path_until_parameter = []
        for part in self.path:
            if part.part_type == PathPartType.Parameter and parameter_names_equal(part.value, name):
                break
            else:
                path_until_parameter.append(part)
        return get_path_parts(path_until_parameter)


def get_path_from_string(path, include_separators):
    param_split_regex_pattern = r'({[^}]+})'
    parts = [p for p in path.split('/') if p]
    parts_partitioned_by_parameter: list[PathPart] = []
    for i, p in enumerate(parts):
        sub_parts = re.split(param_split_regex_pattern, p)
        sub_parts = [x if try_get_path_parameter_name(x) else x for x in sub_parts if x]
        sub_parts = [
            PathPart(PathPartType.Parameter, try_get_path_parameter_name(x)) if is_path_parameter(x) else
            PathPart(PathPartType.Constant, x)
            for x in sub_parts if x]
        if include_separators:
            parts_partitioned_by_parameter.extend([PathPart(PathPartType.Separator, "/")] + sub_parts)
        else:
            parts_partitioned_by_parameter.extend(sub_parts)
    return Path(parts_partitioned_by_parameter)
