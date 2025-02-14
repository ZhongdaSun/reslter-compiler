# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from rest.compiler.utilities import deterministic_short_stream_hash
from rest.compiler.swagger_spec_preprocess import (
    preprocess_api_spec,
    get_json_spec)
from rest.compiler.dependency_analysis_types import (
    get_path_from_string,
    PathPartType)
from rest.compiler.grammar import (
    OperationMethod,
    get_operation_method_from_string,
    RequestId)
from rest.swagger.parser import SwaggerContext
from rest.swagger.objects import (
    Response,
    PathItem)
from rest.compiler.config import ConfigSetting
from rest.restler.utils import restler_logger as logger


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
    logger.write_to_main(f"swagger_file_name={swagger_path}"
                         f"preprocessing_result={preprocessing_result}", ConfigSetting().LogConfig.swagger)
    return preprocessed_spec_path, preprocessing_result


class SwaggerDoc:
    path_info: [RequestInfo]
    path: ""
    host: str
    base_path: str
    consumes: []
    produces: []
    definitions: []
    parameters: []
    responses: []
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
            logger.write_to_main(f"spec_file={source_file_name}", ConfigSetting().LogConfig.swagger)
            self._specification = get_json_spec(self._swagger_file_name)
            # validate_spec(self._specification, '')
            tmp = {'t': {}}
            with SwaggerContext(tmp, 't') as ctx:
                ctx.parse(self._specification)
                self.ctx = ctx
            spec = tmp['t']
            logger.write_to_main(f"spec = {type(spec)} spec={tmp['t']} ", ConfigSetting().LogConfig.swagger)
            self.host = getattr(spec, "host")
            self.base_path = getattr(spec, "basePath")
            path = getattr(spec, "paths")
            self.inline_annotations = getattr(spec, "x-restler-global-annotations")
            if len(path) == 0:
                self.xMsPathsMapping = True
                path = getattr(spec, "x-ms-paths")
            self.switch(path, getattr(spec, "parameters"))
            self.definitions = getattr(spec, "definitions")
        except Exception as e:
            raise Exception(f"Exception: {e}")

    def switch(self, paths, spec_parameters):
        logger.write_to_main(f"type(paths)={type(paths)}", ConfigSetting().LogConfig.swagger)
        for endpoint, obj in paths.items():
            logger.write_to_main(f"endpoint={endpoint}, type(obj)={type(obj)}", ConfigSetting().LogConfig.swagger)
            if isinstance(obj, PathItem):
                endpoint_json = self.specification["paths"][endpoint]
                for operation_item in endpoint_json.keys():
                    http_method_item = operation_item.lower()
                    logger.write_to_main(f"http_method_item={http_method_item}",
                                         ConfigSetting().LogConfig.swagger)
                    if hasattr(obj, http_method_item):
                        opt = getattr(obj, http_method_item)
                        if opt is not None:
                            logger.write_to_main(f"opt={opt}, type(opt)={type(opt)}", ConfigSetting().LogConfig.swagger)
                            request_info = RequestInfo(endpoint=endpoint,
                                                       method=get_operation_method_from_string(http_method_item))
                            logger.write_to_main(f"endpoint={endpoint}", ConfigSetting().LogConfig.swagger)
                            request_info.ExtensionData = endpoint_json[http_method_item]
                            logger.write_to_main(f"request_info.ExtensionData={request_info.ExtensionData}",
                                                 ConfigSetting().LogConfig.swagger)

                            request_info.Responses = getattr(opt, "responses")
                            logger.write_to_main(f"responses={request_info.Responses}",
                                                 ConfigSetting().LogConfig.swagger)
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
                                logger.write_to_main(
                                    f"endpoint={endpoint}, method={http_method_item}, "
                                    f"p={p.name}, p.in={i}, p.type={p.type}, p.schema={p.schema}",
                                    ConfigSetting().LogConfig.swagger)
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
                            from rest.compiler.dependency_analysis_types import get_path_from_string, PathPartType, PathPart
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
                                            elif i == "query":
                                                if name not in query_param.keys():
                                                    query_param[name] = value
                                            elif i == 'body':
                                                if name not in body_param.keys():
                                                    value.update_field("required", True)
                                                    body_param[name] = value
                            self.path_info.append(request_info)

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
