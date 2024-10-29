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
    ENABLE_COMPILED_SUGGESTION = "1. Please try to set environment by execute `export HOST_CACHE_CAPACITY=20`.\n." \
                                 "2. Please place the following code at the entrance of the python script to disable jit compile.\n " \
                                 "Code: `torch_npu.npu.set_compile_mode(jit_compile=False);\n " \
                                 "torch_npu.npu.config.allow_internal_format = False`.\n"
    _SUGGESTION: List[str] = [ENABLE_COMPILED_SUGGESTION]
    _CHECKER = "dynamic shape operator"
    _PROBLEM = "Dynamic shape operator"
    _description = f"Found all operators are dynamic shape"
    _op_list: List[OpInfo] = []
    _tune_op_list: List[str] = []  # record op name to be tuned, and save to tune_ops_file.cfg
    _op_views: List = []

    def __init__(self, cann_version) -> None:
        super().__init__(cann_version=cann_version)

    def check(self, profiling_data) -> bool:
        return self.is_dynamic_shape(profiling_data)

    def make_record(self, profiling_data, rank=None) -> OptimizeRecord:
        """
        make record for what and how to optimize
        """

        if rank is not None:
            self._PROBLEM = f"rank {rank} ".capitalize() + self._PROBLEM.lower()
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
                    f"for details please refer to link : <a href={Config().enable_compiled_tune_url} target='_blank'>LINK</a>"
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
                                           priority_background_color=priority,
                                           rank=kwargs.get("rank"))
