# Copyright (c) 2023, Huawei Technologies Co., Ltd
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
from common_func.file_manager import FileManager

class CommunicationGroupGenerator:
    def __init__(self, collection_path: str, data_map: dict):
        self.collection_path = collection_path
        self.data_map = data_map
        self.communication_group = {}
        self.rank_comm_dir_dict = {}

    def generate(self):
        self.load_communication_json()

    def load_communication_json(self):
        for rank_id, profiling_dir_path in self.data_map:
            comm_dir = profiling_dir_path.get(Constant.COMM_JSON)
            if comm_dir:
                self.rank_comm_dir_dict[rank_id] = FileManager.read_json_file(comm_dir)
            if not self.rank_comm_dir_dict.get(rank_id):
                print(f"rank {rank_id} does not have a valid communication.json")


    def generate_collective_communication_group(self):
        pass

    def generate_p2p_communication_group(self):
        pass

    def get_all_collective_ops_name(self):
        pass
