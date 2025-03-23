# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from compiler.utilities import deterministic_short_stream_hash
from compiler.swagger_spec_preprocess import (
    preprocess_api_spec,
    get_json_spec)
from compiler.grammar import (
    OperationMethod,
    get_operation_method_from_string,
    RequestId)
from swagger.parser import SwaggerContext
from swagger.objects import (
    Response,
    PathItem)
from compiler.config import ConfigSetting


class UnexpectedSwaggerParameter(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class UnsupportedParameterSchema(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ParameterTypeNotFound(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RequestInfo:
    request_id: RequestId
    method: OperationMethod
    path = []
    queryParameters = []
    bodyParameters = []
    headerParameters = []
    formDataParameters = []
    Responses: [Response]
    local_annotation = []
    long_running_operation = None

    ExtensionData: dict

    def __init__(self, endpoint, method):
        self.request_id = RequestId(endpoint=endpoint, method=method, xms_path=None, has_example=False)
        self.path = []
        self.queryParameters = []
        self.bodyParameters = []
        self.headerParameters = []
        self.formDataParameters = []
        self.ExtensionData = {}
        self.local_annotation = []
        self.long_running_operation = None

    @property
    def path_param(self):
        return self.path

    @path_param.setter
    def path_param(self, path_param):
        self.path.append(path_param)

    @path_param.deleter
    def path_param(self):
        self.path.clear()
        self.path = []

    def __dict__(self):
        return_value = dict()
        return_value["endpoint"] = self.request_id.endpoint

        return return_value


def preprocess_swagger_document(swagger_path, working_directory):
    # When a spec is preprocessed, it is converted to json
    spec_extension = ".json"
    preprocessed_specs_dir_path = os.path.join(working_directory, "preprocessed")
    spec_name = f"{os.path.splitext(os.path.basename(swagger_path))[0]}_preprocessed{spec_extension}"
    os.makedirs(preprocessed_specs_dir_path, exist_ok=True)
    preprocessed_spec_path = os.path.join(preprocessed_specs_dir_path, spec_name)

    preprocessing_result = preprocess_api_spec(swagger_path, preprocessed_spec_path)
    return preprocessed_spec_path, preprocessing_result


class SwaggerDoc:
    path_info: [RequestInfo]
    path: ""
    host: str
    base_path: str
    definitions: []
    _specification: dict
    _swagger_file_name: str
    xMsPathsMapping: {}
    global_annotations: []
    inline_annotations: []
    dictionary: []
    externalDocs: str
    ctx: SwaggerContext
    user_specified_examples: []

    def __int__(self):
        self._swagger_file_name = ""
        self.path_info = []
        self.inline_annotations = []
        self.global_annotations = []
        self.dictionary = []
        self.xMsPathsMapping = {}
        self._specification = {}
        self.definitions = []
        self.user_specified_examples = None

    @property
    def swagger_file_name(self):
        return self._swagger_file_name

    @property
    def specification(self):
        return self._specification

    @swagger_file_name.setter
    def swagger_file_name(self, source_file_name):
        self._swagger_file_name = source_file_name
        self.path_info = []
        self.dictionary = []
        self.xMsPathsMapping = False
        self.inline_annotations = []
        self.global_annotations = []
        try:
            self._specification = get_json_spec(self._swagger_file_name)
            # validate_spec(self._specification, '')
            tmp = {'t': {}}
            with SwaggerContext(tmp, 't') as ctx:
                ctx.parse(self._specification)
                self.ctx = ctx
            spec = tmp['t']
            self.host = getattr(spec, "host")
            self.base_path = getattr(spec, "basePath")
            path = getattr(spec, "paths")
            self.inline_annotations = getattr(spec, "x-restler-global-annotations")
            if len(path) == 0:
                self.xMsPathsMapping = True
                path = getattr(spec, "x-ms-paths")
            self.switch(path, getattr(spec, "parameters"))
            self.definitions = getattr(spec, "definitions")
            # self.get_no_parameters_endpoint()
            self.validate_spec()
        except Exception as e:
            raise Exception(f"Exception: {e}")

    def get_no_parameters_endpoint(self):
        consumer_parameter_txt_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                        "no_parameters_endpoint.txt")
        content = ""
        for item in self.path_info:
            if (len(item.path) == 0 and len(item.queryParameters) == 0 and
                    len(item.bodyParameters) == 0 and len(item.formDataParameters) == 0):
                content = (content + item.request_id.endpoint + "\t" + item.request_id.method.name + '\t\t\t\t\t' + "0"
                           + "\n")
            else:
                for form_param in item.formDataParameters:
                    name_param = getattr(form_param, 'name')
                    type_param = getattr(form_param, 'type')
                    in_param = getattr(form_param, 'in')
                    if name_param is None:
                        name_param = "error"
                    if type_param is None:
                        type_param = "error"
                    if in_param is None:
                        in_param = "error"
                    str_value = (item.request_id.endpoint + "\t" + item.request_id.method.name + "\t" +
                                 name_param + '\t' + '' + name_param + '\t' + type_param + '\t\t' +
                                 in_param + '\n')
                    content = content + str_value

        with open(consumer_parameter_txt_file_path, "w") as file:
            file.write(content)
            file.close()

    def create_path_parameter(self):
        consumer_parameter_txt_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                        "path_parameter_file.py")
        content = ""
        for item in self.path_info:
            str_value = "(\"" + item.request_id.endpoint + "\", "
            for parameter in item.path:
                content = content + str_value + "\"" + getattr(parameter, 'name') + "\"),\n"
            for parameter in item.queryParameters:
                content = content + str_value + "\"" + getattr(parameter, 'name') + "\"),\n"
            for parameter in item.bodyParameters:
                content = content + str_value + "\"" + getattr(parameter, 'name') + "\"),\n"
            """
            for parameter in item.headerParameters:
                content = content + str_value + "\"" + getattr(parameter, 'name') + "\"),\n"
            """
        code = f"""
import networkx as nx
import matplotlib.pyplot as plt

edges = [
{content}
]

graph = nx.DiGraph()
graph.add_edges_from(edges)

nx.draw(graph, with_labels=True, node_color="lightblue", node_size=2000)
plt.show()
"""
        with open(consumer_parameter_txt_file_path, "w") as file:
            file.write(code)

    def switch(self, paths, spec_parameters):
        for endpoint, obj in paths.items():
            if isinstance(obj, PathItem):
                endpoint_json = self.specification["paths"][endpoint]
                for operation_item in endpoint_json.keys():
                    http_method_item = operation_item.lower()
                    if hasattr(obj, http_method_item):
                        opt = getattr(obj, http_method_item)
                        if opt is not None:
                            request_info = RequestInfo(endpoint=endpoint,
                                                       method=get_operation_method_from_string(http_method_item))
                            request_info.ExtensionData = endpoint_json[http_method_item]
                            request_info.Responses = getattr(opt, "responses")
                            # opt.is_set("x-ms-examples") | opt.is_set("examples")
                            # remove x-ms-examples is just because x-ms-examples
                            # is automatically populated in the generated OpenAPI 2.0
                            request_info.method = get_operation_method_from_string(operation_item)
                            request_info.local_annotation = getattr(opt, "x-restler-annotations")
                            request_info.long_running_operation = getattr(opt, 'x-ms-long-running-operation')
                            path_param = {}
                            query_param = {}
                            header_param = {}
                            body_param = {}
                            formData_param = {}
                            # issue fix for atest/swagger_only/simple_swagger_all_param_data_types.json
                            for p in opt.parameters:
                                if getattr(p, "$ref") is not None:
                                    local_definition = getattr(p, "$ref")
                                    local_key = local_definition.split("/")[-1]
                                    p = spec_parameters[local_key]
                                    if p is None:
                                        raise Exception(f"error in {local_definition}")
                                i = getattr(p, 'in')
                                name = getattr(p, 'name')
                                if i == 'path':
                                    if name not in path_param.keys():
                                        request_info.path_param = p
                                        path_param[name] = p
                                elif i == "header":
                                    if name not in header_param.keys():
                                        request_info.headerParameters.append(p)
                                        header_param[name] = p
                                elif i == "query":
                                    if name not in query_param.keys():
                                        request_info.queryParameters.append(p)
                                        query_param[name] = p
                                elif i == 'body':
                                    if name not in body_param.keys():
                                        p.update_field("required", True)
                                        request_info.bodyParameters.append(p)
                                        body_param[name] = p
                                elif i == 'formData':
                                    if name not in formData_param.keys():
                                        request_info.formDataParameters.append(p)
                                        formData_param[name] = p
                                else:
                                    raise Exception(f"Not support in type: {endpoint} {i}")
                            from compiler.dependency_analysis_types import get_path_from_string, PathPartType
                            path_words = get_path_from_string(endpoint, False)
                            for item in path_words.path:
                                if item.part_type == PathPartType.Parameter and item.value not in path_param.keys():
                                    if spec_parameters is not None:
                                        for key, value in spec_parameters.items():
                                            i = getattr(value, 'in')
                                            name = getattr(value, 'name')
                                            if i == 'path' and name == item.value:
                                                path_param[name] = value
                                                request_info.path_param = value
                                            elif i == "header":
                                                if name not in header_param.keys():
                                                    header_param[name] = value
                                                    request_info.headerParameters.append(value)
                                            elif i == "query":
                                                if name not in query_param.keys():
                                                    query_param[name] = value
                                                    request_info.queryParameters.append(value)
                                            elif i == 'body':
                                                if name not in body_param.keys():
                                                    value.update_field("required", True)
                                                    body_param[name] = value
                                                    request_info.bodyParameters.append(value)
                                            elif i == 'formData':
                                                if name not in formData_param.keys():
                                                    request_info.formDataParameters.append(value)
                                                    formData_param[name] = value
                                            else:
                                                raise Exception(f"Not support in type: {endpoint} {i}")
                            self.path_info.append(request_info)

    def validate_spec(self):
        content = ""
        for item in self.path_info:
            str_value = ""
            path_params = []
            for path_param in item.path:
                name_param = getattr(path_param, 'name')
                type_param = getattr(path_param, 'type') or getattr(path_param, 'schema')
                in_param = getattr(path_param, 'in')
                if name_param:
                    path_params.append(name_param)
                if name_param is None:
                    str_value = str_value + "error: without parameter name in path parameter.\n"
                if type_param is None:
                    str_value = str_value + f"error: without parameter type of {name_param} in path parameters\n" \
                        if name_param else "error: without parameter type in path parameter\n"
                if in_param is None:
                    str_value = str_value + f"error: without parameter in of {name_param} in path parameters\n" \
                        if name_param else "error: without parameter in in path parameter\n"

            from compiler.dependency_analysis_types import get_path_from_string, PathPartType
            path_words = get_path_from_string(item.request_id.endpoint, False)
            endpoint_params = []
            missing_declare = []
            for endpoint_param in path_words.path:
                if endpoint_param.part_type == PathPartType.Parameter:
                    endpoint_params.append(endpoint_param.value)
                    if endpoint_param.value not in path_params:
                        missing_declare.append(endpoint_param.value)
            if len(missing_declare) == 1:
                str_value = str_value + f"Path Parameter {missing_declare} is not definition!\n"
            elif len(missing_declare) > 1:
                str_value = str_value + f"Path Parameters {missing_declare} are not definition!\n"

            missing_in_endpoint = []
            for path_param in path_params:
                if path_param not in endpoint_params:
                    missing_in_endpoint.append(path_param)

            if len(missing_in_endpoint) == 1:
                str_value = str_value + f"Path Parameter {missing_in_endpoint} is not in the endpoint!\n"
            elif len(missing_in_endpoint) > 1:
                str_value = str_value + f"Path Parameters {missing_in_endpoint} are not in the endpoint!\n"

            for query_param in item.queryParameters:
                name_param = getattr(query_param, 'name')
                type_param = getattr(query_param, 'type') or getattr(query_param, 'schema')
                in_param = getattr(query_param, 'in')
                if name_param is None:
                    str_value = str_value + "error: without parameter name in query parameter.\n"
                if type_param is None:
                    str_value = str_value + f"error: without parameter type of {name_param} in query parameter.\n" \
                        if name_param else "error: without parameter type in query parameter.\n"
                if in_param is None:
                    str_value = str_value + f"error: without parameter in of {name_param} in query parameter.\n" \
                        if name_param else "error: without parameter in in query parameter.\n"

            for body_param in item.bodyParameters:
                name_param = getattr(body_param, 'name')
                type_param = getattr(body_param, 'type') or getattr(body_param, 'schema')
                in_param = getattr(body_param, 'in')
                if name_param is None:
                    str_value = str_value + "error: without parameter name in body parameters.\n"
                if type_param is None:
                    str_value = str_value + f"error: without parameter type of {name_param} in body parameters.\n" \
                        if name_param else "error: without parameter type in body parameters.\n"
                if in_param is None:
                    str_value = str_value + f"error: without parameter in of {name_param} in body parameters.\n" \
                        if name_param else "error: without parameter in in body parameters.\n"

            if len(item.bodyParameters) > 1:
                str_value = str_value + f"It has {len(item.bodyParameters)} body parameters. It should be only one.\n"

            for form_param in item.formDataParameters:
                name_param = getattr(form_param, 'name')
                type_param = getattr(form_param, 'type') or getattr(form_param, 'schema')
                in_param = getattr(form_param, 'in')
                if name_param is None:
                    str_value = str_value + "error: without parameter name in form data\n"
                if type_param is None:
                    str_value = str_value + f"error: without parameter type of {name_param} in form data\n" \
                        if name_param else "error: without parameter type in form data\n"
                if in_param is None:
                    str_value = str_value + f"error: without parameter in of {name_param} in form data\n" \
                        if name_param else "error: without parameter in in form data\n"
            if str_value != '':
                content = content + item.request_id.endpoint + "\t" + item.request_id.method.name + ":\n" + str_value

        if content != '':
            consumer_parameter_txt_file_path = os.path.join(ConfigSetting().GrammarOutputDirectoryPath,
                                                            "error_parameters_info.txt")
            with open(consumer_parameter_txt_file_path, "w", encoding='utf-8') as file:
                file.write(content)
                file.close()
            raise Exception(f"please check the file {consumer_parameter_txt_file_path} to fix issues!")

    @property
    def paths(self):
        return self.path_info

    def get_swagger_document(self, swagger_path, working_directory):
        preprocessed_spec_path, preprocessing_result = preprocess_swagger_document(swagger_path, working_directory)
        if preprocessing_result:
            self.swagger_file_name = preprocessed_spec_path
            return preprocessing_result
        else:
            print(
                f"API spec preprocessing failed ({preprocessing_result}). "
                f"Please check that your specification is valid. "
                f"Attempting to compile Swagger document without preprocessing.")
            self.swagger_file_name = swagger_path
            return False

    # preprocessSwaggerDocument
    def get_swagger_document_stats(self, swagger_path):
        self.path = swagger_path
        with open(swagger_path, "rb") as file:
            swagger_hash = deterministic_short_stream_hash(file)
            swagger_size = os.path.getsize(swagger_path)
        return [("size", str(swagger_size)), ("content_hash", swagger_hash)]
