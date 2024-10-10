import os
import re
import subprocess
from unittest import TestCase

import pandas as pd

from profiler.prof_common.path_manager import PathManager


class TestCompareToolsCmdPytorchNpuVsNpu(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2", "n122-120-121_12321_20240911113658382_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2",
                                             "n122-120-121_12322_20240911113658370_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "CompareToolsCmdPytorchNpuVsNpu")
    RESULT_EXCEL = ""
    RE_MATCH_EXP = r"^performance_comparison_result_\d{1,20}\.xlsx"
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH, "-o",
               self.OUTPUT_PATH]
        completed_process = subprocess.run(cmd, capture_output=True, shell=False)
        if completed_process.returncode != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="comparison task failed.")
        files = os.listdir(self.OUTPUT_PATH)
        newest_file = None
        for file_name in files:
            if re.match(self.RE_MATCH_EXP, file_name):
                file_time = file_name.split(".")[0].split("_")[-1]
                if not newest_file or file_time > newest_file.split(".")[0].split("_")[-1]:
                    newest_file = file_name
        if not newest_file:
            self.assertEqual(False, True, msg="comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, newest_file)

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_overall_metrics(self):
        duration_exp = [
            14302.47, 1128.78, 1128.78, 10320.26, 10320.26, 2836.92, 445.59, 2391.33, 16.33, 0.18, 50636.60,
            8412.29, 11.69, 8400.59, 117.70, 116.68, 1.03, 82.64, 0.16, 82.47, 99.71, 0.00, 99.71, 32759.01, 32759.01,
            17478.85, 17308.09, 170.76, 682.94, 682.94, 65622.00
        ]
        diff_exp = [6.48, 4.84, 4.84, -9.23, -9.23, 10.77, -0.83, 11.60, 0.09, 0.01, 33.92, -331.06, 100.38, -431.44,
                    53.12, 53.13, -0.01, -1.53, 0.26, -1.79, -82.30, 0.19, -82.49, -35.74, -35.74, -0.36, -0.27, -0.09,
                    -48.46, -48.46, -8.05]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OverallMetrics", header=2)
        for index, row in df.iterrows():
            self.assertEqual(duration_exp[index], round(row["Duration(ms)"], 2))
            self.assertEqual(diff_exp[index], round(row["Diff Duration(ms)"], 2))

    def test_kernel_compare(self):
        headers = ["Order Id", "Kernel	Input Shape", "Total Duration(us)", "Avg Duration(us)", "Max Duration(us)",
                   "Min Duration(us)", "Calls", "Total Duration(us).1", "Avg Duration(us).1", "Max Duration(us).1",
                   "Min Duration(us).1", "Calls.1", "Diff Total Ratio", "Diff Avg Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="KernelCompare", header=2)
        self.assertTrue(df.shape[0], 704)
        self.assertTrue(headers, df.columns)
