# Copyright (c) Huawei Technologies Co., Ltd. 2025. All rights reserved.
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
import shutil

import unittest
from msprof_analyze.advisor.interface.interface import Interface
from msprof_analyze.advisor.common.analyzer_scopes import SupportedScopes


class TestAICorePerformanceAdvice(unittest.TestCase):
    TMP_DIR = "./TestAICorePerformanceAdvice/ascend_pt"
    OUTPUT_DIR = "./TestAICorePerformanceAdvice/ascend_pt/ASCEND_PROFILER_OUTPUT"
    interface = None
    err_interface = None

    @classmethod
    def clear_htmls(cls):
        current_path = os.path.dirname(os.path.abspath(__file__))
        for filename in os.listdir(current_path):
            # 检查文件是否以“mstt”开头
            if filename.startswith("mstt"):
                # 构建文件的完整路径
                file_path = os.path.join(current_path, filename)
                # 删除文件
                os.remove(file_path)

    @classmethod
    def copy_kernel_details(cls, path):
        # Define source and destination paths
        source_csv_path = os.path.join(os.path.dirname(__file__), 'data', path)
        destination_csv_path = f"{TestAICorePerformanceAdvice.OUTPUT_DIR}/kernel_details.csv"

        # Check if source CSV file exists
        if not os.path.exists(source_csv_path):
            raise FileNotFoundError(f"test data file not found:{source_csv_path}")

        # Ensure the output directory exists
        if not os.path.exists(TestAICorePerformanceAdvice.OUTPUT_DIR):
            os.makedirs(TestAICorePerformanceAdvice.OUTPUT_DIR)

        # Copy the CSV file from source to destination
        shutil.copyfile(source_csv_path, destination_csv_path)

    def tearDown(self):
        if os.path.exists(TestAICorePerformanceAdvice.TMP_DIR):
            shutil.rmtree(TestAICorePerformanceAdvice.TMP_DIR)
        self.clear_htmls()

    def setUp(self):
        if os.path.exists(TestAICorePerformanceAdvice.TMP_DIR):
            shutil.rmtree(TestAICorePerformanceAdvice.TMP_DIR)
        if not os.path.exists(TestAICorePerformanceAdvice.TMP_DIR):
            os.makedirs(TestAICorePerformanceAdvice.TMP_DIR)
        if not os.path.exists(TestAICorePerformanceAdvice.OUTPUT_DIR):
            os.makedirs(TestAICorePerformanceAdvice.OUTPUT_DIR)
        self.clear_htmls()

    def test_ai_core_performance_total(self):
        file_path = "kernel_details.csv"
        self.copy_kernel_details(file_path)
        interface = Interface(profiling_path=self.TMP_DIR)
        dimension = Interface.COMPUTATION
        scope = SupportedScopes.AICORE_PERFORMANCE_ANALYSIS
        result = interface.get_result(dimension, scope, render_html=1, output_dict=False, profiling_path=self.TMP_DIR)
        self.assertLess(1, len(result.data.get("Cube算子性能分析").get("data")[0]))
        self.assertLess(1, len(result.data.get("Cube算子性能分析").get("data")[1]))
        self.assertLess(1, len(result.data.get("Cube算子性能分析").get("data")[2]))
        self.assertLess(1, len(result.data.get("FA算子性能分析").get("data")[0]))
        self.assertLess(1, len(result.data.get("FA算子性能分析").get("data")[1]))
        self.assertLess(1, len(result.data.get("FA算子性能分析").get("data")[2]))
        self.assertLess(1, len(result.data.get("Vector算子性能分析").get("data")[0]))
        self.assertLess(1, len(result.data.get("Vector算子性能分析").get("data")[1]))
        result.clear()