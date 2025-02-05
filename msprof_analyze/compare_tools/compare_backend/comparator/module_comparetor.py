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
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class ModuleComparator(BaseComparator):
    def __init__(self, origin_data: any, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        if not self._origin_data:
            return
        base_all_data = [data for data in self._origin_data if data[0]]  # index 0 for base module
        base_all_data.sort(key=lambda x: x[0].start_time)
        base_none_data = [data for data in self._origin_data if not data[0]]  # index 0 for base module
        base_none_data.sort(key=lambda x: x[1].start_time)
        index = 0
        for base_module, comparison_module in base_all_data:
            if not comparison_module:
                self._rows.extend(self._bean(base_module, comparison_module).rows)
                continue
            while index < len(base_none_data):
                module = base_none_data[index][1]  # index 1 for comparison module
                if module.start_time < comparison_module.start_time:
                    self._rows.extend(self._bean(None, module).rows)
                    index += 1
                else:
                    break
            self._rows.extend(self._bean(base_module, comparison_module).rows)
        while index < len(base_none_data):
            module = base_none_data[index][1]  # index 1 for comparison module
            self._rows.extend(self._bean(None, module).rows)
            index += 1
        update_order_id(self._rows)
        if not any(row[-1] != Constant.NA for row in self._rows):
            logger.warning("If you want to see the operator's call stack, you must enable with_stack switch.")
