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
from abc import abstractmethod
from collections import defaultdict
from copy import deepcopy
from multiprocessing import Pool

from common_func.constant import Constant


class BaseCommunicationGroup:
    def __init__(self, params: dict):
        self.collection_path = params.get(Constant.COLLECTION_PATH)
        self.data_map = params.get(Constant.DATA_MAP)
        self.data_type = params.get(Constant.DATA_TYPE)
        self.analysis_mode = params.get(Constant.ANALYSIS_MODE)
        self.rank_comm_dir_dict = {}
        self.p2p_link = []
        self.collective_group_dict = defaultdict(set)
        self.p2p_comm_group = []
        self.communication_group = {}

    def load_communication_data(self):
        comm_op_dirs = []
        for rank_id, profiling_dir_path in self.data_map.items():
            if self.data_type == Constant.TEXT:
                comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_JSON)
                matrix_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_MATRIX_JSON)
            else:
                comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.DB_COMMUNICATION_ANALYZER)
                matrix_dir = comm_dir
            if comm_dir and matrix_dir:
                comm_op_dirs.append((rank_id, comm_dir, matrix_dir))
            else:
                print(
                    f"[WARNING] Rank {rank_id} does not have a valid communication.json or communication_matrix.json.")
        with Pool() as p:
            self.rank_comm_dir_dict = p.map(self.read_communication_func, comm_op_dirs)

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

    def generate_collective_communication_group(self):
        self.communication_group[Constant.COLLECTIVE] = \
            [list(group) for group_name, group in self.collective_group_dict.items()]

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

    def whether_valid_comm_group(self, rank_set: set):
        """
        while distinguish which communication group should be used to infer stage info, these group should be ignored:
            1. group can not include more than 1 rank in every single p2p group
        """
        for p2p_rank_set in self.p2p_comm_group:
            if len(rank_set.intersection(p2p_rank_set)) > 1:
                return False
        return True

    @abstractmethod
    def read_communication_func(self, params: tuple):
        pass

    @abstractmethod
    def analyze_communication_data(self):
        pass

    @abstractmethod
    def dump_data(self):
        pass

    def generate(self):
        self.load_communication_data()
        self.analyze_communication_data()
        self.set_p2p_groups()
        self.generate_collective_communication_group()
        self.generate_p2p_communication_group()
        return self.dump_data()


class UnionFind(object):
    """Disjoint Set Union"""

    @classmethod
    def union(cls, first_set: set, second_set: set, third_set: set):
        """make p and q the same set"""
        return first_set | second_set | third_set

    @classmethod
    def is_connected(cls, first_set: set, second_set: set):
        """
        check whether set p and set q are connected
        """
        if first_set & second_set:
            return True
        else:
            return False
