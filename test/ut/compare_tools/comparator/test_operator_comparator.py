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

from msprof_analyze.compare_tools.compare_backend.comparator.operator_comparator import OperatorComparator


class MockBean:
    TABLE_NAME = "TEST"
    HEADERS = ["INDEX", "VALUE1", "VALUE2"]
    OVERHEAD = []

    def __init__(self, index, base_op, comparison_op):
        self._index = index
        self._base_op = base_op
        self._comparison_op = comparison_op

    @property
    def row(self):
        return [self._index + 1, 1, 1]


class TestOperatorComparator(unittest.TestCase):
    def test_compare_when_valid_data(self):
        data = [[1, 1]] * 3
        result = [[1, 1, 1], [2, 1, 1], [3, 1, 1]]
        comparator = OperatorComparator(data, MockBean)
        comparator._compare()
        self.assertEqual(comparator._rows, result)

    def test_compare_when_invalid_data(self):
        comparator = OperatorComparator({}, MockBean)
        comparator._compare()
        self.assertEqual(comparator._rows, [])
