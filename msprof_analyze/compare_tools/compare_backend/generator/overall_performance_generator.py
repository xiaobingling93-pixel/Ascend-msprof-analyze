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
from msprof_analyze.compare_tools.compare_backend.comparator.overall_performance_comparator \
    import OverallPerformanceComparator
from msprof_analyze.compare_tools.compare_backend.compare_bean.profiling_info import ProfilingInfo
from msprof_analyze.compare_tools.compare_backend.generator.base_generator import BaseGenerator
from msprof_analyze.compare_tools.compare_backend.view.screen_view import ScreenView
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class OverallPerformanceGenerator(BaseGenerator):
    def __init__(self, profiling_data_dict: dict, args: any):
        super().__init__(profiling_data_dict, args)

    def compare(self):
        if not self._args.enable_profiling_compare:
            return
        self._result_data = OverallPerformanceComparator(self._profiling_data_dict, ProfilingInfo).generate_data()

    def generate_view(self):
        if not self._result_data:
            return
        ScreenView(self._result_data).generate_view()
        logger.info("The OverallMetrics sheet page is more comprehensive for the disaggregate of performance data, "
                     "and it is recommended to view the overall performance comparison results from "
                     "the performance_comparison_result_*.xlsx.")
