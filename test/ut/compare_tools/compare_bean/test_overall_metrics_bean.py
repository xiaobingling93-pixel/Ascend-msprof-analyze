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
from msprof_analyze.compare_tools.compare_backend.compare_bean.overall_metrics_bean import OverallMetricsBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.profiling_info import ProfilingInfo
from msprof_analyze.prof_common.constant import Constant


class TestOverallMetricsBean(unittest.TestCase):

    def test_rows_should_calculate_successfully(self):
        base_info = ProfilingInfo("pytorch")
        base_info.update_mc2_info("allReduceMatMul", 10, 4, 4)
        base_info.update_communication_group_pg_name({"default_group": "group_name_0", "mp": "group_name_41"})
        base_info.update_communication_group_time({
            "default_group": {
                Constant.WAIT_TIME: 0.1,
                Constant.TRANSMIT_TIME: 0.2
            },
            "mp": {
                Constant.WAIT_TIME: 0.3,
                Constant.TRANSMIT_TIME: 0.4
            }
        })
        comparison_info = ProfilingInfo("pytorch")
        comparison_info.update_mc2_info("allReduceMatMulV2", 9, 5, 5)
        comparison_info.update_communication_group_pg_name({"default_group": "group_name_0", "dp_cp": "group_name_17"})
        comparison_info.update_communication_group_time({
            "default_group": {
                Constant.WAIT_TIME: 0.3,
                Constant.TRANSMIT_TIME: 0.4
            },
            "dp_cp": {
                Constant.WAIT_TIME: 0.5,
                Constant.TRANSMIT_TIME: 0.6
            }
        })
        bean = OverallMetricsBean(base_info, comparison_info)
        rows = bean.rows
        self.assertTrue(rows)

