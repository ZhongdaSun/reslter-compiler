# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, List
import os
import enum

# Define the NamingConvention enum
#  The 'type' of the resource is inferred based on the naming of its name and container as
#  well as conventions for the API method (e.g. PUT vs. POST).
#  A naming convention may be specified by the user, or it is inferred automatically
class NamingConvention(enum.StrEnum):
    CamelCase = "CamelCase"  # accountId
    PascalCase = "PascalCase"  # AccountId
    HyphenSeparator = "HyphenSeparator"  # account-id
    UnderscoreSeparator = "UnderscoreSeparator"  #


# A configuration associated with a single API specification file (e.g. a Swagger .json spec)
# Define the SwaggerSpecConfig class
class SwaggerSpecConfigClass:
    def __init__(self,
                 spec_file_path: str,
                 dictionary_file_path: Optional[str],
                 dictionary: Optional[str],
                 annotation_file_path: Optional[str]):
        #  Swagger spec file path
        self.SpecFilePath = spec_file_path
        #  File path to the custom fuzzing dictionary
        self.DictionaryFilePath = dictionary_file_path

        #  Inline json for the fuzzing dictionary
        #  This can be specified if the user wants a new dictionary generated, but
        #  just wants to specify one property inline
        self.Dictionary = dictionary
        #  The RESTler annotations that should be used for this Swagger spec only
        #  Note: global annotations that should be applied to multiple specs must be
        #  specified at the top level of the config
        self.AnnotationFilePath = annotation_file_path

    def __dict__(self):
        return {
            "SpecFilePath": self.SpecFilePath,
            "DictionaryFilePath": self.DictionaryFilePath,
            "Dictionary": self.Dictionary,
            "AnnotationFilePath": self.AnnotationFilePath
        }


#  The configuration for the payload examples.
# Define the ExampleFileConfig class
class ExampleFileConfig:
    file_path: str
    exact_copy: bool

    def __init__(self, file_path: str, exact_copy: bool):
        #  The path to the example configuration file that contains the examples associated with
        #  one or more request types from the spec.
        self.file_path = file_path

        #  If 'true', copy these examples exactly, without substituting any parameter values from the dictionary
        #  If 'false' (default), the examples are merged with the schema.  In particular, parameters with names
        #  that do not match the schema are discarded.
        self.exact_copy = exact_copy

    def __dict__(self):
        return {"FilePath": self.file_path, "ExactCopy": self.exact_copy}


class UninitializedError(Exception):
    pass


# Define the function convert_to_abs_path
def convert_to_abs_path(current_dir_path: str, file_path: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    else:
        return os.path.join(current_dir_path, file_path)


def ConfigSetting():
    """ Accessor for the RestlerSettings singleton """
    return Config.Instance()


# Define the Config class
#  User-specified compiler configuration
class Config(object):
    __instance = None

    #  An API specification configuration that includes the Swagger specification and
    #  other artifacts (e.g., annotations to augment the information in the spec).
    SwaggerSpecConfig: Optional[List[SwaggerSpecConfigClass]] = None

    #  The Swagger specification specifying this API
    SwaggerSpecFilePath: Optional[List[str]] = None

    #  If specified, use this as the input and generate the python grammar.
    GrammarInputFilePath: Optional[str] = None
    CustomDictionaryFilePath: Optional[str] = None
    AnnotationFilePath: Optional[str] = None

    #  File path specifying the example config file

    ExampleConfigFilePath: Optional[str] = None

    #  Specifies the example config files.  If the example config file path
    #  is specified, both are used.
    ExampleConfigFiles: Optional[List[ExampleFileConfig]] = None
    GrammarOutputDirectoryPath: Optional[str] = None
    IncludeOptionalParameters: bool = True
    UsePathExamples: bool = False
    UseQueryExamples: bool = True
    UseBodyExamples: bool = True
    UseHeaderExamples: bool = False

    #  When set to 'true', discovers examples and outputs them to a directory next to the grammar.
    #  If an existing directory exists, does not over-write it.
    DiscoverExamples: bool = False
    #  When specified, all example payloads are used - both the ones in the specification and the ones in the
    #  example config file.
    #  False by default - example config files override any other available payload examples
    UseAllExamplePayloads: bool = False
    #  The directory where the compiler should look for examples.
    #  If 'discoverExamples' is true, this directory will contain the
    #  example files that have been discovered.
    #  If 'discoverExamples' is false, every time an example is used in the
    #  Swagger file, RESTler will first look for it in this directory.
    ExamplesDirectory: str = ""
    ResolveQueryDependencies: bool = True
    ResolveBodyDependencies: bool = True
    ResolveHeaderDependencies: bool = False
    #  When true, only fuzz the GET requests
    ReadOnlyFuzz: bool = False
    UseRefreshableToken: Optional[bool] = True

    #  When true, allow GET requests to be considered.
    #  This option is present for debugging, and should be
    #  set to 'false' by default.
    #  In limited cases when GET is a valid producer, the user
    #  should add an annotation for it.
    AllowGetProducers: bool = False
    #  If specified, update the engine settings with hints derived from the grammar.
    EngineSettingsFilePath: Optional[str] = None

    #  Perform data fuzzing
    DataFuzzing: bool = False
    #  When specified, use only this naming convention to infer
    #  producer-consumer dependencies.
    ApiNamingConvention: Optional[NamingConvention] = None

    #  When this switch is on, the generated grammar will contain
    #  parameter names for all fuzzable values.  For example:
    #  restler_fuzzable_string("1", param_name="num_items")
    TrackFuzzedParameterNames: bool = False
    #  The maximum depth for Json properties in the schema to test
    #  Any properties exceeding this depth are removed.
    JsonPropertyMaxDepth: Optional[int] = None

    @staticmethod
    def Instance():
        """ Singleton's instance accessor

        @return RestlerSettings instance
        @rtype  RestlerSettings

        """
        if Config.__instance is None:
            raise UninitializedError("config not yet initialized.")
        return Config.__instance

    def __init__(self):
        self.SwaggerSpecConfig = []
        self.SwaggerSpecFilePath = []
        self.GrammarInputFilePath = None
        self.CustomDictionaryFilePath = None
        self.AnnotationFilePath = None
        self.ExampleConfigFilePath = None
        self.ExampleConfigFiles = []
        self.GrammarOutputDirectoryPath = ""
        self.IncludeOptionalParameters = True
        self.UseQueryExamples = True
        self.UseHeaderExamples = False
        self.UseBodyExamples = True
        self.UsePathExamples = False
        self.UseAllExamplePayloads = False
        self.DiscoverExamples = False
        self.ExamplesDirectory = ""
        self.ResolveQueryDependencies = True
        self.ResolveBodyDependencies = True
        self.ResolveHeaderDependencies = False
        self.ReadOnlyFuzz = False
        self.UseRefreshableToken = True
        self.AllowGetProducers = False
        self.EngineSettingsFilePath = None
        self.DataFuzzing = False
        self.ApiNamingConvention = None
        self.TrackFuzzedParameterNames = False
        self.JsonPropertyMaxDepth = None
        Config.__instance = self

    def __dict__(self):
        example_files = []
        if self.ExampleConfigFiles:
            for item in self.ExampleConfigFiles:
                example_files.append(item.__dict__())

        api_specs_config = []
        if self.SwaggerSpecConfig:
            for item in self.SwaggerSpecConfig:
                if item:
                    api_specs_config.append(item.__dict__())

        api_spec = []
        if self.SwaggerSpecFilePath:
            for item in self.SwaggerSpecFilePath:
                api_spec.append(item)

        return {
            "SwaggerSpecFilePath": api_spec,
            "SwaggerSpecConfig": api_specs_config,
            "GrammarOutputDirectoryPath": self.GrammarOutputDirectoryPath,
            "CustomDictionaryFilePath": self.CustomDictionaryFilePath,
            "GrammarInputFilePath": self.GrammarInputFilePath,
            "AnnotationFilePath": self.AnnotationFilePath,
            "ExampleConfigFiles": example_files,
            "ExampleConfigFilePath": self.ExampleConfigFilePath,
            "IncludeOptionalParameters": self.IncludeOptionalParameters,
            "EngineSettingsFilePath": self.EngineSettingsFilePath,
            "UseHeaderExamples": self.UseHeaderExamples,
            "UsePathExamples": self.UsePathExamples,
            "UseQueryExamples": self.UseQueryExamples,
            "UseBodyExamples": self.UseBodyExamples,
            "UseAllExamplePayloads": self.UseAllExamplePayloads,
            "DiscoverExamples": self.DiscoverExamples,
            "ExamplesDirectory": self.ExamplesDirectory,
            "DataFuzzing": self.DataFuzzing,
            "ApiNamingConvention": self.ApiNamingConvention,
            "ReadOnlyFuzz": self.ReadOnlyFuzz,
            "ResolveHeaderDependencies": self.ResolveHeaderDependencies,
            "ResolveQueryDependencies": self.ResolveQueryDependencies,
            "ResolveBodyDependencies": self.ResolveBodyDependencies,
            "UseRefreshableToken": self.UseRefreshableToken,
            "AllowGetProducers": self.AllowGetProducers,
            "TrackFuzzedParameterNames": self.TrackFuzzedParameterNames,
            "JsonPropertyMaxDepth": self.JsonPropertyMaxDepth
        }

    @classmethod
    def init_from_json(cls, config):
        self = cls()
        #  An API specification configuration that includes the Swagger specification and
        #  other artifacts (e.g., annotations to augment the information in the spec).
        api_specs = []
        if 'SwaggerSpecConfig' in config:
            swagger_spec_config = config['SwaggerSpecConfig']
            for api_spec_config in swagger_spec_config:
                annotation_file_path = api_spec_config['AnnotationFilePath'] \
                    if 'AnnotationFilePath' in api_spec_config else None
                dictionary_file_path = api_spec_config['DictionaryFilePath'] \
                    if 'DictionaryFilePath' in api_spec_config else None
                spec_file_path = api_spec_config['SpecFilePath'] \
                    if 'SpecFilePath' in api_spec_config else None
                api_specs.append(SwaggerSpecConfigClass(spec_file_path=spec_file_path,
                                                        dictionary_file_path=dictionary_file_path,
                                                        dictionary=api_spec_config['Dictionary']
                                                        if 'Dictionary' in swagger_spec_config else None,
                                                        annotation_file_path=annotation_file_path))

        self.SwaggerSpecConfig = api_specs

        #  The Swagger specification specifying this API
        self.SwaggerSpecFilePath = config['SwaggerSpecFilePath'] \
            if 'SwaggerSpecFilePath' in config else self.SwaggerSpecFilePath

        #  If specified, use this as the input and generate the python grammar.
        self.GrammarInputFilePath = config['GrammarInputFilePath'] \
            if 'GrammarInputFilePath' in config else self.GrammarInputFilePath
        self.CustomDictionaryFilePath = config['CustomDictionaryFilePath'] \
            if 'CustomDictionaryFilePath' in config else self.CustomDictionaryFilePath
        self.AnnotationFilePath = config['AnnotationFilePath'] \
            if 'AnnotationFilePath' in config else self.AnnotationFilePath

        self.ExampleConfigFilePath = config['ExampleConfigFilePath'] \
            if 'ExampleConfigFilePath' in config else self.ExampleConfigFilePath

        example_files = []
        if 'ExampleConfigFiles' in config:
            configure = config['ExampleConfigFiles']
            for item in configure:
                file_path = item['filePath'] if 'filePath' in item else None
                exact_copy = item['exactCopy'] if 'exactCopy' in item else None
                example_files.append(ExampleFileConfig(file_path, exact_copy))

        self.ExampleConfigFiles = example_files
        self.GrammarOutputDirectoryPath = config['GrammarOutputDirectoryPath'] \
            if 'GrammarOutputDirectoryPath' in config else self.GrammarOutputDirectoryPath
        self.IncludeOptionalParameters = config['IncludeOptionalParameters'] \
            if 'IncludeOptionalParameters' in config else self.IncludeOptionalParameters
        self.UsePathExamples = config['UsePathExamples'] \
            if 'UsePathExamples' in config else self.UsePathExamples
        self.UseQueryExamples = config['UseQueryExamples'] \
            if 'UseQueryExamples' in config else self.UseQueryExamples
        self.UseBodyExamples = config['UseBodyExamples'] \
            if 'UseBodyExamples' in config else self.UseBodyExamples
        self.UseHeaderExamples = config['UseHeaderExamples'] \
            if 'UseHeaderExamples' in config else self.UseHeaderExamples

        self.DiscoverExamples = config['DiscoverExamples'] \
            if 'DiscoverExamples' in config else self.DiscoverExamples

        self.UseAllExamplePayloads = config['UseAllExamplePayloads'] \
            if 'UseAllExamplePayloads' in config else self.UseAllExamplePayloads

        self.ExamplesDirectory = config['ExamplesDirectory'] \
            if 'ExamplesDirectory' in config else self.ExamplesDirectory
        self.ResolveQueryDependencies = config['ResolveQueryDependencies'] \
            if 'ResolveQueryDependencies' in config else self.ResolveQueryDependencies
        self.ResolveBodyDependencies = config['ResolveBodyDependencies'] \
            if 'ResolveBodyDependencies' in config else self.ResolveBodyDependencies
        self.ResolveHeaderDependencies = config['ResolveHeaderDependencies'] \
            if 'ResolveHeaderDependencies' in config else self.ResolveHeaderDependencies

        self.ReadOnlyFuzz = config['ReadOnlyFuzz'] if 'ReadOnlyFuzz' in config else False
        self.UseRefreshableToken = config['UseRefreshableToken'] \
            if 'UseRefreshableToken' in config else self.UseRefreshableToken

        self.AllowGetProducers = config['AllowGetProducers'] \
            if 'AllowGetProducers' in config else self.AllowGetProducers

        self.EngineSettingsFilePath = config['EngineSettingsFilePath'] \
            if 'EngineSettingsFilePath' in config else self.EngineSettingsFilePath

        self.DataFuzzing = config['DataFuzzing'] \
            if 'DataFuzzing' in config else self.DataFuzzing

        self.ApiNamingConvention = config['ApiNamingConvention'] \
            if 'ApiNamingConvention' in config else self.ApiNamingConvention

        self.TrackFuzzedParameterNames = config['TrackFuzzedParameterNames'] \
            if 'TrackFuzzedParameterNames' in config else self.TrackFuzzedParameterNames
        self.JsonPropertyMaxDepth = config['JsonPropertyMaxDepth'] \
            if 'JsonPropertyMaxDepth' in config else self.JsonPropertyMaxDepth
        return self

    # Determines which dictionary to use with each Swagger/OpenAPI spec and returns
    # a 'SwaggerSpecConfig' for each specification.
    def get_swagger_spec_configs_from_compiler_config(self) -> list[SwaggerSpecConfigClass]:
        swagger_docs = []
        docs_with_empty_config = []
        if self.SwaggerSpecFilePath is None and self.SwaggerSpecConfig is None:
            raise ValueError("unspecified API spec file path")
        elif self.SwaggerSpecFilePath:
            for path in self.SwaggerSpecFilePath:
                if os.path.exists(path):
                    swagger_docs.append(path)
                else:
                    # logger.write_to_main(f"ERROR: invalid path found in the list of Swagger specs given: {path}")
                    raise ValueError(f"invalid API spec file path found: {path}")

            for doc in swagger_docs:
                docs_with_empty_config.append(SwaggerSpecConfigClass(spec_file_path=doc,
                                                                     dictionary_file_path=None,
                                                                     dictionary=None,
                                                                     annotation_file_path=None))
        configured_swagger_docs = []
        if self.SwaggerSpecConfig is None or len(self.SwaggerSpecConfig) == 0:
            if len(swagger_docs) == 0:
                raise ValueError("unspecified API spec file path")
            else:
                configured_swagger_docs = docs_with_empty_config
        else:
            for item in self.SwaggerSpecConfig:
                if item is not None and item.SpecFilePath is not None:
                    if os.path.exists(item.SpecFilePath):
                        configured_swagger_docs.append(item)
                    else:
                        print(f"ERROR: invalid path found in the list of Swagger configurations given: {item}")
                        raise ValueError(f"invalid API spec file path found: {item}")
        return configured_swagger_docs

    # Define the function convert_relative_to_abs_paths

    # When relative paths are specified in the config, they are expected to
    # be relative to the config file directory.  This function converts all paths to
    # absolute paths.
    def convert_relative_to_abs_paths(self, config_file_path: str):
        # Get the directory of the config file
        # If relative paths are specified in the config, they are expected to
        # be relative to the config file directory.
        config_file_dir_path = os.path.dirname(os.path.abspath(config_file_path))
        # Convert SwaggerSpecFilePath to absolute paths
        if self.SwaggerSpecFilePath:
            swagger_spec_file_paths = [convert_to_abs_path(config_file_dir_path, path) for path in
                                       self.SwaggerSpecFilePath]
            self.SwaggerSpecFilePath = swagger_spec_file_paths

        # Convert SwaggerSpecConfig paths to absolute paths
        if self.SwaggerSpecConfig:
            for api_spec_config in self.SwaggerSpecConfig:
                api_spec_config.AnnotationFilePath = convert_to_abs_path(config_file_dir_path,
                                                                         api_spec_config.AnnotationFilePath) \
                    if api_spec_config.AnnotationFilePath else None
                api_spec_config.DictionaryFilePath = convert_to_abs_path(config_file_dir_path,
                                                                         api_spec_config.DictionaryFilePath) \
                    if api_spec_config.DictionaryFilePath else None
                api_spec_config.SpecFilePath = convert_to_abs_path(config_file_dir_path, api_spec_config.SpecFilePath) \
                    if api_spec_config.SpecFilePath else None

        self.CustomDictionaryFilePath = convert_to_abs_path(config_file_dir_path, self.CustomDictionaryFilePath) \
            if self.CustomDictionaryFilePath else None
        self.GrammarInputFilePath = convert_to_abs_path(config_file_dir_path, self.GrammarInputFilePath) \
            if self.GrammarInputFilePath else None
        self.EngineSettingsFilePath = convert_to_abs_path(config_file_dir_path, self.EngineSettingsFilePath) \
            if self.EngineSettingsFilePath else None
        self.AnnotationFilePath = convert_to_abs_path(config_file_dir_path, self.AnnotationFilePath) \
            if self.AnnotationFilePath else None
        self.ExampleConfigFilePath = convert_to_abs_path(config_file_dir_path, self.ExampleConfigFilePath) \
            if self.ExampleConfigFilePath else None

        if self.ExampleConfigFiles:
            for item in self.ExampleConfigFiles:
                item.file_path = convert_to_abs_path(config_file_dir_path, item.file_path)


# A sample config with all supported values initialized.
class SampleConfig(Config):
    def __init__(self):
        super().__init__()
        self.SwaggerSpecConfig = None
        self.SwaggerSpecFilePath = None
        self.GrammarInputFilePath = None
        self.CustomDictionaryFilePath = None
        self.AnnotationFilePath = None
        self.ExampleConfigFilePath = None
        self.ExampleConfigFiles = None
        self.GrammarOutputDirectoryPath = None
        self.IncludeOptionalParameters = True
        self.UsePathExamples = None
        self.UseQueryExamples = None
        self.UseBodyExamples = None
        self.UseHeaderExamples = None
        self.DiscoverExamples = False
        self.UseAllExamplePayloads = None
        self.ExamplesDirectory = ""
        self.ResolveQueryDependencies = True
        self.ResolveBodyDependencies = False
        self.ResolveHeaderDependencies = False
        self.ReadOnlyFuzz = False
        self.UseRefreshableToken = True
        self.AllowGetProducers = False
        self.EngineSettingsFilePath = None
        self.DataFuzzing = True
        self.ApiNamingConvention = None
        self.TrackFuzzedParameterNames = False
        self.JsonPropertyMaxDepth = None


# The default config used for unit tests.  Most of these should also be the defaults for
# end users, and options should be explicitly changed by the caller (e.g. RESTler driver or
# the user settings file).
class DefaultConfig(Config):
    def __init__(self):
        super().__init__()
        self.SwaggerSpecConfig = None
        self.SwaggerSpecFilePath = None
        self.GrammarInputFilePath = None
        self.CustomDictionaryFilePath = None
        self.AnnotationFilePath = None
        self.ExampleConfigFilePath = None
        self.ExampleConfigFiles = None
        self.GrammarOutputDirectoryPath = None
        self.IncludeOptionalParameters = True
        self.UseQueryExamples = True
        self.UseHeaderExamples = True
        self.UseBodyExamples = True
        self.UsePathExamples = False
        self.UseAllExamplePayloads = False
        self.DiscoverExamples = False
        self.ExamplesDirectory = ""
        self.ResolveQueryDependencies = True
        self.ResolveBodyDependencies = True
        self.ResolveHeaderDependencies = False
        self.ReadOnlyFuzz = False
        self.UseRefreshableToken = True
        self.AllowGetProducers = False
        self.EngineSettingsFilePath = None
        self.DataFuzzing = False
        self.ApiNamingConvention = None
        self.TrackFuzzedParameterNames = False
        self.JsonPropertyMaxDepth = None
