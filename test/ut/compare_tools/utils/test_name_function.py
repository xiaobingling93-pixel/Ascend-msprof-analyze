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

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from msprof_analyze.compare_tools.compare_backend.utils.name_function import NameFunction
from msprof_analyze.compare_tools.compare_backend.utils.torch_op_node import TorchOpNode


class Args:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


args = {"op_name_map": {}, "use_input_shape": True}
args = Args(**args)
func = NameFunction(args)


class TestNameFunction(unittest.TestCase):
    node = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.node = TorchOpNode(event=TraceEventBean(
            {"pid": 0, "tid": 0, "args": {"Input Dims": [[1, 1], [1, 1]], "name": 0}, "ts": 0, "dur": 1, "ph": "M",
             "name": "process_name"}))

    def test_get_name(self):
        self.assertEqual(NameFunction.get_name(self.node), "process_name")

    def test_get_full_name(self):
        self.assertEqual(NameFunction.get_full_name(self.node), "process_name1,1;\r\n1,1")

    def test_get_name_function(self):
        self.assertEqual(func.get_name_func(), func.get_full_map_name)

    def test_get_map_name(self):
        self.assertEqual(func.get_map_name(self.node), "process_name")

    def test_get_full_map_name(self):
        self.assertEqual(func.get_full_map_name(self.node), "process_name1,1;\r\n1,1")
