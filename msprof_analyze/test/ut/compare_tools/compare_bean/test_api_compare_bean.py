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
from msprof_analyze.compare_tools.compare_backend.compare_bean.api_compare_bean import ApiInfo, ApiCompareBean
from msprof_analyze.compare_tools.compare_backend.utils.common_func import calculate_diff_ratio
from msprof_analyze.compare_tools.compare_backend.utils.excel_config import ExcelConfig
from msprof_analyze.prof_common.constant import Constant


class TestApiInfo(unittest.TestCase):
    def setUp(self):
        self.mock_data1 = MagicMock()
        self.mock_data1.api_dur = 5000.0
        self.mock_data1.api_self_time = 3000.0
        
        self.mock_data2 = MagicMock()
        self.mock_data2.api_dur = 7000.0
        self.mock_data2.api_self_time = 4000.0
        
        self.data_list = [self.mock_data1, self.mock_data2]

    def test_slots_behavior(self):
        api_info = ApiInfo("test_op", self.data_list)
        with self.assertRaises(AttributeError):
            api_info.new_attribute = "test"
        self.assertEqual(api_info.name, "test_op")


class TestApiCompareBean(unittest.TestCase):
    def setUp(self):
        self.base_data1 = MagicMock()
        self.base_data1.api_dur = 5000.0
        self.base_data1.api_self_time = 3000.0
        
        self.base_data2 = MagicMock()
        self.base_data2.api_dur = 7000.0
        self.base_data2.api_self_time = 4000.0
        
        self.comparison_data1 = MagicMock()
        self.comparison_data1.api_dur = 6000.0
        self.comparison_data1.api_self_time = 3500.0
        
        self.comparison_data2 = MagicMock()
        self.comparison_data2.api_dur = 8000.0
        self.comparison_data2.api_self_time = 4500.0
        
        self.base_api_list = [self.base_data1, self.base_data2]
        self.comparison_api_list = [self.comparison_data1, self.comparison_data2]

    def test_row_with_both_empty_data(self):
        bean = ApiCompareBean("test_op", [], [])
        row = bean.row
        self.assertEqual(row[2], 0.0)
        self.assertEqual(row[3], 0.0)
        self.assertEqual(row[4], 0.0)
        self.assertEqual(row[5], 0)
        self.assertEqual(row[6], 0.0)

    def test_row_with_different_data_lengths(self):
        single_comparison_data = [self.comparison_data1]
        bean = ApiCompareBean("test_op", self.base_api_list, single_comparison_data)
        row = bean.row
        
        self.assertEqual(row[5], 2)
        self.assertEqual(row[9], 1)
        self.assertEqual(row[4], 6.0)
        self.assertEqual(row[8], 6.0)