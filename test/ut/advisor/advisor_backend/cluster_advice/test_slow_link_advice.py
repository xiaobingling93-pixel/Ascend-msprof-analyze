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

from msprof_analyze.advisor.advisor_backend.cluster_advice.slow_link_advice import SlowLinkAdvice


class TestSlowLinkAdvice(unittest.TestCase):
    DATA = 'data'
    BOTTLENECK = 'bottleneck'
    ADVICE = 'advice'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prof_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../resource/advisor'))
        cls.expect_data = {
            0: {
                'RDMA time(ms)': 0,
                'RDMA size(mb)': 0,
                'SDMA time(ms)': 0.03629965625,
                'SDMA size(mb)': 0.08536799999999997,
                'RDMA bandwidth(GB/s)': 0,
                'SDMA bandwidth(GB/s)': 2.3518
            },
            1: {
                'RDMA time(ms)': 0,
                'RDMA size(mb)': 0,
                'SDMA time(ms)': 0.05697939062500001,
                'SDMA size(mb)': 0.13439200000000004,
                'RDMA bandwidth(GB/s)': 0,
                'SDMA bandwidth(GB/s)': 2.3586
            }
        }
        cls.expect_bottleneck = 'SDMA bandwidth(GB/s): \n' \
                                'The average is 2.355, ' \
                                'while the maximum  is 2.359GB/s and ' \
                                'the minimum is 2.352GB/s. ' \
                                'the difference is 0.007GB/s. \n'

    def test_compute_ratio_abnormal(self):
        result = SlowLinkAdvice.compute_ratio(19.0, 0)
        self.assertEqual(0, result)

    def test_load_communication_json_abnormal(self):
        slow_link_inst = SlowLinkAdvice("./tmp_dir")
        with self.assertRaises(RuntimeError):
            result = slow_link_inst.load_communication_json()

    def test_compute_bandwidth_abnormal(self):
        slow_link_inst = SlowLinkAdvice("./tmp_dir")
        op_dict = {"Name": "ZhangSan"}
        with self.assertRaises(ValueError):
            slow_link_inst.compute_bandwidth(op_dict)

    def test_run(self):
        slow_link_inst = SlowLinkAdvice(self.prof_dir)
        result = slow_link_inst.run()
        data = dict(result[self.DATA])
        bottleneck = result[self.BOTTLENECK]
        self.assertEqual(self.expect_data, data)
        self.assertEqual(self.expect_bottleneck, bottleneck)
