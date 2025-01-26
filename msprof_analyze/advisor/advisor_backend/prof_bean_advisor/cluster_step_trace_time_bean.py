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


class ClusterStepTraceTimeBean:
    STEP = "Step"
    TYPE = "Type"
    INDEX = "Index"
    COMPUTING = "Computing"
    COMMUNICATION = "Communication(Not Overlapped)"
    FREE = "Free"

    def __init__(self, data: dict):
        self._data = data

    @property
    def step(self) -> str:
        return self._data.get(self.STEP, '')

    @property
    def type(self) -> str:
        return self._data.get(self.TYPE, '')

    @property
    def index(self) -> int:
        try:
            return int(self._data.get(self.INDEX))
        except ValueError as e:
            msg = "[ERROR] Cluster step trace time.csv has invalid value in column 'Index'."
            raise ValueError(msg) from e

    @property
    def compute(self) -> float:
        try:
            return float(self._data.get(self.COMPUTING, ''))
        except ValueError as e:
            msg = "[ERROR] Cluster step trace time.csv has invalid value in column 'Computing'."
            raise ValueError(msg) from e

    @property
    def communication(self) -> float:
        try:
            return float(self._data.get(self.COMMUNICATION, ''))
        except ValueError as e:
            msg = "[ERROR] Cluster step trace time.csv has invalid value in column 'Communication'."
            raise ValueError(msg) from e

    @property
    def free(self) -> float:
        try:
            return float(self._data.get(self.FREE, ''))
        except ValueError as e:
            msg = "[ERROR] Cluster step trace time.csv has invalid value in column 'Free'."
            raise ValueError(msg) from e

