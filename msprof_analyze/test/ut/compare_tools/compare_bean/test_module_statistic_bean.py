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
from unittest.mock import MagicMock, patch
from msprof_analyze.compare_tools.compare_backend.compare_bean.module_statistic_bean import ModuleStatisticBean


class TestModuleStatisticBean(unittest.TestCase):

    def test_modulestatisticbean_rows_should_calculate_successfully(self):
        mock_kernel = MagicMock()
        mock_kernel.kernel_name = "add"
        mock_kernel.device_dur = 2
        mock_torch_op = MagicMock()
        mock_torch_op.name = "add"
        mock_torch_op.device_dur = 5
        mock_torch_op.kernel_list = [mock_kernel]
        mock_data = MagicMock()
        mock_data.device_self_dur = 5
        mock_data.device_total_dur = 10
        mock_data.toy_layer_api_list = [mock_torch_op]
        base_data = [mock_data]
        mock_data.device_total_dur = 11
        comparison_data = [mock_data]
        bean = ModuleStatisticBean("nn.Module/add", base_data, comparison_data)
        rows = bean.rows
        self.assertEqual(len(rows), 2)
