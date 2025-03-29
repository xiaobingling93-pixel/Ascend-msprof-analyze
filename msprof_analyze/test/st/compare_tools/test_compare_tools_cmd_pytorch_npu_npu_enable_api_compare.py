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


class TestCompareToolsCmdPytorchNpuVsNpuEnableApiCompare(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3", "n122-122-067_12380_20240912033946038_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3",
                                             "n122-122-067_12380_20240912033946038_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "CompareToolsCmdPytorchNpuVsNpuEnableApiCompare")
    RESULT_EXCEL = ""
    RE_MATCH_EXP = r"^performance_comparison_result_\d{1,20}\.xlsx"
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--enable_api_compare", "-o", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable api compare comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable api compare comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_api_compare(self):
        headers = ["Order Id", "api name", "Total Duration(ms)", "Self Time(ms)", "Avg Duration(ms)",
                   "Calls", "Total Duration(ms).1", "Self Time(ms).1", "Avg Duration(ms).1", "Calls.1",
                   "Diff Total Ratio", "Diff Self Ratio", "Diff Avg Ratio", "Diff Calls Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="ApiCompare", header=2)
        self.assertEqual(len(df), 311, msg="pytorch npu vs npu api compare results quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu api compare results headers is wrong")
