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
import glob
from collections import defaultdict
import os

from common_func.constant import Constant
from common_func.file_manager import FileManager
from common_func.path_manager import PathManager


class PytorchDataPreprocessor:
    PROFILER_INFO_HEAD = 'profiler_info_'
    PROFILER_INFO_EXTENSION = '.json'
    JSON_RESULT_INFO = "*.json"
    CSV_RESULT_INFO = "*.csv"

    def __init__(self, path_list: str):
        self.path_list = path_list
        self.db_count = 0
        self.text_count = 0
        self.valid_data_flag = True

    def get_data_map(self) -> dict:
        rank_id_map = defaultdict(list)
        for dir_name in self.path_list:
            rank_id = self.get_rank_id(dir_name)
            if rank_id < 0:
                print('[Error]fail to get rankid or rankid invalid.')
                continue
            folder_path = os.path.join(dir_name, Constant.SINGLE_OUTPUT)
            db_files = glob.glob(os.path.join(folder_path, Constant.DB_COMMUNICATION_ANALYZER))
            text_files = (glob.glob(os.path.join(folder_path, self.JSON_RESULT_INFO)) +
                          glob.glob(os.path.join(folder_path, self.CSV_RESULT_INFO)))
            if text_files and db_files:
                self.valid_data_flag = False
                print(f"[ERROR] Rank {rank_id} has both db and text files")
                continue
            if db_files:
                self.db_count += 1
            elif text_files:
                self.text_count += 1
            else:
                print(f"[WARNING] Rank {rank_id} has no valid files")
                continue
            rank_id_map[rank_id].append(dir_name)

        ret_dict = dict()
        try:
            for (rank_id, dir_list) in rank_id_map.items():
                dir_list.sort(key=lambda x: x.split('_')[-3])
                ret_dict[rank_id] = dir_list[0]
        except Exception as e:
            raise RuntimeError("Found invalid directory name!") from e
        return ret_dict

    def get_rank_id(self, dir_name: str) -> int:
        files = os.listdir(dir_name)
        for file_name in files:
            if file_name.startswith(self.PROFILER_INFO_HEAD) and file_name.endswith(self.PROFILER_INFO_EXTENSION):
                rank_id_str = file_name[len(self.PROFILER_INFO_HEAD): -1 * len(self.PROFILER_INFO_EXTENSION)]
                try:
                    rank_id = int(rank_id_str)
                except ValueError:
                    rank_id = -1
                return rank_id
        return -1

    def get_data_type(self):
        if self.valid_data_flag:
            if self.db_count != 0 and self.text_count != 0:
                return None
            if self.db_count != 0:
                return Constant.DB
            if self.text_count != 0:
                return True, Constant.TEXT
        else:
            return None
