from compare_backend.comparator.base_comparator import BaseComparator


class OperatorComparator(BaseComparator):
    def __init__(self, origin_data: any, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        if not self._origin_data:
            return
        self._rows = [None] * (len(self._origin_data))
        for index, (base_op, comparison_op) in enumerate(self._origin_data):
            self._rows[index] = self._bean(index, base_op, comparison_op).row
