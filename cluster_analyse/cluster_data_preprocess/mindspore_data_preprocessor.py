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

from cluster_data_preprocess.data_preprocessor import DataPreprocessor


class MindsporeDataPreprocessor(DataPreprocessor):

    def __init__(self, path_list: list):
        super().__init__(path_list)

    def get_data_map(self) -> dict:
        rank_id_map = defaultdict(list)
        for dir_name in self.path_list:
            rank_id = self.get_rank_id(dir_name)
            if rank_id < 0:
                print('[Error]fail to get rankid or rankid invalid.')
                continue
            rank_id_map[rank_id].append(dir_name)

        try:
            for (rank_id, dir_list) in rank_id_map.items():
                dir_list.sort(key=lambda x: x.split('_')[-3])
                self.data_map[rank_id] = dir_list[0]
        except Exception as e:
            raise RuntimeError("Found invalid directory name!") from e
        return self.data_map
