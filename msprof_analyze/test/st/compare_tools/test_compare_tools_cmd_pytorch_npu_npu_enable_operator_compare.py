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


class TestCompareToolsCmdPytorchNpuVsNpuEnableOperatorCompare(TestCase):
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                       "n122-197-168_1333345_20241105122131111_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_4",
                                             "n122-197-168_1632305_20241105124759292_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "CompareToolsCmdPytorchNpuVsNpuEnableOperatorCompare")
    RESULT_EXCEL = ""
    IS_OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  "CompareToolsCmdPytorchNpuVsNpuEnableOperatorInputShapeCompare")
    IS_RESULT_EXCEL = ""
    MKN_OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   "CompareToolsCmdPytorchNpuVsNpuEnableOperatorMaxKernelNumCompare")
    MKN_RESULT_EXCEL = ""
    ONM_OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   "CompareToolsCmdPytorchNpuVsNpuEnableOperatorOpNameMapCompare")
    ONM_RESULT_EXCEL = ""
    RE_MATCH_EXP = r"^performance_comparison_result_\d{1,20}\.xlsx"
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        PathManager.make_dir_safety(self.IS_OUTPUT_PATH)
        PathManager.make_dir_safety(self.MKN_OUTPUT_PATH)
        PathManager.make_dir_safety(self.ONM_OUTPUT_PATH)
        # 1. no params compare
        cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
               "--enable_operator_compare", "--disable_details", "-o", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable operator compare comparison task failed.")
        if not check_result_file(self.OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable operator compare comparison result excel is not find.")
        self.RESULT_EXCEL = os.path.join(self.OUTPUT_PATH, check_result_file(self.OUTPUT_PATH))

        # 2. use_input_shape compare
        is_cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
                  "--enable_operator_compare", "--disable_details", "--use_input_shape", "-o", self.IS_OUTPUT_PATH,
                  "--force"]
        if execute_cmd(is_cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.IS_OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable use input shape operator compare comparison task failed.")
        if not check_result_file(self.IS_OUTPUT_PATH):
            self.assertEqual(False, True,
                             msg="enable use input shape operator compare comparison result excel is not find.")
        self.IS_RESULT_EXCEL = os.path.join(self.IS_OUTPUT_PATH, check_result_file(self.IS_OUTPUT_PATH))

        # 3. max_kernel_num compare
        mkn_cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
                   "--enable_operator_compare", "--disable_details", "--max_kernel_num=10", "-o", self.MKN_OUTPUT_PATH,
                   "--force"]
        if execute_cmd(mkn_cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.MKN_OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable max kernel num operator compare comparison task failed.")
        if not check_result_file(self.MKN_OUTPUT_PATH):
            self.assertEqual(False, True,
                             msg="enable max kernel num operator compare comparison result excel is not find.")
        self.MKN_RESULT_EXCEL = os.path.join(self.MKN_OUTPUT_PATH, check_result_file(self.MKN_OUTPUT_PATH))

        # 4. op_name_map compare
        onm_cmd = ["msprof-analyze", "compare", "-d", self.COMPARISON_PROFILING_PATH, "-bp", self.BASE_PROFILING_PATH,
                   "--enable_operator_compare", "--disable_details", "--op_name_map={'aten':'to','aten':'item'}", "-o",
                   self.ONM_OUTPUT_PATH, "--force"]
        if execute_cmd(onm_cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.ONM_OUTPUT_PATH):
            self.assertEqual(False, True, msg="enable op name map operator compare comparison task failed.")
        if not check_result_file(self.ONM_OUTPUT_PATH):
            self.assertEqual(False, True,
                             msg="enable op name map operator compare comparison result excel is not find.")
        self.ONM_RESULT_EXCEL = os.path.join(self.ONM_OUTPUT_PATH, check_result_file(self.ONM_OUTPUT_PATH))

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)
        PathManager.remove_path_safety(self.IS_OUTPUT_PATH)
        PathManager.remove_path_safety(self.MKN_OUTPUT_PATH)
        PathManager.remove_path_safety(self.ONM_OUTPUT_PATH)

    def test_operator_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Device Duration(ms)", "Base Operator Number",
                   "Comparison Device Duration(ms)", "Comparison Operator Number", "Diff Duration(ms)", "Diff Ratio"]
        df = pd.read_excel(self.RESULT_EXCEL, sheet_name="OperatorCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu operator compare results 'OperatorCompareStatistic'"
                                           "quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu operator compare results "
                                                           "'OperatorCompareStatistic' headers is wrong")

    def test_is_operator_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Device Duration(ms)", "Base Operator Number",
                   "Comparison Device Duration(ms)", "Comparison Operator Number", "Diff Duration(ms)", "Diff Ratio"]
        df = pd.read_excel(self.IS_RESULT_EXCEL, sheet_name="OperatorCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu use input shape operator compare results "
                                           "'OperatorCompareStatistic' quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu use input shape operator compare "
                                                           "results 'OperatorCompareStatistic' headers is wrong")

    def test_mkn_operator_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Device Duration(ms)", "Base Operator Number",
                   "Comparison Device Duration(ms)", "Comparison Operator Number", "Diff Duration(ms)", "Diff Ratio"]
        df = pd.read_excel(self.MKN_RESULT_EXCEL, sheet_name="OperatorCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu use input shape operator compare results "
                                           "'OperatorCompareStatistic' quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu use input shape operator compare "
                                                           "results 'OperatorCompareStatistic' headers is wrong")

    def test_onm_operator_compare_statistic(self):
        headers = ["Top", "Operator Name", "Base Device Duration(ms)", "Base Operator Number",
                   "Comparison Device Duration(ms)", "Comparison Operator Number", "Diff Duration(ms)", "Diff Ratio"]
        df = pd.read_excel(self.ONM_RESULT_EXCEL, sheet_name="OperatorCompareStatistic", header=2)
        self.assertEqual(len(df), 139, msg="pytorch npu vs npu use input shape operator compare results "
                                           "'OperatorCompareStatistic' quantity is wrong")
        self.assertEqual(headers, df.columns.tolist(), msg="pytorch npu vs npu use input shape operator compare "
                                                           "results 'OperatorCompareStatistic' headers is wrong")
