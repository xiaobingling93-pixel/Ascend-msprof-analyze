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
import tempfile
import pandas as pd

from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.gpu_analyzer import GPUAnalyzer
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.npu_analyzer import NPUAnalyzer
from msprof_analyze.cluster_analyse.recipes.calibrate_npu_gpu.comparator import Comparator
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager

logger = get_logger()


class CalibrateNpuGpu(BaseRecipeAnalysis):
    """GPU/NPU 性能校准分析"""

    def __init__(self, params):
        super().__init__(params)
        logger.info("CalibrateAnalysis init.")
        self.gpu_path = self._extra_args.get('gpu_path', '')
        self.npu_path = self._extra_args.get('npu_path', '')
        self.fuzzy_threshold = float(self._extra_args.get('fuzzy_threshold', 0.8))

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @classmethod
    def add_parser_argument(cls, parser):
        BaseRecipeAnalysis.add_parser_argument(parser)
        parser.add_argument('--gpu_path', type=str, required=True,
                           help='Path to GPU profile SQLite file (required for calibrate mode)')
        parser.add_argument('--npu_path', type=str, required=True,
                           help='Path to NPU profile DB file (required for calibrate mode)')
        parser.add_argument('--fuzzy_threshold', type=float, default=0.8,
                           help='Fuzzy matching threshold between NPU and GPU operations (default: 0.8)')

    def _mapper_func(self, data_map, analysis_class):
        """
        calibrate 模式不需要标准的 mapper 处理，返回空列表
        """
        return []

    def run(self, context):
        """执行校准分析"""
        # 检查必需参数
        if not self.gpu_path or not self.npu_path:
            logger.error("Both --gpu_path and --npu_path are required for calibrate mode.")
            return

        # 检查文件存在性
        if not os.path.exists(self.gpu_path):
            logger.error(f"GPU profile file not found: {self.gpu_path}")
            return
        if not os.path.exists(self.npu_path):
            logger.error(f"NPU profile file not found: {self.npu_path}")
            return

        # 确保输出目录存在
        PathManager.make_dir_safety(self._output_path)

        # 生成输出文件路径
        output_excel = os.path.join(self._output_path, 'compare_profile_report.xlsx')

        # 使用临时目录处理中间文件
        with tempfile.TemporaryDirectory() as tmpdir:
            # 分析 GPU
            logger.info("Analyzing GPU profile...")
            gpu_analyzer = GPUAnalyzer(self.gpu_path)
            gpu_df = gpu_analyzer.get_aggregated_df().reset_index()
            if gpu_df is None or gpu_df.empty:
                logger.error("GPU analysis failed.")
                return

            # 分析 NPU
            logger.info("Analyzing NPU profile...")
            npu_analyzer = NPUAnalyzer(self.npu_path)
            npu_df = npu_analyzer.get_aggregated_df().reset_index()
            if npu_df is None or npu_df.empty:
                logger.error("NPU analysis failed.")
                return

            # 比较结果
            logger.info("Comparing GPU and NPU profiles...")
            comparator = Comparator(gpu_df, npu_df)
            compare_df = comparator.compare(self.fuzzy_threshold)
            comparator.export_excel(output_excel)

        logger.info(f"Calibration report generated: {output_excel}")

        # 根据导出类型处理结果
        if self._export_type == "db":
            self.save_db(compare_df)
        elif self._export_type == "excel":
            # Excel 已经在上面生成了，无需额外操作
            pass
        elif self._export_type == "notebook":
            self.save_notebook(compare_df)
        else:
            logger.error(f"Unsupported export type: {self._export_type}")

    def save_db(self, df):
        """保存结果到数据库"""
        if df is None or df.empty:
            logger.warning("No data to save to database.")
            return
        self.dump_data(df, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER,
                       "CalibrateResult", index=False)
        logger.info("Calibration result saved to database.")

    def save_notebook(self, df):
        """生成 Notebook 报告"""
        if df is None or df.empty:
            logger.warning("No data to generate notebook.")
            return
        # 保存数据文件供 Notebook 使用
        csv_path = os.path.join(self._output_path, 'calibrate_result.csv')
        df.to_csv(csv_path, index=False)
        # 创建 Notebook
        self.create_notebook("stats.ipynb")
        logger.info("Calibration notebook generated.")