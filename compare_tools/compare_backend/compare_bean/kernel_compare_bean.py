from compare_backend.utils.common_func import calculate_diff_ratio
from compare_backend.utils.constant import Constant
from compare_backend.utils.excel_config import ExcelConfig
from profiler.advisor.utils.utils import convert_to_float


class KernelCompareInfo:
    def __init__(self, data_list: list):
        self._kernel_type = None
        self._input_shapes = None
        self._total_dur = None
        self._number = None
        self._max_dur = None
        self._min_dur = None
        if not data_list:
            return
        self._kernel_type = data_list[0]
        self._input_shapes = data_list[1]
        self._total_dur = round(convert_to_float(data_list[2]), 2)
        self._number = data_list[3]
        self._max_dur = round(convert_to_float(data_list[4]), 2)
        self._min_dur = round(convert_to_float(data_list[5]), 2)

    @property
    def kernel_type(self):
        return self._kernel_type

    @property
    def input_shapes(self):
        return self._input_shapes
    
    @property
    def total_dur(self):
        return self._total_dur if self._total_dur else 0.0
    
    @property
    def number(self):
        return self._number
    
    @property
    def max_dur(self):
        return self._max_dur
    
    @property
    def min_dur(self):
        return self._min_dur
    
    @property
    def avg_dur(self):
        return round(self._total_dur / self._number, 2) if self._total_dur and self._number else 0.0


class KernelCompareBean:
    TABLE_NAME = Constant.KERNEL_TABLE
    HEADERS = ExcelConfig.HEADERS.get(TABLE_NAME)
    OVERHEAD = ExcelConfig.OVERHEAD.get(TABLE_NAME)

    def __init__(self, base_kernel: list, comparison_kernel: list):
        self._base_kernel = KernelCompareInfo(base_kernel)
        self._comparison_kernel = KernelCompareInfo(comparison_kernel)
        self._kernel_type = self._base_kernel.kernel_type \
            if self._base_kernel.kernel_type else self._comparison_kernel.kernel_type
        self._input_shapes = self._base_kernel.input_shapes \
            if self._base_kernel.input_shapes else self._comparison_kernel.input_shapes

    @property
    def row(self):
        row = [None, self._kernel_type, self._input_shapes,
               self._base_kernel.total_dur, self._base_kernel.avg_dur,
               self._base_kernel.max_dur, self._base_kernel.min_dur, self._base_kernel.number,
               self._comparison_kernel.total_dur, self._comparison_kernel.avg_dur,
               self._comparison_kernel.max_dur, self._comparison_kernel.min_dur, self._comparison_kernel.number]
        diff_fields = [calculate_diff_ratio(self._base_kernel.total_dur, self._comparison_kernel.total_dur)[1],
                       calculate_diff_ratio(self._base_kernel.avg_dur, self._comparison_kernel.avg_dur)[1]]
        row.extend(diff_fields)
        return row