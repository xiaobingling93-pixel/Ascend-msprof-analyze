#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Huawei Technologies Co., Ltd.
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

import copy
import numpy as np
import os

from msprof_analyze.cluster_analyse.common_func.excel_utils import ExcelUtils
from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.gpu_analyzer import GPUAnalyzer
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.comparator import Comparator
from msprof_analyze.cluster_analyse.recipes.module_statistic.module_statistic import ModuleStatistic
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager

logger = get_logger()


class CalibrateNpuGpu(BaseRecipeAnalysis):
    def __init__(self, params):
        super().__init__(params)
        module_statistic_params = copy.copy(params)
        module_statistic_params.pop('args')
        self.npu_module_statistic_analyzer = ModuleStatistic(params=module_statistic_params)
        self.baseline_profiling_path = self._extra_args.get('baseline_profiling_path', '')
        self.fuzzy_threshold = float(self._extra_args.get('fuzzy_threshold', 0.8))
        self.dump_intermediate_results = self._extra_args.get('dump_intermediate_results', False)

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @classmethod
    def add_parser_argument(cls, parser):
        BaseRecipeAnalysis.add_parser_argument(parser)
        parser.add_argument('--baseline_profiling_path', type=str, required=True,
                           help='Path to the baseline GPU profile')
        parser.add_argument('--fuzzy_threshold', type=float, default=0.8,
                           help='Fuzzy matching threshold between profiles (default: 0.8)')
        parser.add_argument('--dump_intermediate_results', action='store_true',
                           help='Whether to dump intermediate analysis results to Excel files')

    def export_excel(self, output_path, rank_id, df_compare):
        columns_width_configs = {
            'npu': {
                'module': {
                    "(NPU) Parent Module": 20,
                    "(NPU) Module": 20,
                },
                'op_and_kernel': {
                    "(NPU) Op Name": 20,
                    "(NPU) Op Count": 10,
                    "(NPU) Kernel List": 40,
                    "(NPU) Total Kernel Duration(us)": 10,
                    "(NPU) Total Kernel Duration(%)": 10,
                    "(NPU) Avg Kernel Duration(us)": 10,
                }
            },
            'gpu': {
                'module': {
                    "(GPU) Parent Module": 20,
                    "(GPU) Module": 20,
                },
                'op_and_kernel': {
                    "(GPU) Op Name": 20,
                    "(GPU) Op Count": 10,
                    "(GPU) Kernel List": 40,
                    "(GPU) Total Kernel Duration(us)": 10,
                    "(GPU) Total Kernel Duration(%)": 10,
                    "(GPU) Avg Kernel Duration(us)": 10,
                }
            },
            'match_type': {
                "Match Type": 10,
            },
            'compare': {
                "(NPU/GPU) Module Time Ratio": 10,
                "(NPU-GPU,us) Module Time Diff": 10
            }
        }
        excel_utils = ExcelUtils()
        if self.dump_intermediate_results:
            for platform in ['npu', 'gpu']:
                intermediate_file_name = f'{platform}_report_{rank_id}.xlsx'
                index_cols = columns_width_configs[platform]["module"].keys()
                width_configs = columns_width_configs[platform]["module"] | columns_width_configs[platform]["op_and_kernel"]
                platform_df = df_compare[width_configs.keys()].copy()
                op_name_key = f"({platform.upper()}) Op Name"
                platform_df = platform_df[platform_df[op_name_key] != ' ']
                excel_utils.create_excel_writer(output_path, intermediate_file_name, platform_df)
                excel_utils.merge_duplicate_cells(index_cols)
                excel_utils.set_column_width(width_configs)
                excel_utils.set_row_height(0, 27)
                excel_utils.save_and_close()
                excel_utils.clear()
                logger.info(f"{platform} report generated: {os.path.join(output_path, intermediate_file_name)}")

        file_name = f'compare_profile_report_{rank_id}.xlsx'
        index_cols = \
            columns_width_configs["npu"]["module"].keys() | \
                columns_width_configs["gpu"]["module"].keys() | \
                    columns_width_configs["compare"].keys()
        width_configs = \
            columns_width_configs["npu"]["module"] | columns_width_configs["gpu"]["module"] | \
                columns_width_configs["match_type"] | \
                    columns_width_configs["npu"]["op_and_kernel"] | columns_width_configs["gpu"]["op_and_kernel"] | \
                        columns_width_configs["compare"]
        excel_utils.create_excel_writer(output_path, file_name, df_compare)
        excel_utils.merge_duplicate_cells(index_cols)
        excel_utils.set_column_width(width_configs)
        excel_utils.set_row_height(0, 27)
        excel_utils.save_and_close()
        excel_utils.clear()
        logger.info(f"Calibration report generated: {os.path.join(self.output_path, file_name)}")

    def run(self, context):
        PathManager.check_input_file_path(self.baseline_profiling_path)
        PathManager.check_path_owner_consistent([self.baseline_profiling_path])

        logger.info("Analyzing GPU profile...")
        gpu_analyzer = GPUAnalyzer(self.baseline_profiling_path, self._recipe_name)
        gpu_df_dict = gpu_analyzer.get_aggregated_df()
        
        logger.info("Analyzing NPU profile...")
        npu_dfs = self.npu_module_statistic_analyzer.run(context, save=False)

        for rank_id, npu_df in npu_dfs:
            gpu_df = gpu_df_dict[rank_id].reset_index()
            logger.info("Comparing GPU and NPU profiles...")
            comparator = Comparator(gpu_df, npu_df)
            compare_df = comparator.compare(self.fuzzy_threshold)

            if self._export_type == "db":
                self.save_db(compare_df)
            elif self._export_type == "excel":
                self.export_excel(self.output_path, rank_id, compare_df)
            else:
                logger.error(f"Unsupported export type: {self._export_type}")

    def save_db(self, df):
        if df is None or df.empty:
            logger.warning("No data to save to database.")
            return
        self.dump_data(df, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER,
                       "CalibrateResult", index=False)
        logger.info("Calibration result saved to database.")
