# Copyright (c) 2025, Huawei Technologies Co., Ltd
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
from msprof_analyze.cluster_analyse.prof_bean.step_trace_time_bean import StepTraceTimeBean
from msprof_analyze.prof_common.utils import convert_to_float
from msprof_analyze.prof_common.file_manager import FileManager


class MsprofStepTraceTimeAdapter:
    COMPUTE = "Computing"
    COMM_NOT_OVERLAP = "Communication(Not Overlapped)"
    OVERLAPPED = "Overlapped"
    COMMUNICATION = "Communication"
    FREE = "Free"
    STAGE = "Stage"
    BUBBLE = "Bubble"
    COMM_NOT_OVERLAP_EXCLUDE_RECEIVE = "Communication(Not Overlapped and Exclude Receive)"
    PREPARE = "Preparing"

    def __init__(self, file_path):
        self.file_path = file_path
        self._data = {self.COMPUTE: 0, self.COMM_NOT_OVERLAP: 0, self.OVERLAPPED: 0, self.COMMUNICATION: 0,
                      self.FREE: 0, self.STAGE: 0, self.BUBBLE: 0, self.COMM_NOT_OVERLAP_EXCLUDE_RECEIVE: 0,
                      self.PREPARE: 0}

    @classmethod
    def generate_step_trace_time_db_data(cls):
        return []

    def generate_step_trace_time_data(self):
        json_str = []
        for file_path in self.file_path:
            json_str.extend(FileManager.read_json_file(file_path))
        receive_comm = []
        analysis_data = {}
        for data in json_str:
            event_name = data.get("name", "")
            if event_name in {self.COMMUNICATION, self.COMPUTE, self.FREE, self.COMM_NOT_OVERLAP}:
                analysis_data.setdefault(event_name, []).append(data)
            elif event_name.startswith('hcom_receive'):
                receive_comm.append(data)
        for event_type, event_list in analysis_data.items():
            self._data[event_type] = sum((convert_to_float(event.get("dur", 0)) for event in event_list))
        self._data[self.BUBBLE] = sum((convert_to_float(event.get("dur", 0)) for event in receive_comm))
        self._data[self.COMM_NOT_OVERLAP_EXCLUDE_RECEIVE] = self._data[self.COMM_NOT_OVERLAP] - self._data[self.BUBBLE]
        self._data[self.OVERLAPPED] = self._data[self.COMMUNICATION] - self._data[self.COMM_NOT_OVERLAP]
        e2e_time = self._data[self.FREE] + self._data[self.COMPUTE] + self._data[self.COMM_NOT_OVERLAP]
        self._data[self.STAGE] = e2e_time - self._data[self.BUBBLE]
        return [StepTraceTimeBean(self._data)]
