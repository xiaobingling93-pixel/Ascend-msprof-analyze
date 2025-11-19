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

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.operator_memory_bean \
    import OperatorMemoryBean


class TestOperatorMemoryBean(unittest.TestCase):
    bean1 = OperatorMemoryBean({"Name": "cann::add", "Size(KB)": 512, "Allocation Time(us)": 1, "Release Time(us)": 5})
    bean2 = OperatorMemoryBean({"Name": "aten::add", "Size(KB)": 512})

    @staticmethod
    def _get_property_str(bean: OperatorMemoryBean):
        return f"{bean.name}-{bean.size}-{bean.allocation_time}-{bean.release_time}"

    def test_property(self):
        self.assertEqual(self._get_property_str(self.bean1), "cann::add-512.0-1-5")
        self.assertEqual(self._get_property_str(self.bean2), "aten::add-512.0-0-0")

    def test_is_cann_op(self):
        self.assertTrue(self.bean1.is_cann_op())
        self.assertFalse(self.bean2.is_cann_op())
