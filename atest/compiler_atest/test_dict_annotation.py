import unittest
import os

from utilities import (
    DebugConfig,
    Dict_Json,
    compile_spec,
    custom_skip_decorator)

module_name = os.path.basename(__file__).rsplit(".py", 1)[0]


class TestInputProducerSpec(unittest.TestCase):

    def setUp(self):
        DebugConfig().swagger_only = False

    def tearDown(self):
        pass

    @custom_skip_decorator(
        DebugConfig().get_cases_config(module_name, "test_input_producer_spec"))
    def test_input_producer_spec(self):
        result, msg = compile_spec(module_name,
                                   'input_producer_spec', [Dict_Json], "")
        self.assertTrue(result, msg=msg)


if __name__ == '__main__':
    unittest.main()
