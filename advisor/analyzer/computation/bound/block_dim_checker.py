import logging

from typing import List

from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.common import constant
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset

logger = logging.getLogger()


class BlockDimChecker(OperatorChecker):
    _SUGGESTION: List[str] = []
    _CHECKER = "block dim"
    _PROBLEM = "block dim"
    _description = "some operator does not make full use of {} ai core"
    _ITEMS = [
        "op_name", "op_type", "task_type", "task_duration", "income", "block_dim", "mix_block_dim", "input_shapes",
        "input_data_types", "input_formats", "output_shapes", "output_data_types", "output_formats"
    ]

    def pre_check(self, profiling_data) -> bool:
        return not self.is_dynamic_shape(profiling_data)

    def _check_data(self, data):
        self.format_suggestion_content(data)
        if not self._check_summary(data):
            return False
        if not Config().get_config("ai_core_num"):
            logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "ai core num in info.json file")
            return False
        summary = data.op_summary
        op_info = summary.op_list[0]
        if not hasattr(op_info, "block_dim"):
            logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "block dim in op summary")
            return False
        if Config().get_config("ai_core_num"):
            self._aicore_num = int(Config().get_config("ai_core_num"))
        if Config().get_config("aiv_num"):
            self._aiv_num = int(Config().get_config("aiv_num"))
        self._description = self._description.format(self._aicore_num)
        if self._aiv_num:
            self._description += f" or {self._aiv_num} ai vector core"
        self._description += f";\n Top-{OperatorChecker._MAX_TUNE_OP_NUM} operator of " \
                             "task duration are as follows:\n"
        return True

    def make_render(self, html_render, record):
        html_render.render_template(key="computation",
                                    template_dir="templates",
                                    template_name="operator_block_dim.html",
                                    format_result=self.format_operator_result(record, constant.OPERATOR_OUT_TOPK))

    def _check_operator(self, op_info) -> bool:
        if op_info.task_type not in ["AI_CORE", "AI_VECTOR_CORE", "MIX_AIC"]:
            return False
        block_dim = int(op_info.block_dim)
        core_num = self.get_core_num(op_info)
        if block_dim % core_num == 0:
            return False
        if op_info.task_type == "MIX_AIC" and hasattr(op_info, "mix_block_dim") \
                and self._aiv_num and int(op_info.mix_block_dim) % self._aiv_num == 0:
            return False
        return True

    def get_core_num(self, op_info):
        """
        get core num of task type
        """
        if op_info.task_type == "AI_CORE" or not self._aiv_num:
            core_num = self._aicore_num
        else:
            core_num = self._aiv_num
        return core_num
