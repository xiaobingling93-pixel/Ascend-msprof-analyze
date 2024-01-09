import unittest

from compare_bean.profiling_info import ProfilingInfo


class TestProfilingInfo(unittest.TestCase):
    def test_calculate_other_time(self):
        info = ProfilingInfo("NPU")
        info.compute_time = 10
        info.cube_time = 1
        info.fa_time_fwd = 2
        info.fa_time_bwd = 2
        info.vec_time = 3
        info.calculate_other_time()
        self.assertEqual(info.other_time, 2)
        info.vec_time = 7
        info.calculate_other_time()
        self.assertEqual(info.other_time, 0)

    def test_calculate_vec_time(self):
        info = ProfilingInfo("NPU")
        info.compute_time = 10
        info.cube_time = 1
        info.fa_time_fwd = 2
        info.fa_time_bwd = 2
        info.calculate_vec_time()
        self.assertEqual(info.vec_time, 5)

    def test_calculate_schedule_time(self):
        info = ProfilingInfo("NPU")
        info.e2e_time = 10
        info.compute_time = 5
        info.communication_not_overlapped = 3
        info.calculate_schedule_time()
        self.assertEqual(info.scheduling_time, 2)

    def test_update_fa_fwd_info(self):
        info = ProfilingInfo("NPU")
        info.update_fa_fwd_info(5)
        info.update_fa_fwd_info(5)
        self.assertEqual(info.fa_time_fwd, 10)
        self.assertEqual(info.fa_num_fwd, 2)

    def test_update_fa_bwd_info(self):
        info = ProfilingInfo("NPU")
        info.update_fa_bwd_info(5)
        info.update_fa_bwd_info(5)
        self.assertEqual(info.fa_time_bwd, 10)
        self.assertEqual(info.fa_num_bwd, 2)

    def test_update_sdma_info(self):
        info = ProfilingInfo("NPU")
        info.update_sdma_info(5)
        self.assertEqual(info.sdma_time, 5)
        self.assertEqual(info.sdma_num, 1)
        info.update_sdma_info(5, 5)
        self.assertEqual(info.sdma_time, 10)
        self.assertEqual(info.sdma_num, 6)

    def test_update_cube_info(self):
        info = ProfilingInfo("NPU")
        info.update_cube_info(5)
        info.update_cube_info(5)
        self.assertEqual(info.cube_time, 10)
        self.assertEqual(info.cube_num, 2)

    def test_update_vec_info(self):
        info = ProfilingInfo("NPU")
        info.update_vec_info(5)
        info.update_vec_info(5)
        self.assertEqual(info.vec_time, 10)
        self.assertEqual(info.vec_num, 2)

    def test_set_compute_time(self):
        info = ProfilingInfo("NPU")
        info.update_compute_time(1)
        info.set_compute_time(5)
        self.assertEqual(info.compute_time, 5)

    def test_update_compute_time(self):
        info = ProfilingInfo("NPU")
        info.update_compute_time(5)
        info.update_compute_time(5)
        self.assertEqual(info.compute_time, 10)

    def test_set_e2e_time(self):
        info = ProfilingInfo("NPU")
        info.set_e2e_time(5)
        self.assertEqual(info.e2e_time, 5)

    def test_set_comm_not_overlap(self):
        info = ProfilingInfo("NPU")
        info.update_comm_not_overlap(10)
        info.set_comm_not_overlap(5)
        self.assertEqual(info.communication_not_overlapped, 5)

    def test_update_comm_not_overlap(self):
        info = ProfilingInfo("NPU")
        info.update_comm_not_overlap(5)
        info.update_comm_not_overlap(5)
        self.assertEqual(info.communication_not_overlapped, 10)

    def test_set_memory_used(self):
        info = ProfilingInfo("NPU")
        info.set_memory_used(10)
        self.assertEqual(info.memory_used, 10)

    def test_is_not_minimal_profiling(self):
        info = ProfilingInfo("GPU")
        info.minimal_profiling = False
        self.assertFalse(info.is_not_minimal_profiling())
        info = ProfilingInfo("NPU")
        info.minimal_profiling = True
        self.assertFalse(info.is_not_minimal_profiling())
        info.minimal_profiling = False
        self.assertTrue(info.is_not_minimal_profiling())
