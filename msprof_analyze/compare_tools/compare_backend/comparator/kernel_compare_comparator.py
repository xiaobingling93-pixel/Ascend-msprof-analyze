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
from msprof_analyze.compare_tools.compare_backend.comparator.base_comparator import BaseComparator
from msprof_analyze.compare_tools.compare_backend.utils.common_func import update_order_id
from msprof_analyze.prof_common.constant import Constant


class KernelCompareComparator(BaseComparator):
    def __init__(self, origin_data: list, bean: any):
        super().__init__(origin_data, bean)

    @classmethod
    def _aggregated_kernel_by_type_and_shape(cls, kernels: dict):
        result_dict = {}
        for type_shape, shape_values in kernels.items():
            for shape, kernel_data in shape_values.items():
                kernel = [single[1] for single in kernel_data]
                result_list = [type_shape, shape, sum(kernel), len(kernel), max(kernel), min(kernel)]
                result_dict.setdefault(f"{type_shape}{shape}", []).extend(result_list)
        return result_dict

    def _compare(self):
        if not self._origin_data:
            return
        base_kernels = self._origin_data.get(Constant.BASE_DATA, {})
        comparison_kernels = self._origin_data.get(Constant.COMPARISON_DATA, {})
        if not base_kernels or not comparison_kernels:
            return
        base_aggregated_kernels = self._aggregated_kernel_by_type_and_shape(base_kernels)
        comparison_aggregated_kernels = self._aggregated_kernel_by_type_and_shape(comparison_kernels)
        for type_shape, base_data in base_aggregated_kernels.items():
            comparsion_data = comparison_aggregated_kernels.pop(type_shape, [])
            self._rows.append(self._bean(base_data, comparsion_data).row)
        if comparison_aggregated_kernels:
            for _, comparison_data in comparison_aggregated_kernels.items():
                self._rows.append(self._bean([], comparison_data).row)
        update_order_id(self._rows)
