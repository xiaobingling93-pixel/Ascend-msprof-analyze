import os.path
import re

from common_func.path_manager import PathManager
from compare_backend.utils.constant import Constant
from compare_backend.utils.file_reader import FileReader


class Singleton(object):
    def __init__(self, cls):
        self._cls = cls
        self._instance = {}

    def __call__(self, args):
        if self._cls not in self._instance:
            self._instance[self._cls] = self._cls(args)
        return self._instance[self._cls]


@Singleton
class ArgsManager:

    def __init__(self, args: any):
        self._args = args
        self._base_path_dict = {}
        self._comparison_path_dict = {}

    @property
    def args(self):
        return self._args

    @property
    def base_profiling_type(self):
        return self._base_path_dict.get(Constant.PROFILING_TYPE)

    @property
    def comparison_profiling_type(self):
        return self._comparison_path_dict.get(Constant.PROFILING_TYPE)

    @property
    def base_profiling_path(self):
        return self._args.base_profiling_path

    @property
    def comparison_profiling_path(self):
        return self._args.comparison_profiling_path_dict

    @property
    def base_path_dict(self):
        return self._base_path_dict

    @property
    def comparison_path_dict(self):
        return self._comparison_path_dict

    @property
    def enable_profiling_compare(self):
        return self._args.enable_profiling_compare

    @property
    def enable_operator_compare(self):
        return self._args.enable_operator_compare

    @property
    def enable_memory_compare(self):
        return self._args.enable_memory_compare

    @property
    def enable_communication_compare(self):
        return self._args.enable_communication_compare

    @property
    def enable_api_compare(self):
        return self._args.enable_api_compare
    
    @property
    def enable_kernel_compare(self):
        return self._args.enable_kernel_compare

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
        if not os.path.isfile(json_path):
            msg = (f"The data is not collected by PyTorch Adaptor mode or the data is not parsed. "
                   f"Invalid profiling path: {profiler_output}")
            raise RuntimeError(msg)
        path_dict = {Constant.PROFILING_TYPE: Constant.NPU, Constant.PROFILING_PATH: file_path,
                     Constant.TRACE_PATH: json_path, Constant.ASCEND_OUTPUT_PATH: profiler_output}
        sub_dirs = os.listdir(file_path)
        for dir_name in sub_dirs:
            if dir_name == "profiler_info.json" or re.match(r"profiler_info_[0-9]+\.json", dir_name):
                path_dict.update({Constant.INFO_JSON_PATH: os.path.join(file_path, dir_name)})
        return path_dict

    def init(self):
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
                    self._args.enable_memory_compare, self._args.enable_communication_compare,
                    self._args.enable_api_compare, self._args.enable_kernel_compare]):
            self._args.enable_profiling_compare = True
            self._args.enable_operator_compare = True
            self._args.enable_memory_compare = True
            self._args.enable_communication_compare = True
            self._args.enable_api_compare = True
            self._args.enable_kernel_compare = True

        base_profiling_path = PathManager.get_realpath(self._args.base_profiling_path)
        self.check_profiling_path(base_profiling_path)
        self._base_path_dict = self.parse_profiling_path(base_profiling_path)
        comparison_profiling_path = PathManager.get_realpath(self._args.comparison_profiling_path)
        self.check_profiling_path(comparison_profiling_path)
        self._comparison_path_dict = self.parse_profiling_path(comparison_profiling_path)

        if self._args.output_path:
            self.check_output_path(PathManager.get_realpath(self._args.output_path))
