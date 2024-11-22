from compare_backend.comparator.base_comparator import BaseComparator
from profiler.prof_common.constant import Constant
from compare_backend.utils.common_func import update_order_id


class ApiCompareComparator(BaseComparator):
    def __init__(self, origin_data: list, bean: any):
        super().__init__(origin_data, bean)

    @classmethod
    def _aggregated_api_by_name(cls, ops: list):
        ops_dict = {}
        for op in ops:
            ops_dict.setdefault(op.name, []).append(op)
        return ops_dict

    def _compare(self):
        if not self._origin_data:
            return
        base_ops = self._origin_data.get(Constant.BASE_DATA, {})
        comparison_ops = self._origin_data.get(Constant.COMPARISON_DATA, {})
        if not base_ops or not comparison_ops:
            return
        base_aggregated_ops = self._aggregated_api_by_name(base_ops)
        comparison_aggregated_ops = self._aggregated_api_by_name(comparison_ops)
        for op_name, base_data in base_aggregated_ops.items():
            comparsion_data = comparison_aggregated_ops.pop(op_name, [])
            self._rows.append(self._bean(op_name, base_data, comparsion_data).row)
        if comparison_aggregated_ops:
            for op_name, comparison_data in comparison_aggregated_ops.items():
                self._rows.append(self._bean(op_name, [], comparison_data).row)
        update_order_id(self._rows)
