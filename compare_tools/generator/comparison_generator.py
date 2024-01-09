from generator.detail_performance_generator import DetailPerformanceGenerator
from generator.overall_performance_generator import OverallPerformanceGenerator
from profiling_parser.gpu_profiling_parser import GPUProfilingParser
from profiling_parser.npu_profiling_parser import NPUProfilingParser
from utils.constant import Constant
from utils.args_manager import ArgsManager


class ComparisonGenerator:
    PARSER_DICT = {Constant.NPU: NPUProfilingParser, Constant.GPU: GPUProfilingParser}

    def __init__(self):
        self._args_manager = ArgsManager()
        self._overall_data = None
        self._details_data = None

    def run(self):
        self.load_data()
        self.generate_compare_result()

    def load_data(self):
        base_data = self.PARSER_DICT.get(self._args_manager.base_profiling_type)(
            self._args_manager.args, self._args_manager.base_path_dict).load_data()
        comparison_data = self.PARSER_DICT.get(self._args_manager.comparison_profiling_type)(
            self._args_manager.args, self._args_manager.comparison_path_dict).load_data()
        self._overall_data = {Constant.BASE_DATA: base_data.overall_metrics,
                              Constant.COMPARISON_DATA: comparison_data.overall_metrics}
        self._details_data = {Constant.BASE_DATA: base_data, Constant.COMPARISON_DATA: comparison_data}

    def generate_compare_result(self):
        generator_list = [OverallPerformanceGenerator(self._overall_data, self._args_manager.args),
                          DetailPerformanceGenerator(self._details_data, self._args_manager.args)]
        for generator in generator_list:
            generator.start()
        for generator in generator_list:
            generator.join()
