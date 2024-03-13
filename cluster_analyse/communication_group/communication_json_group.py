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
from communication_group.base_communication_group import BaseCommunicationGroup


class CommunicationJsonGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_JSON = "communication_group.json"

    def __init__(self, params: dict):
        super().__init__(params)
        self.communication_ops = []
        self.matrix_ops = []

    def dump_data(self):
        FileManager.create_json_file(self.collection_path, self.communication_group, self.COMMUNICATION_GROUP_JSON)
        comm_data_dict = {
           Constant.COLLECTIVE_GROUP: self.collective_group_dict,
           Constant.COMMUNICATION_OPS: self.communication_ops,
           Constant.MATRIX_OPS: self.matrix_ops,
           Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

    def analyze_communication_data(self):
        for rank_id, rank_id_comm_dict, rank_id_matrix_dict in self.rank_comm_dir_dict:
            for step_id, step_id_dict in rank_id_comm_dict.items():
                if not isinstance(step_id_dict, dict):
                    print(f"[WARNING] rank{rank_id}'s communication.json has a wrong data struct.")
                    continue
                self.get_collective_ops_name(rank_id, step_id_dict.get(Constant.COLLECTIVE))
                for comm_op_type, comm_op_dict in step_id_dict.items():
                    self.add_communication_ops(rank_id, step_id, comm_op_type, comm_op_dict)

            for step_id, step_id_dict in rank_id_matrix_dict.items():
                if not isinstance(step_id_dict, dict):
                    print(f"[WARNING] rank{rank_id}'s communication_matrix.json has a wrong data struct.")
                    continue
                self.set_p2p_link(rank_id, step_id, rank_id_matrix_dict)
                self.get_collective_ops_name(rank_id, step_id_dict.get(Constant.COLLECTIVE))

    def read_communication_func(self: any, params: tuple):
        if len(params) < 3:
            return -1, {}, {}
        rank_id = params[0]
        comm_json_path = params[1]
        matrix_json_path = params[2]
        comm_data = {}
        matrix_data = {}
        if os.path.exists(comm_json_path) and self.analysis_mode in ["all", "communication_time"]:
            comm_data = FileManager.read_json_file(comm_json_path)
        if os.path.exists(matrix_json_path) and self.analysis_mode in ["all", "communication_matrix"]:
            matrix_data = FileManager.read_json_file(matrix_json_path)
        return rank_id, comm_data, matrix_data

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
