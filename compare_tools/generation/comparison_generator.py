from comparator.index_comparator import IndexComparator
from comparator.op_comparator import OpComparator
from generation.communication_compare_generator import CommunicationCompareGenerator
from generation.memory_compare_generator import MemoryCompareGenerator
from generation.memory_statistic_generator import MemoryStatisticGenerator
from generation.operator_compare_generator import OperatorCompareGenerator
from generation.operator_statistic_generator import OperatorStatisticGenerator
from view.excel_view import ExcelViewer
from utils.constant import Constant
from utils.args_manager import ArgsManager
from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder


class ComparisonGenerator:
    def __init__(self, args: any):
        self._args = args
        self._args_manager = ArgsManager()

    def run(self, file_path: str):
        data_dict = {}
        if self._args.enable_operator_compare or self._args.enable_memory_compare:
            op_compare_result = OpComparator(self._args).compare()
        if self._args.enable_communication_compare:
            index_compare_result = IndexComparator(self._args).compare()
            data_dict[Constant.COMMUNICATION_SHEET] = CommunicationCompareGenerator(index_compare_result).generate_data()
        if self._args.enable_operator_compare:
            data_dict[Constant.OPERATOR_SHEET] = OperatorCompareGenerator(op_compare_result).generate_data()
            data_dict[Constant.OPERATOR_TOP_SHEET] = OperatorStatisticGenerator(op_compare_result).generate_data()
        if self._args.enable_memory_compare:
            data_dict[Constant.MEMORY_SHEET] = MemoryCompareGenerator(op_compare_result).generate_data()
            data_dict[Constant.MEMORY_TOP_SHEET] = MemoryStatisticGenerator(op_compare_result).generate_data()
        ExcelViewer(data_dict, file_path).generate_view()
