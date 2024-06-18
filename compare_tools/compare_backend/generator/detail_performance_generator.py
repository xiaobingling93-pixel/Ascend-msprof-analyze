import os
from collections import deque
from datetime import datetime
from queue import Queue

from compare_backend.comparator.communication_comparator import CommunicationComparator
from compare_backend.comparator.module_comparetor import ModuleComparator
from compare_backend.comparator.module_statistic_comparator import ModuleStatisticComparator
from compare_backend.comparator.operator_comparator import OperatorComparator
from compare_backend.comparator.operator_statistic_comparator import OperatorStatisticComparator
from compare_backend.compare_bean.communication_bean import CommunicationBean
from compare_backend.compare_bean.memory_compare_bean import MemoryCompareBean
from compare_backend.compare_bean.memory_statistic_bean import MemoryStatisticBean
from compare_backend.compare_bean.module_compare_bean import ModuleCompareBean
from compare_backend.compare_bean.module_statistic_bean import ModuleStatisticBean
from compare_backend.compare_bean.operator_compare_bean import OperatorCompareBean
from compare_backend.compare_bean.operator_statistic_bean import OperatorStatisticBean
from compare_backend.data_prepare.module_data_prepare import ModuleDataPrepare
from compare_backend.data_prepare.operator_data_prepare import OperatorDataPrepare
from compare_backend.generator.base_generator import BaseGenerator
from compare_backend.utils.common_func import longest_common_subsequence_matching
from compare_backend.utils.constant import Constant
from compare_backend.utils.module_node import ModuleNode
from compare_backend.utils.name_function import NameFunction
from compare_backend.utils.torch_op_node import TorchOpNode
from compare_backend.view.excel_view import ExcelView


class DetailPerformanceGenerator(BaseGenerator):
    def __init__(self, profiling_data_dict: dict, args: any):
        super().__init__(profiling_data_dict, args)

    @classmethod
    def _match_none_subsequence(cls, base_ops: list, comparison_ops: list) -> list:
        op_compare_result = [[op, None] for op in iter(base_ops)]
        op_compare_result.extend([[None, op] for op in iter(comparison_ops)])
        return op_compare_result

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

        op_compare_result = []
        if self._args.enable_operator_compare:
            module_compare_result = self.match_nn_module() if self._profiling_data_dict.get(
                Constant.BASE_DATA).python_function_data and self._profiling_data_dict.get(
                Constant.COMPARISON_DATA).python_function_data else []
            if not module_compare_result:
                op_compare_result = self.match_torch_op()

        if self._args.enable_memory_compare and not op_compare_result:
            op_compare_result = self.match_torch_op()

        if self._args.enable_communication_compare:
            communication_data = {
                Constant.BASE_DATA: self._profiling_data_dict.get(Constant.BASE_DATA).communication_dict,
                Constant.COMPARISON_DATA: self._profiling_data_dict.get(Constant.COMPARISON_DATA).communication_dict}
            comparator_list.append(CommunicationComparator(communication_data, CommunicationBean))

        if self._args.enable_operator_compare:
            if module_compare_result:
                comparator_list.append(ModuleStatisticComparator(module_compare_result, ModuleStatisticBean))
                if not self._args.disable_details:
                    comparator_list.append(ModuleComparator(module_compare_result, ModuleCompareBean))
            else:
                comparator_list.append(OperatorStatisticComparator(op_compare_result, OperatorStatisticBean))
                if not self._args.disable_details:
                    comparator_list.append(OperatorComparator(op_compare_result, OperatorCompareBean))
        if self._args.enable_memory_compare:
            comparator_list.append(OperatorStatisticComparator(op_compare_result, MemoryStatisticBean))
            if not self._args.disable_details:
                comparator_list.append(OperatorComparator(op_compare_result, MemoryCompareBean))
        return comparator_list

    def match_torch_op(self) -> list:
        base_ops = OperatorDataPrepare(self._profiling_data_dict.get(Constant.BASE_DATA)).get_top_layer_ops()
        comparison_ops = OperatorDataPrepare(
            self._profiling_data_dict.get(Constant.COMPARISON_DATA)).get_top_layer_ops()
        if not base_ops and not comparison_ops:
            return []
        name_func = NameFunction(self._args).get_name_func()
        op_compare_result = longest_common_subsequence_matching(base_ops, comparison_ops, name_func) \
            if not self._args.disable_details else self._match_none_subsequence(base_ops, comparison_ops)
        if self._args.max_kernel_num is not None:
            op_compare_result = self._drill_down(op_compare_result, name_func)
        return op_compare_result

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
            match_list = longest_common_subsequence_matching(base_op.child_nodes,
                                                             comparison_op.child_nodes,
                                                             name_func) \
                if not self._args.disable_details else self._match_none_subsequence(base_op.child_nodes,
                                                                                    comparison_op.child_nodes)
            match_list.reverse()
            for data in match_list:
                op_deque.append(data)

        return drill_down_result

    def match_nn_module(self) -> list:
        module_compare_result = []
        base_root_node = ModuleDataPrepare(self._profiling_data_dict.get(Constant.BASE_DATA)).build_module_tree()
        comparison_root_node = ModuleDataPrepare(
            self._profiling_data_dict.get(Constant.COMPARISON_DATA)).build_module_tree()
        for index, base_node in enumerate(base_root_node):
            comparison_node = comparison_root_node[index] if index < len(comparison_root_node) else None
            if not base_node or not comparison_node:
                continue
            module_compare_result.extend(self._matching_all_modules(base_node, comparison_node))
        return module_compare_result

    def _matching_all_modules(self, base_node: ModuleNode, comparison_node: ModuleNode):
        all_matched_modules = []
        matched_queue = Queue()
        matched_queue.put([base_node, comparison_node])
        while not matched_queue.empty():
            matched_base_node, matched_comparison_node = matched_queue.get()
            matched_node_list = self._matching_common_subsequence(matched_base_node, matched_comparison_node)
            all_matched_modules.extend(matched_node_list)
            for matched_node in matched_node_list:
                matched_queue.put(matched_node)
        return all_matched_modules

    def _matching_common_subsequence(self, base_node: ModuleNode, comparison_node: ModuleNode):
        base_modules = base_node.child_nodes if base_node else []
        comparison_modules = comparison_node.child_nodes if comparison_node else []
        if not base_modules and not comparison_modules:
            return []
        name_func = NameFunction(self._args).get_module_name
        result = longest_common_subsequence_matching(base_modules, comparison_modules, name_func) \
            if not self._args.disable_details else self._match_none_subsequence(base_modules, comparison_modules)
        return result
