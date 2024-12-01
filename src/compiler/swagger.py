# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from compiler.utilities import deterministic_short_stream_hash
from compiler.swagger_spec_preprocess import (
    preprocess_api_spec,
    get_json_spec)
from compiler.dependency_analysis_types import (
    get_path_from_string,
    PathPartType)
from compiler.grammar import (
    OperationMethod,
    RequestId)
from swagger.parser import SwaggerContext
from swagger.objects import (
    Response,
    PathItem)
from compiler.config import ConfigSetting
from restler.utils import restler_logger as logger


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
            if isinstance(obj, PathItem):
                logger.write_to_main(f"key={endpoint}, type(obj)={type(obj)}", ConfigSetting().LogConfig.swagger)
                for operation_item in OperationMethod:
                    http_method_item = operation_item.lower()
                    if hasattr(obj, http_method_item):
                        opt = getattr(obj, http_method_item)
                        if opt is not None:
                            logger.write_to_main(f"opt={opt}, type(opt)={type(opt)}", ConfigSetting().LogConfig.swagger)
                            request_info = RequestInfo(endpoint=endpoint, method=http_method_item)
                            logger.write_to_main(f"endpoint={endpoint}", ConfigSetting().LogConfig.swagger)

                            if endpoint in self.specification["paths"]:
                                logger.write_to_main(f"endpoint={endpoint}", ConfigSetting().LogConfig.swagger)
                                endpoint_json = self.specification["paths"][endpoint]
                                if http_method_item in endpoint_json:
                                    logger.write_to_main(f"http_method_item={http_method_item}",
                                                         ConfigSetting().LogConfig.swagger)
                                    request_info.ExtensionData = endpoint_json[http_method_item]
                                    logger.write_to_main(f"request_info.ExtensionData={request_info.ExtensionData}",
                                                         ConfigSetting().LogConfig.swagger)

                            request_info.Responses = getattr(opt, "responses")
                            logger.write_to_main(f"responses={request_info.Responses}",
                                                 ConfigSetting().LogConfig.swagger)
                            # opt.is_set("x-ms-examples") | opt.is_set("examples")
                            # remove x-ms-examples is just because x-ms-examples
                            # is automatically populated in the generated OpenAPI 2.0
                            request_info.request_id.has_example = opt.is_set("examples")
                            request_info.method = operation_item
                            request_info.local_annotation = getattr(opt, "x-restler-annotations")
                            request_info.long_running_operation = getattr(opt, 'x-ms-long-running-operation')
                            for p in opt.parameters:
                                if getattr(p, "$ref") is not None:
                                    local_definition = getattr(p, "$ref")
                                    local_key = local_definition.split("/")[-1]
                                    p = spec_parameters[local_key]
                                    if p is None:
                                        raise Exception(f"error in {local_definition}")
                                i = getattr(p, 'in')
                                logger.write_to_main(
                                    f"endpoint={endpoint}, method={http_method_item}, "
                                    f"p={p.name}, p.in={i}, p.type={p.type}, p.schema={p.schema}",
                                    ConfigSetting().LogConfig.swagger)
                                if i == 'path':
                                    request_info.path_param = p
                                elif i == "header":
                                    request_info.headerParameters.append(p)
                                elif i == "query":
                                    request_info.queryParameters.append(p)
                                elif i == 'body':
                                    p.update_field("required", True)
                                    request_info.bodyParameters.append(p)
                            if spec_parameters is not None:
                                for key, value in spec_parameters.items():
                                    i = getattr(value, 'in')
                                    param_name = getattr(value, 'name')
                                    if i == 'path':
                                        found = False
                                        for item in request_info.path:
                                            if param_name == getattr(item, 'name'):
                                                found = True
                                                break
                                        if not found:
                                            path_parts = get_path_from_string(endpoint, False)
                                            for part in path_parts.path:
                                                if part.part_type == PathPartType.Parameter and param_name == part.value:
                                                    request_info.path_param = value
                                                    logger.write_to_main(f"endpoint={endpoint}, "
                                                                         f"method={http_method_item}, "
                                                                         f"p={value.name}, "
                                                                         f"p.in={i}, "
                                                                         f"p.type={value.type}, "
                                                                         f"p.schema={value.schema}",
                                                                         ConfigSetting().LogConfig.swagger)
                                    elif i == "header":
                                        found = False
                                        for item in request_info.headerParameters:
                                            if param_name == getattr(item, 'name'):
                                                found = True
                                                break
                                        if not found:
                                            request_info.headerParameters.append(value)
                                    elif i == "query":
                                        found = False
                                        for item in request_info.queryParameters:
                                            if param_name == getattr(item, 'name'):
                                                found = True
                                                break
                                        if not found:
                                            request_info.queryParameters.append(value)
                                    elif i == 'body':
                                        found = False
                                        for item in request_info.queryParameters:
                                            if param_name == getattr(item, 'name'):
                                                found = True
                                                break
                                        if not found:
                                            request_info.bodyParameters.append(value)
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
