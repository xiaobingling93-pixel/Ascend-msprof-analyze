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

from advice_base import AdviceBase
from abc import abstractmethod
import os
import json
from collections import defaultdict

class TimelineAdviceBase(AdviceBase):
    class PREPARSE_TYPE:
        OPTIMIZER = 0
        STEP = 1
        OVERLAP_CPT = 2
        OVERLAP_FREE = 3
        OVERLAP_CMU =4
        ENQUEUE = 5
        DEQUEUE = 6
        HOST_TO_DEVICE = 7

    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.trace_view_path = ""
        self.has_preparse = False
        self.preparse_data = defaultdict(list)

    def path_check(self):
        """
        check whether input path is valid
        """
        if not os.path.exists(self.collection_path):
            print("[ERROR] Path: {} is not exist.".format(self.collection_path))
            return False
        if os.path.isdir(self.collection_path) and self.collection_path.endswith("ascend_pt"):
            self.trace_view_path = os.path.join(self.collection_path, "ASCEND_PROFILER_OUTPUT", "trace_view.json")
            if not os.path.exists(self.trace_view_path):
                print("[ERROR] trace_view.json is not exist in the Path: {}.".format(os.path.join(self.collection_path, "ASCEND_PROFILER_OUTPUT")))
                return False
        elif os.path.isfile(self.collection_path) and os.path.basename(self.collection_path) == "trace_view.json":
            self.trace_view_path = self.collection_path
        else:
            print("[ERROR] Please input ascend_pt or trace_view.json.")
            return False
        print("[INFO] Start to analyse the target file: {}".format(self.trace_view_path))
        return True
        

    @abstractmethod
    def run(self):
        """
        analyze profiling data and advice
        """

    @abstractmethod
    def output(self):
        """
        output relevant data
        """
        self.output_format_data[self.DATA] = self.cur_data
        self.output_format_data[self.BOTTLENECK] = self.cur_bottleneck
        self.output_format_data[self.ADVICE] = self.cur_advice

    def preparse(self):
        if self.has_preparse:
            return
        with open(self.trace_view_path, 'r') as f:
            json_reader = json.load(f)
            for entry in json_reader:
                name = entry.get("name", None)
                cat = entry.get("cat", None)
                if name and name.startswith("Optimizer.step#") and name.endswith(".step"):
                    self.preparse_data[self.PREPARSE_TYPE.OPTIMIZER].append(entry)
                elif name and name.startswith("ProfilerStep#"):
                    self.preparse_data[self.PREPARSE_TYPE.STEP].append(entry)
                elif name == "Computing":
                    self.preparse_data[self.PREPARSE_TYPE.OVERLAP_CPT].append(entry)
                elif name == "Free":
                    self.preparse_data[self.PREPARSE_TYPE.OVERLAP_FREE].append(entry)
                elif name == "Communication(Not Overlapped)":
                    self.preparse_data[self.PREPARSE_TYPE.OVERLAP_CMU].append(entry)

                if cat == "enqueue":
                    self.preparse_data[self.PREPARSE_TYPE.ENQUEUE].append(entry)
                elif cat == "dequeue":
                    self.preparse_data[self.PREPARSE_TYPE.DEQUEUE].append(entry)
                elif cat == "HostToDevice":
                    self.preparse_data[self.PREPARSE_TYPE.HOST_TO_DEVICE].append(entry)
        sort_list = [
            self.PREPARSE_TYPE.OVERLAP_CPT,
            self.PREPARSE_TYPE.OVERLAP_FREE,
            self.PREPARSE_TYPE.OVERLAP_CMU,
            self.PREPARSE_TYPE.ENQUEUE,
            self.PREPARSE_TYPE.DEQUEUE,
            self.PREPARSE_TYPE.HOST_TO_DEVICE
        ]
        for sort_entry in sort_list:
            if self.preparse_data[sort_entry]:
                self.preparse_data[sort_entry].sort(key=lambda x : float(x.get("ts")))
        self.preparse = True
        