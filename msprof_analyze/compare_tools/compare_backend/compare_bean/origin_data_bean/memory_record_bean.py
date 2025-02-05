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
from msprof_analyze.compare_tools.compare_backend.utils.common_func import convert_to_float


class MemoryRecordBean:
    __slots__ = ['_data', '_total_reserved_mb']

    def __init__(self, data: dict):
        self._data = data
        self._total_reserved_mb = 0.0
        self.init()

    @property
    def total_reserved_mb(self) -> float:
        return convert_to_float(self._total_reserved_mb)

    def init(self):
        self._total_reserved_mb = self._data.get("Total Reserved(MB)", 0)
