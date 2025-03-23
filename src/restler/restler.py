# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

""" Main application entrypoint.

To see all supported arguments type: python restler.py -h

"""
from __future__ import print_function
import os
import sys
from pathlib import Path

if __name__ == '__main__' and 'restler' not in sys.modules:
    autotest_dir = Path(__file__).absolute().parent
    sys.path = [str(autotest_dir.parent)] + [p for p in sys.path if Path(p) != autotest_dir]
    print(f"autotest_dir={autotest_dir} sys.path={sys.path}")

import signal
import json
import shutil
import argparse
from dataclasses import dataclass
from typing import Optional

import traceback

import restler.utils.logging.trace_db as trace_db
import restler.utils.formatting as formatting

from restler.engine import bug_bucketing
from restler import checkers, restler_settings
from restler.restler_settings import (
    Settings,
    RestlerSettings,
    LogSetting)
import restler.engine.dependencies as dependencies
import restler.engine.core.preprocessing as preprocessing
import restler.engine.core.postprocessing as postprocessing
import restler.engine.core.driver as driver
import restler.engine.core.fuzzer as fuzzer
import restler.utils.import_utilities as import_utilities
import restler.engine.core.fuzzing_monitor as fuzzing_monitor
import restler.engine.core.requests as requests
from restler.engine.errors import InvalidDictionaryException
from restler.engine.errors import NoTokenSpecifiedException
from restler.engine.primitives import InvalidDictPrimitiveException
from restler.engine.primitives import UnsupportedPrimitiveException
from restler.utils import restler_logger as logger

MANAGER_HANDLE = None
Restler_User_Settings = "restler_user_settings.json"


def import_grammar(path):
    """ Imports grammar from path. Must work with relative and full paths.

    @param path: The path to import grammar from.
    @type  path: Str

    @return: The RequestCollection constructed from grammar in @param path.
    @rtype: RequestCollection class object.
    """

    try:
        logger.write_to_main(f"path={path}", LogSetting().restler)
        req_collection = import_utilities.import_attr(path, "req_collection")

    except Exception as error:
        print(f"import_grammar: {error!s}")
        sys.exit(-1)

    grammar_name = os.path.basename(path).replace(".py", "")
    grammar_file = f'restler_grammar_{grammar_name}_{os.getpid()}.py'
    try:
        target_path = os.path.join(logger.EXPERIMENT_DIR, grammar_file)
        shutil.copyfile(path, target_path)
    except shutil.Error:
        pass

    return req_collection


def get_checker_list(req_collection, fuzzing_requests, enable_list, disable_list, set_enable_first, custom_checkers):
    """ Initializes all of the checkers, sets the appropriate checkers
    as enabled/disabled, and returns a list of checker objects

    Note: Order may matter for checkers, in the sense that some checkers (like
    the namespacechecker) reset the state before fuzzing, while others (like the
    use-after-free checker) start operating immediately after the main driver.
    Thus, to be safe, we do not want to reorder the checkers.

    The checkers (at least in Python 2.7) are added to the list in the order
    that they are imported, which is defined in checkers/__init__.py.

    InvalidDynamicObjectChecker was put to the back of the checker order,
    so it doesn't interfere with the others. It also re-renders all of the
    sequences that it needs itself, so it shouldn't be affected by the other
    checkers either.

    As long as the checkers are not re-ordered there shouldn't be any issue with
    skipping some. They don't rely on each other, but it's possible that some
    checkers could affect the fuzzing state in such a way that the next checker
    could behave incorrectly. For instance, LeakageRule needs to use the
    last_rendering_cache from the Fuzz, so we don't want that to be affected by
    another checker (this is why it is run first).

    @param req_collection: The global request collection
    @type  req_collection: RequestCollection
    @param fuzzing_requests: The collection of requests to fuzz
    @type  fuzzing_requests: FuzzingRequestCollection
    @param enable_list: The user-specified list of checkers to enable
    @type  enable_list: List[str]
    @param disable_list: The user-specified list of checkers to disable
    @type  disable_list: List[str]
    @param set_enable_first: This sets the ordering priority for the cases where
                            the user specifies the same checker in both lists.
                            If this is True, set the enabled values first and then
                            set the disabled values (or vice-versa if False).
    @type  set_enable_first: Bool
    @param custom_checkers: List of paths to custom checker python files
    @type  custom_checkers: List[str]

    @return: List of Checker objects to apply
    @rtype : List[Checker]

    """
    # Add any custom checkers
    for custom_checker_file_path in custom_checkers:
        try:
            import_utilities.load_module('custom_checkers', custom_checker_file_path)
            logger.write_to_main(f"Loaded custom checker from {custom_checker_file_path}",
                                 print_to_console=LogSetting().restler)
        except Exception as err:
            traceback.print_exc()
            logger.write_to_main(f"Failed to load custom checker {custom_checker_file_path}: {err!s}",
                                 print_to_console=True)
            sys.exit(-1)

    # Initialize the checker subclasses from CheckerBase
    available_checkers = [checker(req_collection, fuzzing_requests) \
                          for checker in checkers.CheckerBase.__subclasses__()]

    # Set the first and second lists based on the set_enable_first Bool
    if set_enable_first:
        first_list = enable_list
        second_list = disable_list
        first_enable = True
        second_enable = False
    else:
        first_list = disable_list
        second_list = enable_list
        first_enable = False
        second_enable = True

    # Convert lists to lowercase for case-insensitive comparisons
    first_list = [x.lower() for x in first_list]
    second_list = [x.lower() for x in second_list]

    if '*' in second_list:
        second_list = []
        for checker in available_checkers:
            second_list.append(checker.friendly_name)
    # If the second list (priority list) is set to all,
    # do not use the first list
    elif '*' in first_list:
        first_list = []
        for checker in available_checkers:
            first_list.append(checker.friendly_name)

    # Iterate through each checker and search for its friendly name
    # in each list of enabled/disabled
    for checker in available_checkers:
        logger.write_to_main(f"checker={checker.friendly_name}", LogSetting().restler)
        if checker.friendly_name in first_list:
            checker.enabled = first_enable
        if checker.friendly_name in second_list:
            checker.enabled = second_enable

    return available_checkers


def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    # Stop the Sync Manager process to avoid a zombie process
    global MANAGER_HANDLE
    if MANAGER_HANDLE != None:
        MANAGER_HANDLE.shutdown()
    sys.exit(0)


@dataclass
class ExecuteParam:
    settings: Optional[str]
    restler_grammar: str
    working_dir: str
    enable_checkers: []
    disable_checkers: []


def load_common_engine(dir_name: str):
    engine_file = os.path.join(dir_name, Restler_User_Settings)
    try:
        with open(engine_file, encoding='utf-8') as file_handler:
            engine_settings_dict = json.load(file_handler)
            file_handler.close()
    except Exception as error:
        print(f"Error: Failed to load settings file: {error!s}")
        sys.exit(-1)

    if "custom_mutations" in engine_settings_dict.keys():
        engine_settings_dict["custom_mutations"] = os.path.join(dir_name, engine_settings_dict["custom_mutations"])

    if "custom_value_generators" in engine_settings_dict.keys():
        engine_settings_dict["custom_value_generators"] = os.path.join(dir_name,
                                                                       engine_settings_dict["custom_value_generators"])

    if "checkers" in engine_settings_dict.keys():
        checkers_value = engine_settings_dict["checkers"]
        for key_item, values in checkers_value.items():
            if "custom_mutations" in values.keys():
                values["custom_mutations"] = os.path.join(dir_name, values["custom_mutations"])
            if "custom_value_generators" in values.keys():
                values["custom_value_generators"] = os.path.join(dir_name, values["custom_value_generators"])

    if "per_resource_settings" in engine_settings_dict.keys():
        pre_resource_settings = engine_settings_dict["per_resource_settings"]
        for key, values in pre_resource_settings.items():
            if "custom_dictionary" in values.keys():
                values["custom_dictionary"] = os.path.join(dir_name, values["custom_dictionary"])
            if "custom_generators" in values.keys():
                values["custom_generators"] = os.path.join(dir_name, values["custom_generators"])

    if "replay_log" in engine_settings_dict.keys():
        engine_settings_dict["replay_log"] = os.path.join(dir_name, engine_settings_dict["replay_log"])

    if "replay" in engine_settings_dict.keys():
        replay_log = engine_settings_dict["replay"]
        if "trace_database_file_path" in replay_log.keys():
            replay_log["trace_database_file_path"] = os.path.join(dir_name, replay_log["trace_database_file_path"])

    return engine_settings_dict


def execute_restler(config_arg: ExecuteParam):
    try:
        with open(os.path.join(os.path.dirname(__file__), "log_settings.json")) as file_handler:
            log_file = json.load(file_handler)
            file_handler.close()
            LogSetting().init_from_json(log_file)
    except Exception as error:
        print(f"Error: Failed to load settings file: {error!s}")
        sys.exit(-1)

    engine_file_dir = os.path.dirname(__file__)
    local_user_args = load_common_engine(engine_file_dir)
    if bool(config_arg.working_dir):
        local_user_args.update({"engine_file_folder": config_arg.working_dir})
    else:
        local_user_args.update({"engine_file_folder": engine_file_dir})

    # combine settings from settings file to the command-line arguments
    if config_arg.settings:
        local_user_args.update(config_arg.settings)
        local_user_args["settings_file_exists"] = True

    if config_arg.restler_grammar:
        # Set grammar schema to the same path as the restler grammar, but as json
        local_user_args["grammar_schema"] = '.json'.join(config_arg.restler_grammar.rsplit('.py', 1))

    try:
        # Set the restler settings singleton
        engine_settings = restler_settings.RestlerSettings(local_user_args, engine_file_dir)
    except restler_settings.InvalidValueError as e:
        print(f"\nArgument Error::\n\t{e!s}")
        sys.exit(-1)
    except Exception as e:
        print(f"\nFailed to parse user settings file: {e!s}")
        sys.exit(-1)

    try:
        engine_settings.validate_options()
    except restler_settings.OptionValidationError as e:
        print(f"\nArgument Error::\n\t{e!s}")
        sys.exit(-1)

    # Options Validation
    custom_mutations_dict = {}
    replay_log = local_user_args.get('replay_log', None)
    # Replay may be performed with or without the grammar file.
    if not replay_log:
        if not config_arg.restler_grammar:
            print("\nArgument Error::\n\tNo restler grammar was provided.\n")
            sys.exit(-1)

    if engine_settings.fuzzing_mode not in ['bfs', 'bfs-cheap'] and engine_settings.fuzzing_jobs > 1:
        print("\nArgument Error::\n\tOnly bfs supports multiple fuzzing jobs\n")
        sys.exit(-1)
    custom_mutations = local_user_args.get('custom_mutations', None)
    if custom_mutations is not None:
        try:
            if os.path.exists(custom_mutations):
                with open(custom_mutations, encoding='utf-8') as file_handler:
                    custom_mutations_dict = json.load(file_handler)
                    file_handler.close()
            elif os.path.exists(os.path.join(engine_file_dir, custom_mutations)):
                with open(os.path.join(engine_file_dir, custom_mutations), encoding='utf-8') as file_handler:
                    custom_mutations_dict = json.load(file_handler)
                    file_handler.close()
            else:
                with open(os.path.join(os.path.join(__file__), local_user_args['custom_mutations']),
                          encoding='utf-8') as file_handler:
                    custom_mutations_dict = json.load(file_handler)
                    file_handler.close()
        except Exception as error:
            print(f"Cannot import custom mutations: {error!s}")
            sys.exit(-1)

        if engine_settings.custom_value_generators_file_path:
            if not engine_settings.custom_value_generators_file_path.endswith(".py"):
                print(f"Custom value generators must be provided in a Python file.")
                sys.exit(-1)

            if not os.path.exists(engine_settings.custom_value_generators_file_path):
                print(
                    f"Invalid custom value generators file specified: {engine_settings.custom_value_generators_file_path}")
                sys.exit(-1)

    if engine_settings.save_results_in_fixed_dirname:
        logger.save_results_in_fixed_dirname()

    # Create the directory where all the results will be saved
    try:
        logger.create_experiment_dir(os.path.dirname(config_arg.restler_grammar))
    except Exception as err:
        print(f"Failed to create logs directory: {err!s}")
        sys.exit(-1)

    if engine_settings.no_tokens_in_logs:
        logger.no_tokens_in_logs()

    trace_database_thread = None
    if engine_settings.use_trace_database:
        print(f"{formatting.timestamp()}: Initializing: Trace database.")
        trace_database_dir_path = \
            Settings().trace_db_root_dir if Settings().trace_db_root_dir is not None else logger.EXPERIMENT_DIR
        trace_database_thread = trace_db.TraceDatabaseThread(trace_db.set_up_trace_database(trace_database_dir_path))
        trace_database_thread.name = 'Trace Database'
        trace_database_thread.daemon = True
        trace_database_thread.start()

    THREAD_JOIN_WAIT_TIME_SECONDS = 1

    # Validate replay mode options
    if replay_log:
        replay_valid_extensions = [".replay.txt", ".ndjson"]
        if not replay_log.endswith(tuple(replay_valid_extensions)):
            print(f"The replay log must be a RESTler-generated .replay.txt file or a trace database. \
                    The valid extensions are: {replay_valid_extensions}.")
            sys.exit(-1)

    # Legacy replay mode - replay.txt format
    # The new replay mode is integrated into the main algorithm
    if replay_log and replay_log.endswith(".replay.txt"):
        try:
            logger.create_network_log(logger.LOG_TYPE_REPLAY)
            driver.replay_sequence_from_log(replay_log, engine_settings.token_refresh_cmd)
            print("Done playing sequence from log")

            # Finish writing to trace database.
            if trace_database_thread:
                print(f"{formatting.timestamp()}: Finishing writing to Trace Database. "
                      f"Waiting for max {engine_settings.trace_db_cleanup_time} seconds. ")
                trace_database_thread.finish(engine_settings.trace_db_cleanup_time)
                # Wait for Trace DB logging to complete
                # Loop in order to enable the signal handler to run,
                # otherwise CTRL-C does not work.
                while trace_database_thread.is_alive():
                    trace_database_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

            sys.exit(0)
        except NoTokenSpecifiedException:
            logger.write_to_main(
                "Failed to play sequence from log:\n"
                "A valid authorization token was expected.\n"
                "Retry with a token refresh script in the settings file or "
                "update the request in the replay log with a valid authorization token.",
                print_to_console=LogSetting().restler
            )
            sys.exit(-1)
        except Exception as error:
            print(f"Failed to play sequence from log:\n{error!s}")
            sys.exit(-1)
    request_collection = None
    # Import grammar from a restler_grammar file
    if config_arg.restler_grammar:
        try:
            request_collection = import_grammar(config_arg.restler_grammar)
            request_collection.set_grammar_name(config_arg.restler_grammar)
        except Exception as error:
            print(f"Cannot import grammar: {error!s}")
            sys.exit(-1)

    # Create the request collection singleton
    requests.GlobalRequestCollection(request_collection)
    logger.write_to_main(f"req_collection={request_collection.request_id_collection}", LogSetting().restler)
    # Override default candidate values with custom mutations
    custom_mutations_dict_paths = engine_settings.get_endpoint_custom_mutations_paths()
    custom_generators_dict_paths = engine_settings.get_endpoint_custom_generators_paths()
    logger.write_to_main(f"custom_mutations_paths={custom_mutations_dict_paths}", LogSetting().restler)
    per_endpoint_custom_mutations = {}
    if custom_mutations_dict_paths:
        for endpoint in custom_mutations_dict_paths:
            try:
                if os.path.isabs(custom_mutations_dict_paths[endpoint]):
                    path = custom_mutations_dict_paths[endpoint]
                else:
                    # If custom dictionary path is not an absolute path, make it relative to the grammar
                    path = os.path.join(engine_file_dir, custom_mutations_dict_paths[endpoint])
                with open(path, 'r', encoding='utf-8') as mutations:
                    per_endpoint_custom_mutations[endpoint] = json.load(mutations)
            except Exception as error:
                print(f"Cannot import custom mutations: {error!s}")
                sys.exit(-1)
    try:
        if engine_settings.custom_value_generators_file_path:
            if os.path.exists(engine_settings.custom_value_generators_file_path):
                request_collection.set_custom_mutations(custom_mutations_dict, per_endpoint_custom_mutations,
                                                        engine_settings.custom_value_generators_file_path,
                                                        custom_generators_dict_paths)
            elif os.path.exists(os.path.join(engine_file_dir, engine_settings.custom_value_generators_file_path)):
                request_collection.set_custom_mutations(custom_mutations_dict, per_endpoint_custom_mutations,
                                                        os.path.join(engine_file_dir,
                                                                     engine_settings.custom_value_generators_file_path),
                                                        custom_generators_dict_paths)
            else:
                request_collection.set_custom_mutations(custom_mutations_dict, per_endpoint_custom_mutations,
                                                        os.path.join(os.path.dirname(__file__),
                                                                     engine_settings.custom_value_generators_file_path),
                                                        custom_generators_dict_paths)

    except UnsupportedPrimitiveException as primitive:
        logger.write_to_main("Error in mutations dictionary.\n"
                             f"Unsupported primitive type defined: {primitive!s}",
                             print_to_console=LogSetting().restler)
        sys.exit(-1)
    except InvalidDictPrimitiveException as err:
        logger.write_to_main("Error in mutations dictionary.\n"
                             "Dict type primitive was specified as another type.\n"
                             f"{err!s}",
                             print_to_console=LogSetting().restler)
        sys.exit(-1)
    """
    token_auth_method = settings.token_authentication_method
    restler_refreshable_authentication_token = {
        "token_auth_method": token_auth_method,
        "token_refresh_interval": settings.token_refresh_interval,
    }
    if token_auth_method == TokenAuthMethod.CMD:
        restler_refreshable_authentication_token.update({
            "token_refresh_cmd": settings.token_refresh_cmd,
        })
    elif token_auth_method == TokenAuthMethod.MODULE:
        restler_refreshable_authentication_token.update({
            "token_module_file": settings.token_module_file,
            "token_module_function": settings.token_module_function,
            "token_module_data": settings.token_module_data,
        })
    elif token_auth_method == TokenAuthMethod.LOCATION:
        restler_refreshable_authentication_token.update({
            "token_location": settings.token_location,
        })
    
    req_collection.candidate_values_pool.set_candidate_values(
        {
            'restler_refreshable_authentication_token': restler_refreshable_authentication_token
        }
    )
    """
    # Write the random seed to main in case the run exits in the middle and needs to be
    # restarted with the same seed
    logger.write_to_main(f"Random seed: {Settings().random_seed}", True)

    # Initialize the fuzzing monitor
    fuzz_monitor = fuzzing_monitor.FuzzingMonitor()

    # pass some user argument internally to request_set
    fuzz_monitor.set_time_budget(engine_settings.time_budget)
    fuzz_monitor.renderings_monitor.set_memoize_invalid_past_renderings_on()

    if engine_settings.host:
        try:
            request_collection.update_hosts()
        except requests.InvalidGrammarException:
            sys.exit(-1)
    else:
        host = request_collection.get_host_from_grammar()
        if host is not None:
            hostname, port = driver.get_host_and_port(host)

            if engine_settings.connection_settings.target_port is None and port is not None:
                engine_settings.set_port(port)
            engine_settings.set_hostname(hostname)
        else:
            logger.write_to_main(
                "Host not found in grammar. "
                "Add the host to your spec or launch RESTler with --host parameter.",
                print_to_console=True
            )
            sys.exit(-1)

    try:
        request_collection.update_basepaths()
    except requests.InvalidGrammarException:
        sys.exit(-1)

    # Filter and get the requests to be used for fuzzing
    fuzzing_requests = preprocessing.create_fuzzing_req_collection(local_user_args.get('path_regex', None))
    for item in fuzzing_requests:
        logger.write_to_main(f"item={item.endpoint_no_dynamic_objects}", True)
    logger.write_to_main("fuzz_request.size={}".format(fuzzing_requests.size), True)
    logger.write_to_main("req_collection={}".format(request_collection), True)
    # Initialize bug buckets
    bug_bucketing.BugBuckets()

    # Set the spec coverage singleton
    logger.SpecCoverageLog()

    # If both lists were set, parse the command-line to find the order
    if config_arg.enable_checkers and config_arg.disable_checkers:
        set_enable_first = sys.argv.index('--enable_checkers') < sys.argv.index('--disable_checkers')
    else:
        set_enable_first = config_arg.enable_checkers is not None

    user_checkers = get_checker_list(request_collection, fuzzing_requests, config_arg.enable_checkers or [],
                                     config_arg.disable_checkers or [], set_enable_first,
                                     engine_settings.custom_checkers)

    # Initialize request count for each checker
    for checker in user_checkers:
        if checker.enabled:
            fuzz_monitor.status_codes_monitor._requests_count[checker.__class__.__name__] = 0
    try:
        destructors = preprocessing.apply_create_once_resources(fuzzing_requests)
    except preprocessing.CreateOnceFailure as failobj:
        logger.write_to_main(
            failobj.msg,
            print_to_console=True
        )
        postprocessing.delete_create_once_resources(failobj.destructors, fuzzing_requests)
        raise failobj
    except InvalidDictionaryException as ex:
        print(f"Failed preprocessing:\n\t"
              "An error was identified in the dictionary.")
        raise ex
    except Exception as error:
        print(f"Failed preprocessing:\n\t{error!s}")
        raise error

    grammar_path = engine_settings.grammar_schema
    if os.path.exists(grammar_path):
        try:
            with open(grammar_path, 'r', encoding="utf-8") as grammar:
                schema_json = json.load(grammar)
        except Exception as err:
            print(f"Failed to process grammar file: {grammar_path}; {err!s}")
            sys.exit(-1)

        if not preprocessing.parse_grammar_schema(schema_json):
            sys.exit(-1)
    else:
        print(f"Grammar schema file '{grammar_path}' does not exist.")

    # Set up garbage collection
    gc_thread = None
    garbage_collector = None

    if Settings().garbage_collection_interval or Settings().run_gc_after_every_sequence:
        garbage_collector = dependencies.GarbageCollector(request_collection, fuzz_monitor)
        gc_message = "after every test sequence. " \
            if Settings().run_gc_after_every_sequence else f"every {engine_settings.garbage_collection_interval} seconds."
        print(f"{formatting.timestamp()}: Initializing: Garbage collection {gc_message}")
        logger.write_to_main(f"{formatting.timestamp()}: Initializing: Garbage collection {gc_message}",
                             LogSetting().restler)
        gc_thread = dependencies.GarbageCollectorThread(garbage_collector, engine_settings.garbage_collection_interval)
        gc_thread.name = 'Garbage Collector'
        gc_thread.daemon = True
        gc_thread.start()

    # Start fuzzing
    fuzz_thread = fuzzer.FuzzingThread(fuzzing_requests, user_checkers, Settings().fuzzing_jobs, garbage_collector)
    fuzz_thread.name = 'Fuzzer'
    fuzz_thread.daemon = True
    fuzz_thread.start()

    # Wait for the fuzzing job to end before continuing.
    # Looping in case the gc_thread terminates prematurely.
    # We don't want to keep fuzzing if GC stopped working
    num_total_sequences = 0
    while fuzz_thread.is_alive():
        if gc_thread and not gc_thread.is_alive():
            print(f"{formatting.timestamp()}: Garbage collector thread has terminated prematurely")
            logger.write_to_main(f"{formatting.timestamp()}: Garbage collector thread has terminated prematurely",
                                 LogSetting().restler)
            # Terminate the fuzzing thread
            fuzz_monitor.terminate_fuzzing()
        num_total_sequences = fuzz_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    try:
        # Attempt to delete the create_once resources.
        # Note: This is done in addition to attempting to use the garbage collector.
        #   The garbage collector can handle cleaning up resources with destructors
        #   that were not excluded from fuzzing. This post-processing event can clean
        #   up those resources that were excluded. This happens when a create_once
        #   resource was the parent resource in a request.
        postprocessing.delete_create_once_resources(destructors, fuzzing_requests)
    except Exception as error:
        print("Exception occurred in delete create_once_resources: {}".
              format(str(error)))

    # If garbage collection is on, deallocate everything possible.
    if gc_thread:
        print(f"{formatting.timestamp()}: Terminating garbage collection. "
              f"Waiting for max {engine_settings.garbage_collector_cleanup_time} seconds. ")

        gc_thread.finish(engine_settings.garbage_collector_cleanup_time)
        # Wait for GC to complete
        # Loop in order to enable the signal handler to run,
        # otherwise CTRL-C does not work.
        while gc_thread.is_alive():
            gc_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    # Finish writing to trace database.
    if trace_database_thread:
        print(f"{formatting.timestamp()}: Finishing writing to Trace Database. "
              f"Waiting for max {engine_settings.trace_db_cleanup_time} seconds. ")
        trace_database_thread.finish(engine_settings.trace_db_cleanup_time)
        # Wait for Trace DB logging to complete
        # Loop in order to enable the signal handler to run,
        # otherwise CTRL-C does not work.
        while trace_database_thread.is_alive():
            trace_database_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    # Print the end of the run generation stats
    logger.print_generation_stats(request_collection, fuzz_monitor, None, final=True)
    if Settings().garbage_collection_interval or Settings().run_gc_after_every_sequence:
        # Print the garbage collection stats
        logger.print_gc_summary(garbage_collector)

    if fuzz_thread.exception is not None:
        print(fuzz_thread.exception)
        sys.exit(-1)

    RestlerSettings.TEST_DeleteInstance()
    print("Done.")


def execute_from_command_line():
    try:
        log_file = json.load(open(os.path.join(os.path.dirname(__file__), "log_settings.json")))
        LogSetting().init_from_json(log_file)
        print(LogSetting().restler_settings)
    except Exception as error:
        print(f"Error: Failed to load log settings file: {error!s}")
        sys.exit(-1)

    # the following intercepts Ctrl+C (tested on Windows only! but should work on Linux)
    # the next line works in powershell (but not in bash on Windows!)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--max_sequence_length',
                        help='Max number of requests in a sequence'
                             f' (default: {restler_settings.MAX_SEQUENCE_LENGTH_DEFAULT})',
                        type=int, default=restler_settings.MAX_SEQUENCE_LENGTH_DEFAULT, required=False)
    parser.add_argument('--fuzzing_jobs',
                        help='Number of fuzzing jobs to run in parallel'
                             ' (default: 1)',
                        type=int, default=1, required=False)
    parser.add_argument('--target_ip', help='Target IP',
                        type=str, default=None, required=False)
    parser.add_argument('--target_port', help='Target Port',
                        type=int, default=None, required=False)
    parser.add_argument('--time_budget', help='Stops fuzzing after given time'
                                              ' in hours (default: one month)',
                        type=float, default=restler_settings.TIME_BUDGET_DEFAULT, required=False)
    parser.add_argument('--max_request_execution_time',
                        help='The time interval in seconds to wait for a request to complete,'
                             'after which a timeout should be reported as a bug. '
                             f' (default: {restler_settings.MAX_REQUEST_EXECUTION_TIME_DEFAULT} seconds,'
                             f' maximum: {restler_settings.MAX_REQUEST_EXECUTION_TIME_MAX}) seconds.',
                        type=float, default=restler_settings.MAX_REQUEST_EXECUTION_TIME_DEFAULT, required=False)
    parser.add_argument('--fuzzing_mode',
                        help='Fuzzing mode.'
                             ' One of bfs/bfs-fast/bfs-cheap/bfs-minimal/random-walk/'
                             f'directed-smoke-test (default: {restler_settings.FUZZING_MODE_DEFAULT})',
                        type=str, default=restler_settings.FUZZING_MODE_DEFAULT, required=False)
    parser.add_argument('--ignore_feedback',
                        help='Ignore server-side feedback (default: False)',
                        type=bool, default=False, required=False)
    parser.add_argument('--ignore_dependencies',
                        help='Ignore request dependencies (default: False)',
                        type=bool, default=False, required=False)
    parser.add_argument('--garbage_collection_interval',
                        help='Perform async. garbage collection of dynamic '
                             'objects (Default: off).',
                        type=int, required=False)
    parser.add_argument('--dyn_objects_cache_size',
                        help='Max number of objects of one type before deletion by the garbage collector '
                             f'(default: {restler_settings.DYN_OBJECTS_CACHE_SIZE_DEFAULT}).',
                        type=int, default=restler_settings.DYN_OBJECTS_CACHE_SIZE_DEFAULT, required=False)
    parser.add_argument('--restler_grammar',
                        help='RESTler grammar definition. Overrides parsing of'
                             ' swagger specification',
                        type=str, default='', required=False)
    parser.add_argument('--custom_mutations',
                        help='Custom pool of primitive type values. Note that'
                             ' custom mutations will be erased in case'
                             ' checkpoint files exist',
                        type=str, default='', required=False)
    parser.add_argument('--settings',
                        help='Custom user settings file path',
                        type=str, default='', required=False)
    parser.add_argument('--path_regex',
                        help='Limit restler grammars only to endpoints whose'
                             'paths contains a given substing',
                        type=str, default=None, required=False)
    parser.add_argument('--token_refresh_interval',
                        help='Interval to periodically refreshes token (in seconds)'
                             ' (default: None)',
                        type=int, default=None, required=False)
    parser.add_argument('--token_refresh_cmd',
                        help='The cmd to execute in order to refresh the authentication token'
                             ' (default: None)',
                        type=str, default=None, required=False)
    parser.add_argument('--client_certificate_path',
                        help='Path to your X.509 certificate in PEM format. Provide for Certificate Based Authentication'
                             ' (default: None)',
                        type=str, default=None, required=False)
    parser.add_argument('--producer_timing_delay',
                        help='The time interval to wait after a resource-generating '
                             'producer is executed (in seconds)'
                             ' (default: 0 -- no delay)',
                        type=int, default=0, required=False)
    parser.add_argument('--no_tokens_in_logs',
                        help='Do not print auth token data in logs (default: False)',
                        type=bool, default=False, required=False)
    parser.add_argument('--save_results_in_fixed_dirname',
                        help='Save results in a directory with a fixed name (default: False)',
                        type=bool, default=False, required=False)
    parser.add_argument('--host',
                        help='Set to override Host in the grammar (default: do not override)',
                        type=str, default=None, required=False)
    parser.add_argument('--no_ssl',
                        help='Set this flag if you do not want to use SSL validation for the socket',
                        action='store_true')
    parser.add_argument('--include_user_agent',
                        help='Set this flag if you would like to add User-Agent to the request headers',
                        action='store_true')
    parser.add_argument('--enable_checkers',
                        help='Follow with a list of checkers to force those checkers to be enabled',
                        type=str, nargs='+', required=False)
    parser.add_argument('--disable_checkers',
                        help='Follow with a list of checkers to force those checkers to be disabled',
                        type=str, nargs='+', required=False)
    parser.add_argument('--replay_log',
                        help='A log containing a sequence of requests to send to the server',
                        type=str, default=None, required=False)
    parser.add_argument('--use_test_socket',
                        help='Set to use the test socket',
                        action='store_true')
    parser.add_argument('--test_server',
                        help='Set the test server to run',
                        type=str, default=restler_settings.DEFAULT_TEST_SERVER_ID, required=False)
    parser.add_argument('--set_version',
                        help="Sets restler's version",
                        type=str, default=None, required=False)

    args = parser.parse_args()

    settings_file = None
    settings_file_content = None
    engine_file_dir = None
    if bool(args.settings):
        try:
            settings_file = os.path.join(os.path.dirname(__file__), args.settings)
            print(settings_file)
            settings_file_content = json.load(open(settings_file))
            engine_file_dir = os.path.dirname(__file__)
        except Exception as error:
            print(f"Error: Failed to load settings file: {error!s}")
            sys.exit(-1)

    # convert the command-line arguments to a dict
    user_args = vars(args)
    # combine settings from settings file to the command-line arguments
    if settings_file:
        user_args.update(settings_file_content)
        user_args['settings_file_exists'] = True

    if args.restler_grammar:
        # Set grammar schema to the same path as the restler grammar, but as json
        args.grammar_schema = '.json'.join(args.restler_grammar.rsplit('.py', 1))

    try:
        # Set the restler settings singleton
        settings = restler_settings.RestlerSettings(user_args, engine_file_dir)
    except restler_settings.InvalidValueError as error:
        print(f"\nArgument Error::\n\t{error!s}")
        sys.exit(-1)
    except Exception as error:
        print(f"\nFailed to parse user settings file: {error!s}")
        sys.exit(-1)

    try:
        settings.validate_options()
    except restler_settings.OptionValidationError as error:
        print(f"\nArgument Error::\n\t{error!s}")
        sys.exit(-1)

    # Options Validation
    custom_mutations = {}
    # Replay may be performed with or without the grammar file.
    if not args.replay_log:
        if not args.restler_grammar:
            print("\nArgument Error::\n\tNo restler grammar was provided.\n")
            sys.exit(-1)

    if settings.fuzzing_mode not in ['bfs', 'bfs-cheap'] and args.fuzzing_jobs > 1:
        print("\nArgument Error::\n\tOnly bfs supports multiple fuzzing jobs\n")
        sys.exit(-1)

    if args.custom_mutations:
        print(args.custom_mutations)
        try:
            custom_mutations = json.load(open(args.custom_mutations, encoding='utf-8'))
        except Exception as error:
            print(f"Cannot import custom mutations: {error!s}")
            sys.exit(-1)

        if settings.custom_value_generators_file_path:
            if not settings.custom_value_generators_file_path.endswith(".py"):
                print(f"Custom value generators must be provided in a Python file.")
                sys.exit(-1)

            if not os.path.exists(settings.custom_value_generators_file_path):
                print(f"Invalid custom value generators file specified: {settings.custom_value_generators_file_path}")
                sys.exit(-1)

    if settings.save_results_in_fixed_dirname:
        logger.save_results_in_fixed_dirname()

    # Create the directory where all the results will be saved
    try:
        logger.create_experiment_dir(os.getcwd())
    except Exception as err:
        print(f"Failed to create logs directory: {err!s}")
        sys.exit(-1)

    if settings.no_tokens_in_logs:
        logger.no_tokens_in_logs()

    trace_db_thread = None
    if settings.use_trace_database:
        print(f"{formatting.timestamp()}: Initializing: Trace database.")
        trace_database_dir_path = \
            Settings().trace_db_root_dir if Settings().trace_db_root_dir is not None else logger.EXPERIMENT_DIR
        trace_db_thread = trace_db.TraceDatabaseThread(trace_db.set_up_trace_database(trace_database_dir_path))
        trace_db_thread.name = 'Trace Database'
        trace_db_thread.daemon = True
        trace_db_thread.start()

    THREAD_JOIN_WAIT_TIME_SECONDS = 1

    # Validate replay mode options
    if args.replay_log:
        valid_extensions = [".replay.txt", ".ndjson"]
        if not args.replay_log.endswith(tuple(valid_extensions)):
            print(f"The replay log must be a RESTler-generated .replay.txt file or a trace database. \
                    The valid extensions are: {valid_extensions}.")
            sys.exit(-1)

    # Legacy replay mode - replay.txt format
    # The new replay mode is integrated into the main algorithm
    if args.replay_log and args.replay_log.endswith(".replay.txt"):
        try:
            logger.create_network_log(logger.LOG_TYPE_REPLAY)
            driver.replay_sequence_from_log(args.replay_log, settings.token_refresh_cmd)
            print("Done playing sequence from log")

            # Finish writing to trace database.
            if trace_db_thread:
                print(f"{formatting.timestamp()}: Finishing writing to Trace Database. "
                      f"Waiting for max {settings.trace_db_cleanup_time} seconds. ")
                trace_db_thread.finish(settings.trace_db_cleanup_time)
                # Wait for Trace DB logging to complete
                # Loop in order to enable the signal handler to run,
                # otherwise CTRL-C does not work.
                while trace_db_thread.is_alive():
                    trace_db_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

            sys.exit(0)
        except NoTokenSpecifiedException:
            logger.write_to_main(
                "Failed to play sequence from log:\n"
                "A valid authorization token was expected.\n"
                "Retry with a token refresh script in the settings file or "
                "update the request in the replay log with a valid authorization token.",
                print_to_console=LogSetting().restler
            )
            sys.exit(-1)
        except Exception as error:
            print(f"Failed to play sequence from log:\n{error!s}")
            sys.exit(-1)
    req_collection = None
    # Import grammar from a restler_grammar file
    if args.restler_grammar:
        try:
            req_collection = import_grammar(args.restler_grammar)
            req_collection.set_grammar_name(args.restler_grammar)
        except Exception as error:
            print(f"Cannot import grammar: {error!s}")
            sys.exit(-1)

    # Create the request collection singleton
    requests.GlobalRequestCollection(req_collection)
    logger.write_to_main(f"req_collection={req_collection.request_id_collection}", LogSetting().restler)
    # Override default candidate values with custom mutations
    custom_mutations_paths = settings.get_endpoint_custom_mutations_paths()
    logger.write_to_main(f"custom_mutations_paths={custom_mutations_paths}", LogSetting().restler)
    per_endpoint_custom_mutations = {}
    if custom_mutations_paths:
        for endpoint in custom_mutations_paths:
            try:
                if os.path.isabs(custom_mutations_paths[endpoint]):
                    path = custom_mutations_paths[endpoint]
                else:
                    # If custom dictionary path is not an absolute path, make it relative to the grammar
                    path = os.path.join(os.path.dirname(args.restler_grammar), custom_mutations_paths[endpoint])
                with open(path, 'r', encoding='utf-8') as mutations:
                    per_endpoint_custom_mutations[endpoint] = json.load(mutations)
            except Exception as error:
                print(f"Cannot import custom mutations: {error!s}")
                sys.exit(-1)
    try:
        req_collection.set_custom_mutations(custom_mutations, per_endpoint_custom_mutations,
                                            settings.custom_value_generators_file_path, None)
    except UnsupportedPrimitiveException as primitive:
        logger.write_to_main("Error in mutations dictionary.\n"
                             f"Unsupported primitive type defined: {primitive!s}",
                             print_to_console=LogSetting().restler)
        sys.exit(-1)
    except InvalidDictPrimitiveException as err:
        logger.write_to_main("Error in mutations dictionary.\n"
                             "Dict type primitive was specified as another type.\n"
                             f"{err!s}",
                             print_to_console=LogSetting().restler)
        sys.exit(-1)
    """"
    token_auth_method = settings.token_authentication_method
    restler_refreshable_authentication_token = {
        "token_auth_method": token_auth_method,
        "token_refresh_interval": settings.token_refresh_interval,
    }
    if token_auth_method == TokenAuthMethod.CMD:
        restler_refreshable_authentication_token.update({
            "token_refresh_cmd": settings.token_refresh_cmd,
        })
    elif token_auth_method == TokenAuthMethod.MODULE:
        restler_refreshable_authentication_token.update({
            "token_module_file": settings.token_module_file,
            "token_module_function": settings.token_module_function,
            "token_module_data": settings.token_module_data,
        })
    elif token_auth_method == TokenAuthMethod.LOCATION:
        restler_refreshable_authentication_token.update({
            "token_location": settings.token_location,
        })

    req_collection.candidate_values_pool.set_candidate_values(
        {
            'restler_refreshable_authentication_token': restler_refreshable_authentication_token
        }
    )
    """
    # Write the random seed to main in case the run exits in the middle and needs to be
    # restarted with the same seed
    logger.write_to_main(f"Random seed: {Settings().random_seed}", LogSetting().restler)

    # Initialize the fuzzing monitor
    monitor = fuzzing_monitor.FuzzingMonitor()

    # pass some user argument internally to request_set
    monitor.set_time_budget(settings.time_budget)
    monitor.renderings_monitor.set_memoize_invalid_past_renderings_on()

    if settings.host:
        try:
            req_collection.update_hosts()
        except requests.InvalidGrammarException:
            sys.exit(-1)
    else:
        host = req_collection.get_host_from_grammar()
        if host is not None:
            hostname, port = driver.get_host_and_port(host)

            if settings.connection_settings.target_port is None and port is not None:
                settings.set_port(port)
            settings.set_hostname(hostname)
        else:
            logger.write_to_main(
                "Host not found in grammar. "
                "Add the host to your spec or launch RESTler with --host parameter.",
                print_to_console=True
            )
            sys.exit(-1)

    try:
        req_collection.update_basepaths()
    except requests.InvalidGrammarException:
        sys.exit(-1)

    # Filter and get the requests to be used for fuzzing
    fuzzing_requests = preprocessing.create_fuzzing_req_collection(args.path_regex)
    logger.write_to_main("fuzz_request.size={}".format(fuzzing_requests.size), LogSetting().restler)
    logger.write_to_main("req_collection={}".format(req_collection), LogSetting().restler)
    # Initialize bug buckets
    bug_bucketing.BugBuckets()

    # Set the spec coverage singleton
    logger.SpecCoverageLog()

    # If both lists were set, parse the command-line to find the order
    if args.enable_checkers and args.disable_checkers:
        set_enable_first = sys.argv.index('--enable_checkers') < sys.argv.index('--disable_checkers')
    else:
        set_enable_first = args.enable_checkers is not None

    checkers = get_checker_list(req_collection, fuzzing_requests, args.enable_checkers or [],
                                args.disable_checkers or [], set_enable_first, settings.custom_checkers)

    # Initialize request count for each checker
    for checker in checkers:
        if checker.enabled:
            monitor.status_codes_monitor._requests_count[checker.__class__.__name__] = 0
    try:
        destructors = preprocessing.apply_create_once_resources(fuzzing_requests)
    except preprocessing.CreateOnceFailure as failobj:
        logger.write_to_main(
            failobj.msg,
            print_to_console=True
        )
        postprocessing.delete_create_once_resources(failobj.destructors, fuzzing_requests)
        raise failobj
    except InvalidDictionaryException as ex:
        print(f"Failed preprocessing:\n\t"
              "An error was identified in the dictionary.")
        raise ex
    except Exception as error:
        print(f"Failed preprocessing:\n\t{error!s}")
        raise error

    grammar_path = settings.grammar_schema
    if os.path.exists(grammar_path):
        try:
            with open(grammar_path, 'r') as grammar:
                schema_json = json.load(grammar)
        except Exception as err:
            print(f"Failed to process grammar file: {grammar_path}; {err!s}")
            sys.exit(-1)

        if not preprocessing.parse_grammar_schema(schema_json):
            sys.exit(-1)
    else:
        print(f"Grammar schema file '{grammar_path}' does not exist.")

    # Set up garbage collection
    gc_thread = None
    garbage_collector = None

    if args.garbage_collection_interval or Settings().run_gc_after_every_sequence:
        garbage_collector = dependencies.GarbageCollector(req_collection, monitor)
        gc_message = "after every test sequence. " \
            if Settings().run_gc_after_every_sequence else f"every {settings.garbage_collection_interval} seconds."
        print(f"{formatting.timestamp()}: Initializing: Garbage collection {gc_message}")
        logger.write_to_main(f"{formatting.timestamp()}: Initializing: Garbage collection {gc_message}",
                             LogSetting().restler)
        gc_thread = dependencies.GarbageCollectorThread(garbage_collector, settings.garbage_collection_interval)
        gc_thread.name = 'Garbage Collector'
        gc_thread.daemon = True
        gc_thread.start()

    # Start fuzzing
    fuzz_thread = fuzzer.FuzzingThread(fuzzing_requests, checkers, args.fuzzing_jobs, garbage_collector)
    fuzz_thread.name = 'Fuzzer'
    fuzz_thread.daemon = True
    fuzz_thread.start()

    # Wait for the fuzzing job to end before continuing.
    # Looping in case the gc_thread terminates prematurely.
    # We don't want to keep fuzzing if GC stopped working
    num_total_sequences = 0
    while fuzz_thread.is_alive():
        if gc_thread and not gc_thread.is_alive():
            print(f"{formatting.timestamp()}: Garbage collector thread has terminated prematurely")
            logger.write_to_main(f"{formatting.timestamp()}: Garbage collector thread has terminated prematurely",
                                 LogSetting().restler)
            # Terminate the fuzzing thread
            monitor.terminate_fuzzing()
        num_total_sequences = fuzz_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    try:
        # Attempt to delete the create_once resources.
        # Note: This is done in addition to attempting to use the garbage collector.
        #   The garbage collector can handle cleaning up resources with destructors
        #   that were not excluded from fuzzing. This post-processing event can clean
        #   up those resources that were excluded. This happens when a create_once
        #   resource was the parent resource in a request.
        postprocessing.delete_create_once_resources(destructors, fuzzing_requests)
    except Exception as error:
        print("Exception occurred in delete create_once_resources: {}".
              format(str(error)))

    # If garbage collection is on, deallocate everything possible.
    if gc_thread:
        print(f"{formatting.timestamp()}: Terminating garbage collection. "
              f"Waiting for max {settings.garbage_collector_cleanup_time} seconds. ")

        gc_thread.finish(settings.garbage_collector_cleanup_time)
        # Wait for GC to complete
        # Loop in order to enable the signal handler to run,
        # otherwise CTRL-C does not work.
        while gc_thread.is_alive():
            gc_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    # Finish writing to trace database.
    if trace_db_thread:
        print(f"{formatting.timestamp()}: Finishing writing to Trace Database. "
              f"Waiting for max {settings.trace_db_cleanup_time} seconds. ")
        trace_db_thread.finish(settings.trace_db_cleanup_time)
        # Wait for Trace DB logging to complete
        # Loop in order to enable the signal handler to run,
        # otherwise CTRL-C does not work.
        while trace_db_thread.is_alive():
            trace_db_thread.join(THREAD_JOIN_WAIT_TIME_SECONDS)

    # Print the end of the run generation stats
    logger.print_generation_stats(req_collection, monitor, None, final=True)

    # Print the garbage collection stats
    logger.print_gc_summary(garbage_collector)

    if fuzz_thread.exception is not None:
        print(fuzz_thread.exception)
        sys.exit(-1)

    RestlerSettings.TEST_DeleteInstance()
    print("Done.")


if __name__ == '__main__':
    DEBUGG_MODE = True
    if DEBUGG_MODE:
        grammar_folder = os.path.join(os.getcwd(), "grammar")
        params = ExecuteParam(settings=os.path.join(os.getcwd(), "restler_user_settings.json"),
                              restler_grammar=os.path.join(grammar_folder, "grammar.py"),
                              enable_checkers=[],
                              disable_checkers=[],
                              working_dir=grammar_folder)
        execute_restler(config_arg=params)

    else:
        execute_from_command_line()
