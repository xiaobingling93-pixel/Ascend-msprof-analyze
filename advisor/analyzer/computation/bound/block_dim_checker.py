# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from typing import List

from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.prof_common.constant import Constant
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from profiler.prof_common.additional_args_manager import AdditionalArgsManager

logger = logging.getLogger()


class BlockDimChecker(OperatorChecker):
    _SUGGESTION: List[str] = []
    _CHECKER = "block dim"
    _aicore_num = 0
    _aiv_num = 0
    _ITEMS = [
        "op_name", "op_type", "task_type", "task_duration", "income", "block_dim", "mix_block_dim", "input_shapes",
        "input_data_types", "input_formats", "output_shapes", "output_data_types", "output_formats"
    ]

    def __init__(self, cann_version):
        super(BlockDimChecker, self).__init__(cann_version=cann_version)
        self._init_prompt_by_language()

    def pre_check(self, profiling_data) -> bool:
        return not self.is_dynamic_shape(profiling_data)

    def make_render(self, html_render, record, add_render_list=True, **kwargs):
        priority = kwargs.get("priority")
        return html_render.render_template(key="computation",
                                           template_dir="templates",
                                           template_name="operator_block_dim.html",
                                           format_result=self.format_operator_result(record,
                                                                                     Constant.OPERATOR_OUT_TOPK),
                                           add_render_list=add_render_list,
                                           priority_background_color=priority,
                                           rank=kwargs.get("rank"))

    def get_core_num(self, op_info):
        """
        get core num of task type
        """
        if op_info.task_type == "AI_CORE" or not self._aiv_num:
            core_num = self._aicore_num
        else:
            core_num = self._aiv_num
        return core_num

    def _check_data(self, profiling_data):
        self.format_suggestion_content(profiling_data)
        if not self._check_summary(profiling_data):
            return False
        if not Config().get_config("ai_core_num"):
            logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "ai core num in info.json file")
            return False
        summary = profiling_data.op_summary
        op_info = summary.op_list[0]
        if not hasattr(op_info, "block_dim"):
            logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "block dim in op summary")
            return False
        if Config().get_config("ai_core_num"):
            try:
                self._aicore_num = int(Config().get_config("ai_core_num"))
            except ValueError as e:
                logger.warning("get ai_core_num failed, please check info.json： %s", e)
                return False
        if Config().get_config("aiv_num"):
            try:
                self._aiv_num = int(Config().get_config("aiv_num"))
            except ValueError as e:
                logger.warning("get aiv_num failed, please check info.json： %s", e)

        self._description = self._description.format(self._aicore_num)
        if self._aiv_num:
            self._description += self.aiv_num_desc.format(self._aiv_num)
        self._description += self.top_duration_op_desc.format(OperatorChecker._MAX_TUNE_OP_NUM)
        return True

    def _check_operator(self, op_info) -> bool:
        if op_info.task_type not in ["AI_CORE", "AI_VECTOR_CORE", "MIX_AIC"]:
            return False
        block_dim = int(op_info.block_dim)
        core_num = self.get_core_num(op_info)
        if core_num == 0:
            logger.error("The aicore number is zero. BlockDimChecker is skipped. Please check the info.json file.")
            return False
        if block_dim % core_num == 0:
            return False
        is_block_dim = op_info.task_type == "MIX_AIC" and hasattr(op_info, "mix_block_dim")
        if is_block_dim and self._aiv_num and int(op_info.mix_block_dim) % self._aiv_num == 0:
            return False
        return True

    def _init_prompt_by_language(self):
        language = AdditionalArgsManager().language
        if language == "en":
            from profiler.advisor.display.prompt.en.block_dim_prompt import BlockDimPrompt
        else:
            from profiler.advisor.display.prompt.cn.block_dim_prompt import BlockDimPrompt

        self._PROBLEM = BlockDimPrompt.PROBLEM
        self._description = BlockDimPrompt.DESCRIPTION
        self.aiv_num_desc = BlockDimPrompt.AIV_NUM_DESCRIPTION
        self.top_duration_op_desc = BlockDimPrompt.TOP_DURATION_OP_DESCRIPTION
