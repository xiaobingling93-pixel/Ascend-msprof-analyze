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

from timeline_advice.timeline_advice_base import TimelineAdviceBase
import json

class TorchScheAdvice(TimelineAdviceBase):
    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.cur_data = list()
        self.cur_bottleneck = str()
        self.cur_advice = str()

    def run(self):
        if not self.path_check():
            return self.output_format_data
        self.preparse()
        self.process()
        self.output()
        return self.output_format_data

    def process(self):
        if not self.preparse_data[self.PREPARSE_TYPE.ENQUEUE] or not self.preparse_data[self.PREPARSE_TYPE.DEQUEUE]:
            print("[ERROR] Please set Activity with CPU at least.")
            return
        self.cur_data = self.get_taskq_size()
        sche_ratio = self.get_sche_ratio()
        self.cur_bottleneck = "The proportion of scheduling time is {:.2f}%.".format(sche_ratio * 100)
        self.cur_advice = "Optimize your model to reduce scheduling time by using NPU fused operator or get help from engineers."

    def get_taskq_size(self):
        enque_data = self.preparse_data[self.PREPARSE_TYPE.ENQUEUE]
        deque_data = self.preparse_data[self.PREPARSE_TYPE.DEQUEUE]
        merge_data = enque_data + deque_data
        merge_data.sort(key=lambda x : float(x.get("ts")))
        taskq_size = list()
        cur_size = 0
        for entry in merge_data:
            if entry.get("cat") == "enqueue":
                cur_size += 1
            elif entry.get("cat") == "dequeue":
                cur_size -= 1
            taskq_size.append((entry.get("ts") , cur_size))
        return self.data_format(taskq_size)

    def data_format(self, tasq_size):
        time_stamp = [entry[0] for entry in tasq_size]
        size_info = [entry[1] for entry in tasq_size]
        time_stamp = [int(entry - time_stamp[0]) for entry in time_stamp]
        ret_time_stamp = [i for i in range(time_stamp[-1] + 1)]
        ret_size_info = [0] * (time_stamp[-1] + 1)
        for idx, idx_ret in enumerate(time_stamp):
            ret_size_info[idx_ret] = size_info[idx]
        temp_data = [None] * len(ret_time_stamp)
        for i in range(len(ret_time_stamp)):
            temp_data[i] = (ret_time_stamp[i], ret_size_info[i])
        return temp_data

    def get_sche_ratio(self) -> float:
        all_time, deque_time = 0.0, 0.0
        ratio = 0.0
        for entry in self.preparse_data[self.PREPARSE_TYPE.STEP]:
            all_time += entry.get("dur", 0)
        for entry in self.preparse_data[self.PREPARSE_TYPE.DEQUEUE]:
            deque_time += entry.get("dur", 0)
        if all_time > 0:
            ratio = deque_time / all_time
        return ratio
