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
from decimal import Decimal

from msprof_analyze.compare_tools.compare_backend.utils.common_func import convert_to_float, convert_to_decimal


class OperatorMemoryBean:
    __slots__ = ['_data', '_name', '_size', '_allocation_time', '_release_time']
    NA = "N/A"

    def __init__(self, data: dict):
        self._data = data.copy()
        self._name = ""
        self._size = 0.0
        self._allocation_time = Decimal(0)
        self._release_time = Decimal(0)
        self.init()

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> float:
        return convert_to_float(self._size)

    @property
    def allocation_time(self) -> Decimal:
        if not self._allocation_time or self._allocation_time == self.NA:
            return Decimal(0)
        return convert_to_decimal(self._allocation_time)

    @property
    def release_time(self) -> Decimal:
        if not self._release_time or self._release_time == self.NA:
            return Decimal(0)
        return convert_to_decimal(self._release_time)

    def init(self):
        self._name = self._data.get("Name", "")
        self._size = self._data.get("Size(KB)", 0)
        self._allocation_time = self._data.get("Allocation Time(us)", 0)
        self._release_time = self._data.get("Release Time(us)", 0)

    def is_cann_op(self):
        return "cann::" in self._name
