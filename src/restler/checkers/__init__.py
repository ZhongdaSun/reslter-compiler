# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# The ordering of these checkers is expected to remain consistent.
# If a new checker is added or a new ordering is deemed necessary,
# the unit tests and baseline logs will need to be updated as well.
from restler.checkers.leakage_rule_checker import *
from restler.checkers.resource_hierarchy_checker import *
from restler.checkers.use_after_free_checker import *
from restler.checkers.namespace_rule_checker import *
from restler.checkers.invalid_dynamic_object_checker import *
from restler.checkers.payload_body_checker import *
from restler.checkers.examples_checker import *
from restler.checkers.invalid_value_checker import *