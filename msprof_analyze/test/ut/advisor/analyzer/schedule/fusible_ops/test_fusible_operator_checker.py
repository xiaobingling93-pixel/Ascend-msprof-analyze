# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
from unittest.mock import MagicMock, patch

from msprof_analyze.advisor.analyzer.schedule.fusible_ops.fusible_operator_checker import FusibleOperatorChecker
from msprof_analyze.advisor.result.result import OptimizeResult


class TestFusibleOperatorChecker(unittest.TestCase):
    def setUp(self):
        self.checker = FusibleOperatorChecker()

    def test_get_mte_time(self):
        task = MagicMock()
        task.aic_mte2_time = '10'
        task.aiv_mte2_time = '20'
        task.aic_fixpipe_time = '30'
        task.aiv_mte3_time = '40'
        result = FusibleOperatorChecker.get_mte_time(task)
        self.assertEqual(result, 60.0)

    def test_check_hccl(self):
        task1 = MagicMock(task_type='COMMUNICATION', op_name='hcom_op')
        task2 = MagicMock(task_type='OTHER', op_name='normal_op')
        self.assertTrue(FusibleOperatorChecker.check_hccl(task1))
        self.assertFalse(FusibleOperatorChecker.check_hccl(task2))

    def test_calculate_total_time(self):
        pre_timestamp = '10'
        timestamp = '20'
        duration = '5'
        result, flag = FusibleOperatorChecker.calculate_total_time(pre_timestamp, timestamp, duration)
        self.assertEqual(result, 15)
        self.assertTrue(flag)

    def test_check_sequence_ratio(self):
        detail = [100, 0, 0, 0, False, False]
        self.checker.step_duration = 50
        self.checker.sequence_duration_threshold = 0.1
        result = self.checker.check_sequence_ratio(detail)
        self.assertTrue(result)

    def test_check_sequence_num(self):
        detail = [0, 0, 0, 10, False, False]
        self.checker.sequence_count_threshold = 5
        result = self.checker.check_sequence_num(detail)
        self.assertTrue(result)

    def test_check_bound(self):
        detail1 = [100, 0, 0, 0, True, False]
        detail2 = [10, 0, 0, 0, False, False]
        self.checker.step_duration = 50
        self.checker.sequence_duration_threshold = 0.3
        self.assertTrue(self.checker.check_bound(detail1))
        self.assertFalse(self.checker.check_bound(detail2))

    def test_add_detail(self):
        task_name = 'test_task'
        details = []
        detail = [100, 50, 30, 2, True, False]
        self.checker.index_dict[task_name] = (0, 1)
        self.checker.add_detail(task_name, details, detail)
        self.assertEqual(len(details), 1)

    def test_generate_key(self):
        task = MagicMock(op_name='test_op', input_shapes='[1,2]', output_shapes='[2,3]')
        result = self.checker.generate_key(task)
        self.assertEqual(result, 'test_op-[1,2]-[2,3]')

    def test_compute_priority(self):
        self.checker.host_details = [[100, 0, 0, 0, False, False]]
        self.checker.mte_details = []
        self.checker.step_duration = 50
        result = self.checker.compute_priority()
        from msprof_analyze.advisor.display.html.priority_background_color import PriorityBackgroundColor
        self.assertEqual(result, PriorityBackgroundColor.high)

    def test_check_tasks(self):
        profiling_dataset = MagicMock()
        profiling_dataset.op_summary.op_list = [MagicMock()]
        with patch('msprof_analyze.advisor.analyzer.schedule.fusible_ops.fusible_operator_checker.' \
                   'FusibleOperatorChecker.calculate_total_time') as mock_calculate:
            mock_calculate.return_value = (100, True)
            result = self.checker.check_tasks(profiling_dataset)
            self.assertTrue(result)

    def test_make_record(self):
        result = OptimizeResult()
        self.checker.problem = 'test_problem'
        self.checker.desc = 'test_desc'
        self.checker.suggestions = ['test_suggestion']
        self.checker.host_details = [[1, 2, 100, 50, 30, 2, True, False]]
        self.checker.mte_details = [[3, 4, 200, 100, 60, 3, False, True]]
        self.checker.make_record(result)
        self.assertTrue(result.page_dict)


if __name__ == '__main__':
    unittest.main()
