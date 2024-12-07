import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cluster_analyse"))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compare_backend.comparison_generator import ComparisonGenerator
from compare_backend.disaggregate.overall_perf_interface import OverallPerfInterface
from compare_backend.utils.compare_args import Args
from profiler.prof_common.constant import Constant


class ComparisonInterface:
    def __init__(self, base_profiling_path: str, comparison_profiling_path: str = "",
                 base_step: str = "", comparison_step: str = ""):
        self.base_profiling_path = base_profiling_path
        if comparison_profiling_path:
            self._args = Args(base_profiling_path=base_profiling_path,
                              comparison_profiling_path=comparison_profiling_path,
                              base_step=base_step,
                              comparison_step=comparison_step)

    def compare(self, compare_type: str) -> dict:
        return ComparisonGenerator(self._args).run_interface(compare_type)

    def disaggregate_perf(self, compare_type: str) -> dict:
        if compare_type != Constant.OVERALL_COMPARE:
            print('[ERROR] Invalid compare_type value: {compare_type} which not supported.')
            return {}
        return OverallPerfInterface(self.base_profiling_path).run()
