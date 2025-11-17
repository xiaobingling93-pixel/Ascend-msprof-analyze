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

from msprof_analyze.cluster_analyse.prof_bean.step_trace_time_bean import StepTraceTimeBean


class TestStepTraceTimeBean(unittest.TestCase):

    def test(self):
        data = {"Step": 0, "Attr1": 1, "Attr2": 2}
        bean = StepTraceTimeBean(data)
        self.assertEqual(bean.row, [1.0, 2.0])
        self.assertEqual(bean.step, 0)
        self.assertEqual(bean.all_headers, ['Step', 'Type', 'Index', 'Attr1', 'Attr2'])
