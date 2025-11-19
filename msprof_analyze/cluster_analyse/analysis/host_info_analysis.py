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

from msprof_analyze.cluster_analyse.analysis.base_analysis import BaseAnalysis
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.cluster_analyse.common_func.utils import increase_shared_value
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.cluster_analyse.cluster_data_preprocess.msprof_data_preprocessor import MsprofDataPreprocessor
from msprof_analyze.cluster_analyse.cluster_data_preprocess.mindspore_data_preprocessor import MindsporeDataPreprocessor

logger = get_logger()


class HostInfoAnalysis(BaseAnalysis):
    TABLE_HOST_INFO = "HOST_INFO"
    TABLE_RANK_DEVICE_MAP = "RANK_DEVICE_MAP"

    def __init__(self, param: dict):
        super().__init__(param)
        self.all_rank_host_info = {}
        self.all_rank_device_info = []
        self.is_msprof = param.get(Constant.IS_MSPROF)
        self.is_mindspore = param.get(Constant.IS_MINDSPORE)

    def run(self, completed_processes=None, lock=None):
        if self.data_type != Constant.DB:
            if completed_processes and lock:
                increase_shared_value(completed_processes, lock)
            logger.info("HostInfoAnalysis completed")
            return
        self.analyze_host_info()
        self.dump_db()
        if completed_processes and lock:
            increase_shared_value(completed_processes, lock)
        logger.info("HostInfoAnalysis completed")

    def dump_db(self):
        output_path = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        PathManager.make_dir_safety(output_path)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        conn, curs = DBManager.create_connect_db(result_db)
        if not (conn and curs):
            logger.error("Failed to create db %s", str(Constant.DB_CLUSTER_COMMUNICATION_ANALYZER))
            return
        self.dump_host_info(result_db, conn)
        self.dump_rank_device_map(result_db, conn)
        DBManager.destroy_db_connect(conn, curs)

    def dump_host_info(self, result_db, db_conn):
        if not self.all_rank_host_info:
            logger.warning("No host info data be analyzed.")
            return
        DBManager.create_tables(result_db, Constant.TABLE_HOST_INFO)
        save_host_info = list(self.all_rank_host_info.items())
        sql = "insert into {} values ({value})".format(Constant.TABLE_HOST_INFO,
                                                       value="?," * (len(save_host_info[0]) - 1) + "?")
        DBManager.executemany_sql(db_conn, sql, save_host_info)

    def dump_rank_device_map(self, result_db, db_conn):
        if not self.all_rank_device_info:
            logger.warning("No rank device map data be analyzed.")
            return
        self.all_rank_device_info.sort()
        DBManager.create_tables(result_db, Constant.TABLE_RANK_DEVICE_MAP)
        sql = "insert into {} values ({value})".format(Constant.TABLE_RANK_DEVICE_MAP,
                                                       value="?," * (len(self.all_rank_device_info[0]) - 1) + "?")
        DBManager.executemany_sql(db_conn, sql, self.all_rank_device_info)

    def analyze_host_info(self):
        print_empty_host_info = ""
        for rank_id, profiling_dir in self.data_map.items():
            host_info = []
            rank_device_info = []
            db_path = self._get_db_path(rank_id, profiling_dir)
            if (os.path.exists(db_path) and DBManager.check_tables_in_db(db_path, self.TABLE_HOST_INFO)):
                conn, curs = DBManager.create_connect_db(db_path)
                sql = "select * from {0}".format(self.TABLE_HOST_INFO)
                host_info = DBManager.fetch_all_data(curs, sql, is_dict=False)
                DBManager.destroy_db_connect(conn, curs)
            if not (host_info and host_info[0]):
                if not print_empty_host_info:
                    print_empty_host_info = f"No {self.TABLE_HOST_INFO} data in {self.data_type} file."
                continue
            if (os.path.exists(db_path) and DBManager.check_tables_in_db(db_path, self.TABLE_RANK_DEVICE_MAP)):
                conn, curs = DBManager.create_connect_db(db_path)
                sql = "select * from {0}".format(self.TABLE_RANK_DEVICE_MAP)
                rank_device_info = DBManager.fetch_all_data(curs, sql, is_dict=False)
                DBManager.destroy_db_connect(conn, curs)
            if self.is_msprof:
                device_id = MsprofDataPreprocessor.get_device_id(profiling_dir)
                rank_device_info = [[rank_id, device_id]]
            if self.is_mindspore:
                prof_dir = MindsporeDataPreprocessor.get_msprof_dir(profiling_dir)
                device_id = MsprofDataPreprocessor.get_device_id(prof_dir)
                rank_device_info = [[rank_id, device_id]]
            if not (rank_device_info and rank_device_info[0]):
                if not print_empty_host_info:
                    print_empty_host_info = f"No {self.TABLE_RANK_DEVICE_MAP} data in {self.data_type} file."
                continue
            host_uid, host_name = str(host_info[0][0]), str(host_info[0][1])
            for idx, data in enumerate(rank_device_info):
                rank_device_info[idx] = list(data) + [host_uid, profiling_dir]
            self.all_rank_host_info[host_uid] = host_name
            self.all_rank_device_info.extend(rank_device_info)
        if print_empty_host_info:
            logger.warning(print_empty_host_info)

    def _get_db_path(self, rank_id, profiling_dir):
        if self.is_msprof:
            return MsprofDataPreprocessor.get_msprof_profiler_db_path(profiling_dir)
        if self.is_mindspore:
            return os.path.join(profiling_dir, Constant.SINGLE_OUTPUT, f"ascend_mindspore_profiler_{rank_id}.db")
        return os.path.join(profiling_dir, Constant.SINGLE_OUTPUT, f"ascend_pytorch_profiler_{rank_id}.db")
