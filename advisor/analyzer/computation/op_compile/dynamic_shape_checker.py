import copy
import logging
from typing import List

from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.common import constant
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
        less_than_cann800_list = [constant.CANN_VERSION_C30, constant.CANN_VERSION_C13, constant.CANN_VERSION_C15]
        # CANN 8.0.0 之前从 ge_info 中获取 op_state 属性，进行动态 shape 逻辑判断
        if self.cann_version in less_than_cann800_list:
            if hasattr(profiling_database, "ge_info"):
                ge_info = profiling_database.ge_info
                static_shape_operators = ge_info.get_static_shape_operators()
                if len(static_shape_operators) == 0:
                    OperatorChecker.IS_ALL_OPERATOR_DYNAMIC_SHAPE = True
                    return True
            else:
                logger.warning(
                    "Skip dynamic shape checker because of not containing ge_info.db file in host filefloder.\n"
                    "To enable dynamic shape checker, please try to set data_simplification=False in experimental_config.\n"
                    "More details please refer to link : %s", constant.ASCEND_PROFILER_URL)
        else:
            # CANN 8.0.0 之后 op_state 属性从 op_summary 文件中获取
            if hasattr(profiling_database, "op_summary"):
                static_shape_operators = profiling_database.op_summary.get_static_shape_operators()
                if len(static_shape_operators) == 0:
                    OperatorChecker.IS_ALL_OPERATOR_DYNAMIC_SHAPE = True
                    return True
            else:
                logger.warning(
                        "Skip dynamic shape checker because of not containing op_summary.csv file in current filefloder."
                    )
            
        return False

    def make_record(self, profiling_database) -> OptimizeRecord:
        """
        make record for what and how to optimize
        """

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
                    f"for details please refer to link : <a href={constant.ENABLE_COMPILED_TUNE_URL}>LINK</a>"
            release_suggestion_list.append(release_suggestion.replace('\n', '<br>'))
        format_result = {"record": record.__dict__, "suggestion": '<br> '.join(release_suggestion_list)}
        return format_result

    def make_render(self, html_render, record):
        html_render.render_template(key="computation",
                                    template_dir="templates",
                                    template_name="operator_dynamic_shape.html",
                                    format_result=self.format_operator_result(record))
