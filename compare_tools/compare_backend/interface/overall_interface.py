from compare_backend.comparator.overall_performance_comparator import OverallPerformanceComparator
from compare_backend.compare_bean.profiling_info import ProfilingInfo
from profiler.prof_common.constant import Constant


class OverallInterface:
    def __init__(self, overall_data: dict):
        self._overall_data = overall_data

    def run(self):
        data = {Constant.BASE_DATA: self._overall_data.get(Constant.BASE_DATA).overall_metrics,
                Constant.COMPARISON_DATA: self._overall_data.get(Constant.COMPARISON_DATA).overall_metrics}
        return OverallPerformanceComparator(data, ProfilingInfo).generate_data()
