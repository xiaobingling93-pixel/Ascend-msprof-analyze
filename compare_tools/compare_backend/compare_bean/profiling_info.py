from compare_backend.utils.constant import Constant


class ProfilingInfo:
    TABLE_NAME = Constant.PERFORMANCE_TABLE
    HEADERS = []
    OVERHEAD = []

    def __init__(self, profiling_type: str):
        self.profiling_type = profiling_type
        self.other_time = 0.0
        self.lccl_num = 0
        self.compute_time = 0.0
        self.communication_not_overlapped = 0.0
        self.wait_time = 0.0
        self.memory_used = 0.0
        self.e2e_time = 0.0
        self.scheduling_time = 0.0
        self.lccl_time = 0.0
        self.minimal_profiling = False
        self.hide_op_details = False
        self.is_level0 = False

        self.cube_time = 0.0
        self.vec_time = 0.0
        self.cube_num = 0
        self.vec_num = 0
        self.sdma_num = 0
        self.fa_num_fwd = 0
        self.fa_num_bwd = 0
        self.pa_num = 0
        self.conv_time_fwd = 0.0
        self.conv_time_bwd = 0.0
        self.conv_num_fwd = 0
        self.conv_num_bwd = 0
        self.sdma_time = 0.0
        self.fa_time_bwd = 0.0
        self.pa_time = 0.0
        self.fa_time_fwd = 0.0
        # 性能拆解新指标
        self.fa_time_fwd_cube = 0.0
        self.fa_num_fwd_cube = 0
        self.fa_time_bwd_cube = 0.0
        self.fa_num_bwd_cube = 0
        self.fa_time_fwd_vector = 0.0
        self.fa_num_fwd_vector = 0
        self.fa_time_bwd_vector = 0.0
        self.fa_num_bwd_vector = 0

        self.conv_time_fwd_cube = 0.0
        self.conv_num_fwd_cube = 0
        self.conv_time_bwd_cube = 0.0
        self.conv_num_bwd_cube = 0
        self.conv_time_fwd_vector = 0.0
        self.conv_num_fwd_vector = 0
        self.conv_time_bwd_vector = 0.0
        self.conv_num_bwd_vector = 0

        self.matmul_time_cube = 0.0
        self.matmul_num_cube = 0
        self.matmul_time_vector = 0.0
        self.matmul_num_vector = 0

        self.page_attention_time = 0.0
        self.page_attention_num = 0

        self.vector_time_trans = 0.0
        self.vector_num_trans = 0
        self.vector_time_notrans = 0.0
        self.vector_num_notrans = 0

        self.sdma_time_tensor_move = 0.0
        self.sdma_num_tensor_move = 0
        self.sdma_time_stream = 0.0
        self.sdma_num_stream = 0

        self.other_cube_time = 0.0
        self.other_cube_num = 0
        self.RDMA_bandwidth = 0.0
        self.SDMA_bandwidth = 0.0
    @property
    def e2e_time_ms(self):
        return self.e2e_time * 10 ** 3

    @property
    def compute_time_ms(self):
        return self.compute_time * 10 ** 3

    @property
    def free_time_ms(self):
        return self.scheduling_time * 10 ** 3

    @property
    def communication_not_overlapped_ms(self):
        return self.communication_not_overlapped * 10 ** 3

    @property
    def wait_time_ms(self):
        return self.wait_time * 10 ** 3

    @property
    def transmit_time_ms(self):
        return (self.communication_not_overlapped - self.wait_time) * 10 ** 3

    @property
    def fa_total_time(self):
        return sum((self.fa_time_fwd_cube, self.fa_time_fwd_vector, self.fa_time_bwd_cube, self.fa_time_bwd_vector))

    @property
    def fa_total_num(self):
        return sum((self.fa_num_fwd_cube, self.fa_num_fwd_vector, self.fa_num_bwd_cube, self.fa_num_bwd_vector))

    @property
    def conv_total_time(self):
        return sum(
            (self.conv_time_fwd_cube, self.conv_time_fwd_vector, self.conv_time_bwd_cube,
             self.conv_time_bwd_vector))

    @property
    def conv_total_num(self):
        return sum((self.conv_num_fwd_cube, self.conv_num_fwd_vector, self.conv_num_bwd_cube,
                    self.conv_num_bwd_vector))

    @property
    def mm_total_time(self):
        return sum((self.matmul_time_cube, self.matmul_time_vector))

    @property
    def mm_total_num(self):
        return sum((self.matmul_num_cube, self.matmul_num_vector))

    @property
    def vector_total_time(self):
        return sum((self.vector_time_trans, self.vector_time_notrans))

    @property
    def vector_total_num(self):
        return sum((self.vector_num_trans, self.vector_num_notrans))
    def trans_to_s(self):
        self.cube_time /= 10 ** 3
        self.vec_time /= 10 ** 3
        self.conv_time_fwd /= 10 ** 3
        self.conv_time_bwd /= 10 ** 3
        self.sdma_time /= 10 ** 3
        self.fa_time_bwd /= 10 ** 3
        self.pa_time /= 10 ** 3
        self.fa_time_fwd /= 10 ** 3
    def trans_time_to_s(self):
        # 新指标单位为ms
        self.fa_time_fwd_cube /= 10 ** 3
        self.fa_time_bwd_cube /= 10 ** 3
        self.fa_time_fwd_vector /= 10 ** 3
        self.fa_time_bwd_vector /= 10 ** 3
        self.conv_time_fwd_cube /= 10 ** 3
        self.conv_time_bwd_cube /= 10 ** 3
        self.conv_time_fwd_vector /= 10 ** 3
        self.conv_time_bwd_vector /= 10 ** 3
        self.matmul_time_cube /= 10 ** 3
        self.matmul_time_vector /= 10 ** 3
        self.vector_time_trans /= 10 ** 3
        self.vector_time_notrans /= 10 ** 3
        self.sdma_time_tensor_move /= 10 ** 3
        self.sdma_time_stream /= 10 ** 3
        self.page_attention_time /= 10 ** 3
        self.other_cube_time /= 10 ** 3
        self.other_time = self.other_time / 10 ** 6
        self.compute_time = self.compute_time / 10 ** 6
        self.communication_not_overlapped = self.communication_not_overlapped / 10 ** 6
        self.wait_time = self.wait_time / 10 ** 6
        self.e2e_time = self.e2e_time / 10 ** 6
        self.scheduling_time = self.scheduling_time / 10 ** 6
        self.lccl_time = self.lccl_time / 10 ** 6

    def calculate_cube_time(self):
        self.cube_time = self.matmul_time_cube + self.matmul_time_vector + self.other_cube_time

    def calculate_vec_time(self):
        self.vec_time = self.vector_time_trans + self.vector_time_notrans

    def calculate_cube_num(self):
        self.cube_num = self.matmul_num_cube + self.matmul_num_vector + self.other_cube_num

    def calculate_vec_num(self):
        self.vec_num = self.vector_num_trans + self.vector_num_notrans

    def calculate_sdma_num(self):
        self.sdma_num = self.sdma_num_tensor_move + self.sdma_num_stream

    def calculate_fa_num_fwd(self):
        self.fa_num_fwd = self.fa_num_fwd_cube + self.fa_num_fwd_vector

    def calculate_fa_num_bwd(self):
        self.fa_num_bwd = self.fa_num_bwd_cube + self.fa_num_bwd_vector

    def calculate_pa_num(self):
        self.pa_num = self.page_attention_num

    def calculate_pa_time(self):
        self.pa_num = self.page_attention_num

    def calculate_conv_time_fwd(self):
        self.conv_time_fwd = self.conv_time_fwd_cube + self.conv_time_fwd_vector

    def calculate_conv_time_bwd(self):
        self.conv_time_bwd = self.conv_time_bwd_cube + self.conv_time_bwd_vector

    def calculate_conv_num_fwd(self):
        self.conv_num_fwd = self.conv_num_fwd_cube + self.conv_num_fwd_vector

    def calculate_conv_num_bwd(self):
        self.conv_num_bwd = self.conv_num_bwd_cube + self.conv_num_bwd_vector

    def calculate_sdma_time(self):
        self.sdma_time = self.sdma_time_tensor_move + self.sdma_time_stream

    def calculate_fa_time_fwd(self):
        self.fa_time_fwd = self.fa_time_fwd_cube + self.fa_time_fwd_vector

    def calculate_fa_time_bwd(self):
        self.fa_time_bwd = self.fa_time_bwd_cube + self.fa_time_bwd_vector

    def calculate_other_time(self):
        self.other_time = max(
            [0, self.compute_time - self.cube_time - self.fa_time_fwd - self.fa_time_bwd -
             self.pa_time - self.vec_time - self.conv_time_fwd - self.conv_time_bwd])

    def calculate_schedule_time(self):
        self.scheduling_time = (self.e2e_time - self.compute_time - self.lccl_time - self.communication_not_overlapped)

    def update_fa_fwd_cube_info(self, time: float):
        self.fa_time_fwd_cube += time
        self.fa_num_fwd_cube += 1

    def update_fa_bwd_cube_info(self, time: float):
        self.fa_time_bwd_cube += time
        self.fa_num_bwd_cube += 1

    def update_fa_fwd_vector_info(self, time: float):
        self.fa_time_fwd_vector += time
        self.fa_num_fwd_vector += 1

    def update_fa_bwd_vector_info(self, time: float):
        self.fa_time_bwd_vector += time
        self.fa_num_bwd_vector += 1

    def update_sdma_tensor_move_info(self, time: float):
        self.sdma_time_tensor_move += time
        self.sdma_num_tensor_move += 1

    def update_sdma_stream_info(self, time: float, num: int = 1):
        self.sdma_time_stream += time
        self.sdma_num_stream += num

    def update_lccl_info(self, time: float):
        self.lccl_time += time
        self.lccl_num += 1

    def update_conv_bwd_cube_info(self, time: float):
        self.conv_time_bwd_cube += time
        self.conv_num_bwd_cube += 1

    def update_conv_fwd_cube_info(self, time: float):
        self.conv_time_fwd_cube += time
        self.conv_num_fwd_cube += 1

    def update_conv_bwd_vector_info(self, time: float):
        self.conv_time_bwd_vector += time
        self.conv_num_bwd_vector += 1

    def update_conv_fwd_vector_info(self, time: float):
        self.conv_time_fwd_vector += time
        self.conv_num_fwd_vector += 1

    def update_matmul_cube_info(self, time: float):
        self.matmul_time_cube += time
        self.matmul_num_cube += 1

    def update_matmul_vector_info(self, time: float):
        self.matmul_time_vector += time
        self.matmul_num_vector += 1

    def update_page_attention_info(self, time: float):
        self.page_attention_time += time
        self.page_attention_num += 1

    def update_vector_trans_info(self, time: float):
        self.vector_time_trans += time
        self.vector_num_trans += 1

    def update_vector_notrans_info(self, time: float):
        self.vector_time_notrans += time
        self.vector_num_notrans += 1

    def update_other_cube_info(self, time: float):
        self.other_cube_time += time
        self.other_cube_num += 1

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

    def update_comm_not_overlap_wait_time(self, time: float):
        self.wait_time = time

    def set_memory_used(self, memory: float):
        self.memory_used = memory

    def is_not_minimal_profiling(self) -> bool:
        return self.profiling_type == Constant.NPU and not self.minimal_profiling

    def set_RDMA_bandwidth(self, bandwidth: float):
        self.RDMA_bandwidth = bandwidth

    def set_SDMA_bandwidth(self, bandwidth: float):
        self.SDMA_bandwidth = bandwidth