import logging

from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.utils.utils import safe_index_value, convert_to_float
from profiler.compare_tools.compare_backend.utils.constant import Constant as CompareConstant
from profiler.compare_tools.compare_interface.comparison_interface import ComparisonInterface

logger = logging.getLogger()


class ComparisonChecker:
    BENCHMARK_PREFIX = "Benchmark "
    SHOW_TOPK = 10
    DIFF_AVG_RATIO = "Diff Avg Ratio"
    COMPARE_MODE_TO_DESC = {CompareConstant.KERNEL_COMPARE: "Kernel compare",
                            CompareConstant.API_COMPARE: "Api compare"}

    def __init__(self, profiling_path, benchmark_profiling_path, step=None, benchmark_step=None, rank=None,
                 benchmark_rank=None):

        self.profiling_path = profiling_path
        self.benchmark_profiling_path = benchmark_profiling_path
        self.step = str(step) if step is not None else step
        self.benchmark_step = str(benchmark_step) if benchmark_step is not None else benchmark_step
        self.rank = rank
        self.benchmark_rank = benchmark_rank
        self.compare_mode = None
        self.format_result = {}
        self.desc = None
        self.suggestion = None

    def compare(self, compare_mode):
        """
        :Param event_dataset: dataset of timeline event
        """
        if compare_mode is None:
            return
        self.compare_mode = compare_mode
        compare_interface = ComparisonInterface(self.profiling_path, self.benchmark_profiling_path, self.step,
                                                self.benchmark_step)
        result = compare_interface.compare(self.compare_mode)
        data = result.get(self.compare_mode, {})
        headers = data.get("headers", {})
        rows = data.get("rows", [])
        format_headers = []

        for schema in headers:
            name = schema.get("name", "null")
            if name not in format_headers:
                format_headers.append(name)
            else:
                format_headers.append(f"{self.BENCHMARK_PREFIX} {name}")

        if not rows:
            return

        self.format_result[self.compare_mode] = {"headers": format_headers, "rows": rows}

    def make_record(self, result: OptimizeResult):
        """
        make record for what and how to optimize
        """
        if not self.format_result:
            return

        sheet_name = self._get_sheet_name()
        self.desc = sheet_name
        optimization_item = OptimizeItem(sheet_name, self.desc, [])
        result.add(OptimizeRecord(optimization_item))

        result.add_detail(sheet_name, headers=self.format_result.get(self.compare_mode, {}).get("headers"))

        for row in self.format_result.get(self.compare_mode, {}).get("rows"):
            result.add_detail(sheet_name, detail=row)

    def make_render(self, html_render, **kwargs):
        if not self.format_result:
            return

        headers = self.format_result.get(self.compare_mode, {}).get("headers", [])
        diff_avg_index = safe_index_value(headers, self.DIFF_AVG_RATIO)
        if diff_avg_index is None:
            logger.warning("'%s' not exsits in headers of comparison result, skip render html.", self.DIFF_AVG_RATIO)
            return
        rows = self.format_result.get(self.compare_mode, {}).get("rows", [])
        sorted_rows = sorted(rows,
                             key=lambda x: convert_to_float(x[diff_avg_index]) if diff_avg_index < len(x) else -1.0,
                             reverse=True)

        topk_rows = []
        if sorted_rows:
            topk_rows = sorted_rows[:self.SHOW_TOPK]

        if not headers or not topk_rows:
            return

        html_desc = self.desc + f". Only show {self.SHOW_TOPK} rows here, see mstt_advisor*.xlsx for details"

        html_render.render_template(key="comparison",
                                    template_dir="templates",
                                    template_name="comparison.html",
                                    sheet_name=self._get_sheet_name(),
                                    desc=html_desc,
                                    headers=headers,
                                    rows=topk_rows)

    def _get_sheet_name(self):

        sheet_name = ""
        if self.rank is not None:
            sheet_name += f"Rank{self.rank}"
        if self.step is not None:
            sheet_name += f" Step{self.step}"
        if sheet_name:
            sheet_name += " and "
        if self.benchmark_rank is not None:
            sheet_name += f"Rank{self.benchmark_rank}"
        if self.benchmark_step is not None:
            sheet_name += f" Step{self.benchmark_step}"
        if not sheet_name:
            sheet_name = "Target and Benchmark"

        sheet_name = f"{self.COMPARE_MODE_TO_DESC.get(self.compare_mode, '')} of {sheet_name}"
        return sheet_name
