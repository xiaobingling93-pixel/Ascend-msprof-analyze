from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.excel_config import ExcelConfig
from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder


class OperatorCompareBean:
    TABLE_NAME = Constant.OPERATOR_TABLE
    HEADERS = ExcelConfig.HEADERS.get(TABLE_NAME)
    OVERHEAD = ExcelConfig.OVERHEAD.get(TABLE_NAME)

    def __init__(self, index: int, base_op: TorchOpNode, comparison_op: TorchOpNode):
        self._index = index
        self._base_op = OperatorInfo(base_op)
        self._comparison_op = OperatorInfo(comparison_op)

    @property
    def row(self):
        row = [self._index + 1, self._base_op.operator_name, self._base_op.input_shape, self._base_op.input_type,
               self._base_op.kernel_details, self._base_op.device_dur, self._comparison_op.operator_name,
               self._comparison_op.input_shape, self._comparison_op.input_type, self._comparison_op.kernel_details,
               self._comparison_op.device_dur]
        diff_fields = calculate_diff_ratio(self._base_op.device_dur, self._comparison_op.device_dur)
        row.extend(diff_fields)
        return row


class OperatorInfo:
    def __init__(self, torch_op: TorchOpNode):
        self.operator_name = None
        self.input_shape = None
        self.input_type = None
        self.device_dur = 0
        self.kernel_details = ""
        self._kernel_list = []
        if torch_op:
            self.operator_name = torch_op.name
            self.input_shape = torch_op.input_shape
            self.input_type = torch_op.input_type
            self._kernel_list = TreeBuilder.get_total_kernels(torch_op)
        self._update_kernel_fields()

    def _update_kernel_fields(self):
        for kernel in self._kernel_list:
            self.device_dur += kernel.device_dur
            self.kernel_details += kernel.kernel_details
