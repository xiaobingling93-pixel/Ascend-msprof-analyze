import logging
from typing import Dict, List

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.result.result import OptimizeResult
from profiler.compare_tools.compare_backend.utils.constant import Constant
from profiler.compare_tools.compare_interface.comparison_interface import ComparisonInterface

logger = logging.getLogger()


class OverallSummaryAnalyzer(BaseAnalyzer):

    def __init__(self, profiling_path, benchmark_profiling_path=None, **kwargs):
        self.benchmark_profiling_path = benchmark_profiling_path or profiling_path
        self.profiling_path = profiling_path
        self.html_render = HTMLRender()
        self.result = OptimizeResult()

    def optimize(self):
        compare_result = ComparisonInterface(self.benchmark_profiling_path, self.profiling_path).compare(
            Constant.OVERALL_COMPARE)

        headers = compare_result.get('Model Profiling Time Distribution').get("headers", [])
        rows = compare_result.get('Model Profiling Time Distribution').get("rows", [])

        self.make_record()
        self.make_render(headers=headers, rows=rows)
        return compare_result

    def make_record(self):
        pass

    def make_render(self, **kwargs):
        headers = kwargs.get("headers")
        rows = kwargs.get("rows")

        if not headers or not rows:
            logger.info("Empty headers or rows, skip render overall analysis html")
        self.html_render.render_template(key="overall",
                                         template_dir="templates",
                                         template_name="overall_analysis.html",
                                         headers=kwargs.get("headers"),
                                         rows=kwargs.get("rows"))
