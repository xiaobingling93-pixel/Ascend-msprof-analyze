#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from msprof_analyze.cluster_analyse.common_func.excel_utils import ExcelUtils
from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.gpu_analyzer import GPUAnalyzer
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.comparator import Comparator
from msprof_analyze.cluster_analyse.recipes.module_statistic.module_statistic import ModuleStatistic
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class CalibrateNpuGpu(BaseRecipeAnalysis):
    def __init__(self, params):
        super().__init__(params)
        self.npu_module_statistic_analyzer = ModuleStatistic(params=params)
        self.baseline_profiling_path = self._extra_args.get('baseline_profiling_path', '')
        self.fuzzy_threshold = float(self._extra_args.get('fuzzy_threshold', 0.8))

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @classmethod
    def add_parser_argument(cls, parser):
        BaseRecipeAnalysis.add_parser_argument(parser)
        parser.add_argument('--baseline_profiling_path', type=str, required=True,
                           help='Path to baseline profile (GPU or NPU)')
        parser.add_argument('--fuzzy_threshold', type=float, default=0.8,
                           help='Fuzzy matching threshold between profiles (default: 0.8)')

    def export_excel(self, output_path, file_name, df_compare):
        index_cols = ['Parent Module_gpu', 'Module_gpu', 'Parent Module_npu', 'Module_npu', 'Module Time Ratio (NPU/GPU)']
        column_width_config = {
            "Parent Module_npu": 20,
            "Module_npu": 20,
            "Parent Module_gpu": 20,
            "Module_gpu": 20,

            "match_type": 10,

            "Op Name_gpu": 20,
            "Op Count_gpu": 10,
            "Kernel List_gpu": 40,
            "Total Kernel Duration(ns)_gpu": 10,
            "Total Kernel Duration(%)_gpu": 10,
            "Avg Kernel Duration(ns)_gpu": 10,

            "Op Name_npu": 20,
            "Op Count_npu": 10,
            "Kernel List_npu": 40,
            "Total Kernel Duration(ns)_npu": 10,
            "Total Kernel Duration(%)_npu": 10,
            "Avg Kernel Duration(ns)_npu": 10,

            "Module Time Ratio (NPU/GPU)": 20
        }

        excel_utils = ExcelUtils()
        excel_utils.create_excel_writer(output_path, file_name, df_compare)
        excel_utils.merge_duplicate_cells(index_cols)
        excel_utils.set_column_width(column_width_config)
        excel_utils.set_row_height(0, 27)
        excel_utils.save_and_close()
        excel_utils.clear()

    def run(self, context):
        if not self.baseline_profiling_path or not os.path.exists(self.baseline_profiling_path):
            logger.error("Please make sure the profiling path of baseline is properly indicated")
            return

        logger.info("Analyzing GPU profile...")
        gpu_analyzer = GPUAnalyzer(self.baseline_profiling_path)
        gpu_df_dict = gpu_analyzer.get_aggregated_df()
        
        logger.info("Analyzing NPU profile...")
        npu_dfs = self.npu_module_statistic_analyzer.run(context, save=False)

        for rank_id, npu_df in npu_dfs:
            file_name_to_save = f'compare_profile_report_{rank_id}.xlsx'
            gpu_df = gpu_df_dict[rank_id].reset_index()
            logger.info("Comparing GPU and NPU profiles...")
            comparator = Comparator(gpu_df, npu_df)
            compare_df = comparator.compare(self.fuzzy_threshold)
            self.export_excel(self.output_path, file_name_to_save, compare_df)
            logger.info(f"Calibration report generated: {os.path.join(self.output_path, file_name_to_save)}")

        if self._export_type == "db":
            self.save_db(compare_df)
        elif self._export_type == "excel":
            pass
        elif self._export_type == "notebook":
            self.save_notebook(compare_df)
        else:
            logger.error(f"Unsupported export type: {self._export_type}")

    def save_db(self, df):
        if df is None or df.empty:
            logger.warning("No data to save to database.")
            return
        self.dump_data(df, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER,
                       "CalibrateResult", index=False)
        logger.info("Calibration result saved to database.")

    def save_notebook(self, df):
        if df is None or df.empty:
            logger.warning("No data to generate notebook.")
            return
        # 保存数据文件供 Notebook 使用
        csv_path = os.path.join(self._output_path, 'calibrate_result.csv')
        df.to_csv(csv_path, index=False)
        # 创建 Notebook
        self.create_notebook("stats.ipynb")
        logger.info("Calibration notebook generated.")
