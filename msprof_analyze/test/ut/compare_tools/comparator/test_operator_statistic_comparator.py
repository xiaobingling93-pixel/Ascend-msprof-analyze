import unittest
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.comparator.operator_statistic_comparator \
    import OperatorStatisticComparator


class MockBean:
    TABLE_NAME = "TEST"
    HEADERS = ["INDEX", "VALUE1", "VALUE2"]
    OVERHEAD = []

    def __init__(self, name, base_data, comparison_data):
        self._name = name
        self._base_data = 0 if not base_data else 1
        self._comparison_data = 0 if not comparison_data else 1

    @property
    def row(self):
        return [self._name, self._base_data, self._comparison_data]


class TestOperatorStatisticComparator(unittest.TestCase):
    def test_compare_when_valid_data(self):
        base_dict = {"add": [1], "matmul": [1]}
        comparison_dict = {"add": [1], "reduce": [1]}
        with patch(
                "msprof_analyze.compare_tools.compare_backend.comparator.operator_statistic_comparator."
                "OperatorStatisticComparator._group_by_op_name",
                return_value=(base_dict, comparison_dict)):
            comparator = OperatorStatisticComparator({1: 2}, MockBean)
            comparator._compare()
            self.assertEqual(comparator._rows, [[1, 1, 1], [2, 1, 0], [3, 0, 1]])

    def test_compare_when_invalid_data(self):
        comparator = OperatorStatisticComparator({}, MockBean)
        comparator._compare()
        self.assertEqual(comparator._rows, [])

    def test_group_by_op_name_when_valid_data(self):
        class Node:
            def __init__(self, name):
                self.name = name

        data = [[Node("add"), Node("add")], [None, Node("reduce")], [Node("matmul"), None],
                [Node("matmul"), Node("matmul")], [Node("reduce"), Node("reduce")]]
        comparator = OperatorStatisticComparator(data, MockBean)
        base_dict, comparison_dict = comparator._group_by_op_name()
        self.assertEqual(len(base_dict.get("matmul")), 2)
        self.assertEqual(len(comparison_dict.get("reduce")), 2)

    def test_group_by_op_name_when_invalid_data(self):
        comparator = OperatorStatisticComparator([], MockBean)
        base_dict, comparison_dict = comparator._group_by_op_name()
        self.assertEqual(base_dict, {})
        self.assertEqual(comparison_dict, {})
