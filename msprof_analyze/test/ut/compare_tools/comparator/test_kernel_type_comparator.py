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
from unittest.mock import MagicMock, patch
from msprof_analyze.compare_tools.compare_backend.comparator.kernel_type_comparator import KernelTypeComparator
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.op_stastic_bean import OpStatisticBean
from msprof_analyze.prof_common.constant import Constant


class TestKernelTypeComparator(unittest.TestCase):
    def setUp(self):
        self.mock_bean = MagicMock()
        self.mock_bean.row = {"key": "test", "base": 0, "comparison": 0, "diff": 0}

        self.base_kernels = {
            "kernel_type1": MagicMock(),
            "kernel_type2": MagicMock(),
            "kernel_type3": MagicMock()
        }
        
        self.comparison_kernels = {
            "kernel_type1": MagicMock(),
            "kernel_type2": MagicMock(),
            "kernel_type4": MagicMock()
        }
        
        self.origin_data = {
            Constant.BASE_DATA: self.base_kernels,
            Constant.COMPARISON_DATA: self.comparison_kernels
        }

    def test_compare_with_empty_origin_data(self):
        comparator = KernelTypeComparator({}, self.mock_bean)
        comparator._compare()
        self.assertEqual(comparator._rows, [])

    @patch('msprof_analyze.compare_tools.compare_backend.comparator.kernel_type_comparator.update_order_id')
    def test_compare_mixed_data_types(self, mock_update_order_id):
        op_statistic_bean = OpStatisticBean({"total_time": 100})
        magic_mock = MagicMock()
        
        origin_data = {
            Constant.BASE_DATA: {"type1": op_statistic_bean, "type2": magic_mock},
            Constant.COMPARISON_DATA: {"type1": op_statistic_bean, "type2": magic_mock}
        }
        
        comparator = KernelTypeComparator(origin_data, self.mock_bean)
        
        mock_bean_instance = MagicMock()
        mock_bean_instance.row = ["test", 0, 0, 0]
        self.mock_bean.return_value = mock_bean_instance
        comparator._compare()
        self.assertEqual(self.mock_bean.call_count, 2)
        mock_update_order_id.assert_called_once_with(comparator._rows)