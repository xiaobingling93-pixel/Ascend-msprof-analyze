import unittest

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.operator_memory_bean \
    import OperatorMemoryBean


class TestOperatorMemoryBean(unittest.TestCase):
    bean1 = OperatorMemoryBean({"Name": "cann::add", "Size(KB)": 512, "Allocation Time(us)": 1, "Release Time(us)": 5})
    bean2 = OperatorMemoryBean({"Name": "aten::add", "Size(KB)": 512})

    @staticmethod
    def _get_property_str(bean: OperatorMemoryBean):
        return f"{bean.name}-{bean.size}-{bean.allocation_time}-{bean.release_time}"

    def test_property(self):
        self.assertEqual(self._get_property_str(self.bean1), "cann::add-512.0-1-5")
        self.assertEqual(self._get_property_str(self.bean2), "aten::add-512.0-0-0")

    def test_is_cann_op(self):
        self.assertTrue(self.bean1.is_cann_op())
        self.assertFalse(self.bean2.is_cann_op())
