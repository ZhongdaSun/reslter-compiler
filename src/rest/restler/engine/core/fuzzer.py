# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import threading

import rest.restler.engine.core.driver as driver
import rest.restler.utils.restler_logger as logger
import traceback

from rest.restler.engine.core.fuzzing_monitor import Monitor
from rest.restler.engine.core.requests import GrammarRequestCollection
from rest.restler.engine.errors import InvalidDictionaryException
from rest.restler.restler_settings import LogSettings


class FuzzingThread(threading.Thread):
    """ Fuzzer thread class
    """

    def __init__(self, fuzzing_requests, checkers, fuzzing_jobs=1, garbage_collector=None):
        """ Constructor for the Fuzzer thread class

        @param fuzzing_requests: The collection of requests to fuzz
        @type  fuzzing_requests: FuzzingRequestCollection
        @param checkers: List of checker objects
        @type  checkers: List[Checker]

        """
        threading.Thread.__init__(self)

        self._fuzzing_requests = fuzzing_requests
        self._checkers = checkers
        self._fuzzing_jobs = fuzzing_jobs
        self._garbage_collector = garbage_collector
        self._num_total_sequences = 0
        self._exception = None

    @property
    def exception(self):
        return self._exception

    def run(self):
        """ Thread entrance - performs fuzzing
        """
        try:
            logger.write_to_main(f"self._checkers={self._checkers}", LogSettings().fuzzer)
            self._num_total_sequences = driver.generate_sequences(
                self._fuzzing_requests, self._checkers, self._fuzzing_jobs,
                self._garbage_collector
            )

            # At the end of everything print out any request that were never
            # rendered (because they never had valid constraints).
            logger.print_request_rendering_stats_never_rendered_requests(
                self._fuzzing_requests,
                GrammarRequestCollection().candidate_values_pool,
                Monitor()
            )
        except InvalidDictionaryException:
            pass
        except Exception as err:
            self._exception = traceback.format_exc()
        logger.write_to_main("exit....")

    def join(self, *args):
        """ Overrides thread join function

        @return: The total number of sequences from the fuzzing run
        @rtype : Int

        """
        threading.Thread.join(self, *args)
        return self._num_total_sequences
