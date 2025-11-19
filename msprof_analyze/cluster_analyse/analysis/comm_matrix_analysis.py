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

import copy
import os
from collections import defaultdict

from msprof_analyze.cluster_analyse.analysis.base_analysis import BaseAnalysis
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.cluster_analyse.common_func.utils import increase_shared_value
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.cluster_analyse.common_func.utils import double_hash
from msprof_analyze.prof_common.file_manager import FileManager

logger = get_logger()


class CommMatrixAnalysis(BaseAnalysis):
    SAVED_JSON = "cluster_communication_matrix.json"
    COMMUNICATION_MATRIX_TABLE = "ClusterCommAnalyzerMatrix"

    def __init__(self, param: dict):
        super().__init__(param)
        self.communication_ops = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.MATRIX_OPS)

    @staticmethod
    def combine_link(link_info_dict: dict, single_link_dict: dict):
        link_info_dict[Constant.TRANSPORT_TYPE] = single_link_dict.get(Constant.TRANSPORT_TYPE)
        link_info_dict[Constant.OP_NAME] = single_link_dict.get(Constant.OP_NAME, '')
        link_info_dict[Constant.TRANSIT_TIME_MS] += single_link_dict.get(Constant.TRANSIT_TIME_MS, 0)
        link_info_dict[Constant.TRANSIT_SIZE_MB] += single_link_dict.get(Constant.TRANSIT_SIZE_MB, 0)

    def run(self, completed_processes, lock):
        if not self.communication_ops:
            increase_shared_value(completed_processes, lock)
            logger.info("CommMatrixAnalysis completed")
            return
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()
        increase_shared_value(completed_processes, lock)
        logger.info("CommMatrixAnalysis completed")

    def dump_db(self):
        res_comm_matrix = self.adapter.transfer_matrix_from_json_to_db(self.comm_ops_struct)
        output_path = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, self.COMMUNICATION_MATRIX_TABLE)
        conn, cursor = DBManager.create_connect_db(result_db)
        if res_comm_matrix:
            res_matrix_value = [list(data.values()) for data in res_comm_matrix]
            sql = "insert into {} values ({value})".format(self.COMMUNICATION_MATRIX_TABLE,
                                                           value="?," * (len(res_matrix_value[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_matrix_value)
        DBManager.destroy_db_connect(conn, cursor)

    def compute_total_info(self, step_dict: dict):
        self.merge_same_links(step_dict)
        self.combine_link_info(step_dict)

    def merge_same_links(self, step_dict: dict):
        def update_rank_map(step_dict):
            for op_name, op_dict in step_dict.items():
                group_name = op_name.split("@")[-1]
                for rank_id, rank_dict in op_dict.items():
                    for link_key in rank_dict:
                        if '-' not in link_key:
                            logger.warning("%s has an invalid link key %s!", str(op_name), str(link_key))
                            break
                        src_rank = link_key.split('-')[0]
                        dst_rank = link_key.split('-')[1]
                        if src_rank == dst_rank:
                            if src_rank not in project_local_global_rank_map.get(group_name, {}):
                                project_local_global_rank_map.setdefault(group_name, {})[src_rank] = rank_id
                            elif project_local_global_rank_map.get(group_name, {}).get(src_rank) != rank_id:
                                logger.warning(f"In the same communication group {group_name}, global rank {rank_id} "
                                               f"and {project_local_global_rank_map.get(group_name, {}).get(src_rank)} "
                                               f"get the same local rank {src_rank}!")

        def process_link_key(rank_dict):
            for link_key in rank_dict:
                if '-' not in link_key:
                    logger.warning("%s has an invalid link key %s!", str(op_name), str(link_key))
                    break
                self.combine_link(link_info[link_key], rank_dict[link_key])

        def convert_local_to_global_rank(rank_map):
            tmp_link = {}
            for link_key, link_dict in link_info.items():
                src_rank = link_key.split('-')[0]
                dst_rank = link_key.split('-')[1]
                if src_rank not in rank_map:
                    logger.warning(f"The src local rank {src_rank} of the operator {op_name} "
                                   f"cannot be mapped to the global rank.")
                    continue
                if dst_rank not in rank_map:
                    logger.warning(f"The dst local rank {dst_rank} of the operator {op_name} "
                                   f"cannot be mapped to the global rank.")
                    continue
                src_rank = rank_map[src_rank]
                dst_rank = rank_map[dst_rank]
                link_dict[Constant.BANDWIDTH_GB_S] = \
                    self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                       link_dict.get(Constant.TRANSIT_TIME_MS, 0))
                tmp_link[f"{src_rank}-{dst_rank}"] = link_dict
            return tmp_link

        default_value = {
            Constant.TRANSPORT_TYPE: '',
            Constant.TRANSIT_TIME_MS: 0,
            Constant.TRANSIT_SIZE_MB: 0,
            Constant.OP_NAME: ''
        }
        project_local_global_rank_map = self.get_parallel_group_info()
        update_rank_map(step_dict)
        for op_name, op_dict in step_dict.items():
            link_info = defaultdict(lambda: copy.deepcopy(default_value))
            group_name = op_name.split("@")[-1]
            for rank_dict in op_dict.values():
                process_link_key(rank_dict)
            step_dict[op_name] = convert_local_to_global_rank(project_local_global_rank_map.get(group_name, {}))

    def combine_link_info(self, step_dict: dict):
        default_value = {
            Constant.TRANSPORT_TYPE: '',
            Constant.TRANSIT_TIME_MS: 0,
            Constant.TRANSIT_SIZE_MB: 0,
            Constant.OP_NAME: ''
        }
        total_op_info = defaultdict(lambda: copy.deepcopy(default_value))
        total_group_op_info = defaultdict(lambda: copy.deepcopy(total_op_info))
        for op_name, op_dict in step_dict.items():
            group_name = op_name.split("@")[-1]
            if self.check_add_op(op_name):
                for link_key, link_dict in op_dict.items():
                    self.combine_link(total_group_op_info[group_name][link_key], link_dict)
        for group_name, total_op_info in total_group_op_info.items():
            for _, link_dict in total_op_info.items():
                link_dict[Constant.BANDWIDTH_GB_S] = \
                    self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                       link_dict.get(Constant.TRANSIT_TIME_MS, 0))
            step_dict[f"{Constant.TOTAL_OP_INFO}@{group_name}"] = total_op_info

    def get_parallel_group_info(self):
        parallel_group_info = {}
        for profiler_path in self.data_map.values():
            meta_json = os.path.join(profiler_path, "profiler_metadata.json")
            if os.path.exists(meta_json):
                meta_data = FileManager.read_json_file(meta_json)
                for group_name, group_info in meta_data.get("parallel_group_info", {}).items():
                    global_ranks = group_info.get("global_ranks")
                    if isinstance(global_ranks, list) and global_ranks:
                        global_ranks.sort()
                        parallel_group_info[double_hash(group_name)] = dict(enumerate(global_ranks))
        return parallel_group_info
