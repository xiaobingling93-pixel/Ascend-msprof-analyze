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
import copy
import os

from msprof_analyze.advisor.analyzer.computation.pp_stage_computation_analyzer import PPStageComputationAnalyzer
from msprof_analyze.test.ut.advisor.advisor_backend.tools.tool import recover_env


mock_profiling_path = os.path.realpath(__file__)

class TestPPStageComputationAnalyzer(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        self.rank_num = 8
        rank_result_data = {
            "problems": {
                "data": [["ai cpu issues", "ai cpu desc", "ai cpu suggestion"],
                         ["frequency issues", "frequency desc"]]
            },
            "ai cpu issues": {
                "headers": ["op name", "duration", "count"],
                "data": [["index", 1000, 10]]
            },
            "frequency issues": {
                "headers": ["op name", "duration", "freq reduction"],
                "data": [["matmul", 1000, 0.5]]
            }
        }
        self.mocked_multiprocess_data = {}
        for i in range(self.rank_num):
            self.mocked_multiprocess_data[f"rank {i}"] = copy.deepcopy(rank_result_data)

    def test_merge_multiprocess_result(self):
        pp_stage_computation_analyzer = PPStageComputationAnalyzer(mock_profiling_path)
        pp_stage_computation_analyzer._merge_multiprocess_result()
        result = pp_stage_computation_analyzer.result
        self.assertFalse(result.data)

        pp_stage_computation_analyzer._multiprocess_result = copy.deepcopy(self.mocked_multiprocess_data)
        pp_stage_computation_analyzer._merge_multiprocess_result()
        data = dict(pp_stage_computation_analyzer.result.data)

        problems = data.get("问题综述", {}).get("data", [])
        self.assertEqual(len(problems), self.rank_num)
        for i in range(self.rank_num):
            self.assertTrue(f"rank {i} ai cpu issues" in data)
            self.assertTrue(f"rank {i} frequency issues" in data)


if __name__ == '__main__':
    tester = TestPPStageComputationAnalyzer()
    tester.test_merge_multiprocess_result()
