import os
from collections import deque
from datetime import datetime

import numpy as np

from comparator.communication_comparator import CommunicationComparator
from comparator.operator_comparator import OperatorComparator
from comparator.operator_statistic_comparator import OperatorStatisticComparator
from compare_bean.communication_bean import CommunicationBean
from compare_bean.memory_compare_bean import MemoryCompareBean
from compare_bean.memory_statistic_bean import MemoryStatisticBean
from compare_bean.operator_compare_bean import OperatorCompareBean
from compare_bean.operator_statistic_bean import OperatorStatisticBean
from generator.base_generator import BaseGenerator
from profiling_parser.base_profiling_parser import ProfilingResult
from utils.constant import Constant
from utils.name_function import NameFunction
from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder
from view.excel_view import ExcelView


class DetailPerformanceGenerator(BaseGenerator):
    def __init__(self, profiling_data_dict: dict, args: any):
        super().__init__(profiling_data_dict, args)

    def compare(self):
        if self._args.enable_operator_compare or self._args.enable_memory_compare or \
                self._args.enable_communication_compare:
            print("[INFO] Start to compare performance detail data, please wait.")
            comparator_list = self._create_comparator()
            for comparator in comparator_list:
                self._result_data.update(comparator.generate_data())

    def generate_view(self):
        if not self._result_data:
            return
        dir_path = self._args.output_path if self._args.output_path else "./"
        file_name = "performance_comparison_result_{}.xlsx".format(datetime.utcnow().strftime("%Y%m%d%H%M%S"))
        result_file_path = os.path.realpath(os.path.join(dir_path, file_name))
        ExcelView(self._result_data, result_file_path, self._args).generate_view()
        print(f"[INFO] The comparison result file has been generated: {result_file_path}")

    def _create_comparator(self):
        comparator_list = []
        if self._args.enable_operator_compare or self._args.enable_memory_compare:
            op_compare_result = self.match_torch_op()

        if self._args.enable_communication_compare:
            communication_data = {
                Constant.BASE_DATA: self._profiling_data_dict.get(Constant.BASE_DATA).communication_dict,
                Constant.COMPARISON_DATA: self._profiling_data_dict.get(Constant.COMPARISON_DATA).communication_dict}
            comparator_list.append(CommunicationComparator(communication_data, CommunicationBean))

        if self._args.enable_operator_compare:
            comparator_list.append(OperatorComparator(op_compare_result, OperatorCompareBean))
            comparator_list.append(OperatorStatisticComparator(op_compare_result, OperatorStatisticBean))

        if self._args.enable_memory_compare:
            comparator_list.append(OperatorComparator(op_compare_result, MemoryCompareBean))
            comparator_list.append(OperatorStatisticComparator(op_compare_result, MemoryStatisticBean))
        return comparator_list

    def match_torch_op(self) -> list:
        base_ops = self._get_top_layer_ops(self._profiling_data_dict.get(Constant.BASE_DATA))
        comparison_ops = self._get_top_layer_ops(self._profiling_data_dict.get(Constant.COMPARISON_DATA))
        if not base_ops and not comparison_ops:
            return []
        name_func = NameFunction(self._args).get_name_func()
        compare_result_data = self._matching_op(base_ops, comparison_ops, name_func)
        if self._args.max_kernel_num is not None:
            compare_result_data = self._drill_down(compare_result_data, name_func)
        return compare_result_data

    @classmethod
    def _matching_op(cls, base_ops: list, comparison_ops: list, name_func: any) -> list:
        if not comparison_ops:
            result_data = [None] * len(base_ops)
            for index, value in enumerate(base_ops):
                result_data[index] = [value, None]
            return result_data

        result_data = []
        comparison_len, base_len = len(comparison_ops), len(base_ops)
        dp = [[0] * (base_len + 1) for _ in range(comparison_len + 1)]
        for comparison_index in range(1, comparison_len + 1):
            for base_index in range(1, base_len + 1):
                if name_func(base_ops[base_index - 1]) == name_func(
                        comparison_ops[comparison_index - 1]):
                    dp[comparison_index][base_index] = dp[comparison_index - 1][base_index - 1] + 1
                else:
                    dp[comparison_index][base_index] = max(dp[comparison_index][base_index - 1],
                                                           dp[comparison_index - 1][base_index])
        matched_op = []
        comparison_index, base_index = comparison_len, base_len
        while comparison_index > 0 and base_index > 0:
            if name_func(base_ops[base_index - 1]) == name_func(
                    comparison_ops[comparison_index - 1]):
                matched_op.append([comparison_index - 1, base_index - 1])
                comparison_index -= 1
                base_index -= 1
                continue
            if dp[comparison_index][base_index - 1] > dp[comparison_index - 1][base_index]:
                base_index -= 1
            else:
                comparison_index -= 1
        if not matched_op:
            matched_base_index_list = []
        else:
            matched_op.reverse()
            matched_op = np.array(matched_op)
            matched_base_index_list = list(matched_op[:, 1])
        curr_comparison_index = 0
        for base_index, base_api_node in enumerate(base_ops):
            if base_index not in matched_base_index_list:
                result_data.append([base_api_node, None])
                continue
            matched_comparison_index = matched_op[matched_base_index_list.index(base_index), 0]
            for comparison_index in range(curr_comparison_index, matched_comparison_index):
                result_data.append([None, comparison_ops[comparison_index]])
            result_data.append([base_api_node, comparison_ops[matched_comparison_index]])
            curr_comparison_index = matched_comparison_index + 1
        if curr_comparison_index < len(comparison_ops):
            for comparison_index in range(curr_comparison_index, len(comparison_ops)):
                result_data.append([None, comparison_ops[comparison_index]])
        return result_data

    def _get_top_layer_ops(self, profiling_data: ProfilingResult) -> any:
        root_node = TreeBuilder.build_tree(profiling_data.torch_op_data, profiling_data.kernel_dict,
                                           profiling_data.memory_list)
        level1_child_nodes = root_node.child_nodes
        result_data = []
        for level1_node in level1_child_nodes:
            if level1_node.is_step_profiler():
                result_data.extend(level1_node.child_nodes)
            else:
                result_data.append(level1_node)
        return result_data

    def _drill_down(self, compare_result_data: list, name_func: any) -> list:
        drill_down_result = []
        compare_result_data.reverse()
        op_deque = deque(compare_result_data)
        while op_deque:
            match_data = op_deque.pop()
            base_op = match_data[0] if match_data[0] else TorchOpNode()
            comparison_op = match_data[1] if match_data[1] else TorchOpNode()
            if not base_op.child_nodes or not comparison_op.child_nodes:
                drill_down_result.append(match_data)
                continue
            if max(base_op.kernel_num, comparison_op.kernel_num) <= self._args.max_kernel_num:
                drill_down_result.append(match_data)
                continue
            match_list = self._matching_op(base_op.child_nodes, comparison_op.child_nodes, name_func)
            match_list.reverse()
            for data in match_list:
                op_deque.append(data)

        return drill_down_result
