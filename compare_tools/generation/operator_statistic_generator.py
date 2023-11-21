from generation.base_generator import BaseGenerator
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.tree_builder import TreeBuilder


class OperatorStatisticGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.OPERATOR_TOP_SHEET, data)

    def generate_data(self):
        base_op_dict, comparison_op_dict = {}, {}
        for base_op, comparison_op in self.data:
            if base_op:
                kernel_list = TreeBuilder.get_total_kernels(base_op)
                duration = sum([kernel.device_dur / Constant.US_TO_MS for kernel in kernel_list])
                base_op_dict.setdefault(base_op.name, []).append(duration)
            if comparison_op:
                kernel_list = TreeBuilder.get_total_kernels(comparison_op)
                duration = sum([kernel.device_dur / Constant.US_TO_MS for kernel in kernel_list])
                comparison_op_dict.setdefault(comparison_op.name, []).append(duration)
        result_data = []
        for op_name, base_duration_list in base_op_dict.items():
            base_dur = sum(base_duration_list)
            comparison_duration_list = comparison_op_dict.pop(op_name, None)
            if comparison_duration_list:
                comparison_dur = sum(comparison_duration_list)
                result_data.append(
                    [op_name, base_dur, len(base_duration_list), comparison_dur,
                     len(comparison_duration_list)] + calculate_diff_ratio(base_dur, comparison_dur))
            else:
                result_data.append(
                    [op_name, base_dur, len(base_duration_list), 0, 0] + calculate_diff_ratio(base_dur, 0))
        for op_name, comparison_duration_list in comparison_op_dict.items():
            comparison_dur = sum(comparison_duration_list)
            result_data.append([op_name, 0, 0, comparison_dur, len(comparison_duration_list)] +
                               calculate_diff_ratio(0, comparison_dur))
        result_data.sort(key=lambda x: x[-2], reverse=True)
        return result_data
