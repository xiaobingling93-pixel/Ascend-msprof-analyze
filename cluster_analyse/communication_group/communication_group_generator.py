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
from copy import deepcopy
from multiprocessing import Pool
from collections import defaultdict
from common_func.constant import Constant
from common_func.file_manager import FileManager


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
        self.p2p_comm_group = []
        self.p2p_link = []
        self.matrix_ops = []

    def generate(self):
        self.load_communication_json()
        self.analyze_communication_ops()
        self.set_p2p_groups()
        self.generate_collective_communication_group()
        self.generate_p2p_communication_group()
        FileManager.create_json_file(self.collection_path, self.communication_group, self.COMMUNICATION_GROUP_JSON)
        comm_data_dict = {
           Constant.COLLECTIVE_GROUP: self.collective_group_dict,
           Constant.COMMUNICATION_OPS: self.communication_ops,
           Constant.MATRIX_OPS: self.matrix_ops,
           Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

    def analyze_communication_ops(self):
        for rank_id, rank_id_comm_dict, rank_id_matrix_dict in self.rank_comm_dir_dict:
            for step_id, step_id_dict in rank_id_comm_dict.items():
                if not isinstance(step_id_dict, dict):
                    print(f"[WARNING] rank{rank_id}'s communication.json has a wrong data struct.")
                    continue
                self.set_p2p_link(rank_id, step_id, rank_id_matrix_dict)
                self.get_collective_ops_name(rank_id, step_id_dict.get(Constant.COLLECTIVE))
                for comm_op_type, comm_op_dict in step_id_dict.items():
                    self.add_communication_ops(rank_id, step_id, comm_op_type, comm_op_dict)

    @staticmethod
    def read_comm_json_func(params: tuple):
        if len(params) < 3:
            return -1, {}, {}
        rank_id = params[0]
        comm_json_path = params[1]
        matrix_json_path = params[2]
        comm_data = {}
        matrix_data = {}
        if os.path.exists(comm_json_path):
            comm_data = FileManager.read_json_file(comm_json_path)
        if os.path.exists(matrix_json_path):
            matrix_data = FileManager.read_json_file(matrix_json_path)
        return rank_id, comm_data, matrix_data

    def load_communication_json(self):
        comm_op_dirs = []
        for rank_id, profiling_dir_path in self.data_map.items():
            comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_JSON)
            matrix_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_MATRIX_JSON)
            if comm_dir and matrix_dir:
                comm_op_dirs.append((rank_id, comm_dir, matrix_dir))
            else:
                print(f"[WARNING] Rank {rank_id} does not have a valid communication.json or communication_matrix.json.")
        with Pool() as p:
            self.rank_comm_dir_dict = p.map(self.read_comm_json_func, comm_op_dirs)

    def generate_collective_communication_group(self):
        self.communication_group[Constant.COLLECTIVE] = \
            [list(group) for group_name, group in self.collective_group_dict.items()]

    def whether_valid_comm_group(self, rank_set: set):
        """
        while distinguish which communication group should be used to infer stage info, these group should be ignored:
            1. group can not include more than 1 rank in every single p2p group
        """
        for p2p_rank_set in self.p2p_comm_group:
            if len(rank_set.intersection(p2p_rank_set)) > 1:
                return False
        return True

    def generate_p2p_communication_group(self):
        stage_group = {}
        for group_name, rank_set in self.collective_group_dict.items():
            if not self.whether_valid_comm_group(rank_set):
                continue
            unioned_set = set()
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

    def set_p2p_groups(self):
        self.p2p_link = sorted(self.p2p_link, key=lambda x: min(x))
        while self.p2p_link:
            union_set = deepcopy(self.p2p_link[0])
            rm_list = [self.p2p_link[0]]
            for idx, link_rank_set_x in enumerate(self.p2p_link[1:]):
                if UnionFind.is_connected(link_rank_set_x, union_set):
                    union_set = union_set.union(link_rank_set_x)
                    rm_list.append(link_rank_set_x)
            self.p2p_comm_group.append(union_set)
            self.p2p_link = [element for element in self.p2p_link if element not in rm_list]

    def set_p2p_link(self, rank_id: int, step_id: str, rank_id_matrix_dict: dict):
        ops = rank_id_matrix_dict.get(step_id, {})
        self.add_matrix_ops(rank_id, step_id, ops)
        if not ops:
            print(f"[WARNING] rank{rank_id} {step_id} do not have communication matrix ops data.")
            return
        p2p_ops = ops.get(Constant.P2P, {})
        for op_name, link_dict in p2p_ops.items():
            self.append_p2p_link(op_name, link_dict)

    def append_p2p_link(self, op_name, link_dict):
        for link in link_dict:
            if '-' not in link:
                print(f"[WARNING] {op_name} has an invalid link key {link}!")
                break
            src_rank = int(link.split('-')[0])
            dst_rank = int(link.split('-')[1])
            if src_rank != dst_rank:
                rank_set = set([src_rank, dst_rank])
                if rank_set in self.p2p_link:
                    continue
                self.p2p_link.append(rank_set)

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

    def add_matrix_ops(self, rank_id: int, step_id: str, step_id_dict: dict):
        for comm_op_type, comm_dict in step_id_dict.items():
            if comm_op_type != Constant.COLLECTIVE and comm_op_type != Constant.P2P:
                print(f"[WARNING] Unknown communication operators type!")
                continue
            for op_name, op_link_info in comm_dict.items():
                if op_name.startswith('Total'):
                    continue
                group_name = op_name.split('@')[-1]
                self.matrix_ops.append({
                    Constant.RANK_ID: rank_id,
                    Constant.STEP_ID: step_id,
                    Constant.COMM_OP_TYPE: comm_op_type,
                    Constant.COMM_OP_NAME: op_name,
                    Constant.GROUP_NAME: group_name,
                    Constant.COMM_OP_INFO: op_link_info
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
            return False
