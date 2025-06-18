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
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class StepTraceTimeBean:
    STEP = "Step"
    COMPLEMENT_HEADER = ["Step", "Type", "Index"]
    EXCLUDE_HEADER = ["Step", "Device_id"]

    def __init__(self, data: list):
        self._data = data

    @property
    def row(self) -> list:
        row = []
        for field_name in self._data.keys():
            if field_name in self.EXCLUDE_HEADER:
                continue
            try:
                row.append(float(self._data.get(field_name, )))
            except Exception as e:
                logger.warning(e)
                row.append(0)
        return row

    @property
    def step(self) -> str:
        return self._data.get(self.STEP, '')

    @property
    def all_headers(self) -> list:
        headers = [filed_name for filed_name in self._data.keys() if filed_name not in self.EXCLUDE_HEADER]
        return self.COMPLEMENT_HEADER + headers
