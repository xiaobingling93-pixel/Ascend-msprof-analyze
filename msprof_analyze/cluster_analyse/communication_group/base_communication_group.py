# Copyright (c) 2024, Huawei Technologies Co., Ltd
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

from msprof_analyze.cluster_analyse.cluster_utils.data_transfer_adapter import DataTransferAdapter
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class BaseCommunicationGroup:
    def __init__(self, params: dict):
        self.collection_path = params.get(Constant.COLLECTION_PATH)
        self.cluster_analysis_output_path = params.get(Constant.CLUSTER_ANALYSIS_OUTPUT_PATH)
        self.data_map = params.get(Constant.DATA_MAP)
        self.data_type = params.get(Constant.DATA_TYPE)
        self.analysis_mode = params.get(Constant.ANALYSIS_MODE)
        self.rank_comm_dir_dict = {}
        self.p2p_link = []
        self.collective_group_dict = defaultdict(set)
        self.p2p_comm_group = []
        self.communication_group = {}
        self.communication_ops = []
        self.matrix_ops = []
        self.adapter = DataTransferAdapter()

    def load_communication_data(self):
        comm_op_dirs = []
        for rank_id, profiling_dir_path in self.data_map.items():
            if self.data_type == Constant.TEXT:
                comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_JSON)
                matrix_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_MATRIX_JSON)
            else:
                comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.DB_COMMUNICATION_ANALYZER)
                matrix_dir = comm_dir
            if os.path.exists(comm_dir) or os.path.exists(matrix_dir):
                comm_op_dirs.append((rank_id, comm_dir, matrix_dir))
            else:
                logger.warning(
                    "Rank %s does not have valid communication data and communication_matrix data.", rank_id
                )
        max_processes = int(os.cpu_count() / 2)
        with Pool(processes=max_processes) as p:
            self.rank_comm_dir_dict = p.map(self.read_communication_func, comm_op_dirs)

    def set_p2p_groups(self):
        self.p2p_link = sorted(self.p2p_link, key=lambda x: min(x))
        while self.p2p_link:
            union_set = deepcopy(self.p2p_link[0])
            rm_list = [self.p2p_link[0]]
            for _, link_rank_set_x in enumerate(self.p2p_link[1:]):
                if UnionFind.is_connected(link_rank_set_x, union_set):
                    union_set = union_set.union(link_rank_set_x)
                    rm_list.append(link_rank_set_x)
            self.p2p_comm_group.append(union_set)
            self.p2p_link = [element for element in self.p2p_link if element not in rm_list]

    def generate_collective_communication_group(self):
        self.communication_group[Constant.COLLECTIVE] = \
            [list(group) for _, group in self.collective_group_dict.items()]

    def generate_p2p_communication_group(self):
        stage_group = {}
        for _, rank_set in self.collective_group_dict.items():
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

    def analyze_communication_data(self):
        for rank_id, rank_id_comm_dict, rank_id_matrix_dict in self.rank_comm_dir_dict:
            for step_id, step_id_dict in rank_id_comm_dict.items():
                if not isinstance(step_id_dict, dict):
                    logger.warning("rank%s's communication.json has a wrong data struct.", rank_id)
                    continue
                self.get_collective_ops_name(rank_id, step_id_dict.get(Constant.COLLECTIVE))
                for comm_op_type, comm_op_dict in step_id_dict.items():
                    self.add_communication_ops(rank_id, step_id, comm_op_type, comm_op_dict)

            for step_id, step_id_dict in rank_id_matrix_dict.items():
                if not isinstance(step_id_dict, dict):
                    logger.warning("rank%s's communication_matrix.json has a wrong data struct.", rank_id)
                    continue
                self.set_p2p_link(rank_id, step_id, rank_id_matrix_dict)
                self.get_collective_ops_name(rank_id, step_id_dict.get(Constant.COLLECTIVE))

    @abstractmethod
    def dump_data(self):
        pass

    def collect_comm_data(self):
        comm_data_dict = {
            Constant.COLLECTIVE_GROUP: self.collective_group_dict,
            Constant.COMMUNICATION_OPS: self.communication_ops,
            Constant.MATRIX_OPS: self.matrix_ops,
            Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

    def generate(self):
        self.load_communication_data()
        self.analyze_communication_data()
        self.set_p2p_groups()
        self.generate_collective_communication_group()
        self.generate_p2p_communication_group()
        self.dump_data()
        return self.collect_comm_data()

    def set_p2p_link(self, rank_id: int, step_id: str, rank_id_matrix_dict: dict):
        ops = rank_id_matrix_dict.get(step_id, {})
        self.add_matrix_ops(rank_id, step_id, ops)
        if not ops:
            logger.warning(
                "rank%s %s do not have communication matrix ops data.", rank_id, step_id
            )
            return
        p2p_ops = ops.get(Constant.P2P, {})
        for op_name, link_dict in p2p_ops.items():
            self.append_p2p_link(op_name, link_dict)

    def append_p2p_link(self, op_name, link_dict):
        for link in link_dict:
            if '-' not in link:
                logger.warning("%s has an invalid link key %s!", op_name, link)
                break
            src_rank = int(link.split('-')[0])
            dst_rank = int(link.split('-')[1])
            if src_rank != dst_rank:
                rank_set = {src_rank, dst_rank}
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
                logger.warning("Unknown communication operators type!")
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
