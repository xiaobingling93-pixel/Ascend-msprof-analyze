from compare_backend.comparator.base_comparator import BaseComparator
from compare_backend.utils.common_func import update_order_id
from compare_backend.utils.constant import Constant


class ModuleComparator(BaseComparator):
    def __init__(self, origin_data: any, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        if not self._origin_data:
            return
        base_all_data = [data for data in self._origin_data if data[0]]  # index 0 for base module
        base_all_data.sort(key=lambda x: x[0].start_time)
        base_none_data = [data for data in self._origin_data if not data[0]]  # index 0 for base module
        base_none_data.sort(key=lambda x: x[1].start_time)
        index = 0
        for base_module, comparison_module in base_all_data:
            if not comparison_module:
                self._rows.extend(self._bean(base_module, comparison_module).rows)
                continue
            while index < len(base_none_data):
                module = base_none_data[index][1]  # index 1 for comparison module
                if module.start_time < comparison_module.start_time:
                    self._rows.extend(self._bean(None, module).rows)
                    index += 1
                else:
                    break
            self._rows.extend(self._bean(base_module, comparison_module).rows)
        while index < len(base_none_data):
            module = base_none_data[index][1]  # index 1 for comparison module
            self._rows.extend(self._bean(None, module).rows)
            index += 1
        update_order_id(self._rows)
        if not any(row[-1] != Constant.NA for row in self._rows):
            print(f"[WARNING] If you want to see the operator's call stack, you must enable with_stack switch.")
