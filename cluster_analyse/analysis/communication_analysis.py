import os
from collections import defaultdict

from analysis.base_analysis import BaseAnalysis
from common_func.constant import Constant
from common_func.db_manager import DBManager


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

    @staticmethod
    def execute(conn, res_data, table_name):
        if res_data:
            res_value = [list(data.values()) for data in res_data]
            sql = "insert into {} values ({value})".format(table_name, value="?," * (len(res_value[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_value)

    def compute_total_info(self, comm_ops: dict):
        if not comm_ops:
            return
        total_rank_dict = defaultdict(lambda: {
                Constant.COMMUNICATION_TIME_INFO: defaultdict(float),
                Constant.COMMUNICATION_BANDWIDTH_INFO: {}
            })
        for communication_op, rank_dict in comm_ops.items():
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
        for transport_type, bandwidth_dict in total_bandwidth_info_dict.items():
            bandwidth_dict[Constant.BANDWIDTH_GB_S] = \
                self.compute_ratio(bandwidth_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                   bandwidth_dict.get(Constant.TRANSIT_TIME_MS, 0))
