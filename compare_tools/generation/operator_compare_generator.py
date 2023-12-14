from generation.base_generator import BaseGenerator
from utils.args_manager import ArgsManager
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder


class OperatorCompareGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.OPERATOR_SHEET, data)

    def generate_data(self):
        def get_row_info(torch_op_node: TorchOpNode):
            if not torch_op_node:
                return [None] * 4 + [0]
            kernel_list = TreeBuilder.get_total_kernels(torch_op_node)
            duration = 0
            kernel_details = ""
            for kernel in kernel_list:
                duration += kernel.device_dur
                kernel_details += kernel.kernel_details
            return [torch_op_node.name, torch_op_node.input_shape, torch_op_node.input_type, kernel_details, duration]

        if not self.data:
            return []
        data = [None] * (len(self.data))
        index = 0
        for base_op, comparison_op in self.data:
            base_row = get_row_info(base_op)
            if ArgsManager().base_profiling_path == ArgsManager().comparison_profiling_path:
                comparison_row = [None] * 5
                diff_ratio = [None] * 2
            else:
                comparison_row = get_row_info(comparison_op)
                diff_ratio = calculate_diff_ratio(base_row[-1], comparison_row[-1])
            data[index] = base_row + comparison_row + diff_ratio
            index += 1
        return data
