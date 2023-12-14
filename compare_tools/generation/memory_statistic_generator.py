from generation.base_generator import BaseGenerator
from utils.args_manager import ArgsManager
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.tree_builder import TreeBuilder


class MemoryStatisticGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.MEMORY_TOP_SHEET, data)

    def generate_data(self):
        base_op_dict, comparison_op_dict = {}, {}
        for base_op, comparison_op in self.data:
            if base_op:
                memory_list = TreeBuilder.get_total_memory(base_op)
                size = sum([memory.size / Constant.KB_TO_MB for memory in memory_list])
                duration = sum([memory.duration / Constant.US_TO_MS for memory in memory_list])
                base_op_dict.setdefault(base_op.name, {}).setdefault("size", []).append(size)
                base_op_dict.setdefault(base_op.name, {}).setdefault("duration", []).append(duration)
            if comparison_op:
                memory_list = TreeBuilder.get_total_memory(comparison_op)
                size = sum([memory.size / Constant.KB_TO_MB for memory in memory_list])
                duration = sum([memory.duration / Constant.US_TO_MS for memory in memory_list])
                comparison_op_dict.setdefault(comparison_op.name, {}).setdefault("size", []).append(size)
                comparison_op_dict.setdefault(comparison_op.name, {}).setdefault("duration", []).append(duration)
        result_data = []
        for op_name, base_data in base_op_dict.items():
            base_dur = sum(base_data.get("duration", []))
            base_size = sum(base_data.get("size", []))
            base_num = len(base_data.get("size", []))
            comparison_data = comparison_op_dict.pop(op_name, None)
            if ArgsManager().base_profiling_path == ArgsManager().comparison_profiling_path:
                result_data.append([op_name, base_dur, base_size, base_num] + [None] * 5)
            elif comparison_data:
                comparison_dur = sum(comparison_data.get("duration", []))
                comparison_size = sum(comparison_data.get("size", []))
                comparison_num = len(comparison_data.get("size", []))
                result_data.append(
                    [op_name, base_dur, base_size, base_num, comparison_dur, comparison_size,
                     comparison_num] + calculate_diff_ratio(base_size, comparison_size))
            else:
                result_data.append(
                    [op_name, base_dur, base_size, base_num, 0, 0, 0] + calculate_diff_ratio(base_size, 0))
        for op_name, comparison_data_dict in comparison_op_dict.items():
            comparison_dur = sum(comparison_data_dict.get("duration", []))
            comparison_size = sum(comparison_data_dict.get("size", []))
            comparison_num = len(comparison_data_dict.get("size", []))
            result_data.append([op_name, 0, 0, 0, comparison_dur, comparison_size, comparison_num] +
                               calculate_diff_ratio(0, comparison_size))
        if ArgsManager().base_profiling_path != ArgsManager().comparison_profiling_path:
            result_data.sort(key=lambda x: x[-2], reverse=True)
        return result_data
