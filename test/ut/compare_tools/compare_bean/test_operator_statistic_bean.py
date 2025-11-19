# Copyright (c) 2025, Huawei Technologies Co., Ltd. All rights reserved.
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
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.compare_bean.operator_statistic_bean import OperatorStatisticBean


class MockKernel:
    def __init__(self, device_dur):
        self.device_dur = device_dur


class TestOperatorStatisticBean(unittest.TestCase):
    name = "matmul"

    def test_row_when_valid_data(self):
        result = [None, self.name, 8.0, 2, 4.0, 1, -4.0, 0.5]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(2000), MockKernel(2000)]):
            bean = OperatorStatisticBean(self.name, [1, 1], [1])
            self.assertEqual(bean.row, result)

    def test_row_when_invalid_base_data(self):
        result = [None, self.name, 0, 0, 4.0, 1, 4.0, float("inf")]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(2000), MockKernel(2000)]):
            bean = OperatorStatisticBean(self.name, [], [1])
            self.assertEqual(bean.row, result)

    def test_row_when_invalid_comparison_data(self):
        result = [None, self.name, 8.0, 2, 0, 0, -8.0, 0]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(2000), MockKernel(2000)]):
            bean = OperatorStatisticBean(self.name, [1, 1], [])
            self.assertEqual(bean.row, result)
