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


class OperatorStatisticComparator(BaseComparator):
    def __init__(self, origin_data: list, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        if not self._origin_data:
            return
        base_op_dict, comparison_op_dict = self._group_by_op_name()
        for op_name, base_data in base_op_dict.items():
            comparison_data = comparison_op_dict.pop(op_name, [])
            self._rows.append(self._bean(op_name, base_data, comparison_data).row)
        for op_name, comparison_data in comparison_op_dict.items():
            self._rows.append(self._bean(op_name, [], comparison_data).row)
        self._rows.sort(key=lambda x: x[-2], reverse=True)  # order by diff column
        update_order_id(self._rows)

    def _group_by_op_name(self):
        base_op_dict, comparison_op_dict = {}, {}
        for base_op, comparison_op in self._origin_data:
            if base_op:
                base_op_dict.setdefault(base_op.name, []).append(base_op)
            if comparison_op:
                comparison_op_dict.setdefault(comparison_op.name, []).append(comparison_op)
        return base_op_dict, comparison_op_dict
