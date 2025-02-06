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
import os
import unittest

from msprof_analyze.advisor.advisor_backend.interface import Interface


class TestOpScheAdvice(unittest.TestCase):
    interface = None

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        TestOpScheAdvice.interface = Interface(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace_view.json"))

    def test_run(self):
        dataset = TestOpScheAdvice.interface.get_data('timeline', 'op_schedule')
        case_advice = dataset.get('advice')
        case_bottleneck = dataset.get('bottleneck')
        case_data = dataset.get('data')
        self.assertEqual(201, len(case_advice))
        self.assertEqual(54, len(case_bottleneck))
        self.assertEqual(2, len(case_data))
        self.assertEqual(274, len(case_data[0]))
        self.assertEqual(274, len(case_data[1]))
