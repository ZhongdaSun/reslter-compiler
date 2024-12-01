# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import json
from typing import List, Dict, Any
from compiler.utilities import JsonSerialization
from compiler.config import ConfigSetting
from restler.utils import restler_logger as logger

# Types describing the format of the user-specified example config file
# The format is the same as the paths section in OpenAPI specification to
# increase readability for the user.

class ExamplePayload:
    name: str

    def __init__(self, name):
        self.name = name


class FileExamplePayload(ExamplePayload):
    file_path: str

    def __init__(self, name, file_path):
        super().__init__(name)
        self.file_path = file_path


class InlineExamplePayload(ExamplePayload):
    inlined_payload: dict

    def __init__(self, name, inlined_payload):
        super().__init__(name)
        self.inlined_payload = inlined_payload


class ExampleMethod:
    # (exampleName, example)
    name: str
    example_payloads: list[ExamplePayload]

    def __init__(self, name, example_payloads):
        self.name = name
        self.example_payloads = example_payloads

    def __dict__(self):
        return {"name": self.name,
                "example_payloads": self.example_payloads}


class ExamplePath:
    path: str
    methods: list[ExampleMethod]

    def __init__(self, path, methods):
        self.path = path
        self.methods = methods


class ExampleConfigFile:
    paths: list[ExamplePath]
    exact_copy: bool

    def __init__(self, paths, exact_copy):
        self.paths = paths
        self.exact_copy = exact_copy


class ExamplePayloadInfo:
    payload: dict
    payload_info: ExamplePayload
    exact_copy: bool

    def __init__(self, example_payload, payload_info, exact_copy):
        self.exact_copy = exact_copy
        self.payload_info = payload_info
        self.payload = example_payload


# Deserialize the example config file
"""
(*
 "paths": {
     "/.../": {
         "get": {
         "one": "/path/to/1",
         "two": "/path/to/2"
         },
         "put": {},
         ...
         }
 *)
 """


def get_example_config_file(file_path, exact_copy) -> ExampleConfigFile:
    if os.path.exists(file_path):
        try:
            return try_deserialize_example_config_file(file_path, exact_copy)
        except Exception as e:
            print(f"ERROR: example file could not be deserialized:  {e}")
            raise ValueError("invalid example config file path")
    else:
        print(f"ERROR: invalid file path for the example config file given: {file_path}")
        raise ValueError("invalid example config file path")


"""
def serialize_example_config_file(file_path, example_paths):
    paths = []
    for p in example_paths:
        methods = []
        for m in p["methods"]:
            example_payloads = []
            for e in m["examplePayloads"]:
                ex_value = e["filePathOrInlinedPayload"]
                if e["filePathOrInlinedPayload"]["type"] == "FilePath":
                    ex_value = e["filePathOrInlinedPayload"]["file"]
                example_payloads.append({e["name"]: ex_value})

            methods.append({m["name"]: dict(example_payloads)})

        paths.append({p["path"]: dict(methods)})

    root_object = {"paths": dict(paths)}

    with open(file_path, 'w') as file:
        json.dump(root_object, file)
"""


def try_deserialize_example_config_file(example_config_file_path: str,
                                        exact_copy: bool):
    try:
        if not os.path.exists(example_config_file_path):
            raise Exception(f"{example_config_file_path} not exists.")
        j_object = JsonSerialization.try_deeserialize_from_file(example_config_file_path)
        paths_obj = j_object["paths"]
        paths = []
        for path_property in paths_obj.keys():  # paths
            methods = []
            for method_property, method_value in paths_obj[path_property].items():  # post: {}
                method_name = method_property.lower()
                method_examples = []
                for example_property, example_value in method_value.items():  # "1": {}
                    if isinstance(example_value, str):
                        file_path = os.path.join(os.path.dirname(example_config_file_path), example_value)
                        if os.path.exists(file_path):
                            example_payload = FileExamplePayload(name=example_property, file_path=file_path)
                        else:
                            example_payload = InlineExamplePayload(name=example_property, inlined_payload=example_value)
                    else:
                        example_payload = InlineExamplePayload(name=example_property, inlined_payload=example_value)

                    method_examples.append(example_payload)

                methods.append(ExampleMethod(name=method_name, example_payloads=method_examples))

            paths.append(ExamplePath(path=path_property, methods=methods))

        return ExampleConfigFile(paths=paths, exact_copy=exact_copy)

    except Exception as e:
        print(f"ERROR: example file could not be deserialized: {example_config_file_path}: {e}")
        raise ValueError("invalid example config file")


# The format of an example payload.
# Currently, all examples are valid JSON and are represented as
# a JToken for convenience
# Define PayloadFormat type
class PayloadFormat:
    def __init__(self, j_token):
        self.payload = j_token


# Parameter payload from an example
# Define ExampleParameterPayload type
class ExampleParameterPayload:
    def __init__(self, parameter_name, payload):
        # The name of the parameter
        self.parameter_name = parameter_name
        # The content of the payload
        self.payload = payload


# Define ExampleRequestPayload type
# Request payload contents obtained from an example payload
class ExampleRequestPayload:
    def __init__(self, example_file_path: str, parameter_examples: List[ExampleParameterPayload], exact_copy: bool):
        # Path of the file containing this payload
        self.example_file_path = example_file_path
        # The payloads for each parameter
        self.parameter_examples = parameter_examples
        # Make an exact copy of this example payload, without matching with the schema
        self.exact_copy = exact_copy


# Define a function to get example payloads from config files
# Merges the example payloads from all the specified config files
def get_user_specified_payload_examples(endpoint: str,
                                        method: str,
                                        config: list[ExampleConfigFile],
                                        discover_examples: bool):
    logger.write_to_main(f"endpoint={endpoint}, method={method}, "
                         f"config={config}, discover_examples={discover_examples}", ConfigSetting().LogConfig.example)
    examples = []
    for payload_examples in config:
        if discover_examples:
            raise ValueError("Only one of 'discoverExamples' or an example config file can be specified.")

        example_file_paths_or_inlined_payloads = []
        for ep_payload in payload_examples.paths:
            if ep_payload.path == endpoint:
                for method_payload in ep_payload.methods:
                    if method_payload.name.lower() == method.lower():
                        example_file_paths_or_inlined_payloads.extend(
                            [ep for ep in method_payload.example_payloads])

        example_objects = []
        for ep in example_file_paths_or_inlined_payloads:
            if isinstance(ep, FileExamplePayload):
                example_json = JsonSerialization.try_deeserialize_from_file(ep.file_path)
                example_objects.append(ExamplePayloadInfo(example_payload=example_json,
                                                          payload_info=ep,
                                                          exact_copy=payload_examples.exact_copy))
            elif isinstance(ep, InlineExamplePayload):
                example_objects.append(ExamplePayloadInfo(example_payload=ep.inlined_payload,
                                                          payload_info=ep,
                                                          exact_copy=payload_examples.exact_copy))

        examples.extend(example_objects)

    return examples


# Gets the example payloads that were specified inline in the specification
# These are the examples specified as full payloads -
# individual property examples are extracted in a different place, while
# traversing the schema.
# getSpecPayloadExamples
def get_spec_payload_examples(swagger_method_definition, endpoint, method):
    path_info = None
    if endpoint in swagger_method_definition["paths"]:
        path_info = swagger_method_definition["paths"]
    elif endpoint in swagger_method_definition["x-ms-paths"]:
        path_info = swagger_method_definition["x-ms-paths"]
    else:
        raise Exception("please check the endpoint in spec")

    if method not in path_info[endpoint]:
        raise Exception(f"please check {endpoint} and {method}.")

    extension_data = path_info[endpoint][method]

    if len(extension_data) == 0:
        return []

    # // Get example if it exists.  If not, fall back on the parameter list.
    # remove x-ms-example just because it is not in Swagger2.0
    # example = next((v for k, v in extension_data.items() if k == "x-ms-examples" or k.lower() == "examples"), None)
    example = next((v for k, v in extension_data.items() if k.lower() == "examples"), None)

    if not example:
        return []

    dict_data = example if isinstance(example, dict) else {}
    spec_example_values = []

    for i in dict_data.values():
        example_values = i if isinstance(i, dict) else {}

        if len(example_values) < 1:
            print(f"Invalid example specification found: {example_values}")
        else:
            files_or_raw_examples = []
            if "$ref" in example_values:
                files_or_raw_examples.append(example_values["$ref"])
            if "parameters" in example_values:
                files_or_raw_examples.append(example_values)

            for relative_example_file_path_or_raw in files_or_raw_examples:
                if isinstance(relative_example_file_path_or_raw, str):
                    example_json = JsonSerialization.try_deeserialize_from_file(relative_example_file_path_or_raw)
                    example_payload = FileExamplePayload(name="", file_path=relative_example_file_path_or_raw)
                    spec_example_values.append(ExamplePayloadInfo(example_payload=example_json,
                                                                  payload_info=example_payload,
                                                                  exact_copy=False))
                else:
                    try:
                        raw_example_json = json.loads(json.dumps(relative_example_file_path_or_raw))
                        example_payload = InlineExamplePayload(name="", inlined_payload=raw_example_json)
                        spec_example_values.append(ExamplePayloadInfo(example_payload=raw_example_json,
                                                                      payload_info=example_payload,
                                                                      exact_copy=False))
                    except Exception as e:
                        print(f"example {relative_example_file_path_or_raw} is invalid. {e}")

    return spec_example_values


# getExampleConfig
def get_example_config(endpoint: str,
                       method: str,
                       swagger_method_definition: Dict[str, Any],
                       discover_examples: bool,
                       user_specified_payloads: List[ExampleConfigFile],
                       use_all_examples: bool):
    # TODO: only do user specified if discoverExamples is false.

    # The example payloads specified in the example config file take precedence over the
    # examples in the specification.
    user_specified_payloads_example_values = get_user_specified_payload_examples(endpoint,
                                                                                 method,
                                                                                 user_specified_payloads,
                                                                                 discover_examples)

    if use_all_examples or len(user_specified_payloads_example_values) == 0:
        spec_payload_examples = get_spec_payload_examples(swagger_method_definition,
                                                          endpoint,
                                                          method)
    else:
        spec_payload_examples = []

    example_payloads = user_specified_payloads_example_values + spec_payload_examples

    example_payload_objects = []
    for example_payload in example_payloads:
        if isinstance(example_payload.payload, dict):
            if "parameters" in example_payload.payload.keys():
                example_parameter_values = example_payload.payload["parameters"]
                parameter_examples = [ExampleParameterPayload(parameter_name, payload=param_value) for
                                      parameter_name, param_value in example_parameter_values.items()]
                example_payload_obj = None
                if isinstance(example_payload.payload_info, FileExamplePayload):
                    example_payload_obj = ExampleRequestPayload(
                        example_file_path=example_payload.payload_info.file_path,
                        parameter_examples=parameter_examples,
                        exact_copy=example_payload.exact_copy)
                elif isinstance(example_payload.payload_info, InlineExamplePayload):
                    example_payload_obj = ExampleRequestPayload(
                        example_file_path="",
                        parameter_examples=parameter_examples,
                        exact_copy=example_payload.exact_copy)

                example_payload_objects.append(example_payload_obj)

    return example_payload_objects
