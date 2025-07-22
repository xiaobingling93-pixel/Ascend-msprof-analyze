# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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
import json
import os

from msprof_analyze.cluster_analyse.analysis.base_analysis import BaseAnalysis
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.cluster_analyse.common_func.utils import increase_shared_value
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.file_manager import FileManager


logger = get_logger()


class ClusterBaseInfoAnalysis(BaseAnalysis):

    def __init__(self, param: dict):
        super().__init__(param)
        self.distributed_args = {}

    def run(self, completed_processes=None, lock=None):
        if self.data_type != Constant.DB:
            if completed_processes and lock:
                increase_shared_value(completed_processes, lock)
            logger.info("ClusterBaseInfoAnalysis skipped, since data type is not db")
            return
        if not self.extract_base_info():
            logger.warning("ClusterBaseInfoAnalysis skipped, since no metadata or distributed args found")
            return
        self.dump_db()
        if completed_processes and lock:
            increase_shared_value(completed_processes, lock)
        logger.info("ClusterBaseInfoAnalysis completed")

    def dump_db(self):
        if not self.distributed_args:
            return
        output_path = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        PathManager.make_dir_safety(output_path)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        conn, curs = DBManager.create_connect_db(result_db)
        DBManager.create_tables(result_db, Constant.TABLE_CLUSTER_BASE_INFO)
        save_distributed_args = [[Constant.DISTRIBUTED_ARGS, json.dumps(self.distributed_args)]]
        sql = "insert into {} values ({value})".format(Constant.TABLE_CLUSTER_BASE_INFO,
                                                       value="?," * (len(save_distributed_args[0]) - 1) + "?")
        DBManager.executemany_sql(conn, sql, save_distributed_args)
        DBManager.destroy_db_connect(conn, curs)

    def extract_base_info(self):
        file_list = self.get_profiler_metadata_file()
        if not file_list:
            return False
        for file_path in file_list:
            try:
                meta_data = FileManager.read_json_file(file_path)
            except RuntimeError as e:
                logger.error("Read json failed. %s", str(e))
                continue
            if not meta_data.get(Constant.DISTRIBUTED_ARGS):
                continue
            for key, value in meta_data[Constant.DISTRIBUTED_ARGS].items():
                if key == "rank":
                    continue
                self.distributed_args.setdefault(key, value)
            return True
        return False

    def get_profiler_metadata_file(self):
        meta_file_list = []
        for root, _, files in PathManager.limited_depth_walk(self.collection_path):
            for file_name in files:
                if file_name == Constant.PROFILER_METADATA:
                    meta_file_list.append(os.path.join(root, file_name))
        return meta_file_list


