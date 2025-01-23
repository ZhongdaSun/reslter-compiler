# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# The ordering of these checkers is expected to remain consistent.
# If a new checker is added or a new ordering is deemed necessary,
# the unit tests and baseline logs will need to be updated as well.
from rest.restler.checkers.leakage_rule_checker import *
from rest.restler.checkers.resource_hierarchy_checker import *
from rest.restler.checkers.use_after_free_checker import *
from rest.restler.checkers.namespace_rule_checker import *
from rest.restler.checkers.invalid_dynamic_object_checker import *
from rest.restler.checkers.payload_body_checker import *
from rest.restler.checkers.examples_checker import *
from rest.restler.checkers.invalid_value_checker import *