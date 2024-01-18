from compare_backend.utils.common_func import calculate_diff_ratio
from compare_backend.utils.constant import Constant
from compare_backend.utils.excel_config import ExcelConfig
from compare_backend.utils.torch_op_node import TorchOpNode
from compare_backend.utils.tree_builder import TreeBuilder


class MemoryCompareBean:
    TABLE_NAME = Constant.MEMORY_TABLE
    HEADERS = ExcelConfig.HEADERS.get(TABLE_NAME)
    OVERHEAD = ExcelConfig.OVERHEAD.get(TABLE_NAME)

    def __init__(self, index: int, base_op: TorchOpNode, comparison_op: TorchOpNode):
        self._index = index
        self._base_op = MemoryInfo(base_op)
        self._comparison_op = MemoryInfo(comparison_op)

    @property
    def row(self):
        row = [self._index + 1, self._base_op.operator_name, self._base_op.input_shape, self._base_op.input_type,
               self._base_op.memory_details, self._base_op.size, self._comparison_op.operator_name,
               self._comparison_op.input_shape, self._comparison_op.input_type, self._comparison_op.memory_details,
               self._comparison_op.size]
        diff_fields = calculate_diff_ratio(self._base_op.size, self._comparison_op.size)
        row.extend(diff_fields)
        return row


class MemoryInfo:
    def __init__(self, torch_op: TorchOpNode):
        self.operator_name = None
        self.input_shape = None
        self.input_type = None
        self.size = 0
        self.memory_details = ""
        self._memory_list = []
        if torch_op:
            self.operator_name = torch_op.name
            self.input_shape = torch_op.input_shape
            self.input_type = torch_op.input_type
            self._memory_list = TreeBuilder.get_total_memory(torch_op)
        self._update_memory_fields()

    def _update_memory_fields(self):
        for memory in self._memory_list:
            self.size += memory.size
            self.memory_details += memory.memory_details
