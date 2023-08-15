# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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


class StepTraceTimeBean:
    STEP = "Step"
    COMPLEMENT_HEADER = ["Step", "Type", "Index"]

    def __init__(self, data: list):
        self._data = data

    @property
    def row(self) -> list:
        row = []
        for field_name in self._data.keys():
            if field_name == self.STEP:
                continue
            row.append(float(self._data.get(field_name, )))
        return row

    @property
    def step(self) -> float:
        return float(self._data.get(self.STEP, ''))

    @property
    def all_headers(self) -> list:
        return self.COMPLEMENT_HEADER + list(self._data.keys())[1:]
