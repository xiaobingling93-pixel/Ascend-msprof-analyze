import copy
import logging
from typing import List

from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.common import constant
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.profiling.info_collection import OpInfo
from profiler.advisor.result.item import OptimizeItem, StatisticsItem, OptimizeRecord

logger = logging.getLogger()


class DynamicShapeChecker(OperatorChecker):
    ENABLE_COMPILED_SUGGESTION = "Optimize by enabling compiled operator, such as:\n" \
                                 "`torch_npu.npu.set_compile_mode(jit_compile=False)`\n"
    _SUGGESTION: List[str] = [ENABLE_COMPILED_SUGGESTION]
    _CHECKER = "dynamic shape operator"
    _PROBLEM = "Dynamic shape operator"
    _description = f"Found all operators are dynamic shape"
    _op_list: List[OpInfo] = []
    _tune_op_list: List[str] = []  # record op name to be tuned, and save to tune_ops_file.cfg
    _op_views: List = []

    def __init__(self, cann_version) -> None:
        super().__init__(cann_version=cann_version)

    def check(self, profiling_database) -> bool:
        return self.is_dynamic_shape(profiling_database)

    def make_record(self, profiling_database, rank_id=None) -> OptimizeRecord:
        """
        make record for what and how to optimize
        """

        if rank_id is not None:
            self._PROBLEM = f"rank {rank_id} ".capitalize() + self._PROBLEM.lower()
        optimization_item = OptimizeItem(
            self._PROBLEM,
            self._description,
            self._SUGGESTION
        )
        statistics_item = StatisticsItem("", "", 1)
        return OptimizeRecord(optimization_item, statistics_item)

    def format_operator_result(self, record, limit=-1):
        """
        Format operator result to html
        :param record: profiling check record
        :param limit: Limit number of operator statistics lists.
        :return:
        """
        optimization_item = record.optimization_item
        release_suggestion_list = []
        for suggestion in optimization_item.suggestion:
            release_suggestion = copy.deepcopy(suggestion)
            if release_suggestion == DynamicShapeChecker.ENABLE_COMPILED_SUGGESTION:
                release_suggestion += \
                    f"for details please refer to link : <a href={Config().enable_compiled_tune_url}>LINK</a>"
            release_suggestion_list.append(release_suggestion.replace('\n', '<br>'))
        format_result = {"record": record.__dict__, "suggestion": '<br> '.join(release_suggestion_list)}
        return format_result

    def make_render(self, html_render, record, add_render_list=True, **kwargs):
        priority = kwargs.get("priority")
        return html_render.render_template(key="computation",
                                           template_dir="templates",
                                           template_name="operator_dynamic_shape.html",
                                           format_result=self.format_operator_result(record),
                                           add_render_list=add_render_list,
                                           priority_background_color=priority)
