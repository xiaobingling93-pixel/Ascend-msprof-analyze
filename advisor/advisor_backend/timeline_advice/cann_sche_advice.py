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
from common_func_advisor.constant import Constant
from collections import defaultdict

class CannScheAdvice(TimelineAdviceBase):
    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.cur_data = dict()
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
        if not self.preparse_data[self.PREPARSE_TYPE.OVERLAP_CPT]:
            print("[ERROR] Please set Activity with NPU and set Level to Level1 at lease.")
            return
        compute_time, communication_time, free_time = self.get_ratio_from_overlap()
        all_time = compute_time + communication_time + free_time
        self.cur_data = self.get_dev_delay()

        cmp_ratio = compute_time / all_time if all_time > 0 else 0.0
        cmu_ratio = communication_time / all_time if all_time > 0 else 0.0
        free_ratio = free_time / all_time if all_time > 0 else 0.0
        if free_ratio > Constant.CANN_SCHE_THRESHOLD:
            self.cur_advice = "Optimize your model to reduce scheduling time by analyse PyTorch's profiling data."
        self.cur_bottleneck = "The proportion of scheduling time is {:.2f}%, computing time is {:.2f}%," \
            "and communication time is {:.2f}%.".format(free_ratio * 100, cmp_ratio * 100, cmu_ratio * 100)

    def get_ratio_from_overlap(self):
        compute_time = 0.0
        communication_time = 0.0
        free_time = 0.0
        for entry in self.preparse_data[self.PREPARSE_TYPE.OVERLAP_CPT]:
            compute_time += entry.get("dur", 0)
        for entry in self.preparse_data[self.PREPARSE_TYPE.OVERLAP_FREE]:
            free_time += entry.get("dur", 0)
        for entry in self.preparse_data[self.PREPARSE_TYPE.OVERLAP_CMU]:
            communication_time += entry.get("dur", 0)
        return compute_time, communication_time, free_time

    def get_dev_delay(self):
        h2d_data = self.preparse_data[self.PREPARSE_TYPE.HOST_TO_DEVICE]
        h2d_pair_data = defaultdict(list)
        ret_data = list()
        index = 0
        for entry in h2d_data:
            name = entry.get("name")
            if not name:
                continue
            h2d_pair_data[name].append(entry)
            if len(h2d_pair_data[name]) == 2:
                start_idx = 0 if h2d_pair_data[name][0].get("ph") == "s" else 1
                end_idx = 1 if start_idx == 0 else 1
                start_entry = h2d_pair_data[name][start_idx]
                end_entry = h2d_pair_data[name][end_idx]
                ret_data.append((start_entry.get("ts"), end_entry.get("ts") - start_entry.get("ts")))
                index += 1
        ret_data.sort(key=lambda x : x[0])
        return ret_data
