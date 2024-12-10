from profiler.compare_tools.compare_backend.comparator.base_comparator import BaseComparator
from profiler.compare_tools.compare_backend.compare_bean.origin_data_bean.op_stastic_bean import OpStatisticBean
from profiler.compare_tools.compare_backend.utils.common_func import update_order_id
from profiler.prof_common.constant import Constant


class KernelTypeComparator(BaseComparator):
    def __init__(self, origin_data: dict, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        base_kernels = self._origin_data.get(Constant.BASE_DATA, {})
        comparison_kernels = self._origin_data.get(Constant.COMPARISON_DATA, {})
        for key, base_kernel in base_kernels.items():
            comparison_kernel = comparison_kernels.pop(key, OpStatisticBean({}))
            self._rows.append(self._bean(base_kernel, comparison_kernel).row)
        for comparison_kernel in comparison_kernels.values():
            self._rows.append(OpStatisticBean({}), comparison_kernel)
        self._rows.sort(key=lambda x: x[-2], reverse=True)  # order by diff column
        update_order_id(self._rows)
