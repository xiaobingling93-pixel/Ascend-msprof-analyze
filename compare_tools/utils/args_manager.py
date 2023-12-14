import os.path

from common_func.path_manager import PathManager
from utils.constant import Constant
from utils.file_reader import FileReader
from utils.profiling_parser import GPUProfilingParser, NPUProfilingParser


class Singleton(object):
    def __init__(self, cls):
        self._cls = cls
        self._instance = {}

    def __call__(self):
        if self._cls not in self._instance:
            self._instance[self._cls] = self._cls()
        return self._instance[self._cls]


@Singleton
class ArgsManager:
    PARSER_DICT = {Constant.NPU: NPUProfilingParser, Constant.GPU: GPUProfilingParser}

    def __init__(self):
        self._args = None
        self._base_profiling_type = None
        self._comparison_profiling_type = None
        self._base_profiling = None
        self._comparison_profiling = None

    @property
    def base_profiling_type(self):
        return self._base_profiling_type

    @property
    def comparison_profiling_type(self):
        return self._comparison_profiling_type

    @property
    def base_profiling(self):
        return self._base_profiling

    @property
    def comparison_profiling(self):
        return self._comparison_profiling

    @property
    def base_profiling_path(self):
        return self._args.base_profiling_path

    @property
    def comparison_profiling_path(self):
        return self._args.comparison_profiling_path

    @classmethod
    def check_profiling_path(cls, file_path: str):
        PathManager.input_path_common_check(file_path)
        PathManager.check_path_owner_consistent(file_path)

    @classmethod
    def check_output_path(cls, output_path: str):
        PathManager.check_input_directory_path(output_path)
        PathManager.make_dir_safety(output_path)
        PathManager.check_path_writeable(output_path)

    def parse_profiling_path(self, file_path: str):
        self.check_profiling_path(file_path)
        if os.path.isfile(file_path):
            (split_file_path, split_file_name) = os.path.split(file_path)
            (shot_name, extension) = os.path.splitext(split_file_name)
            if extension != ".json":
                msg = f"Invalid profiling path suffix: {file_path}"
                raise RuntimeError(msg)
            json_type = FileReader.check_json_type(file_path)
            return {Constant.PROFILING_TYPE: json_type, Constant.PROFILING_PATH: file_path,
                    Constant.TRACE_PATH: file_path}
        ascend_output = os.path.join(file_path, "ASCEND_PROFILER_OUTPUT")
        profiler_output = ascend_output if os.path.isdir(ascend_output) else file_path
        json_path = os.path.join(profiler_output, "trace_view.json")
        memory_path = os.path.join(profiler_output, "operator_memory.csv")
        if not os.path.isfile(json_path):
            msg = f"Invalid profiling path: {file_path}"
            raise RuntimeError(msg)
        memory_path = memory_path if os.path.isfile(memory_path) else None
        return {Constant.PROFILING_TYPE: Constant.NPU, Constant.PROFILING_PATH: file_path,
                Constant.TRACE_PATH: json_path, Constant.MEMORY_DATA_PATH: memory_path}

    def init(self, args: any):
        self._args = args
        if self._args.max_kernel_num is not None and self._args.max_kernel_num <= Constant.LIMIT_KERNEL:
            msg = f"Invalid param, --max_kernel_num has to be greater than {Constant.LIMIT_KERNEL}"
            raise RuntimeError(msg)
        if not isinstance(self._args.op_name_map, dict):
            raise RuntimeError(
                "Invalid param, --op_name_map must be dict, for example: --op_name_map={'name1':'name2'}")
        if self._args.gpu_flow_cat and len(self._args.gpu_flow_cat) > Constant.MAX_FLOW_CAT_LEN:
            msg = f"Invalid param, --gpu_flow_cat exceeded the maximum value {Constant.MAX_FLOW_CAT_LEN}"
            raise RuntimeError(msg)

        if not any([self._args.enable_profiling_compare, self._args.enable_operator_compare,
                    self._args.enable_memory_compare, self._args.enable_communication_compare]):
            self._args.enable_profiling_compare = True
            self._args.enable_operator_compare = True
            self._args.enable_memory_compare = True
            self._args.enable_communication_compare = True

        base_profiling_path = PathManager.get_realpath(self._args.base_profiling_path)
        self.check_profiling_path(base_profiling_path)
        base_profiling_dict = self.parse_profiling_path(base_profiling_path)
        comparison_profiling_path = PathManager.get_realpath(self._args.comparison_profiling_path)
        self.check_profiling_path(comparison_profiling_path)
        comparison_profiling_dict = self.parse_profiling_path(comparison_profiling_path)

        if self._args.output_path:
            self.check_output_path(PathManager.get_realpath(self._args.output_path))

        Constant.BASE_PROFILING = Constant.BASE_PROFILING + self._args.base_profiling_path
        self._base_profiling_type = base_profiling_dict.get(Constant.PROFILING_TYPE)
        self._base_profiling = self.PARSER_DICT.get(self._base_profiling_type)(self._args, base_profiling_dict)

        if base_profiling_path == comparison_profiling_path:
            Constant.COMPARISON_PROFILING = "Same To Base Profiling"
            self._comparison_profiling_type = self._base_profiling_type
            self._comparison_profiling = self._base_profiling
        else:
            Constant.COMPARISON_PROFILING = Constant.COMPARISON_PROFILING + self._args.comparison_profiling_path
            self._comparison_profiling_type = comparison_profiling_dict.get(Constant.PROFILING_TYPE)
            self._comparison_profiling = self.PARSER_DICT.get(self._comparison_profiling_type)(self._args,
                                                                                               comparison_profiling_dict)
