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
from collections import defaultdict


class CommunicationGroupGenerator:
    COMMUNICATION_GROUP_JSON = "communication_group.json"

    def __init__(self, collection_path: str, data_map: dict):
        self.collection_path = collection_path
        self.data_map = data_map
        self.communication_group = {}
        self.collective_group_dict = defaultdict(set)
        self.p2p_group_dict = defaultdict(list)
        self.rank_comm_dir_dict = {}
        self.communication_ops = []

    def generate(self):
        self.load_communication_json()
        self.analyze_communication_ops()
        self.generate_collective_communication_group()
        self.generate_p2p_communication_group()
        FileManager.create_json_file(self.collection_path, self.communication_group, self.COMMUNICATION_GROUP_JSON)
        return self.communication_group, self.collective_group_dict, self.communication_ops

    def analyze_communication_ops(self):
        for rank_id, rank_id_dict in self.rank_comm_dir_dict.items():
            for step_id, step_id_dict in rank_id_dict.items():
                if not isinstance(step_id_dict, dict):
                    print(f"rank{rank_id}'s communication.json has a wrong data struct.")
                    continue
                for comm_op_type, comm_op_dict in step_id_dict.items():
                    if comm_op_type == Constant.COLLECTIVE:
                        self.get_collective_ops_name(rank_id, comm_op_dict)
                    elif comm_op_type == Constant.P2P:
                        pass
                    else:
                        print(f"rank{rank_id}'s communication.json has no p2p or collective.")
                        continue
                    self.add_communication_ops(rank_id, step_id, comm_op_type, comm_op_dict)

    def load_communication_json(self):
        for rank_id, profiling_dir_path in self.data_map.items():
            comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_JSON)
            if comm_dir:
                self.rank_comm_dir_dict[rank_id] = FileManager.read_json_file(comm_dir)
            if not self.rank_comm_dir_dict.get(rank_id):
                print(f"rank {rank_id} does not have a valid communication.json.")

    def generate_collective_communication_group(self):
        self.communication_group[Constant.COLLECTIVE] = [list(group) for group in self.collective_group_dict.values()]

    def generate_p2p_communication_group(self):
        stage_group = {}
        for rank_set in self.collective_group_dict.values():
            unioned_set = {}
            remove_key = []
            for first_rank, stage in stage_group.items():
                if UnionFind.is_connected(rank_set, stage):
                    unioned_set = UnionFind.union(rank_set, stage, unioned_set)
                    remove_key.append(first_rank)
            if unioned_set:
                for key in remove_key:
                    del stage_group[key]
                stage_group[min(unioned_set)] = unioned_set
            else:
                stage_group[min(rank_set)] = rank_set
        first_rank_sort_list = sorted([first_rank for first_rank in stage_group])
        self.communication_group[Constant.P2P] = \
            [list(stage_group.get(first_rank, {})) for first_rank in first_rank_sort_list]

    def get_collective_ops_name(self, rank_id: int, comm_op_dict: dict):
        for comm_op in comm_op_dict:
            if comm_op.startswith('Total'):
                continue
            group_name = comm_op.split('@')[-1]
            self.collective_group_dict[group_name].add(rank_id)

    def add_communication_ops(self, rank_id: str, step_id: str, comm_op_type: str, comm_op_dict: dict):
        for comm_op in comm_op_dict:
            if comm_op.startswith('Total'):
                continue
            group_name = comm_op.split('@')[-1]
            self.communication_ops.append({
                Constant.RANK_ID: rank_id,
                Constant.STEP_ID: step_id,
                Constant.COMM_OP_TYPE: comm_op_type,
                Constant.COMM_OP_NAME: comm_op,
                Constant.GROUP_NAME: group_name,
                Constant.COMM_OP_INFO: comm_op_dict.get(comm_op)
            })


class UnionFind(object):
    """Disjoint Set Union"""
    @classmethod
    def union(cls, p: set, q: set, o: set):
        """make p and q the same set"""
        return p | q | o

    @classmethod
    def is_connected(cls, p: set, q: set):
        """
        check whether set p and set q are connected
        """
        if p & q:
            return True
        else:
            False
