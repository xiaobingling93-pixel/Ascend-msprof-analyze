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
from msprof_analyze.prof_common.constant import Constant


class OverallInterface:
    def __init__(self, overall_data: dict):
        self._overall_data = overall_data

    def run(self):
        data = {Constant.BASE_DATA: self._overall_data.get(Constant.BASE_DATA).overall_metrics,
                Constant.COMPARISON_DATA: self._overall_data.get(Constant.COMPARISON_DATA).overall_metrics}
        return OverallPerformanceComparator(data, ProfilingInfo).generate_data()
