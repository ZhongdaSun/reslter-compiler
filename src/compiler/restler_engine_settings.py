# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from compiler.utilities import JsonSerialization


class Constants:
    PerResourceSettingsKey = "per_resource_settings"
    ProducerTimingDelayKey = "producer_timing_delay"
    CustomDictionaryKey = "custom_dictionary"
    MaxParameterCombinationsKey = "max_combinations"
    DefaultParameterCombinations = 20


class EngineSettings:
    settings: dict

    def __init__(self, settings: dict):
        self.settings = settings

    def get_per_resource_settings(self):
        prs = self.settings.get(Constants.PerResourceSettingsKey)
        return prs if prs else None

    def get_per_resource_dictionary(self, endpoint):
        prs = self.get_per_resource_settings()
        if prs:
            resource_settings = prs.get(endpoint)
            if resource_settings:
                return resource_settings.get(Constants.CustomDictionaryKey)
            return None

    def get_body_payload_recipe_file_path(self):
        checkers_key = "checkers"
        payload_body_key = "payloadbody"
        recipe_file_key = "recipe_file"

        checker_settings = self.settings.get(checkers_key)
        if checker_settings:
            payload_body = checker_settings.get(payload_body_key)
            if payload_body:
                return payload_body.get(recipe_file_key)

    def add_per_resource_timing_delays(self, requests):
        default_timing_delay_seconds = 0
        per_resource_settings = self.get_per_resource_settings() or {}

        for req in requests:
            if req.requestMetadata.isLongRunningOperation:
                timing_delay_setting = {Constants.ProducerTimingDelayKey: default_timing_delay_seconds}
                if req.id.endpoint not in per_resource_settings:
                    per_resource_settings[req.id.endpoint] = timing_delay_setting
                else:
                    per_resource_settings[req.id.endpoint].setdefault(Constants.ProducerTimingDelayKey,
                                                                      default_timing_delay_seconds)

        self.settings.pop(Constants.PerResourceSettingsKey, None)
        self.settings[Constants.PerResourceSettingsKey] = per_resource_settings

    def add_per_resource_dictionaries(self,
                                      per_resource_dictionaries,
                                      engine_settings_file_path,
                                      grammar_output_directory_path):
        per_resource_settings = self.get_per_resource_settings() or {}

        for endpoint, values in per_resource_dictionaries.items():
            dictionary_name = values[0][0]
            dictionary_file_path = f"{dictionary_name}.json"
            dictionary_setting = {Constants.CustomDictionaryKey: dictionary_file_path}

            if endpoint not in per_resource_settings:
                per_resource_settings[endpoint] = dictionary_setting
            else:
                per_resource_settings[endpoint].setdefault(Constants.CustomDictionaryKey, dictionary_file_path)

        self.settings.pop(Constants.PerResourceSettingsKey, None)
        self.settings[Constants.PerResourceSettingsKey] = per_resource_settings

    def add_max_combinations(self):
        if Constants.MaxParameterCombinationsKey not in self.settings:
            self.settings[Constants.MaxParameterCombinationsKey] = Constants.DefaultParameterCombinations

    def __dict__(self):
        dict_value = {
            "client_certificate_path": None,
            "max_combinations": str(self.settings.get(Constants.MaxParameterCombinationsKey)),
            "test_combinations_settings": {
                "example_payloads": {
                    "payload_kind": "all"
                },
                "max_examples": 100,
                "max_schema_combinations": 30
            },
            "max_request_execution_time": 90,
            "save_results_in_fixed_dirname": False,
            "global_producer_timing_delay": 2,
            "dyn_objects_cache_size": 200,
            "fuzzing_jobs": 1,
            "fuzzing_mode": "bfs",
            "garbage_collection_interval": 300,
            "reconnect_on_every_request": False,
            "ignore_dependencies": True,
            "ignore_feedback": True,
            "include_user_agent": True,
            "run_gc_after_every_sequence": True,
            "max_async_resource_creation_time": 45,
            "max_sequence_length": 11,
            "no_ssl": True,
            "disable_cert_validation": True,
            "disable_logging": False,
            "no_tokens_in_logs": True,
            "ignore_decoding_failures": True,
            "request_throttle_ms": 500,
            "custom_retry_settings": {
                "status_codes": [
                    "429"
                ],
                "response_text": [
                    "please re-try"
                ],
                "interval_sec": 5
            },
            "target_ip": "100.100.100.100",
            "target_port": 500,
            "time_budget": 12,
            "token_refresh_cmd": "some refresh command",
            "add_fuzzable_dates": True,
            "token_refresh_interval": 60,
            "wait_for_async_resource_creation": False,
            "custom_value_generators": "E:\\test\\python_autotest\\test_dict\\custom_value_generators.py",
            "per_resource_settings": self.settings[Constants.PerResourceSettingsKey],
            "sequence_exploration_settings": {
                "create_prefix_once": [
                    {
                        "methods": ["GET", "HEAD"],
                        "endpoints": "*",
                        "reset_after_success": False
                    }
                ]
            },
            "include_requests": [
            ],
            "max_logged_request_combinations": 5,
            "exclude_requests": [
            ],
            "checkers": {
                "NamespaceRule": {
                    "mode": "exhaustive"
                },
                "Examples": {
                    "mode": "exhaustive"
                },
                "UseAfterFree": {
                    "mode": "exhaustive"
                },
                "LeakageRule": {
                    "mode": "exhaustive"
                },
                "InvalidDynamicObject": {
                    "mode": "exhaustive"
                },
                "ResourceHierarchy": {
                    "mode": "exhaustive"
                },
                "PayloadBody": {
                    "mode": "normal",
                    "start_with_valid": True,
                    "start_with_examples": True,
                    "size_dep_budget": False,
                    "use_feedback": True
                },
                "InvalidValue": {
                    "custom_dictionary": "E:\\test\\python_autotest\\src\\test_dict\\defaultDict.json",
                    "max_combinations": 2,
                    "custom_value_generators": "E:\\test\\python_autotest\\src\\test_dict\\invalid_value_generators.py",
                    "random_seed": 0
                }
            },
            "custom_bug_codes": [
                "400",
                "2?4",
                "3*"
            ],
            "custom_non_bug_codes": [
                "404",
                "500"
            ]
        }
        return dict_value


# 获取引擎设置
def get_engine_settings(engine_settings_file_path):
    if os.path.exists(engine_settings_file_path):
        try:
            json_data = JsonSerialization.try_deeserialize_from_file(engine_settings_file_path)
            return True, EngineSettings(settings=json_data)
        except Exception as e:
            return False, Exception(str(e))
    else:
        return False, Exception(f"ERROR: invalid path specified for engine settings: {engine_settings_file_path}")


def new_engine_settings() -> EngineSettings:
    return EngineSettings({})


# 更新引擎设置并写入编译器输出目录
def update_engine_settings(requests,
                           per_resource_dictionaries,
                           engine_settings_file_path,
                           grammar_output_directory_path,
                           new_engine_settings_file_path):
    if engine_settings_file_path is not None:
        is_succeeded, engine_settings = get_engine_settings(engine_settings_file_path)

        if is_succeeded:
            engine_settings.add_per_resource_dictionaries(per_resource_dictionaries,
                                                          engine_settings_file_path,
                                                          grammar_output_directory_path)
            engine_settings.add_max_combinations()
            JsonSerialization.serialize_to_file(file=new_engine_settings_file_path, obj=engine_settings.__dict__())
            return True
        else:
            return False

    else:
        engine_settings = EngineSettings(settings={})
        engine_settings.add_max_combinations()
        engine_settings.add_per_resource_dictionaries(per_resource_dictionaries,
                                                      engine_settings_file_path,
                                                      grammar_output_directory_path)
        JsonSerialization.serialize_to_file(file=new_engine_settings_file_path, obj=engine_settings.__dict__())
        return True
