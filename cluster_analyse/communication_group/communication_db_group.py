import os

from common_func.data_transfer_adapter import DataTransferAdapter
from common_func.db_manager import DBManager
from common_func.constant import Constant
from communication_group.base_communication_group import BaseCommunicationGroup


class CommunicationDBGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_TABLE = "CommunicationGroup"

    def __init__(self, params: dict):
        super().__init__(params)

    def read_communication_func(self, params: tuple):
        if len(params) < 3:
            return -1, ({}, {}, {})
        rank_id = params[0]
        db_path = params[1]
        time_data = []
        bandwidth_data = []
        matrix_data = []
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
        comm_data = DataTransferAdapter.transfer_comm_from_db_to_json(time_data, bandwidth_data)
        comm_matrix_data = DataTransferAdapter.transfer_matrix_from_db_to_json(matrix_data)
        return rank_id, comm_data, comm_matrix_data

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
            Constant.COMMUNICATION_OPS: self.communication_ops,
            Constant.MATRIX_OPS: self.matrix_ops,
            Constant.COMMUNICATION_GROUP: self.communication_group
        }
        return comm_data_dict

