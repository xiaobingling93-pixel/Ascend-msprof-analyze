import os

from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.table_constant import TableConstant
from communication_group.base_communication_group import BaseCommunicationGroup


class CommunicationDBGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_TABLE = "CommunicationGroup"

    def __init__(self, params: dict):
        super().__init__(params)
        self.communication_bandwidth_info = []
        self.communication_time_info = []
        self.matrix_info = []

    def read_communication_func(self, params: tuple):
        if len(params) < 3:
            return -1, ({}, {}, {})
        rank_id = params[0]
        db_path = params[1]
        time_data = {}
        bandwidth_data = {}
        matrix_data = {}
        if os.path.exists(db_path):
            conn, cursor = DBManager.create_connect_db(db_path)
            time_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_TIME)
            bandwidth_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_BANDWIDTH)
            matrix_info_sql = "select * from {0}".format(Constant.TABLE_COMM_ANALYZER_MATRIX)
            if (DBManager.check_tables_in_db(db_path, Constant.TABLE_COMM_ANALYZER_TIME,
                                             Constant.TABLE_COMM_ANALYZER_BANDWIDTH)
                    and self.analysis_mode in ["all", "communication_time"]):
                time_data = DBManager.fetch_all_data(cursor, time_info_sql)
                bandwidth_data = DBManager.fetch_all_data(cursor, bandwidth_info_sql)
            if (DBManager.check_tables_in_db(db_path, Constant.TABLE_COMM_ANALYZER_MATRIX)
                    and self.analysis_mode in ["all", "communication_matrix"]):
                matrix_data = DBManager.fetch_all_data(cursor, matrix_info_sql)
            DBManager.destroy_db_connect(conn, cursor)
        return rank_id, (self.data_group_by_step(time_data), self.data_group_by_step(bandwidth_data),
                         self.data_group_by_step(matrix_data))

    @staticmethod
    def data_group_by_step(data: any) -> any:
        res = {}
        for item in data:
            res.setdefault(item[TableConstant.STEP], []).append(item)
        return res

    def dump_data(self):
        output_path = os.path.join(self.collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        res = []
        for data_type, data_list in self.communication_group.items():
            for data in data_list:
                rank_set = "(" + ",".join(str(i) for i in data) + ")"
                data = [data_type, rank_set]
                res.append(data)
        if res:
            DBManager.create_tables(result_db, self.COMMUNICATION_GROUP_TABLE)
            conn, cursor = DBManager.create_connect_db(result_db)
            sql = "insert into {} values ({value})".format(self.COMMUNICATION_GROUP_TABLE,
                                                           value="?," * (len(res[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res)
            DBManager.destroy_db_connect(conn, cursor)
        else:
            print("[WARNING] The CommunicationGroup table won't be created because no data has been calculated.")
        comm_data_dict = {
            Constant.COLLECTIVE_GROUP: self.collective_group_dict,
            Constant.COMMUNICATION_TIME_INFO: self.communication_time_info,
            Constant.COMMUNICATION_BANDWIDTH_INFO: self.communication_bandwidth_info,
            Constant.MATRIX_OPS: self.matrix_info,
            Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

    def analyze_communication_data(self):
        for rank_id, data_tuple in self.rank_comm_dir_dict:
            time_data, bandwidth_data, matrix_data = data_tuple[0], data_tuple[1], data_tuple[2]
            for step, data_list in time_data.items():
                for data in data_list:
                    self.compute_collective_group(data, rank_id, self.communication_time_info)
            for step, data_list in bandwidth_data.items():
                for data in data_list:
                    self.compute_collective_group(data, rank_id, self.communication_bandwidth_info)
            for step, data_list in matrix_data.items():
                self.add_p2p_and_rank(rank_id, step, matrix_data)
                for data in data_list:
                    self.compute_collective_group(data, rank_id, self.matrix_info)

    def compute_collective_group(self, data, rank_id, res_list):
        if data[TableConstant.TYPE] == Constant.COLLECTIVE:
            self.collective_group_dict[data[TableConstant.GROUP_NAME]].add(rank_id)
            data[TableConstant.RANK_ID] = rank_id
            res_list.append(data)

    def add_p2p_and_rank(self, rank_id: int, step: str, data_dict: dict):
        data_list = data_dict[step]
        if not data_list:
            print(f"[WARNING] rank {rank_id} {step} don't have communication matrix ops data")
            return
        for data in data_list:
            if data[TableConstant.TYPE] != Constant.COLLECTIVE and data[TableConstant.TYPE] != Constant.P2P:
                print(f"[WARNING] Unknown communication operators type!")
                continue
            if data[TableConstant.TYPE] == Constant.P2P:
                if data[TableConstant.SRC_RANK] != data[TableConstant.DST_RANK]:
                    rank_set = {data[TableConstant.SRC_RANK], data[TableConstant.DST_RANK]}
                    if rank_set not in self.p2p_link:
                        self.p2p_link.append(rank_set)
