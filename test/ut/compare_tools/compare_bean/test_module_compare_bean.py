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
from unittest.mock import patch, MagicMock
from msprof_analyze.compare_tools.compare_backend.compare_bean.module_compare_bean import ModuleCompareBean


class TestModuleCompareBean(unittest.TestCase):

    @patch("msprof_analyze.compare_tools.compare_backend.compare_bean."
           "module_compare_bean.longest_common_subsequence_matching")
    def test_modulecomparebean_rows_should_calculate_successfully(self, mock_longest_common_subsequence_matching):
        mock_kernel = MagicMock(device_dur=30, kernel_details="")
        op = MagicMock()
        op.name = "ADD"
        op.kernel_list = [mock_kernel]
        op.call_stack = ""
        mock_longest_common_subsequence_matching.return_value = [[op, op]]
        module = MagicMock()
        module.module_class = ""
        module.module_level = ""
        module.module_name = ""
        module.device_self_dur = 1
        module.device_total_dur = 2
        module.toy_layer_api_list = []
        module.call_stack = ""
        base_module = module
        module.device_total_dur = 3
        comparison_module = module
        bean = ModuleCompareBean(base_module, comparison_module)
        rows = bean.rows
        self.assertEqual(len(rows), 2)
