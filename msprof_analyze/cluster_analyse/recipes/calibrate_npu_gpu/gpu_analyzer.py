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

import pandas as pd
from collections import defaultdict
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_exports.calibrate_npu_gpu_export import GPUNVTXEventsExport, GPUKernelExport

logger = get_logger()


class GPUAnalyzer:
    def __init__(self, gpu_db_path, recipe_name):
        self.gpu_db_path = gpu_db_path
        self.recipe_name = recipe_name

    def load_data(self):
        nvtx_event_export = GPUNVTXEventsExport(self.gpu_db_path, self.recipe_name)
        df_nvtx = nvtx_event_export.read_export_db()
        if df_nvtx is None or df_nvtx.empty:
            logger.error(f"Can not export nvtx events from {self.gpu_db_path}")
            return None, None

        gpu_kernel_export = GPUKernelExport(self.gpu_db_path, self.recipe_name)
        df_kernels = gpu_kernel_export.read_export_db()
        if df_kernels is None or df_kernels.empty:
            logger.error(f"Can not export CUDA kernel events from {self.gpu_db_path}")
            return None, None

        return df_nvtx, df_kernels

    def process_hierarchy(self, df_nvtx, df_kernels, user_def_markers=None):
        if user_def_markers is None:
            user_def_markers = ['Qwen', 'Attention', 'Linear', 'RMSNorm', 'Embedding', 'Sampler', 'Logits']

        TYPE_PUSH = 1
        TYPE_POP = -1
        TYPE_KERNEL = 0

        nvtx_push = [
            (row.start_ns, TYPE_PUSH, row.thread_id, row.name, None)
            for row in df_nvtx.itertuples(index=False)
        ]
        nvtx_pop = [
            (row.end_ns, TYPE_POP, row.thread_id, None, None)
            for row in df_nvtx.itertuples(index=False)
        ]
        kernel_events = [
            (row.cpu_start_ns, TYPE_KERNEL, row.thread_id, (row.kernel_name, row.gpu_duration_ns), row.rank_id)
            for row in df_kernels.itertuples(index=False)
        ]

        all_events = nvtx_push + nvtx_pop + kernel_events
        all_events.sort(key=lambda x: x[0])

        unique_names = df_nvtx['name'].unique()
        marker_cache = {}
        op_cache = {}

        for name in unique_names:
            if not isinstance(name, str):
                marker_cache[name] = False
                op_cache[name] = None
                continue

            is_marker = False
            for m in user_def_markers:
                if m in name:
                    is_marker = True
                    break
            marker_cache[name] = is_marker

            if "::" in name:
                op_cache[name] = name.split(',')[0]
            else:
                op_cache[name] = None

        results = defaultdict(list)

        class ThreadState:
            def __init__(self):
                self.full_stack = []
                self.filtered_stack = []
                self.op_stack = []

        thread_states = defaultdict(ThreadState)

        for time_ns, event_type, tid, payload, rank_id in all_events:
            state = thread_states[tid]

            if event_type == TYPE_PUSH:
                name = payload
                state.full_stack.append(name)

                if marker_cache.get(name, False):
                    state.filtered_stack.append(name)

                op_val = op_cache.get(name)
                if op_val:
                    state.op_stack.append(op_val)

            elif event_type == TYPE_POP:
                if state.full_stack:
                    popped_name = state.full_stack.pop()

                    if marker_cache.get(popped_name, False):
                        if state.filtered_stack:
                            state.filtered_stack.pop()

                    if op_cache.get(popped_name):
                        if state.op_stack:
                            state.op_stack.pop()

            elif event_type == TYPE_KERNEL:
                kernel_name, duration = payload

                raw_op = state.op_stack[-1] if state.op_stack else "None"

                f_stack = state.filtered_stack
                len_f = len(f_stack)

                if len_f >= 2:
                    parent_module = '/' + '/'.join(f_stack[:-1])
                    module = f_stack[-1]
                elif len_f == 1:
                    parent_module = ""
                    module = f_stack[-1]
                else:
                    parent_module = ""
                    module = "No Scope"

                if module != "No Scope":
                    results[rank_id].append({
                        'Parent Module': parent_module,
                        'Module': module,
                        'Op Name': raw_op,
                        'Kernel Name': kernel_name,
                        'Duration (ns)': duration
                    })

        return {tid: pd.DataFrame(result) for tid, result in results.items()}

    def analyze(self):
        df_nvtx, df_kernels = self.load_data()
        if df_nvtx is None or df_kernels is None:
            logger.error("Failed to load data.")
            return None
        df_dict = self.process_hierarchy(df_nvtx, df_kernels)
        return df_dict
    
    def get_aggregated_df(self):
        df_dict = self.analyze()
        final_df_dict = {}
        for tid, df in df_dict.items():
            grouped = df.groupby(['Parent Module', 'Module', 'Op Name', 'Kernel Name']).agg(
                Total_Time_ns=('Duration (ns)', 'sum'),
                Count=('Duration (ns)', 'count')
            ).reset_index()
            grouped['Avg_Time_ns'] = grouped['Total_Time_ns'] / grouped['Count']

            grouped = grouped.sort_values(
                by=['Parent Module', 'Module', 'Op Name', 'Total_Time_ns'],
                ascending=[True, True, True, False]
            )
            
            final_df = grouped[['Parent Module', 'Module', 'Op Name', 'Kernel Name',
                            'Total_Time_ns', 'Avg_Time_ns', 'Count']]

            final_df = final_df.rename(columns={'Kernel Name': 'Kernel List',
                                                'Total_Time_ns': 'Total Kernel Duration(ns)',
                                                'Avg_Time_ns': 'Avg Kernel Duration(ns)',
                                                'Count': 'Op Count'})
            final_df = final_df.set_index(['Parent Module', 'Module', 'Op Name'])
            final_df_dict[tid] = final_df
        return final_df_dict
