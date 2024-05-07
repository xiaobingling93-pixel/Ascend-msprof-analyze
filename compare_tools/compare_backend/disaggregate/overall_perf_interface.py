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
        self._check_path()
        self._load_data()
        self._generate_result()
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
        self._result_data = getattr(overall_data, "__dict__", {})
