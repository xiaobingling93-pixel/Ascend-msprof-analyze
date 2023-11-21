from generation.base_generator import BaseGenerator
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder


class MemoryCompareGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.MEMORY_SHEET, data)

    def generate_data(self):
        def get_row_info(torch_op_node: TorchOpNode):
            if not torch_op_node:
                return [None] * 4 + [0]
            memory_list = TreeBuilder.get_total_memory(torch_op_node)
            size = 0
            memory_details = ""
            for memory in memory_list:
                size += memory.size
                memory_details += memory.memory_details
            return [torch_op_node.name, torch_op_node.input_shape, torch_op_node.input_type, memory_details, size]

        if not self.data:
            return []
        data = [None] * (len(self.data))
        for index, (base_op, comparison_op) in enumerate(self.data):
            base_row = get_row_info(base_op)
            comparison_row = get_row_info(comparison_op)
            diff_ratio = calculate_diff_ratio(base_row[-1], comparison_row[-1])
            data[index] = base_row + comparison_row + diff_ratio
        return data
