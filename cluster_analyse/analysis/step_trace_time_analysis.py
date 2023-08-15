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

import os

from common_func.constant import Constant
from collections import defaultdict
from common_func.file_manager import FileManager
from prof_bean.step_trace_time_bean import StepTraceTimeBean


class StepTraceTimeAnalysis:
    CLUSTER_TRACE_TIME_CSV = "cluster_step_trace_time.csv"

    def __init__(self, param: dict):
        self.collection_path = param.get(Constant.COLLECTION_PATH)
        self.data_map = param.get(Constant.DATA_MAP)
        self.communication_group = param.get(Constant.COMMUNICATION_GROUP)
        self.step_time_dict = {}
        self.step_data_list = []

    @staticmethod
    def get_max_data_row(data_group_list: list):
        if not data_group_list:
            return []
        ret = []
        for idx in range(len(data_group_list[0])):
            max_val = 0
            for idy in range(len(data_group_list)):
                max_val = max(max_val, data_group_list[idy][idx])
            ret.append(max_val)
        return ret

    def run(self):
        self.load_step_trace_time_data()
        self.analyze_step_time()
        self.dump_data()

    def dump_data(self):
        if not self.step_data_list:
            print("Can't get step time info!")
        headers = self.get_headers()
        FileManager.create_csv_file(self.collection_path, self.step_data_list, self.CLUSTER_TRACE_TIME_CSV, headers)

    def load_step_trace_time_data(self):
        for rank_id, profiling_dir_path in self.data_map.items():
            step_time_file = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.STEP_TIME_CSV)
            if step_time_file:
                self.step_time_dict[rank_id] = FileManager.read_csv_file(step_time_file, StepTraceTimeBean)
            if not self.step_time_dict.get(rank_id):
                print(f"rank {rank_id} does not have a valid step_trace_time.json.")

    def analyze_step_time(self):
        for rank_id, data_bean_list in self.step_time_dict.items():
            for data_bean in data_bean_list:
                self.step_data_list.append([data_bean.step, Constant.RANK, rank_id] + data_bean.row)
        stage_list = self.communication_group.get(Constant.P2P)
        if not stage_list:
            return
        step_group_dict = {}
        for data_list in self.step_data_list:
            stage_group = 'None'
            for stage in stage_list:
                if data_list[2] in stage:
                    stage_group = tuple(stage)
                    break
            key = (data_list[0], stage_group)
            step_group_dict.setdefault(key, []).append(data_list[3:])

        for key, data_group_list in step_group_dict.items():
            self.step_data_list.append([key[0], Constant.STAGE, key[1]] + self.get_max_data_row(data_group_list))

    def get_headers(self):
        if self.step_time_dict:
            for rank in self.step_time_dict:
                if self.step_time_dict.get(rank):
                    return self.step_time_dict[rank][0].all_headers
        return []
