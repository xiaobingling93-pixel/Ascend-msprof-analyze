from compare_backend.comparator.overall_performance_comparator import OverallPerformanceComparator
from compare_backend.compare_bean.profiling_info import ProfilingInfo
from compare_backend.generator.base_generator import BaseGenerator
from compare_backend.view.screen_view import ScreenView


class OverallPerformanceGenerator(BaseGenerator):
    def __init__(self, profiling_data_dict: dict, args: any):
        super().__init__(profiling_data_dict, args)

    def compare(self):
        if not self._args.enable_profiling_compare:
            return
        self._result_data = OverallPerformanceComparator(self._profiling_data_dict, ProfilingInfo).generate_data()

    def generate_view(self):
        if not self._result_data:
            return
        ScreenView(self._result_data).generate_view()
