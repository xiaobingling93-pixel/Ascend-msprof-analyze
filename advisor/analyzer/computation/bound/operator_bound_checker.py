import logging
from typing import List

from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.common import constant
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from profiler.advisor.utils.utils import to_percent

logger = logging.getLogger()


class OperatorBoundChecker(OperatorChecker):
    _MIN_TASK_DURATION = 20  # min task duration 20us
    _CHECKER = "operator no bound"
    _PROBLEM = "operator no bound"
    _SUGGESTION: List[str] = []
    _description = (
            f"There is no mte, cube, vector, scalar ratio is more than {to_percent(Config().operator_bound_ratio)};\n" +
            f"Top task duration operators need to be tuned are as follows: \n")
    _ITEMS = [
        "op_name", "op_type", "task_type", "task_duration", "vec_ratio", "mac_ratio", "scalar_ratio", "mte1_ratio",
        "mte2_ratio", "mte3_ratio", "block_dim", "input_shapes", "input_data_types", "input_formats", "output_shapes",
        "output_data_types", "output_formats"
    ]

    def pre_check(self, profiling_data) -> bool:
        return not self.is_dynamic_shape(profiling_data)

    def _check_data(self, data):
        self.format_suggestion_content(data)
        if not self._check_summary(data):
            return False
        for op_info in data.op_summary.op_list:
            return self._check_operator(op_info)

        logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "ratio in op summary")
        return False

    def _check_operator(self, op_info) -> bool:
        bound_list = ["vec_ratio", "mac_ratio", "scalar_ratio", "mte1_ratio", "mte2_ratio", "mte3_ratio"]
        ratio_list = [self.get_ratio(op_info, attr) for attr in bound_list]
        if not any(ratio_list):
            return False  # no data, skip check
        if any(ratio and ratio > Config().operator_bound_ratio for ratio in ratio_list):
            return False
        return True

    def make_render(self, html_render, record, add_render_list=True, **kwargs):
        priority = kwargs.get("priority")
        return html_render.render_template(key="computation",
                                           template_dir="templates",
                                           template_name="operator_no_bound.html",
                                           format_result=self.format_operator_result(record,
                                                                                     constant.OPERATOR_OUT_TOPK),
                                           add_render_list=add_render_list,
                                           priority_background_color=priority,
                                           rank=kwargs.get("rank"))