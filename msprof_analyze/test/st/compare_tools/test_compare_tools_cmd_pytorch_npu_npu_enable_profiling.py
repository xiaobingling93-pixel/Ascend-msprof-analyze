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
from typing import List
from unittest import TestCase

import pandas as pd

from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.test.st.utils import execute_cmd, check_result_file
from msprof_analyze.test.st.utils import ST_DATA_PATH


class TestCompareToolsCmdPytorchNpuVsNpuEnableProfiling(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                       "n122-197-168_1333345_20241105122131111_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                             "n122-197-168_1632305_20241105124759292_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "CompareToolsCmdPytorchNpuVsNpuEnableProfiling")
    RESULT_EXCEL = ""
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--enable_profiling_compare", "-o", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable profiling comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable profiling comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_overall_metrics(self):
        duration_exp: List[float] = [
            1725.15, 11.98, 11.98, 31.78, 31.78, 756.62, 705.49, 51.13, 879.83, 66.23, 813.60, 32.90, 12.04, 520.82,
            307.11, 13.12, 293.99, 0.00, 0.00, 207.81, 0.01, 207.80, 5.87, 0.01, 5.86, 0.03, 0.03, 2897.92, 2897.92,
            5143.89
        ]
        diff_exp: List[float] = [
            0.34, 0.00, 0.00, 0.01, 0.01, 0.15, 0.14, 0.01, 0.17, 0.01, 0.16, 0.01, 0.00, 0.10, 0.06, 0.00, 0.06, 0.00,
            0.00, 0.04, 0.00, 0.04, 0.00, 0.00, 0.00, 0.00, 0.00, 0.56, 0.56, 1.00]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OverallMetrics", header=2)
        for index, row in df.iterrows():
            self.assertEqual(duration_exp[index], round(row["Duration(ms)"], 2),
                             msg="pytorch npu vs npu enable profiling compare results 'Duration(ms)"
                                 "' column is wrong")
            self.assertEqual(diff_exp[index], round(row["Duration Ratio"], 2),
                             msg="pytorch npu vs npu enable profiling compare results 'Duration Ratio"
                                 "' column is wrong")
