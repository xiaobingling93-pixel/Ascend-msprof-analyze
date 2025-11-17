# Copyright (c) 2025, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from msprof_analyze.advisor.common.enum_params_parser import EnumParamsParser
from test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestEnumParamsParser(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        self.enum_params_parser = EnumParamsParser()
        self.argument_keys = sorted(["cann_version", "torch_version", "analysis_dimensions",
                                     "profiling_type", "mindspore_version"])
        self.env_keys = ["ADVISOR_ANALYZE_PROCESSES", "DISABLE_PROFILING_COMPARISON", "DISABLE_AFFINITY_API"]

    def test_get_keys(self):
        total_keys = sorted(self.argument_keys + self.env_keys)
        keys = sorted(self.enum_params_parser.get_keys())
        self.assertIsInstance(keys, list)
        self.assertEqual(keys, total_keys)

    def test_get_argument_keys(self):
        argument_keys = sorted(self.enum_params_parser.get_arguments_keys())
        self.assertIsInstance(argument_keys, list)
        self.assertEqual(argument_keys, self.argument_keys)

    def test_get_env_keys(self):
        env_keys = sorted(self.enum_params_parser.get_envs_keys())
        self.assertIsInstance(env_keys, list)
        self.assertEqual(env_keys, sorted(self.env_keys))

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
