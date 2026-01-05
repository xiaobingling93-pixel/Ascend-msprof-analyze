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
import pandas as pd

from msprof_analyze.cluster_analyse.recipes.module_statistic.module_statistic import ModuleStatistic
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class NPUAnalyzer(ModuleStatistic):
    """分析 NPU Ascend PyTorch Profiler DB 文件"""

    def __init__(self, db_path):
        params = {
            Constant.RECIPE_NAME: "ms_custom",
            Constant.EXPORT_TYPE: Constant.EXCEL,
            Constant.RANK_ID: 0
        }
        super().__init__(params)
        self.db_path = db_path

    def analyze(self):
        """执行分析，返回统计 DataFrame"""
        data_map = {
            Constant.PROFILER_DB_PATH: self.db_path,
            Constant.PROFILING_PATH: os.path.dirname(self.db_path),
            Constant.RANK_ID: 0
        }
        # 使用 ModuleStatistic 的 _mapper_func 进行数据处理
        # _mapper_func 返回 (rank_id, stat_df)
        _, stat_df = self._mapper_func(data_map, None)
        return stat_df

    def _aggregate_module_operator_stats(self, df):
        """
        重写聚合逻辑，以匹配 NPUAnalyzer 的原始行为：
        将相同 (module, op, kernel) 的所有出现折叠为一行，并对持续时间求和。
        """
        if df is None or df.empty:
            logger.warning("Empty dataframe received for aggregation")
            return pd.DataFrame()

        # 注意：df 是 verbose_df，包含 'device_time'
        stat_df = (
            df.groupby(['module_parent', 'module', 'op_name', 'kernel_list'])
            .agg(
                module_start=('module_start', 'first'),
                op_start=('op_start', 'first'),
                total_kernel_duration=('device_time', 'sum'),
                avg_kernel_duration=('device_time', 'mean'),
                op_count=('device_time', 'count')
            ).reset_index()
        )

        stat_df = stat_df.sort_values(by=['module_parent', 'module']).reset_index(drop=True)
        stat_df.drop(columns=['module_start', 'op_start'], inplace=True)

        return self._format_stat_df_columns(stat_df)

    def _format_stat_df_columns(self, stat_df):
        try:
            # 我们总是使用 EXCEL 格式的列名
            stat_df = stat_df.rename(columns={
                'module_parent': 'Parent Module',
                'module': 'Module',
                'op_name': 'Op Name',
                'kernel_list': 'Kernel List',
                'op_count': 'Op Count',
                'total_kernel_duration': 'Total Kernel Duration(ns)',
                'avg_kernel_duration': 'Avg Kernel Duration(ns)'})
        except Exception as e:
            logger.error(f"Failed to format statistic data's title, error message: {e}")
            return pd.DataFrame()
        return stat_df

    def get_aggregated_df(self):
        """获取聚合后的 DataFrame"""
        stat_df = self.analyze()
        if stat_df.empty:
            print("No correlated data found.")
            return False

        final_df = stat_df.rename(columns={'Total Kernel Duration(ns)': 'Total Time (ns)',
                                           'Avg Kernel Duration(ns)': 'Avg Time (ns)'})
        final_df = final_df.set_index(['Parent Module', 'Module', 'Op Name'])
        return final_df
