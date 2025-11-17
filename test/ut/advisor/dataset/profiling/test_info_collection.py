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
from msprof_analyze.advisor.dataset.profiling.info_collection import OpInfo


class TestOpInfo(unittest.TestCase):
    def test_has_attr_when_strict_mode_is_true(self):
        info = OpInfo()
        self.assertFalse(info.has_attr("key", True))

    def test_has_attr_when_strict_mode_is_false(self):
        info = OpInfo()
        self.assertFalse(info.has_attr("key", False))
        info.add_attr("key", "value")
        self.assertTrue(info.has_attr("key", False))

    def test_get_attr_when_strict_mode_is_true(self):
        info = OpInfo()
        info.add_attr("key", "value")
        self.assertTrue(info.get_attr("key", True))

    def test_get_attr_should_return_empty_str_when_strict_mode_is_false_and_key_not_exists(self):
        info = OpInfo()
        self.assertEqual(info.get_attr("key", False), "")

    def test_get_attr_should_return_value_when_strict_mode_is_false_and_key_exists(self):
        info = OpInfo()
        info.add_attr("aic_mac_ratio", "0.5")
        info.add_attr("aiv_vec_ratio", "0.5")
        self.assertEqual(info.get_attr("mac_ratio", False), "0.5")
        self.assertEqual(info.get_attr("vec_ratio", False), "0.5")

    def test_get_float_attr_should_return_right_value_when_key_exists(self):
        info = OpInfo()
        info.add_attr("key", "1.0")
        self.assertEqual(info.get_float_attr("key", False), 1.0)

    def test_get_float_attr_should_return_0_when_invalid_conversion(self):
        info = OpInfo()
        info.add_attr("key", "a")
        self.assertEqual(info.get_float_attr("key", False), 0.0)

    def test_get_decimal_attr_should_return_right_value_when_key_exists(self):
        info = OpInfo()
        info.add_attr("key", "1.0")
        self.assertEqual(info.get_decimal_attr("key", False), 1.0)

    def test_get_decimal_attr_should_return_0_when_invalid_conversion(self):
        info = OpInfo()
        info.add_attr("key", "a")
        self.assertEqual(info.get_decimal_attr("key", False), 0.0)

    def test_is_cube_op_should_return_true_when_op_name_contains_cube(self):
        info = OpInfo()
        info.add_attr("mac_ratio", "0.5")
        info.add_attr("ffts_type", "1")
        info.add_attr("op_name", "ffts_task")
        self.assertTrue(info.is_cube_op)

    def test_is_cube_op_should_return_false_when_op_name_not_contains_cube(self):
        info = OpInfo()
        info.add_attr("mac_ratio", "0")
        info.add_attr("ffts_type", "0")
        info.add_attr("op_name", "ffts_task")
        self.assertFalse(info.is_cube_op)