import os
from typing import List
from unittest import TestCase

import pandas as pd

from profiler.prof_common.path_manager import PathManager
from .utils import execute_cmd, check_result_file


class TestCompareToolsCmdPytorchNpuVsNpuEnableProfiling(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3", "n122-122-067_12380_20240912033946038_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3",
                                             "n122-122-067_12380_20240912033946038_ascend_pt")
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
            14474.86, 1194.01, 1194.01, 10442.62, 10402.34, 40.28, 2821.57, 444.33, 2377.24, 16.47,
            0.18, 23922.06, 4604.98, 9.35, 4595.63, 128.38, 127.35, 1.03, 93.30, 1.27, 92.03, 146.49, 0.10,
            146.39, 23310.81, 23310.81, 170.82, 0.20, 170.62, 373.72, 373.72, 38770.64
        ]
        diff_exp: List[float] = [0.37, 0.03, 0.03, 0.27, 0.27, 0.00, 0.07, 0.01, 0.06, 0.00,
                                 0.00, 0.62, 0.12, 0.00, 0.12, 0.00, 0.00, 0.00, 0.00, 0.00,
                                 0.00, 0.00, 0.00, 0.00, 0.60, 0.60, 0.00, 0.00, 0.00, 0.01,
                                 0.01, 1.00]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OverallMetrics", header=2)
        for index, row in df.iterrows():
            self.assertEqual(duration_exp[index], round(row["Duration(ms)"], 2),
                             msg="pytorch npu vs npu enable profiling compare results 'Duration(ms)"
                                 "' column is wrong")
            self.assertEqual(diff_exp[index], round(row["Duration Ratio"], 2),
                             msg="pytorch npu vs npu enable profiling compare results 'Duration Ratio"
                                 "' column is wrong")
