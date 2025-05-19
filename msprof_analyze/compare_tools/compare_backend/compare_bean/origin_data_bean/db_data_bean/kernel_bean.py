# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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
from msprof_analyze.prof_common.constant import Constant


class KernelBean:

    def __init__(self, data):
        self._data = data

    @property
    def name(self):
        return self._data.get("OpName", "")

    @property
    def dur(self):
        return self._data.get("Duration") / Constant.NS_TO_US if self._data.get("Duration") else 0

    @property
    def task_id(self):
        return self._data.get("TaskId", "")

    @property
    def task_type(self):
        return self._data.get("TaskType", "")

    @property
    def input_shapes(self):
        return self._data.get("InputShapes", "")

    @property
    def connection_id(self):
        return self._data.get("connectionId", "")
