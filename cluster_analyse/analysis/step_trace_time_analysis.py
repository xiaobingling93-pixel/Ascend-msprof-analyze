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

from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.file_manager import FileManager
from prof_bean.step_trace_time_bean import StepTraceTimeBean


class StepTraceTimeAnalysis:
    CLUSTER_TRACE_TIME_CSV = "cluster_step_trace_time.csv"
    CLUSTER_TRACE_TIME_TABLE = "ClusterStepTraceTime"

    def __init__(self, param: dict):
        self.collection_path = param.get(Constant.COLLECTION_PATH)
        self.data_map = param.get(Constant.DATA_MAP)
        self.communication_group = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_GROUP)
        self.step_time_dict = {}
        self.step_data_list = []
        self.data_type = param.get(Constant.DATA_TYPE)

    @staticmethod
    def get_max_data_row(data_group_list: list):
        if not data_group_list:
            return []
        ret = []
        for idx in range(len(data_group_list[0])):
            max_val = 0
            for idy in range(len(data_group_list)):
                max_val = max(max_val, data_group_list[idy][idx])
            ret.append(max_val)
        return ret

    def run(self):
        self.load_step_trace_time_data()
        self.analyze_step_time()
        self.dump_data()

    def dump_data(self):
        if not self.step_data_list:
            print("[WARNING] Can't get step time info!")
        if self.data_type == Constant.TEXT:
            headers = self.get_headers()
            FileManager.create_csv_file(self.collection_path, self.step_data_list, self.CLUSTER_TRACE_TIME_CSV, headers)
        else:
            output_path = os.path.join(self.collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
            result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
            DBManager.create_tables(result_db, self.CLUSTER_TRACE_TIME_TABLE)
            conn, cursor = DBManager.create_connect_db(result_db)
            sql = "insert into {} values ({value})".format(self.CLUSTER_TRACE_TIME_TABLE,
                                                           value="?," * (len(self.step_data_list[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, self.step_data_list)
            DBManager.destroy_db_connect(conn, cursor)

    def load_step_trace_time_data(self):
        for rank_id, profiling_dir_path in self.data_map.items():
            if self.data_type == Constant.TEXT:
                step_time_file = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.STEP_TIME_CSV)
                if step_time_file:
                    self.step_time_dict[rank_id] = FileManager.read_csv_file(step_time_file, StepTraceTimeBean)
            else:
                step_time_file = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT,
                                              Constant.DB_COMMUNICATION_ANALYZER)
                if step_time_file and DBManager.check_tables_in_db(step_time_file, Constant.TABLE_STEP_TRACE):
                    conn, cursor = DBManager.create_connect_db(step_time_file)
                    sql = "select * from {0}".format(Constant.TABLE_STEP_TRACE)
                    data = DBManager.fetch_all_data(cursor, sql, is_dict=False)
                    self.step_time_dict[rank_id] = data
                    DBManager.destroy_db_connect(conn, cursor)
            if not self.step_time_dict.get(rank_id):
                print(f"[WARNING] Rank {rank_id} does not have a valid step_trace_time.json.")

    def analyze_step_time(self):
        for rank_id, data_bean_list in self.step_time_dict.items():
            for data_bean in data_bean_list:
                if self.data_type == Constant.TEXT:
                    self.step_data_list.append([data_bean.step, Constant.RANK, rank_id] + data_bean.row)
                else:
                    self.step_data_list.append([data_bean[0], Constant.RANK, rank_id] + list(data_bean[1:]))
        stage_list = self.communication_group.get(Constant.P2P)
        if not stage_list:
            return
        step_group_dict = {}
        for data_list in self.step_data_list:
            stage_group = tuple()
            for stage in stage_list:
                if data_list[2] in stage:
                    stage_group = tuple(stage)
                    break
            key = (data_list[0], stage_group)
            step_group_dict.setdefault(key, []).append(data_list[3:])

        for key, data_group_list in step_group_dict.items():
            if self.data_type == Constant.TEXT:
                self.step_data_list.append([key[0], Constant.STAGE, key[1]] + self.get_max_data_row(data_group_list))
            else:
                index = "(" + ",".join(str(i) for i in key[1]) + ")"
                self.step_data_list.append([key[0], Constant.STAGE, index] + self.get_max_data_row(data_group_list))

    def get_headers(self):
        if self.step_time_dict:
            for rank in self.step_time_dict:
                if self.step_time_dict.get(rank):
                    return self.step_time_dict[rank][0].all_headers
        return []
