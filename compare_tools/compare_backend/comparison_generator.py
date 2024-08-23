from compare_backend.generator.detail_performance_generator import DetailPerformanceGenerator
from compare_backend.generator.overall_performance_generator import OverallPerformanceGenerator
from compare_backend.interface.overall_interface import OverallInterface
from compare_backend.interface.compare_interface import CompareInterface
from compare_backend.profiling_parser.gpu_profiling_parser import GPUProfilingParser
from compare_backend.profiling_parser.npu_profiling_parser import NPUProfilingParser
from compare_backend.utils.constant import Constant
from compare_backend.utils.args_manager import ArgsManager


class ComparisonGenerator:
    PARSER_DICT = {Constant.NPU: NPUProfilingParser, Constant.GPU: GPUProfilingParser}
    INTERFACE_DICT = {Constant.OVERALL_COMPARE: OverallInterface}

    def __init__(self, args):
        self._args_manager = ArgsManager(args)
        self._data_dict = {}

    def run(self):
        try:
            self._args_manager.init()
            self.load_data()
            self.generate_compare_result()
        except NotImplementedError as e:
            print(f"[ERROR] {e}")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {e}")

    def load_data(self):
        self._data_dict[Constant.BASE_DATA] = self.PARSER_DICT.get(self._args_manager.base_profiling_type)(
            self._args_manager.args,
            self._args_manager.base_path_dict,
            self._args_manager.base_step).load_data()
        self._data_dict[Constant.COMPARISON_DATA] = self.PARSER_DICT.get(self._args_manager.comparison_profiling_type)(
            self._args_manager.args,
            self._args_manager.comparison_path_dict,
            self._args_manager.comparison_step).load_data()

    def generate_compare_result(self):
        overall_data = {Constant.BASE_DATA: self._data_dict.get(Constant.BASE_DATA).overall_metrics,
                        Constant.COMPARISON_DATA: self._data_dict.get(Constant.COMPARISON_DATA).overall_metrics}
        generator_list = [OverallPerformanceGenerator(overall_data, self._args_manager.args),
                          DetailPerformanceGenerator(self._data_dict, self._args_manager.args)]
        for generator in generator_list:
            generator.start()
        for generator in generator_list:
            generator.join()

    def run_interface(self, compare_type: str) -> dict:
        try:
            self._args_manager.init()
            self._args_manager.set_compare_type(compare_type)
            self.load_data()
            interface = self.INTERFACE_DICT.get(compare_type)
            if interface:
                return interface(self._data_dict).run()
            return CompareInterface(self._data_dict, self._args_manager).run()
        except NotImplementedError as e:
            print(f"[ERROR] {e}")
        except RuntimeError as e:
            print(f"[ERROR] {e}")
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
        except Exception as e:
            print(f"[ERROR] {e}")
        return {}
