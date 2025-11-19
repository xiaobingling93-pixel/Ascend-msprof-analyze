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
from unittest.mock import MagicMock, patch, call
from msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor import ModuleComparator
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger


class TestModuleComparator(unittest.TestCase):
    def setUp(self):
        self.mock_bean = MagicMock()
        self.mock_bean.rows = [["row_data"]]

        self.base_module1 = MagicMock()
        self.base_module1.start_time = 100
        
        self.base_module2 = MagicMock()
        self.base_module2.start_time = 200
        
        self.comparison_module1 = MagicMock()
        self.comparison_module1.start_time = 150
        
        self.comparison_module2 = MagicMock()
        self.comparison_module2.start_time = 250
        
        self.comparison_module3 = MagicMock()
        self.comparison_module3.start_time = 300
        self.origin_data = [
            (self.base_module1, self.comparison_module1),
            (self.base_module2, self.comparison_module2),
            (None, self.comparison_module3),
            (MagicMock(), None),
        ]

    def test_compare_with_empty_origin_data(self):
        comparator = ModuleComparator(None, self.mock_bean)
        comparator._compare()
        self.assertEqual(comparator._rows, [])

    def test_compare_with_empty_list(self):
        comparator = ModuleComparator([], self.mock_bean)
        comparator._compare()
        self.assertEqual(comparator._rows, [])

    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.update_order_id')
    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.logger')
    def test_compare_only_base_data(self, mock_logger, mock_update_order_id):
        origin_data = [
            (self.base_module1, None),
            (self.base_module2, None)
        ]
        
        comparator = ModuleComparator(origin_data, self.mock_bean)
        
        mock_bean_instance = MagicMock()
        mock_bean_instance.rows = [["test_row"]]
        self.mock_bean.return_value = mock_bean_instance
        
        comparator._compare()
        self.assertEqual(self.mock_bean.call_count, 2)
        mock_update_order_id.assert_called_once_with(comparator._rows)
        mock_logger.warning.assert_not_called()

    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.update_order_id')
    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.logger')
    def test_compare_only_comparison_data(self, mock_logger, mock_update_order_id):
        origin_data = [
            (None, self.comparison_module1),
            (None, self.comparison_module2)
        ]
        
        comparator = ModuleComparator(origin_data, self.mock_bean)
        
        mock_bean_instance = MagicMock()
        mock_bean_instance.rows = [["test_row"]]
        self.mock_bean.return_value = mock_bean_instance
        
        comparator._compare()
        self.assertEqual(self.mock_bean.call_count, 2)
        mock_update_order_id.assert_called_once_with(comparator._rows)
        mock_logger.warning.assert_not_called()

    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.update_order_id')
    @patch('msprof_analyze.compare_tools.compare_backend.comparator.module_comparetor.logger')
    def test_compare_with_timing_ordering(self, mock_logger, mock_update_order_id):
        base_module_early = MagicMock()
        base_module_early.start_time = 100
        
        base_module_late = MagicMock()
        base_module_late.start_time = 300
        
        comparison_module_mid = MagicMock()
        comparison_module_mid.start_time = 200
        
        comparison_module_very_late = MagicMock()
        comparison_module_very_late.start_time = 400
        comparison_only_early = MagicMock()
        comparison_only_early.start_time = 50
        
        comparison_only_mid = MagicMock()
        comparison_only_mid.start_time = 250
        
        origin_data = [
            (base_module_early, comparison_module_mid),
            (base_module_late, comparison_module_very_late),
            (None, comparison_only_early),
            (None, comparison_only_mid)
        ]
        
        comparator = ModuleComparator(origin_data, self.mock_bean)
        
        mock_bean_instance = MagicMock()
        mock_bean_instance.rows = [["test_row"]]
        self.mock_bean.return_value = mock_bean_instance
        
        comparator._compare()
        self.assertEqual(self.mock_bean.call_count, 4)
        mock_update_order_id.assert_called_once_with(comparator._rows)