# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from enum import Enum
from abc import abstractmethod
import re
import inflect
from typing import Union, Optional, List
from rest.compiler.access_paths import AccessPath
from rest.compiler.grammar import (
    PrimitiveType,
    PrimitiveTypeEnum,
    ParameterKind,
    RequestId,
    CustomPayloadType,
    ProducerConsumerAnnotation)
from rest.compiler.config import ConfigSetting
from rest.restler.utils import restler_logger as logger

inflect_engine = inflect.engine()


class NamingConvention(Enum):
    CamelCase = 1
    PascalCase = 2
    HyphenSeparator = 3
    UnderscoreSeparator = 4


# getContainerPartFromBody
def get_container_part_from_body(json_pointer):
    """
    从 JSON 指针中移除数组索引，并返回倒数第二个属性部分作为容器部分。

    @param json_pointer: 请求体中的 JSON 指针
    @return: 容器部分，或 None
    @rtype: Optional[str]
    """
    # 移除数组索引
    properties_only = [x for x in json_pointer.path if not (x.startswith('[') and x.endswith(']'))]
    return properties_only[-2] if len(properties_only) >= 2 else None


# 资源引用类，标识API规范中的资源，通过路径、查询或请求体中的信息来定义
# Path: defined by the full path parts, up to the name.
# Query: defined by the name only.
# Body: defined by the json pointer to the resource.
#
# Every resource is considered in the context of its API (endpoint and method).
class ResourceReference:
    name: str  # 资源名称

    def __init__(self, name):
        """ 初始化资源引用类

        @param name: 资源名称
        """
        self.name = name

    def __dict__(self):
        return {"name": self.name}

    def __eq__(self, other):
        if isinstance(other, ResourceReference):
            if self.name == other.name:
                return True
            else:
                return False
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    @abstractmethod
    def get_access_path_parts(self):
        return NotImplemented

    @abstractmethod
    def get_body_container_name(self):
        return NotImplemented

    @abstractmethod
    def get_resource_name(self):
        return NotImplemented

    @abstractmethod
    def get_access_path(self):
        return NotImplemented

    @abstractmethod
    def is_nested_body_resource(self):
        return NotImplemented

    # If the path to property contains at least 2 identifiers, then it has a body container.
    # getContainerName
    @abstractmethod
    def get_container_name(self, endpoint_parts):
        return NotImplemented

    @abstractmethod
    def get_parent_access_path(self):
        return NotImplemented


# 继承自 ResourceReference，表示请求体中传递或响应中的参数资源引用
# Reference to a parameter passed in the body of a request
# or returned in a response
class BodyResource(ResourceReference):
    full_path: AccessPath  # 资源的完整路径

    def __init__(self, name: str, full_path: list):
        """ 初始化请求体资源引用类

        @param name: 资源名称
        @param full_path: 资源的访问路径
        """
        super().__init__(name)
        self.full_path = AccessPath(full_path)

    def __dict__(self):
        return {"BodyResource": {"name": self.name,
                                 "fullPath": {"path": self.full_path.path}
                                 }
                }

    def __eq__(self, other):
        if isinstance(other, BodyResource):
            return self.name == other.name and self.full_path == other.full_path
        else:
            return False

    def __hash__(self):
        return hash((self.name, self.full_path.__str__()))

    def get_access_path_parts(self):
        return self.full_path

    def get_body_container_name(self):
        logger.write_to_main(f"full_path={self.full_path}   "
                             f"contain_body={get_container_part_from_body(self.full_path)}",
                             ConfigSetting().LogConfig.api_resource)
        return get_container_part_from_body(self.full_path)

    def get_resource_name(self):
        return self.full_path.get_name_part()

    def get_access_path(self):
        return self.full_path.get_json_pointer()

    def is_nested_body_resource(self):
        return len(self.full_path.get_path_property_name_parts()) > 1

    def get_container_name(self, endpoint_parts):
        if self.is_nested_body_resource():
            return self.get_body_container_name()
        else:
            return get_container_part_from_path(endpoint_parts)

    def get_parent_access_path(self):
        return self.full_path.get_parent_path()


# The path up to the parameter name
class PathResource(ResourceReference):
    path_to_parameter: []  # 参数的路径
    response_path: AccessPath  # 响应路径

    def __init__(self, name: str, path_to_parameter: [], response_path: AccessPath):
        """ 初始化路径资源类

        @param name: 资源名称
        @param path_to_parameter: 参数的路径
        @param response_path: 响应路径
        """
        super().__init__(name)
        self.path_to_parameter = path_to_parameter
        self.response_path = response_path

    def __dict__(self):
        return {"PathResource": {"name": self.name,
                                 "pathToParameter": self.path_to_parameter,
                                 "responsePath": {"path": self.response_path.path}
                                 }
                }

    def __eq__(self, other):
        if isinstance(other, PathResource):
            if len(self.path_to_parameter) == len(other.path_to_parameter):
                for i in (0, len(self.path_to_parameter) - 1):
                    if self.path_to_parameter[i] != other.path_to_parameter[i]:
                        return False
            return self.name == other.name and self.response_path == other.response_path
        else:
            return False

    def __hash__(self):
        return hash((self.name, self.response_path.__str__(), "".join(self.path_to_parameter)))

    def get_access_path_parts(self):
        return self.response_path

    # getBodyContainerName
    def get_body_container_name(self):
        logger.write_to_main(f"response_path={self.response_path} "
                             f"body_container_name={get_container_part_from_body(self.response_path)}",
                             ConfigSetting().LogConfig.api_resource)
        return get_container_part_from_body(self.response_path)

    def get_resource_name(self):
        return self.name

    def get_access_path(self):
        return self.response_path.get_json_pointer()

    def is_nested_body_resource(self):
        return False

    def get_container_name(self, endpoint_parts):
        logger.write_to_main(f"resource_reference.path_to_parameter={self.path_to_parameter}",
                             ConfigSetting().LogConfig.api_resource)
        return get_container_part_from_path(self.path_to_parameter)

    def get_parent_access_path(self):
        return None


class QueryResource(ResourceReference):
    def __init__(self, name):
        super().__init__(name)

    def __dict__(self):
        return {"QueryResource": self.name}

    def get_access_path_parts(self):
        return AccessPath(path=[])

    def get_body_container_name(self):
        return None

    def get_resource_name(self):
        return self.name

    def get_access_path(self):
        return None

    def is_nested_body_resource(self):
        return False

    def get_container_name(self, endpoint_parts):
        return get_container_part_from_path(endpoint_parts)

    def get_parent_access_path(self):
        return None


class HeaderResource(ResourceReference):
    def __init__(self, name):
        super().__init__(name)

    def __dict__(self):
        return {"name": self.name}

    def get_access_path_parts(self):
        return AccessPath(path=[])

    def get_body_container_name(self):
        return None

    def get_resource_name(self):
        return self.name

    def get_access_path(self):
        return None

    def is_nested_body_resource(self):
        return False

    def get_container_name(self, endpoint_parts):
        return get_container_part_from_path(endpoint_parts)

    def get_parent_access_path(self):
        return None


# Gets the first non path parameter of this endpoint
# getContainerPartFromPath
def get_container_part_from_path(path_parts: List[str]) -> Optional[str]:
    """
    从路径部分推断容器名称，优先检查最后和倒数第二个部分。
    ["users", "accounts"]      # Output: "accounts"
    ["users", "{user_id}"]     # Output: "users"
    ["{user_id}"]              # Output: None
    []                         # Output: None
    @param path_parts: 路径部分列表
    @return: 容器名称，或 None
    @rtype: Optional[str]
    """
    logger.write_to_main(f"path_parts={path_parts}", ConfigSetting().LogConfig.api_resource)
    if len(path_parts) == 0:
        return None

    def get_container(path_part: Optional[str]) -> Optional[str]:
        if path_part is None:
            return None
        if path_part.startswith("{"):
            return None
        return path_part

    # 检查路径最后两个部分是否为容器
    possible_containers = []
    # The last part may be a container (e.g. for POST)
    # If not, then try to find it in the second part.

    # Try the last part and then the second-to-last part
    possible_containers = [
        get_container(path_parts[-1]) if len(path_parts) > 0 else None,
        get_container(path_parts[-2]) if len(path_parts) > 1 else None,
    ]

    # Filter out None values and return the first non-None container
    return next((container for container in possible_containers if container is not None), None)


def custom_singularize(word: str) -> str:
    """
    Custom singularization to handle compound words and edge cases.
    Splits compound words, singularizes valid plural parts, and reassembles them.
    """

    # Exception list for terms that should not be singularized or require special handling
    singularization_exceptions = {
        "data": "data",
        "address": "address"  # Prevents incorrect singularization to "addres"
    }

    # Split compound words using regex
    words = re.split(r'[-]|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', word)

    def singularize_part(part: str) -> str:
        if part.lower() in singularization_exceptions:
            return singularization_exceptions[part.lower()]
        singular = inflect_engine.singular_noun(part)
        return singular if singular else part

    # Singularize each part and reassemble
    singularized_parts = [singularize_part(w) for w in words]
    return '-'.join(singularized_parts)


# getConvention
# Infer the naming convention.
# The naming convention is inferred from the container if present.
# Otherwise, infer it from the resource name.
# If not possible to infer, the default (camel case) is used.
def get_convention(s):
    """
    根据资源名称推断命名约定。
    PascalCase->NamingConvention.PascalCase
    camelCase->NamingConvention.CamelCase
    snake_case->NamingConvention.UnderscoreSeparator
    kebab-case->NamingConvention.HyphenSeparator
    ALLCAPS->NamingConvention.CamelCase (default)

    @param s: 资源名称字符串或列表
    @return: 命名约定
    @rtype: NamingConvention
    """
    has_upper = any(c.isupper() for c in s)
    has_lower = any(c.islower() for c in s)
    has_underscores = '_' in s
    has_hyphens = '-' in s
    starts_with_upper = s[0].isupper() if s else False

    if has_upper and has_lower:
        return NamingConvention.PascalCase if starts_with_upper else NamingConvention.CamelCase
    elif has_underscores:
        return NamingConvention.UnderscoreSeparator
    elif has_hyphens:
        return NamingConvention.HyphenSeparator
    else:
        return NamingConvention.CamelCase  # 默认使用驼峰命名


# Define regex patterns for splitting based on naming conventions
RegexSplitMap = {
    NamingConvention.PascalCase: re.compile(
        r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=[A-Z][a-z])'),
    NamingConvention.CamelCase: re.compile(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=[A-Z][a-z])'),
    NamingConvention.UnderscoreSeparator: re.compile(r'_'),
    NamingConvention.HyphenSeparator: re.compile(r'-'),
}


# getTypeWords
def get_type_words(name: str, naming_convention: Optional[NamingConvention] = None) -> List[str]:
    """
    Splits the input name into its constituent words based on the inferred or provided naming convention.

    :param name: The input string to split.
    :param naming_convention: The naming convention to use for splitting. If None, it is inferred.
    :return: A list of words obtained from the input string.
    :raises ValueError: If the naming convention cannot be determined or if the name is invalid.
    """
    if not name:
        return []
    if not isinstance(name, str):
        raise TypeError("Input name must be a string.")

    # Infer the naming convention if not provided
    type_naming_convention = naming_convention or get_convention(name)

    # Ensure the naming convention is supported
    if type_naming_convention not in RegexSplitMap:
        raise ValueError(f"Unsupported naming convention: {type_naming_convention}")

    # Handle hyphen-separated names explicitly
    if "-" in name:
        return [word.lower() for word in name.split("-")]

    # Split the name based on its convention
    name_regex_split = RegexSplitMap[type_naming_convention]
    return [word.lower() for word in name_regex_split.split(name) if word]


# Gets the candidate type names for this resource, based on its container.
# This function currently uses heuristics to infer a set of possible type names
# based on the word parts of the container name, as determined by naming convention.
# Note: this function normalizes the original identifier names after splitting the names
# based on naming convention.  Make sure producer-consumer inference
# uses only the normalized type names.
def get_candidate_type_names(container_name,
                             naming_convention,
                             body_container_name,
                             resource_name,
                             resource_name_words):
    normalized_separator = "__"
    if container_name:
        # Singularize the container name
        container_name_without_plural = custom_singularize(container_name)
        container_words = get_type_words(container_name_without_plural, naming_convention)

        if not body_container_name:
            # Top-level container is just the container name
            return [normalized_separator.join(container_words)]
        else:
            # Generate candidate names with suffixes and suffix removal
            candidate_type_names = []

            # Add all suffixes
            for i in range(len(container_words)):
                candidate_type_names.append(normalized_separator.join(container_words[i:]))
            # Add combinations up to second-to-last word for intermediate granularities
            for i in range(1, len(container_words) - 1):
                candidate_type_names.append(normalized_separator.join(container_words[:i + 1]))

            return candidate_type_names
    else:
        # Handle the case where container_name is absent
        if not resource_name_words:
            raise Exception("The resource name must be non-empty.")

        primary_parameter_name = (
            resource_name_words[0]
            if len(resource_name_words) == 1
            else normalized_separator.join(resource_name_words[:-1])
        )
        return [primary_parameter_name]


# The resource id.
# The type name is inferred during construction.
# Note: resource IDs may use several naming conventions in the same one.  This is not currently supported.
# For example: "/admin/pre-receive-environments/{pre_receive_environment_id}"
class ApiResource:
    # The request ID in which this resource is declared in the API spec
    request_id: RequestId
    # The reference identifying the resource
    resource_reference: ResourceReference

    # The name of the resource container, if it exists.
    # The container is the static parent of this resource - if the immediate parent
    # is a path parameter, this is considered as container not defined.
    container_name: []
    body_container_name: []
    path_container_name: []

    # The inferred type name of the resource
    # These are expected to be sorted in order of most specific to least specific type
    candidate_type_names: []

    # The naming convention.  (Required for serialization.)
    naming_convention: NamingConvention
    access_path: AccessPath
    access_path_parts: AccessPath
    parent_access_path: AccessPath
    resource_name: str

    # Gets the variable name that should be present in the response
    # Example: /api/accounts/{accountId}
    #   * the var name is "Id" --> "id"
    producer_parameter_name: []
    is_nested_body_resource: bool
    primitive_type: PrimitiveType

    def __init__(self,
                 request_id: RequestId,
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType):
        if request_id.xMsPath is not None:
            endpoint_parts = request_id.xMsPath.get_normalized_endpoint().split('/')
        else:
            endpoint_parts = request_id.endpoint.split('/')
        logger.write_to_main(f"endpoint_parts={endpoint_parts}", ConfigSetting().LogConfig.api_resource)

        # The request ID in which this resource is declared in the API spec
        self.request_id = request_id

        # The reference identifying the resource
        self.resource_reference = resource_reference

        # The name of the resource container, if it exists.
        # The container is the static parent of this resource - if the immediate parent
        # is a path parameter, this is considered as container not defined.
        self.container_name = resource_reference.get_container_name(endpoint_parts)
        self.body_container_name = resource_reference.get_body_container_name()
        self.path_container_name = get_container_part_from_path(endpoint_parts)

        self.resource_name = resource_reference.get_resource_name()
        resource_name_words = get_type_words(self.resource_name, naming_convention)

        type_name = get_candidate_type_names(self.container_name,
                                             naming_convention,
                                             self.body_container_name,
                                             self.resource_name,
                                             resource_name_words)
        logger.write_to_main(f"type_name={type_name}", ConfigSetting().LogConfig.api_resource)
        self.candidate_type_names = [x.lower() for x in type_name]
        logger.write_to_main(f"candidate_type_names="
                             f"{self.candidate_type_names}", ConfigSetting().LogConfig.api_resource)
        self.naming_convention = naming_convention
        self.access_path = resource_reference.get_access_path()
        self.access_path_parts = resource_reference.get_access_path_parts()
        self.parent_access_path = resource_reference.get_parent_access_path()

        self.producer_parameter_name = resource_name_words[-1].lower() \
            if resource_name_words else self.resource_name
        self.is_nested_body_resource = resource_reference.is_nested_body_resource()
        self.primitive_type = primitive_type

    def __dict__(self):
        dict_value = {"RequestId": self.request_id.__dict__(),
                      "ResourceReference": self.resource_reference.__dict__(),
                      "ContainerName": self.container_name
                      }
        if self.body_container_name is not None:
            dict_value["BodyContainerName"] = self.body_container_name
        if self.path_container_name:
            dict_value["PathContainerName"] = self.path_container_name
        dict_value["CandidateTypeNames"] = self.candidate_type_names
        if self.access_path is not None:
            dict_value["AccessPath"] = "/".join(self.access_path_parts.path)
        dict_value["AccessPathParts"] = {
            "path": self.access_path_parts.path if self.access_path_parts is not None else ""}
        dict_value["ResourceName"] = self.resource_name
        dict_value["ProducerParameterName"] = self.producer_parameter_name
        dict_value["IsNestedBodyResource"] = self.is_nested_body_resource
        if isinstance(self.primitive_type, PrimitiveTypeEnum):
            dict_value["PrimitiveType"] = self.primitive_type.api_resource_dict()
        else:
            dict_value["PrimitiveType"] = self.primitive_type.name
        return dict_value

    def __eq__(self, other):
        if isinstance(other, ApiResource) and type(self.resource_reference) == type(other.resource_reference):
            return (self.request_id == other.request_id
                    and self.resource_reference == other.resource_reference
                    and self.naming_convention == other.naming_convention
                    and self.primitive_type == other.primitive_type)
        return False

    def __hash__(self):
        return hash((self.resource_reference, self.request_id, self.naming_convention, self.primitive_type))


# A consumer resource.  For example, the 'accountId' path parameter in the below request
# 'accountId', '/api/accounts/{accountId}', GET
class Consumer:
    def __init__(self,
                 consumer_id: ApiResource,
                 parameter_kind: ParameterKind,
                 annotation: Optional[ProducerConsumerAnnotation]):
        self.consumer_id = consumer_id

        # The parameter type of the consumer
        self.parameter_kind = parameter_kind

        # The annotation for this consumer, if specified
        self.annotation = annotation

    def __dict__(self):
        dict_value = {"id": self.consumer_id.__dict__(), "parameterKind": self.parameter_kind.name}
        if self.annotation:
            dict_value["annotation"] = self.annotation.__dict__()
        return dict_value


# A producer resource.  For example, the 'accountId' property returned in the response of
# the below request.
# '/api/userInfo', GET
class Producer(ApiResource):
    def __init__(self, request_id: RequestId,
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType):
        super().__init__(request_id, resource_reference, naming_convention, primitive_type)

    def __dict__(self):
        return {"id": super().__dict__()}


# A resource value produced in a response of the specified request.
class ResponseProducer(Producer):
    def __init__(self, request_id: RequestId,
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType):
        super().__init__(request_id, resource_reference, naming_convention, primitive_type)

    def __int__(self, producer: Producer):
        request_id = producer.request_id
        resource_reference = producer.resource_reference
        naming_convention = producer.naming_convention
        primitive_type = producer.primitive_type

        super().__init__(request_id, resource_reference, naming_convention, primitive_type)

    def __dict__(self):
        return {"ResponseObject": super().__dict__()}


# A producer in the body of the request, the value of which gets set with the input payload.
# This is a producer for a consumer in the body of the same request.
#  A resource value that comes from the same body payload.
class BodyPayloadInputProducer(Producer):
    def __init__(self, request_id: RequestId,
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType):
        super().__init__(request_id, resource_reference, naming_convention, primitive_type)

    def __dict__(self):
        super().__dict__()


class OrderingConstraintProducer(Producer):
    def __init__(self,
                 request_id: RequestId,  # The request ID of the source request
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType):
        super().__init__(request_id, resource_reference, naming_convention, primitive_type)

    def __dict__(self):
        return super().__dict__()


# A producer in the request that is not returned in the response
# Example: unique ID specified by a user.

# A resource value that is produced when assigned
# Currently, only assigning such values from the dictionary is supported.
# The dictionary payload is an option type because it is only present when
# the initial payload is being generated.
# (producer, dictionary payload, isWriter)
# When 'isWriter' is true, this is a writer variable that should be generated
# with the original payload.
class InputOnlyProducer(Producer):
    def __init__(self, request_id: RequestId,
                 resource_reference,
                 naming_convention: NamingConvention,
                 primitive_type: PrimitiveType,
                 parameter_kind: ParameterKind):
        super().__init__(request_id, resource_reference, naming_convention, primitive_type)
        self.parameter_kind = parameter_kind

    def __dict__(self):
        ret_result = super().__dict__()
        ret_result["parameterKind"] = self.parameter_kind.title()
        return ret_result

    def get_input_parameter_access_path(self):
        if self.access_path is not None:
            return self.access_path_parts
        else:
            return AccessPath([self.resource_name, self.parameter_kind.lower()])


# A resource value specified as a payload in the custom dictionary.
# (payloadType, consumerResourceName, isObject)
# To be converted to 'consumerResourcePath' in VSTS#7191
class DictionaryPayload:
    def __init__(self, payload_type: CustomPayloadType, primitive_type, name, is_object):
        self.payload_type = payload_type
        self.primitive_type = primitive_type
        self.name = name
        self.is_object = is_object

    def __dict__(self):
        return {
            "DictionaryPayload":
                {
                    "payloadType": self.payload_type.name,
                    "primitiveType": self.primitive_type.name,
                    "name": self.name,
                    "isObject": self.is_object
                }
        }


# A resource value that is produced when assigned
# Currently, only assigning such values from the dictionary is supported.
# The dictionary payload is an option type because it is only present when
# the initial payload is being generated.
# (producer, dictionary payload, isWriter)
# When 'isWriter' is true, this is a writer variable that should be generated
# with the original payload.
class InputParameter:
    def __init__(self, producer: InputOnlyProducer, dictionary_payload: Optional[DictionaryPayload], is_writer: bool):
        self.input_only_producer = producer
        self.dictionary_payload = dictionary_payload
        self.is_writer = is_writer

    def __dict__(self):
        ret_value = {}
        item = []
        if self.input_only_producer:
            item.append(self.input_only_producer.__dict__())
        if self.dictionary_payload is None:
            item.append(self.dictionary_payload)
        else:
            item.append(self.dictionary_payload.__dict__())
        item.append(self.is_writer)
        ret_value["InputParameter"] = item
        return ret_value


class ProducerConsumerDependency:
    def __init__(self, consumer: Consumer, producer=Union[Producer, None]):
        # The consumer of the resource.
        # Any consumer, as described by the 'Consumer' type above, is valid in this context.
        # For example: 'accountId', '/api/accounts/{accountId}/users', PUT
        self.consumer = consumer

        # The producer of the resource.  Any producer, as described by the 'Producer' type
        # above, is valid in this context.
        # '/api/userInfo', GET,
        self.producer = producer

    def __dict__(self):
        ret_value = {"consumer": self.consumer.__dict__()}
        if self.producer:
            ret_value["producer"] = self.producer.__dict__()
        return ret_value
