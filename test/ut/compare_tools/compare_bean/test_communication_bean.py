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

from msprof_analyze.compare_tools.compare_backend.compare_bean.communication_bean import CommunicationBean


class TestCommunicationBean(unittest.TestCase):
    def test_rows_when_valid_data(self):
        base_data = {"comm_list": [0.5, 7], "comm_task": {"Notify Wait": [1, 2, 3]}}
        comparison_data = {"comm_list": [1, 3, 5], "comm_task": {"Notify Wait": [1, 2, 3], "Memcpy": [5]}}
        result = [[None, 'allreduce', None, 2, 7.5, 3.75, 7, 0.5, 'allreduce', None, 3, 9, 3.0, 5, 1, 1.5, 1.2],
                  [None, '|', 'Notify Wait', 3, 6, 2.0, 3, 1, '|', 'Notify Wait', 3, 6, 2.0, 3, 1, None, None],
                  [None, None, None, None, 0, None, None, None, '|', 'Memcpy', 1, 5, 5.0, 5, 5, None, None]]

        comm = CommunicationBean("allreduce", base_data, comparison_data)
        self.assertEqual(comm.rows, result)
