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

from msprof_analyze.cluster_analyse.cluster_utils.parallel_strategy_calculator import ParallelStrategyCalculator


class TestParallelStrategyCalculator(unittest.TestCase):
    def test_parallel_strategy_calculator_should_raise_runtime_error_when_dp4_ep3(self):
        with self.assertRaises(RuntimeError):
            calculator = ParallelStrategyCalculator(
                world_size=16,
                tensor_model_parallel_size=1,
                pipeline_model_parallel_size=4,
                data_parallel_size=4,
                context_parallel_size=1,
                expert_model_parallel_size=3)

            calculator.run()

    def test_parallel_strategy_calculator_should_raise_runtime_error_when_dp1_pp4_tp2_world_size16(self):
        with self.assertRaises(RuntimeError):
            calculator = ParallelStrategyCalculator(
                world_size=16,
                tensor_model_parallel_size=2,
                pipeline_model_parallel_size=4,
                data_parallel_size=1,
                context_parallel_size=1,
                expert_model_parallel_size=1)

            calculator.run()

    def test_parallel_strategy_calculator_dp2_pp4_tp2(self):
        calculator = ParallelStrategyCalculator(
            world_size=16,
            tensor_model_parallel_size=2,
            pipeline_model_parallel_size=4,
            data_parallel_size=2,
            context_parallel_size=1,
            expert_model_parallel_size=1)

        # dp index, pp index, tp index
        expected_res = [
            (0, 0, 0), (0, 0, 1), (1, 0, 0), (1, 0, 1), (0, 1, 0), (0, 1, 1), (1, 1, 0), (1, 1, 1),
            (0, 2, 0), (0, 2, 1), (1, 2, 0), (1, 2, 1), (0, 3, 0), (0, 3, 1), (1, 3, 0), (1, 3, 1)
        ]
        res = calculator.run()
        self.assertEqual(res, expected_res)
