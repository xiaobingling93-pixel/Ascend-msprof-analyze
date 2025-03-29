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
import os
from unittest import TestCase

import pandas as pd

from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.test.st.utils import execute_cmd, check_result_file
from msprof_analyze.test.st.utils import ST_DATA_PATH


class TestCompareToolsCmdPytorchNpuVsNpuEnableMemoryCompare(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                       "n122-197-168_1333345_20241105122131111_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                             "n122-197-168_1632305_20241105124759292_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "CompareToolsCmdPytorchNpuVsNpuEnableMemoryCompare")
    RESULT_EXCEL = ""
    RE_MATCH_EXP = r"^performance_comparison_result_\d{1,20}\.xlsx"
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--enable_memory_compare", "--disable_details", "-o", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable memory compare comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable memory compare comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_memory_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Allocated Duration(ms)", "Base Allocated Memory(MB)",
                   "Base Operator Number", "Comparison Allocated Duration(ms)", "Comparison Allocated Memory(MB)",
                   "Comparison Operator Number", "Diff Memory(MB)", "Diff Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="MemoryCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu memory compare results 'MemoryCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(),
                         msg="pytorch npu vs npu memory compare results 'MemoryCompareStatistic'"
                             "headers is wrong")
