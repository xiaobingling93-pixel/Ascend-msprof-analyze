# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
import logging
from collections import defaultdict

from analysis.base_analysis import BaseAnalysis
from common_func.constant import Constant
from common_func.table_constant import TableConstant
from common_func.db_manager import DBManager
from prof_bean.communication_bandwidth_bean import CommunicationBandwidthBean
from prof_bean.communication_time_bean import CommunicationTimeBean


logger = logging.getLogger()


class CommunicationAnalysis(BaseAnalysis):
    SAVED_JSON = "cluster_communication.json"
    COMMUNICATION_BANDWIDTH_TABLE = "ClusterCommAnalyzerBandwidth"
    COMMUNICATION_TIME_TABLE = "ClusterCommAnalyzerTime"

    def __init__(self, param: dict):
        super().__init__(param)
        self.communication_ops = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_OPS)

    @staticmethod
    def combine_size_distribution(op_dict: dict, total_dict: dict):
        for size, size_info in op_dict.items():
            total_dict[size][0] += size_info[0]
            total_dict[size][1] += size_info[1]

    @staticmethod
    def execute(conn, res_data, table_name):
        if res_data:
            res_value = [list(data.values()) for data in res_data]
            sql = "insert into {} values ({value})".format(table_name, value="?," * (len(res_value[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_value)

    def run(self):
        if not self.communication_ops:
            return
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()

    def dump_db(self):
        res_comm_time, res_comm_bandwidth = self.adapter.transfer_comm_from_json_to_db(self.comm_ops_struct)
        output_path = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, self.COMMUNICATION_TIME_TABLE, self.COMMUNICATION_BANDWIDTH_TABLE)
        conn, cursor = DBManager.create_connect_db(result_db)
        self.execute(conn, res_comm_time, self.COMMUNICATION_TIME_TABLE)
        self.execute(conn, res_comm_bandwidth, self.COMMUNICATION_BANDWIDTH_TABLE)
        DBManager.destroy_db_connect(conn, cursor)

    def compute_total_info(self, comm_ops: dict):
        if not comm_ops:
            return
        default_value = {
            Constant.COMMUNICATION_TIME_INFO: defaultdict(float),
            Constant.COMMUNICATION_BANDWIDTH_INFO: {}
        }
        total_rank_dict = defaultdict(lambda: {default_value.copy()})
        for _, rank_dict in comm_ops.items():
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
        for _, bandwidth_dict in total_bandwidth_info_dict.items():
            bandwidth_dict[Constant.BANDWIDTH_GB_S] = \
                self.compute_ratio(bandwidth_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                   bandwidth_dict.get(Constant.TRANSIT_TIME_MS, 0))


class CommunicationAnalysisOptimized(BaseAnalysis):
    COMMUNICATION_BANDWIDTH_TABLE = "ClusterCommunicationBandwidth"
    COMMUNICATION_TIME_TABLE = "ClusterCommunicationTime"
    
    def __init__(self, param: dict):
        super().__init__(param)
        self._communication_ops = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_OPS)
        self._communication_group = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_GROUP)
        self._aggregate_time = {}
        self._aggregate_bandwidth = {}
        self._output_time = []
        self._output_bandwidth = []
        
    @staticmethod
    def _execute(conn, res_data, table_name):
        if res_data:
            sql = "insert into {} values ({value})".format(table_name, value="?," * (len(res_data[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_data)
            
    @staticmethod
    def _format_time_data(communication_data):
        data_dict = {}
        for single_op in communication_data:
            formatted_data = CommunicationTimeBean(single_op)
            data_dict.setdefault(formatted_data.step_id, {}).\
                setdefault(formatted_data.rank_id, {}).\
                setdefault(formatted_data.group_name, []).extend([formatted_data])
        return data_dict
    
    def run(self):
        if not self._communication_ops[0] or not self._communication_ops[1]:
            return
        self._aggregate_time = self._format_time_data(self._communication_ops[0])
        self._aggregate_bandwidth = self._format_bandwidth_data(self._communication_ops[1])
        self._compute_total_info()
        self._dump_data()

    def _format_bandwidth_data(self, communication_data: dict):
        data_dict = {}
        for single_op in communication_data:
            formatted_data = CommunicationBandwidthBean(single_op)
            data_dict.setdefault(formatted_data.step_id, {}).\
                setdefault(formatted_data.rank_id, {}).\
                setdefault(formatted_data.transport_type, {}).\
                setdefault(formatted_data.package_size, []).extend([formatted_data])
        return data_dict

    def _dump_data(self):
        output_path = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, self.COMMUNICATION_TIME_TABLE)
        DBManager.create_tables(result_db, self.COMMUNICATION_BANDWIDTH_TABLE)
        conn, cursor = DBManager.create_connect_db(result_db)
        self._execute(conn, self._output_time, self.COMMUNICATION_TIME_TABLE)
        self._execute(conn, self._output_bandwidth, self.COMMUNICATION_BANDWIDTH_TABLE)
        DBManager.destroy_db_connect(conn, cursor)

    def _compute_total_info(self):
        if not self._aggregate_time or not self._aggregate_bandwidth:
            logger.error("[ERROR] communication data is null.")
            return
        for step_id, rank_dict in self._aggregate_time.items():
            for rank_id, communication_op_info in rank_dict.items():
                rank_set_dict = {}
                for group_name, single_group_op_info in communication_op_info.items():
                    total_dict = {
                        TableConstant.RANK_ID: rank_id,
                        TableConstant.STEP: step_id,
                        TableConstant.GROUP_NAME: group_name,
                        TableConstant.HCCL_OP_NAME: Constant.TOTAL_OP_INFO
                    }
                    total_time_info = CommunicationTimeBean(total_dict)
                    for com_info_dict in single_group_op_info:
                        total_time_info += com_info_dict
                        self._output_time.append(com_info_dict.convert_output())
                    rank_set = str(self.collective_group_dict.get(group_name))
                    if not rank_set:
                        logger.warning("failed to find rank set with group name: %s.", str(group_name))
                        continue
                    if rank_set_dict.get(rank_set):
                        rank_set_dict[rank_set] += total_time_info
                    else:
                        rank_set_dict[rank_set] = total_time_info
                for _, total_time_info in rank_set_dict.items():
                    total_time_info.compute_ratio()
                    self._output_time.append(total_time_info.convert_output())
        for step_id, rank_dict in self._aggregate_bandwidth.items():
            for rank_id, communication_op_info in rank_dict.items():
                for transport_type, bandwidth_info in communication_op_info.items():
                    total_transit_size = 0.0
                    total_transit_time = 0.0
                    total_info = []
                    op_group_set = set()
                    for package_size, package_info in bandwidth_info.items():
                        total_dict = {
                            TableConstant.RANK_ID: rank_id,
                            TableConstant.STEP: step_id,
                            TableConstant.GROUP_NAME: '',
                            TableConstant.HCCL_OP_NAME: Constant.TOTAL_OP_INFO,
                            TableConstant.TRANSPORT_TYPE: transport_type,
                            TableConstant.TRANSIT_SIZE: 0.0,
                            TableConstant.TRANSIT_TIME: 0.0,
                            TableConstant.BANDWIDTH: 0.0,
                            TableConstant.PACKAGE_SIZE: package_size
                        }
                        total_bandwidth_info = CommunicationBandwidthBean(total_dict)
                        for bandwidth_package_info in package_info:
                            total_bandwidth_info += bandwidth_package_info
                            self._output_bandwidth.append(bandwidth_package_info.convert_output())
                            op_group = bandwidth_package_info.hccl_op_name + "@" + bandwidth_package_info.group_name
                            if op_group not in op_group_set:
                                op_group_set.add(op_group)
                                total_transit_size += bandwidth_package_info.transit_size
                                total_transit_time += bandwidth_package_info.transit_time
                        total_info.append(total_bandwidth_info)
                    total_bandwidth = total_transit_size / total_transit_time if total_transit_time else 0.0
                    for single_total_info in total_info:
                        single_total_info.set_transit_size(total_transit_size)
                        single_total_info.set_transit_time(total_transit_time)
                        single_total_info.set_bandwidth(total_bandwidth)
                        self._output_bandwidth.append(single_total_info.convert_output())
