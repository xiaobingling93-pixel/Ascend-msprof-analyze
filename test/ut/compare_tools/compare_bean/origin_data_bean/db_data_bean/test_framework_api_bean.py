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

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.framework_api_bean import \
    FrameworkApiBean


class TestFrameworkApiBean(unittest.TestCase):
    bean = FrameworkApiBean(
        {"name": "aten::add", "startNs": 1749193260000000000, "endNs": 1749199260000000000, "connectionId": 123,
         "cann_connectionId": 33, "inputShapes": "256;64", "inputDtypes": "int8;float"})

    def test_property(self):
        self.assertEqual(self.bean.dur, 6000000000.0)
        self.assertEqual(self.bean.connection_id, 123)
        self.assertEqual(self.bean.cann_connection_id, 33)
        self.assertEqual(self.bean.input_dims, "256;64")
        self.assertEqual(self.bean.input_type, "int8;float")
        self.assertEqual(self.bean.start_time, 1749193260000000)

    def test_reset_name(self):
        self.bean.reset_name("aaa")
        self.assertEqual(self.bean.name, "aaa")

    def test_is_optimizer(self):
        self.assertFalse(self.bean.is_optimizer())
        self.bean.reset_name("OptimizerNpu")
        self.assertTrue(self.bean.is_optimizer())

    def test_is_step_profiler(self):
        self.assertFalse(self.bean.is_step_profiler())
        self.bean.reset_name("ProfilerStep#4")
        self.assertTrue(self.bean.is_step_profiler())

    def test_is_fa_for_cpu_op(self):
        self.assertFalse(self.bean.is_fa_for_cpu_op())
        self.bean.reset_name("flash_attention")
        self.assertTrue(self.bean.is_fa_for_cpu_op())

    def test_is_conv_for_cpu_op(self):
        self.assertFalse(self.bean.is_conv_for_cpu_op())
        self.bean.reset_name("aten::conv")
        self.assertTrue(self.bean.is_conv_for_cpu_op())

    def test_is_matmul_for_cpu_op(self):
        self.assertFalse(self.bean.is_matmul_for_cpu_op())
        self.bean.reset_name("aten::addmm")
        self.assertTrue(self.bean.is_matmul_for_cpu_op())

    def test_is_bwd_for_cpu_op(self):
        self.assertFalse(self.bean.is_bwd_for_cpu_op())
        self.bean.reset_name("backward")
        self.assertTrue(self.bean.is_bwd_for_cpu_op())

    def test_is_cpu_cube_op(self):
        self.bean.reset_name("aten::bmm")
        self.assertTrue(self.bean.is_cpu_cube_op())

    def test_is_x_mode(self):
        self.bean.x_mode = True
        self.assertTrue(self.bean.is_x_mode())
