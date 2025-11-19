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

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.memory_record_bean \
    import MemoryRecordBean


class TestMemoryRecordBean(unittest.TestCase):
    def test_total_reserved_mb(self):
        self.assertEqual(MemoryRecordBean({"Total Reserved(MB)": 5}).total_reserved_mb, 5)
        self.assertEqual(MemoryRecordBean({}).total_reserved_mb, 0)
