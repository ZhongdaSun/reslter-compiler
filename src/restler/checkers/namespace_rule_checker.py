# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

""" Implements logic for user namespace violation checker. """
from __future__ import print_function

from restler.checkers.checker_base import *

import itertools

from restler.engine.bug_bucketing import BugBuckets
import restler.engine.dependencies as dependencies
import restler.engine.primitives as primitives
from restler.engine.core.request_utilities import NO_TOKEN_SPECIFIED
from restler.engine.core.request_utilities import NO_SHADOW_TOKEN_SPECIFIED

STATIC_OAUTH_TOKEN = 'static_oauth_token'


class NameSpaceRuleChecker(CheckerBase):
    """ Checker for Namespace rule violations. """

    def __init__(self, req_collection, fuzzing_requests):
        CheckerBase.__init__(self, req_collection, fuzzing_requests)

        def set_var(member_var, arg):
            """ helper for setting member variables from settings """
            val = Settings().get_checker_arg(self.friendly_name, arg)
            if val is not None:
                return val
            return member_var

        self._trigger_on_dynamic_objects = True
        self._trigger_on_dynamic_objects = set_var(self._trigger_on_dynamic_objects, 'trigger_on_dynamic_objects')

        self._trigger_objects = {}
        self._trigger_objects = set_var(self._trigger_objects, 'trigger_objects')

    def apply(self, rendered_sequence, lock):
        """ Applies check for namespace rule violations.

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
        self._custom_mutations = self._req_collection.candidate_values_pool.candidate_values
        logger.write_to_main("rendered_sequence={}".format(rendered_sequence), True)
        # We need more than one user to apply this checker.
        self._authentication_method = self._get_authentication_method()
        if self._authentication_method not \
                in [STATIC_OAUTH_TOKEN, primitives.REFRESHABLE_AUTHENTICATION_TOKEN]:
            return

        self._namespace_rule()

    def _render_original_sequence_start(self, seq):
        """ Helper to re-render the start of the original sequence to create
        the appropriate dynamic objects. Does not send the final target request.

        @param seq: The sequence whose last request we will try to render.
        @type  seq: Sequence Class object.

        @return: None
        @rtype : None

        """
        self._checker_log.checker_print("\nRe-rendering start of original sequence")

        for request in seq.requests[:-1]:
            rendered_data, parser, tracked_parameters, updated_writer_variables, replay_blocks = request.render_current(
                self._req_collection.candidate_values_pool
            )
            rendered_data = seq.resolve_dependencies(rendered_data)
            response = self._send_request(parser, rendered_data)
            if response.has_valid_code():
                for name, v in updated_writer_variables.items():
                    dependencies.set_variable(name, v)

            request_utilities.call_response_parser(parser, response)

    def _namespace_rule(self):
        """ Try to hijack objects of @param target_types and use them via
        a secondary attacker user.

        @param target_types: The types of the target object to attemp hijack.
        @type  target_types: Set

        @return: None
        @rtype : None

        """
        # For the target types (target dynamic objects), get the latest
        # values which we know will exist due to the previous rendering.
        # We will later on use these old values atop a new rendering.
        hijacked_values = {}
        consumed_types = self._sequence.consumes
        consumed_types = set(itertools.chain(*consumed_types))

        # Check if last request contains any trigger_object

        last_request = self._sequence.last_request
        last_rendering, last_parser, _, _, _ = last_request.render_current(self._req_collection.candidate_values_pool)

        last_request_contains_a_trigger_object = False
        for obj in self._trigger_objects:
            if last_rendering.find(obj) != -1:
                last_request_contains_a_trigger_object = True
                self._checker_log.checker_print(f"\n\
                    The last request contains trigger_object: {obj}\n\
                    The last request rendering is:\n{last_rendering}\n")
                break

        # Exit the checker if there is nothing to do.
        if not last_request_contains_a_trigger_object:
            if not self._trigger_on_dynamic_objects:
                return
            # Here, trigger_on_dynamic_objects is True.
            # Exit the checker if there are no consumed_types
            # # in the entire sequence.
            if not consumed_types:
                return
            # Exit the checker if non-exhaustive mode and
            # the last request does not consume anything.
            if self._mode != 'exhaustive' and not self._sequence.last_request.consumes:
                return

        # If we reach this point, we will re-render some request(s).

        self._render_original_sequence_start(self._sequence)

        if last_request_contains_a_trigger_object:
            # Simply re-render the last request with the attacker credentials.
            self._checker_log.checker_print(f"Re-rendering the last request with the attacker credentials.")
            self._render_hijack_request(last_request)
            if not self._trigger_on_dynamic_objects:
                return

        for type in consumed_types:
            hijacked_values[type] = dependencies.get_variable(type)

        self._checker_log.checker_print(f"Hijacked values: {hijacked_values}")

        for i, req in enumerate(self._sequence):
            # Render only last request if not in exhaustive (expensive) mode.
            if self._mode != 'exhaustive' and i != self._sequence.length - 1:
                continue
            # In exhaustive mode, skip requests that are not consumers.
            if not req.consumes:
                continue
            dependencies.reset_tlb()
            self._render_attacker_subsequence(req)

            # Feed hijacked values.
            for type in hijacked_values:
                dependencies.set_variable(type, hijacked_values[type])
            self._render_hijack_request(req)

    def _render_attacker_subsequence(self, req):
        """ Helper to render attacker user and try to hijack @param target_type
        objects.

        @param req: The hijack request.
        @type  req: Request Class object.

        @return: None
        @rtype : None

        """
        # Render subsquence up to before any producer of @param consumed_types.
        consumed_types = req.consumes
        for stopping_length, req in enumerate(self._sequence):
            # Stop before producing the target type.
            if req.produces.intersection(consumed_types):
                break

        for i in range(stopping_length):
            request = self._sequence.requests[i]
            rendered_data, parser, tracked_parameters, replay_blocks = request.render_current(
                self._req_collection.candidate_values_pool
            )
            rendered_data = self._sequence.resolve_dependencies(rendered_data)
            rendered_data = self._change_user_identity(rendered_data)
            response = self._send_request(parser, rendered_data)
            request_utilities.call_response_parser(parser, response)

        self._checker_log.checker_print("Subsequence rendering up to: {}". \
                                        format(stopping_length))

    def _render_hijack_request(self, req):
        """ Render the last request of the sequence and inspect the status
        code of the response. If it's any of 20x, we have probably hit a bug.

        @param req: The hijack request.
        @type  req: Request Class object.

        @return: None
        @rtype : None

        """
        self._checker_log.checker_print("Hijack request rendering")
        rendered_data, parser, tracked_parameters, updated_writer_variables, replay_blocks = req.render_current(
            self._req_collection.candidate_values_pool
        )
        rendered_data = self._sequence.resolve_dependencies(rendered_data)
        rendered_data = self._change_user_identity(rendered_data)

        response = self._send_request(parser, rendered_data)
        if response.has_valid_code():
            for name, v in updated_writer_variables.items():
                dependencies.set_variable(name, v)

        request_utilities.call_response_parser(parser, response)
        if response and self._rule_violation(self._sequence, response):
            self._print_suspect_sequence(self._sequence, response)
            logger.write_to_main(f"{self.__class__.__name__}", True)
            BugBuckets.Instance().update_bug_buckets(
                self._sequence, response.status_code, origin=self.__class__.__name__, reproduce=False
            )

    def _false_alarm(self, seq, response):
        """ Catches namespace rule violation false alarms that
        occur when a GET request returns an empty list as its body

        @param seq: The sequence to check
        @type  seq: Sequence Class object.
        @param response: Body of response.
        @type  response: Str

        @return: True if false alarm detected
        @rtype : Bool

        """
        try:
            if seq.last_request.method.startswith('GET') and response.body == '[]':
                return True
        except Exception:
            pass

        return False

    def _get_authentication_method(self):
        """ Trys to find out the authentication method used (if any).

        @return: The authenctication methid used.
        @rtype : Str

        """
        try:
            token1 = self._custom_mutations[primitives.CUSTOM_PAYLOAD][STATIC_OAUTH_TOKEN]
            token2 = self._custom_mutations[primitives.SHADOW_VALUES][primitives.CUSTOM_PAYLOAD][STATIC_OAUTH_TOKEN]
            return STATIC_OAUTH_TOKEN
        except Exception:
            pass

        from restler.engine.core.request_utilities import latest_token_value as token1
        from restler.engine.core.request_utilities import latest_shadow_token_value as token2
        if token1 is not NO_TOKEN_SPECIFIED and token2 is not NO_SHADOW_TOKEN_SPECIFIED:
            return primitives.REFRESHABLE_AUTHENTICATION_TOKEN

        return 'ONLY_ONE_USER'

    def _change_user_identity(self, data):
        """ Chandes user identity by substituting original token with shadow
        token.

        @param data: The payload whose token we will substitute
        @param data: Str

        @return: The new payload with the token substituted
        @rtype : Str

        """
        # print(repr(data))
        if self._authentication_method == primitives.REFRESHABLE_AUTHENTICATION_TOKEN:
            from restler.engine.core.request_utilities import latest_token_value
            from restler.engine.core.request_utilities import latest_shadow_token_value
            token1 = latest_token_value
            token2 = latest_shadow_token_value
            data = data.replace(token1, token2)
        else:
            shadow_values = self._custom_mutations[primitives.SHADOW_VALUES]
            for shadow_type in shadow_values:
                for shadow_key, shadow_val in shadow_values[shadow_type].items():
                    try:
                        victim_val = self._custom_mutations[shadow_type][shadow_key]
                        # Replace will do nothing if "replaced" value is not found.
                        data = data.replace(victim_val, shadow_val)
                    except Exception as error:
                        print(f"Exception: {error!s}")
                        continue
        # print(repr(data))
        return data
