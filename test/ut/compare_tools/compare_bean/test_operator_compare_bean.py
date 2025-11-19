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

from msprof_analyze.compare_tools.compare_backend.compare_bean.operator_compare_bean import OperatorCompareBean


class MockNode:
    def __init__(self, name):
        self.name = name
        self.input_shape = None
        self.input_type = None


class MockKernel:
    def __init__(self, device_dur):
        self.device_dur = device_dur
        self.kernel_details = "add"


class TestOperatorCompareBean(unittest.TestCase):
    name = 'aten::add'

    def test_row_when_valid_data(self):
        result = [2, self.name, None, None, 'add', 8, self.name, None, None, 'add', 8, 0, 1.0]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(8)]):
            op = OperatorCompareBean(1, MockNode(self.name), MockNode(self.name))
            self.assertEqual(op.row, result)

    def test_row_when_invalid_base_data(self):
        result = [2, None, None, None, "", 0, self.name, None, None, 'add', 8, 8, float("inf")]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(8)]):
            op = OperatorCompareBean(1, None, MockNode(self.name))
            self.assertEqual(op.row, result)

    def test_row_when_invalid_comparison_data(self):
        result = [2, self.name, None, None, 'add', 8, None, None, None, '', 0, -8, 0]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_kernels",
                   return_value=[MockKernel(8)]):
            op = OperatorCompareBean(1, MockNode(self.name), None)
            self.assertEqual(op.row, result)
