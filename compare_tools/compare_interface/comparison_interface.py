from compare_backend.comparison_generator import ComparisonGenerator
from compare_backend.utils.constant import Constant


class Args:
    def __init__(self,
                 base_profiling_path: str,
                 comparison_profiling_path: str,
                 enable_profiling_compare: bool = False,
                 enable_operator_compare: bool = False,
                 enable_memory_compare: bool = False,
                 enable_communication_compare: bool = False,
                 output_path: str = "",
                 max_kernel_num: int = None,
                 op_name_map: dict = None,
                 use_input_shape: bool = False,
                 gpu_flow_cat: str = ""):
        self.base_profiling_path = base_profiling_path
        self.comparison_profiling_path = comparison_profiling_path
        self.enable_profiling_compare = enable_profiling_compare
        self.enable_operator_compare = enable_operator_compare
        self.enable_memory_compare = enable_memory_compare
        self.enable_communication_compare = enable_communication_compare
        self.output_path = output_path
        self.max_kernel_num = max_kernel_num
        self.op_name_map = op_name_map or {}
        self.use_input_shape = use_input_shape
        self.gpu_flow_cat = gpu_flow_cat


class ComparisonInterface:
    def __init__(self, base_profiling_path: str, comparison_profiling_path: str):
        self._args = Args(base_profiling_path, comparison_profiling_path)

    def compare(self, compare_type: str) -> dict:
        if compare_type == Constant.OVERALL_COMPARE:
            self._args.enable_profiling_compare = True

        return ComparisonGenerator(self._args).run_interface(compare_type)
