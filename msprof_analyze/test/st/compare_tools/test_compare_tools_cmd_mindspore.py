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
import unittest
from unittest import TestCase
import pandas as pd

from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.test.st.utils import execute_cmd, check_result_file
from msprof_analyze.test.st.utils import ST_DATA_PATH


class TestCompareToolsCmdMindSpore(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "ms_cluster_data_1", "ubuntu_3543034_20250228021645572_ascend_ms")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "ms_cluster_data_1",
                                             "ubuntu_3543025_20250228021645573_ascend_ms")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "CompareToolsCmdMindSpore")
    RESULT_EXCEL = ""
    COMMAND_SUCCESS = 0
    RUN_TEST = os.path.exists(BASE_PROFILING_PATH) and os.path.exists(COMPARISON_PROFILING_PATH)

    @unittest.skipIf(not RUN_TEST, "Skipping this test based on RUN_TEST environment variable")
    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH, "-o",
               self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertTrue(False, msg="enable api compare comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertTrue(False, msg="enable api compare comparison result excel is not find.")
        self.result_excel = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    @unittest.skipIf(not RUN_TEST, "Skipping this test based on RUN_TEST environment variable")
    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    @unittest.skipIf(not RUN_TEST, "Skipping this test based on RUN_TEST environment variable")
    def test_overall_metrics(self):
        index_exp = [
            "Computing Time", "Other", "Uncovered Communication Time", "tp-0-1-2-3", "Transmit",
            "hccl_world_group", "Transmit", "dp-cp-1", "Transmit", "pp-1-5", "Transmit",
            "dp-cp-0", "Transmit", "pp-0-4", "Transmit", "Uncovered Communication Overlapped",
            "tp-0-1-2-3 & dp-cp-1", "tp-0-1-2-3 & pp-1-5", "tp-0-1-2-3 & hccl_world_group", "tp-0-1-2-3 & dp-cp-0",
            "tp-0-1-2-3 & pp-0-4", "Free Time", "Free", "E2E Time"
        ]
        diff_duration = [0.74, 0.74, -243.79, -243.59, -243.59, -0.81, -0.81, -5.37, -5.37, -712.80, -712.80, 6.71,
                         6.71, 712.77, 712.77, 0.70, -4.31, -534.99, -0.62, 5.64, 534.96, 2.03, 2.03, -241.01]
        df = pd.read_excel(self.result_excel, sheet_name="OverallMetrics", header=2)
        for index, row in df.iterrows():
            self.assertEqual(index_exp[index], row["Index"].strip().split(":")[0],
                             msg="mindspore data compare results 'Index' column is wrong")
            self.assertEqual(diff_duration[index], round(row["Diff Duration(ms)"], 2),
                             msg="mindspore data compare results 'Diff Duration(ms)' column is wrong")