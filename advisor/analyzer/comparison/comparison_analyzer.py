import logging

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.analyzer.comparison.comparison_checker import ComparisonChecker

logger = logging.getLogger()


class ComparisonAnalyzer(BaseAnalyzer):

    def __init__(self, collection_path, n_processes: int = 1, **kwargs) -> None:
        super().__init__(collection_path, n_processes, **kwargs)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()

    def optimize(self, compare_profiling_list, **kwargs):
        for compare_profiling_path in compare_profiling_list:
            self._optimize(**compare_profiling_path)
        return self.result

    def get_priority(self):
        pass

    def _optimize(self, profiling_path, benchmark_profiling_path, **kwargs):
        comparison_checker = ComparisonChecker(profiling_path,
                                               benchmark_profiling_path,
                                               step=kwargs.get("step"),
                                               benchmark_step=kwargs.get("benchmark_step"),
                                               rank=kwargs.get("rank"),
                                               benchmark_rank=kwargs.get("benchmark_rank"))
        comparison_checker.compare(kwargs.get("compare_mode"))
        comparison_checker.make_record(self.result)
        comparison_checker.make_render(self.html_render)
