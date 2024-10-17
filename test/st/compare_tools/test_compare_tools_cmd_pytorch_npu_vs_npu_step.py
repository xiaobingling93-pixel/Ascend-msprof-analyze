import os
from typing import List
from unittest import TestCase

import pandas as pd

from profiler.prof_common.path_manager import PathManager
from .utils import execute_cmd, check_result_file


class TestCompareToolsCmdPytorchNpuVsNpu(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3", "n122-122-067_12380_20240912033946038_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3",
                                             "n122-122-067_12380_20240912033946038_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "CompareToolsCmdPytorchNpuVsNpuStep")
    RESULT_EXCEL = ""
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--base_step=5", "--comparison_step=5", "--disable_details", "-o", self.OUTPUT_PATH]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="step comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="step comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_overall_metrics(self):
        duration_exp = [
            14474.86, 1194.01, 1194.01, 10442.62, 10402.34, 40.28, 2821.57, 444.33, 2377.24, 16.47, 0.18, 23922.06,
            4604.98, 9.35, 4595.63, 128.38, 127.35, 1.03, 93.30, 1.27, 92.03, 146.49, 0.10, 146.39, 23310.81, 23310.81,
            170.82, 0.20, 170.62, 373.72, 373.72, 38770.64
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
        self.assertEqual(len(df), 703, msg="pytorch npu vs npu step compare results quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu step compare results headers is wrong")

    def test_communication_compare(self):
        total_duration: List[float] = [
            9354.86, 1046.68, 9191.52, 24.74, 27743477.86, 12418099.90, 23832.90, 28928712.46, 18411.66, 2939703.28,
            327934.12, 17074.96, 77.58, 931489.92, 2894.42, 75.46, 80.86, 15119087.00, 3594561.44, 12963.36,
            12692002.20, 6180907.46, 9859.70
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
        self.assertEqual(len(df), 141, msg="pytorch npu vs npu operator compare results 'OperatorCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(),
                         msg="pytorch npu vs npu operator compare results 'OperatorCompareStatistic'"
                             "headers is wrong")

    def test_memory_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Allocated Duration(ms)", "Base Allocated Memory(MB)",
                   "Base Operator Number", "Comparison Allocated Duration(ms)", "Comparison Allocated Memory(MB)",
                   "Comparison Operator Number", "Diff Memory(MB)", "Diff Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="MemoryCompareStatistic", header=2)
        self.assertEqual(len(df), 141, msg="pytorch npu vs npu memory compare results 'MemoryCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu memory compare results "
                                                           "'MemoryCompareStatistic' headers is wrong")

    def test_api_compare(self):
        headers = ["Order Id", "api name", "Total Duration(ms)", "Self Time(ms)", "Avg Duration(ms)",
                   "Calls", "Total Duration(ms).1", "Self Time(ms).1", "Avg Duration(ms).1", "Calls.1",
                   "Diff Total Ratio", "Diff Self Ratio", "Diff Avg Ratio", "Diff Calls Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="ApiCompare", header=2)
        self.assertEqual(len(df), 311, msg="pytorch npu vs npu api compare results quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu api compare results headers is wrong")
