# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from typing import Union, Dict, List
import yaml
import json
import re
import enum

# todo no need to support x-ms-paths
from compiler.xms_paths import convert_xms_paths_to_paths
from compiler.config import ConfigSetting
from compiler.utilities import JsonSerialization

from restler.utils import restler_logger as logger


class RefResolution(enum.Enum):
    FileRef = 0
    LocalDefinitionRef = 1
    AllRef = 3


class SpecFormat(enum.Enum):
    Json = 1
    Yaml = 2


class Ref:
    ref_type: RefResolution
    file_name: str

    def __init__(self, ref_type: RefResolution, file_name: str):
        self.ref_type = ref_type
        self.file_name = file_name


# Contains a mapping of x-ms-path endpoints to transformed endpoints
# This mapping is only present if an x-ms-paths element is found in the specification
class SpecPreprocessingResult:
    def __init__(self, xMsPathsMapping: Union[Dict[str, str], None]):
        self.xMsPathsMapping = xMsPathsMapping


def normalize_file_path(x):
    return os.path.abspath(x)


def get_spec_format(spec_file_path):
    spec_extension = os.path.splitext(spec_file_path)[1]

    if spec_extension == ".json":
        return SpecFormat.Json
    elif spec_extension in [".yml", ".yaml"]:
        return SpecFormat.Yaml
    else:
        raise ValueError("This specification format extension is not supported")


def convert_yaml_to_json(yaml_file_path):
    with open(yaml_file_path, 'r') as spec_reader:
        yaml_data = yaml.safe_load(spec_reader)

    return json.dumps(yaml_data)


def get_json_spec(file_path):
    spec_format = get_spec_format(file_path)
    if spec_format == SpecFormat.Json:
        return JsonSerialization.try_deeserialize_from_file(file_path)
    elif spec_format == SpecFormat.Yaml:
        return convert_yaml_to_json(file_path)


class SpecCache:
    def __init__(self):
        self.json_specs = {}

    def find_spec(self, file_path):
        normalized_path = normalize_file_path(file_path)
        logger.write_to_main(f"normalized_path={normalized_path}", ConfigSetting().LogConfig.swagger_spec_preprocess)
        if normalized_path not in self.json_specs:
            self.json_specs[normalized_path] = get_json_spec(normalized_path)

        return self.json_specs[normalized_path]


class EscapeCharacters:

    @staticmethod
    def replace_swagger_escape_characters(path: str) -> str:
        """Replace Swagger escape characters '~1' and '~0'."""
        return path.replace("~1", "/").replace("~0", "~")

    @staticmethod
    def contains_swagger_escape_characters(path: str) -> bool:
        """Check if the path contains Swagger escape characters."""
        return "~1" in path or "~0" in path

    @staticmethod
    def get_ref_parts(ref_path: str) -> List[str]:
        """Get reference parts from the ref path."""
        # Split the path with the regex that avoids the leading '/'
        ref_regex = re.compile(r'(?<![/])/')
        parts = ref_regex.split(ref_path)[1:]
        # Skip the first element and replace escape characters
        return [EscapeCharacters.replace_swagger_escape_characters(part) for part in parts]


def get_definition_reference(ref_location, spec):
    if ref_location.find("definition"):
        ref_path = ref_location.split("/")[-1]
        return {ref_path: spec[ref_path]}


# Find the object at 'refPath' in the specified file.
# getObjInFile
def get_obj_in_file(file_path, ref_path: Ref):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Referenced file {file_path} does not exist")

    json_spec = SpecCache().find_spec(file_path)
    if ref_path.ref_type == RefResolution.FileRef:
        ref_path = ref_path.file_name.split("#")[0]
        if "[" in ref_path or EscapeCharacters.contains_swagger_escape_characters(ref_path):
            logger.write_to_main(f"json_spec={json_spec}", ConfigSetting().LogConfig.swagger_spec_preprocess)
            parts = EscapeCharacters.get_ref_parts(ref_path)
            selected_object_or_array = json_spec
            for part in parts:
                if isinstance(selected_object_or_array, dict):
                    selected_object_or_array = selected_object_or_array.get(part)
                elif isinstance(selected_object_or_array, list):
                    selected_object_or_array = selected_object_or_array[int(part)]
                else:
                    raise ValueError("Only an object or array is expected here")
            if selected_object_or_array is None:
                raise ValueError(f"Reference path {ref_path} not found")
            return selected_object_or_array
        else:
            ref_path_for_select_token = ref_path.replace("/", ".")
            logger.write_to_main(f"ref_path_for_select_token={ref_path_for_select_token}", True)
            ret_value = json_spec
            for item in ref_path_for_select_token:
                if item is not None and item != "":
                    ret_value = ret_value[item]
            logger.write_to_main(f"ret_value={ret_value}", ConfigSetting().LogConfig.swagger_spec_preprocess)
            return ret_value
    elif ref_path.ref_type == RefResolution.LocalDefinitionRef:

        return None


# Parses the value of a $ref property and returns the type of reference.
# getDefinitionRef
def get_definition_ref(ref_location):
    parts = ref_location.split("#")
    if len(parts) == 2:
        logger.write_to_main(f"parts={parts}", ConfigSetting().LogConfig.swagger_spec_preprocess)
        return Ref(ref_type=RefResolution.LocalDefinitionRef, file_name=ref_location)
    elif len(parts) == 1:
        logger.write_to_main(f"parts={parts}", ConfigSetting().LogConfig.swagger_spec_preprocess)
        return Ref(ref_type=RefResolution.FileRef, file_name=ref_location)
    else:
        raise ValueError(f"Invalid Ref found: {ref_location}")


# Returns a list of properties with all file $refs inlined.
# TODO: this doesn't catch recursion in local refs (within a file) yet.
# inlineFileRefs2
def inline_file_refs2(properties: dict,
                      normalized_document_file_path: str,
                      ref_resolution: RefResolution,
                      parent_property_path: str,
                      ref_stack: List[str]):
    def get_child_properties_for_object(obj: dict, property_name: str) -> List[dict]:
        # Special case: if the child properties are a ref and a description,
        # skip the description of the ref.
        ref = [x for x in obj["properties"] if x["name"] == "$ref"]

        if ref:
            return ref
        elif property_name:
            # TODO: Temporary workaround for issue #61 - NSWag failure to parse
            # required boolean in Headers.  Remove this when the NSWag bug is fixed.
            # The workaround is to remove the required property.
            # This is fine for now, since RESTler does not currently fuzz or
            # learn from header values
            header_in_path = f"headers.{property_name}"
            if obj["Path"].endswith(header_in_path):
                return [o for o in obj["Properties"] if o["Name"] != "required"]
            else:
                return obj["Properties"]
        else:
            return obj["properties"]

    def resolve_refs(normalized_full_ref_file_path: str,
                     definition_path: Ref,
                     ref_resolution: RefResolution,
                     ref_stack: List[str],
                     property_name: str) -> List[dict]:
        logger.write_to_main(f"normalized_full_ref_file_path={normalized_full_ref_file_path}, "
                             f"definition_path.file_name={definition_path.file_name}",
                             ConfigSetting().LogConfig.swagger_spec_preprocess)
        # Get the referenced object from the file

        found_obj = get_obj_in_file(normalized_full_ref_file_path, definition_path)
        # We are replacing the single "$ref": "Path" with a potential
        # list of properties in that type definition.

        if found_obj:
            # return [p for p in found_obj["properties"]]
            return found_obj
        else:
            full_token_path = (normalized_full_ref_file_path, found_obj["Path"])
            recursion_found = full_token_path in ref_stack
            if recursion_found:
                return [
                    {"type": "object"},
                    {"description": "Restler: recursion limit reached"}
                ]

            else:
                return inline_file_refs2(found_obj["properties"],
                                         normalized_full_ref_file_path,
                                         ref_resolution,
                                         f"{parent_property_path}/{property_name}",
                                         [full_token_path] + ref_stack)

    new_properties = []
    for key, value in properties.items():
        if key == "$ref":
            definition_ref = get_definition_ref(value)
            if definition_ref.ref_type == RefResolution.FileRef:
                logger.write_to_main(f"file_name={definition_ref.file_name}",
                                     ConfigSetting().LogConfig.swagger_spec_preprocess)
                if ref_resolution == RefResolution.FileRef or ref_resolution == RefResolution.AllRef:
                    if EscapeCharacters.contains_swagger_escape_characters(value):
                        logger.write_to_main(f"file_name={definition_ref.file_name}",
                                             ConfigSetting().LogConfig.swagger_spec_preprocess)
                        resolved_ref = resolve_refs(normalized_document_file_path,
                                                    definition_ref,
                                                    ref_resolution,
                                                    ref_stack, value)
                        new_properties.append({"name": f"{definition_ref.file_name}", "value": resolved_ref})
                    else:
                        full_ref_file_path = normalize_file_path(
                            os.path.dirname(normalized_document_file_path) + definition_ref.file_name)
                        new_properties.append({"name": f"{definition_ref.file_name}", "value": full_ref_file_path})
                        logger.write_to_main(f"new_properties={new_properties}",
                                             ConfigSetting().LogConfig.swagger_spec_preprocess)
                elif ref_resolution == RefResolution.LocalDefinitionRef or RefResolution.AllRef:
                    logger.write_to_main(f"file_name={definition_ref.file_name}",
                                         ConfigSetting().LogConfig.swagger_spec_preprocess)
                    resolved_ref = resolve_refs(normalized_document_file_path,
                                                definition_ref,
                                                ref_resolution,
                                                ref_stack,
                                                value)
                    new_properties.append({"name": f"{definition_ref.file_name}", "value": resolved_ref})
            elif definition_ref.ref_type == RefResolution.LocalDefinitionRef:
                if ref_resolution == RefResolution.LocalDefinitionRef or ref_resolution == RefResolution.AllRef:
                    resolved_ref = resolve_refs(normalized_document_file_path, definition_ref, ref_resolution,
                                                ref_stack, value)
                    new_properties.append({"name": f"{definition_ref.file_name}", "value": resolved_ref})
                    logger.write_to_main(f"new_properties={new_properties}",
                                         ConfigSetting().LogConfig.swagger_spec_preprocess)
        else:
            if isinstance(value, dict):
                new_properties.extend(inline_file_refs2(properties=value,
                                                        normalized_document_file_path=normalized_document_file_path,
                                                        ref_resolution=ref_resolution,
                                                        parent_property_path=f"{parent_property_path}@{key}",
                                                        ref_stack=ref_stack))

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        continue
                    elif isinstance(item, dict):
                        new_properties.extend(
                            inline_file_refs2(properties=item,
                                              normalized_document_file_path=normalized_document_file_path,
                                              ref_resolution=ref_resolution,
                                              parent_property_path=f"{parent_property_path}@{key}",
                                              ref_stack=ref_stack))

    return new_properties


def inline_file_refs(json_obj: dict, document_file_path: str) -> dict:
    json_specs = inline_file_refs2(
        json_obj,
        normalize_file_path(document_file_path),
        RefResolution.FileRef,
        "",
        [])
    logger.write_to_main(f"json_specs={json_specs}", ConfigSetting().LogConfig.swagger_spec_preprocess)
    spec_str = json.dumps(json_obj, ensure_ascii=False)
    for item in json_specs:
        key = item["name"].split("#")
        if len(key) == 2:
            if isinstance(item["value"], str):
                spec_str = spec_str.replace(item["name"], item["value"])
            elif isinstance(item["value"], dict):
                str_key = "\"".join(item["name"]).join("\"")
                str_value = json.dumps(item["value"])
                spec_str = spec_str.replace(str_key, str_value)
        elif len(key) == 1:
            value = "\\\\".join(item["value"].split("\\"))
            str_key = key[0]
            index = spec_str.find(str_key)
            spec_str = spec_str.replace(str_key, value)
            logger.write_to_main(f"key={str_key}, value={value}, index={index}",
                                 ConfigSetting().LogConfig.swagger_spec_preprocess)

    logger.write_to_main(f"spec_str={spec_str}", ConfigSetting().LogConfig.swagger_spec_preprocess)
    return json.loads(spec_str)


# No need to support x-ms-paths.
def transform_x_ms_paths(json_spec):
    if "x-ms-paths" in json_spec.keys():
        x_ms_paths = json_spec["x-ms-paths"]

        if not x_ms_paths:
            return json_spec, None

        new_paths = dict()
        if "paths" in json_spec.keys():
            paths = json_spec["paths"]
            for path_name, path_value in paths.items():
                new_paths[path_name] = path_value

        x_ms_paths_items = x_ms_paths.items()
        # Re-write the spec by transforming the x-ms-path keys into valid paths and inserting them into the
        # path's property.
        for path_name, path_value in x_ms_paths_items:
            new_paths[convert_xms_paths_to_paths(path_name)] = path_value

        json_spec.pop("paths", None)
        json_spec.pop("x-ms-paths", None)
        json_spec["paths"] = new_paths

        # Mapping back the transformed paths
        # mapping = {k: v for k, v in mapping.items() if k != v}
        # mapping = mapping if mapping else None

    return json_spec  # , mapping


# preprocessApiSpec
# Preprocesses the document to inline all file references in type definitions (excluding examples).
def preprocess_api_spec(spec_path, output_spec_path):
    json_spec_obj = SpecCache().find_spec(spec_path)

    # Check whether x-ms-paths is present.  If yes, transform it to 'paths' and keep track of the paths.
    # todo no need to support x-ms-path
    # json_spec_obj, path_mapping = transform_x_ms_paths(json_spec_obj)

    new_object = inline_file_refs(json_spec_obj, spec_path)
    logger.write_to_main(f"new_object={new_object}", ConfigSetting().LogConfig.swagger_spec_preprocess)

    JsonSerialization.serialize_to_file(output_spec_path, new_object)
    """

    spec_preprocessing_result = {}
    if path_mapping:
        spec_preprocessing_result['xMsPathsMapping'] = {v: k for k, v in path_mapping.items()}
    """

    return True
