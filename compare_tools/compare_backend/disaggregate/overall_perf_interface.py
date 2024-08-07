from common_func.path_manager import PathManager
from compare_backend.profiling_parser.gpu_profiling_parser import GPUProfilingParser
from compare_backend.profiling_parser.npu_profiling_parser import NPUProfilingParser
from compare_backend.utils.args_manager import ArgsManager
from compare_backend.utils.compare_args import Args
from compare_backend.utils.constant import Constant


class OverallPerfInterface:
    PARSER_DICT = {Constant.NPU: NPUProfilingParser, Constant.GPU: GPUProfilingParser}

    def __init__(self, profiling_path: str):
        self._profiling_path = profiling_path
        self._profiling_path_dict = {}
        self._result_data = {}

    def run(self):
        try:
            self._check_path()
            self._load_data()
            self._generate_result()
        except NotImplementedError as e:
            print(f"[ERROR] {e}")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {e}")
        return self._result_data

    def _check_path(self):
        profiling_path = PathManager.get_realpath(self._profiling_path)
        self._profiling_path_dict = ArgsManager().parse_profiling_path(profiling_path)

    def _load_data(self):
        args = Args(enable_profiling_compare=True)
        profiling_type = self._profiling_path_dict.get(Constant.PROFILING_TYPE, Constant.NPU)
        self._profiling_data = self.PARSER_DICT.get(profiling_type)(args, self._profiling_path_dict).load_data()

    def _generate_result(self):
        overall_data = self._profiling_data.overall_metrics

        self._result_data = {
            "profiling_type": overall_data.profiling_type,
            "minimal_profiling": overall_data.minimal_profiling,
            "overall": {"e2e_time_ms": overall_data.e2e_time_ms,
                        "computing_time_ms": overall_data.compute_time_ms,
                        "uncovered_communication_time_ms": overall_data.communication_not_overlapped_ms,
                        "free_time_ms": overall_data.free_time_ms},
            "computing_time_disaggregate": {"fa_time_ms": overall_data.fa_total_time,
                                            "conv_time_ms": overall_data.conv_total_time,
                                            "matmul_time_ms": overall_data.mm_total_time,
                                            "page_attention_time_ms": overall_data.page_attention_time,
                                            "vector_time_ms": overall_data.vector_total_time,
                                            "tensor_move_time_ms": overall_data.sdma_time_tensor_move,
                                            "other_cube_time_ms": overall_data.other_cube_time},
            "computing_num_disaggregate": {"fa_num": overall_data.fa_total_num,
                                           "conv_num": overall_data.conv_total_num,
                                           "matmul_num": overall_data.mm_total_num,
                                           "page_attention_num": overall_data.page_attention_num,
                                           "vector_num": overall_data.vector_total_num,
                                           "tensor_move_num": overall_data.sdma_num_tensor_move,
                                           "other_cube_num": overall_data.other_cube_num},
            "communication_time_disaggregate": {"wait_time_ms": overall_data.wait_time_ms,
                                                "transmit_time_ms": overall_data.transmit_time_ms},
            "free_time_disaggregate": {"sdma_time_ms": overall_data.sdma_time_stream,
                                       "free_ms": overall_data.free_time_ms - overall_data.sdma_time_stream}
        }
