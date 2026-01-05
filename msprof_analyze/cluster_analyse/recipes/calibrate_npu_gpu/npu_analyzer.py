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
from collections import defaultdict, deque

from msprof_analyze.cluster_analyse.common_func.excel_utils import ExcelUtils
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_exports.module_statistic_export import FrameworkOpToKernelExport, ModuleMstxRangeExport
from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class NodeType:
    MODULE_EVENT_NODE = 0
    CPU_OP_EVENT = 1
    KERNEL_EVENT = 2


class TreeNode:
    def __init__(self, start, end, node_type, name):
        self.start = start
        self.end = end
        self.node_type = node_type
        self.name = name
        self.children = []

    def add_child(self, node):
        self.children.append(node)


class NPUAnalyzer:
    """分析 NPU Ascend PyTorch Profiler DB 文件"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._recipe_name = "ms_custom"

    def analyze(self):
        """执行分析，返回统计 DataFrame"""
        params = {
            Constant.COLLECTION_PATH: "",
            Constant.DATA_MAP: {},
            Constant.RECIPE_NAME: self._recipe_name,
            Constant.PARALLEL_MODE: "",
            Constant.EXPORT_TYPE: "excel",
            Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "",
            Constant.RANK_LIST: "all"
        }

        # 使用原 analyze_npu.py 中的 ModuleStatisticCustom 类
        # 由于该类依赖于 BaseRecipeAnalysis，我们直接复制其核心逻辑
        # 这里简化处理：调用自定义的 _custom_mapper_func
        data_map = {"RANK_ID": 0, "profiler_db_path": self.db_path}
        rank_id, stat_df, verbose_df, module_df, kernel_df = self._custom_mapper_func(data_map)
        return stat_df

    def _custom_mapper_func(self, data_map):
        """基于原 ModuleStatisticCustom.custom_mapper_func"""
        profiler_db_path = data_map.get("profiler_db_path")
        rank_id = data_map.get("RANK_ID")

        # 导出 module 范围事件
        module_export = ModuleMstxRangeExport(profiler_db_path, self._recipe_name)
        module_df = module_export.read_export_db()
        if module_df is None or module_df.empty:
            logger.error(f"Cannot export mstx range event from rank {rank_id}")
            return rank_id, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 导出 kernel 到 op 映射
        kernel_df = self._query_framework_op_to_kernel(profiler_db_path)
        if kernel_df is None or kernel_df.empty:
            logger.error(f"Cannot export framework op to kernel mapper from rank {rank_id}")
            return rank_id, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 转换时间列为整数
        mstx_time_columns = ['startNs', 'endNs']
        module_df[mstx_time_columns] = module_df[mstx_time_columns].astype(int)
        kernel_time_columns = ['kernel_ts', 'kernel_end', 'op_ts', 'op_end']
        kernel_df[kernel_time_columns] = kernel_df[kernel_time_columns].astype(int)

        # 构建树
        root = self._build_node_tree(module_df, kernel_df)
        if not root:
            logger.error(f"Empty event tree for rank {rank_id}")
            return rank_id, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 扁平化为 DataFrame
        verbose_df = self._flatten_tree_to_dataframe(root)
        if verbose_df.empty:
            logger.error(f"Failed to extract event tree data for rank {rank_id}")
            return rank_id, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 聚合统计
        stat_df = self._aggregate_module_operator_stats(verbose_df.copy())
        return rank_id, stat_df, verbose_df, module_df, kernel_df

    def _query_framework_op_to_kernel(self, profiler_db_path):
        """查询框架 op 到 kernel 的映射"""
        KERNEL_RELATED_TABLE_LIST = [Constant.TABLE_COMPUTE_TASK_INFO, Constant.TABLE_COMMUNICATION_OP,
                                     Constant.TABLE_COMMUNICATION_SCHEDULE_TASK_INFO]
        valid_dfs = []
        for table_name in KERNEL_RELATED_TABLE_LIST:
            if not DBManager.check_tables_in_db(profiler_db_path, table_name):
                continue
            export = FrameworkOpToKernelExport(profiler_db_path, self._recipe_name, table_name)
            df = export.read_export_db()
            if df is not None and not df.empty:
                valid_dfs.append(df)
        if not valid_dfs:
            return None
        try:
            return pd.concat(valid_dfs, ignore_index=True)
        except Exception as e:
            logger.error(f"Failed to concatenate framework op to kernel dataframes: {str(e)}")
            return None

    def _build_node_tree(self, module_df, kernel_df):
        """构建事件树（同原 _build_node_tree）"""
        nodes = []

        # 1. 创建mstx节点
        for _, row in module_df.iterrows():
            nodes.append(TreeNode(
                row['startNs'],
                row['endNs'],
                NodeType.MODULE_EVENT_NODE,
                row['name']
            ))

        # 2. 按op_name分组处理kernel数据
        op_groups = defaultdict(list)
        for _, row in kernel_df.iterrows():
            op_groups[(row['op_name'], row['op_ts'], row['op_end'])].append(row)

        # 3. 创建op节点和对应的kernel节点
        for (op_name, op_ts, op_end), kernels in op_groups.items():
            # 创建op节点
            op_node = TreeNode(
                op_ts,
                op_end,
                NodeType.CPU_OP_EVENT,
                op_name
            )

            # 为每个op添加对应的kernel节点
            for kernel in kernels:
                kernel_node = TreeNode(
                    kernel['kernel_ts'],
                    kernel['kernel_end'],
                    NodeType.KERNEL_EVENT,
                    kernel['kernel_name']
                )
                op_node.add_child(kernel_node)

            nodes.append(op_node)

        if not nodes:
            logger.error(f"Empty node (module_event/cpu_op/kernel), skipping tree build")
            return None

        # 4. 按开始时间升序、结束时间降序排序
        nodes.sort(key=lambda x: (x.start, -x.end))

        # 5. 构建树结构
        root = self._create_root_node(module_df, kernel_df)
        stack = [root]

        for node in nodes:
            # 找到最近的能包含当前节点的父节点
            while stack[-1].start > node.start or stack[-1].end < node.end:
                stack.pop()

            # 添加到父节点的children中
            stack[-1].add_child(node)
            stack.append(node)

        return root

    def _create_root_node(self, module_df, kernel_df):
        global_start = min(module_df['startNs'].min(), kernel_df['kernel_ts'].min(), kernel_df['op_ts'].min())
        global_end = max(module_df['endNs'].max(), kernel_df['kernel_end'].max(), kernel_df['op_end'].max())
        root = TreeNode(global_start, global_end, NodeType.MODULE_EVENT_NODE, "")
        return root

    def _flatten_tree_to_dataframe(self, root_node):
        """扁平化树为 DataFrame（同原 _flatten_tree_to_dataframe）"""
        results = []

        def traverse(node, module_deque, depth=0):
            if depth > 20:  # MAX_TRAVERSE_DEPTH
                logger.warning(f"Max traversal depth 20 reached, traversal stopped. "
                               f"Some information may be lost")
                return
            if node.node_type != NodeType.MODULE_EVENT_NODE:
                return
            for op_child in node.children:
                if op_child.node_type == NodeType.MODULE_EVENT_NODE:
                    module_deque.append(node.name)
                    traverse(op_child, module_deque, depth + 1)
                    module_deque.pop()
                if op_child.node_type == NodeType.CPU_OP_EVENT:
                    module = node.name
                    module_parent = "/".join(module_deque)
                    # 跳过没有module归属的op
                    if not module and not module_parent:
                        continue
                    # 收集该op下的所有kernel信息
                    kernel_names = []
                    total_device_time = 0.0
                    for kernel_child in op_child.children:
                        if kernel_child.node_type == NodeType.KERNEL_EVENT:
                            kernel_names.append(kernel_child.name)
                            duration = kernel_child.end - kernel_child.start
                            total_device_time += duration
                    results.append({
                        'module_parent': module_parent,
                        'module': module,
                        'module_start': node.start,
                        'module_end': node.end,
                        'op_name': op_child.name,
                        'op_start': op_child.start,
                        'op_end': op_child.end,
                        'kernel_list': ', '.join(kernel_names),
                        'device_time': total_device_time
                    })

        traverse(root_node, deque(), 0)
        if not results:
            return pd.DataFrame()
        # 转换为DataFrame并排序
        df = pd.DataFrame(results)
        df = df.sort_values(by=['module_start', 'op_start'], ascending=[True, True])
        return df

    def _aggregate_module_operator_stats(self, df):
        """聚合模块和算子统计（同原 _aggregate_module_operator_stats）"""
        # df = verbose_df.copy()
        if df is None or df.empty:
            logger.warning("Empty dataframe received for aggregation")
            return pd.DataFrame()

        stat_df = (
            df.groupby(['module_parent', 'module', 'op_name', 'kernel_list'])
            .agg(
                module_start=('module_start', 'first'),  # 取第一个 module_start
                op_start=('op_start', 'first'),  # 取第一个 op_start
                total_kernel_duration=('device_time', 'sum'),  # 计算 device_time 的总时间
                avg_kernel_duration=('device_time', 'mean'),  # 计算 device_time 的平均时间
                op_count=('device_time', 'count')  # 计算每组的行数（计数）
            ).reset_index()
        )

        # stat_df = stat_df.sort_values(by=['module_start', 'op_start']).reset_index(drop=True)
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