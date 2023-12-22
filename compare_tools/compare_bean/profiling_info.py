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
        self.flash_attention_time_bwd = 0.0
        self.flash_attention_time_fwd = 0.0
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
        self.flash_attention_time_bwd = self.flash_attention_time_bwd / 10 ** 6
        self.flash_attention_time_fwd = self.flash_attention_time_fwd / 10 ** 6
