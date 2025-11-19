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
from msprof_analyze.compare_tools.compare_backend.comparison_generator import ComparisonGenerator
from msprof_analyze.compare_tools.compare_backend.disaggregate.overall_perf_interface import OverallPerfInterface
from msprof_analyze.compare_tools.compare_backend.utils.compare_args import Args
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.analyze_dict import AnalyzeDict
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class ComparisonInterface:
    def __init__(self, base_profiling_path: str, comparison_profiling_path: str = "",
                 base_step: str = "", comparison_step: str = "", **kwargs):
        self.base_profiling_path = base_profiling_path
        if comparison_profiling_path:
            self._args = Args(base_profiling_path=base_profiling_path,
                              comparison_profiling_path=comparison_profiling_path,
                              base_step=base_step,
                              comparison_step=comparison_step,
                              use_kernel_type=kwargs.get("use_kernel_type", False))

    def compare(self, compare_type: str) -> dict:
        return ComparisonGenerator(AnalyzeDict(vars(self._args))).run_interface(compare_type)

    def disaggregate_perf(self, compare_type: str) -> dict:
        if compare_type != Constant.OVERALL_COMPARE:
            logger.error(f'Invalid compare_type value: {compare_type} which not supported.')
            return {}
        return OverallPerfInterface(self.base_profiling_path).run()
