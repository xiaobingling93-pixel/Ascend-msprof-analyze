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


class Comparator:
    """比较 GPU 和 NPU 分析结果"""

    def __init__(self, df_gpu: pd.DataFrame,
                 df_npu: pd.DataFrame,
                 ):
        self.df_gpu = df_gpu
        self.df_npu = df_npu

    @staticmethod
    def preprocess_and_agg(df, platform_suffix, kernel_col_name, count_col_name):
        """预处理和聚合数据（同原 preprocess_and_agg）"""
        df = df.copy()
        df['full_module'] = df['Parent Module'].fillna('').astype(str) + '/' + df['Module'].astype(str)

        agg_rules = {
            'Op Name': lambda x: ','.join(x.dropna().astype(str).unique()),
            kernel_col_name: lambda x: ','.join(x.dropna().astype(str)),
            'Total Time (ns)': 'sum',
            'Parent Module': 'first',
            'Module': 'first'
        }

        df_agg = df.groupby('full_module', as_index=False).agg(agg_rules)

        rename_dict = {
            'Total Time (ns)': f'Total Time (ns){platform_suffix}',
            'Op Name': f'Op Name{platform_suffix}',
            kernel_col_name: f'Kernel List{platform_suffix}',
            'full_module': f'full_module{platform_suffix}'
        }
        return df_agg.rename(columns=rename_dict)

    @staticmethod
    def get_best_fuzzy_match(key, candidates, threshold=0.8):
        """模糊匹配（同原 get_best_fuzzy_match）"""
        if not candidates:
            return None
        matches = difflib.get_close_matches(key, candidates, n=1, cutoff=threshold)
        return matches[0] if matches else None

    def compare(self, enable_fuzzy=True, fuzzy_threshold=0.6):
        """比较 GPU 和 NPU 数据，返回合并 DataFrame"""
        df_gpu, df_npu = self.df_gpu, self.df_npu

        # 聚合数据
        df_gpu_agg = self.preprocess_and_agg(df_gpu, '_gpu', 'Kernel Name', 'Count')
        df_npu_agg = self.preprocess_and_agg(df_npu, '_npu', 'Kernel List', 'Op Count')

        # 初始化匹配键
        df_gpu_agg['match_key'] = df_gpu_agg['full_module_gpu']
        df_npu_agg['match_key'] = df_npu_agg['full_module_npu'].str.replace('Ascend', '', regex=False)
        df_npu_agg['match_type'] = 'rule'

        # 模糊匹配
        if enable_fuzzy:
            gpu_keys_set = set(df_gpu_agg['match_key'])
            unmatched_mask = ~df_npu_agg['match_key'].isin(gpu_keys_set)
            unmatched_npu_keys = df_npu_agg.loc[unmatched_mask, 'match_key'].unique()
            candidate_keys = list(gpu_keys_set)

            match_map = {}
            for n_key in unmatched_npu_keys:
                best_match = self.get_best_fuzzy_match(n_key, candidate_keys, threshold=fuzzy_threshold)
                if best_match:
                    match_map[n_key] = best_match

            rows_to_update = df_npu_agg['match_key'].isin(match_map.keys())
            df_npu_agg.loc[rows_to_update, 'match_type'] = 'fuzzy'
            df_npu_agg.loc[rows_to_update, 'match_key'] = df_npu_agg.loc[rows_to_update, 'match_key'].map(match_map)

        # 合并
        df_merged = pd.merge(
            df_gpu_agg,
            df_npu_agg,
            on='match_key',
            how='outer',
            suffixes=('_gpu', '_npu')
        )

        df_merged['full_module_name'] = df_merged['match_key']

        # 计算比率
        t_gpu = df_merged['Total Time (ns)_gpu']
        t_npu = df_merged['Total Time (ns)_npu']
        df_merged['Time Ratio (NPU/GPU)'] = t_npu / t_gpu

        # 列排序
        match_cols = ['Parent Module_gpu', 'Module_gpu', 'Parent Module_npu', 'Module_npu', 'match_type']
        cols = match_cols + [
            'Op Name_gpu', 'Kernel List_gpu',
            'Total Time (ns)_gpu', 'Total Time (ns)_npu', 'Time Ratio (NPU/GPU)',
            'Op Name_npu', 'Kernel List_npu',
        ]
        final_cols = [c for c in cols if c in df_merged.columns]

        # 填充缺失列
        for c in match_cols:
            if c not in df_merged.columns:
                df_merged[c] = np.nan
        df_merged['match_type'] = df_merged['match_type'].fillna('')

        df_merged_final = df_merged[final_cols].sort_values(
            ['Parent Module_gpu', 'Total Time (ns)_gpu', 'Time Ratio (NPU/GPU)'],
            ascending=[True, False, False]
        ).reset_index(drop=True)

        return df_merged_final

    def export_excel(self, output_path, alarm_threshold=1.5):
        """导出比较报告 Excel"""
        df_raw = self.compare()
        if df_raw.empty:
            print("No compared data found.")
            return False

        final_df = df_raw.copy()
        index_cols = ['Parent Module_gpu', 'Module_gpu', 'Parent Module_npu', 'Module_npu']
        final_df = final_df.set_index(index_cols)
        len_index = len(index_cols)

        try:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Sheet 1: Compare Profile Analysis
                final_df.to_excel(writer, merge_cells=True, sheet_name='Compare Profile Analysis')
                workbook = writer.book

                format_float = workbook.add_format({'num_format': '0.00'})
                red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                yellow_format = workbook.add_format({'bg_color': '#FFFFCC', 'font_color': '#333333'})

                worksheet1 = writer.sheets['Compare Profile Analysis']
                worksheet1.set_column('A:D', 30)
                worksheet1.set_column('E:E', 15)
                worksheet1.set_column('F:G', 20)
                worksheet1.set_column('H:J', 20, format_float)
                worksheet1.set_column('K:L', 20)

                # 标记 Time Ratio 超过阈值的
                if 'Time Ratio (NPU/GPU)' in final_df.columns:
                    col_idx = final_df.columns.get_loc('Time Ratio (NPU/GPU)')
                    col_idx += len_index

                    start_row = 1
                    end_row = final_df.shape[0] + 1

                    worksheet1.conditional_format(start_row, col_idx, end_row, col_idx, {
                        'type': 'cell',
                        'criteria': '>',
                        'value': alarm_threshold,
                        'format': red_format
                    })

                    # 高亮 fuzzy 匹配行
                    match_type_col_letter = 'E'
                    range_str = f"A2:E{end_row + 1}"
                    worksheet1.conditional_format(range_str, {
                        'type': 'formula',
                        'criteria': f'=${match_type_col_letter}2="fuzzy"',
                        'format': yellow_format
                    })

            print(f"Success! Comparison report generated: {output_path}")
            return True
        except Exception as e:
            print(f"Error writing Excel: {e}")
            import traceback
            traceback.print_exc()
            return False