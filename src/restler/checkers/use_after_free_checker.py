# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

""" Implements logic for use after free checker. """
from __future__ import print_function

from restler.checkers.checker_base import *

import copy

import restler.engine.dependencies as dependencies
import restler.engine.core.sequences as sequences
from restler.engine.core.fuzzing_monitor import Monitor

from restler.engine.bug_bucketing import BugBuckets
from restler.utils.restler_logger import raw_network_logging as RAW_LOGGING


class UseAfterFreeChecker(CheckerBase):
    """ Checker for use after free violations. """
    def __init__(self, req_collection, fuzzing_requests):
        CheckerBase.__init__(self, req_collection, fuzzing_requests)

    def apply(self, rendered_sequence, lock):
        """ Applies check for resource leakage rule violations.

        @param rendered_sequence: Object containing the rendered sequence information
        @type  rendered_sequence: RenderedSequence
        @param lock: Lock object used to sync more than one fuzzing job
        @type  lock: thread.Lock

        @return: None
        @rtype : None

        """
        if not rendered_sequence.valid:
            return
        self._sequence = rendered_sequence.sequence

        self._lock = lock
        logger.write_to_main(f"rendered_sequence={rendered_sequence}", True)
        # Operate only on sequences that end with delete that is a proper
        # consumer (I don't know how can a delete not be a consumer of something,
        # but I will be checking just in case...)
        if not self._sequence.last_request.is_destructor():
            return
        current_destructor = self._sequence.last_request

        # Note that set of types consumed by the destructor define a hierarchy
        # (not just one type) and we must try to use an object of the exact
        # hierarchy so that we decrease false positives.
        destructed_types = current_destructor.consumes
        if not destructed_types:
            return

        # Log some helpful info
        self._checker_log.checker_print(f"\nTarget types: {destructed_types}")
        self._checker_log.checker_print(f"Clean dependencies: {dependencies.tlb}")

        # Try using the deleted objects.
        self._use_after_free(destructed_types)

    def _use_after_free(self, destructed_types):
        """ Tries to access deleted dynamic object. Accessing means try to apply
        any request, defined in the request collection, that consumes an object
        with type @param type.

        @param destructed_types: Ordered set of the hierarchy of dynamic object
                                    types the current request will need in order
                                    to destruct (probably) an object of the last
                                    object type.
        @type  destructed_types: Set

        @return: None
        @rtype : None

        """
        consumers = []
        destructor = self._sequence.last_request

        # Search for any consumer request, except for the current destructor
        # request, that consumes an hierarchy similar to the one deleted.
        for request in self._fuzzing_requests:
            if request.hex_definition == destructor.hex_definition:
                continue
            if request.consumes == destructed_types:
                consumers.append(copy.copy(request))

        self._checker_log.checker_print("Found * {} * consumers.".\
                            format(len(consumers)))

        # Try any consumer of the deleted types.
        for request in consumers:
            # Try accessing deleted objects.
            self._render_last_request(self._sequence + sequences.Sequence(request))
            # One consumer is OK -- to save us some time
            if self._mode != 'exhaustive':
                break

    def _render_last_request(self, seq):
        """ Render the last request of the sequence and inspect the status
        code of the response. If it's any of 20x, we have probably hit a bug.

        @param seq: The sequence whose last request we will try to render.
        @type  seq: Sequence Class object.

        @return: None
        @rtype : None

        """
        request = seq.last_request
        for rendered_data, parser,_,updated_writer_variables, replay_blocks in\
            request.render_iter(self._req_collection.candidate_values_pool,
                                skip=request._current_combination_id):
            # Hold the lock (because other workers may be rendering the same
            # request) and check whether the current rendering is known from the
            # past to lead to invalid status codes. If so, skip the current
            # rendering.
            if self._lock is not None:
                self._lock.acquire()
            should_skip = Monitor().is_invalid_rendering(request)
            if self._lock is not None:
                self._lock.release()

            # Skip the loop and don't forget to increase the counter.
            if should_skip:
                RAW_LOGGING("Skipping rendering: {}".\
                            format(request._current_combination_id))
                request._current_combination_id += 1
                continue

            rendered_data = seq.resolve_dependencies(rendered_data)

            response = self._send_request(parser, rendered_data)

            rendering_is_valid = response.has_valid_code()
            if rendering_is_valid:
                for name,v in updated_writer_variables.items():
                    dependencies.set_variable(name, v)

            # Append the rendered data to the sent list as we will not be rendering
            # with the sequence's render function
            seq.append_data_to_sent_list(request.method_endpoint_hex_definition,
                                         rendered_data, parser, response, replay_blocks=replay_blocks)
            if response and self._rule_violation(seq, response):
                self._print_suspect_sequence(seq, response)
                logger.write_to_main(f"{self.__class__.__name__}", True)
                BugBuckets.Instance().update_bug_buckets(seq, response.status_code, origin=self.__class__.__name__)

    def _false_alarm(self, seq, response):
        """ Catches use after free rule violation false alarms -
        specifically for GitLab merged branches

        @param seq: The sequence to check
        @type  seq: Sequence Class object.
        @param response: unused
        @type  response: Str

        @return: Whether rule is violated or not.
        @rtype : Bool

        """
        # Here is an example of code filtering for false alarms.
        # #try:
        #    # Handle gitlab merged branches type that cause false alarms
        #    for p in list(seq)[-2].definition:
        #        if p[1] == '/repository/merged_branches':
        #            return True
        #except Exception:
        #    pass

        # If we reach this point no violation has occured.
        return False
