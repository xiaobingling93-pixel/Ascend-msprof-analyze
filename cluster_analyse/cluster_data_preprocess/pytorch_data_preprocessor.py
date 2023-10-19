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

from collections import defaultdict
from common_func.file_manager import FileManager
import os


class PytorchDataPreprocessor:
    PROFILER_INFO_HEAD = 'profiler_info_'
    PROFILER_INFO_EXTENSION = '.json'

    def __init__(self, path: str):
        self.path = os.path.realpath(path)

    def get_data_map(self) -> dict:
        ascend_pt_dirs = []
        for root, dirs, files in os.walk(self.path):
            for dir_name in dirs:
                if dir_name.endswith("ascend_pt"):
                    ascend_pt_dirs.append(os.path.join(root, dir_name))
        rank_id_map = defaultdict(list)
        for dir_name in ascend_pt_dirs:
            rank_id = self.get_rank_id(dir_name)
            if rank_id < 0:
                print('[Error]fail to get rankid or rankid invalid.')
                continue
            rank_id_map[rank_id].append(dir_name)

        ret_dict = dict()
        for (rank_id, dir_list) in rank_id_map.items():
            dir_list.sort(key=lambda x: x.split('_')[-3])
            ret_dict[rank_id] = os.path.join(self.path, dir_list[0])
        return ret_dict

    def get_rank_id(self, dir_name: str) -> int:
        files = os.listdir(dir_name)
        for file_name in files:
            if file_name.startswith(self.PROFILER_INFO_HEAD) and file_name.endswith(self.PROFILER_INFO_EXTENSION):
                return int(file_name[len(self.PROFILER_INFO_HEAD): -1 * len(self.PROFILER_INFO_EXTENSION)])
        return -1
