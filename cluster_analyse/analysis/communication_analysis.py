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

from common_func.constant import Constant
from collections import defaultdict
from common_func.file_manager import FileManager


class CommunicationAnalysis:
    CLUSTER_COMMUNICATION_JSON = "cluster_communication.json"

    def __init__(self, param: dict):
        self.collection_path = param.get(Constant.COLLECTION_PATH)
        self.data_map = param.get(Constant.DATA_MAP)
        self.collective_group_dict = param.get(Constant.COLLECTIVE_GROUP)
        self.communication_ops = param.get(Constant.COMMUNICATION_OPS)
        self.comm_ops_struct = {}

    @staticmethod
    def combine_size_distribution(op_dict: dict, total_dict: dict):
        for size, size_info in op_dict.items():
            total_dict[size][0] += size_info[0]
            total_dict[size][1] += size_info[1]

    def run(self):
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()

    def dump_data(self):
        if not self.comm_ops_struct:
            print("There is no final comm ops data generated")
            return
        output_comm_data = {}
        for key in self.comm_ops_struct:
            output_comm_data[str(key)] = self.comm_ops_struct.get(key)
        FileManager.create_json_file(self.collection_path, output_comm_data, self.CLUSTER_COMMUNICATION_JSON)

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

    def compute_total_info(self, comm_ops: dict):
        if not comm_ops:
            return
        total_rank_dict = {}
        for communication_op, rank_dict in comm_ops.items():
            for rank_id, communication_op_info in rank_dict.items():
                total_rank_dict.setdefault(rank_id, {}).setdefault(Constant.COMMUNICATION_TIME_INFO, defaultdict(float))
                total_rank_dict.setdefault(rank_id, {}).setdefault(Constant.COMMUNICATION_BANDWIDTH_INFO, {})
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
        if total_time_info_dict[Constant.WAIT_TIME_MS] + total_time_info_dict[Constant.TRANSIT_TIME_MS] == 0:
            total_time_info_dict[Constant.WAIT_TIME_RATIO] = 0
        else:
            total_time_info_dict[Constant.WAIT_TIME_RATIO] = \
                round(total_time_info_dict[Constant.WAIT_TIME_MS] /
                      (total_time_info_dict[Constant.WAIT_TIME_MS] + total_time_info_dict[Constant.TRANSIT_TIME_MS]), 4)
        if total_time_info_dict[Constant.SYNCHRONIZATION_TIME_MS] + total_time_info_dict[Constant.TRANSIT_TIME_MS] == 0:
            total_time_info_dict[Constant.SYNCHRONIZATION_TIME_RATIO] = 0
        else:
            total_time_info_dict[Constant.SYNCHRONIZATION_TIME_RATIO] = \
                round(total_time_info_dict[Constant.SYNCHRONIZATION_TIME_MS] /
                      (total_time_info_dict[Constant.SYNCHRONIZATION_TIME_MS] +
                       total_time_info_dict[Constant.TRANSIT_TIME_MS]), 4)

    def compute_bandwidth_ratio(self, total_bandwidth_info_dict: dict):
        for transport_type, bandwidth_dict in total_bandwidth_info_dict.items():
            if bandwidth_dict[Constant.TRANSIT_TIME_MS] == 0:
                bandwidth_dict[Constant.BANDWIDTH_GB_S] = 0
            else:
                bandwidth_dict[Constant.BANDWIDTH_GB_S] = \
                    round(bandwidth_dict[Constant.TRANSIT_SIZE_MB] / bandwidth_dict[Constant.TRANSIT_TIME_MS], 4)
