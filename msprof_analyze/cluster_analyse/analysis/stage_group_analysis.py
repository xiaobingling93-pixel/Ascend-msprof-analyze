import json
import os
from copy import deepcopy

import pandas as pd

from msprof_analyze.cluster_analyse.common_func.table_constant import TableConstant
from msprof_analyze.cluster_analyse.common_func.utils import UnionFind
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.database_service import DatabaseService
from msprof_analyze.prof_common.file_manager import FileManager

logger = get_logger()


class StageInfoAnalysis:
    TABLE_COMMUNICATION_GROUP = "CommunicationGroup"
    TABLE_CLUSTER_COMMUNICATION_MATRIX = "ClusterCommAnalyzerMatrix"
    TABLE_COMMUNICATION_GROUP_MAPPING = "CommunicationGroupMapping"
    TABLE_CLUSTER_COMMUNICATION_MATRIX_SIMPLIFIED = "ClusterCommunicationMatrix"

    COMMUNICATION_GROUP_JSON = "communication_group.json"
    KEY_COMM_GROUP_PARALLEL_INFO = "comm_group_parallel_info"
    CLUSTER_COMMUNICATION_MATRIX_JSON = "cluster_communication_matrix.json"

    def __init__(self, param: dict):
        self.cluster_analysis_output_path = param.get(Constant.CLUSTER_ANALYSIS_OUTPUT_PATH)
        self.cluster_analysis_output_dir = os.path.join(self.cluster_analysis_output_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        self.data_type = param.get(Constant.DATA_TYPE)
        self.simplified_mode = param.get(Constant.DATA_SIMPLIFICATION)
        self.collective_group_dict = {}
        self.p2p_link = []
        self.p2p_union_group = []
        self.stage_group = []

    def run(self):
        if not os.path.exists(self.cluster_analysis_output_path):
            logger.error(f"StageInfoAnalysis: {self.cluster_analysis_output_path} not exist!")
            return []
        if not self.prepare_data():
            logger.error(f"StageInfoAnalysis: prepare data failed!")
            return []
        self.generate_p2p_union_group()
        self.generate_stage_group()
        return self.stage_group

    def prepare_data(self):
        return self.prepare_data_for_text_type() if self.data_type == Constant.TEXT else self.prepare_data_for_db_type()

    def prepare_data_for_text_type(self):
        # step0: check file exist
        communication_group_json = os.path.join(self.cluster_analysis_output_dir, self.COMMUNICATION_GROUP_JSON)
        comm_matrix_json = os.path.join(self.cluster_analysis_output_dir, self.CLUSTER_COMMUNICATION_MATRIX_JSON)
        if not os.path.exists(communication_group_json) or not os.path.exists(comm_matrix_json):
            logger.error(f"{communication_group_json} or {comm_matrix_json} not exists!")
            return False

        # step1: generate collective_group_dict from communication_group.json
        group_data = FileManager.read_json_file(communication_group_json)
        if self.KEY_COMM_GROUP_PARALLEL_INFO not in group_data:
            logger.error(f"{self.KEY_COMM_GROUP_PARALLEL_INFO} not in {self.COMMUNICATION_GROUP_JSON}")
            return False
        comm_group_df = pd.DataFrame(group_data.get(self.KEY_COMM_GROUP_PARALLEL_INFO))
        self.collective_group_dict = \
            comm_group_df[comm_group_df[TableConstant.TYPE] == Constant.COLLECTIVE].set_index(TableConstant.GROUP_NAME)[
                TableConstant.RANK_SET].to_dict()
        self.collective_group_dict = {key: set(value) for key, value in self.collective_group_dict.items()}

        # step2: generate p2p_link from communication_matrix.json
        matrix_data = FileManager.read_json_file(comm_matrix_json)
        for step_link_data in matrix_data.get(Constant.P2P, {}).values():
            for op_name, link_dict in step_link_data.items():
                self.append_p2p_link(op_name, link_dict)

        return True

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

    def prepare_data_for_db_type(self):
        """
        generate collective_group_dict and p2p_link
        """
        # step1: load data from cluster_analysis.db
        if not os.path.exists(self.cluster_analysis_output_dir):
            logger.warning("rank %s db path %s does not exist.", self.cluster_analysis_output_path)
        cluster_analysis_db = os.path.join(self.cluster_analysis_output_dir,
                                           Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        data_service = DatabaseService(cluster_analysis_db, {})
        if self.simplified_mode:
            table_communication_group = self.TABLE_COMMUNICATION_GROUP_MAPPING
            table_cluster_comm_matrix = self.TABLE_CLUSTER_COMMUNICATION_MATRIX_SIMPLIFIED
        else:
            table_communication_group = self.TABLE_COMMUNICATION_GROUP
            table_cluster_comm_matrix = self.TABLE_CLUSTER_COMMUNICATION_MATRIX
        data_service.add_table_for_query(table_communication_group,
                                         [TableConstant.TYPE, TableConstant.GROUP_NAME, TableConstant.RANK_SET])
        data_service.add_table_for_query(table_cluster_comm_matrix,
                                         [TableConstant.GROUP_NAME, TableConstant.HCCL_OP_NAME,
                                          TableConstant.SRC_RANK, TableConstant.DST_RANK])
        data_dict = data_service.query_data()
        comm_group_df = data_dict.get(table_communication_group, None)
        matrix_df = data_dict.get(table_cluster_comm_matrix, None)
        if comm_group_df is None or comm_group_df.empty:
            logger.error(f"There is no {table_communication_group} data in {cluster_analysis_db}.")
            return False
        if matrix_df is None or matrix_df.empty:
            logger.error(f"There is no {table_cluster_comm_matrix} data in {cluster_analysis_db}.")
            return False

        # step2: generate collective_group_dict
        comm_group_df[TableConstant.RANK_SET] = comm_group_df[TableConstant.RANK_SET].apply(
            lambda s: tuple(map(int, s.strip('()').split(','))))
        self.collective_group_dict = \
            comm_group_df[comm_group_df[TableConstant.TYPE] == Constant.COLLECTIVE].set_index(TableConstant.GROUP_NAME)[
                TableConstant.RANK_SET].to_dict()
        self.collective_group_dict = {key: set(value) for key, value in self.collective_group_dict.items()}

        # setp3: generate p2p_link
        p2p_matrix_df = matrix_df[matrix_df[TableConstant.HCCL_OP_NAME].str.contains('receive|recv|send',
                                                                                     case=False, regex=True)]
        p2p_matrix_df[TableConstant.SRC_RANK] = p2p_matrix_df[TableConstant.SRC_RANK].apply(
            lambda x: int(x) if str(x).isdigit() else -1)
        p2p_matrix_df[TableConstant.DST_RANK] = p2p_matrix_df[TableConstant.DST_RANK].apply(
            lambda x: int(x) if str(x).isdigit() else -1)
        p2p_matrix_df = p2p_matrix_df[
            (p2p_matrix_df[TableConstant.SRC_RANK] != -1) &
            (p2p_matrix_df[TableConstant.DST_RANK] != -1)
            ]
        links = list(zip(p2p_matrix_df[TableConstant.SRC_RANK], p2p_matrix_df[TableConstant.DST_RANK]))
        self.p2p_link = list(set(links))
        return True

    def generate_p2p_union_group(self):
        self.p2p_link = sorted(self.p2p_link, key=lambda x: min(x))
        while self.p2p_link:
            union_set = deepcopy(self.p2p_link[0])
            rm_list = [self.p2p_link[0]]
            for _, link_rank_set_x in enumerate(self.p2p_link[1:]):
                if UnionFind.is_connected(link_rank_set_x, union_set):
                    union_set = union_set.union(link_rank_set_x)
                    rm_list.append(link_rank_set_x)
            self.p2p_union_group.append(union_set)
            self.p2p_link = [element for element in self.p2p_link if element not in rm_list]

    def generate_stage_group(self):
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
        self.stage_group = [list(stage_group.get(first_rank, {})) for first_rank in first_rank_sort_list]

    def whether_valid_comm_group(self, rank_set: set):
        """
        while distinguish which communication group should be used to infer stage info, these group should be ignored:
            1. group can not include more than 1 rank in every single p2p group
        """
        for p2p_rank_set in self.p2p_union_group:
            if len(rank_set.intersection(p2p_rank_set)) > 1:
                return False
        return True


if __name__ == '__main__':
    params = {
        Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "/home/fanglanyue/data_space/mstt/",
        Constant.DATA_TYPE: Constant.DB,
        Constant.DATA_SIMPLIFICATION: False
    }
    worker = StageInfoAnalysis(params)
    aa = worker.run()
    print(aa)
