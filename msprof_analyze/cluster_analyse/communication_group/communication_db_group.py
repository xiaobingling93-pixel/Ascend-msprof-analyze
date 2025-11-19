#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C)  2024-2024. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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

from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.cluster_analyse.communication_group.base_communication_group import BaseCommunicationGroup
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


def get_communication_data(rank_id: str, db_path: str, analysis_mode: str):
    time_data = []
    bandwidth_data = []
    matrix_data = []
    if not os.path.exists(db_path):
        logger.warning("rank %s db path %s does not exist.", rank_id, db_path)
        return [], [], []
    conn, cursor = DBManager.create_connect_db(db_path)
    time_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_TIME)
    bandwidth_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_BANDWIDTH)
    matrix_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_MATRIX)
    if (DBManager.check_tables_in_db(db_path, Constant.TABLE_COMM_ANALYZER_TIME,
                                     Constant.TABLE_COMM_ANALYZER_BANDWIDTH)
            and analysis_mode in [Constant.ALL, Constant.COMMUNICATION_TIME]):
        time_data = DBManager.fetch_all_data(cursor, time_info_sql)
        bandwidth_data = DBManager.fetch_all_data(cursor, bandwidth_info_sql)
    if (DBManager.check_tables_in_db(db_path, Constant.TABLE_COMM_ANALYZER_MATRIX)
            and analysis_mode in [Constant.ALL, Constant.COMMUNICATION_MATRIX]):
        matrix_data = DBManager.fetch_all_data(cursor, matrix_info_sql)
    DBManager.destroy_db_connect(conn, cursor)
    return time_data, bandwidth_data, matrix_data


def dump_group_db(dump_data: list, group_table: str, cluster_analysis_output_path: str):
    if dump_data:
        output_path = os.path.join(cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, group_table)
        conn, cursor = DBManager.create_connect_db(result_db)
        sql = "insert into {} values ({value})".format(group_table,
                                                       value="?," * (len(dump_data[0]) - 1) + "?")
        DBManager.executemany_sql(conn, sql, dump_data)
        DBManager.destroy_db_connect(conn, cursor)
    else:
        logger.warning("[WARNING] The CommunicationGroup table won't be created because no data has been calculated.")


class CommunicationDBGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_TABLE = "CommunicationGroup"

    def __init__(self, params: dict):
        super().__init__(params)

    def read_communication_func(self, params: tuple):
        if len(params) < 3:
            return -1, {}, {}
        rank_id = params[0]
        db_path = params[1]
        time_data, bandwidth_data, matrix_data = get_communication_data(rank_id, db_path, self.analysis_mode)
        comm_data = self.adapter.transfer_comm_from_db_to_json(time_data, bandwidth_data)
        comm_matrix_data = self.adapter.transfer_matrix_from_db_to_json(matrix_data)
        return rank_id, comm_data, comm_matrix_data

    def dump_data(self):
        self.comm_group_parallel_info_df["rank_set"] = (self.comm_group_parallel_info_df["rank_set"].
                                                        apply(lambda x: "(" + ",".join(str(i) for i in x) + ")"))
        res = self.comm_group_parallel_info_df.values.tolist()
        dump_group_db(res, self.COMMUNICATION_GROUP_TABLE, self.cluster_analysis_output_path)


class CommunicationDBGroupOptimized(BaseCommunicationGroup):
    COMMUNICATION_GROUP_MAPPING_TABLE = "CommunicationGroupMapping"

    def __init__(self, params: dict):
        super().__init__(params)
        self.bandwidth_data = []
        self.matrix_ops = []

    def read_communication_func(self, params: tuple):
        if len(params) < 3:
            return -1, {}, {}
        rank_id = params[0]
        db_path = params[1]
        time_data, bandwidth_data, matrix_data = get_communication_data(rank_id, db_path, self.analysis_mode)
        comm_matrix_data = self.adapter.transfer_matrix_from_db_to_json(matrix_data)
        comm_time_data = (time_data, bandwidth_data)
        return rank_id, comm_time_data, comm_matrix_data

    def set_group_rank_map(self, rank_id: int, time_data: list):
        for single_time_data in time_data:
            group_type = single_time_data.get(Constant.TYPE)
            group_name = single_time_data.get(Constant.GROUP_NAME)
            if not group_name:
                return
            if group_type == Constant.COLLECTIVE:
                self.collective_group_dict[group_name].add(rank_id)
            elif group_type == Constant.P2P:
                self.p2p_group_dict[group_name].add(rank_id)

    def analyze_communication_data(self):
        for rank_id, comm_time_data, comm_matrix_data in self.rank_comm_dir_dict:
            time_data, bandwidth_data = comm_time_data
            if self.analysis_mode in [Constant.ALL, Constant.COMMUNICATION_TIME]:
                if not time_data:
                    logger.warning("[WARNING] rank %s has error format in time data.", rank_id)
                    continue
                self.set_group_rank_map(rank_id, time_data)
                self.communication_ops.extend(self._merge_data_with_rank(rank_id, time_data))
                self.bandwidth_data.extend(self._merge_data_with_rank(rank_id, bandwidth_data))
            if self.analysis_mode in [Constant.ALL, Constant.COMMUNICATION_MATRIX]:
                if not comm_matrix_data:
                    logger.warning("[WARNING] rank %s matrix data is null.", rank_id)
                    continue
                for step_id, step_id_dict in comm_matrix_data.items():
                    if not isinstance(step_id_dict, dict):
                        logger.warning("[WARNING] rank %s has error format in matrix data.", rank_id)
                        continue
                    self.add_matrix_ops(rank_id, step_id, step_id_dict)
                    self.set_group_rank_map(rank_id, time_data)

    def generate_collective_communication_group(self):
        collective_group = []
        for group_name, group in self.collective_group_dict.items():
            collective_group.append((group_name, list(group)))
        self.communication_group[Constant.COLLECTIVE] = collective_group

    def collect_comm_data(self):
        comm_data_dict = {
            Constant.COLLECTIVE_GROUP: self.collective_group_dict,
            Constant.COMMUNICATION_OPS: (self.communication_ops, self.bandwidth_data),
            Constant.MATRIX_OPS: self.matrix_ops,
            Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

    def dump_data(self):
        self.comm_group_parallel_info_df["rank_set"] = (self.comm_group_parallel_info_df["rank_set"].
                                                        apply(lambda x: "(" + ",".join(str(i) for i in x) + ")"))
        res = self.comm_group_parallel_info_df.values.tolist()
        dump_group_db(res, self.COMMUNICATION_GROUP_MAPPING_TABLE, self.cluster_analysis_output_path)

    def _merge_data_with_rank(self, rank_id: int, data_list: list):
        res = []
        for single_time_data in data_list:
            single_time_data[Constant.RANK_ID] = rank_id
            res.append(single_time_data)
        return res
