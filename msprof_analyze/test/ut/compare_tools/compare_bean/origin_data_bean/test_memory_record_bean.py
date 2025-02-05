import unittest

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.memory_record_bean \
    import MemoryRecordBean


class TestMemoryRecordBean(unittest.TestCase):
    def test_total_reserved_mb(self):
        self.assertEqual(MemoryRecordBean({"Total Reserved(MB)": 5}).total_reserved_mb, 5)
        self.assertEqual(MemoryRecordBean({}).total_reserved_mb, 0)
