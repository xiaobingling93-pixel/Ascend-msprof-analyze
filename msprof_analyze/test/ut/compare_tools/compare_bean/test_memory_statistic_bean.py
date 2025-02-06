import unittest
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.compare_bean.memory_statistic_bean import MemoryStatisticBean


class MockMemory:
    def __init__(self, size, duration):
        self.size = size
        self.duration = duration


class TestMemoryStatisticBean(unittest.TestCase):
    name = "matmul"

    def test_row_when_valid_data(self):
        result = [None, self.name, 8.0, 40.0, 2, 4.0, 20.0, 1, -20.0, 0.5]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_memory",
                   return_value=[MockMemory(10240, 2000), MockMemory(10240, 2000)]):
            bean = MemoryStatisticBean(self.name, [1, 1], [1])
            self.assertEqual(bean.row, result)

    def test_row_when_invalid_base_data(self):
        result = [None, self.name, 0, 0, 0, 4.0, 20.0, 1, 20.0, float("inf")]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_memory",
                   return_value=[MockMemory(10240, 2000), MockMemory(10240, 2000)]):
            bean = MemoryStatisticBean(self.name, [], [1])
            self.assertEqual(bean.row, result)

    def test_row_when_invalid_comparison_data(self):
        result = [None, self.name, 8.0, 40.0, 2, 0, 0, 0, -40.0, 0]
        with patch("msprof_analyze.compare_tools.compare_backend.utils.tree_builder.TreeBuilder.get_total_memory",
                   return_value=[MockMemory(10240, 2000), MockMemory(10240, 2000)]):
            bean = MemoryStatisticBean(self.name, [1, 1], [])
            self.assertEqual(bean.row, result)
