# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import json
from collections import defaultdict
from typing import List, Dict, Optional
from rest.compiler.access_paths import try_get_access_path_from_string
from rest.compiler.grammar import (
    ParameterKind,
    PrimitiveType,
    CustomPayloadType,
    DefaultPrimitiveValues)
from rest.compiler.apiresource import DictionaryPayload
from rest.compiler.utilities import JsonSerialization
from rest.compiler.config import ConfigSetting
from rest.restler.utils import restler_logger as logger


class InvalidMutationsDictionaryFormat(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def DictionarySetting():
    """ Accessor for the RestlerSettings singleton """
    return MutationsDictionary.Instance()


def find_payload_entry(payload_map, entry_name):
    if payload_map is not None:
        return payload_map.get(entry_name, None)
    else:
        return None


def find_path_payload_entry(payload_map, entry_path):
    if payload_map is None:
        return None
    else:
        p_map = payload_map
        filtered_map = {k: v for k, v in p_map.items() if try_get_access_path_from_string(k) == entry_path}
        return next(iter(filtered_map.values()), None)


def get_request_type_payload_prefix(endpoint, method):
    return f"{endpoint}/{method.name.lower()}/"


def get_request_type_payload_name(endpoint, method, property_name_or_path):
    prefix = get_request_type_payload_prefix(endpoint, method)
    return f"{prefix}{property_name_or_path}"


def is_request_type_payload_name(endpoint, method, property_value):
    prefix = get_request_type_payload_prefix(endpoint, method)
    return property_value.startswith(prefix)


def get_keys(map_list):
    logger.write_to_main(f"map_list={map_list}", ConfigSetting().LogConfig.dictionary)
    keys = []
    for custom_payload_entries in map_list:
        if custom_payload_entries:
            logger.write_to_main(f"custom_payload_entries={custom_payload_entries}",
                                 ConfigSetting().LogConfig.dictionary)
            keys.extend(custom_payload_entries.keys())
    logger.write_to_main(f"key={keys}", ConfigSetting().LogConfig.dictionary)
    return keys


# Combines the elements of the two dictionaries
def combine_dict(one_dict, second_dict):
    if one_dict is None and second_dict is None:
        return {}
    elif one_dict is None and len(second_dict) > 1:
        return second_dict
    elif len(one_dict) > 0 and second_dict is None:
        return one_dict
    else:
        merged_dict = defaultdict(list)

        # 合并逻辑
        for d in (one_dict, second_dict):
            for key, value in d.items():
                if value not in merged_dict[key]:
                    merged_dict[key].append(value)

        combined_suffix = dict((k, v[0] if len(v) == 1 else v) for k, v in merged_dict.items())

        return combined_suffix


class MutationsDictionary:
    __instance = None
    restler_fuzzable_string: Optional[List[str]]
    restler_fuzzable_string_unquoted: Optional[List[str]]
    restler_fuzzable_datetime: Optional[List[str]]
    restler_fuzzable_datetime_unquoted: Optional[List[str]]
    restler_fuzzable_date: Optional[List[str]]
    restler_fuzzable_date_unquoted: Optional[List[str]]
    restler_fuzzable_uuid4: Optional[List[str]]
    restler_fuzzable_uuid4_unquoted: Optional[List[str]]
    restler_fuzzable_int: Optional[List[str]]
    restler_fuzzable_number: Optional[List[str]]
    restler_fuzzable_bool: Optional[List[str]]
    restler_fuzzable_object: Optional[List[str]]

    restler_custom_payload: Optional[Dict[str, List[str]]]
    restler_custom_payload_unquoted: Optional[Dict[str, List[str]]]
    restler_custom_payload_uuid4_suffix: Optional[Dict[str, List[str]]]
    restler_custom_payload_header: Optional[Dict[str, List[str]]]
    restler_custom_payload_header_unquoted: Optional[Dict[str, List[str]]]
    restler_custom_payload_query: Optional[Dict[str, List[str]]]
    shadow_values: Optional[Dict[str, Dict[str, List[str]]]]

    def __init__(self):
        self.restler_fuzzable_string = []
        self.restler_fuzzable_string_unquoted = []
        self.restler_fuzzable_datetime = []
        self.restler_fuzzable_datetime_unquoted = []
        self.restler_fuzzable_date = []
        self.restler_fuzzable_date_unquoted = []
        self.restler_fuzzable_uuid4 = []
        self.restler_fuzzable_uuid4_unquoted = []
        self.restler_fuzzable_int = []
        self.restler_fuzzable_number = []
        self.restler_fuzzable_bool = []
        self.restler_fuzzable_object = []

        self.restler_custom_payload = {}
        self.restler_custom_payload_unquoted = {}
        self.restler_custom_payload_uuid4_suffix = {}
        self.restler_custom_payload_header = {}
        self.restler_custom_payload_header_unquoted = {}
        self.restler_custom_payload_query = {}
        self.shadow_values = {}
        MutationsDictionary.__instance = self

    def __dict__(self):
        return_dict = dict()
        return_dict["restler_fuzzable_string"] = self.restler_fuzzable_string
        return_dict["restler_fuzzable_string_unquoted"] = self.restler_fuzzable_string_unquoted
        return_dict["restler_fuzzable_datetime"] = self.restler_fuzzable_datetime
        return_dict["restler_fuzzable_datetime_unquoted"] = self.restler_fuzzable_datetime_unquoted
        return_dict["restler_fuzzable_date"] = self.restler_fuzzable_date
        return_dict["restler_fuzzable_date_unquoted"] = self.restler_fuzzable_date_unquoted
        return_dict["restler_fuzzable_uuid4"] = self.restler_fuzzable_uuid4
        return_dict["restler_fuzzable_uuid4_unquoted"] = self.restler_fuzzable_uuid4_unquoted
        return_dict["restler_fuzzable_int"] = self.restler_fuzzable_int
        return_dict["restler_fuzzable_number"] = self.restler_fuzzable_number
        return_dict["restler_fuzzable_bool"] = self.restler_fuzzable_bool
        return_dict["restler_fuzzable_object"] = self.restler_fuzzable_object
        return_dict["restler_custom_payload"] = self.restler_custom_payload
        return_dict["restler_custom_payload_unquoted"] = self.restler_custom_payload_unquoted
        return_dict["restler_custom_payload_uuid4_suffix"] = self.restler_custom_payload_uuid4_suffix
        if len(self.restler_custom_payload_header) > 0:
            return_dict["restler_custom_payload_header"] = self.restler_custom_payload_header
        if len(self.restler_custom_payload_header_unquoted) > 0:
            return_dict["restler_custom_payload_header_unquoted"] = self.restler_custom_payload_header_unquoted
        if len(self.restler_custom_payload_query) > 0:
            return_dict["restler_custom_payload_query"] = self.restler_custom_payload_query
        if len(self.shadow_values) > 0:
            return_dict["shadow_values"] = self.shadow_values

        return return_dict

    @classmethod
    def init_from_json(cls, json_str):
        self = cls()
        temp_value = json_str.get("restler_fuzzable_string")
        self.restler_fuzzable_string = temp_value if temp_value is not None \
            else [DefaultPrimitiveValues[PrimitiveType.String]]
        self.restler_fuzzable_string_unquoted = json_str.get("restler_fuzzable_string_unquoted") \
            if json_str.get("restler_fuzzable_string_unquoted") else []
        self.restler_fuzzable_datetime = json_str.get("restler_fuzzable_datetime") \
            if json_str.get("restler_fuzzable_datetime") else [DefaultPrimitiveValues[PrimitiveType.DateTime]]
        self.restler_fuzzable_datetime_unquoted = json_str.get("restler_fuzzable_datetime_unquoted") \
            if json_str.get("restler_fuzzable_datetime_unquoted") else []
        self.restler_fuzzable_date = json_str.get("restler_fuzzable_date") \
            if json_str.get("restler_fuzzable_date") else [DefaultPrimitiveValues[PrimitiveType.Date]]
        self.restler_fuzzable_date_unquoted = json_str.get("restler_fuzzable_date_unquoted") \
            if json_str.get("restler_fuzzable_date_unquoted") else []
        self.restler_fuzzable_uuid4 = json_str.get("restler_fuzzable_uuid4") \
            if json_str.get("restler_fuzzable_uuid4") else [DefaultPrimitiveValues[PrimitiveType.Uuid]]
        self.restler_fuzzable_uuid4_unquoted = json_str.get("restler_fuzzable_uuid4_unquoted") \
            if json_str.get("restler_fuzzable_uuid4_unquoted") else []
        self.restler_fuzzable_int = json_str.get("restler_fuzzable_int") \
            if json_str.get("restler_fuzzable_int") else [DefaultPrimitiveValues[PrimitiveType.Int]]
        self.restler_fuzzable_number = json_str.get("restler_fuzzable_number") \
            if json_str.get("restler_fuzzable_number") else [DefaultPrimitiveValues[PrimitiveType.Number]]
        self.restler_fuzzable_bool = json_str.get("restler_fuzzable_bool") \
            if json_str.get("restler_fuzzable_bool") else [DefaultPrimitiveValues[PrimitiveType.Bool]]
        self.restler_fuzzable_object = json_str.get("restler_fuzzable_object") \
            if json_str.get("restler_fuzzable_object") else [DefaultPrimitiveValues[PrimitiveType.Object]]

        self.restler_custom_payload = json_str.get("restler_custom_payload") \
            if json_str.get("restler_custom_payload") else {}
        self.restler_custom_payload_unquoted = json_str.get("restler_custom_payload_unquoted") \
            if json_str.get("restler_custom_payload_unquoted") else {}
        self.restler_custom_payload_uuid4_suffix = json_str.get("restler_custom_payload_uuid4_suffix") \
            if json_str.get("restler_custom_payload_uuid4_suffix") else {}

        self.restler_custom_payload_header = json_str.get("restler_custom_payload_header") \
            if json_str.get("restler_custom_payload_header") else {}
        self.restler_custom_payload_header_unquoted = json_str.get("restler_custom_payload_header_unquoted") \
            if json_str.get("restler_custom_payload_header_unquoted") else {}
        self.restler_custom_payload_query = json_str.get("restler_custom_payload_query") \
            if json_str.get("restler_custom_payload_query") else {}
        self.shadow_values = json_str.get("shadow_values") \
            if json_str.get("shadow_values") else {}

        return self

    def merged_dictionary(self, other):
        if not isinstance(other, MutationsDictionary):
            raise Exception("other is not MutationsDictionary")
        if len(other.restler_fuzzable_string) > 0:
            self.restler_fuzzable_string = list(dict.fromkeys(self.restler_fuzzable_string +
                                                              other.restler_fuzzable_string))

        self.restler_fuzzable_string_unquoted = list(dict.fromkeys(
            self.restler_fuzzable_string_unquoted + other.restler_fuzzable_string_unquoted))
        self.restler_fuzzable_datetime = list(dict.fromkeys(
            self.restler_fuzzable_datetime + other.restler_fuzzable_datetime))
        self.restler_fuzzable_datetime_unquoted = list(dict.fromkeys(
            self.restler_fuzzable_datetime_unquoted + other.restler_fuzzable_datetime_unquoted))
        self.restler_fuzzable_date = list(dict.fromkeys(
            self.restler_fuzzable_date + other.restler_fuzzable_date))
        self.restler_fuzzable_date_unquoted = list(dict.fromkeys(
            self.restler_fuzzable_date_unquoted + other.restler_fuzzable_date_unquoted))
        self.restler_fuzzable_uuid4 = list(dict.fromkeys(
            self.restler_fuzzable_uuid4 + other.restler_fuzzable_uuid4))
        self.restler_fuzzable_uuid4_unquoted = list(dict.fromkeys(
            self.restler_fuzzable_uuid4_unquoted + other.restler_fuzzable_uuid4_unquoted))
        self.restler_fuzzable_int = list(dict.fromkeys(self.restler_fuzzable_int + other.restler_fuzzable_int))
        self.restler_fuzzable_number = list(dict.fromkeys(self.restler_fuzzable_number + other.restler_fuzzable_number))
        self.restler_fuzzable_bool = list(dict.fromkeys(self.restler_fuzzable_bool + other.restler_fuzzable_bool))
        self.restler_fuzzable_object = list(dict.fromkeys(self.restler_fuzzable_object + other.restler_fuzzable_object))

        self.restler_custom_payload = combine_dict(self.restler_custom_payload,
                                                   other.restler_custom_payload)
        self.restler_custom_payload_unquoted = combine_dict(self.restler_custom_payload_unquoted,
                                                            other.restler_custom_payload_unquoted)
        self.restler_custom_payload_uuid4_suffix = combine_dict(self.restler_custom_payload_uuid4_suffix,
                                                                other.restler_custom_payload_uuid4_suffix)
        self.restler_custom_payload_header = combine_dict(self.restler_custom_payload_header,
                                                          other.restler_custom_payload_header)
        self.restler_custom_payload_header_unquoted = combine_dict(self.restler_custom_payload_header_unquoted,
                                                                   other.restler_custom_payload_header_unquoted)
        self.restler_custom_payload_query = combine_dict(self.restler_custom_payload_query,
                                                         other.restler_custom_payload_query)
        self.shadow_values = combine_dict(self.shadow_values,
                                          other.shadow_values)

    def custom_payload_uuid4_suffix(self, dict_value):
        if len(dict_value) > 0:
            self.restler_custom_payload_uuid4_suffix.update(dict_value)
            result = self.restler_custom_payload_uuid4_suffix
            sorted_dict = {key: result[key] for key in sorted(result.keys())}
            self.restler_custom_payload_uuid4_suffix = sorted_dict

    @staticmethod
    def Instance():
        """ Singleton's instance accessor

        @return RestlerSettings instance
        @rtype  RestlerSettings

        """
        if MutationsDictionary.__instance is None:
            raise Exception("config not yet initialized.")
        return MutationsDictionary.__instance

    # findBodyCustomPayload
    def find_body_custom_payload(self, endpoint, method):
        body_payload_name = get_request_type_payload_name(endpoint, method, "__body__")
        return find_payload_entry(self.restler_custom_payload, body_payload_name)

    # Find a custom payload that is specific to the request type
    # The syntax is <endpoint>/<method>/<propertyNameOrPath>
    # Examples:
    #   - Specify values for the parameter 'blogId' anywhere in the payload
    #         (path parameter will be replaced):  /blog/{blogId}/get/blogId
    #   - Substitute the Content-Type of the request
    #  findRequestTypeCustomPayload
    def find_request_type_custom_payload(self, endpoint, method, property_name_or_path, parameter_kind):
        request_type_payload_name = get_request_type_payload_name(endpoint, method, property_name_or_path)
        payload = find_payload_entry(self.restler_custom_payload, request_type_payload_name)

        if payload is not None:
            return request_type_payload_name, CustomPayloadType.String
        else:
            if parameter_kind == ParameterKind.Header:
                header_payload = find_payload_entry(self.restler_custom_payload_header, request_type_payload_name)
                if header_payload is not None:
                    return request_type_payload_name, CustomPayloadType.Header
            elif parameter_kind == ParameterKind.Query:
                query_payload = find_payload_entry(self.restler_custom_payload_query, request_type_payload_name)
                if query_payload is not None:
                    return request_type_payload_name, CustomPayloadType.Query
            else:
                raise ValueError("ParameterKind should be Query or Header in this context")

            return None, None

    # Note: per-endpoint dictionaries allow restricting a payload to a specific endpoint.
    def get_parameter_for_custom_payload(self, consumer_resource_name, access_path_parts, primitive_type,
                                         parameter_kind):
        # Check both custom payloads and unquoted custom payloads.
        payloads = [
            (self.restler_custom_payload_query if parameter_kind == ParameterKind.Query else {},
             CustomPayloadType.Query),
            (self.restler_custom_payload_header if parameter_kind == ParameterKind.Header else {},
             CustomPayloadType.Header),
            (self.restler_custom_payload, CustomPayloadType.String),
            (self.restler_custom_payload_unquoted, CustomPayloadType.String)
        ]

        results = []

        for custom_payload_entries, payload_type in payloads:
            # First, check for an exact access path, and if one is not found, check for the resource name.
            path_payload_entry = find_path_payload_entry(custom_payload_entries, access_path_parts)

            if path_payload_entry is not None:
                payload_entry = path_payload_entry
                payload_name = "/" + ("/".join(access_path_parts.path))
            else:
                payload_entry = find_payload_entry(custom_payload_entries, consumer_resource_name)
                payload_name = consumer_resource_name

            if payload_entry is not None and payload_type == CustomPayloadType.String:
                entry_value = next(iter(payload_entry), None).strip()
                is_object = entry_value.startswith("{") or entry_value.startswith("[")
                results.append(
                    DictionaryPayload(payload_type=payload_type, primitive_type=primitive_type, name=payload_name,
                                      is_object=is_object))
            elif payload_entry is not None:
                results.append(
                    DictionaryPayload(payload_type=payload_type, primitive_type=primitive_type, name=payload_name,
                                      is_object=False))

        return results

    def get_custom_payload_header_parameter_names(self):
        logger.write_to_main("get_custom_payload_header_parameter_names", ConfigSetting().LogConfig.dictionary)
        return get_keys([self.restler_custom_payload_header, self.restler_custom_payload_header_unquoted])

    def get_custom_payload_query_parameter_names(self):
        logger.write_to_main("get_custom_payload_query_parameter_names", ConfigSetting().LogConfig.dictionary)
        return get_keys([self.restler_custom_payload_query])

    def get_custom_payload_names(self):
        logger.write_to_main("get_custom_payload_names", ConfigSetting().LogConfig.dictionary)
        return get_keys([self.restler_custom_payload, self.restler_custom_payload_unquoted])

    def get_parameter_for_custom_payload_uuid_suffix(self, consumer_resource_name, access_path_parts, primitive_type):
        payload_type = CustomPayloadType.UuidSuffix

        # First, check for an exact access path, and if one is not found, check for the resource name.
        path_payload_entry = find_path_payload_entry(self.restler_custom_payload_uuid4_suffix, access_path_parts)

        if path_payload_entry:
            payload_name = "/" + ("/".join(access_path_parts.path))
            payload_entry = path_payload_entry
        else:
            payload_entry = find_payload_entry(self.restler_custom_payload_uuid4_suffix, consumer_resource_name)
            payload_name = consumer_resource_name

        if payload_entry and payload_type == CustomPayloadType.String:
            entry_value = next(iter(payload_entry.values()), None).strip()
            is_object = entry_value.startswith("{") or entry_value.startswith("[")
            return DictionaryPayload(payload_type=payload_type, primitive_type=primitive_type,
                                     name=payload_name, is_object=is_object)
        elif payload_entry:
            return DictionaryPayload(payload_type=payload_type, primitive_type=primitive_type,
                                     name=payload_name, is_object=False)
        else:
            return None

    # Combines the elements of the two dictionaries
    def combine_custom_payload_suffix(self, second_dict):
        logger.write_to_main(f"second={second_dict.__dict__()}", ConfigSetting().LogConfig.dictionary)
        if (self.restler_custom_payload_uuid4_suffix is None and
                second_dict.restler_custom_payload_uuid4_suffix is None):
            combined_suffix = {}
        elif (self.restler_custom_payload_uuid4_suffix is None or
              len(self.restler_custom_payload_uuid4_suffix) == 0):
            combined_suffix = second_dict.restler_custom_payload_uuid4_suffix
        elif second_dict.restler_custom_payload_uuid4_suffix is None:
            combined_suffix = self.restler_custom_payload_uuid4_suffix
        else:
            merged_dict = defaultdict(list)

            # 合并逻辑
            for d in (self.restler_custom_payload_uuid4_suffix, second_dict.restler_custom_payload_uuid4_suffix):
                for key, value in d.items():
                    if value not in merged_dict[key]:
                        merged_dict[key].append(value)

            combined_suffix = dict((k, v[0] if len(v) == 1 else v) for k, v in merged_dict.items())

        self.custom_payload_uuid4_suffix(combined_suffix)
        logger.write_to_main(f"dict={self.__dict__()}", ConfigSetting().LogConfig.dictionary)
        return self


# The default mutations dictionary generated when a user does not specify it
def init_user_dictionary():
    self = MutationsDictionary()
    self.restler_fuzzable_string.append(DefaultPrimitiveValues[PrimitiveType.String])
    self.restler_fuzzable_int.append(DefaultPrimitiveValues[PrimitiveType.Int])
    self.restler_fuzzable_number.append(DefaultPrimitiveValues[PrimitiveType.Number])
    self.restler_fuzzable_bool.append(DefaultPrimitiveValues[PrimitiveType.Bool])
    self.restler_fuzzable_datetime.append(DefaultPrimitiveValues[PrimitiveType.DateTime])
    self.restler_fuzzable_date.append(DefaultPrimitiveValues[PrimitiveType.Date])
    self.restler_fuzzable_object.append(DefaultPrimitiveValues[PrimitiveType.Object])
    self.restler_fuzzable_uuid4.append(DefaultPrimitiveValues[PrimitiveType.Uuid])
    return self


def get_dictionary(dictionary_file_path):
    if os.path.exists(dictionary_file_path):
        data = JsonSerialization.try_deeserialize_from_file(dictionary_file_path)
        if data is not None:
            return MutationsDictionary.init_from_json(data)
        else:
            raise Exception("ERROR: Cannot deserialize mutations dictionary. json.JSONDecodeError")
    else:
        raise Exception(f"ERROR: invalid path for dictionary: {dictionary_file_path}")


def get_dictionary_from_string(dictionary_string):
    try:
        data = json.loads(dictionary_string)
        return MutationsDictionary.init_from_json(data)
    except json.JSONDecodeError as e:
        return f"ERROR: Cannot deserialize mutations dictionary. {e}"
