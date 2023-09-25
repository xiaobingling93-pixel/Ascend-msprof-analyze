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
from abc import abstractmethod

from common_func.constant import Constant
from collections import defaultdict
from common_func.file_manager import FileManager


class BaseCommAnalysis:

    def __init__(self, param: dict):
        self.collection_path = param.get(Constant.COLLECTION_PATH)
        self.data_map = param.get(Constant.DATA_MAP)
        self.collective_group_dict = param.get(Constant.COLLECTIVE_GROUP)
        self.comm_ops_struct = {}

    @staticmethod
    def compute_ratio(dividend: float, divisor: float):
        if abs(divisor) < 1e-15:
            return 0
        else:
            return round(dividend / divisor, 4)

    @abstractmethod
    def run(self):
        pass

    def dump_data(self):
        if not self.comm_ops_struct:
            print("There is no final comm ops data generated")
            return
        output_comm_data = {}
        for key in self.comm_ops_struct:
            output_comm_data[str(key)] = self.comm_ops_struct.get(key)
        FileManager.create_json_file(self.collection_path, output_comm_data, self.SAVED_JSON)

    def split_op_by_group(self):
        for single_op in self.communication_ops:
            if single_op.get(Constant.COMM_OP_TYPE) == Constant.P2P:
                rank_tup = Constant.P2P
            else:
                rank_tup = tuple(self.collective_group_dict.get(single_op.get(Constant.GROUP_NAME), []))
            rank_id = single_op.get(Constant.RANK_ID, 'N/A')
            step_id = single_op.get(Constant.STEP_ID, 'N/A')
            op_name = single_op.get(Constant.COMM_OP_NAME, 'N/A')
            op_info = single_op.get(Constant.COMM_OP_INFO)
            self.comm_ops_struct.setdefault(rank_tup, {}).setdefault(step_id, {}).\
                setdefault(op_name, {}).setdefault(rank_id, op_info)

    def combine_ops_total_info(self):
        for rank_tup, group_dict in self.comm_ops_struct.items():
            for step_id, communication_ops in group_dict.items():
                self.compute_total_info(communication_ops)


class CommunicationAnalysis(BaseCommAnalysis):
    SAVED_JSON = "cluster_communication.json"

    def __init__(self, param: dict):
        super().__init__(param)
        self.communication_ops = param.get(Constant.COMMUNICATION_OPS)

    @staticmethod
    def combine_size_distribution(op_dict: dict, total_dict: dict):
        for size, size_info in op_dict.items():
            total_dict[size][0] += size_info[0]
            total_dict[size][1] += size_info[1]

    def run(self):
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()

    def compute_total_info(self, comm_ops: dict):
        if not comm_ops:
            return
        total_rank_dict = defaultdict(lambda: {
                Constant.COMMUNICATION_TIME_INFO: defaultdict(float),
                Constant.COMMUNICATION_BANDWIDTH_INFO: {}
            })
        for communication_op, rank_dict in comm_ops.items():
            for rank_id, communication_op_info in rank_dict.items():
                for com_info, com_info_dict in communication_op_info.items():
                    if com_info == Constant.COMMUNICATION_TIME_INFO:
                        self.combine_time_info(com_info_dict, total_rank_dict[rank_id][com_info])
                    if com_info == Constant.COMMUNICATION_BANDWIDTH_INFO:
                        self.combine_bandwidth_info(com_info_dict, total_rank_dict[rank_id][com_info])
        for rank_id in total_rank_dict:
            self.compute_time_ratio(total_rank_dict[rank_id][Constant.COMMUNICATION_TIME_INFO])
            self.compute_bandwidth_ratio(total_rank_dict[rank_id][Constant.COMMUNICATION_BANDWIDTH_INFO])
        comm_ops[Constant.TOTAL_OP_INFO] = total_rank_dict

    def combine_time_info(self, com_info_dict: dict, total_time_info_dict: dict):
        ratio_list = [Constant.WAIT_TIME_RATIO, Constant.SYNCHRONIZATION_TIME_RATIO]
        for time_info in com_info_dict:
            if time_info not in ratio_list and time_info != Constant.START_TIMESTAMP:
                total_time_info_dict[time_info] += com_info_dict.get(time_info)

    def combine_bandwidth_info(self, com_info_dict: dict, total_bandwidth_info_dict: dict):
        add_list = [Constant.TRANSIT_TIME_MS, Constant.TRANSIT_SIZE_MB]
        dict_list = [Constant.SIZE_DISTRIBUTION]
        for transport_type, part_transport_dict in com_info_dict.items():
            if transport_type not in total_bandwidth_info_dict:
                total_bandwidth_info_dict[transport_type] = {
                    Constant.TRANSIT_TIME_MS: 0,
                    Constant.TRANSIT_SIZE_MB: 0,
                    Constant.SIZE_DISTRIBUTION: defaultdict(lambda: [0, 0])
                }
            for bandwidth_msg, value in part_transport_dict.items():
                if bandwidth_msg in add_list:
                    total_bandwidth_info_dict[transport_type][bandwidth_msg] += value
                if bandwidth_msg in dict_list:
                    self.combine_size_distribution(value, total_bandwidth_info_dict[transport_type][bandwidth_msg])

    def compute_time_ratio(self, total_time_info_dict: dict):
        total_time_info_dict[Constant.WAIT_TIME_RATIO] = \
            self.compute_ratio(total_time_info_dict.get(Constant.WAIT_TIME_MS, 0),
                               total_time_info_dict.get(Constant.WAIT_TIME_MS, 0) +
                               total_time_info_dict.get(Constant.TRANSIT_TIME_MS, 0))
        total_time_info_dict[Constant.SYNCHRONIZATION_TIME_RATIO] = \
            self.compute_ratio(total_time_info_dict.get(Constant.SYNCHRONIZATION_TIME_MS, 0),
                               total_time_info_dict.get(Constant.SYNCHRONIZATION_TIME_MS, 0) +
                               total_time_info_dict.get(Constant.TRANSIT_TIME_MS, 0))

    def compute_bandwidth_ratio(self, total_bandwidth_info_dict: dict):
        for transport_type, bandwidth_dict in total_bandwidth_info_dict.items():
            bandwidth_dict[Constant.BANDWIDTH_GB_S] = \
                self.compute_ratio(bandwidth_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                   bandwidth_dict.get(Constant.TRANSIT_TIME_MS, 0))


class CommMatrixAnalysis(BaseCommAnalysis):
    SAVED_JSON = "cluster_communication_matrix.json"

    def __init__(self, param: dict):
        super().__init__(param)
        self.communication_ops = []

    @staticmethod
    def combine_link(link_info_dict: dict, single_link_dict: dict):
        link_info_dict[Constant.TRANSPORT_TYPE] = single_link_dict.get(Constant.TRANSPORT_TYPE)
        link_info_dict[Constant.TRANSIT_TIME_MS] += single_link_dict.get(Constant.TRANSIT_TIME_MS, 0)
        link_info_dict[Constant.TRANSIT_SIZE_MB] += single_link_dict.get(Constant.TRANSIT_SIZE_MB, 0)

    def run(self):
        self.load_communication_matrix_data()
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()

    def load_communication_matrix_data(self):
        rank_comm_dict = {}
        for rank_id, profiling_dir_path in self.data_map.items():
            comm_dir = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.COMM_MATRIX_JSON)
            rank_comm_dict[rank_id] = FileManager.read_json_file(comm_dir)
            if not rank_comm_dict.get(rank_id):
                print(f"Rank {rank_id} does not have a valid communication_matrix.json.")
        self.construct_matrix_data(rank_comm_dict)

    def construct_matrix_data(self, rank_comm_dict: dict):
        for rank_id, rank_id_dict in rank_comm_dict.items():
            for step_id, step_id_dict in rank_id_dict.items():
                self.add_comm_ops(rank_id, step_id, step_id_dict)

    def add_comm_ops(self, rank_id: int, step_id: int, step_id_dict: dict):
        for comm_op_type, comm_dict in step_id_dict.items():
            if comm_op_type != Constant.COLLECTIVE and comm_op_type != Constant.P2P:
                print(f"Unknown communication opertors type!")
                continue
            for op_name, op_link_info in comm_dict.items():
                if op_name.startswith('Total'):
                    continue
                group_name = op_name.split('@')[-1]
                self.communication_ops.append({
                    Constant.RANK_ID: rank_id,
                    Constant.STEP_ID: step_id,
                    Constant.COMM_OP_TYPE: comm_op_type,
                    Constant.COMM_OP_NAME: op_name,
                    Constant.GROUP_NAME: group_name,
                    Constant.COMM_OP_INFO: op_link_info
                })

    def compute_total_info(self, step_dict: dict):
        self.merge_same_links(step_dict)
        self.combine_link_info(step_dict)

    def merge_same_links(self, step_dict: dict):
        def process_link_key():
            for link_key in rank_dict:
                if '-' not in link_key:
                    print(f"{op_name} has an invalid link key {link_key}!")
                    break
                src_rank = link_key.split('-')[0]
                dst_rank = link_key.split('-')[1]
                if src_rank == dst_rank:
                    if src_rank not in project_local_global_rank_map:
                        project_local_global_rank_map[src_rank] = rank_id
                    elif project_local_global_rank_map.get(src_rank) != rank_id:
                        print(f"In the same communication group, local ranks projecting to global ranks repeat!")
                self.combine_link(link_info[link_key], rank_dict[link_key])

        def convert_local_to_global_rank():
            tmp_link = {}
            for link_key, link_dict in link_info.items():
                src_rank = link_key.split('-')[0]
                dst_rank = link_key.split('-')[1]
                src_rank = project_local_global_rank_map[src_rank] \
                    if src_rank in project_local_global_rank_map else src_rank
                dst_rank = project_local_global_rank_map[dst_rank] \
                    if dst_rank in project_local_global_rank_map else dst_rank
                link_dict[Constant.BANDWIDTH_GB_S] = \
                    self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                       link_dict.get(Constant.TRANSIT_TIME_MS, 0))
                tmp_link[f"{src_rank}-{dst_rank}"] = link_dict
            return tmp_link

        project_local_global_rank_map = dict()
        for op_name, op_dict in step_dict.items():
            link_info = defaultdict(lambda: {
                Constant.TRANSPORT_TYPE: '',
                Constant.TRANSIT_TIME_MS: 0,
                Constant.TRANSIT_SIZE_MB: 0
            })
            for rank_id, rank_dict in op_dict.items():
                process_link_key()
            step_dict[op_name] = convert_local_to_global_rank()

    def combine_link_info(self, step_dict: dict):
        total_op_info = defaultdict(lambda: {
            Constant.TRANSPORT_TYPE: '',
            Constant.TRANSIT_TIME_MS: 0,
            Constant.TRANSIT_SIZE_MB: 0
        })
        for op_name, op_dict in step_dict.items():
            for link_key, link_dict in op_dict.items():
                self.combine_link(total_op_info[link_key], link_dict)
        for link_key, link_dict in total_op_info.items():
            link_dict[Constant.BANDWIDTH_GB_S] = \
                self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                   link_dict.get(Constant.TRANSIT_TIME_MS, 0))
        step_dict[Constant.TOTAL_OP_INFO] = total_op_info
