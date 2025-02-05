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


class OperatorComparator(BaseComparator):
    def __init__(self, origin_data: any, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        if not self._origin_data:
            return
        self._rows = [None] * (len(self._origin_data))
        for index, (base_op, comparison_op) in enumerate(self._origin_data):
            self._rows[index] = self._bean(index, base_op, comparison_op).row
