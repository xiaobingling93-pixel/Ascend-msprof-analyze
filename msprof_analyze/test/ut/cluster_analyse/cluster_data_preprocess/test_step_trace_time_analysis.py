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

from msprof_analyze.cluster_analyse.analysis.step_trace_time_analysis import StepTraceTimeAnalysis
from msprof_analyze.cluster_analyse.prof_bean.step_trace_time_bean import StepTraceTimeBean
from msprof_analyze.prof_common.constant import Constant


class TestStepTraceTimeAnalysis(unittest.TestCase):
    DIR_PATH = ''

    def test_get_max_data_row_when_given_data_return_max_rows(self):
        check = StepTraceTimeAnalysis({})
        ls = [
            [1, 3, 5, 7, 10],
            [2, 4, 6, 8, 11],
            [1000, -1, -1, -1, -1]
        ]
        ret = check.get_max_data_row(ls)
        self.assertEqual([1000, 4, 6, 8, 11], ret)

    def test_get_max_data_when_given_row_single_ls_return_this_row(self):
        check = StepTraceTimeAnalysis({})
        ls = [
            [1, 3, 5, 7, 10]
        ]
        ret = check.get_max_data_row(ls)
        self.assertEqual([1, 3, 5, 7, 10], ret)

    def test_analyze_step_time_when_give_normal_expect_stage(self):
        check = StepTraceTimeAnalysis({})
        check.data_type = Constant.TEXT
        check.step_time_dict = {
            0: [
                StepTraceTimeBean({"Step": 0, "time1": 1, "time2": 2}),
                StepTraceTimeBean({"Step": 1, "time1": 1, "time2": 2}),
            ],
            1: [
                StepTraceTimeBean({"Step": 0, "time1": 10, "time2": 20}),
                StepTraceTimeBean({"Step": 1, "time1": 10, "time2": 20})
            ]
        }
        check.communication_data_dict = {Constant.STAGE: [[0, 1]]}
        check.analyze_step_time()
        self.assertIn([0, 'stage', (0, 1), 10.0, 20.0], check.step_data_list)

    def test_analyze_step_time_when_given_none_step_expect_stage_and_rank_row(self):
        check = StepTraceTimeAnalysis({})
        check.data_type = Constant.TEXT
        check.step_time_dict = {
            0: [
                StepTraceTimeBean({"Step": None, "time1": 1, "time2": 2})
            ],
            1: [
                StepTraceTimeBean({"Step": None, "time1": 10, "time2": 20}),
            ],
            2: [
                StepTraceTimeBean({"Step": None, "time1": 2, "time2": 3}),
            ],
            3: [
                StepTraceTimeBean({"Step": None, "time1": 1, "time2": 1}),
            ],
        }
        check.communication_data_dict = {Constant.STAGE: [[0, 1], [2, 3]]}
        check.analyze_step_time()
        self.assertIn([None, 'stage', (2, 3), 2.0, 3.0], check.step_data_list)
        self.assertIn([None, 'rank', 0, 1.0, 2.0], check.step_data_list)