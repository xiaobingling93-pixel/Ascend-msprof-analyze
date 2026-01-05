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

import argparse
import os
import pandas as pd
import sqlite3
from collections import defaultdict
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()

class GPUAnalyzer:
    """分析 GPU Nsys SQLite profile 文件"""

    def __init__(self, sqlite_path):
        self.sqlite_path = sqlite_path

    def load_data(self):
        """从 SQLite 文件加载 NVTX 和 Kernel 数据"""
        conn = sqlite3.connect(self.sqlite_path)

        query_nvtx = """
        SELECT
            n.start AS start_ns,
            n.end AS end_ns,
            n.globalTid AS thread_id,
            COALESCE(n.text, s.value, 'Unknown_Region') as name
        FROM NVTX_EVENTS AS n
        LEFT JOIN StringIds AS s ON n.textId = s.id
        WHERE n.eventType = 59
        ORDER BY n.start
        """

        query_kernels = """
        SELECT
            r.start AS cpu_start_ns,
            r.globalTid AS thread_id,
            k.start AS gpu_start_ns,
            k.end - k.start AS gpu_duration_ns,
            s.value AS kernel_name
        FROM CUPTI_ACTIVITY_KIND_RUNTIME AS r
        JOIN CUPTI_ACTIVITY_KIND_KERNEL AS k
            ON r.correlationId = k.correlationId
        LEFT JOIN StringIds AS s ON k.demangledName = s.id
        """

        try:
            df_nvtx = pd.read_sql_query(query_nvtx, conn)
            df_kernels = pd.read_sql_query(query_kernels, conn)

            if df_nvtx.empty:
                logger.warning("Warning: No NVTX events found. Check if --trace=nvtx was enabled and logic ran.")
            if df_kernels.empty:
                logger.warning("Warning: No Kernels found. Check if CUDA code actually ran.")

        except Exception as e:
            logger.error(f"Error reading database: {e}")
            conn.close()
            return None, None

        conn.close()
        return df_nvtx, df_kernels

    def process_hierarchy(self, df_nvtx, df_kernels, user_def_markers=None):
        """处理层次结构，关联 NVTX 范围和 Kernel"""
        if user_def_markers is None:
            user_def_markers = ['Qwen', 'Attention', 'Linear', 'RMSNorm', 'Embedding', 'Sampler', 'Logits']

        # 1. 预处理：将 DataFrames 转换为统一的事件列表
        # 使用 list comprehension 和 itertuples 替代 iterrows，速度极快

        # NVTX Push 事件
        nvtx_push = [
            (row.start_ns, 1, row.thread_id, row.name)
            for row in df_nvtx.itertuples(index=False)
        ]
        # NVTX Pop 事件 (使用 end_ns)
        nvtx_pop = [
            (row.end_ns, -1, row.thread_id, None)
            for row in df_nvtx.itertuples(index=False)
        ]
        # Kernel 事件 (使用 cpu_start_ns)
        # 结构: (time, type, thread_id, (kernel_name, duration))
        # type=0 用于 Kernel，为了排序稳定性，我们将 Kernel 放在 Push(1) 之后，Pop(-1) 之前
        # 但实际上时间戳是主序。如果时间戳完全相同，我们希望先 Push 进栈，再记录 Kernel，再 Pop。
        # 这里 type 设为 0，排序逻辑需要注意：通常 CPU 启动 Kernel 都在 NVTX 范围内部。
        kernel_events = [
            (row.cpu_start_ns, 0, row.thread_id, (row.kernel_name, row.gpu_duration_ns))
            for row in df_kernels.itertuples(index=False)
        ]

        # 合并并排序所有事件
        # 排序优先级: 时间 -> 类型 (Push(1) -> Kernel(0) -> Pop(-1))
        # 注意：如果时间完全相等，我们希望顺序是: Push -> Kernel -> Pop
        # 为了实现这个顺序，我们可以调整 type 的值：Push=1, Kernel=2, Pop=3 (仅用于排序逻辑)
        # 但简单按时间排通常足够，因为 CPU 时间戳通常不会完全碰撞。
        all_events = nvtx_push + nvtx_pop + kernel_events
        all_events.sort(key=lambda x: x[0])

        # 2. 字符串匹配缓存 (避免在循环中重复做 string in string)
        # 只需要对唯一的 NVTX name 做判断
        unique_names = df_nvtx['name'].unique()
        marker_cache = {}  # {name: True/False}
        aten_cache = {}  # {name: clean_aten_name or None}

        for name in unique_names:
            if not isinstance(name, str):
                marker_cache[name] = False
                aten_cache[name] = None
                continue

            # 检查是否是 Marker
            is_marker = False
            for m in user_def_markers:
                if m in name:
                    is_marker = True
                    break
            marker_cache[name] = is_marker

            # 检查是否是 Aten op
            if "aten::" in name:
                aten_cache[name] = name.split(',')[0]
            else:
                aten_cache[name] = None

        # 3. 核心循环：使用增量栈
        results = []

        # 状态存储: {thread_id: StackState}
        # 我们维护两个栈：
        # full_stack: 原始 NVTX 栈，用于处理 Pop 逻辑
        # filtered_stack: 仅包含 marker 的栈，用于快速生成 Module 路径
        # aten_stack: 仅包含 aten op 的栈，用于快速获取 Op
        class ThreadState:
            def __init__(self):
                self.full_stack = []  # List[name]
                self.filtered_stack = []  # List[name]
                self.aten_stack = []  # List[clean_name]

        thread_states = defaultdict(ThreadState)

        # 常量定义，避免魔法数字
        TYPE_PUSH = 1
        TYPE_POP = -1
        TYPE_KERNEL = 0

        for time_ns, event_type, tid, payload in all_events:
            state = thread_states[tid]

            if event_type == TYPE_PUSH:
                name = payload
                state.full_stack.append(name)

                # 增量维护 filtered_stack
                if marker_cache.get(name, False):
                    state.filtered_stack.append(name)

                # 增量维护 aten_stack
                aten_val = aten_cache.get(name)
                if aten_val:
                    state.aten_stack.append(aten_val)

            elif event_type == TYPE_POP:
                if state.full_stack:
                    popped_name = state.full_stack.pop()

                    # 对应的弹出 filtered_stack
                    if marker_cache.get(popped_name, False):
                        if state.filtered_stack:
                            state.filtered_stack.pop()

                    # 对应的弹出 aten_stack
                    if aten_cache.get(popped_name):
                        if state.aten_stack:
                            state.aten_stack.pop()

            elif event_type == TYPE_KERNEL:
                # 此时不需要任何循环查找，状态已经在 O(1) 内准备好了
                kernel_name, duration = payload

                # 获取 Op
                raw_aten_op = state.aten_stack[-1] if state.aten_stack else "None"

                # 获取 Module
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
                    results.append({
                        'Parent Module': parent_module,
                        'Module': module,
                        'Op': raw_aten_op,
                        'Kernel Name': kernel_name,
                        'Duration (ns)': duration
                    })

        return pd.DataFrame(results)

    def analyze(self):
        """执行分析，返回 DataFrame"""
        df_nvtx, df_kernels = self.load_data()
        if df_nvtx is None or df_kernels is None:
            logger.error("Failed to load data.")
            return None
        df = self.process_hierarchy(df_nvtx, df_kernels)
        return df
    
    def get_aggregated_df(self):
        """导出 Excel 报告"""
        df = self.analyze()
        if df is None or df.empty:
            logger.error("No data to export.")
            return False

        # 分组聚合
        grouped = df.groupby(['Parent Module', 'Module', 'Op', 'Kernel Name']).agg(
            Total_Time_ns=('Duration (ns)', 'sum'),
            Count=('Duration (ns)', 'count')
        ).reset_index()
        grouped['Avg_Time_ns'] = grouped['Total_Time_ns'] / grouped['Count']

        grouped = grouped.sort_values(
            by=['Parent Module', 'Module', 'Op', 'Total_Time_ns'],
            ascending=[True, True, True, False]
        )

        final_df = grouped[['Parent Module', 'Module', 'Op', 'Kernel Name',
                           'Total_Time_ns', 'Avg_Time_ns', 'Count']]
        final_df = final_df.rename(columns={'Op': 'Op Name',
                                            'Total_Time_ns': 'Total Time (ns)',
                                            'Avg_Time_ns': 'Avg Time (ns)'})
        final_df = final_df.set_index(['Parent Module', 'Module', 'Op Name'])
        return final_df