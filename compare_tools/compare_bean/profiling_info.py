from utils.constant import Constant


class ProfilingInfo:
    TABLE_NAME = Constant.PERFORMANCE_TABLE
    HEADERS = []
    OVERHEAD = []

    def __init__(self, profiling_type: str):
        self.profiling_type = profiling_type
        self.cube_time = 0.0
        self.other_time = 0.0
        self.vec_time = 0.0
        self.cube_num = 0
        self.vec_num = 0
        self.sdma_num = 0
        self.fa_num_fwd = 0
        self.fa_num_bwd = 0
        self.compute_time = 0.0
        self.communication_not_overlapped = 0.0
        self.memory_used = 0.0
        self.e2e_time = 0.0
        self.sdma_time = 0.0
        self.scheduling_time = 0.0
        self.fa_time_bwd = 0.0
        self.fa_time_fwd = 0.0
        self.minimal_profiling = False
        self.hide_op_details = False

    def trans_time_to_s(self):
        self.cube_time = self.cube_time / 10 ** 6
        self.other_time = self.other_time / 10 ** 6
        self.vec_time = self.vec_time / 10 ** 6
        self.compute_time = self.compute_time / 10 ** 6
        self.communication_not_overlapped = self.communication_not_overlapped / 10 ** 6
        self.e2e_time = self.e2e_time / 10 ** 6
        self.sdma_time = self.sdma_time / 10 ** 6
        self.scheduling_time = self.scheduling_time / 10 ** 6
        self.fa_time_bwd = self.fa_time_bwd / 10 ** 6
        self.fa_time_fwd = self.fa_time_fwd / 10 ** 6

    def calculate_other_time(self):
        self.other_time = max(
            [0, self.compute_time - self.cube_time - self.fa_time_fwd - self.fa_time_bwd - self.vec_time])

    def calculate_vec_time(self):
        self.vec_time = self.compute_time - self.cube_time - self.fa_time_fwd - self.fa_time_bwd

    def calculate_schedule_time(self):
        self.scheduling_time = self.e2e_time - self.compute_time - self.communication_not_overlapped

    def update_fa_fwd_info(self, time: float):
        self.fa_time_fwd += time
        self.fa_num_fwd += 1

    def update_fa_bwd_info(self, time: float):
        self.fa_time_bwd += time
        self.fa_num_bwd += 1

    def update_sdma_info(self, time: float, num: int = 1):
        self.sdma_time += time
        self.sdma_num += num

    def update_cube_info(self, time: float):
        self.cube_time += time
        self.cube_num += 1

    def update_vec_info(self, time: float):
        self.vec_time += time
        self.vec_num += 1

    def set_compute_time(self, time: float):
        self.compute_time = time

    def update_compute_time(self, time: float):
        self.compute_time += time

    def set_e2e_time(self, time: float):
        self.e2e_time = time

    def set_comm_not_overlap(self, time: float):
        self.communication_not_overlapped = time

    def update_comm_not_overlap(self, time: float):
        self.communication_not_overlapped += time

    def set_memory_used(self, memory: float):
        self.memory_used = memory
