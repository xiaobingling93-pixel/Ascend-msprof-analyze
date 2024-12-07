import os
from unittest import TestCase

import pandas as pd

from profiler.prof_common.path_manager import PathManager
from .utils import execute_cmd, check_result_file


class TestCompareToolsCmdPytorchNpuVsNpuEnableApiCompare(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
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
