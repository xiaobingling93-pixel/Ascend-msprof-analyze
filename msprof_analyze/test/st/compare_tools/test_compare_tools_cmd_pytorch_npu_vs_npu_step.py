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


class TestCompareToolsCmdPytorchNpuVsNpu(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                       "n122-197-168_1333345_20241105122131111_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                             "n122-197-168_1632305_20241105124759292_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "CompareToolsCmdPytorchNpuVsNpuStep")
    RESULT_EXCEL = ""
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--base_step=5", "--comparison_step=5", "--disable_details", "-o", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="step comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="step comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_overall_metrics(self):
        duration_exp = [
            1725.15, 11.98, 11.98, 31.78, 31.78, 756.62, 705.49, 51.13, 879.83, 66.23, 813.60, 32.90, 12.04, 520.82,
            307.11, 13.12, 293.99, 0.00, 0.00, 207.81, 0.01, 207.80, 5.87, 0.01, 5.86, 0.03, 0.03, 2897.92, 2897.92,
            5143.89
        ]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OverallMetrics", header=2)
        for index, row in df.iterrows():
            self.assertEqual(duration_exp[index], round(row["Duration(ms)"], 2),
                             msg="pytorch npu vs npu step compare results 'Duration(ms)"
                                 "' column is wrong"
                             )

    def test_kernel_compare(self):
        headers = ["Order Id", "Kernel", "Input Shape", "Total Duration(us)", "Avg Duration(us)", "Max Duration(us)",
                   "Min Duration(us)", "Calls", "Total Duration(us).1", "Avg Duration(us).1", "Max Duration(us).1",
                   "Min Duration(us).1", "Calls.1", "Diff Total Ratio", "Diff Avg Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="KernelCompare", header=2)
        self.assertEqual(len(df), 498, msg="pytorch npu vs npu step compare results quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu step compare results headers is wrong")

    def test_communication_compare(self):
        total_duration: List[float] = [
            351054.85, 7.22, 400355.22, 80.52, 590652.54, 8.96, 25518.15, 67.62, 49.08, 389.39, 41357.87, 15.68,
            80.18, 144247.88, 867518.01, 4973.28, 336.97, 91039.10, 30.74
        ]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="CommunicationCompare", header=2)
        for index, row in df.iterrows():
            self.assertEqual(total_duration[index], round(row["Total Duration(us)"], 2),
                             msg="pytorch npu vs npu step communication compare results 'Total Duration(us)"
                                 "' column is wrong")

    def test_operator_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Device Duration(ms)", "Base Operator Number",
                   "Comparison Device Duration(ms)", "Comparison Operator Number", "Diff Duration(ms)", "Diff Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OperatorCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu operator compare results 'OperatorCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(),
                         msg="pytorch npu vs npu operator compare results 'OperatorCompareStatistic'"
                             "headers is wrong")

    def test_memory_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Allocated Duration(ms)", "Base Allocated Memory(MB)",
                   "Base Operator Number", "Comparison Allocated Duration(ms)", "Comparison Allocated Memory(MB)",
                   "Comparison Operator Number", "Diff Memory(MB)", "Diff Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="MemoryCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu memory compare results 'MemoryCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu memory compare results "
                                                           "'MemoryCompareStatistic' headers is wrong")

    def test_api_compare(self):
        headers = ["Order Id", "api name", "Total Duration(ms)", "Self Time(ms)", "Avg Duration(ms)",
                   "Calls", "Total Duration(ms).1", "Self Time(ms).1", "Avg Duration(ms).1", "Calls.1",
                   "Diff Total Ratio", "Diff Self Ratio", "Diff Avg Ratio", "Diff Calls Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="ApiCompare", header=2)
        self.assertEqual(len(df), 310, msg="pytorch npu vs npu api compare results quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu api compare results headers is wrong")
