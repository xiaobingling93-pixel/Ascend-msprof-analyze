import unittest
import sys
import os

profiler_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(os.path.join(profiler_root_dir, "compare_tools"))
sys.path.append(os.path.join(profiler_root_dir, "cluster_analyse"))

from profiler.advisor.common.enum_params_parser import EnumParamsParser
from profiler.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestEnumParamsParser(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        self.enum_params_parser = EnumParamsParser()
        self.argument_keys = sorted(["cann_version", "torch_version", "analysis_dimensions", "profiling_type"])
        self.env_keys = ["ADVISOR_ANALYZE_PROCESSES"]

    def test_get_keys(self):
        total_keys = sorted(self.argument_keys + self.env_keys)
        keys = sorted(self.enum_params_parser.get_keys())
        self.assertTrue(isinstance(keys, list))
        self.assertEqual(keys, total_keys)

    def test_get_argument_keys(self):
        argument_keys = sorted(self.enum_params_parser.get_arguments_keys())
        self.assertTrue(isinstance(argument_keys, list))
        self.assertEqual(argument_keys, self.argument_keys)

    def test_get_env_keys(self):
        env_keys = sorted(self.enum_params_parser.get_envs_keys())
        self.assertTrue(isinstance(env_keys, list))
        self.assertEqual(env_keys, self.env_keys)

    def test_get_default(self):
        self.assertTrue(self.enum_params_parser.get_default("cann_version"), "8.0.RC1")
        self.assertTrue(self.enum_params_parser.get_default("torch_version"), "2.1.0")
        self.assertTrue(self.enum_params_parser.get_default("analysis_dimensions"),
                        ["computation", "communication", "schedule", "memory"])
        self.assertTrue(self.enum_params_parser.get_default("profiling_type"), "ascend_pytorch_profiler")
        self.assertTrue(self.enum_params_parser.get_default("ADVISOR_ANALYZE_PROCESSES"), 1)

    def test_get_options(self):
        self.assertTrue(self.enum_params_parser.get_options("cann_version"), ["6.3.RC2", "7.0.RC1", "7.0.0", "8.0.RC1"])
        self.assertTrue(self.enum_params_parser.get_options("torch_version"), ["1.11.0", "2.1.0"])
        self.assertTrue(self.enum_params_parser.get_options("analysis_dimensions"),
                        [["computation", "communication", "schedule", "memory"], ["communication"], ["schedule"],
                         ["computation"], ["memory"]])
        self.assertTrue(self.enum_params_parser.get_options("profiling_type"),
                        ["ascend_pytorch_profiler", "mslite", "msprof"])
        self.assertTrue(self.enum_params_parser.get_options("ADVISOR_ANALYZE_PROCESSES"), list(range(1, 9)))
