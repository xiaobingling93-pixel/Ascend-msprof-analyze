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

import pandas as pd
import numpy as np
import difflib
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()

class Comparator:
    def __init__(self, df_gpu: pd.DataFrame,
                 df_npu: pd.DataFrame,
                 ):
        self.df_gpu = df_gpu
        self.df_npu = df_npu

    @staticmethod
    def agg_kernel(df: pd.DataFrame):
        agg_rules = {
            'Kernel List': lambda x: ', '.join(x.dropna().astype(str)),
            'Total Kernel Duration(ns)': 'sum',
            'Avg Kernel Duration(ns)': 'mean',
            'Op Count': 'sum',
            'Parent Module': 'first',
            'Module': 'first',
            'Op Name': 'first',
        }
        df = df.groupby(['Parent Module', 'Module', 'Op Name']).agg(agg_rules)

        return df

    @staticmethod
    def get_best_fuzzy_match(key, candidates, threshold=0.8):
        if not candidates:
            return None
        matches = difflib.get_close_matches(key, candidates, n=1, cutoff=threshold)
        return matches[0] if matches else None

    def compare(self, enable_fuzzy=True, fuzzy_threshold=0.6):
        df_gpu, df_npu = self.df_gpu, self.df_npu

        df_gpu = self.agg_kernel(df_gpu)
        df_npu = self.agg_kernel(df_npu)

        # 初始化匹配键
        df_gpu['match_key'] = df_gpu['Parent Module'].fillna('').astype(str) + '/' + df_gpu['Module'].astype(str)
        df_npu['match_key'] = df_npu['Parent Module'].fillna('').astype(str) + '/' + df_npu['Module'].astype(str)
        df_npu['match_key'] = df_npu['match_key'].str.replace('Ascend', '', regex=False)
        df_npu['match_type'] = 'rule'

        # 模糊匹配
        if enable_fuzzy:
            gpu_keys_set = set(df_gpu['match_key'])
            unmatched_mask = ~df_npu['match_key'].isin(gpu_keys_set)
            unmatched_npu_keys = df_npu.loc[unmatched_mask, 'match_key'].unique()
            candidate_keys = list(gpu_keys_set)

            match_map = {}
            for n_key in unmatched_npu_keys:
                best_match = self.get_best_fuzzy_match(n_key, candidate_keys, threshold=fuzzy_threshold)
                if best_match:
                    match_map[n_key] = best_match

            rows_to_update = df_npu['match_key'].isin(match_map.keys())
            df_npu.loc[rows_to_update, 'match_type'] = 'fuzzy'
            df_npu.loc[rows_to_update, 'match_key'] = df_npu.loc[rows_to_update, 'match_key'].map(match_map)

        df_gpu = df_gpu.sort_values(['match_key', 'Total Kernel Duration(ns)'], ascending=[True, False])
        df_npu = df_npu.sort_values(['match_key', 'Total Kernel Duration(ns)'], ascending=[True, False])

        df_gpu['row_id'] = df_gpu.groupby('match_key').cumcount()
        df_npu['row_id'] = df_npu.groupby('match_key').cumcount()

        df_merged = pd.merge(
            df_gpu,
            df_npu,
            on=['match_key', 'row_id'],
            how='outer',
            suffixes=('_gpu', '_npu')
        )

        split_keys = df_merged['match_key'].str.rsplit('/', n=1, expand=True)

        for suffix in ['_gpu', '_npu']:
            col_parent = f'Parent Module{suffix}'
            col_module = f'Module{suffix}'
            
            if col_parent not in df_merged.columns:
                df_merged[col_parent] = np.nan
            if col_module not in df_merged.columns:
                df_merged[col_module] = np.nan

            df_merged[col_parent] = df_merged[col_parent].fillna(split_keys[0])
            df_merged[col_module] = df_merged[col_module].fillna(split_keys[1])
        
        df_merged.drop(columns=['row_id'], inplace=True)

        # 计算耗时占比：Duration / sum(Duration)
        df_merged['Total Kernel Duration(%)_gpu'] = df_merged['Total Kernel Duration(ns)_gpu'] / df_merged['Total Kernel Duration(ns)_gpu'].sum() * 100
        df_merged['Total Kernel Duration(%)_npu'] = df_merged['Total Kernel Duration(ns)_npu'] / df_merged['Total Kernel Duration(ns)_npu'].sum() * 100

        # 计算 Module 层级的耗时比率：NPU / GPU
        gpu_module_sum = df_gpu.groupby('match_key')['Total Kernel Duration(ns)'].sum()
        npu_module_sum = df_npu.groupby('match_key')['Total Kernel Duration(ns)'].sum()
        
        # 计算 Ratio
        module_ratio = npu_module_sum / gpu_module_sum
        
        # 映射回 merged dataframe
        df_merged['Module Time Ratio (NPU/GPU)'] = df_merged['match_key'].map(module_ratio)

        match_cols = ['Parent Module_gpu', 'Module_gpu', 'Parent Module_npu', 'Module_npu', 'match_type']
        cols = match_cols + [
            'Op Name_gpu', 'Op Count_gpu', 'Kernel List_gpu',
            'Total Kernel Duration(ns)_gpu', 'Total Kernel Duration(%)_gpu', 'Avg Kernel Duration(ns)_gpu',
            'Op Name_npu', 'Op Count_npu', 'Kernel List_npu',
            'Total Kernel Duration(ns)_npu', 'Total Kernel Duration(%)_npu', 'Avg Kernel Duration(ns)_npu',
            'Module Time Ratio (NPU/GPU)',
        ]
        final_cols = [c for c in cols if c in df_merged.columns]

        for c in match_cols:
            if c not in df_merged.columns:
                df_merged[c] = np.nan
        df_merged = df_merged.fillna(' ')

        df_merged_final = df_merged[final_cols].sort_values(
            ['Parent Module_gpu', 'Module Time Ratio (NPU/GPU)', 'Total Kernel Duration(ns)_gpu'],
            ascending=[True, False, False]
        ).reset_index(drop=True)

        return df_merged_final
